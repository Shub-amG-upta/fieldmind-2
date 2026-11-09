#!/usr/bin/env python3
"""
Collect the decider's exact /v1/systemone requests from saved runs, with what is
needed to score any answer to them (reports/laya_l1.md, Track A4).

    .venv/bin/python -m bench.decider_requests SET SOURCE [SOURCE ...] --out FILE

SOURCE is either
  * a benchmark test folder (results/benchmarks/<test>/): one <ep>_*.run.json.gz
    and <ep>_*.summary.json per episode (board runs, e.g. bev3_armB), or
  * a run_demo output folder: runs_*.json (a list of runs) and summary_*.json.
Runs must have been made with --log-prompts (decider envelopes carry `prompt`);
board runs always log them.

One JSON line per decider request:
  set, source, episode, tick, prompt (the request body, verbatim), offered (the
  option keys in offered order), n_belief (offered[:n_belief] came from belief),
  belief_top, retriever_tops (line 1 of each diagnostician prompt of the same
  evidence tick), answer_backend + answer_choice (the answer the run got: bev on
  a board run, the mock on a mock run), true_group, heldout, after_onset.

Nothing here reads Laya; it only fixes the questions every model is scored on.
"""

from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from bench.system_one import after_onset  # noqa: E402


def _load(path: str):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def runs_and_truth(source: str) -> list[tuple[dict, dict]]:
    """[(run, T2 block of its summary)] for every episode in `source`."""
    out = []
    bench_runs = sorted(glob.glob(os.path.join(source, "*.run.json.gz")))
    if bench_runs:
        for f in bench_runs:
            s = _load(f.replace(".run.json.gz", ".summary.json"))
            out.append((_load(f), s["evaluation"].get("T2_root_cause", {})))
        return out
    runs = sorted(glob.glob(os.path.join(source, "runs_*.json")))
    sums = sorted(glob.glob(os.path.join(source, "summary_*.json")))
    if len(runs) != 1 or len(sums) != 1:
        raise SystemExit(f"{source}: expected one runs_*.json and one summary_*.json")
    t2 = {e["episode_id"]: e.get("T2_root_cause", {}) for e in _load(sums[0])["per_episode"]}
    for run in _load(runs[0]):
        out.append((run, t2.get(run["episode_id"], {})))
    return out


def requests_of(run: dict, t2: dict, set_name: str, source: str) -> list[dict]:
    gt = run["ground_truth"]
    tick_s = float(gt.get("tick_period_s") or 30.0)
    onset = gt.get("fault_onset_t")
    group = [g for g in (t2.get("true_group") or "").split("+") if g]
    line1: dict[int, set] = {}
    n_belief: dict[int, int] = {}
    for a in run["assessments"]:
        for c in (a.get("multi") or {}).get("compact", []):
            if c.get("agent") == "diagnostician" and c.get("case_ids"):
                line1.setdefault(c["evidence_tick"], set()).add(c["case_ids"][0])
            elif c.get("agent") == "decider" and "evidence_tick" in c:
                n_belief[c["evidence_tick"]] = c.get("n_belief")
    rows = []
    for a in run["assessments"]:
        for e in a.get("envelopes") or []:
            if e.get("agent") != "decider":
                continue
            if not e.get("prompt"):
                raise SystemExit(f"{run['episode_id']} tick {e.get('tick')}: decider envelope without "
                                 f"prompt (run made without --log-prompts?)")
            req = json.loads(e["prompt"])
            q = next(iter(req["questions"].values()))
            offered = list(q["criteria"])
            tick = int(e["tick"])
            nb = n_belief.get(tick)
            pay = e.get("payload") or {}
            rows.append({
                "set": set_name, "source": source, "episode": run["episode_id"], "tick": tick,
                "prompt": e["prompt"], "offered": offered, "n_belief": nb,
                "belief_top": offered[0] if (nb is None or nb > 0) else None,
                "retriever_tops": sorted(line1.get(tick, ())),
                "answer_backend": e.get("backend"),
                "answer_choice": pay.get("choice") if e.get("status") == "ok" else None,
                "true_group": group, "heldout": bool(t2.get("heldout")),
                "after_onset": after_onset(tick, tick_s, onset),
            })
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    ap.add_argument("set")
    ap.add_argument("sources", nargs="+")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    rows = []
    for src in a.sources:
        for run, t2 in runs_and_truth(src):
            rows += requests_of(run, t2, a.set, src)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    eps = sorted({r["episode"] for r in rows})
    post = sum(r["after_onset"] for r in rows)
    print(f"{a.set}: {len(rows)} decider requests ({post} after onset) from {len(eps)} episodes -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
