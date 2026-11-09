#!/usr/bin/env python3
"""
Laya on the exact bev-idea requests a board run sent to bev-decider (reports/laya_l1.md,
Track A5, per-idea comparison). Runs in .venv-laya.

    .venv-laya/bin/python -m bench.laya_pair_journal RUN_DIR [RUN_DIR ...] --label NAME [--revision SHA]

RUN_DIR holds a board run's *.calls.jsonl.gz journals (bench/call_journal.py), whose
decider-role entries for agents `bev_<idea>` carry the request verbatim and bev's reply.
Each request is answered by Laya (bench.laya_serve.Laya.answer, normal order) and the two
answers are compared question by question: same top choice (choice questions), same side
of 0.5 (yes/no questions). There is no ground truth for these questions; agreement is
descriptive only. Writes results/laya_l1/pairs/<NAME>.jsonl and prints the summary.
"""

from __future__ import annotations

import argparse
import collections
import glob
import gzip
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from bench.laya_serve import Laya  # noqa: E402

OUT = ROOT / "results" / "laya_l1" / "pairs"


def kind(qid: str) -> str:
    """Question family from its id: cite_<case>, sep, note<i>, act_<id>, claim<i>, ..."""
    return re.sub(r"[_\d].*$", "", qid) or qid


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Laya vs bev on a board run's bev-idea requests")
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--label", required=True)
    ap.add_argument("--checkpoint", default="convaiinnovations/laya")
    ap.add_argument("--revision", default=None)
    a = ap.parse_args(argv)
    model = Laya(a.checkpoint, None, a.revision, "cpu")
    OUT.mkdir(parents=True, exist_ok=True)
    agree = collections.defaultdict(lambda: [0, 0])
    seen = set()
    with (OUT / f"{a.label}.jsonl").open("w", encoding="utf-8") as f:
        for d in a.runs:
            for jf in sorted(glob.glob(os.path.join(d, "*.calls.jsonl.gz"))):
                ep = os.path.basename(jf).split(".calls")[0]
                for line in gzip.open(jf, "rt", encoding="utf-8"):
                    r = json.loads(line)
                    if r.get("event") != "done" or not str(r.get("agent", "")).startswith("bev_"):
                        continue
                    if r.get("key") in seen or r["reply"].get("status", "ok") != "ok":
                        continue
                    seen.add(r.get("key"))
                    bev = json.loads(r["reply"]["text"])["answers"]
                    lay = model.answer(r["prompt"], None)["answers"]
                    rows = {}
                    for qid, b in bev.items():
                        l = lay.get(qid) or {}
                        if b.get("type") == "noul":
                            same = (b["noul"] >= 0.5) == (l.get("noul", -1) >= 0.5)
                        else:
                            same = b.get("choice") == l.get("choice")
                        k = f"{r['agent'][4:]}:{kind(qid)}"
                        agree[k][0] += same
                        agree[k][1] += 1
                        rows[qid] = {"bev": b, "laya": l, "same": same}
                    f.write(json.dumps({"episode": ep, "tick": r.get("tick"), "agent": r["agent"],
                                        "answers": rows}, ensure_ascii=False) + "\n")
    print(f"{a.label}: {len(seen)} requests")
    for k in sorted(agree):
        s, n = agree[k]
        print(f"  {k:24s} same answer {s}/{n} ({s / n * 100:.1f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
