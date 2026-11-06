#!/usr/bin/env python3
"""
Laya GGUF parity (reports/laya_l1.md, Track B2): the same decider requests sent to a
llama-server /v1/systemone serving the converted GGUF, against the PyTorch Laya
answers saved by bench.laya_score (normal pass). Stdlib only.

    .venv/bin/python -m bench.laya_parity URL SET [SET ...] [--tag primary] [--limit N] [--label F16]

Per set: unique prompts compared, top answer identical, max and median |dp| over
every option, input-token count identical, mean latency. Writes
results/laya_l1/parity_<label>.json. Pass rule (pre-registered): the top answer is
identical on every compared request.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "results" / "laya_l1"


def post(url: str, body: str, timeout: float = 300.0) -> dict:
    req = urllib.request.Request(f"{url.rstrip('/')}/v1/systemone", data=body.encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def compare(ref: dict, got: dict) -> dict:
    """Top answer and |dp| per question of one request."""
    same, dps = True, []
    for qid, a in ref["answers"].items():
        b = got["answers"].get(qid) or {}
        if a["type"] == "noul":
            dps.append(abs(a["noul"] - float(b.get("noul", -9))))
            same &= (a["noul"] >= 0.5) == (float(b.get("noul", -9)) >= 0.5)
            continue
        pb = b.get("probabilities") or {}
        same &= a["choice"] == b.get("choice")
        dps += [abs(p - float(pb.get(k, -9))) for k, p in a["probabilities"].items()]
    return {"same_top": same, "max_dp": max(dps) if dps else 0.0, "dps": dps}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Laya GGUF vs PyTorch parity")
    ap.add_argument("url")
    ap.add_argument("sets", nargs="+")
    ap.add_argument("--tag", default="primary")
    ap.add_argument("--limit", type=int, default=0, help="unique prompts per set (0 = all)")
    ap.add_argument("--label", required=True)
    a = ap.parse_args(argv)
    out = {"url": a.url, "label": a.label, "sets": {}}
    for s in a.sets:
        reqs = {(r["episode"], r["tick"]): r["prompt"]
                for r in map(json.loads, (BASE / "requests" / f"{s}.jsonl").open())}
        refs = {}
        for r in map(json.loads, (BASE / "answers" / f"{s}__{a.tag}__normal.jsonl").open()):
            p = reqs[(r["episode"], r["tick"])]
            refs.setdefault(p, r["reply"])
        prompts = list(refs)[: a.limit or None]
        rows, ms, tok_same, worst = [], [], 0, None
        for p in prompts:
            t0 = time.perf_counter()
            got = post(a.url, p)
            ms.append((time.perf_counter() - t0) * 1000)
            c = compare(refs[p], got)
            tok_same += (got.get("usage") or {}).get("input_tokens") == refs[p]["usage"]["prompt_tokens"]
            rows.append(c)
            if worst is None or c["max_dp"] > worst[0]:
                worst = (c["max_dp"], p[:160])
        alldp = [d for r in rows for d in r["dps"]]
        res = {"compared": len(rows), "same_top": sum(r["same_top"] for r in rows),
               "max_dp": max(alldp) if alldp else None,
               "median_dp": statistics.median(alldp) if alldp else None,
               "same_input_tokens": tok_same, "mean_ms": statistics.mean(ms) if ms else None,
               "worst_request_head": worst[1] if worst else None}
        out["sets"][s] = res
        print(f"{a.label} {s}: top answer identical {res['same_top']}/{res['compared']}, "
              f"max |dp| {res['max_dp']:.4f}, median |dp| {res['median_dp']:.5f}, "
              f"input tokens identical {tok_same}/{len(rows)}, {res['mean_ms']:.0f} ms per request", flush=True)
    (BASE / f"parity_{a.label}.json").write_text(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
