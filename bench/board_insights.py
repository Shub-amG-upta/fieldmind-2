#!/usr/bin/env python3
"""
What a board run says about the LLM, beyond its accuracy (reports/accuracy_fixes.md, fix 1).

    python -m bench.board_insights results/benchmarks/<run> [<run> ...] [--out insights.json]

For each run folder (bench/benchmark.py output: <episode>_multi.run.json.gz, *.calls.jsonl.gz),
and its mock dry run if present (results/benchmarks_mock/<same name>, the line-1 rule on the same
episodes; or --mock-root):

  accuracy        group / case top-1 inside the fault (bench.evaluator), board and mock
  agree_mock      share of scored ticks whose published rank-1 equals the mock's
  line1_follow    share of diagnostician answers whose first case is shown line 1
  copy_21         share whose case order is exactly [2, 1] (the order of both prompt examples)
  deviate_right   when the first case is NOT line 1: share where it is the true case
  true_shown      share of in-fault ticks with a model call where some side's prompt showed the true case
  guard_cut_true  such ticks where the token guard cut the true case from a prompt
  one_case        calls showing one case: share answered [1] (vs [] or a failure)
  cost            diagnostician calls, prompt and decode tokens, latency; wall time per tick;
                  skips (clear_skip, empty_skip) from the bev stats

Board numbers are agent results only for the arm and plant they were run on. Energy is not read
here (null unless the device meter logged it).
"""

from __future__ import annotations

import argparse
import gzip
import json
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _runs(folder: Path) -> dict[str, dict]:
    out = {}
    for p in sorted(folder.glob("*_multi.run.json.gz")):
        with gzip.open(p, "rt") as f:
            r = json.load(f)
        out[r["episode_id"]] = r
    return out


def _calls(folder: Path) -> list[dict]:
    out = []
    for p in sorted(folder.glob("*.calls.jsonl.gz")):
        with gzip.open(p, "rt") as f:
            for line in f:
                d = json.loads(line)
                if d.get("event") == "done":
                    out.append(d)
    return out


def _reply(d: dict) -> dict:
    r = d.get("reply")
    if isinstance(r, dict):
        return r
    try:                                     # older journals stored the reply's repr
        import ast
        return ast.literal_eval(r) if isinstance(r, str) else {}
    except (ValueError, SyntaxError):
        return {}


def _lines(answer) -> list[int]:
    """Case lines of a diagnostician answer, in its order (compact log, expanded form)."""
    out = []
    for x in (answer or {}).get("r") or []:
        v = x[0] if isinstance(x, (list, tuple)) else x
        if isinstance(v, int):
            out.append(v)
    return out


def _in_fault(run: dict, tick: int) -> bool:
    gt = run["ground_truth"]
    tk = float(gt.get("tick_period_s", 30.0))
    wins = gt.get("fault_windows")
    if wins:
        t = (tick + 1) * tk
        return any(s <= t < e for s, e in wins)
    return tick * tk >= (gt.get("fault_onset_t") or 0)


def _accuracy(runs: dict) -> dict:
    from bench.evaluator import aggregate, evaluate
    if not runs:
        return {}
    s = aggregate([evaluate(r) for r in runs.values()])
    return {"group_top1_in_fault": s.get("Q2_group_top1_in_fault"),
            "group_top1": s["Q2_library"]["group_top1"], "case_top1": s["Q2_library"]["top1"],
            "belief_group": s["Q2_library"]["belief_group"],
            "detection": s.get("Q7_detection_rate"), "far_before_fault": s.get("Q7_far_before_fault"),
            "fp_per_hour": s.get("Q5_fp_per_hour")}


def _agree(board: dict, mock: dict) -> float | None:
    n = same = 0
    for ep, r in board.items():
        m = mock.get(ep)
        if m is None:
            continue
        mt = {a["tick"]: a for a in m["assessments"]}
        for a in r["assessments"]:
            b = mt.get(a["tick"])
            if b is None or not a["hypotheses"] or not b["hypotheses"] or not _in_fault(r, a["tick"]):
                continue
            n += 1
            same += a["hypotheses"][0]["case_ref"] == b["hypotheses"][0]["case_ref"]
    return round(same / n, 3) if n else None


def insights(folder: Path, mock_folder: Path | None) -> dict:
    runs = _runs(folder)
    calls = _calls(folder)
    n = follow = copy = dev = dev_right = shown_true = n_fault = cut_true = 0
    one = Counter()
    for r in runs.values():
        tgt = r["ground_truth"].get("root_cause_id")
        for a in r["assessments"]:
            diag = [c for c in (a.get("multi") or {}).get("compact", [])
                    if c.get("agent") == "diagnostician" and c.get("case_ids") is not None]
            if diag and _in_fault(r, a["tick"]) and tgt not in (None, "NONE"):
                # per tick, over the sides asked (each side is shown only its own cases)
                n_fault += 1
                shown_true += any(tgt in c["case_ids"] for c in diag)
                cut_true += any(tgt in (c.get("guard_dropped") or []) for c in diag)
            for c in diag:
                ids, lines = c["case_ids"], _lines(c.get("answer"))
                if len(ids) == 1:
                    one["[1]" if lines[:1] == [1] else "[]" if c.get("answer") else "failed"] += 1
                if not lines or len(ids) < 2:
                    continue                 # follow / copy only mean something with a choice
                n += 1
                follow += lines[0] == 1
                copy += lines[:2] == [2, 1] and len(lines) == 2
                if lines[0] != 1:
                    dev += 1
                    dev_right += 0 < lines[0] <= len(ids) and ids[lines[0] - 1] == tgt
    diag = [c for c in calls if str(c.get("role", "")).startswith("diag")]
    rep = [_reply(c) for c in diag]
    lat = [x.get("latency_ms") for x in rep if x.get("latency_ms") is not None]
    bev = Counter()
    for r in runs.values():
        per = ((r.get("multi") or {}).get("bev") or {}).get("per_idea") or {}
        for idea in ("clear_skip", "empty_skip"):
            bev[idea] += (per.get(idea) or {}).get("used", 0)
    ticks = sum(r["n_ticks"] for r in runs.values())
    wall = sum(r.get("wall_clock_s") or 0 for r in runs.values())
    mock = _runs(mock_folder) if mock_folder and mock_folder.exists() else {}
    out = {"run": folder.name, "episodes": len(runs), "ticks": ticks,
           "accuracy_board": _accuracy(runs),
           "accuracy_mock": _accuracy({k: v for k, v in mock.items() if k in runs}) if mock else None,
           "agree_mock": _agree(runs, mock) if mock else None,
           "answers_with_a_choice": n,
           "line1_follow": round(follow / n, 3) if n else None,
           "copy_21": round(copy / n, 3) if n else None,
           "deviations": dev, "deviate_right": round(dev_right / dev, 3) if dev else None,
           "true_shown": round(shown_true / n_fault, 3) if n_fault else None,
           "guard_cut_true": cut_true,
           "one_case": dict(one),
           "cost": {"diag_calls": len(diag),
                    "prompt_tokens": sum(x.get("prefill_tokens") or 0 for x in rep),
                    "decode_tokens": sum(x.get("decode_tokens") or 0 for x in rep),
                    "diag_latency_ms_median": round(statistics.median(lat), 1) if lat else None,
                    "wall_s_per_tick": round(wall / ticks, 2) if ticks else None,
                    "skips": dict(bev)}}
    return out


def _fmt(x, d=3):
    return "-" if x is None else (f"{x:.{d}f}" if isinstance(x, float) else str(x))


def table(rows: list[dict]) -> str:
    h = ("| run | eps | acc board (mock) | case top-1 board (mock) | agree w/ mock | line-1 follow | "
         "copy [2,1] | deviations right | true case shown | guard cut true | 1-case answers | "
         "diag calls | decode tok | s/tick |")
    out = [h, "|" + "---|" * (h.count("|") - 1)]
    for r in rows:
        b, m = r["accuracy_board"], r["accuracy_mock"] or {}
        acc = b.get("group_top1_in_fault") if b.get("group_top1_in_fault") is not None else b.get("group_top1")
        macc = m.get("group_top1_in_fault") if m.get("group_top1_in_fault") is not None else m.get("group_top1")
        out.append(f"| {r['run']} | {r['episodes']} | {_fmt(acc)} ({_fmt(macc)}) | "
                   f"{_fmt(b.get('case_top1'))} ({_fmt(m.get('case_top1'))}) | {_fmt(r['agree_mock'])} | "
                   f"{_fmt(r['line1_follow'])} | {_fmt(r['copy_21'])} | "
                   f"{_fmt(r['deviate_right'])} of {r['deviations']} | {_fmt(r['true_shown'])} | "
                   f"{r['guard_cut_true']} | {r['one_case']} | {r['cost']['diag_calls']} | "
                   f"{r['cost']['decode_tokens']} | {_fmt(r['cost']['wall_s_per_tick'], 2)} |")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+", type=Path)
    ap.add_argument("--mock-root", type=Path, default=ROOT / "results/benchmarks_mock")
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    rows = [insights(p, a.mock_root / p.name) for p in a.runs]
    print(table(rows))
    if a.out:
        a.out.write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
