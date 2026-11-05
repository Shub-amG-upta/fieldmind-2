#!/usr/bin/env python3
"""Data for the three bev-decider-3 slides: ppt_handoff/bev3_slides/data/*.csv.
Read-only on results/; needs ppt_handoff/data/figures_data.json (figures_data.py).

    unset PYTHONPATH; .venv/bin/python ppt_handoff/tools/bev3_slides_data.py

Every value comes from a board run file. Nothing is estimated."""
from __future__ import annotations

import collections
import csv
import gzip
import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_tables as mt  # noqa: E402

OUT = ROOT / "ppt_handoff/bev3_slides/data"
OUT.mkdir(parents=True, exist_ok=True)
D = json.load(open(ROOT / "ppt_handoff/data/figures_data.json"))
R = {(r["config"], r["episode"]): r for r in D["rows"]}
FAULT, FIRST4 = mt.FAULT, mt.FIRST4
ALL12 = FAULT + ["ep_E01_fouling_drift", "ep_N01_normal"]
r3 = mt.r3


def write(name, rows):
    cols = list(dict.fromkeys(k for r in rows for k in r))
    with open(OUT / name, "w", newline="") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        w.writerows(rows)
    print("wrote", name, len(rows), "rows")


# 1. per episode, v3 against bev3 ------------------------------------------------
ep_rows = []
for e in ALL12:
    v, b = R[("v3", e)], R[("bev3", e)]
    dp = b.get("decider_picks") or {}
    ep_rows.append({
        "episode": e, "family": e[3], "true_group": D["episodes"][e]["true_group"],
        "heldout_true_cause": D["episodes"][e]["heldout"], "ticks": v["ticks"], "scored_ticks": v.get("scored_ticks"),
        "v3_group_top1": v.get("group_top1"), "bev3_group_top1": b.get("group_top1"),
        "bev3_group_top1_decider_removed_replay": b.get("no_decider_group_top1"),
        "belief_group_top1": v.get("belief_group_top1"),
        "v3_exact_top1": v.get("exact_top1"), "bev3_exact_top1": b.get("exact_top1"),
        "v3_true_group_in_top3": v.get("true_group_in_top3"), "bev3_true_group_in_top3": b.get("true_group_in_top3"),
        "v3_right_before_trip": v.get("right_before_trip"), "bev3_right_before_trip": b.get("right_before_trip"),
        "v3_first_right_min_after_onset": v.get("first_right_min_after_onset"),
        "bev3_first_right_min_after_onset": b.get("first_right_min_after_onset"),
        "v3_lead_time_min_exact": v.get("lead_time_min_exact"), "bev3_lead_time_min_exact": b.get("lead_time_min_exact"),
        "decider_ticks_fixed": b.get("decider_fixed_ticks"), "decider_ticks_broken": b.get("decider_broke_ticks"),
        "decider_calls": b["decider_calls"], "decider_calls_failed": (b.get("decider_meta") or {}).get("failed"),
        "decider_answers_rejected_by_gate": (b.get("decider_meta") or {}).get("rejected"),
        "decider_scored_calls": dp.get("n"), "decider_pick_right": dp.get("dec"),
        "belief_top_right_on_those_ticks": dp.get("bel"), "llama_first_pick_right_on_those_ticks": dp.get("llama"),
        "llama_first_pick_n": dp.get("llama_n"), "decider_picked_filler_case": dp.get("flat"),
        "v3_llama_calls": v["llama_calls"], "bev3_llama_calls": b["llama_calls"],
        "v3_wall_s": v["wall_s"], "bev3_wall_s": b["wall_s"],
        "v3_median_nonquiet_tick_s": v.get("median_nonquiet_tick_s"), "bev3_median_nonquiet_tick_s": b.get("median_nonquiet_tick_s"),
        "v3_max_tick_s": v.get("max_tick_s"), "bev3_max_tick_s": b.get("max_tick_s"),
        "v3_ticks_over_30s": v["ticks_over_30s"], "bev3_ticks_over_30s": b["ticks_over_30s"],
        "v3_chip_c_before": v.get("chip_c_start"), "v3_chip_c_after": v.get("chip_c_end"),
        "bev3_chip_c_before": b.get("chip_c_start"), "bev3_chip_c_after": b.get("chip_c_end"),
        "bev3_replay_reproduces_published": b.get("replay_ok"),
    })
write("bev3_vs_v3_per_episode.csv", ep_rows)


# 2. summary ---------------------------------------------------------------------
def m(rows, k):
    v = [r[k] for r in rows if r.get(k) is not None]
    return r3(st.mean(v)) if v else None


def s(rows, k):
    return sum(r[k] or 0 for r in rows)


summ = []
for label, eps in (("10 fault episodes", FAULT), ("first 4 (A01 B01 C01 D01)", FIRST4)):
    rs = [x for x in ep_rows if x["episode"] in eps]
    for metric, a, b in [("group top-1 (mean of episodes)", "v3_group_top1", "bev3_group_top1"),
                         ("exact top-1 (mean, excl. held-out C01/C03)", "v3_exact_top1", "bev3_exact_top1"),
                         ("true group in top 3", "v3_true_group_in_top3", "bev3_true_group_in_top3"),
                         ("right before the trip (A01-A03, D01)", "v3_right_before_trip", "bev3_right_before_trip"),
                         ("first right, min after onset", "v3_first_right_min_after_onset", "bev3_first_right_min_after_onset"),
                         ("lead time, min (exact case; A01-A03, D01)", "v3_lead_time_min_exact", "bev3_lead_time_min_exact")]:
        summ.append({"episode_set": label, "metric": metric, "v3": m(rs, a), "bev3": m(rs, b),
                     "belief_alone": m(rs, "belief_group_top1") if metric.startswith("group top-1") else None,
                     "bev3_decider_removed_replay": m(rs, "bev3_group_top1_decider_removed_replay")
                     if metric.startswith("group top-1") else None})
    # pooled (tick-weighted)
    n = s(rs, "scored_ticks")
    summ.append({"episode_set": label, "metric": "group top-1 (all scored ticks pooled)",
                 "v3": r3(sum(x["v3_group_top1"] * x["scored_ticks"] for x in rs) / n),
                 "bev3": r3(sum(x["bev3_group_top1"] * x["scored_ticks"] for x in rs) / n),
                 "belief_alone": r3(sum(x["belief_group_top1"] * x["scored_ticks"] for x in rs) / n),
                 "bev3_decider_removed_replay": r3(sum(x["bev3_group_top1_decider_removed_replay"] * x["scored_ticks"]
                                                       for x in rs) / n)})
    summ.append({"episode_set": label, "metric": "decider ticks fixed / broken (same-run replay)",
                 "v3": None, "bev3": f"{s(rs, 'decider_ticks_fixed')} / {s(rs, 'decider_ticks_broken')}"})
allr = ep_rows
for metric, a, b in [("Llama calls", "v3_llama_calls", "bev3_llama_calls"), ("wall time, s", "v3_wall_s", "bev3_wall_s"),
                     ("ticks over 30 s", "v3_ticks_over_30s", "bev3_ticks_over_30s")]:
    summ.append({"episode_set": "all 12 episodes", "metric": metric, "v3": r3(s(allr, a)), "bev3": r3(s(allr, b))})
summ.append({"episode_set": "all 12 episodes", "metric": "decider calls (failed / rejected)", "v3": None,
             "bev3": f"{s(allr, 'decider_calls')} ({s(allr, 'decider_calls_failed')} / {s(allr, 'decider_answers_rejected_by_gate')})"})
for metric, a, b in [("median non-quiet tick, s (mean of episodes)", "v3_median_nonquiet_tick_s", "bev3_median_nonquiet_tick_s")]:
    summ.append({"episode_set": "all 12 episodes", "metric": metric, "v3": m(allr, a), "bev3": m(allr, b)})
summ.append({"episode_set": "all 12 episodes", "metric": "slowest tick, s", "v3": max(x["v3_max_tick_s"] or 0 for x in allr),
             "bev3": max(x["bev3_max_tick_s"] or 0 for x in allr)})
write("bev3_vs_v3_summary.csv", summ)

# 3. decider picks by family -------------------------------------------------------
fam = []
for f, name in (("A", "feed water (FCV seize, BFP suction)"), ("B", "tube leak"), ("C", "fuel (wet coal*, feeder trip)"),
                ("D", "high-CV coal")):
    rs = [x for x in ep_rows if x["family"] == f]
    n = s(rs, "decider_scored_calls")
    ln = s(rs, "llama_first_pick_n")
    fam.append({"family": f, "fault": name, "decider_calls_after_onset": n,
                "decider_pick_right": r3(s(rs, "decider_pick_right") / n),
                "llama_first_pick_right": r3(s(rs, "llama_first_pick_right_on_those_ticks") / ln) if ln else None,
                "belief_top_right": r3(s(rs, "belief_top_right_on_those_ticks") / n),
                "decider_picked_filler_case": r3(s(rs, "decider_picked_filler_case") / n)})
rs = [x for x in ep_rows if x["family"] in "ABCD"]
n = s(rs, "decider_scored_calls"); ln = s(rs, "llama_first_pick_n")
fam.append({"family": "all", "fault": "10 fault episodes", "decider_calls_after_onset": n,
            "decider_pick_right": r3(s(rs, "decider_pick_right") / n),
            "llama_first_pick_right": r3(s(rs, "llama_first_pick_right_on_those_ticks") / ln),
            "belief_top_right": r3(s(rs, "belief_top_right_on_those_ticks") / n),
            "decider_picked_filler_case": r3(s(rs, "decider_picked_filler_case") / n)})
write("decider_picks_by_family.csv", fam)

# 4. cost per model call, from the board's own timings ----------------------------
cost = collections.OrderedDict()
opts = collections.Counter()
trigger = {"nonquiet_ticks": 0, "decider_calls": 0}
srcs = [("single agent", "single", ep, f) for ep, f in
        {e: f for e, (f, _) in dict(mt.CONFIGS[0][2]).items()}.items()]
srcs += [("v3", "multi_v3", ep, None) for ep in ALL12] + [("bev3", "bev3_armB", ep, None) for ep in ALL12]
for cfg, folder, ep, sf in srcs:
    if cfg == "single agent":
        run = mt.load_run(mt.paths(sf, ep, "single")[0])
    else:
        run = mt.load_run(mt.paths(folder, ep, "multi")[0])
    for a in run["assessments"]:
        envs = list(a.get("envelopes", [])) + [t["envelope"] for t in (a.get("multi") or {}).get("text", [])]
        if cfg == "bev3" and a.get("triage") != "QUIET":
            trigger["nonquiet_ticks"] += 1
        for e in envs:
            if e.get("status") != "ok":
                continue
            lane = {"npu": "NPU", "cpu": "CPU", "bev": "NPU (bev-decide)"}.get(e.get("backend"), "NPU")
            model = {"decider": "bev-decider 0.4B Q8_0"}.get(e["agent"]) or (
                "Gemma 3 1B Q4_0" if e.get("backend") == "cpu" else "Llama 3.2 3B Q4_0")
            key = (cfg, e["agent"], lane, model)
            g = cost.setdefault(key, {"n": 0, "pt": 0, "dt": 0, "pms": 0.0, "dms": 0.0, "lat": []})
            g["n"] += 1
            g["lat"].append(e.get("latency_ms") or 0)
            for c in e.get("calls", []):
                g["pt"] += c.get("prefill") or 0
                g["dt"] += c.get("decode") or 0
                g["pms"] += c.get("prefill_ms") or 0
                g["dms"] += c.get("decode_ms") or 0
            if e["agent"] == "decider":
                trigger["decider_calls"] += 1
                opts[len(json.loads(e["prompt"])["questions"]["root_cause"]["criteria"])] += 1
crow = []
for (cfg, agent, lane, model), g in cost.items():
    tot = sum(g["lat"]) / 1000
    crow.append({"system": cfg, "agent": agent, "lane": lane, "model": model, "calls": g["n"],
                 "mean_prompt_tokens": round(g["pt"] / g["n"]), "mean_answer_tokens": round(g["dt"] / g["n"], 1),
                 "total_answer_tokens": g["dt"],
                 "mean_prefill_s": r3(g["pms"] / 1000 / g["n"]), "mean_decode_s": r3(g["dms"] / 1000 / g["n"]),
                 "mean_call_s": r3(tot / g["n"]), "median_call_s": r3(st.median(g["lat"]) / 1000),
                 "decode_share_of_prefill_plus_decode": r3(g["dms"] / (g["pms"] + g["dms"])) if g["pms"] + g["dms"] else None,
                 "prefill_tok_per_s": round(g["pt"] / (g["pms"] / 1000)) if g["pms"] else None,
                 "decode_tok_per_s": round(g["dt"] / (g["dms"] / 1000), 1) if g["dms"] else None,
                 "total_call_time_s": round(tot)})
write("model_call_costs.csv", crow)
write("decider_options_per_call.csv", [{"options_offered": k, "calls": v} for k, v in sorted(opts.items())])
json.dump(trigger, open(OUT / "decider_trigger.json", "w"))
print("decider trigger", trigger)
