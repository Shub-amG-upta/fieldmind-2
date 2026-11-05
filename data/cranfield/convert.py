"""
Cranfield three-phase flow facility (2015 benchmark) -> FieldMind episodes.

Source data: MATLAB File Exchange 50938 "A Benchmark Case for Statistical
Process Monitoring - Cranfield Multiphase Flow Facility" (Yi Cao, v1.1.0,
BSD licence), archive cvatutor-1.1.0.zip, placed by hand in
data/reference/cranfield/ (sha256 checked below).

Paper (the ONLY source of tag meanings and fault windows):
  C. Ruiz-Cárcel, Y. Cao, D. Mba, L. Lao, R.T. Samuel, "Statistical process
  monitoring of a multiphase flow facility", Control Engineering Practice 42
  (2015) 74-88. docs/Cranfield_RuizCarcel2015.pdf.
  Table 1 = variables, Table 3 = fault summary, Tables 4-9 = fault start/end.

REAL rig data (not synthetic). 1 Hz. Times in the paper are seconds from the
start of each data set; here t = sample index (s), so a fault "starting at
657 s" is t >= 657 (a one-sample ambiguity, immaterial at a 30 s tick).

The data files also carry `EvoFault*` vectors. They are NOT fault labels: for
the blockage cases they are the valve angle (paper §2.3.2.1, "the valve angle
was measured using a protractor ... to record the fault evolution") and are
non-zero from the first sample. They are not used; the cross-check against the
tables is printed by `--check`.

Host-side only (scipy). Run:
    python -m data.cranfield.convert            # writes the episodes
    python -m data.cranfield.convert --check    # cross-checks only
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ZIP = ROOT / "data/reference/cranfield/cvatutor-1.1.0.zip"
ZIP_SHA256 = "3af7686da0fd963b1f7814be1bb59b5a8b990df2cce7b553de3debcf67b8ba6a"
MAT_DIR = ROOT / "data/reference/cranfield/cvatutor/CVACaseStudy"
OUT_REPORT = ROOT / "data/episodes_cranfield"
OUT_DEV = ROOT / "data/episodes_cranfield_dev"
CITE = "Ruiz-Carcel et al. 2015, Control Eng. Practice 42:74-88"

# Table 1. Column j (1-based) of every data matrix. Tag = location + magnitude,
# slugged (two locations carry several magnitudes, e.g. FT407 flow/density/temp).
VARIABLES = [
    # (tag,                     location, description,                          unit)
    ("pt312_air_supply_p",      "PT312", "Air delivery pressure",               "MPa"),
    ("pt401_riser_bottom_p",    "PT401", "Pressure in the bottom of the riser", "MPa"),
    ("pt408_riser_top_p",       "PT408", "Pressure in top of the riser",        "MPa"),
    ("pt403_top_sep_p",         "PT403", "Pressure in top separator",           "MPa"),
    ("pt501_3ph_sep_p",         "PT501", "Pressure in 3 phase separator",       "MPa"),
    ("dp_riser",                "PT408", "Diff. pressure (PT401-PT408)",        "MPa"),
    ("dp_vc404",                "PT403", "Differential pressure over VC404",    "MPa"),
    ("ft305_air_in",            "FT305", "Flow rate input air",                 "Sm3/s"),
    ("ft104_water_in",          "FT104", "Flow rate input water",               "kg/s"),
    ("ft407_riser_top_flow",    "FT407", "Flow rate top riser",                 "kg/s"),
    ("li405_top_sep_level",     "LI405", "Level top separator",                 "m"),
    ("ft406_top_sep_out_flow",  "FT406", "Flow rate top separator output",      "kg/s"),
    ("ft407_riser_top_density", "FT407", "Density top riser",                   "kg/m3"),
    ("ft406_top_sep_out_density", "FT406", "Density top separator output",      "kg/m3"),
    ("ft104_water_in_density",  "FT104", "Density water input",                 "kg/m3"),
    ("ft407_riser_top_temp",    "FT407", "Temperature top riser",               "degC"),
    ("ft406_top_sep_out_temp",  "FT406", "Temperature top separator output",    "degC"),
    ("ft104_water_in_temp",     "FT104", "Temperature water input",             "degC"),
    ("li504_3ph_sep_level",     "LI504", "Level gas-liquid 3 phase separator",  "%"),
    ("vc501_position",          "VC501", "Position of valve VC501",             "%"),
    ("vc302_position",          "VC302", "Position of valve VC302",             "%"),
    ("vc101_position",          "VC101", "Position of valve VC101",             "%"),
    ("po1_pump_current",        "PO1",   "Water pump current",                  "A"),
    ("pt417_2in_line_p",        "PT417", "Pressure in mixture zone 2in line",   "MPa"),
]
TAGS = [v[0] for v in VARIABLES]

# Table 3 (fault summary) and Tables 4-9 (fault start/end, seconds). Every
# number below is quoted from the paper. Durations are checked against the files.
FAULTS = {
    1: ("Air line blockage", "incipient"),
    2: ("Water line blockage", "incipient"),
    3: ("Top separator input blockage", "incipient"),
    4: ("Open direct bypass", "incipient"),
    5: ("Slugging conditions", "intermittent"),
    6: ("Pressurization of the 2in line", "abrupt"),
}
SETS = {
    # set: (duration_s, operating, water_kg_s, air_m3_s, [(start, end), ...], table)
    "1_1": (5811, "changing", None, None, [(1566, 5181)], 4),
    "1_2": (4467, "steady", 2.0, 0.0417, [(657, 3777)], 4),
    "1_3": (4321, "steady", 3.5, 0.0208, [(691, 3691)], 4),
    "2_1": (9192, "changing", None, None, [(2244, 6616)], 5),
    "2_2": (3496, "steady", 2.0, 0.0278, [(476, 2656)], 5),
    "2_3": (3421, "steady", 3.5, 0.0417, [(331, 2467)], 5),
    "3_1": (9090, "changing", None, None, [(1136, 8352)], 6),
    "3_2": (6272, "steady", 2.0, 0.0278, [(333, 5871)], 6),
    "3_3": (10764, "steady", 3.5, 0.0208, [(596, 9566)], 6),
    "4_1": (7208, "changing", None, None, [(953, 6294)], 7),
    "4_2": (4451, "steady", 2.0, 0.0417, [(851, 3851)], 7),
    "4_3": (3661, "steady", 3.5, 0.0208, [(241, 3241)], 7),
    "5_1": (2541, "changing", None, None, [(686, 1172), (1772, 2253)], 8),
    "5_2": (10608, "changing", None, None, [(1633, 2955), (7031, 7553), (8057, 10608)], 8),
    "6_1": (2800, "changing", None, None, [(1723, 2800)], 9),
    "6_2": (4830, "changing", None, None, [(1037, 4830)], 9),
}
TRAINING = {"T1": 10372, "T2": 9825, "T3": 13200}   # §3.1, "original length"

# DEV / REPORT split (pre-registered here, before any agent run; needs advisor
# confirmation). Faults with three sets: the FIRST steady-state set (x_2) is
# dev. Faults with two sets: x_1 is dev. Everything else is report. Normal sets
# T1-T3 are CALIBRATION ONLY (L1 thresholds); they are not scored.
DEV_SETS = {"1_2", "2_2", "3_2", "4_2", "5_1", "6_1"}

TICK_PERIOD_S = 30          # same as the boiler, so the cost study compares like with like


def _load():
    import scipy.io as sio
    mats = {"T": sio.loadmat(MAT_DIR / "Training.mat")}
    for c in range(1, 7):
        mats[c] = sio.loadmat(MAT_DIR / f"FaultyCase{c}.mat")
    return mats


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _unpack():
    if _sha256(ZIP) != ZIP_SHA256:
        raise SystemExit(f"{ZIP} sha256 differs from {ZIP_SHA256}: not the file this was built for")
    if not MAT_DIR.exists():
        with zipfile.ZipFile(ZIP) as z:
            z.extractall(ZIP.parent / "cvatutor")


def _write_episode(out: Path, eid: str, X, gt: dict) -> None:
    d = out / eid
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    with open(d / "timeseries.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["t"] + TAGS)
        for i, row in enumerate(X):
            w.writerow([float(i)] + [repr(float(v)) for v in row])
    (d / "notes.jsonl").write_text("")
    (d / "ground_truth.json").write_text(json.dumps(gt, indent=2))


def check(mats) -> list[str]:
    """Cross-checks that do not depend on the conversion. Returns problems."""
    probs = []
    for name, n in TRAINING.items():
        got = mats["T"][name].shape
        if got != (n, 24):
            probs.append(f"{name}: shape {got}, paper says {n} s x 24")
    # Column order from physics (DERIVED, independent of the set points):
    # pressure falls along the flow path, supply PT312 > riser bottom PT401 >
    # riser top PT408, and top separator PT403 > 3-phase separator PT501; and
    # column 6 is the differential transmitter across PT401-PT408 (Table 1),
    # so it tracks col2 - col3 (not exactly: a separate instrument).
    import numpy as np
    N = np.vstack([mats["T"][k] for k in TRAINING])
    for hi, lo in ((0, 1), (1, 2), (3, 4)):
        if np.mean(N[:, hi] > N[:, lo]) < 0.99:
            probs.append(f"normal data: col{hi + 1} > col{lo + 1} on only "
                         f"{np.mean(N[:, hi] > N[:, lo]):.3f} of samples (pressure order)")
    dp = np.median(np.abs(N[:, 5] - (N[:, 1] - N[:, 2]))) / np.median(N[:, 5])
    if dp > 0.10:
        probs.append(f"normal data: col6 vs col2-col3 median rel. deviation {dp:.3f} > 0.10")
    for s, (dur, _op, w, a, wins, _t) in SETS.items():
        c = int(s[0])
        X = mats[c][f"Set{s}"]
        if X.shape != (dur, 24):
            probs.append(f"Set{s}: shape {X.shape}, paper says {dur} s x 24")
        if w is not None:   # steady sets: measured flows before the fault vs the paper's set points
            st = wins[0][0]
            mw, ma = X[:st, 8].mean(), X[:st, 7].mean()
            if abs(mw - w) / w > 0.01 or abs(ma - a) / a > 0.01:
                probs.append(f"Set{s}: pre-fault water {mw:.3f} / air {ma:.4f} vs paper {w} / {a}")
    return probs


def evofault_vs_tables(mats) -> list[str]:
    """Where EvoFault is a 0/x flag (cases 4-6) its non-zero segments should
    match the tables; for cases 1-3 it is a valve angle and does not."""
    import numpy as np
    out = []
    for s, (_d, _o, _w, _a, wins, _t) in SETS.items():
        e = mats[int(s[0])][f"EvoFault{s}"].ravel().astype(float)
        dd = np.diff(np.r_[0, (e > 0).astype(int), 0])
        segs = list(zip(np.where(dd == 1)[0].tolist(), np.where(dd == -1)[0].tolist()))
        out.append(f"  Set{s}: tables {wins}  EvoFault>0 segments {segs[:4]}")
    return out


def convert() -> None:
    _unpack()
    mats = _load()
    probs = check(mats)
    if probs:
        raise SystemExit("cross-check failed:\n  " + "\n  ".join(probs))
    for out in (OUT_REPORT, OUT_DEV):
        out.mkdir(parents=True, exist_ok=True)
    src = f"MATLAB File Exchange 50938 cvatutor-1.1.0.zip (sha256 {ZIP_SHA256[:12]}...)"
    n = 0
    for s, (dur, op, w, a, wins, table) in SETS.items():
        c = int(s[0])
        fname, ftype = FAULTS[c]
        eid = f"cf_F{c}_{s.replace('_', '.')}_{fname.lower().replace(' ', '_')}"
        gt = {
            "episode_id": eid, "asset": "cranfield", "family": f"F{c}", "tier": "-",
            "split": "dev" if s in DEV_SETS else "report",
            "dataset": f"FaultyCase{c}.mat / Set{s}",
            "source": f"{CITE}, Table {table}; data {src}",
            "duration_s": dur, "sample_period_s": 1.0, "tick_period_s": TICK_PERIOD_S,
            "operating_conditions": op, "water_kg_s": w, "air_m3_s": a,
            "fault_windows": [list(x) for x in wins],
            "fault_onset_t": float(wins[0][0]), "trip_t": None,
            "root_cause_id": f"CF-{c}", "root_cause_text": fname, "fault_type": ftype,
            "required_modalities": ["timeseries"],
            "_provenance": "REAL rig data (Cranfield three-phase flow facility). Not synthetic.",
        }
        out = OUT_DEV if s in DEV_SETS else OUT_REPORT
        _write_episode(out, eid, mats[c][f"Set{s}"], gt)
        n += 1
    print(f"wrote {n} fault episodes ({len(DEV_SETS)} dev, {n - len(DEV_SETS)} report)")
    print(f"  dev:    {OUT_DEV.relative_to(ROOT)}")
    print(f"  report: {OUT_REPORT.relative_to(ROOT)}")
    print("normal sets T1-T3 are read by data/cranfield/fingerprint.py for calibration only")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        _unpack()
        mats = _load()
        probs = check(mats)
        print("cross-checks:", "PASS" if not probs else "FAIL")
        for p in probs:
            print("  " + p)
        print("EvoFault vs the paper's tables (not used as labels):")
        print("\n".join(evofault_vs_tables(mats)))
        return
    convert()


if __name__ == "__main__":
    main()
