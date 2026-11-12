#!/usr/bin/env python3
"""
=============================================================================
 PAPER B ITEM 2 SCORE  --  each published fix against the no-model run
 (reports/paperB_item2_prereg.md, "Measures")
=============================================================================

    .venv/bin/python bench/paperB_score.py <arm folder> <no-model folder> [--base <base folder>]
                                           [--boot 2000] [--seed 20261111] [--json out.json]

<arm folder>: a board run of one arm (results/benchmarks/paperB_<arm>_<system>_<plant>).
<no-model folder>: the same episodes on the mock backend (retrieval order; NOT an agent result).
--base: the system's run without the fix (for "what the arm changed").

Accuracy (the accuracy-fixes rule): group top-1 inside the fault windows where the
episode has them (T2 group_top1_in_fault), else group top-1 from onset (the
boiler); case top-1 beside it. Headline: the MEAN OVER EPISODES of each
episode's share (the convention of the earlier tables, e.g. Cranfield v3 0.524);
pooled over ticks beside it (a long episode weighs more there: Cranfield v3
pooled is 0.327). The difference arm - no-model, and its 95% interval from
resampling EPISODES (paired: an episode's arm and no-model runs stay together). Echo from
bench.echo_test.scan, changes from bench.echo_test.changed, cost from the run
files (model calls and model seconds per tick, per lane).
=============================================================================
"""

from __future__ import annotations

import argparse
import gzip
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bench import echo_test as E  # noqa: E402


def episode_scores(folder: Path) -> dict[str, dict]:
    """{run stem: right / n for the accuracy rule, and for case top-1}."""
    out = {}
    for f in sorted(Path(folder).glob("*.summary.json")):
        t2 = (json.loads(f.read_text()).get("evaluation") or {}).get("T2_root_cause") or {}
        n_in = t2.get("n_scored_in_fault") or 0
        if n_in:
            g, n = t2.get("group_top1_in_fault"), n_in
        else:
            g, n = t2.get("group_top1"), t2.get("n_scored") or 0
        if not n or g is None:
            continue
        out[f.name.replace(".summary.json", "")] = {
            "right": round(g * n), "n": n,
            "case_right": round((t2.get("top1") or 0) * (t2.get("n_scored") or 0)), "case_n": t2.get("n_scored") or 0}
    return out


def _pooled(rows, key="right", n="n"):
    tot = sum(r[n] for r in rows)
    return sum(r[key] for r in rows) / tot if tot else None


def _mean(rows, key="right", n="n"):
    xs = [r[key] / r[n] for r in rows if r[n]]
    return sum(xs) / len(xs) if xs else None


def compare(arm: Path, nomodel: Path, boot: int = 2000, seed: int = 20261111) -> dict:
    a, b = episode_scores(arm), episode_scores(nomodel)
    common = sorted(set(a) & set(b))
    out = {"episodes": len(common), "only_in_arm": sorted(set(a) - set(b)), "only_in_nomodel": sorted(set(b) - set(a))}
    if not common:
        return out
    A, B = [a[k] for k in common], [b[k] for k in common]
    out.update(arm=round(_mean(A), 4), nomodel=round(_mean(B), 4),
               arm_pooled=round(_pooled(A), 4), nomodel_pooled=round(_pooled(B), 4),
               arm_case=round(_mean(A, "case_right", "case_n") or 0, 4),
               nomodel_case=round(_mean(B, "case_right", "case_n") or 0, 4))
    out["diff"] = round(out["arm"] - out["nomodel"], 4)
    rng = random.Random(seed)
    diffs = []
    for _ in range(boot):
        idx = [rng.randrange(len(common)) for _ in common]
        pa, pb = _mean([A[i] for i in idx]), _mean([B[i] for i in idx])
        if pa is not None and pb is not None:
            diffs.append(pa - pb)
    diffs.sort()
    if diffs:
        out["diff_95"] = [round(diffs[int(0.025 * (len(diffs) - 1))], 4), round(diffs[int(0.975 * (len(diffs) - 1))], 4)]
    return out


def cost(folder: Path) -> dict:
    calls, secs, ticks = {}, {}, 0
    for f in sorted(Path(folder).glob("*.run.json.gz")):
        run = json.loads(gzip.decompress(f.read_bytes()))
        ticks += len(run.get("assessments") or [])
        for a in run.get("assessments") or []:
            for e in a.get("envelopes") or []:
                ln = e.get("backend")
                if ln in (None, "mock", "code"):
                    continue
                for c in e.get("calls") or []:
                    calls[ln] = calls.get(ln, 0) + 1
                    secs[ln] = secs.get(ln, 0.0) + (c.get("latency_ms") or 0) / 1000
    return {"ticks": ticks, "calls_per_tick": {k: round(v / ticks, 3) for k, v in calls.items()} if ticks else {},
            "model_s_per_tick": {k: round(v / ticks, 3) for k, v in secs.items()} if ticks else {}}


def score(arm: Path, nomodel: Path, base: Path | None = None, boot: int = 2000, seed: int = 20261111) -> dict:
    out = {"arm": str(arm), "nomodel": str(nomodel), "accuracy": compare(arm, nomodel, boot, seed),
           "cost": cost(arm)}
    try:
        out["echo"] = [{k: r[k] for k in ("lane", "model", "n", "line1", "chance", "deviations", "dev_right",
                                          "dev_random")} for r in E.scan([str(arm)])]
    except SystemExit as e:                     # a reporting episode: refused, as the dev rule says
        out["echo"] = f"refused: {e}"
    if base is not None:
        out["changed_vs_base"] = {k: v for k, v in E.changed(str(arm), str(base)).items()
                                  if k in ("scored", "scored_differ", "differ_model_right", "differ_nomodel_right",
                                           "share_scored_differ")}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("arm")
    ap.add_argument("nomodel")
    ap.add_argument("--base", default=None)
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261111)
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)
    res = score(Path(a.arm), Path(a.nomodel), Path(a.base) if a.base else None, a.boot, a.seed)
    print("No-model numbers come from the mock backend: retrieval order, not an agent result.")
    print(json.dumps(res, indent=1))
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
