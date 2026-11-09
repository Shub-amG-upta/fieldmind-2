"""
=============================================================================
 REAL-TIME LANES  (multi-agent Phase 4; scheduling study, plan Phase 5)
=============================================================================

One worker thread per lane. Each lane runs ONE model call at a time from its
own queue; the tick loop only submits jobs and collects whatever has finished,
so the tick never waits for a model (plan rule 1).

  submit(job)  choose the job's lane under the placement policy, then queue it.
               Each lane's queue is ordered by (priority, submit order): a P1
               job runs before any waiting P2-P4 job (plan "Priorities and
               deadlines"). A newer job for the same (agent, side) replaces one
               still WAITING (plan: "at most one waiting job per (agent,
               side)"); a running call finishes.
  drain()      the Results that finished since the last drain (non-blocking).
  followup     optional callable(result) -> Job | None, set by the orchestrator:
               a follow-up job is submitted the moment its parent finishes (on
               the lane's worker thread, same evidence tick and wall tick) and
               the parent's Result is released only together with the
               follow-up's, so a two-stage answer (explain: Llama ranks, the
               decision model cites) costs no extra tick.

Placement policies (multi.placement; plan "Policies to compare in the
scheduling study"). Decision-model jobs (decider, bev_*) always go to their
own lane; the policies choose among the model lanes of the job's kind:
  fixed              each agent's lane from multi.fixed_placement
  earliest_finish    the lane whose predicted finish is earliest: the time the
                     lane frees up (its running call, then every queued job of
                     equal or higher priority) + prompt / prefill rate +
                     answer cap / decode rate. Ties to the first lane (NPU).
  tick_alternation   all model work of odd evidence ticks on the first lane
                     (NPU), of even ticks on the second (CPU)
  priority_reserved  earliest finish, but while a P1 job is waiting or running
                     no P2-P4 job is given the first lane (NPU): the NPU is
                     kept for urgent work
The rates start at the lane's planning rates (SimLane). With multi.adapt_rates
they are updated after every call from that call's measured prefill and decode
timings (EWMA), so the prediction follows the real state of the chip, including
heat; without it (the default) they stay at the planning rates, which keeps a
mock run deterministic (measured mock timings are noise and feed back into lane
choice).

Deadlines are in ticks (multi.rt_deadline_ticks) and turned into wall seconds
with the wall tick, so a compressed clock keeps the plan's meaning (P1 10 s,
P2 30 s, P3 60 s at 30 s ticks). Every finished call records its lane,
priority, evidence tick, wait, run time, deadline and whether it was met.

Timings are WALL-CLOCK seconds since the runner started (laptop or board),
not the simulated clock of lockstep mode. Stdlib only.
=============================================================================
"""

from __future__ import annotations

import heapq
import itertools
import queue
import threading
import time

from ..schemas import AgentEnvelope
from .jobs import Result

POLICIES = ("fixed", "earliest_finish", "tick_alternation", "priority_reserved")
# DESIGN: weight of the newest measured rate in the lane's running estimate. Range 0.1-0.5.
# Affects only the earliest_finish / priority_reserved predictions (and their telemetry).
RATE_EWMA = 0.3


class RealtimeRunner:
    def __init__(self, scheduler, clock=time.monotonic, wall_tick_s: float | None = None,
                 deadline_ticks: dict | None = None):
        if scheduler.placement not in POLICIES:
            raise ValueError(f"real-time placement must be one of {POLICIES}, "
                             f"got {scheduler.placement!r}")
        self.s = scheduler
        self.policy = scheduler.placement
        self.clock = clock
        self.t0 = clock()
        self.wall_tick_s = wall_tick_s
        self.deadline_ticks = {int(k): (None if v is None else float(v))
                               for k, v in (deadline_ticks or {}).items()}
        self.lock = threading.Lock()
        self.cv = threading.Condition(self.lock)
        self.done: queue.Queue = queue.Queue()
        self.heaps: dict[str, list] = {l.name: [] for l in scheduler.lanes}
        self.order = [l.name for l in scheduler.lanes]
        self._seq = itertools.count()
        self.closed = False
        self.waiting: dict[tuple, object] = {}          # (agent, side) -> job not started
        self.running: dict[str, object] = {l.name: None for l in scheduler.lanes}
        self.adapt = bool(scheduler.cfg.get("adapt_rates"))
        self.rates = {l.name: [float(l.prefill_tok_s), float(l.decode_tok_s)]
                      for l in scheduler.lanes}
        self.spans: list[dict] = []                     # one per finished call
        self.replaced: list[str] = []
        self.followup = None                            # callable(result) -> Job | None
        self.chained: dict[str, Result] = {}            # follow-up job id -> its parent's Result
        self.settling = 0          # finished jobs not yet handed on (done queue or follow-up)
        self.threads = [threading.Thread(target=self._worker, args=(l,), daemon=True,
                                         name=f"lane-{l.name}") for l in scheduler.lanes]
        for t in self.threads:
            t.start()

    def now(self) -> float:
        return self.clock() - self.t0

    # ------------------------------------------------------------------ placement
    def _service(self, lane: str, job) -> float:
        pre, dec = self.rates[lane]
        return (job.prompt_tokens or 0) / pre + job.max_answer_tokens / dec

    def _free_at(self, lane: str, now: float, priority: int) -> float:
        """When `lane` could start a job of `priority`: its running call's
        predicted end, then every queued job that would run first."""
        t = now
        run = self.running[lane]
        if run is not None:
            t = max(t, run.wall_start + self._service(lane, run))
        for p, _, j in self.heaps[lane]:
            if not j.replaced and p <= priority:
                t += self._service(lane, j)
        return t

    def _p1_active(self) -> bool:
        if any(j is not None and j.priority == 1 for j in self.running.values()):
            return True
        return any(p == 1 and not j.replaced for h in self.heaps.values() for p, _, j in h)

    def _fixed(self, job, lanes: list[str]) -> str:
        table = self.s.fixed_placement
        name = table.get(job.agent)
        if name is None and job.agent.startswith("bev_"):
            name = table.get("bev")             # bev ideas: explicit table entry
        if name is None and len(lanes) == 1:
            name = lanes[0]                     # the only lane of its kind
        if name is None:
            raise KeyError(f"agent {job.agent!r} has no lane in multi.fixed_placement")
        return name

    def choose(self, job) -> str:
        """The lane for `job` under the policy (call with the lock held)."""
        lanes = [l.name for l in self.s.eligible_lanes(job.agent)]
        if self.policy == "fixed" or self.s.lane_kind(job.agent) == "decider":
            return self._fixed(job, lanes)
        if self.policy == "tick_alternation":
            return lanes[0] if len(lanes) == 1 or job.evidence_tick % 2 == 1 else lanes[1]
        if job.prompt_tokens is None:
            raise ValueError(f"{job.agent}: {self.policy} needs the job's prompt_tokens at submit")
        cands = lanes
        if self.policy == "priority_reserved" and job.priority >= 2 and len(lanes) > 1 \
                and self._p1_active():
            cands = lanes[1:]
        now = self.now()
        finish = {n: self._free_at(n, now, job.priority) + self._service(n, job) for n in cands}
        best = min(cands, key=lambda n: (finish[n], lanes.index(n)))
        job.predicted_finish_s = round(finish[best], 6)
        return best

    # ------------------------------------------------------------------ queueing
    def submit(self, job, tick_wall_s: float | None = None) -> None:
        with self.cv:
            job.wall_submit = self.now()
            job.wall_tick = job.wall_submit if tick_wall_s is None else tick_wall_s
            job.lane = self.choose(job)
            old = self.waiting.get((job.agent, job.side))
            if old is not None:
                old.replaced = True
                self.replaced.append(old.job_id)
                self.chained.pop(old.job_id, None)      # its parent is superseded too
            self.waiting[(job.agent, job.side)] = job
            heapq.heappush(self.heaps[job.lane], (job.priority, next(self._seq), job))
            self.cv.notify_all()

    def _pop(self, lane: str):
        h = self.heaps[lane]
        while h:
            _, _, job = heapq.heappop(h)
            if not job.replaced:
                return job
        return None

    def _has_job(self, lane: str) -> bool:
        return any(not j.replaced for _, _, j in self.heaps[lane])

    def in_flight(self, agent: str, side: str) -> list:
        """Jobs of (agent, side) waiting or running now."""
        with self.lock:
            out = [j for j in self.running.values()
                   if j is not None and (j.agent, j.side) == (agent, side)]
            w = self.waiting.get((agent, side))
            return out + ([w] if w is not None else [])

    def drain(self) -> list[Result]:
        out = []
        while True:
            try:
                out.append(self.done.get_nowait())
            except queue.Empty:
                return out

    def idle(self) -> bool:
        with self.lock:
            return (not self.waiting and not self.settling
                    and all(j is None for j in self.running.values())
                    and not any(self._has_job(n) for n in self.heaps))

    def wait_idle(self, timeout_s: float) -> bool:
        end = self.clock() + timeout_s
        while self.clock() < end:
            if self.idle():
                return True
            time.sleep(0.01)
        return self.idle()

    def close(self) -> None:
        with self.cv:
            self.closed = True
            self.cv.notify_all()
        for t in self.threads:
            t.join(timeout=5)

    # ------------------------------------------------------------------ lanes
    def _update_rates(self, lane: str, env) -> None:
        """EWMA of the measured prefill and decode rates of `lane` (calls that
        report both a token count and a time); only with multi.adapt_rates."""
        if not self.adapt:
            return
        for c in getattr(env, "calls", None) or []:
            if c.get("status") != "ok":
                continue
            for i, (n, ms) in enumerate(((c.get("prefill"), c.get("prefill_ms")),
                                         (c.get("decode"), c.get("decode_ms")))):
                if n and ms and n > 0 and ms > 0:
                    r = n / (ms / 1000.0)
                    self.rates[lane][i] = (1 - RATE_EWMA) * self.rates[lane][i] + RATE_EWMA * r

    def _worker(self, lane) -> None:
        while True:
            with self.cv:
                self.cv.wait_for(lambda: self.closed or self._has_job(lane.name))
                job = self._pop(lane.name)
                if job is None:
                    if self.closed:
                        return
                    continue
                if self.waiting.get((job.agent, job.side)) is job:
                    del self.waiting[(job.agent, job.side)]
                self.running[lane.name] = job
                job.wall_start = self.now()
            start = job.wall_start
            self.s.current = job                     # this thread's job (LaneBackend)
            try:
                lane.begin(job)
                env = job.work()
            except Exception as e:                   # the tick never fails
                env = AgentEnvelope(agent=job.agent, tick=job.evidence_tick,
                                    status="error", error=repr(e),
                                    payload={"error": repr(e)})
            finally:
                if lane.running is job:
                    lane.end(job)
                self.s.current = None
            end = self.now()
            job.start_s, job.finish_s = start, end   # wall clock, not simulated
            dticks = self.deadline_ticks.get(job.priority)
            deadline = (dticks * self.wall_tick_s
                        if dticks is not None and self.wall_tick_s else None)
            age = end - job.wall_tick
            with self.cv:
                self._update_rates(lane.name, env)
                self.running[lane.name] = None
                self.settling += 1     # idle() stays False until the result is handed on
                self.spans.append({
                    "lane": lane.name, "job": job.job_id, "agent": job.agent, "side": job.side,
                    "priority": job.priority, "evidence_tick": job.evidence_tick,
                    "tick_s": round(job.wall_tick, 4), "submit_s": round(job.wall_submit, 4),
                    "start_s": round(start, 4), "end_s": round(end, 4),
                    "wait_s": round(start - job.wall_submit, 4), "run_s": round(end - start, 4),
                    "predicted_finish_s": getattr(job, "predicted_finish_s", None),
                    "deadline_s": None if deadline is None else round(deadline, 4),
                    "met": None if deadline is None else age <= deadline,
                    "age_ticks": round(age / self.wall_tick_s, 4) if self.wall_tick_s else None,
                    "status": getattr(env, "status", None)})
                self.cv.notify_all()
            result = Result(job=job, envelope=env, evidence_tick=job.evidence_tick,
                            lane=lane.name, queue_wait_ms=(start - job.wall_submit) * 1000,
                            start_s=start, finish_s=end, tick_epoch_s=job.wall_tick)
            nxt = None
            if self.followup is not None and job.job_id not in self.chained:
                try:
                    nxt = self.followup(result)
                except Exception as e:                # a follow-up never breaks the lane
                    nxt = None
                    result.envelope.error = (result.envelope.error or "") + f" followup: {e!r}"
            try:
                if nxt is not None:
                    with self.cv:
                        self.chained[nxt.job_id] = result
                    self.submit(nxt, tick_wall_s=job.wall_tick)
                else:
                    with self.cv:
                        parent = self.chained.pop(job.job_id, None)
                    if parent is not None:
                        self.done.put(parent)
                    self.done.put(result)
            finally:
                with self.cv:
                    self.settling -= 1
                    self.cv.notify_all()

    # ------------------------------------------------------------------ telemetry
    def telemetry(self) -> dict:
        with self.lock:
            spans = list(self.spans)
            rates = {k: [round(v[0], 2), round(v[1], 3)] for k, v in self.rates.items()}
        return {"policy": self.policy, "wall_tick_s": self.wall_tick_s, "adapt_rates": self.adapt,
                **summarize(spans),
                "rates_tok_s": rates, "replaced_waiting_jobs": len(self.replaced),
                "workers_alive": {t.name: t.is_alive() for t in self.threads},
                "spans": spans}


def _pct(xs: list, q: float):
    if not xs:
        return None
    s = sorted(xs)
    return round(s[min(len(s) - 1, int(q * len(s)))], 4)


def summarize(spans: list[dict]) -> dict:
    """Per-run scheduling numbers from the finished calls: calls and busy time per
    lane, time the NPU and CPU lanes were busy together, deadline misses per
    priority, answer age at completion in ticks (p50 / p95 / max)."""
    by_lane: dict[str, list] = {}
    for sp in spans:
        by_lane.setdefault(sp["lane"], []).append(sp)
    overlap = 0.0
    if "npu" in by_lane and "cpu" in by_lane:
        for x in by_lane["npu"]:
            for y in by_lane["cpu"]:
                overlap += max(0.0, min(x["end_s"], y["end_s"]) - max(x["start_s"], y["start_s"]))
    misses = {}
    for sp in spans:
        if sp.get("met") is None:
            continue
        m = misses.setdefault(f"P{sp['priority']}", {"n": 0, "missed": 0})
        m["n"] += 1
        m["missed"] += not sp["met"]
    ages = [sp["age_ticks"] for sp in spans if sp.get("age_ticks") is not None]
    return {"calls": {k: len(v) for k, v in by_lane.items()},
            "busy_s": {k: round(sum(s["end_s"] - s["start_s"] for s in v), 3)
                       for k, v in by_lane.items()},
            "both_lanes_busy_s": round(overlap, 3),
            "deadline": misses,
            "age_ticks": {"p50": _pct(ages, 0.5), "p95": _pct(ages, 0.95),
                          "max": max(ages) if ages else None}}
