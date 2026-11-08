"""
Statistics of the Cranfield NORMAL data sets (T1, T2, T3), for calibrating
L1 thresholds in the Cranfield asset pack. Fault data sets are NOT read here.

Per tag: range, robust range, per-sample step noise, lag-1 autocorrelation,
the 3-min MAD (the stuck-instrument check), and the distribution of the
least-squares slope (units/min) over the 3, 5 and 10-min windows the L1 RATE
checks and the signature use. Windows are taken every 30 s (one per tick).

Normal operation here INCLUDES the deliberate set-point changes of the
training runs (paper §2.3.1, Table 2): they are part of normal behaviour, as
the boiler's OU load swings are, so thresholds fitted to these numbers do not
fire on a set-point change.

Writes data/reference/cranfield/fingerprint.json. Host-side (numpy, scipy).
    python -m data.cranfield.fingerprint
"""

from __future__ import annotations

import json

import numpy as np

from .convert import MAT_DIR, ROOT, TAGS, TRAINING, VARIABLES, _unpack

OUT = ROOT / "data/reference/cranfield/fingerprint.json"
WINDOWS_MIN = (3, 5, 10)
STEP_S = 30
# Accuracy-fixes step 2b (pre-registered, reports/accuracy_fixes.md): the chance that ANY
# state-raising check fires on a healthy tick is held at ALPHA_F (DESIGN, the conventional 99 %
# control limit; range 0.005-0.05), Sidak over m = tags x kinds (limit, rate).
ALPHA_F, KINDS = 0.01, 2


def _slopes(x: np.ndarray, win: int) -> np.ndarray:
    """OLS slope per minute over every `win`-sample window starting each 30 s."""
    t = np.arange(win, dtype=float)
    tc = t - t.mean()
    den = (tc ** 2).sum()
    out = [((x[s:s + win] - x[s:s + win].mean()) * tc).sum() / den * 60.0
           for s in range(0, len(x) - win + 1, STEP_S)]
    return np.asarray(out)


def _mad3(x: np.ndarray) -> np.ndarray:
    win = 180
    return np.asarray([np.median(np.abs(x[s:s + win] - np.median(x[s:s + win])))
                       for s in range(0, len(x) - win + 1, STEP_S)])


def sidak(alpha_f: float, m: int) -> float:
    """Per-check level that keeps the family-wise rate at alpha_f over m independent checks."""
    return 1.0 - (1.0 - alpha_f) ** (1.0 / m)


def joint_q(x: np.ndarray, q: float) -> tuple[float, bool]:
    """Empirical q-quantile of x; the max (or min) when x holds fewer than 1/(1-q) or 1/q
    values (recorded as `at_extreme`)."""
    tail = min(q, 1.0 - q)
    if len(x) * tail < 1.0:
        return float(x.max() if q > 0.5 else x.min()), True
    return float(np.quantile(x, q)), False


def build() -> dict:
    import scipy.io as sio
    _unpack()
    T = sio.loadmat(MAT_DIR / "Training.mat")
    sets = {k: T[k] for k in TRAINING}
    out = {"_source": "Cranfield 2015 benchmark, normal sets T1-T3 (calibration only); "
                      "data/cranfield/fingerprint.py",
           "sample_period_s": 1.0,
           "n_samples": {k: int(v.shape[0]) for k, v in sets.items()},
           "tags": {}}
    a = sidak(ALPHA_F, KINDS * len(VARIABLES))
    out["joint"] = {"alpha_family": ALPHA_F, "m": KINDS * len(VARIABLES), "alpha_per_check": a}
    for j, (tag, loc, desc, unit) in enumerate(VARIABLES):
        xs = [v[:, j] for v in sets.values()]
        allx = np.concatenate(xs)
        steps = np.concatenate([np.diff(x) for x in xs])
        ac = [float(np.corrcoef(x[:-1], x[1:])[0, 1]) if x.std() > 0 else None for x in xs]
        rec = {"location": loc, "description": desc, "unit": unit,
               "min": float(allx.min()), "max": float(allx.max()),
               "p0_1": float(np.percentile(allx, 0.1)), "p99_9": float(np.percentile(allx, 99.9)),
               "median": float(np.median(allx)),
               "step_sd": float(steps.std()),
               "step_abs_p99_99": float(np.percentile(np.abs(steps), 99.99)),
               "step_abs_max": float(np.abs(steps).max()),
               "lag1_ac": ac,
               "mad_3min_min": float(np.concatenate([_mad3(x) for x in xs]).min()),
               "mad_3min_p1": float(np.percentile(np.concatenate([_mad3(x) for x in xs]), 1)),
               "slope_abs": {}}
        for w in WINDOWS_MIN:
            s = np.abs(np.concatenate([_slopes(x, w * 60) for x in xs]))
            rec["slope_abs"][f"{w}min"] = {"p50": float(np.percentile(s, 50)),
                                           "p85": float(np.percentile(s, 85)),
                                           "p99_7": float(np.percentile(s, 99.7)),
                                           "max": float(s.max()), "n": int(len(s))}
        s5 = np.abs(np.concatenate([_slopes(x, 5 * 60) for x in xs]))
        lo, lo_x = joint_q(allx, a / 2)
        hi, hi_x = joint_q(allx, 1 - a / 2)
        rt, rt_x = joint_q(s5, 1 - a)
        rec["joint"] = {"lo": lo, "hi": hi, "rate": rt, "n_values": int(len(allx)),
                        "n_rate_windows": int(len(s5)),
                        "at_extreme": [k for k, x in (("lo", lo_x), ("hi", hi_x), ("rate", rt_x)) if x]}
        out["tags"][tag] = rec
    return out


def main() -> None:
    fp = build()
    OUT.write_text(json.dumps(fp, indent=1))
    print(f"wrote {OUT.relative_to(ROOT)}  samples {fp['n_samples']}")
    print(f"{'tag':27s} {'unit':6s} {'p0.1':>9s} {'p99.9':>9s} {'step sd':>9s} "
          f"{'mad3 min':>9s} {'|s| p85 10m':>11s} {'p99.7 5m':>10s} {'p99.7 10m':>10s}")
    for tag in TAGS:
        r = fp["tags"][tag]
        print(f"{tag:27s} {r['unit']:6s} {r['p0_1']:9.4g} {r['p99_9']:9.4g} {r['step_sd']:9.3g} "
              f"{r['mad_3min_min']:9.3g} {r['slope_abs']['10min']['p85']:11.3g} "
              f"{r['slope_abs']['5min']['p99_7']:10.3g} {r['slope_abs']['10min']['p99_7']:10.3g}")


if __name__ == "__main__":
    main()
