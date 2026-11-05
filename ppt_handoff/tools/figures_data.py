#!/usr/bin/env python3
"""Collects everything the figures need from the saved board runs into
ppt_handoff/data/figures_data.json. Read-only on results/.

    unset PYTHONPATH; .venv/bin/python ppt_handoff/tools/figures_data.py

Plotting is separate (make_figures.py, needs matplotlib) so this project's
venv stays as it is. Scoring follows make_tables.py / bench/evaluator.py:
group top-1 from fault onset onward, look-alike groups from
data/kb/case_groups.json. The "decider removed" numbers replay each bev run
from its own saved answers with the decider's offsets left out
(bench/replay_multi.py), so they carry no run-to-run model noise."""
from __future__ import annotations

import gzip
import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_tables as mt  # noqa: E402
import bench.replay_multi as rm  # noqa: E402
from bench.stage_monitor_multi import episode_dir, load_truth  # noqa: E402

B = ROOT / "results/benchmarks"
OUT = ROOT / "ppt_handoff/data/figures_data.json"
TICK = 30.0
FAULT, FIRST4, SIX = mt.FAULT, mt.FIRST4, mt.SIX
ALL12 = FAULT + ["ep_E01_fouling_drift", "ep_N01_normal"]

single_map = dict(mt.CONFIGS[0][2])
CONFIGS = [
    # key, label, description, {episode: folder}, merge rule (for replay), has decider
    ("single", "Single agent", "L0-L7 pipeline, Llama 3.2 3B on the NPU, one big prompt, no grammar, model order wins",
     {e: f for e, (f, _) in single_map.items()}, None),
    ("v2_model", "Multi v2 · model", "multi-agent v2 prompts (group letters, Gemma note reader), merge rule model",
     {e: "multi_v2_6mark" for e in SIX}, None),
    ("v2_tiebreak", "Multi v2 · tiebreak", "multi-agent v2 prompts, merge rule tiebreak",
     {e: "multi_tiebreak_6mark" for e in SIX}, None),
    ("v2_nudge", "Multi v2 · nudge", "multi-agent v2 prompts, merge rule nudge",
     {**{e: "multi_nudge_6mark" for e in SIX}, **{e: "multi_nudge_6.1mark" for e in FAULT if e not in FIRST4}}, None),
    ("v3", "Multi v3 (hybrid)", "multi-agent v3: no group letters, raw notes, merge rule hybrid + flat guard",
     {e: "multi_v3" for e in ALL12}, "hybrid"),
    ("bev2", "bev-decider-2", "accuracy.yaml (v2 prompts, Llama 3B both lanes, verifier off) + nudge + bev-decider",
     {e: "bev_armB" for e in ALL12}, "nudge"),
    ("bev3", "bev-decider-3", "v3 + bev-decider (System One decider on the NPU, port 8082)",
     {e: "bev3_armB" for e in ALL12}, "hybrid"),
]


def load_run(folder: str, ep: str, arch: str) -> dict:
    rp, _ = mt.paths(folder, ep, arch)
    return mt.load_run(rp)


def score(run, ranking, truth):
    g, tg = truth["gmap"], truth["tgroup"]
    pub = {a["tick"]: a for a in run["assessments"]}
    per = {}
    for r in ranking:
        a = pub[r["tick"]]
        if a["tick"] * TICK < truth["onset"] or not a["hypotheses"]:
            continue
        top = r["hyps"][0][0] if r["hyps"] else None
        per[r["tick"]] = top is not None and g.get(top) == tg
    return (sum(per.values()) / len(per) if per else None), per


def replay_without_decider(run, rule):
    orig = rm._decider
    rm._decider = lambda recs, dec: dec
    try:
        return rm.replay(run, rule)
    finally:
        rm._decider = orig


def main() -> None:
    out = {"configs": [], "episodes": {}, "rows": [], "calls": [], "ticks": {}, "screening": []}
    for key, label, desc, eps, rule in CONFIGS:
        out["configs"].append({"key": key, "label": label, "description": desc,
                               "episodes": list(eps), "folders": sorted(set(eps.values()))})
        arch = "single" if key == "single" else "multi"
        for ep, folder in eps.items():
            row = mt.episode_row("single" if key == "single" else key, ep, folder)
            row["config"] = key
            run = load_run(folder, ep, arch)
            truth = load_truth(episode_dir(ep))
            out["episodes"].setdefault(ep, {
                "onset_min": truth["onset"] / 60 if truth and truth.get("onset") is not None else None,
                "trip_min": (truth["gt"].get("trip_t") / 60) if truth and truth["gt"].get("trip_t") else None,
                "true_group": truth.get("tgroup") if truth else None, "heldout": truth.get("heldout") if truth else None,
                "ticks": len(run["assessments"])})
            envs = [e for a in run["assessments"] for e in a.get("envelopes", [])]
            envs += [t["envelope"] for a in run["assessments"] for t in (a.get("multi") or {}).get("text", [])]
            for e in envs:
                lane = "bev" if e.get("backend") == "bev" else ("cpu" if e.get("backend") == "cpu" else "npu")
                out["calls"].append({"config": key, "episode": ep, "agent": e.get("agent"), "lane": lane,
                                     "status": e.get("status"), "latency_s": (e.get("latency_ms") or 0) / 1000,
                                     "prefill": (e.get("tokens") or {}).get("prefill"),
                                     "decode": (e.get("tokens") or {}).get("decode")})
            dec = [e for e in envs if e.get("agent") == "decider"]
            row["decider_calls"] = len(dec)
            row["llama_calls"] = len(envs) - len(dec)
            # per-tick series
            g = truth.get("gmap", {}) if truth else {}
            tg = truth.get("tgroup") if truth else None
            series = []
            rules = {}
            for a in run["assessments"]:
                rr = next((x for x in (a.get("multi") or {}).get("compact", []) or []
                           if isinstance(x, dict) and x.get("agent") == "rule"), None)
                if rr:
                    rules[a["tick"]] = rr
                top = a["hypotheses"][0].get("case_ref") if a["hypotheses"] else None
                b1 = mt.shown_belief(a)[0][0] if a.get("belief_ranking") else None
                scored = bool(truth and truth.get("scored") and a["tick"] * TICK >= truth["onset"] and a["hypotheses"])
                series.append({"tick": a["tick"], "triage": a.get("triage"),
                               "lat_s": (a.get("tick_latency_ms") or 0) / 1000,
                               "scored": scored, "ok": scored and g.get(top) == tg,
                               "bel_ok": scored and g.get(b1) == tg,
                               "regime": rr.get("regime") if rr else None})
            out["ticks"][f"{key}|{ep}"] = series
            # the diagnosticians' own first pick (rule records exist for tiebreak, nudge, hybrid runs)
            if truth and truth.get("scored") and rules:
                n = ok = 0
                for t, rr in rules.items():
                    if t * TICK < truth["onset"] or not rr.get("model_ranked"):
                        continue
                    n += 1
                    ok += g.get(rr["model_ranked"][0]) == tg
                row["llama_first_pick_n"], row["llama_first_pick_right"] = n, ok
            # bev: decider effect inside the same run, and the decider's own picks
            if dec and truth and truth.get("scored"):
                pub, per_pub = score(run, rm.published(run), truth)
                nod, per_nod = score(run, replay_without_decider(run, rule), truth)
                row["no_decider_group_top1"] = mt.r3(nod)
                row["decider_fixed_ticks"] = sum(per_pub[t] and not per_nod[t] for t in per_pub)
                row["decider_broke_ticks"] = sum(per_nod[t] and not per_pub[t] for t in per_pub)
                bel = {a["tick"]: (a.get("belief_ranking") or [{}])[0].get("case_ref") for a in run["assessments"]}
                d = {"n": 0, "dec": 0, "bel": 0, "flat": 0, "offered": 0, "llama_n": 0, "llama": 0}
                for e in dec:
                    if e.get("status") != "ok" or e["tick"] * TICK < truth["onset"]:
                        continue
                    ch = e["payload"]["choice"]
                    offered = json.loads(e["prompt"])["questions"]["root_cause"]["criteria"]
                    d["n"] += 1
                    d["dec"] += g.get(ch) == tg
                    d["bel"] += g.get(bel.get(e["tick"])) == tg
                    d["flat"] += ch in rm.FLAT
                    mr = (rules.get(e["tick"]) or {}).get("model_ranked")
                    if mr:
                        d["llama_n"] += 1
                        d["llama"] += g.get(mr[0]) == tg
                    d["offered"] += any(g.get(c) == tg for c in offered)
                row["decider_picks"] = d
            if rule:
                row["replay_ok"] = rm.replay(run, rule) == rm.published(run)
            row["decider_meta"] = (run.get("multi") or {}).get("decider")
            out["rows"].append(row)
    for m in ("llama32-3b", "qwen3-1.7b", "gemma3-1b-qat", "qwen25-0.5b"):
        d = json.load(open(ROOT / f"results/board/A/{m}/screen.summary.json"))
        out["screening"].append({"model": m, "prefill_tok_s": d["server_prefill_tok_s"],
                                 "decode_tok_s": d["server_decode_tok_s"],
                                 "verified_s": d["measured_verified_s"]})
    OUT.write_text(json.dumps(out, default=str))
    print(f"wrote {OUT.relative_to(ROOT)}: {len(out['rows'])} episode rows, {len(out['calls'])} calls, "
          f"{sum(len(v) for v in out['ticks'].values())} ticks")
    bad = [r["config"] + "|" + r["episode"] for r in out["rows"] if r.get("replay_ok") is False]
    print("replay mismatches:", bad or "none")


if __name__ == "__main__":
    main()
