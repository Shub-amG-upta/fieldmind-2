"""
Tennessee Eastman Process (Rieth et al. 2017) -> FieldMind episodes.

Data: C. A. Rieth, B. D. Amsel, R. Tran, M. B. Cook, "Additional Tennessee
Eastman Process Simulation Data for Anomaly Detection Evaluation", Harvard
Dataverse, doi:10.7910/DVN/6C3JR1 (public domain, CC0). Four .RData data
frames: faultNumber, simulationRun, sample, xmeas_1..41, xmv_1..11; one sample
per 3 min. Training runs 500 samples (fault from sample 21, i.e. after 1 h),
testing runs 960 samples (fault from sample 161, after 8 h).

Process description (variables, units, faults): Downs & Vogel 1993, Comput.
Chem. Eng. 17:245-255, Tables 4, 5 (variables) and 8 (disturbances); IDV 16-20
are "unknown" in the original. Names below are the standard ones; they are
checked against the paper in reports/b2_tep_pack.md.

SIMULATED data (Ricker's decentralised control, Rieth's runs), not plant data.

Row order (checked on the files, and asserted on every block read): the
faulty files are ordered by RUN, then FAULT, then SAMPLE (run 1: faults 1..20,
then run 2 ...); the fault-free files by run, then sample. Blocks are read with
pyreadr row ranges so the 837 MB file never has to sit in memory whole
(8.6 GB laptop).

Tags are PLAIN names (`reactor_pressure`), never `xmeas_7`: TEP is widely
published and its variable numbering would let a language model recognise the
benchmark (memorisation). The mapping is in data/kb_tep/asset_model.json.

    python -m data.tep.convert            # writes the episodes
    python -m data.tep.convert --check    # ordering and file checks only
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REF = ROOT / "data/reference/tep"
OUT_REPORT = ROOT / "data/episodes_tep"
OUT_DEV = ROOT / "data/episodes_tep_dev"
CITE = "Rieth et al. 2017, Harvard Dataverse doi:10.7910/DVN/6C3JR1"

FILES = {   # name: (Dataverse file id, samples per run, faults per run block)
    "TEP_FaultFree_Training.RData": (3031241, 500, 1),
    "TEP_FaultFree_Testing.RData": (3031240, 960, 1),
    "TEP_Faulty_Training.RData": (3031242, 500, 20),
    "TEP_Faulty_Testing.RData": (3031243, 960, 20),
}
SHA256 = {   # recorded on download (2026-11-06); sizes equal the Dataverse listing
    "TEP_FaultFree_Training.RData": "12d1055b852763fac09ef36bd7c9612a800c8bf7b6f75f344d12119206f9e940",
    "TEP_FaultFree_Testing.RData": "4f45afafa469793eeb7203fb9ed10ed0b1724c73c9c95537f15a0889ade0ebd4",
    "TEP_Faulty_Training.RData": "058df8bd90c5f575f44d2f6085bdd3bc3662e3e9cc25a50e34af42be3748952b",
    "TEP_Faulty_Testing.RData": "c2f1aabc77498efda4d5f9ad81ecc829e2fcd98752b84cf5b2a06558cabacc36",
}
SAMPLE_S = 180.0                    # 3 min, Rieth et al. / Downs & Vogel
ONSET_SAMPLE = {500: 20, 960: 160}  # fault introduced after 1 h (training) / 8 h (testing)

# Downs & Vogel 1993 Table 4 (XMEAS 1-22 continuous; 23-41 sampled analyses)
# and Table 5 (XMV 1-11; XMV 12, agitator speed, is not in the data set).
VARIABLES = [
    ("xmeas_1", "a_feed", "A feed (stream 1)", "kscmh"),
    ("xmeas_2", "d_feed", "D feed (stream 2)", "kg/h"),
    ("xmeas_3", "e_feed", "E feed (stream 3)", "kg/h"),
    ("xmeas_4", "a_c_feed", "A and C feed (stream 4)", "kscmh"),
    ("xmeas_5", "recycle_flow", "Recycle flow (stream 8)", "kscmh"),
    ("xmeas_6", "reactor_feed_rate", "Reactor feed rate (stream 6)", "kscmh"),
    ("xmeas_7", "reactor_pressure", "Reactor pressure", "kPa gauge"),
    ("xmeas_8", "reactor_level", "Reactor level", "%"),
    ("xmeas_9", "reactor_temperature", "Reactor temperature", "degC"),
    ("xmeas_10", "purge_rate", "Purge rate (stream 9)", "kscmh"),
    ("xmeas_11", "separator_temperature", "Product separator temperature", "degC"),
    ("xmeas_12", "separator_level", "Product separator level", "%"),
    ("xmeas_13", "separator_pressure", "Product separator pressure", "kPa gauge"),
    ("xmeas_14", "separator_underflow", "Product separator underflow (stream 10)", "m3/h"),
    ("xmeas_15", "stripper_level", "Stripper level", "%"),
    ("xmeas_16", "stripper_pressure", "Stripper pressure", "kPa gauge"),
    ("xmeas_17", "stripper_underflow", "Stripper underflow (stream 11)", "m3/h"),
    ("xmeas_18", "stripper_temperature", "Stripper temperature", "degC"),
    ("xmeas_19", "stripper_steam_flow", "Stripper steam flow", "kg/h"),
    ("xmeas_20", "compressor_work", "Compressor work", "kW"),
    ("xmeas_21", "reactor_cw_outlet_temp", "Reactor cooling water outlet temperature", "degC"),
    ("xmeas_22", "separator_cw_outlet_temp", "Separator cooling water outlet temperature", "degC"),
] + [(f"xmeas_{23 + i}", f"reactor_feed_{c.lower()}", f"Reactor feed analysis (stream 6), component {c}", "mol%")
     for i, c in enumerate("ABCDEF")] + \
    [(f"xmeas_{29 + i}", f"purge_gas_{c.lower()}", f"Purge gas analysis (stream 9), component {c}", "mol%")
     for i, c in enumerate("ABCDEFGH")] + \
    [(f"xmeas_{37 + i}", f"product_{c.lower()}", f"Product analysis (stream 11), component {c}", "mol%")
     for i, c in enumerate("DEFGH")] + [
    ("xmv_1", "d_feed_valve", "D feed flow (stream 2) valve", "%"),
    ("xmv_2", "e_feed_valve", "E feed flow (stream 3) valve", "%"),
    ("xmv_3", "a_feed_valve", "A feed flow (stream 1) valve", "%"),
    ("xmv_4", "a_c_feed_valve", "A and C feed flow (stream 4) valve", "%"),
    ("xmv_5", "compressor_recycle_valve", "Compressor recycle valve", "%"),
    ("xmv_6", "purge_valve", "Purge valve (stream 9)", "%"),
    ("xmv_7", "separator_liquid_valve", "Separator pot liquid flow (stream 10) valve", "%"),
    ("xmv_8", "stripper_product_valve", "Stripper liquid product flow (stream 11) valve", "%"),
    ("xmv_9", "stripper_steam_valve", "Stripper steam valve", "%"),
    ("xmv_10", "reactor_cw_valve", "Reactor cooling water flow valve", "%"),
    ("xmv_11", "condenser_cw_valve", "Condenser cooling water flow valve", "%"),
]
COLUMNS = [v[0] for v in VARIABLES]
TAGS = [v[1] for v in VARIABLES]

# Downs & Vogel 1993 Table 8 (IDV 1-15) and IDV 16-20 ("unknown" in the paper).
# Used ONLY for the case library's text and the ground truth; never in a prompt
# by number.
FAULTS = {
    1: ("A/C feed ratio step, B composition constant (stream 4)", "step"),
    2: ("B composition step, A/C ratio constant (stream 4)", "step"),
    3: ("D feed temperature step (stream 2)", "step"),
    4: ("Reactor cooling water inlet temperature step", "step"),
    5: ("Condenser cooling water inlet temperature step", "step"),
    6: ("A feed loss (stream 1)", "step"),
    7: ("C header pressure loss, reduced availability (stream 4)", "step"),
    8: ("A, B, C feed composition variation (stream 4)", "random variation"),
    9: ("D feed temperature variation (stream 2)", "random variation"),
    10: ("C feed temperature variation (stream 4)", "random variation"),
    11: ("Reactor cooling water inlet temperature variation", "random variation"),
    12: ("Condenser cooling water inlet temperature variation", "random variation"),
    13: ("Reaction kinetics slow drift", "slow drift"),
    14: ("Reactor cooling water valve sticking", "sticking"),
    15: ("Condenser cooling water valve sticking", "sticking"),
    16: ("Unknown disturbance 16", "unknown"),
    17: ("Unknown disturbance 17", "unknown"),
    18: ("Unknown disturbance 18", "unknown"),
    19: ("Unknown disturbance 19", "unknown"),
    20: ("Unknown disturbance 20", "unknown"),
}
CASE_ID = {f: f"PF-{f:02d}" for f in FAULTS}        # neutral ids (no "IDV")

# PRE-REGISTERED split (human decision 2026-11-07): test run 1 = dev, runs 2-6
# = report, for every fault; fault-free test runs 1-2 dev, 3-12 report.
DEV_RUNS, REPORT_RUNS = (1,), (2, 3, 4, 5, 6)
NORMAL_DEV_RUNS, NORMAL_REPORT_RUNS = (1, 2), tuple(range(3, 13))
TICK_PERIOD_S = 180                                  # one assessment per sample


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_block(fname: str, run: int, fault: int = 0):
    """One simulation run as a (samples, 52) float array, in COLUMNS order.
    Asserts the block's faultNumber / simulationRun / sample columns, so a wrong
    offset cannot pass silently."""
    import numpy as np
    import pyreadr
    _id, n, nf = FILES[fname]
    k = (run - 1) * nf + (max(fault, 1) - 1 if nf > 1 else 0)
    df = next(iter(pyreadr.read_r(REF / fname, row_offset=k * n, row_limit=n).values()))
    if len(df) != n:
        raise ValueError(f"{fname} run {run} fault {fault}: {len(df)} rows, expected {n}")
    if not ((df["faultNumber"] == fault).all() and (df["simulationRun"] == run).all()
            and (df["sample"].to_numpy() == np.arange(1, n + 1)).all()):
        raise ValueError(f"{fname} run {run} fault {fault}: block ids do not match (ordering)")
    return df[COLUMNS].to_numpy(dtype=float)


def read_runs(fname: str, n_runs: int) -> dict:
    """Runs 1..n_runs of a file, read in ONE pass: the files are ordered by run
    first, so these are the leading rows. Returns {(run, fault): (samples, 52)};
    fault 0 for the fault-free files. Every block's ids are asserted."""
    import numpy as np
    import pyreadr
    _id, n, nf = FILES[fname]
    df = next(iter(pyreadr.read_r(REF / fname, row_limit=n_runs * nf * n).values()))
    if len(df) != n_runs * nf * n:
        raise ValueError(f"{fname}: {len(df)} rows for {n_runs} runs, expected {n_runs * nf * n}")
    out = {}
    for k in range(n_runs * nf):
        run, fault = k // nf + 1, (k % nf + 1 if nf > 1 else 0)
        blk = df.iloc[k * n:(k + 1) * n]
        if not ((blk["faultNumber"] == fault).all() and (blk["simulationRun"] == run).all()
                and (blk["sample"].to_numpy() == np.arange(1, n + 1)).all()):
            raise ValueError(f"{fname} run {run} fault {fault}: block ids do not match (ordering)")
        out[(run, fault)] = blk[COLUMNS].to_numpy(dtype=float)
    return out


def _write_episode(out: Path, eid: str, X, gt: dict) -> None:
    d = out / eid
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    with open(d / "timeseries.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["t"] + TAGS)
        for i, row in enumerate(X):
            w.writerow([i * SAMPLE_S] + [repr(float(v)) for v in row])
    (d / "notes.jsonl").write_text("")
    (d / "ground_truth.json").write_text(json.dumps(gt, indent=2))


def _gt(eid, family, split, src, n, fault=0, run=1):
    onset = ONSET_SAMPLE[n] * SAMPLE_S
    base = {"episode_id": eid, "asset": "tep", "family": family, "tier": "-", "split": split,
            "dataset": src, "source": CITE, "duration_s": n * SAMPLE_S,
            "sample_period_s": SAMPLE_S, "tick_period_s": TICK_PERIOD_S, "simulation_run": run,
            "trip_t": None, "required_modalities": ["timeseries"],
            "_provenance": "SIMULATED (Tennessee Eastman Process, Rieth et al. 2017). Not plant data."}
    if fault == 0:
        base.update(fault_windows=[], fault_onset_t=None, root_cause_id="NONE",
                    root_cause_text="No fault. Normal operation.")
    else:
        text, ftype = FAULTS[fault]
        base.update(fault_windows=[[onset, n * SAMPLE_S]], fault_onset_t=onset,
                    root_cause_id=CASE_ID[fault], root_cause_text=text, fault_type=ftype)
    return base


def convert() -> None:
    for out in (OUT_DEV, OUT_REPORT):
        out.mkdir(parents=True, exist_ok=True)
    n = 0
    faulty = read_runs("TEP_Faulty_Testing.RData", max(DEV_RUNS + REPORT_RUNS))
    normal = read_runs("TEP_FaultFree_Testing.RData", max(NORMAL_DEV_RUNS + NORMAL_REPORT_RUNS))
    for fault in FAULTS:
        for run in DEV_RUNS + REPORT_RUNS:
            split = "dev" if run in DEV_RUNS else "report"
            eid = f"tep_F{fault:02d}_r{run}"
            X = faulty[(run, fault)]
            _write_episode(OUT_DEV if split == "dev" else OUT_REPORT, eid, X,
                           _gt(eid, f"F{fault}", split, f"TEP_Faulty_Testing run {run}", 960, fault, run))
            n += 1
    for run in NORMAL_DEV_RUNS + NORMAL_REPORT_RUNS:
        split = "dev" if run in NORMAL_DEV_RUNS else "report"
        eid = f"tep_N_r{run}"
        X = normal[(run, 0)]
        _write_episode(OUT_DEV if split == "dev" else OUT_REPORT, eid, X,
                       _gt(eid, "N", split, f"TEP_FaultFree_Testing run {run}", 960, 0, run))
        n += 1
    print(f"wrote {n} episodes: dev {len(list(OUT_DEV.iterdir()))}, report {len(list(OUT_REPORT.iterdir()))}")


def check() -> list[str]:
    probs = []
    for f in FILES:
        if not (REF / f).exists():
            probs.append(f"missing {f}")
    if probs:
        return probs
    probs += [f"{f}: sha256 differs from the recorded one" for f in FILES if sha256(REF / f) != SHA256[f]]
    if probs:
        return probs
    import numpy as np
    for f, (_i, n, nf) in FILES.items():
        X = read_block(f, 2, 3 if nf > 1 else 0)          # an interior block: ordering asserted
        if X.shape != (n, 52) or np.isnan(X).any():
            probs.append(f"{f}: block shape {X.shape} or NaN")
    # fault runs share the fault-free run's seed: identical before the onset
    a = read_block("TEP_FaultFree_Testing.RData", 3, 0)
    b = read_block("TEP_Faulty_Testing.RData", 3, 6)
    same = int(np.argmax(np.any(a != b, axis=1)))
    if not (ONSET_SAMPLE[960] - 2 <= same <= ONSET_SAMPLE[960] + 2):
        probs.append(f"fault-free vs fault 6, run 3: first differing sample {same}, expected ~{ONSET_SAMPLE[960]}")
    return probs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    probs = check()
    print("checks:", "PASS" if not probs else "FAIL")
    for p in probs:
        print("  " + p)
    if probs:
        raise SystemExit(1)
    if not a.check:
        convert()


if __name__ == "__main__":
    main()
