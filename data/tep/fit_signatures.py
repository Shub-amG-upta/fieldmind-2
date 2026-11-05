"""
Fits the TEP case library from the official FAULTY TRAINING runs
(human decision 2026-11-07: signatures FITTED on the training split, frozen in
a commit before any test run is put through the agent). Test runs are never
read here.

Method (pre-registered in the approved plan, docs: reports/b2_tep_pack.md):
  * the agent's own signature: OLS slope (units/min) of each tag over the
    signature window (configs/tep.yaml checks.signature_window_min = 60 min =
    20 samples), mapped to UP / DOWN / FLAT by the deadband of
    configs/tep.yaml checks.bands (fitted on fault-FREE runs). The same
    arithmetic as fieldmind.agent.orchestrator.slopes_10min and
    l1_symbolize.direction_and_band (a test asserts they agree);
  * post-onset windows: every window ending at or after the first faulty sample
    (training runs: sample 21, after 1 h);
  * a run SHOWS (tag, DIR) when DIR (UP or DOWN) is the tag's most frequent
    direction over that run's post-onset windows;
  * a triple (tag, DIR, "*") enters the fault's case when >= THRESHOLD of the
    runs show it. THRESHOLD = 0.70 is ASSUMED (range 0.60-0.90; it sets case
    size and overlap); the case sizes at 0.60 and 0.80 are recorded too;
  * moving triples only: a FLAT triple would be shared by almost every case
    (healthy deadband = p85, so most tags read FLAT most of the time).
  * LEVEL and VARIABILITY triples (human decision 2026-11-07, after the
    movement-only fit gave 12 empty and 2 identical signatures -- recorded in
    reports/b2_tep_pack.md): a run shows (tag, HIGH|LOW) when the tag is above
    alarm_hi / below alarm_lo (configs/tep.yaml limits) on most of its
    post-onset samples, and (tag, NOISY) when the 60-min spread of its
    sample-to-sample changes is above checks.variability on most post-onset
    windows -- the same quantities the TEP pack's LIMIT and PATTERN facts test
    at every tick. Same >= THRESHOLD rule across runs.
Faults with no triple at the threshold keep an EMPTY signature (recorded,
not tuned).

    python -m data.tep.fit_signatures
"""

from __future__ import annotations

import json

import numpy as np
import yaml

from .convert import CASE_ID, FAULTS, ONSET_SAMPLE, ROOT, SAMPLE_S, TAGS, read_runs

N_FIT = 100                 # training runs per fault used (of 500): DESIGN, plenty for a vote
THRESHOLD = 0.70            # ASSUMED, range 0.60-0.90
SENSITIVITY = (0.60, 0.80)
OUT = ROOT / "data/kb_tep/case_library.json"

# case text: the fault's mechanism without stream numbers or any benchmark wording
CASE_TEXT = {
    1: "Feed composition step: ratio of A to C in the A+C feed changes, B fixed",
    2: "Feed composition step: B content of the A+C feed changes, A/C ratio fixed",
    3: "D feed temperature step",
    4: "Reactor cooling water inlet temperature step",
    5: "Condenser cooling water inlet temperature step",
    6: "Loss of the A feed",
    7: "Pressure loss in the C supply header (reduced availability of the A+C feed)",
    8: "Random variation in the A, B, C composition of the A+C feed",
    9: "Random variation in the D feed temperature",
    10: "Random variation in the C feed temperature",
    11: "Random variation in the reactor cooling water inlet temperature",
    12: "Random variation in the condenser cooling water inlet temperature",
    13: "Slow drift in the reaction kinetics",
    14: "Reactor cooling water valve sticking",
    15: "Condenser cooling water valve sticking",
    16: "Unclassified disturbance (no mechanism published): pattern 16",
    17: "Unclassified disturbance (no mechanism published): pattern 17",
    18: "Unclassified disturbance (no mechanism published): pattern 18",
    19: "Unclassified disturbance (no mechanism published): pattern 19",
    20: "Unclassified disturbance (no mechanism published): pattern 20",
}


def window_slopes(X: np.ndarray, w: int) -> np.ndarray:
    """(windows, tags) OLS slope per minute; window i ends at sample i + w - 1.
    Same arithmetic as l1_checks._slope_per_min on index time (dt = SAMPLE_S)."""
    i = np.arange(w, dtype=float)
    ic = i - i.mean()
    den = (ic ** 2).sum()
    out = np.empty((X.shape[0] - w + 1, X.shape[1]))
    for s in range(out.shape[0]):
        seg = X[s:s + w]
        out[s] = ((seg - seg.mean(axis=0)) * ic[:, None]).sum(axis=0) / den * (60.0 / SAMPLE_S)
    return out


def directions(slopes: np.ndarray, dead: np.ndarray) -> np.ndarray:
    """+1 UP, -1 DOWN, 0 FLAT, as l1_symbolize.direction_and_band (FLAT when
    |slope| < deadband)."""
    return np.where(np.abs(slopes) < dead, 0, np.sign(slopes)).astype(int)


def window_step_sd(X: np.ndarray, w: int) -> np.ndarray:
    """(windows, tags) population sd of the w-1 changes in each window (as
    fieldmind/assets/tep.variability)."""
    d = np.diff(X, axis=0)
    return np.stack([d[s:s + w - 1].std(axis=0) for s in range(X.shape[0] - w + 1)])


def fit(training: dict, bands: dict, w: int, lo=None, hi=None, var_thr=None) -> dict:
    dead = np.array([bands[t][0] for t in TAGS])
    onset = ONSET_SAMPLE[500]                     # first faulty sample index (0-based)
    res = {}
    for f in FAULTS:
        shows = np.zeros((2, len(TAGS)))          # [UP, DOWN] run counts
        lvl = np.zeros((2, len(TAGS)))            # [HIGH, LOW] run counts
        noisy = np.zeros(len(TAGS))
        runs = [r for (r, ff) in training if ff == f]
        for r in runs:
            X = training[(r, f)]
            if lo is not None:
                post_x = X[onset:]
                lvl[0] += (post_x > hi).mean(axis=0) > 0.5
                lvl[1] += (post_x < lo).mean(axis=0) > 0.5
                v = window_step_sd(X, w)[max(0, onset - w + 1):]
                noisy += (v > var_thr).mean(axis=0) > 0.5
            d = directions(window_slopes(X, w), dead)
            post = d[max(0, onset - w + 1):]       # windows ending at or after the onset
            for j in range(len(TAGS)):
                up, dn, fl = (post[:, j] == 1).sum(), (post[:, j] == -1).sum(), (post[:, j] == 0).sum()
                if up > max(dn, fl):
                    shows[0, j] += 1
                elif dn > max(up, fl):
                    shows[1, j] += 1
        res[f] = {"n_runs": len(runs), "share_up": (shows[0] / len(runs)).tolist(),
                  "share_down": (shows[1] / len(runs)).tolist(),
                  "share_high": (lvl[0] / len(runs)).tolist(), "share_low": (lvl[1] / len(runs)).tolist(),
                  "share_noisy": (noisy / len(runs)).tolist()}
    return res


def triples(stats: dict, thr: float) -> dict:
    """Signature in the library's string form "tag|DIR|BAND": weight (a tag may
    carry a movement, a level and a variability triple at once)."""
    out = {}
    for j, t in enumerate(TAGS):
        if stats["share_up"][j] >= thr:
            out[f"{t}|UP|*"] = 1.0
        elif stats["share_down"][j] >= thr:
            out[f"{t}|DOWN|*"] = 1.0
        if stats.get("share_high", [0] * len(TAGS))[j] >= thr:
            out[f"{t}|HIGH|-"] = 1.0
        elif stats.get("share_low", [0] * len(TAGS))[j] >= thr:
            out[f"{t}|LOW|-"] = 1.0
        if stats.get("share_noisy", [0] * len(TAGS))[j] >= thr:
            out[f"{t}|NOISY|-"] = 1.0
    return out


def _support(stats: dict, key: str) -> float:
    t, d, _ = key.split("|")
    j = TAGS.index(t)
    return round(stats[{"UP": "share_up", "DOWN": "share_down", "HIGH": "share_high",
                        "LOW": "share_low", "NOISY": "share_noisy"}[d]][j], 2)


def build() -> tuple[dict, dict]:
    cfg = yaml.safe_load((ROOT / "configs/tep.yaml").read_text())
    bands = cfg["checks"]["bands"]
    w = int(cfg["checks"]["signature_window_min"] * 60 / SAMPLE_S)
    lim = cfg["checks"]["limits"]
    lo = np.array([lim[t]["alarm_lo"]["value"] for t in TAGS])
    hi = np.array([lim[t]["alarm_hi"]["value"] for t in TAGS])
    var_thr = np.array([cfg["checks"]["variability"]["thresholds"][t] for t in TAGS])
    training = read_runs("TEP_Faulty_Training.RData", N_FIT)
    stats = fit(training, bands, w, lo, hi, var_thr)
    cases, summary = [], {}
    for f, st in stats.items():
        sig = triples(st, THRESHOLD)
        support = {k: _support(st, k) for k in sig}
        moving = ", ".join(f"{k.split('|')[0].replace('_', ' ')} {k.split('|')[1].lower()}"
                           for k in list(sig)[:6])
        cases.append({
            "case_id": CASE_ID[f], "family": FAULTS[f][1], "title": CASE_TEXT[f],
            "root_cause": CASE_TEXT[f],
            "source": f"FITTED: faulty training runs 1-{N_FIT} (Rieth et al. 2017), data/tep/fit_signatures.py",
            "discriminating_evidence": (f"In training runs: {moving}." if sig else
                                        "No consistent direction in the training runs (pattern not separable by slope)."),
            "signature": sig, "contradicting_signature": {},
            "_fit": {"threshold": THRESHOLD, "n_runs": st["n_runs"], "support": support},
            "equipment": "", "actions": [], "provenance": "curated_case", "weight": 1.0})
        summary[CASE_ID[f]] = {"size": len(sig), **{f"size_at_{s}": len(triples(st, s)) for s in SENSITIVITY}}
    lib = {"_comment": "FITTED on the official faulty TRAINING runs (human decision 2026-11-07); frozen before "
                       "any test run is put through the agent. Generated by data/tep/fit_signatures.py -- do not "
                       "edit by hand. Ids are neutral (no benchmark numbering).",
           "cases": cases}
    return lib, summary


def main() -> None:
    lib, summary = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(lib, indent=1))
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"{'case':6s} {'type':17s} {'size@0.70':>9s} {'@0.60':>6s} {'@0.80':>6s}  signature")
    for c in lib["cases"]:
        s = summary[c["case_id"]]
        print(f"{c['case_id']:6s} {c['family']:17s} {s['size']:9d} {s['size_at_0.6']:6d} {s['size_at_0.8']:6d}  "
              + ", ".join(f"{k.split('|')[0]}:{k.split('|')[1]}" for k in list(c["signature"])[:6])
              + (" ..." if len(c["signature"]) > 6 else ""))


if __name__ == "__main__":
    main()
