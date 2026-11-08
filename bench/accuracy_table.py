#!/usr/bin/env python3
"""
Accuracy-fixes: one table per run of the dev sets of the three plants (mock).

On the mock backend the multi-agent v3 arm publishes the retrieval order (the
"line-1 rule": the board's Llama was shown to do the same, reports/b3_*), so
this table measures the CODE's diagnosis -- exactly what the accuracy-fixes
steps change. Mock numbers are not agent results.

    python bench/accuracy_table.py --out DIR [--label NAME] [--plants boiler,cranfield,tep]
                                   [--plus configs/x.yaml]   (appended to every plant's overlay)

Runs run_demo.py for each plant into DIR/<plant>/ and prints one row per plant.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLANTS = {
    "boiler": ("configs/v3.yaml", "data/episodes_dev"),
    "cranfield": ("configs/v3.yaml,configs/cranfield.yaml", "data/episodes_cranfield_dev"),
    "tep": ("configs/v3.yaml,configs/tep.yaml", "data/episodes_tep_dev"),
}
# the reporting sets: run ONCE per phase to report, never to decide (CLAUDE.md)
REPORT = {"boiler": "data/episodes", "cranfield": "data/episodes_cranfield", "tep": "data/episodes_tep"}


def run(plant: str, out: Path, extra: list[str], plus: str = "", which: str = "dev",
        data_root: Path = ROOT) -> dict:
    ov, eps = PLANTS[plant]
    eps = str(data_root / (REPORT[plant] if which == "report" else eps))
    ov = f"{ov},{plus}" if plus else ov
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = [sys.executable, "run_demo.py", "--backend", "mock", "--arch", "multi", "--overlay", ov,
           "--all", "--episodes-dir", eps, "--tag", which, "--out", str(out / plant)] + extra
    r = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"{plant}: run_demo failed\n{r.stderr[-2000:]}")
    return json.loads((out / plant / f"summary_mock_{which}.json").read_text())["summary"]


def row(plant: str, s: dict) -> str:
    q = s["Q2_library"]
    f = lambda x, d=3: "-" if x is None else f"{x:.{d}f}"
    return (f"{plant:10s} line-1 {f(q['group_top1'])}  case top-1 {f(q['top1'])}  in-fault {f(s.get('Q2_group_top1_in_fault'))}  "
            f"belief {f(q['belief_group'])}  | detect {f(s.get('Q7_detection_rate'))}  "
            f"FA before {f(s.get('Q7_far_before_fault'))}  FP/h normal {f(s.get('Q5_fp_per_hour'), 2)}  "
            f"AI rate {f(s.get('S4_llm_invocation_rate'))}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--label", default="")
    ap.add_argument("--plants", default="boiler,cranfield,tep")
    ap.add_argument("--plus", default="")
    ap.add_argument("--set", default="dev", choices=("dev", "report"))
    ap.add_argument("--data-root", type=Path, default=ROOT, help="where the (gitignored) episode folders are")
    a, extra = ap.parse_known_args()
    print(f"== {a.label or a.out.name}")
    res = {}
    for p in a.plants.split(","):
        res[p] = run(p, a.out, extra, a.plus, a.set, a.data_root)
        print(row(p, res[p]), flush=True)
    (a.out / "table.json").write_text(json.dumps(
        {p: {k: v for k, v in s.items() if k.startswith(("Q2", "Q5", "Q7", "S4"))} for p, s in res.items()},
        indent=1))


if __name__ == "__main__":
    main()
