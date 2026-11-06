#!/usr/bin/env python3
"""
Decider pick accuracy of Laya against bev, belief and the retriever on the same
requests (reports/laya_l1.md, Track A5).

    .venv/bin/python -m bench.system_one_eval [--tag primary] [--sets a,b,...] [--out DIR]

Joins results/laya_l1/requests/<set>.jsonl (bench.decider_requests) with
results/laya_l1/answers/<set>__<tag>__{normal,shuffled}.jsonl (bench.laya_score).
Per set: n, pick accuracy (pooled over requests, episode-bootstrap interval) for
Laya, Laya with shuffled options, belief's top, the retriever's top (on the
requests where it exists, with Laya on the same requests), bev where the run got
bev's answer, chance; first-option rates; shuffle invariance; truncation and
options cut. Writes laya_l1_<tag>.md / .json to --out.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from bench.system_one import bootstrap_by_episode, pooled_share  # noqa: E402

BASE = ROOT / "results" / "laya_l1"
DEV_SETS = ("boiler_dev", "cranfield_dev", "tep_board")
ALL_SETS = DEV_SETS + ("boiler_reporting_bev", "cranfield_dev_bev")


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.open(encoding="utf-8")] if path.exists() else []


def build_rows(requests: list[dict], normal: list[dict], shuffled: list[dict]) -> list[dict]:
    """One row per scored request: post-onset, in an episode with a true group."""
    an = {(r["episode"], r["tick"]): r["reply"] for r in normal}
    ash = {(r["episode"], r["tick"]): r["reply"] for r in shuffled}
    rows = []
    for q in requests:
        if not q["after_onset"] or not q["true_group"]:
            continue
        key = (q["episode"], q["tick"])
        if key not in an:
            continue
        g = set(q["true_group"])
        rep = an[key]
        qid = next(iter(rep["answers"]))
        pick = rep["answers"][qid]["choice"]
        offered = q["offered"]
        row = {
            "episode": q["episode"], "tick": q["tick"], "heldout": q["heldout"],
            "laya": pick in g,
            "laya_first": pick == offered[0],
            "belief": (q["belief_top"] in g) if q["belief_top"] else None,
            "retriever": any(c in g for c in q["retriever_tops"]) if q["retriever_tops"] else None,
            "bev": (q["answer_choice"] in g) if q["answer_backend"] == "bev" and q["answer_choice"] else None,
            "chance": sum(c in g for c in offered) / len(offered),
            "first_chance": 1.0 / len(offered),
            "truncated": bool(rep.get("truncated")),
            "options_cut": int(rep.get("options_cut") or 0),
            "n_options": len(offered),
        }
        row["laya_where_retriever"] = row["laya"] if row["retriever"] is not None else None
        row["laya_where_bev"] = row["laya"] if row["bev"] is not None else None
        rs = ash.get(key)
        if rs is not None:
            sp = rs["answers"][qid]["choice"]
            order = (rs.get("asked_order") or {}).get(qid) or offered
            row.update({"laya_shuf": sp in g, "laya_first_shuf": sp == order[0],
                        "invariant": sp == pick})
        else:
            row.update({"laya_shuf": None, "laya_first_shuf": None, "invariant": None})
        rows.append(row)
    return rows


def summarize(rows: list[dict]) -> dict:
    def ci(key):
        p, lo, hi = bootstrap_by_episode(rows, key)
        n = sum(1 for r in rows if r.get(key) is not None)
        return {"p": p, "lo": lo, "hi": hi, "n": n}
    mean = lambda k: (sum(r[k] for r in rows) / len(rows)) if rows else None  # noqa: E731
    return {
        "n": len(rows), "episodes": len({r["episode"] for r in rows}),
        "laya": ci("laya"), "laya_shuf": ci("laya_shuf"),
        "belief": ci("belief"), "retriever": ci("retriever"),
        "laya_where_retriever": ci("laya_where_retriever"),
        "bev": ci("bev"), "laya_where_bev": ci("laya_where_bev"),
        "chance": mean("chance"),
        "laya_first": pooled_share(rows, "laya_first"), "laya_first_shuf": pooled_share(rows, "laya_first_shuf"),
        "first_chance": mean("first_chance"), "invariant": pooled_share(rows, "invariant"),
        "truncated": pooled_share(rows, "truncated"),
        "options_cut_share": (sum(r["options_cut"] for r in rows) / sum(r["n_options"] for r in rows)) if rows else None,
    }


def per_episode(rows: list[dict]) -> dict:
    out = {}
    for ep in sorted({r["episode"] for r in rows}):
        rr = [r for r in rows if r["episode"] == ep]
        out[ep] = {"n": len(rr), **{k: pooled_share(rr, k) for k in
                   ("laya", "laya_shuf", "belief", "retriever", "laya_where_retriever", "bev", "invariant")}}
    return out


def evaluate(tag: str, sets) -> dict:
    res = {}
    for s in sets:
        reqs = _jsonl(BASE / "requests" / f"{s}.jsonl")
        norm = _jsonl(BASE / "answers" / f"{s}__{tag}__normal.jsonl")
        shuf = _jsonl(BASE / "answers" / f"{s}__{tag}__shuffled.jsonl")
        if not reqs or not norm:
            continue
        rows = build_rows(reqs, norm, shuf)
        res[s] = {"all": summarize(rows),
                  "library": summarize([r for r in rows if not r["heldout"]]),
                  "per_episode": per_episode(rows)}
    wins = {s: (r["all"]["laya_where_retriever"]["p"] or 0) > (r["all"]["retriever"]["p"] or 0)
            for s, r in res.items() if s in DEV_SETS}
    res["_rule"] = {"laya_beats_retriever": wins, "dev_sets_scored": len(wins),
                    "go_to_track_c": sum(wins.values()) >= 2}
    return res


def fmt(x, pct=False):
    if x is None:
        return "–"
    return f"{x * 100:.1f}%" if pct else f"{x:.3f}"


def fmt_ci(c):
    if c["p"] is None:
        return "–"
    return f"{c['p']:.3f} [{c['lo']:.2f}, {c['hi']:.2f}] (n {c['n']})"


def markdown(res: dict, tag: str) -> str:
    L = [f"# Laya L1 decider results ({tag})", "",
         "Pick accuracy: share of post-onset decider requests whose pick is in the true group, pooled; "
         "[2.5%, 97.5%] from 2,000 episode resamples.", "",
         "| set | requests (episodes) | Laya | Laya, shuffled | belief top | retriever top | Laya on retriever's requests | bev | Laya on bev's requests | chance |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for s, r in res.items():
        if s.startswith("_"):
            continue
        a = r["all"]
        L.append(f"| {s} | {a['n']} ({a['episodes']}) | {fmt_ci(a['laya'])} | {fmt_ci(a['laya_shuf'])} | "
                 f"{fmt_ci(a['belief'])} | {fmt_ci(a['retriever'])} | {fmt_ci(a['laya_where_retriever'])} | "
                 f"{fmt_ci(a['bev'])} | {fmt_ci(a['laya_where_bev'])} | {fmt(a['chance'])} |")
    L += ["", "| set | Laya first option | shuffled: first listed | chance | choice unchanged by shuffle | state truncated | options cut at 48 tokens |",
          "|---|---|---|---|---|---|---|"]
    for s, r in res.items():
        if s.startswith("_"):
            continue
        a = r["all"]
        L.append(f"| {s} | {fmt(a['laya_first'], 1)} | {fmt(a['laya_first_shuf'], 1)} | {fmt(a['first_chance'], 1)} | "
                 f"{fmt(a['invariant'], 1)} | {fmt(a['truncated'], 1)} | {fmt(a['options_cut_share'], 1)} |")
    L += ["", "Library episodes only:", "",
          "| set | n | Laya | belief top | retriever top | Laya on retriever's | bev |", "|---|---|---|---|---|---|---|"]
    for s, r in res.items():
        if s.startswith("_"):
            continue
        a = r["library"]
        L.append(f"| {s} | {a['n']} | {fmt(a['laya']['p'])} | {fmt(a['belief']['p'])} | {fmt(a['retriever']['p'])} | "
                 f"{fmt(a['laya_where_retriever']['p'])} | {fmt(a['bev']['p'])} |")
    L += ["", f"Rule (pre-registered): Laya beats the retriever on {sum(res['_rule']['laya_beats_retriever'].values())} "
          f"of {res['_rule']['dev_sets_scored']} dev sets {res['_rule']['laya_beats_retriever']}; "
          f"go to Track C: **{res['_rule']['go_to_track_c']}**", ""]
    for s, r in res.items():
        if s.startswith("_"):
            continue
        L += [f"## {s} per episode", "", "| episode | n | Laya | shuffled | belief | retriever | Laya on retriever's | bev | unchanged |",
              "|---|---|---|---|---|---|---|---|---|"]
        for ep, e in r["per_episode"].items():
            L.append(f"| {ep} | {e['n']} | {fmt(e['laya'])} | {fmt(e['laya_shuf'])} | {fmt(e['belief'])} | "
                     f"{fmt(e['retriever'])} | {fmt(e['laya_where_retriever'])} | {fmt(e['bev'])} | {fmt(e['invariant'], 1)} |")
        L.append("")
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Laya decider pick accuracy")
    ap.add_argument("--tag", default="primary")
    ap.add_argument("--sets", default=",".join(ALL_SETS))
    ap.add_argument("--out", default=str(BASE))
    a = ap.parse_args(argv)
    res = evaluate(a.tag, a.sets.split(","))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"laya_l1_{a.tag}.json").write_text(json.dumps(res, indent=1))
    md = markdown(res, a.tag)
    (out / f"laya_l1_{a.tag}.md").write_text(md)
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
