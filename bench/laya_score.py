#!/usr/bin/env python3
"""
Score saved decider requests with Laya (reports/laya_l1.md, Track A4). Runs in
.venv-laya. Uses bench.laya_serve.Laya.answer, the code path the HTTP server
serves, in-process (no HTTP per request).

    .venv-laya/bin/python -m bench.laya_score SET [SET ...]
        [--checkpoint convaiinnovations/laya] [--subfolder S] [--revision SHA]
        [--tag primary] [--passes normal,shuffled]

Reads results/laya_l1/requests/<SET>.jsonl (bench.decider_requests) and writes
results/laya_l1/answers/<SET>__<tag>__<pass>.jsonl, one line per request:
  episode, tick, reply (bev-decide shape, plus truncated / options_cut / layout).
Resumable: requests already in the output are skipped. Identical prompts are
answered once per pass (Laya is deterministic on CPU; checked by the repeat test
in the report).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from bench.laya_serve import Laya  # noqa: E402
from bench.system_one import SEED  # noqa: E402

OUT = ROOT / "results" / "laya_l1"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="score decider requests with Laya")
    ap.add_argument("sets", nargs="+")
    ap.add_argument("--checkpoint", default="convaiinnovations/laya")
    ap.add_argument("--subfolder", default=None)
    ap.add_argument("--revision", default=None)
    ap.add_argument("--tag", default="primary")
    ap.add_argument("--passes", default="normal,shuffled")
    a = ap.parse_args(argv)
    model = Laya(a.checkpoint, a.subfolder, a.revision, "cpu")
    print(f"{model.name}: {model.layout} layout", flush=True)
    (OUT / "answers").mkdir(parents=True, exist_ok=True)
    cache: dict[tuple, dict] = {}
    for p in a.passes.split(","):
        seed = None if p == "normal" else SEED
        for s in a.sets:
            src = OUT / "requests" / f"{s}.jsonl"
            dst = OUT / "answers" / f"{s}__{a.tag}__{p}.jsonl"
            done = set()
            if dst.exists():
                done = {(r["episode"], r["tick"]) for r in map(json.loads, dst.open())}
            rows = [json.loads(l) for l in src.open()]
            t0, n = time.perf_counter(), 0
            with dst.open("a", encoding="utf-8") as f:
                for r in rows:
                    key = (r["episode"], r["tick"])
                    if key in done:
                        continue
                    ck = (r["prompt"], seed)
                    if ck not in cache:
                        cache[ck] = model.answer(r["prompt"], seed)
                        n += 1
                    f.write(json.dumps({"episode": r["episode"], "tick": r["tick"],
                                        "reply": cache[ck]}, ensure_ascii=False) + "\n")
            dt = time.perf_counter() - t0
            print(f"{s} {p}: {len(rows)} requests, {n} new model calls, {dt:.0f} s"
                  f"{f' ({dt / n * 1000:.0f} ms per call)' if n else ''}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
