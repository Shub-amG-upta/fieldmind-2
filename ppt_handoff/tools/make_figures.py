#!/usr/bin/env python3
"""Charts and flow diagrams for the deck, from ppt_handoff/data/figures_data.json
(written by figures_data.py). Needs matplotlib and graphviz `dot`; this laptop's
system python has matplotlib, the project venv does not:

    /usr/bin/python3 -I ppt_handoff/tools/make_figures.py

Output: ppt_handoff/figures/*.png (16:9, 200 dpi). Every number drawn comes from
the data file; nothing is estimated. Energy was never measured and is not drawn."""
from __future__ import annotations

import json
import statistics as st
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
D = json.load(open(ROOT / "ppt_handoff/data/figures_data.json"))
OUT = ROOT / "ppt_handoff/figures"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "axes.titlesize": 15,
                     "axes.labelsize": 13, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "legend.frameon": False})
W, H = 13.33, 7.5
COL = {"single": "#7f7f7f", "v2_model": "#d62728", "v2_tiebreak": "#ff7f0e", "v2_nudge": "#bcbd22",
       "v3": "#1f77b4", "bev2": "#9467bd", "bev3": "#17a589", "belief": "#333333"}
LAB = {c["key"]: c["label"] for c in D["configs"]}
LAB["belief"] = "Belief alone (code only)"
DESC = {c["key"]: c["description"] for c in D["configs"]}
ORDER = ["single", "v2_model", "v2_tiebreak", "v2_nudge", "v3", "bev2", "bev3"]
FAULT = ["ep_A01_fcv_seize", "ep_A02_fcv_seize_fast", "ep_A03_bfp_suction", "ep_B01_tube_leak",
         "ep_B02_tube_leak_fast", "ep_B03_tube_leak_slow", "ep_C01_wet_coal", "ep_C02_feeder_trip",
         "ep_C03_wet_coal_mild", "ep_D01_high_cv_coal"]
FIRST4 = ["ep_A01_fcv_seize", "ep_B01_tube_leak", "ep_C01_wet_coal", "ep_D01_high_cv_coal"]
SHORT = {"ep_A01_fcv_seize": "A01\nFCV seize", "ep_A02_fcv_seize_fast": "A02\nFCV seize fast",
         "ep_A03_bfp_suction": "A03\nBFP suction", "ep_B01_tube_leak": "B01\ntube leak",
         "ep_B02_tube_leak_fast": "B02\nleak fast", "ep_B03_tube_leak_slow": "B03\nleak slow",
         "ep_C01_wet_coal": "C01\nwet coal*", "ep_C02_feeder_trip": "C02\nfeeder trip",
         "ep_C03_wet_coal_mild": "C03\nwet coal mild*", "ep_D01_high_cv_coal": "D01\nhigh-CV coal",
         "ep_E01_fouling_drift": "E01\nfouling", "ep_N01_normal": "N01\nnormal"}
NOTE = ("QIDK (SM8650) board runs · reporting episodes · one run per episode · group top-1 scored from fault onset · "
        "agent code on the laptop, model calls on the board · energy not measured · all plant data simulated")
R = {(r["config"], r["episode"]): r for r in D["rows"]}
made = []


def rows(cfg, eps=None):
    return [R[(cfg, e)] for e in (eps or [r["episode"] for r in D["rows"] if r["config"] == cfg]) if (cfg, e) in R]


def mean(cfg, key, eps):
    v = [R[(cfg, e)].get(key) for e in eps if (cfg, e) in R and R[(cfg, e)].get(key) is not None]
    return st.mean(v) if v else None


def has_all(cfg, eps):
    return all((cfg, e) in R for e in eps)


def save(fig, name, note=NOTE, title=None, sub=None):
    if title:
        fig.text(0.01, 0.995, title, fontsize=20, fontweight="bold", ha="left", va="top")
    if sub:
        fig.text(0.01, 0.94, sub, fontsize=12, color="#444", ha="left", va="top")
    if note:
        fig.text(0.01, 0.005, note, fontsize=8.5, color="#777", ha="left", va="bottom")
    fig.savefig(OUT / name, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    made.append(name)


def label_bars(ax, bars, fmt="{:.2f}", dy=0.01, size=10):
    for b in bars:
        h = b.get_height()
        if h == h and h is not None:
            ax.text(b.get_x() + b.get_width() / 2, h + dy, fmt.format(h), ha="center", va="bottom", fontsize=size)


# ---------------------------------------------------------------- per benchmark
AG_COL = {"diagnostician": "#1f77b4", "verifier": "#ff7f0e", "text_reader": "#8c564b", "decider": "#17a589"}


def bench_figure(cfg, idx):
    rs = rows(cfg)
    eps = [r["episode"] for r in rs]
    feps = [e for e in FAULT if e in eps]
    fig, axs = plt.subplots(1, 3, figsize=(W, H), gridspec_kw={"width_ratios": [1.5, 1.1, 1.1]})
    ax = axs[0]
    x = range(len(feps))
    b1 = ax.bar([i - 0.2 for i in x], [R[(cfg, e)]["group_top1"] for e in feps], 0.4, color=COL[cfg], label=LAB[cfg])
    ax.bar([i + 0.2 for i in x], [R[(cfg, e)]["belief_group_top1"] for e in feps], 0.4, color="#cccccc",
           label=LAB["belief"])
    label_bars(ax, b1, size=9)
    ax.set_xticks(list(x)); ax.set_xticklabels([SHORT[e].split("\n")[0] for e in feps], fontsize=10)
    ax.set_ylim(0, 1.12); ax.set_ylabel("group top-1"); ax.set_title("Accuracy per fault episode")
    ax.legend(loc="upper right", fontsize=9)
    ax = axs[1]
    bars = ax.bar(range(len(eps)), [R[(cfg, e)]["wall_s"] or 0 for e in eps], color=COL[cfg])
    label_bars(ax, bars, "{:.0f}", dy=5, size=8)
    ax.set_xticks(range(len(eps))); ax.set_xticklabels([SHORT[e].split("\n")[0] for e in eps], fontsize=9)
    ax.set_ylabel("seconds"); ax.set_title("Wall time per episode")
    ax = axs[2]
    agents = [a for a in AG_COL if any(c["config"] == cfg and c["agent"] == a for c in D["calls"])]
    bottom = [0] * len(eps)
    for a in agents:
        v = [sum(1 for c in D["calls"] if c["config"] == cfg and c["episode"] == e and c["agent"] == a) for e in eps]
        ax.bar(range(len(eps)), v, bottom=bottom, color=AG_COL[a], label=a.replace("_", " "))
        bottom = [b + y for b, y in zip(bottom, v)]
    ax.set_xticks(range(len(eps))); ax.set_xticklabels([SHORT[e].split("\n")[0] for e in eps], fontsize=9)
    ax.set_ylabel("model calls"); ax.set_title("Model calls per episode"); ax.legend(fontsize=9)
    g = mean(cfg, "group_top1", feps); b = mean(cfg, "belief_group_top1", feps)
    unusable = sum(r["unusable_answers"] for r in rs); over = sum(r["ticks_over_30s"] for r in rs)
    sub = (f"{DESC[cfg]}\nMean group top-1 {g:.3f} (belief {b:.3f}) on {len(feps)} fault episodes · "
           f"total wall {sum(r['wall_s'] or 0 for r in rs):,.0f} s · unusable answers {unusable} · ticks over 30 s {over}")
    for a in axs[1:]:
        a.tick_params(axis="x", labelsize=9, rotation=60)
    fig.subplots_adjust(top=0.78, wspace=0.3)
    save(fig, f"{idx:02d}_bench_{cfg}.png", title=f"Benchmark: {LAB[cfg]}", sub=sub)


for i, c in enumerate(ORDER):
    bench_figure(c, 10 + i)


# ---------------------------------------------------------------- comparisons
def fig_accuracy_first4():
    fig, ax = plt.subplots(figsize=(W, H))
    vals = [mean(c, "group_top1", FIRST4) for c in ORDER]
    bars = ax.bar(range(len(ORDER)), vals, color=[COL[c] for c in ORDER], width=0.62)
    label_bars(ax, bars, dy=0.015, size=13)
    for i, c in enumerate(ORDER):
        ax.scatter([i] * 4, [R[(c, e)]["group_top1"] for e in FIRST4], color="black", s=14, zorder=3, alpha=0.6)
    bel = mean("v3", "belief_group_top1", FIRST4)
    ax.axhline(bel, ls="--", color=COL["belief"], lw=1.5)
    ax.text(-0.45, bel + 0.012, f"belief alone {bel:.3f}", ha="left", fontsize=11)
    ax.set_xticks(range(len(ORDER))); ax.set_xticklabels([LAB[c].replace(" · ", "\n") for c in ORDER])
    ax.set_ylim(0, 1.05); ax.set_ylabel("mean group top-1 (dots = episodes)")
    fig.subplots_adjust(top=0.86)
    save(fig, "20_accuracy_first4.png", title="Accuracy: every configuration on the same four fault episodes",
         sub="A01, B01, C01, D01 · bar = mean of the four episodes · dashed line = belief (code-only ranking)")


def fig_accuracy_all10():
    cfgs = ["v2_nudge", "v3", "bev2", "bev3"]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(W, H), gridspec_kw={"width_ratios": [4, 1]})
    w = 0.2
    for k, c in enumerate(cfgs):
        ax.bar([i + (k - 1.5) * w for i in range(10)], [R[(c, e)]["group_top1"] for e in FAULT], w,
               color=COL[c], label=LAB[c])
    for i, e in enumerate(FAULT):
        ax.plot([i - 0.42, i + 0.42], [R[("v3", e)]["belief_group_top1"]] * 2, color="black", lw=2)
    ax.plot([], [], color="black", lw=2, label=LAB["belief"])
    ax.set_xticks(range(10)); ax.set_xticklabels([SHORT[e] for e in FAULT], fontsize=9)
    ax.set_ylim(0, 1.08); ax.set_ylabel("group top-1"); ax.legend(ncol=5, fontsize=10, loc="upper center",
                                                                  bbox_to_anchor=(0.5, 1.1))
    vals = [mean(c, "group_top1", FAULT) for c in cfgs] + [mean("v3", "belief_group_top1", FAULT)]
    bars = ax2.bar(range(5), vals, color=[COL[c] for c in cfgs] + ["#cccccc"])
    label_bars(ax2, bars, size=11)
    ax2.set_xticks(range(5)); ax2.set_xticklabels(["v2\nnudge", "v3", "bev2", "bev3", "belief"], fontsize=10)
    ax2.set_ylim(0, 1.08); ax2.set_title("mean of 10")
    fig.subplots_adjust(top=0.8, wspace=0.12)
    save(fig, "21_accuracy_all10.png", title="Accuracy on all ten fault episodes",
         sub="* C01 and C03: the true cause (wet coal) is held out of the library; only its look-alike group can score")


def fig_heatmap():
    rows_ = ORDER + ["belief"]
    M = []
    for c in rows_:
        if c == "belief":
            M.append([R[("v3", e)]["belief_group_top1"] for e in FAULT])
        else:
            M.append([R[(c, e)]["group_top1"] if (c, e) in R else float("nan") for e in FAULT])
    fig, ax = plt.subplots(figsize=(W, H * 0.85))
    im = ax.imshow(M, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
    for i, row in enumerate(M):
        for j, v in enumerate(row):
            ax.text(j, i, "not run" if v != v else f"{v:.2f}", ha="center", va="center",
                    fontsize=10 if v == v else 8, color="#555" if v != v else "black")
    ax.set_xticks(range(10)); ax.set_xticklabels([SHORT[e] for e in FAULT], fontsize=9)
    ax.set_yticks(range(len(rows_))); ax.set_yticklabels([LAB[c] for c in rows_])
    ax.grid(False); fig.colorbar(im, ax=ax, fraction=0.025, label="group top-1")
    fig.subplots_adjust(top=0.85)
    save(fig, "22_heatmap_group_top1.png", title="Group top-1, every configuration × fault episode",
         sub="Belief row: the code-only ranking (the same in every run: computed by code)")


def fig_quality():
    cfgs = ["v2_nudge", "v3", "bev2", "bev3"]
    mets = [("group_top1", "group top-1"), ("exact_top1", "exact top-1\n(8 episodes)"),
            ("true_group_in_top3", "right group\nin top 3"), ("mrr", "MRR"),
            ("right_before_trip", "right before trip\n(A01–A03, D01)")]
    fig, ax = plt.subplots(figsize=(W, H))
    w = 0.2
    for k, c in enumerate(cfgs):
        bars = ax.bar([i + (k - 1.5) * w for i in range(len(mets))], [mean(c, m, FAULT) for m, _ in mets], w,
                      color=COL[c], label=LAB[c])
        label_bars(ax, bars, size=8.5)
    ax.set_xticks(range(len(mets))); ax.set_xticklabels([l for _, l in mets])
    ax.set_ylim(0, 1.1); ax.set_ylabel("mean over fault episodes"); ax.legend(ncol=4, loc="upper center",
                                                                             bbox_to_anchor=(0.5, 1.08))
    fig.subplots_adjust(top=0.83)
    save(fig, "23_quality_metrics_all10.png", title="Diagnosis quality: five metrics, ten fault episodes",
         sub="Higher is better for all five")


def fig_helped_harmed():
    fig, ax = plt.subplots(figsize=(W, H * 0.85))
    h = [sum(R[(c, e)]["ticks_helped_vs_belief"] for e in FIRST4) for c in ORDER]
    m = [-sum(R[(c, e)]["ticks_harmed_vs_belief"] for e in FIRST4) for c in ORDER]
    y = range(len(ORDER))
    ax.barh(y, h, color="#2ca02c", label="ticks the model made right (belief wrong)")
    ax.barh(y, m, color="#d62728", label="ticks the model made wrong (belief right)")
    for i in y:
        ax.text(h[i] + 2, i, f"+{h[i]}", va="center", fontsize=11)
        ax.text(m[i] - 2, i, f"−{-m[i]}", va="center", ha="right", fontsize=11)
    ax.set_yticks(list(y)); ax.set_yticklabels([LAB[c] for c in ORDER]); ax.invert_yaxis()
    ax.axvline(0, color="black", lw=1); ax.set_xlabel("scored ticks (A01, B01, C01, D01)")
    ax.set_xlim(min(m) - 40, max(h) + 40); ax.legend(loc="lower right")
    fig.subplots_adjust(top=0.84)
    save(fig, "24_helped_harmed_first4.png", title="Where the model changed the answer, compared with belief",
         sub="Net value of the language model = green minus red")


def fig_wall_time():
    cfgs = ["single", "v2_nudge", "v3", "bev2", "bev3"]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(W, H), gridspec_kw={"width_ratios": [3, 1.2]})
    w = 0.16
    for k, c in enumerate(cfgs):
        bars = ax.bar([i + (k - 2) * w for i in range(4)], [R[(c, e)]["wall_s"] for e in FIRST4], w,
                      color=COL[c], label=LAB[c])
        label_bars(ax, bars, "{:.0f}", dy=30, size=8)
    ax.set_xticks(range(4)); ax.set_xticklabels([SHORT[e] for e in FIRST4]); ax.set_ylabel("seconds")
    ax.legend(fontsize=10); ax.set_title("Wall time per episode")
    tot = [sum(R[(c, e)]["wall_s"] for e in FIRST4) for c in cfgs]
    bars = ax2.bar(range(len(cfgs)), tot, color=[COL[c] for c in cfgs])
    label_bars(ax2, bars, "{:,.0f} s", dy=60, size=10)
    ax2.set_xticks(range(len(cfgs))); ax2.set_xticklabels(["single", "v2\nnudge", "v3", "bev2", "bev3"])
    ax2.set_title("Total, four episodes")
    fig.subplots_adjust(top=0.84, wspace=0.18)
    save(fig, "25_wall_time_first4.png", title="Speed: time to run the same four episodes",
         sub=f"Lockstep: each tick waits for its own model calls. Single agent {tot[0]:,.0f} s against v3 "
             f"{tot[2]:,.0f} s ({tot[0] / tot[2]:.1f}× faster)")


def fig_call_latency():
    groups = [("single", "diagnostician", "npu", "Single agent\ndiagnostician\nLlama 3B · NPU"),
              ("single", "verifier", "npu", "Single agent\nverifier\nLlama 3B · NPU"),
              ("v3", "diagnostician", "npu", "v3 diagnostician\nLlama 3B · NPU"),
              ("v3", "verifier", "cpu", "v3 verifier\nGemma 1B · CPU"),
              ("v2_nudge", "text_reader", "cpu", "v2 note reader\nGemma 1B · CPU"),
              ("bev2", "text_reader", "cpu", "bev2 note reader\nLlama 3B · CPU"),
              ("bev3", "decider", "bev", "bev-decider\n0.4B · NPU\n(System One)")]
    data, labels = [], []
    for c, a, lane, lab in groups:
        v = [x["latency_s"] for x in D["calls"] if x["config"] == c and x["agent"] == a and x["lane"] == lane
             and x["status"] == "ok" and x["latency_s"] > 0]
        if v:
            data.append(v); labels.append(f"{lab}\nn={len(v)}")
    fig, ax = plt.subplots(figsize=(W, H))
    bp = ax.boxplot(data, patch_artist=True, showfliers=False, widths=0.55)
    cols = ["#7f7f7f", "#b0b0b0", "#1f77b4", "#ff7f0e", "#bcbd22", "#9467bd", "#17a589"]
    for p, c in zip(bp["boxes"], cols):
        p.set_facecolor(c); p.set_alpha(0.8)
    for i, v in enumerate(data):
        md = st.median(v)
        ax.text(i + 1.32, md, f"{md:.2f} s", va="center", fontsize=10, fontweight="bold")
    ax.set_yscale("log"); ax.set_ylabel("seconds per call (log scale)")
    ax.set_xticks(range(1, len(labels) + 1)); ax.set_xticklabels(labels, fontsize=9)
    fig.subplots_adjust(top=0.86)
    save(fig, "26_call_latency.png", title="Model call time by agent, lane and model",
         sub="Board-side call time (box = middle 50%, whiskers 1.5 IQR, outliers hidden) · label = median")


def fig_tick_latency():
    cfgs = ["single", "v2_nudge", "v3", "bev2", "bev3"]
    fig, ax = plt.subplots(figsize=(W, H))
    for c in cfgs:
        v = sorted(t["lat_s"] for r in rows(c, FIRST4) for t in D["ticks"][f"{c}|{r['episode']}"]
                   if t["triage"] != "QUIET" and t["lat_s"] > 0)
        n = len(v)
        over = sum(x > 30 for x in v)
        ax.step(v, [(i + 1) / n for i in range(n)], where="post", color=COL[c], lw=2.2,
                label=f"{LAB[c]}: median {st.median(v):.1f} s, {over} of {n} over 30 s")
    ax.axvline(30, color="red", ls="--"); ax.text(31, 0.05, "30 s tick budget", color="red")
    ax.set_xscale("log"); ax.set_xlabel("non-quiet tick time, seconds (log scale)"); ax.set_ylabel("share of ticks")
    ax.legend(loc="upper left", fontsize=10)
    fig.subplots_adjust(top=0.86)
    save(fig, "27_tick_latency.png", title="Tick time: how long each non-quiet tick took",
         sub="A01, B01, C01, D01 · cumulative distribution · tick time = laptop code + board model calls")


def fig_tokens():
    cfgs = ["single", "v2_model", "v2_tiebreak", "v2_nudge", "v3", "bev2", "bev3"]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(W, H))
    for k, (axx, key, title) in enumerate([(ax, "prefill", "Prompt tokens processed"),
                                          (ax2, "decode", "Answer tokens generated")]):
        llama = [sum(x[key] or 0 for x in D["calls"] if x["config"] == c and x["episode"] in FIRST4
                     and x["agent"] != "decider") / 1000 for c in cfgs]
        dec = [sum(x[key] or 0 for x in D["calls"] if x["config"] == c and x["episode"] in FIRST4
                   and x["agent"] == "decider") / 1000 for c in cfgs]
        axx.bar(range(len(cfgs)), llama, color=[COL[c] for c in cfgs], label="Llama / Gemma calls")
        if any(dec):
            axx.bar(range(len(cfgs)), dec, bottom=llama, color="#17a589", hatch="//", alpha=0.5,
                    label="bev-decider calls")
        for i, (a, b) in enumerate(zip(llama, dec)):
            axx.text(i, a + b, f"{a + b:,.0f}k", ha="center", va="bottom", fontsize=10)
        axx.set_xticks(range(len(cfgs))); axx.set_xticklabels([LAB[c].replace(" · ", "\n") for c in cfgs],
                                                                fontsize=9, rotation=0)
        axx.set_title(title); axx.set_ylabel("thousand tokens")
        if k == 0:
            axx.legend(fontsize=10)
    fig.subplots_adjust(top=0.84, wspace=0.2)
    save(fig, "28_tokens_first4.png", title="Tokens processed on the board, four fault episodes",
         sub="Decode (answer) tokens are the expensive ones: ~14–16 tok/s on the NPU against 670–990 tok/s prefill")


def fig_tradeoff():
    fig, ax = plt.subplots(figsize=(W, H))
    for c in ORDER:
        x = sum(R[(c, e)]["wall_s"] for e in FIRST4) / 60
        y = mean(c, "group_top1", FIRST4)
        ax.scatter(x, y, s=260, color=COL[c], zorder=3, edgecolor="black")
        ax.annotate(LAB[c], (x, y), xytext=(10, 6), textcoords="offset points", fontsize=12)
    bel = mean("v3", "belief_group_top1", FIRST4)
    ax.axhline(bel, ls="--", color="black"); ax.text(1, bel + 0.008, f"belief alone {bel:.3f}", fontsize=11)
    ax.set_xscale("log"); ax.set_xlabel("total wall time for the four episodes, minutes (log scale)")
    ax.set_ylabel("mean group top-1"); ax.set_ylim(0.3, 0.9)
    fig.subplots_adjust(top=0.86)
    save(fig, "29_accuracy_vs_time.png", title="Accuracy against time: up and to the left is better",
         sub="A01, B01, C01, D01")


def fig_decider_effect():
    fig, axs = plt.subplots(2, 1, figsize=(W, H * 1.05), sharex=True)
    for ax, c in zip(axs, ["bev3", "bev2"]):
        pub = [R[(c, e)]["group_top1"] for e in FAULT]
        nod = [R[(c, e)]["no_decider_group_top1"] for e in FAULT]
        ax.bar([i - 0.2 for i in range(10)], nod, 0.4, color="#bbbbbb", label="same run, decider removed (replay)")
        ax.bar([i + 0.2 for i in range(10)], pub, 0.4, color=COL[c], label="published (with decider)")
        for i, e in enumerate(FAULT):
            f, b = R[(c, e)]["decider_fixed_ticks"], R[(c, e)]["decider_broke_ticks"]
            if f or b:
                ax.text(i, max(pub[i], nod[i]) + 0.03, f"+{f} / −{b}", ha="center", fontsize=9,
                        color="#2ca02c" if f > b else "#d62728")
        ax.set_ylim(0, 1.18); ax.set_ylabel("group top-1")
        mp, mn = st.mean(pub), st.mean(nod)
        fx = sum(R[(c, e)]["decider_fixed_ticks"] for e in FAULT)
        bk = sum(R[(c, e)]["decider_broke_ticks"] for e in FAULT)
        ax.set_title(f"{LAB[c]}: mean {mn:.3f} without the decider → {mp:.3f} with it "
                     f"({mp - mn:+.3f}); ticks fixed {fx}, broken {bk}", loc="left", fontsize=13)
        ax.legend(loc="upper right", fontsize=9, ncol=2)
    axs[1].set_xticks(range(10)); axs[1].set_xticklabels([SHORT[e] for e in FAULT], fontsize=9)
    fig.subplots_adjust(top=0.86, hspace=0.25)
    save(fig, "30_decider_effect.png", title="What bev-decider changed, measured inside the same runs",
         sub="Each bev run replayed from its own saved answers with the decider's offsets removed: "
             "no run-to-run model noise · labels = ticks fixed / broken")


def fig_decider_picks():
    fams = ["A", "B", "C", "D"]
    fig, axs = plt.subplots(1, 2, figsize=(W, H), sharey=True)
    for ax, c in zip(axs, ["bev3", "bev2"]):
        vals = {"dec": [], "bel": [], "llama": []}
        for f in fams:
            ds = [R[(c, e)]["decider_picks"] for e in FAULT if e[3] == f]
            n = sum(d["n"] for d in ds); ln = sum(d["llama_n"] for d in ds)
            vals["dec"].append(sum(d["dec"] for d in ds) / n)
            vals["bel"].append(sum(d["bel"] for d in ds) / n)
            vals["llama"].append(sum(d["llama"] for d in ds) / ln if ln else 0)
        w = 0.27
        for k, (key, lab, col) in enumerate([("dec", "bev-decider's pick", "#17a589"),
                                             ("llama", "Llama diagnosticians' first pick", "#1f77b4"),
                                             ("bel", "belief's top case (code)", "#999999")]):
            bars = ax.bar([i + (k - 1) * w for i in range(4)], vals[key], w, color=col, label=lab)
            label_bars(ax, bars, size=9)
        alln = sum(R[(c, e)]["decider_picks"]["n"] for e in FAULT)
        tot = {k: sum(R[(c, e)]["decider_picks"][k] for e in FAULT) for k in ("dec", "bel", "flat", "llama",
                                                                                   "llama_n")}
        ax.set_title(f"{LAB[c]}: decider {tot['dec'] / alln:.2f} · Llama {tot['llama'] / tot['llama_n']:.2f} · "
                     f"belief {tot['bel'] / alln:.2f}\n(n={alln} decider calls; flat-case picks "
                     f"{tot['flat'] / alln:.0%})", fontsize=12)
        ax.set_xticks(range(4)); ax.set_xticklabels(["A: feed water", "B: tube leak", "C: fuel (wet coal,\nfeeder)",
                                                     "D: high-CV coal"], fontsize=10)
        ax.set_ylim(0, 1.15)
    axs[0].set_ylabel("share of decider calls where the pick is in the true group")
    axs[0].legend(loc="upper left", fontsize=9)
    fig.subplots_adjust(top=0.8, wspace=0.08)
    save(fig, "31_decider_picks_by_family.png", title="How often each source names the right cause",
         sub="On the ticks where bev-decider was called (after fault onset), by fault family")


def fig_letters():
    with_l = ["v2_tiebreak", "v2_nudge", "bev2"]
    no_l = ["v3", "bev3"]
    fams = ["A", "B", "C", "D"]
    fig, ax = plt.subplots(figsize=(W, H))

    def rate(cfgs, fam=None):
        rs = [r for c in cfgs for r in rows(c) if r.get("llama_first_pick_n") and (fam is None or r["episode"][3] == fam)]
        return sum(r["llama_first_pick_right"] for r in rs) / sum(r["llama_first_pick_n"] for r in rs)
    cats = ["all"] + fams
    a = [rate(with_l)] + [rate(with_l, f) for f in fams]
    b = [rate(no_l)] + [rate(no_l, f) for f in fams]
    b1 = ax.bar([i - 0.2 for i in range(5)], a, 0.4, color="#d62728", label="group letters in the prompt (v2 tiebreak, v2 nudge, bev2)")
    b2 = ax.bar([i + 0.2 for i in range(5)], b, 0.4, color="#1f77b4", label="no group letters (v3, bev3)")
    label_bars(ax, b1, size=11); label_bars(ax, b2, size=11)
    ax.set_xticks(range(5)); ax.set_xticklabels(["all families", "A: feed water", "B: tube leak", "C: fuel", "D: high-CV coal"])
    ax.set_ylim(0, 1.05); ax.set_ylabel("Llama's first pick in the true group (scored ticks)"); ax.legend(loc="upper left")
    fig.subplots_adjust(top=0.86)
    save(fig, "32_group_letter_shortcut.png", title="A prompt shortcut: the group letter halved the model's accuracy",
         sub="Same model (Llama 3.2 3B, NPU). With letters, the model tended to copy the most common letter "
             "instead of reading the facts · five independent board runs")


def fig_timeline(ep, name):
    cfgs = [c for c in ["single", "v2_nudge", "v3", "bev2", "bev3"] if (c, ep) in R]
    info = D["episodes"][ep]
    fig, ax = plt.subplots(figsize=(W, H * 0.75))
    lanes = ["belief"] + cfgs
    end = max(t["tick"] for t in D["ticks"][f"v3|{ep}"]) * 30 / 60 + 0.5
    for i, c in enumerate(lanes):
        src = D["ticks"][f"{'v3' if c == 'belief' else c}|{ep}"]
        for t in src:
            x = t["tick"] * 30 / 60
            if not t["scored"]:
                col = "#eeeeee"
            else:
                okk = t["bel_ok"] if c == "belief" else t["ok"]
                col = "#2ca02c" if okk else "#d62728"
            ax.barh(i, 0.5, left=x, color=col, height=0.7, linewidth=0)
        rr = R[("v3" if c == "belief" else c, ep)]
        v = rr["belief_group_top1"] if c == "belief" else rr["group_top1"]
        ax.text(end + 1, i, f"{v:.2f}", va="center", fontsize=12, fontweight="bold")
    ax.axvline(info["onset_min"], color="black", ls="--"); ax.text(info["onset_min"], -0.75, " fault onset", fontsize=10)
    if info.get("trip_min"):
        ax.axvline(info["trip_min"], color="red", ls="--"); ax.text(info["trip_min"], -0.75, " trip", color="red", fontsize=10)
    ax.set_yticks(range(len(lanes))); ax.set_yticklabels([LAB[c] for c in lanes]); ax.invert_yaxis()
    ax.set_xlabel("minutes into the episode"); ax.set_xlim(0, end + 6); ax.grid(False); ax.set_ylim(len(lanes) - 0.4, -1.1)
    ax.legend(handles=[Patch(color="#2ca02c", label="right group on top"), Patch(color="#d62728", label="wrong"),
                       Patch(color="#eeeeee", label="before onset, or quiet (no ranking yet)")], loc="lower right",
              bbox_to_anchor=(1, 1.0), ncol=3, fontsize=10)
    fig.subplots_adjust(top=0.8)
    save(fig, name, title=f"Tick by tick: {SHORT[ep].replace(chr(10), ' ')}",
         sub="Each cell = one 30 s tick; the number on the right = group top-1 for the episode")


def fig_screening():
    S = D["screening"]
    names = {"llama32-3b": "Llama 3.2 3B", "qwen3-1.7b": "Qwen3 1.7B", "gemma3-1b-qat": "Gemma 3 1B",
             "qwen25-0.5b": "Qwen2.5 0.5B"}
    fig, axs = plt.subplots(1, 3, figsize=(W, H * 0.85))
    for ax, key, title, fmt in [(axs[0], "prefill_tok_s", "Prefill (prompt) tok/s", "{:,.0f}"),
                                (axs[1], "decode_tok_s", "Decode (answer) tok/s", "{:.1f}"),
                                (axs[2], "verified_s", "One verified diagnosis, s", "{:.2f}")]:
        bars = ax.bar(range(4), [s[key] for s in S], color=["#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd"])
        label_bars(ax, bars, fmt, dy=max(s[key] for s in S) * 0.01, size=11)
        ax.set_xticks(range(4)); ax.set_xticklabels([names[s["model"]].replace(" ", "\n", 1) for s in S], fontsize=10)
        ax.set_title(title)
    fig.subplots_adjust(top=0.8, wspace=0.25)
    save(fig, "35_npu_model_screening.png", title="Four models on the Hexagon NPU (HTP0), llama.cpp b11371",
         sub="Pure Q4_0 weights, Q8_0 embedding, every layer on HTP0 · diagnosis = 700-token prompt + 60-token "
             "answer, plus a 350 + 30 verification",
         note="QIDK (SM8650) screening runs, 10 calls per model · llama-server -c 4096 -np 1 --cache-ram 0 · energy not measured")


def fig_temps():
    cfgs = ["v3", "bev2", "bev3"]
    eps = FAULT + ["ep_E01_fouling_drift", "ep_N01_normal"]
    fig, ax = plt.subplots(figsize=(W, H))
    w = 0.26
    for k, c in enumerate(cfgs):
        for i, e in enumerate(eps):
            r = R.get((c, e))
            if not r or r.get("chip_c_start") is None:
                continue
            x = i + (k - 1) * w
            ax.plot([x, x], [r["chip_c_start"], r["chip_c_end"]], color=COL[c], lw=3)
            ax.scatter([x], [r["chip_c_start"]], color="white", edgecolor=COL[c], s=40, zorder=3)
            ax.scatter([x], [r["chip_c_end"]], color=COL[c], s=40, zorder=3)
    for c in cfgs:
        ax.plot([], [], color=COL[c], lw=3, label=LAB[c])
    ax.scatter([], [], color="white", edgecolor="black", label="before the episode")
    ax.scatter([], [], color="black", label="after")
    ax.set_xticks(range(len(eps))); ax.set_xticklabels([SHORT[e] for e in eps], fontsize=8.5)
    ax.set_ylabel("hottest CPU/NPU zone, °C"); ax.legend(ncol=5, loc="upper center", bbox_to_anchor=(0.5, 1.08))
    fig.subplots_adjust(top=0.83)
    save(fig, "36_chip_temperature.png", title="Chip temperature before and after each episode",
         sub="The runner waits for the chip to cool before each episode · v3's episodes after its B01 restart "
             "started hot (cooling target taken from a hot reading)")


for f in (fig_accuracy_first4, fig_accuracy_all10, fig_heatmap, fig_quality, fig_helped_harmed, fig_wall_time,
          fig_call_latency, fig_tick_latency, fig_tokens, fig_tradeoff, fig_decider_effect, fig_decider_picks,
          fig_letters, fig_screening, fig_temps):
    f()
fig_timeline("ep_A01_fcv_seize", "33_timeline_A01.png")
fig_timeline("ep_B01_tube_leak", "34_timeline_B01.png")

# ---------------------------------------------------------------- flow diagrams (graphviz)
CODE = 'shape=box, style="rounded,filled", fillcolor="#f1f3f5", color="#868e96"'
NPU = 'shape=box, style="rounded,filled", fillcolor="#ffd8a8", color="#e67700", penwidth=1.6'
CPU = 'shape=box, style="rounded,filled", fillcolor="#d0ebff", color="#1c7ed6", penwidth=1.6'
BEV = 'shape=box, style="rounded,filled", fillcolor="#c3fae8", color="#0ca678", penwidth=1.8'
DATA = 'shape=cylinder, style=filled, fillcolor="#fff9db", color="#c9a400"'
OUTN = 'shape=box, style="rounded,filled,bold", fillcolor="#e6fcf5", color="#087f5b", penwidth=2'
HEAD = ('digraph G {{ graph [rankdir=TB, fontname="DejaVu Sans", fontsize=24, labelloc=t, labeljust=l, '
        'label=<<b>{title}</b><br/><font point-size="14">{sub}</font><br/> >, pad=0.4, nodesep=0.5, ranksep=0.55, '
        'bgcolor=white, newrank=true, splines=spline];\n'
        ' node [fontname="DejaVu Sans", fontsize=13, margin="0.18,0.08"]; '
        'edge [fontname="DejaVu Sans", fontsize=11, color="#495057", penwidth=1.3];\n')
LEGEND = ('subgraph cluster_key { label="key"; fontsize=12; style="rounded,dashed"; color="#adb5bd";\n'
          ' k1 [label="code (laptop)", ' + CODE + ']; k2 [label="model · NPU (HTP0)", ' + NPU + '];\n'
          ' k3 [label="model · CPU", ' + CPU + ']; k4 [label="System One model · NPU", ' + BEV + '];\n'
          ' {rank=same; k1; k2; k3; k4} k1 -> k2 -> k3 -> k4 [style=invis]; }\n')


def multi_flow(title, sub, notes_label, npu_nodes, cpu_label, cpu_nodes, note_edges, gate_label, decider=False,
               ver_edge=True):
    src = HEAD.format(title=title, sub=sub)
    src += (' plant [label="Plant sensors\\n6 tags · 5 s samples", ' + DATA + '];\n'
            ' notes [label="Engineer notes\\n' + notes_label + '", ' + DATA + '];\n'
            ' {rank=same; plant; notes}\n'
            ' subgraph cluster_hard { label="Hard path · code · every tick · < 200 ms"; style=rounded; color="#868e96"; fontsize=14;\n'
            '  sens [label="Sensor agent\\nL1 checks → facts (t84.F1 …)", ' + CODE + '];\n'
            '  tri [label="Triage\\nQUIET → no model work", ' + CODE + '];\n'
            '  ret [label="Retriever + belief\\n13-case library · log-odds ranking", ' + CODE + '];\n'
            '  {rank=same; sens; tri; ret} sens -> tri -> ret; }\n'
            ' bb [label="Blackboard\\none writer per section", ' + DATA + '];\n'
            ' sch [label="Scheduler · one queue per lane · priorities P1–P4\\nask a side again only when its evidence changes", ' + CODE + '];\n'
            ' plant -> sens; ret -> sch [label="  non-quiet tick"]; ret -> bb [style=dashed, arrowhead=none];\n'
            ' subgraph cluster_npu { label="NPU lane :8080 · Llama 3.2 3B Q4_0 · HTP0"; style="rounded,filled"; fillcolor="#fff4e6"; color="#e67700"; fontsize=14;\n'
            + npu_nodes + ' }\n'
            ' subgraph cluster_cpu { label="' + cpu_label + '"; style="rounded,filled"; fillcolor="#e7f5ff"; color="#1c7ed6"; fontsize=14;\n'
            + cpu_nodes + ' }\n'
            ' sch -> dw; sch -> dh;\n' + note_edges)
    if ver_edge:
        src += ' sch -> ver; ver -> gate [label="  pass / fail\\n  (only lowers confidence)"];\n'
    if decider:
        src += (' subgraph cluster_bev { label="Decider lane :8082 · bev-decide · HTP0"; style="rounded,filled"; fillcolor="#e6fcf5"; color="#0ca678"; fontsize=14;\n'
                '  dec [label="bev-decider 0.4B · System One\\nQwen3 (20 layers) + decision head · Q8_0\\none forward pass, no text · median 0.37 s\\n'
                'options: belief top 3 + diagnosticians\' top 3", ' + BEV + ']; }\n'
                ' sch -> dec [label="  on evidence change"]; dw -> dec [style=dotted, label=" their top 3"];\n'
                ' dec -> gate [label="  probability per option"];\n')
    src += (' gate [label=' + gate_label + ', ' + CODE + ', penwidth=2];\n'
            ' dw -> gate [label="  checked answer\\n  (line numbers)"]; dh -> gate;\n'
            ' bb -> gate [style=dashed];\n'
            ' pub [label="Published assessment every tick\\nplant state (code) · top-3 causes · actions from the catalogue", ' + OUTN + '];\n'
            ' gate -> pub;\n' + LEGEND + '}')
    return src


def dot(name, src):
    p = OUT / f"{name}.dot"
    p.write_text(src)
    subprocess.run(["dot", "-Tpng", "-Gdpi=170", str(p), "-o", str(OUT / f"{name}.png")], check=True)
    subprocess.run(["dot", "-Tsvg", str(p), "-o", str(OUT / f"{name}.svg")], check=True)
    p.unlink()
    made.append(f"{name}.png")


DIAG = ('  dw [label="Water diagnostician\\ndrum level · feed · steam flow\\n~750-token prompt · ≤ 60-token answer{x}", ' + NPU + '];\n'
        '  dh [label="Heat diagnostician\\nbed temp · pressure · steam temp\\n~750-token prompt · ≤ 60-token answer{x}", ' + NPU + '];\n'
        '  {{rank=same; dw; dh}}\n')

dot("01_flow_single_agent", HEAD.format(title="Single agent (baseline)",
    sub="one long model call per tick, and the tick waits for it · Llama 3.2 3B Q4_0 on the NPU") +
    ' plant [label="Plant sensors\\n6 tags · 5 s samples", ' + DATA + '];\n'
    ' subgraph cluster_code { label="Agent code (laptop)"; style=rounded; color="#868e96"; fontsize=14;\n'
    '  l0 [label="L0 ingest\\n60-min window", ' + CODE + ']; l1 [label="L1 checks\\n→ facts", ' + CODE + '];\n'
    '  l2 [label="L2 triage", ' + CODE + ']; l3 [label="L3 retrieve\\ncases · notes · records", ' + CODE + '];\n'
    '  bel [label="Belief\\nlog-odds", ' + CODE + '];\n'
    '  {rank=same; l0; l1; l2; l3; bel} l0 -> l1 -> l2 -> l3 -> bel; }\n'
    ' subgraph cluster_npu { label="NPU lane :8080 · Llama 3.2 3B · HTP0 · one call at a time"; style="rounded,filled"; fillcolor="#fff4e6"; color="#e67700"; fontsize=14;\n'
    '  l4 [label="L4 diagnose\\n~1,900-token prompt\\nfree JSON ≤ 256 tokens · median 13.8 s", ' + NPU + '];\n'
    '  l5 [label="L5 verify (conditional)\\n~1,100-token prompt\\nfree JSON ≤ 256 tokens", ' + NPU + '];\n'
    '  {rank=same; l4; l5} l4 -> l5; }\n'
    ' l6 [label="L6 gate\\ncitations checked · the model\'s order wins · actions from catalogue", ' + CODE + ', penwidth=2];\n'
    ' l7 [label="L7 memory", ' + CODE + '];\n'
    ' pub [label="Published assessment\\n(the tick waits for both calls: 81 of 500 ticks over 30 s)", ' + OUTN + '];\n'
    ' plant -> l0; bel -> l4 [label="  non-quiet tick"]; l5 -> l6; l6 -> l7 -> pub;\n'
    ' l2 -> l6 [style=dashed, label="  QUIET: no model call"];\n' + LEGEND + "}")

dot("02_flow_multi_v2", multi_flow(
    "Multi-agent v2", "small jobs on two lanes · grammar-constrained answers · case lines tagged with group letters · "
    "Gemma note reader · merge rule model / tiebreak / nudge",
    "→ note reader", DIAG.format(x="\\n(case lines with group letters)"),
    "CPU lane :8081 · Gemma 3 1B · 6 threads",
    '  ver [label="Verifier\\npass / fail the top claims", ' + CPU + '];\n'
    '  nr [label="Note reader\\nnote → coded facts", ' + CPU + '];\n',
    ' notes -> nr; nr -> dw [label="  note facts"]; nr -> dh;\n',
    '"Gate + merge rule\\nchecks every citation · model | tiebreak | nudge"'))

dot("03_flow_multi_v3", multi_flow(
    "Multi-agent v3 (current best)", "no group letters · raw note text straight to the diagnosticians · "
    "merge rule hybrid with the filler-case guard",
    "raw text, filtered by plant side", DIAG.format(x="\\nfacts + cases + raw notes"),
    "CPU lane :8081 · Gemma 3 1B · 6 threads",
    '  ver [label="Verifier (conditional)\\npass / fail the top claims", ' + CPU + '];\n',
    ' notes -> dw; notes -> dh;\n',
    '"Gate + merge rule hybrid\\nbelief weak or tied → the model\'s picks lead\\nbelief clear → nudge (+0.35 / +0.175, cap 1.2)\\n'
    'a filler case is never promoted"'))

dot("04_flow_bev_decider_2", multi_flow(
    "bev-decider-2", "accuracy.yaml (v2 prompts with group letters, Llama 3B on both lanes, verifier off) "
    "+ merge rule nudge + the System One decider",
    "→ note reader", DIAG.format(x="\\n(case lines with group letters)"),
    "CPU lane :8081 · Llama 3.2 3B · 6 threads",
    '  nr [label="Note reader\\nnote → coded facts", ' + CPU + '];\n',
    ' notes -> nr; nr -> dw [label="  note facts"]; nr -> dh;\n',
    '"Gate + merge rule nudge\\ndiagnosticians\' + decider\'s offsets summed, cap 1.2 per case\\n'
    'the decider never pushes a filler case"', decider=True, ver_edge=False))

dot("05_flow_bev_decider_3", multi_flow(
    "bev-decider-3 (v3 + System One decider)", "exactly v3 plus the decider · three model servers on the board, "
    "two of them sharing the Hexagon NPU",
    "raw text, filtered by plant side", DIAG.format(x="\\nfacts + cases + raw notes"),
    "CPU lane :8081 · Gemma 3 1B · 6 threads",
    '  ver [label="Verifier (conditional)\\npass / fail the top claims", ' + CPU + '];\n',
    ' notes -> dw; notes -> dh;\n',
    '"Gate + merge rule hybrid\\nbelief weak or tied → the model\'s picks lead (the decider can\'t change the top)\\n'
    'belief clear → nudge with diagnosticians\' + decider\'s offsets (cap 1.2)"', decider=True))

dot("06_board_deployment", HEAD.format(title="Deployment: laptop and QIDK board",
    sub="the agent runs on the laptop; every model call goes over USB (adb forward) to persistent servers on the board") +
    ' agent [label="Laptop · FieldMind agent (Python)\\nhard path · scheduler · gate · benchmark runner + monitor", ' + CODE + ', penwidth=2];\n'
    ' subgraph cluster_board { label="QIDK · Snapdragon 8 Gen 3 (SM8650) · 11.1 GiB"; style=rounded; color="#343a40"; fontsize=15;\n'
    '  subgraph cluster_htp { label="Hexagon NPU (HTP0, v75 libraries)"; style="rounded,filled"; fillcolor="#fff4e6"; color="#e67700"; fontsize=14;\n'
    '   s1 [label="llama-server :8080\\nLlama 3.2 3B · Q4_0 + Q8_0 embedding\\n29/29 layers + output on HTP0", ' + NPU + '];\n'
    '   s3 [label="bev-decide :8082 (bev2, bev3)\\nbev-decider 0.4B · Q8_0\\n21/21 layers on HTP0", ' + BEV + '];\n'
    '   {rank=same; s1; s3} }\n'
    '  subgraph cluster_cpu { label="Kryo CPU"; style="rounded,filled"; fillcolor="#e7f5ff"; color="#1c7ed6"; fontsize=14;\n'
    '   s2 [label="llama-server :8081 · 6 threads\\nGemma 3 1B (v2, v3, bev3) · Llama 3B (bev2)", ' + CPU + ']; }\n'
    '  lib [label="llama.cpp b11371 (99b95488)\\nlibggml-hexagon · libggml-htp-v75", ' + DATA + ']; }\n'
    ' agent -> s1 [label="  HTTP · adb forward"]; agent -> s2; agent -> s3;\n'
    ' s1 -> lib [style=dotted, arrowhead=none]; s2 -> lib [style=dotted, arrowhead=none]; s3 -> lib [style=dotted, arrowhead=none];\n'
    "}")

print(f"wrote {len(made)} figures to {OUT.relative_to(ROOT)}/")
for m in made:
    print(" ", m)
