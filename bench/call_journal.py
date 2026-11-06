"""
Crash-safe log of every model call of one episode, and resume from it.

`<stem>.calls.jsonl` is append-only. A model answer is flushed and fsynced before
the agent sees it, so a crash, Ctrl-C, unplug or power cut loses at most the call
in progress. Running the same episode again replays the logged answers in order
(no board call), which rebuilds the agent's state tick by tick, then continues
live from the first call that has no logged answer.

Rules that keep a resumed run honest:
  * a logged answer is reused only if lane, role, cap, grammar and the exact
    prompt all match the call being made; otherwise ResumeDiverged stops the run
    and the runner starts the episode over. Nothing is ever mixed silently.
  * replayed answers keep the timings measured when they were made.
  * the run file records `resume` (sessions, replayed and live calls).
  * a lost connection is NOT an answer: it stops the run (the runner waits for the
    board and resumes) instead of leaving failed calls in the published result. A
    timeout or server error while the lane is still healthy is a real result of
    the configuration and is logged and used, as it always was.

Lockstep only: real time does not make its calls in a repeatable order.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import time
import urllib.request
from pathlib import Path

from fieldmind.runtime.llm_backend import LLMReply

RESUME_DIVERGED = "RESUME_DIVERGED"
# A call that killed the run this many times is logged as a failed call on the next try, so
# one bad request cannot block a batch. One death can be a USB drop; two on the same call are
# not. (Seen on TEP: the pinned llama-server dies on one exact prompt + grammar, every time.)
MAX_DEATHS_PER_CALL = 2


class ResumeDiverged(RuntimeError):
    """The call being made is not the one logged at this position."""


class BoardConnectionLost(ConnectionError):
    """The lane cannot be reached. The message holds a phrase the runner's
    DISCONNECT rule recognises, so it waits for the board and resumes."""


def call_key(lane: str, role: str, max_tokens: int, grammar: str | None, prompt: str) -> str:
    body = json.dumps([lane, role, max_tokens, grammar or "", prompt], ensure_ascii=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def read_records(path: Path) -> list[dict]:
    """Every whole line of the log; a torn last line (a crash mid-write) is dropped."""
    if not path.exists():
        return []
    out = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.endswith("\n"):
                break
            try:
                out.append(json.loads(line))
            except ValueError:
                break
    return out


def _lane_healthy(url: str) -> bool:
    try:
        with urllib.request.urlopen(f"{url.rstrip('/')}/health", timeout=10) as r:
            return r.status == 200
    except Exception:
        return False


class CallJournal:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        recs = read_records(self.path)
        self.replay = [r for r in recs if r.get("event") == "done"]
        self.n_sessions = sum(r.get("event") == "session" for r in recs) + 1
        self.deaths: dict = {}          # (agent, lane, tick): starts with no answer since the last answer
        for r in recs:
            if r.get("event") == "done":
                self.deaths = {}
            elif r.get("event") == "start":
                k = (r.get("agent"), r.get("lane"), r.get("tick"))
                self.deaths[k] = self.deaths.get(k, 0) + 1
        self.crash_recorded = 0
        self.i = 0
        self.replayed = 0
        self.live = 0
        self._announced_live = not self.replay
        # rewrite without a torn tail before appending, so every line stays whole
        if self.path.exists() and self.path.read_bytes()[-1:] not in (b"\n", b""):
            good = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(good, encoding="utf-8")
            os.replace(tmp, self.path)
        self.f = self.path.open("a", encoding="utf-8")
        self._write({"event": "session", "n": self.n_sessions, "replay": len(self.replay),
                     "t": time.strftime("%Y-%m-%dT%H:%M:%S")}, sync=True)

    def _write(self, rec: dict, sync: bool) -> None:
        self.f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self.f.flush()
        if sync:
            os.fsync(self.f.fileno())

    def next_logged(self, key: str, where: str) -> dict | None:
        """The logged answer for this call, or None once the log is used up."""
        if self.i >= len(self.replay):
            return None
        rec = self.replay[self.i]
        if rec["key"] != key:
            raise ResumeDiverged(
                f"{RESUME_DIVERGED}: call {self.i} ({where}) differs from the logged "
                f"{rec.get('agent')}@{rec.get('lane')} tick {rec.get('tick')}")
        self.i += 1
        self.replayed += 1
        return rec

    def went_live(self, tick) -> None:
        if not self._announced_live:
            self._announced_live = True
            self._write({"event": "live", "tick": tick, "replayed": self.replayed}, sync=True)

    def started(self, **fields) -> None:
        self._write({"event": "start", **fields}, sync=False)    # screen only; never replayed

    def done(self, **fields) -> None:
        self.live += 1
        self._write({"event": "done", **fields}, sync=True)      # on disk before the agent sees it

    def summary(self) -> dict:
        return {"sessions": self.n_sessions, "replayed_calls": self.replayed,
                "live_calls": self.live, "resumed": self.replayed > 0,
                "calls_recorded_failed_after_server_death": self.crash_recorded}

    def close(self) -> None:
        if not self.f.closed:
            self.f.close()


class JournalBackend:
    """Sits between one lane and its real backend, so the lane's own accounting and
    everything above it see exactly the replies they would have seen."""

    def __init__(self, inner, lane: str, journal: CallJournal, scheduler=None):
        self.inner, self.lane, self.journal, self.scheduler = inner, lane, journal, scheduler

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def _job(self) -> tuple:
        job = getattr(self.scheduler, "current", None)
        return getattr(job, "agent", None), getattr(job, "evidence_tick", None)

    def generate(self, prompt, role="generic", max_tokens=512, mock_hint=None, **extra):
        grammar = extra.get("grammar")
        agent, tick = self._job()
        key = call_key(self.lane, role, max_tokens, grammar, prompt)
        logged = self.journal.next_logged(key, f"{agent}@{self.lane} tick {tick}")
        if logged is not None:
            return LLMReply(**logged["reply"])
        self.journal.went_live(tick)
        model = getattr(self.inner, "model_file", getattr(self.inner, "name", "?"))
        n = self.journal.deaths.get((agent, self.lane, tick), 0)
        if n >= MAX_DEATHS_PER_CALL:
            self.journal.deaths.pop((agent, self.lane, tick))
            self.journal.crash_recorded += 1
            reply = LLMReply(text="", status="error", backend=self.lane, model=model,
                             error=f"server died on this exact call {n} times; recorded as a failed call",
                             prefill_tokens=None, decode_tokens=None, ttft_ms=None, decode_ms=None)
            self.journal.started(agent=agent, lane=self.lane, tick=tick, role=role, model=model,
                                 prompt=prompt, grammar=grammar)
            self.journal.done(key=key, agent=agent, lane=self.lane, tick=tick, role=role, model=model,
                              prompt=prompt, grammar=grammar, crash_recorded=True,
                              reply=dataclasses.asdict(reply))
            return reply
        self.journal.started(agent=agent, lane=self.lane, tick=tick, role=role, model=model,
                             prompt=prompt, grammar=grammar)
        reply = self.inner.generate(prompt, role=role, max_tokens=max_tokens,
                                    mock_hint=mock_hint, **extra)
        if reply.status != "ok":
            err = str(reply.error)
            url = getattr(self.inner, "url", None)
            if err.startswith("connection:") or (url and not _lane_healthy(url)):
                raise BoardConnectionLost(
                    f"Connection refused: {agent}@{self.lane} tick {tick}: "
                    f"{reply.status} {err[:160]} (board connection lost; not scored)")
        self.journal.done(key=key, agent=agent, lane=self.lane, tick=tick, role=role,
                          model=model, prompt=prompt, reply=dataclasses.asdict(reply))
        return reply

    def close(self) -> None:
        self.inner.close()


def wrap_lane_with(journal: CallJournal):
    """The `wrap_lane` hook of bench.harness.run_episode."""
    def wrap(lane, scheduler):
        return JournalBackend(lane.backend, lane.name, journal, scheduler)
    return wrap
