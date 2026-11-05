#!/usr/bin/env python3
"""Two charts for the bev-decider-3 slides, from ppt_handoff/bev3_slides/data/*.csv.

    /usr/bin/python3 -I ppt_handoff/tools/bev3_slides_figures.py
"""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "ppt_handoff/bev3_slides/data"
OUT = ROOT / "ppt_handoff/bev3_slides/figures"
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.25, "legend.frameon": False})
NOTE = ("QIDK (SM8650) board runs · reporting episodes · one run per episode · agent code on the laptop, "
        "model calls on the board · energy not measured · all plant data simulated")
V3, BEV3, BEL, NOD = "#1f77b4", "#17a589", "#bbbbbb", "#7fd1c0"


def rd(name):
    return list(csv.DictReader(open(DATA / name)))


def f(x):
    return None if x in ("", None) else float(x)


def head(fig, title, sub):
    fig.text(0.01, 0.995, title, fontsize=20, fontweight="bold", ha="left", va="top")
    fig.text(0.01, 0.94, sub, fontsize=12, color="#444", ha="left", va="top")
    fig.text(0.01, 0.005, NOTE, fontsize=8.5, color="#777", ha="left", va="bottom")


# 40: accuracy, v3 against bev3 ---------------------------------------------------
E = [r for r in rd("bev3_vs_v3_per_episode.csv") if r["family"] in "ABCD"]
S = {(r["episode_set"], r["metric"]): r for r in rd("bev3_vs_v3_summary.csv")}
lab = [r["episode"][3:6] + ("*" if r["heldout_true_cause"] == "True" else "") for r in E]
fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13.33, 7.5), gridspec_kw={"width_ratios": [4, 1.3]})
x = range(len(E))
w = 0.27
b1 = ax.bar([i - w for i in x], [f(r["v3_group_top1"]) for r in E], w, color=V3, label="v3")
b2 = ax.bar(list(x), [f(r["bev3_group_top1"]) for r in E], w, color=BEV3, label="bev-decider-3 (v3 + decider)")
ax.bar([i + w for i in x], [f(r["belief_group_top1"]) for r in E], w, color=BEL, label="belief alone (code only)")
for bars in (b1, b2):
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.012, f"{b.get_height():.2f}", ha="center", va="bottom", fontsize=9, rotation=90)
ax.set_xticks(list(x)); ax.set_xticklabels(lab); ax.set_ylim(0, 1.18); ax.set_ylabel("group top-1")
ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.09))
k = "10 fault episodes"
vals = [f(S[(k, "group top-1 (mean of episodes)")]["v3"]), f(S[(k, "group top-1 (mean of episodes)")]["bev3"]),
        f(S[(k, "group top-1 (mean of episodes)")]["bev3_decider_removed_replay"]),
        f(S[(k, "group top-1 (mean of episodes)")]["belief_alone"])]
bars = ax2.bar(range(4), vals, color=[V3, BEV3, NOD, BEL])
for b in bars:
    ax2.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.01, f"{b.get_height():.3f}", ha="center", fontsize=10)
ax2.set_xticks(range(4)); ax2.set_xticklabels(["v3", "bev3", "bev3,\ndecider\nremoved\n(replay)", "belief"], fontsize=10)
ax2.set_ylim(0, 1.1); ax2.set_title("mean of 10", fontsize=13)
fig.subplots_adjust(top=0.82, wspace=0.12)
head(fig, "bev-decider-3 against v3: accuracy on ten fault episodes",
     "* C01, C03: true cause held out of the library (group credit only) · 'decider removed' = the bev3 run "
     "replayed from its own answers without the decider's offsets")
fig.savefig(OUT / "40_bev3_vs_v3_accuracy.png", dpi=200, bbox_inches="tight", facecolor="white")
plt.close(fig)

# 41: where the time goes in one model call ----------------------------------------
C = {(r["system"], r["agent"]): r for r in rd("model_call_costs.csv")}
rows = [("single agent", "diagnostician", "Single-agent diagnosis\nLlama 3.2 3B · NPU"),
        ("v3", "diagnostician", "v3 diagnosis\nLlama 3.2 3B · NPU"),
        ("v3", "verifier", "v3 verification\nGemma 3 1B · CPU"),
        ("bev3", "decider", "bev-decider decision\n0.4B · NPU · System One")]
fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13.33, 7.5), gridspec_kw={"width_ratios": [2.2, 1]})
y = range(len(rows))
pre = [f(C[(s, a)]["mean_prefill_s"]) for s, a, _ in rows]
dec = [f(C[(s, a)]["mean_decode_s"]) for s, a, _ in rows]
tot = [f(C[(s, a)]["mean_call_s"]) for s, a, _ in rows]
oth = [max(0.0, t - p - d) for t, p, d in zip(tot, pre, dec)]
ax.barh(y, pre, color="#4dabf7", label="prefill (read the prompt)")
ax.barh(y, dec, left=pre, color="#ff6b6b", label="decode (write the answer, token by token)")
ax.barh(y, oth, left=[p + d for p, d in zip(pre, dec)], color="#dee2e6", label="other (HTTP, head, sampling)")
for i, (s, a, _) in enumerate(rows):
    r = C[(s, a)]
    ax.text(tot[i] + 0.2, i, f"{tot[i]:.2f} s  ·  {r['mean_prompt_tokens']} in / {float(r['mean_answer_tokens']):.0f} out",
            va="center", fontsize=11)
ax.set_yticks(list(y)); ax.set_yticklabels([l for _, _, l in rows]); ax.invert_yaxis()
ax.set_xlabel("mean seconds per call (board timings)"); ax.set_xlim(0, 21)
ax.legend(loc="lower right", fontsize=10)
ax.set_title("One model call, split by phase", fontsize=14, loc="left")
# right: total model time on the NPU/CPU for the 12 episodes, v3 against bev3
parts = [("diagnostician", "#1f77b4"), ("verifier", "#ff922b"), ("decider", BEV3)]
for j, sysn in enumerate(["v3", "bev3"]):
    left = 0
    for a, col in parts:
        v = f(C[(sysn, a)]["total_call_time_s"]) if (sysn, a) in C else 0
        ax2.bar(j, v, bottom=left, color=col, label=a if j == 1 else None)
        if v:
            ax2.text(j, left + v / 2, f"{v:.0f} s", ha="center", va="center", fontsize=10, color="white", fontweight="bold")
        left += v
    ax2.text(j, left + 20, f"{left:.0f} s", ha="center", fontsize=11, fontweight="bold")
ax2.set_xticks([0, 1]); ax2.set_xticklabels(["v3", "bev3"]); ax2.set_ylabel("total model-call time, 12 episodes (s)")
ax2.legend(fontsize=10, loc="upper center", bbox_to_anchor=(0.5, -0.07), ncol=3)
ax2.set_ylim(0, 2250); ax2.set_title("Total model time, 12 episodes", fontsize=14, loc="left")
fig.subplots_adjust(top=0.84, wspace=0.35)
head(fig, "Where the time goes: generating text against deciding",
     "A System One decision has no decode phase · in bev3 it was added beside the Llama calls, so total model time rose")
fig.savefig(OUT / "41_call_time_split.png", dpi=200, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("wrote 40_bev3_vs_v3_accuracy.png, 41_call_time_split.png")
