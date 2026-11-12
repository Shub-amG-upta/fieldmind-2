#!/usr/bin/env python3
"""
=============================================================================
 ENERGY FROM AN EXTERNAL POWER METER  (paper B item 4; PLAN_PAPER_B.md)
=============================================================================

The board has no power sensor (reports/bev_measurement.md: no rails, battery
readings denied, DC supply outside the gauge), so energy comes from a logging
meter on the board's DC input. This tool reads the meter's CSV and the runner's
laptop-time windows and reports energy; it never estimates. Without a meter log
there is no number (CLAUDE.md: energy stays null).

    .venv/bin/python bench/energy.py idle   <meter.csv> --from <unix> --to <unix> [columns]
    .venv/bin/python bench/energy.py runs   <meter.csv> <results/benchmarks/<test>> --idle-w <W> [columns]
           [--nomodel <results/benchmarks_mock/<test>>]

Columns (the meter's CSV header names): --time-col (unix seconds, or ISO with
--time-iso), and either --power-col (W) or --volt-col (V) and --amp-col (A).
Rows must be in laptop time: the meter's logger runs on the laptop, or its
clock offset is measured and given with --offset-s (added to the meter time).

Per run (the agent process window child_t0_unix .. child_t1_unix that
bench/benchmark.py records): energy (trapezoid over the meter's samples),
mean power, energy above idle (mean power minus --idle-w, times the window),
and per tick. With --nomodel (the same episodes on the mock backend): energy
above idle per published top-cause change (bench/echo_test.changed), the
quantity "joules per changed decision".

Every result names the meter file and its sha256, the idle figure and the
window. A run whose window the meter does not cover (or covers with a gap over
MAX_GAP_S) gets no number.
=============================================================================
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# DESIGN: the longest gap between meter samples inside a window that still gives a number. Range 1-10 s.
# Affects which runs are refused, never the value.
MAX_GAP_S = 5.0


def read_meter(path: str, time_col: str, power_col: str | None = None, volt_col: str | None = None,
               amp_col: str | None = None, time_iso: bool = False, offset_s: float = 0.0) -> list[tuple[float, float]]:
    """[(laptop unix seconds, watts)] sorted by time."""
    if not power_col and not (volt_col and amp_col):
        raise SystemExit("give --power-col, or --volt-col and --amp-col")
    out = []
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                t = (datetime.fromisoformat(row[time_col]).timestamp() if time_iso else float(row[time_col]))
                w = float(row[power_col]) if power_col else float(row[volt_col]) * float(row[amp_col])
            except (KeyError, ValueError):
                continue                       # a header repeat or a blank line: skipped, never guessed
            out.append((t + offset_s, w))
    out.sort()
    return out


def window(samples: list[tuple[float, float]], t0: float, t1: float) -> dict | None:
    """Energy over [t0, t1] by the trapezoid rule, the window's ends interpolated; None when the
    meter does not cover the window or has a gap over MAX_GAP_S inside it."""
    if t1 <= t0 or not samples or samples[0][0] > t0 or samples[-1][0] < t1:
        return None
    pts = [(t, w) for t, w in samples if t0 < t < t1]

    def at(t):
        for (ta, wa), (tb, wb) in zip(samples, samples[1:]):
            if ta <= t <= tb:
                return wa if tb == ta else wa + (wb - wa) * (t - ta) / (tb - ta)
        return None
    pts = [(t0, at(t0))] + pts + [(t1, at(t1))]
    gaps = [b[0] - a[0] for a, b in zip(pts, pts[1:])]
    if max(gaps) > MAX_GAP_S:
        return None
    j = sum((b[0] - a[0]) * (a[1] + b[1]) / 2 for a, b in zip(pts, pts[1:]))
    return {"joules": round(j, 3), "seconds": round(t1 - t0, 3), "mean_w": round(j / (t1 - t0), 4),
            "samples": len(pts) - 2, "max_gap_s": round(max(gaps), 3)}


def _sha(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def runs(samples, test_dir: Path, idle_w: float, nomodel_dir: Path | None = None) -> list[dict]:
    """One row per finished run of a benchmark test (test.json's runs, with their windows)."""
    meta = json.loads((test_dir / "test.json").read_text())
    out = []
    for e in meta.get("runs") or []:
        t0, t1 = e.get("child_t0_unix"), e.get("child_t1_unix")
        row = {"episode": e.get("episode"), "run": e.get("run"), "stem": e.get("stem")}
        if t0 is None or t1 is None:
            row["energy"] = None
            row["why"] = "no process window recorded (a run from before bench/benchmark.py recorded it)"
            out.append(row)
            continue
        w = window(samples, t0, t1)
        row["energy"] = w
        if w is None:
            row["why"] = "meter does not cover the window, or a gap over MAX_GAP_S"
            out.append(row)
            continue
        above = (w["mean_w"] - idle_w) * w["seconds"]
        row["joules_above_idle"] = round(above, 3)
        rf = test_dir / f"{e['stem']}.run.json.gz"
        if rf.exists():
            run = json.loads(gzip.decompress(rf.read_bytes()))
            n = len(run.get("assessments") or [])
            row["ticks"] = n
            row["joules_above_idle_per_tick"] = round(above / n, 4) if n else None
        if nomodel_dir is not None:
            from bench.echo_test import changed
            import tempfile, shutil
            g = nomodel_dir / f"{e['stem']}.run.json.gz"
            if rf.exists() and g.exists():
                with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
                    shutil.copy(rf, a); shutil.copy(g, Path(b) / rf.name)
                    c = changed(a, b, allow_reporting=True)
                row["published_changes"] = c["ticks_differ"]
                row["joules_above_idle_per_change"] = (round(above / c["ticks_differ"], 2)
                                                       if c["ticks_differ"] else None)
        out.append(row)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="what", required=True)
    for name in ("idle", "runs"):
        s = sub.add_parser(name)
        s.add_argument("meter")
        if name == "runs":
            s.add_argument("test_dir")
            s.add_argument("--idle-w", type=float, required=True, help="the board's idle power (from `idle`)")
            s.add_argument("--nomodel", default=None, help="the same test on the mock backend")
        else:
            s.add_argument("--from", dest="t0", type=float, required=True)
            s.add_argument("--to", dest="t1", type=float, required=True)
        s.add_argument("--time-col", required=True)
        s.add_argument("--power-col")
        s.add_argument("--volt-col")
        s.add_argument("--amp-col")
        s.add_argument("--time-iso", action="store_true")
        s.add_argument("--offset-s", type=float, default=0.0)
    a = ap.parse_args(argv)
    samples = read_meter(a.meter, a.time_col, a.power_col, a.volt_col, a.amp_col, a.time_iso, a.offset_s)
    src = {"meter_file": a.meter, "meter_sha256": _sha(a.meter), "samples": len(samples), "offset_s": a.offset_s}
    if a.what == "idle":
        print(json.dumps({**src, "idle": window(samples, a.t0, a.t1)}, indent=1))
    else:
        rows = runs(samples, Path(a.test_dir), a.idle_w, Path(a.nomodel) if a.nomodel else None)
        print(json.dumps({**src, "idle_w": a.idle_w, "runs": rows}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
