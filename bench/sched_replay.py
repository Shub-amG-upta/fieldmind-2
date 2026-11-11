#!/usr/bin/env python3
"""
=============================================================================
 SCHEDULING REPLAY  --  the sweep's recorded job streams, re-placed offline
 (sched fix part C; reports/sched_fix.md)
=============================================================================

    .venv/bin/python bench/sched_replay.py [--policies fixed,earliest_finish,calibrated_finish]
                                           [--json out.json]

For every real-time cell of the 2026-11-10/11 board sweep (results/benchmarks/
sched_*), the jobs the agent submitted (agent, side, priority, evidence tick,
submit time, deadline, prompt estimate) are replayed on a simulated clock and
placed by each policy. The DECISIONS are made by the real
fieldmind.multi.realtime.RealtimeRunner (its threads stopped, its clock the
simulated one), so the policies are the code that runs on the board, imported,
not copied. Only the WORLD is modelled:

  - a call reads its real prompt tokens and writes its real answer tokens (the
    call the job made on the board; the agent's median when unmatched);
  - each model lane runs at its in-situ alone speed (bench.sched_study insitu),
    slowed by the in-situ together/alone ratio while the other model lane is
    working (a fluid model: speeds change at every start and finish);
  - decision-model follow-ups run on their own lane for their recorded time;
  - a newer job for the same (agent, side) replaces one still waiting.

Assumptions: the agent submits the same jobs whatever the placement (calls are
decided by evidence changes, not by answers), so a job the board replaced before
it ran is missing from the stream. The world is medians: per-call variation,
heat and the board's own noise are not in it.

Validation first: the replay of each cell's RECORDED policy is compared with
the cell's recorded P2 misses. The other policies' numbers are predictions
of this model, not board results.
=============================================================================
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bench import sched_study as S  # noqa: E402

MODEL_LANES = ("npu", "cpu")
EPS = 1e-9
# DESIGN: a run's own alone speed for a lane is used when at least this many of its calls on
# that lane ran with no overlap; otherwise the sweep-wide median. Range 5-30. Affects the world model.
MIN_OWN_CALLS = 10
# DESIGN, fixed before reading any replay result of calibrated_finish: the replay is valid for a
# run only when the board replaced at most this share of the jobs it submitted (a replaced job is
# missing from the stream, so the replay has less work than the board had). Range 0.02-0.10.
MAX_REPLACED_SHARE = 0.05


class SimClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def stream(run: dict) -> dict:
    """The recorded jobs of one real-time run: arrivals (calls that were not a
    follow-up), each call's real tokens, and each call's follow-up."""
    rt = run["multi"]["realtime"]
    spans = rt["spans"]
    calls = S.span_calls(run)
    est = {x["job_id"]: x.get("prompt_tokens") for a in run["assessments"]
           for x in (a.get("multi") or {}).get("results") or []}
    kids = S.followups(spans)
    kid_jobs = {k["job"] for k in kids.values()}
    med: dict[str, list] = {}
    for s in spans:
        c = calls.get(s["job"])
        if c:
            med.setdefault(s["agent"], []).append((c["prefill"], c.get("decode") or 0))
    def typical(agent):
        v = sorted(med.get(agent) or [(0, 0)])
        return v[len(v) // 2]
    jobs = []
    for s in sorted(spans, key=lambda s: (s["submit_s"], s["job"])):
        if s["job"] in kid_jobs:
            continue
        c = calls.get(s["job"])
        pre, dec = (c["prefill"], c.get("decode") or 0) if c else typical(s["agent"])
        jobs.append({"job": s["job"], "agent": s["agent"], "side": s.get("side") or "all",
                     "priority": s["priority"], "evidence_tick": s["evidence_tick"],
                     "tick_s": s["tick_s"], "submit_s": s["submit_s"], "deadline_s": s["deadline_s"],
                     "lane": s["lane"], "run_s": s["run_s"], "est": est.get(s["job"]) or pre,
                     "prefill": pre, "decode": dec, "matched": bool(c),
                     "followup_s": kids[s["job"]]["run_s"] if s["job"] in kids else None})
    return {"wall_tick_s": rt["wall_tick_s"], "jobs": jobs}


def make_runner(config: str, asset: str, policy: str, clock: SimClock):
    """The scheduler and runner a board run of this cell builds, with `policy`;
    the runner's worker threads stopped (decisions only)."""
    from fieldmind.multi.lanes import SimLane
    from fieldmind.multi.realtime import RealtimeRunner
    from fieldmind.multi.scheduler import Scheduler
    from fieldmind.runtime.llm_backend import MockBackend
    from run_demo import load_config
    cfg = load_config(str(ROOT / "configs/base.yaml"), "mock",
                      ",".join(str(ROOT / o) for o in S.overlay(config, asset).split(",")))
    m = dict(cfg["multi"])
    m["placement"] = policy
    lanes = [SimLane(n, MockBackend(), lc["prefill_tok_s"], lc["decode_tok_s"], kind=lc.get("kind", "llm"))
             for n, lc in m["lanes"].items()]
    sched = Scheduler(lanes, m)
    rt = RealtimeRunner(sched, clock=clock)
    rt.close()                                   # no worker threads: this replay runs the lanes
    return sched, rt, m


def simulate(st: dict, config: str, asset: str, policy: str, world: dict) -> list[dict]:
    """Replay one recorded stream under `policy`. Returns one record per job that
    ran: lane, start, call end, release (after any follow-up), deadline."""
    clock = SimClock()
    sched, rt, m = make_runner(config, asset, policy, clock)
    caps = m.get("answer_caps") or {}
    cap_of = lambda a: caps.get("verifier", 30) if a.startswith("verif") else caps.get("diagnostician", 60)  # noqa: E731
    alone, together = world["alone"], world["together_over_alone"]
    lanes = {n: None for n in rt.running}         # lane -> state of its running call
    bev_free = {n: 0.0 for n in rt.running if n not in MODEL_LANES}
    rec_of, out = {}, []
    arrivals = list(st["jobs"])
    i = 0

    def speed(n, phase):
        other = [o for o in MODEL_LANES if o != n and lanes.get(o) is not None]
        f = together[n][phase] if other else 1.0
        return alone[n][phase] * f

    def start_next(n):
        if n not in MODEL_LANES:
            return
        job = rt._pop(n)
        if job is None:
            return
        if rt.waiting.get((job.agent, job.side)) is job:
            del rt.waiting[(job.agent, job.side)]
        rt.running[n] = job
        job.wall_start = clock.t
        r = rec_of[job.job_id]
        lanes[n] = {"job": job, "pre": float(r["prefill"]), "dec": float(r["decode"]),
                    "pre_s": 0.0, "dec_s": 0.0, "start": clock.t}

    def finish(n):
        s = lanes[n]
        job, r = s["job"], rec_of[s["job"].job_id]
        lanes[n] = None
        rt.running[n] = None
        from fieldmind.schemas import AgentEnvelope
        env = AgentEnvelope(agent=job.agent, tick=job.evidence_tick)
        env.calls = [{"status": "ok", "prefill": r["prefill"], "decode": r["decode"],
                      "prefill_ms": s["pre_s"] * 1000, "decode_ms": s["dec_s"] * 1000}]
        rt._update_rates(n, env)
        rt._learn(job, env)
        release = clock.t
        if r["followup_s"] is not None:          # the decision model's lane, first come first served
            bev = next(iter(bev_free), None)
            begin = max(clock.t, bev_free[bev]) if bev else clock.t
            release = begin + r["followup_s"]
            if bev:
                bev_free[bev] = release
        out.append({"job": r["job"], "priority": r["priority"], "lane": n, "start": s["start"],
                    "end": clock.t, "release": release, "tick_s": r["tick_s"], "deadline_s": r["deadline_s"]})

    while i < len(arrivals) or any(lanes[n] for n in MODEL_LANES) or any(rt._has_job(n) for n in MODEL_LANES):
        # time to the next event: an arrival or a running call's end at the current speeds
        nxt, who = (arrivals[i]["submit_s"], "arrival") if i < len(arrivals) else (float("inf"), None)
        for n in MODEL_LANES:
            s = lanes[n]
            if s is None:
                continue
            t_end = clock.t + s["pre"] / speed(n, "prefill") + s["dec"] / speed(n, "decode")
            if t_end < nxt - EPS:
                nxt, who = t_end, n
        dt = max(0.0, nxt - clock.t)
        for n in MODEL_LANES:                    # progress every running call over dt
            s = lanes[n]
            if s is None:
                continue
            left = dt
            sp_p, sp_d = speed(n, "prefill"), speed(n, "decode")
            use = min(left, s["pre"] / sp_p) if s["pre"] > 0 else 0.0
            s["pre"] -= use * sp_p
            s["pre_s"] += use
            left -= use
            if left > 0 and s["dec"] > 0:
                use = min(left, s["dec"] / sp_d)
                s["dec"] -= use * sp_d
                s["dec_s"] += use
        clock.t = nxt
        for n in MODEL_LANES:
            s = lanes[n]
            if s is not None and s["pre"] <= 1e-6 and s["dec"] <= 1e-6:
                finish(n)
        if who == "arrival":
            r = arrivals[i]
            i += 1
            if r["lane"] not in MODEL_LANES:
                continue                          # decision-model jobs keep their own lane
            job = sched.new_job(r["agent"], r["evidence_tick"], r["priority"], cap_of(r["agent"]),
                                clock.t, side=r["side"], prompt_tokens=r["est"])
            job.wall_submit = clock.t
            job.wall_tick = r["tick_s"]
            rec_of[job.job_id] = r
            job.lane = rt.choose(job)
            old = rt.waiting.get((job.agent, job.side))
            if old is not None:
                old.replaced = True
            rt.waiting[(job.agent, job.side)] = job
            import heapq
            heapq.heappush(rt.heaps[job.lane], (job.priority, next(rt._seq), job))
        for n in MODEL_LANES:
            if lanes[n] is None:
                start_next(n)
    return out


def misses(records: list[dict], priority: int, at: str) -> tuple[int, int]:
    rs = [r for r in records if r["priority"] == priority and r["deadline_s"] is not None]
    return sum((r[at] - r["tick_s"]) > r["deadline_s"] for r in rs), len(rs)


def recorded_misses(run: dict, priority: int) -> tuple[int, int]:
    """The board run's own count, judged at call end (bench.sched_study.run_metrics)."""
    d = S.run_metrics(run, {})["deadline"][f"P{priority}"]
    return d["missed"], d["n"]


def replay_all(policies: list[str], world: dict, root: Path = ROOT / "results/benchmarks") -> list[dict]:
    rows = []
    for c in S.cells():
        if c["mode"] != "realtime":
            continue
        for f in sorted((root / c["name"]).glob("*.run.json.gz")):
            with gzip.open(f, "rt") as fh:
                run = json.load(fh)
            st = stream(run)
            replaced = run["multi"]["realtime"].get("replaced_waiting_jobs") or 0
            row = {"cell": c["name"], "config": c["config"], "policy_recorded": c["policy"],
                   "tick_s": c["tick_s"], "asset": c["asset"], "episode": run["episode_id"],
                   "jobs": len(st["jobs"]), "unmatched": sum(not j["matched"] for j in st["jobs"]),
                   "replaced_on_board": replaced,
                   "valid": replaced <= MAX_REPLACED_SHARE * (len(st["jobs"]) + replaced),
                   "recorded_P2": recorded_misses(run, 2), "sim": {}}
            w = world_for_run(run, world)
            for p in policies:
                recs = simulate(st, c["config"], c["asset"], p, w)
                row["sim"][p] = {"P2_end": misses(recs, 2, "end"), "P2_release": misses(recs, 2, "release"),
                                 "P1_release": misses(recs, 1, "release"),
                                 "cpu_calls": sum(r["lane"] == "cpu" for r in recs), "ran": len(recs)}
            rows.append(row)
    return rows


def world_from(insitu: dict) -> dict:
    lanes = insitu["lanes"]
    return {"alone": {n: lanes[n]["alone"] for n in MODEL_LANES},
            "together_over_alone": {n: lanes[n]["together_over_alone"] for n in MODEL_LANES}}


def world_for_run(run: dict, sweep: dict) -> dict:
    """The sweep-wide world with each lane's alone speed replaced by this run's own
    median when the run has at least MIN_OWN_CALLS no-overlap calls on that lane
    (the run's own heat and prompt sizes); contention ratios stay sweep-wide."""
    own = S.insitu([run])["lanes"]
    alone = {n: dict(sweep["alone"][n]) for n in MODEL_LANES}
    for n in MODEL_LANES:
        if own[n]["n_alone"] >= MIN_OWN_CALLS:
            alone[n] = {k: own[n]["alone"][k] or alone[n][k] for k in ("prefill", "decode")}
    return {"alone": alone, "together_over_alone": sweep["together_over_alone"]}


def summary(rows: list[dict], policies: list[str]) -> str:
    def rate(pairs):
        k = sum(a for a, _ in pairs); n = sum(b for _, b in pairs)
        return k / n if n else None
    cells: dict = {}
    for r in rows:
        cells.setdefault((r["config"], r["asset"], r["policy_recorded"], r["tick_s"]), []).append(r)
    head = ("| config | plant | recorded policy | s/tick | P2 missed: board | replay, same policy | "
            + " | ".join(f"replay {p}" for p in policies) + " |")
    out = [head, "|" + "---|" * (6 + len(policies))]
    for (cfg, asset, pol, t), rs in sorted(cells.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2], -kv[0][3])):
        f = lambda x: "–" if x is None else f"{x:.2f}"  # noqa: E731
        valid = all(r["valid"] for r in rs)
        board = rate([r["recorded_P2"] for r in rs])
        same = rate([r["sim"][pol]["P2_end"] for r in rs]) if pol in policies else None
        out.append(f"| {cfg} | {asset} | {pol} | {t:g}{'' if valid else ' (not valid)'} | {f(board)} | {f(same)} | "
                   + " | ".join(f(rate([r["sim"][p]["P2_end"] for r in rs])) for p in policies) + " |")
    # capacity per (config, plant, policy) from the replay, on the streams of each recorded policy
    out += ["", f"Capacity in the replay (P2 misses <= {S.KEEP_UP_P2_MISS:.0%} at that load and every slower one)", "",
            "| config | plant | stream from | " + " | ".join(policies) + " |", "|" + "---|" * (3 + len(policies))]
    groups: dict = {}
    for (cfg, asset, pol, t), rs in cells.items():
        for p in policies:
            groups.setdefault((cfg, asset, pol), {}).setdefault(p, {})[t] = rate([r["sim"][p]["P2_end"] for r in rs])
    for (cfg, asset, pol), by in sorted(groups.items()):
        caps = [S.capacity(by[p]) for p in policies]
        out.append(f"| {cfg} | {asset} | {pol} cells | "
                   + " | ".join("none" if c is None else f"{c:g} s" for c in caps) + " |")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--policies", default="fixed,earliest_finish,calibrated_finish")
    ap.add_argument("--insitu", default=str(ROOT / "reports/data/sched_insitu.json"))
    ap.add_argument("--json", default=None)
    args = ap.parse_args(argv)
    policies = args.policies.split(",")
    world = world_from(json.loads(Path(args.insitu).read_text()))
    rows = replay_all(policies, world)
    print("REPLAY: decisions by the real runner code, the world modelled from the sweep's in-situ medians. "
          "Predictions of this model, not board results.\n")
    print(summary(rows, policies))
    if args.json:
        Path(args.json).write_text(json.dumps(rows, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
