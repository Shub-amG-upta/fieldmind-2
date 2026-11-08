"""
Statistics of the TEP FAULT-FREE training runs (500 runs x 25 h), for
calibrating L1 thresholds in the TEP asset pack. No fault run is read here.

Windows are counted in SAMPLES (one per 3 min) and match the TEP config:
  rate      10 samples = 30 min   (RATE checks)
  signature 20 samples = 60 min   (the agent's signature slope)
  variab.   20 samples = 60 min   (sd of the sample-to-sample changes in the
                                   window: a trend-free spread, the TEP
                                   variability check; human decision 2026-11-07)
  frozen    20 samples = 60 min   (the analysers hold their value 6 or 15 min
                                   between updates, Downs & Vogel Table 4, so a
                                   shorter window would read a normal hold as a
                                   stuck instrument)
Slopes are least squares, in units per minute, one window per sample.

Writes data/reference/tep/fingerprint.json.   python -m data.tep.fingerprint
"""

from __future__ import annotations

import json

import numpy as np

from .convert import COLUMNS, REF, ROOT, SAMPLE_S, TAGS, VARIABLES

OUT = REF / "fingerprint.json"
W_RATE, W_SIG, W_FROZEN, W_VAR = 10, 20, 20, 20
# Accuracy-fixes step 2b (pre-registered, reports/accuracy_fixes.md): the chance that ANY
# state-raising check fires on a healthy tick is held at ALPHA_F (DESIGN, the conventional 99 %
# control limit; range 0.005-0.05), Sidak over m = tags x kinds (limit, rate, variability).
ALPHA_F, KINDS = 0.01, 3


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


def window_step_sd(X: np.ndarray, w: int) -> np.ndarray:
    """sd of the w-1 sample-to-sample changes in every length-w window, per run.
    X: (runs, n, tags) -> (runs, windows, tags). Same arithmetic as the TEP
    pack's variability check (fieldmind/assets/tep.py; a test asserts it)."""
    d = np.diff(X, axis=1)
    return np.stack([d[:, s:s + w - 1, :].std(axis=1) for s in range(X.shape[1] - w + 1)], axis=1)


def window_value_sd(X: np.ndarray, w: int) -> np.ndarray:
    """Population sd of the VALUES in every length-w window, per run (the TEP pack's
    WIDE check, accuracy-fixes step 5). X: (runs, n, tags) -> (runs, windows, tags)."""
    return np.stack([X[:, s:s + w, :].std(axis=1) for s in range(X.shape[1] - w + 1)], axis=1)


def window_shift(X: np.ndarray, w: int) -> np.ndarray:
    """|mean of each length-w window - mean of the run's first w samples|, for windows
    that do not overlap the first w (the TEP pack's SHIFT check, step 5)."""
    base = X[:, :w, :].mean(axis=1, keepdims=True)
    return np.stack([np.abs(X[:, s:s + w, :].mean(axis=1) - base[:, 0, :])
                     for s in range(w, X.shape[1] - w + 1)], axis=1)


def _slopes(X: np.ndarray, w: int) -> np.ndarray:
    """OLS slope per minute of every length-w window, per run. X: (runs, n, tags)."""
    t = np.arange(w, dtype=float) * SAMPLE_S / 60.0
    tc = t - t.mean()
    den = (tc ** 2).sum()
    out = []
    for s in range(0, X.shape[1] - w + 1):
        seg = X[:, s:s + w, :]
        out.append(((seg - seg.mean(axis=1, keepdims=True)) * tc[None, :, None]).sum(axis=1) / den)
    return np.abs(np.stack(out, axis=1))          # (runs, windows, tags)


def build() -> dict:
    import pyreadr
    df = next(iter(pyreadr.read_r(REF / "TEP_FaultFree_Training.RData").values()))
    runs = sorted(df["simulationRun"].unique())
    X = np.stack([df[df["simulationRun"] == r].sort_values("sample")[COLUMNS].to_numpy(float)
                  for r in runs])                  # (500, 500, 52)
    s_rate, s_sig = _slopes(X, W_RATE), _slopes(X, W_SIG)
    v = window_step_sd(X, W_VAR)
    vs, sh = window_value_sd(X, W_VAR), window_shift(X, W_VAR)
    # exactly constant over a frozen-check window, anywhere in healthy data
    frozen = np.zeros(X.shape[2], dtype=bool)
    for s in range(0, X.shape[1] - W_FROZEN + 1):
        seg = X[:, s:s + W_FROZEN, :]
        frozen |= (seg.max(axis=1) == seg.min(axis=1)).any(axis=0)
    flat = X.reshape(-1, X.shape[2])
    a = sidak(ALPHA_F, KINDS * X.shape[2])
    out = {"_source": "TEP fault-free training runs (Rieth et al. 2017), data/tep/fingerprint.py",
           "runs": len(runs), "samples_per_run": int(X.shape[1]), "sample_period_s": SAMPLE_S,
           "windows_samples": {"rate": W_RATE, "signature": W_SIG, "frozen": W_FROZEN,
                               "variability": W_VAR},
           "joint": {"alpha_family": ALPHA_F, "m": KINDS * X.shape[2], "alpha_per_check": a,
                     "n_values": int(flat.shape[0]), "n_rate_windows": int(s_rate[:, :, 0].size),
                     "n_var_windows": int(v[:, :, 0].size)},
           "tags": {}}
    for j, (col, tag, desc, unit) in enumerate(VARIABLES):
        out["tags"][tag] = {
            "column": col, "description": desc, "unit": unit,
            "mean": float(flat[:, j].mean()), "sd": float(flat[:, j].std()),
            "p0_1": float(np.percentile(flat[:, j], 0.1)), "p99_9": float(np.percentile(flat[:, j], 99.9)),
            "step_sd": float(np.diff(X[:, :, j], axis=1).std()),
            "ever_constant_60min": bool(frozen[j]),
            "step_sd_60min_p99_7": float(np.percentile(v[:, :, j], 99.7)),
            "rate_slope_abs_p99_7": float(np.percentile(s_rate[:, :, j], 99.7)),
            "value_sd_60min_p99_7": float(np.percentile(vs[:, :, j], 99.7)),
            "shift_60min_p99_7": float(np.percentile(sh[:, :, j], 99.7)),
            "sig_slope_abs": {"p85": float(np.percentile(s_sig[:, :, j], 85)),
                              "p99_7": float(np.percentile(s_sig[:, :, j], 99.7)),
                              "max": float(s_sig[:, :, j].max())},
        }
        lo, lo_x = joint_q(flat[:, j], a / 2)
        hi, hi_x = joint_q(flat[:, j], 1 - a / 2)
        rt, rt_x = joint_q(s_rate[:, :, j].ravel(), 1 - a)
        va, va_x = joint_q(v[:, :, j].ravel(), 1 - a)
        out["tags"][tag]["joint"] = {"lo": lo, "hi": hi, "rate": rt, "var": va,
                                     "at_extreme": [k for k, x in (("lo", lo_x), ("hi", hi_x),
                                                    ("rate", rt_x), ("var", va_x)) if x]}
    return out


def main() -> None:
    fp = build()
    OUT.write_text(json.dumps(fp, indent=1))
    print(f"wrote {OUT.relative_to(ROOT)}: {fp['runs']} runs x {fp['samples_per_run']} samples")
    print(f"{'tag':26s} {'unit':9s} {'mean':>10s} {'sd':>9s} {'p0.1':>10s} {'p99.9':>10s} "
          f"{'rate p99.7':>10s} {'sig p85':>9s} {'const?':>6s}")
    for tag in TAGS:
        r = fp["tags"][tag]
        print(f"{tag:26s} {r['unit']:9s} {r['mean']:10.4g} {r['sd']:9.3g} {r['p0_1']:10.4g} {r['p99_9']:10.4g} "
              f"{r['rate_slope_abs_p99_7']:10.3g} {r['sig_slope_abs']['p85']:9.3g} {str(r['ever_constant_60min']):>6s}")


if __name__ == "__main__":
    main()
