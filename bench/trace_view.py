"""
`--trace`: a scrolling terminal view of the run. Each model call as it starts and
finishes (lane, agent, model, time, tokens, the answer itself) and one summary per
tick. It only reads the two log files the run writes, so it cannot affect a result,
and the same text can be piped to a file with `tee`.

The running score is the monitor's per-tick marks (bench.stage_monitor_multi); the
figures to report are the evaluator's, in the episode's summary.json.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from bench.stage_monitor_multi import episode_dir, load_truth, tick_accuracy

ANSWER_CHARS = 170


def _model(name) -> str:
    n = str(name or "?").lower()
    for key, short in (("llama-3.2-3b", "Llama3B"), ("gemma-3-1b", "Gemma1B"), ("qwen3-1.7b", "Qwen1.7B"),
                       ("qwen2.5-0.5b", "Qwen0.5B"), ("mock", "mock")):
        if key in n:
            return short
    return str(name)[:12]


def call_started(r: dict) -> str:
    return f"  {str(r.get('lane')).upper():3s} {str(r.get('agent')):13s} {_model(r.get('model')):8s} running ..."


def call_done(r: dict) -> str:
    rep = r.get("reply") or {}
    text = " ".join(str(rep.get("text") or "").split())
    answer = text[:ANSWER_CHARS] + ("..." if len(text) > ANSWER_CHARS else "")
    status = "" if rep.get("status") == "ok" else f" {str(rep.get('status')).upper()}: {rep.get('error')}"
    return (f"  {str(r.get('lane')).upper():3s} {str(r.get('agent')):13s} {_model(r.get('model')):8s} "
            f"{(rep.get('latency_ms') or 0) / 1000:5.1f}s {rep.get('prefill_tokens')}->"
            f"{rep.get('decode_tokens')}t{status}  answer: {answer}")


class Score:
    def __init__(self, truth):
        self.truth, self.n, self.pub, self.bel = truth, 0, 0, 0

    def line(self, d: dict) -> str:
        m = d.get("multi") or {}
        hyp = d.get("hypotheses") or []
        code = m.get("hard_ms")
        head = (f"t{d['tick']:04d} {d['state']:<11s} {d['triage']:<11s} "
                f"code {code:.0f}ms" if code is not None else
                f"t{d['tick']:04d} {d['state']:<11s} {d['triage']:<11s}")
        if not hyp:
            return f"{head} | no ranking published | saved"
        a = tick_accuracy(d, self.truth) if self.truth else {}
        top = hyp[0]
        out = f"{head} | PUBLISHED {top.get('case_ref') or top.get('cause', '')[:30]} conf {d.get('confidence', 0):.2f}"
        if a.get("scored"):
            self.n += 1
            self.pub += a["pub"] == "✓"
            self.bel += a["bel"] == "✓"
            out += (f" | truth {self.truth['target']} pub {a['pub']} belief {a['bel']}"
                    f" | so far: published {self.pub}/{self.n}, belief {self.bel}/{self.n}")
        elif a.get("pub") == "pre":
            out += " | before the fault, not scored"
        return out + " | saved"


class Tail:
    """New whole lines of a file that may not exist yet."""

    def __init__(self, path: Path, from_end: bool = False):
        self.path, self.pos = path, 0
        if from_end and path.exists():
            self.pos = path.stat().st_size

    def lines(self) -> list[dict]:
        if not self.path.exists():
            return []
        if self.path.stat().st_size < self.pos:   # the episode restarted: a new, shorter file
            self.pos = 0
        with self.path.open("rb") as f:
            f.seek(self.pos)
            data = f.read()
        end = data.rfind(b"\n") + 1
        self.pos += end
        out = []
        for x in data[:end].decode("utf-8", "replace").splitlines():
            try:
                out.append(json.loads(x))
            except ValueError:                   # read across a restart: a viewer never stops a run
                pass
        return out


def follow(r, out=None) -> None:
    """Prints (to the file `out` if given) until the runner thread ends."""
    import builtins

    def print(*a, **k):                         # noqa: A001
        builtins.print(*a, **{**k, "file": out} if out is not None else k)

    stem, ticks, calls, score, quiet = None, None, None, None, False

    def drain():
        nonlocal quiet
        if ticks is None:
            return
        tick_lines = ticks.lines()              # read first, so a tick's calls print before it
        for c in calls.lines():
            ev = c.get("event")
            if ev == "session" and c.get("replay"):
                quiet = True
                print(f"  RESUMING: replaying {c['replay']} saved answers without the board "
                      f"(session {c['n']})", flush=True)
            elif ev == "live":
                quiet = False
                print(f"  LIVE again from tick {c.get('tick')} ({c.get('replayed')} answers replayed)",
                      flush=True)
            elif ev == "start":
                print(call_started(c), flush=True)
            elif ev == "done":
                print(call_done(c), flush=True)
        for d in tick_lines:
            line = score.line(d)                # always, so the score covers replayed ticks
            if not quiet:
                print(line, flush=True)

    while r.is_alive():
        with r.lock:
            cur = r.current
        if cur and cur["stem"] != stem:
            drain()
            stem = cur["stem"]
            truth = load_truth(episode_dir(cur["ep"]))
            print(f"\n=== {cur['ep']}" + (f"  true cause {truth['target']} "
                  f"(fault from {truth['onset']:.0f} s)" if truth else ""), flush=True)
            ticks = Tail(cur["ticks"])
            calls = Tail(cur["ticks"].with_name(f"{stem}.calls.jsonl"), from_end=True)
            score, quiet = Score(truth), False
        drain()
        time.sleep(0.25)
    drain()
