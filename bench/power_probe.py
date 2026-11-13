"""
Does the board's fuel gauge measure the board's power? One command, one verdict.

The TA's method (Phase Matters, MobiSys Workshop '26, section 2.3: "energy: fuel-gauge I x V at 100 ms granularity"):
read /sys/class/power_supply/battery/current_now and voltage_now every 100 ms. This probe runs that logger on the
board through a known load step and says whether the reading follows it:

    30 s idle  ->  30 s with every CPU core spinning  ->  30 s idle

  env -u PYTHONPATH .venv/bin/python -m bench.power_probe            (non-root; reports DENIED if sysfs is closed)
  env -u PYTHONPATH .venv/bin/python -m bench.power_probe --root     (adb root for this probe only; adb unroot after)
  env -u PYTHONPATH .venv/bin/python -m bench.power_probe analyse <run dir>   (re-read a saved run)

Verdicts (rules fixed in this file before any SM8750 run):
  PASS     the reading steps by >= FLOOR_W under load, >= K_NOISE x the idle noise, and comes back after
  FAIL     the load ran, and the step is below FLOOR_W: the gauge does not see the board's draw
  UNCLEAR  a large step, but noisy, or it did not come back, or the units look wrong
  INVALID  the load did not run (CPU busy < MIN_BUSY) or too few samples: nothing can be concluded
  DENIED   current_now / voltage_now cannot be read (rerun with --root)

Nothing here is an energy result. A PASS says only that the gauge follows a CPU load step on this board; energy runs
still need their own rules (idle subtraction, update rate, what the gauge's supply path covers).

Board clock: /proc/uptime (seconds since boot). The board's wall clock is wrong (CLAUDE.md); laptop time is logged
around the run. The board-side script is pushed as a file, never passed through two shell layers.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

from bench import board

PSY = "/sys/class/power_supply/battery"
DEVICE_DIR = "/data/local/tmp/fm_power"

# Sysfs units, CITED: Linux Documentation/ABI/testing/sysfs-class-power, current_now "represented in microamps",
# voltage_now "represented in microvolts". So P [W] = current_now * voltage_now * 1e-12.
UA_UV_TO_W = 1e-12

IDLE_S = 30   # DESIGN, range 15-60: length of each idle phase. Affects samples per phase only.
LOAD_S = 30   # DESIGN, range 15-60: length of the load phase. As the TA's warm runs, it is short enough to stay cool.
SETTLE_S = 2.0  # DESIGN, range 1-5: samples this soon after a phase change are dropped (gauges average over a window).
MIN_SAMPLES = 20  # DESIGN, range 10-50: below this per phase the logger mostly failed (100 ms x 28 s gives ~280).
MIN_BUSY = 0.90  # DESIGN, range 0.80-0.95: CPU busy share during the load phase, from /proc/stat. Below it, INVALID.
# DESIGN, range 0.2-1.0 W: the smallest step that counts as "sees the board's draw". Basis, stated honestly: an
# expectation (not a citation) that every core of a phone SoC spinning draws well over 1 W more than idle; and the one
# measured flat case, the old SM8650 (reports/bev_measurement.md: 5.45 -> 5.25 mA at about 9.0 V), is a step of
# about 2 mW, far below any value in the range. The raw step is always printed, so another floor can be applied.
FLOOR_W = 0.5
K_NOISE = 5.0  # DESIGN, range 3-10: the step must exceed this many robust SDs of the idle reading.
RETURN_SHARE = 0.5  # DESIGN, range 0.3-0.7: idle after must be within this share of the step of idle before.
VOLT_RANGE = (2.5, 15.0)  # DESIGN: a battery-path voltage outside this range means the units are not uA/uV.

BOARD_SCRIPT = r"""# FieldMind power probe, board side. Written by bench/power_probe.py and pushed as a file.
# Args: OUT_DIR IDLE_S LOAD_S N_LOAD. Clock: /proc/uptime (the board's wall clock is wrong).
# No `kill`: on the board's /system/bin/sh a redirected `( ... ) &` is two nested processes and $! names the outer one,
# so kill missed its target (and on the first SM8650 run took the whole script down). Loops stop on a stop file.
B=${FM_PSY:-/sys/class/power_supply/battery}
STAT=${FM_STAT:-/proc/stat}
UP=${FM_UPTIME:-/proc/uptime}
O=$1; IDLE=$2; LOAD=$3; N=$4
now() { read u _ < "$UP"; echo "$u"; }
mark() { echo "$1,$(now),$(head -n 1 "$STAT")" >> "$O/markers.csv"; }
mkdir -p "$O"; rm -f "$O/stop_log" "$O/stop_load"
: > "$O/samples.csv"; : > "$O/markers.csv"; : > "$O/errors.txt"
( while [ ! -e "$O/stop_log" ]; do
    read i < "$B/current_now"; read v < "$B/voltage_now"
    echo "$(now),$i,$v"
    sleep 0.1
  done ) >> "$O/samples.csv" 2>> "$O/errors.txt" &
mark log_start
sleep "$IDLE"
mark load_start
k=0
while [ "$k" -lt "$N" ]; do
  ( while [ ! -e "$O/stop_load" ]; do :; done ) > /dev/null 2>&1 &
  k=$((k+1))
done
sleep "$LOAD"
mark load_end
: > "$O/stop_load"
sleep "$IDLE"
mark log_end
: > "$O/stop_log"
wait
echo probe-done
"""


# ---- analysis (pure; tested on synthetic and locally generated runs) ---------------------------------------------

def parse_samples(text: str) -> tuple[list[tuple[float, int, int]], int]:
    """(t, current_now, voltage_now) rows, and the count of malformed lines."""
    rows, bad = [], 0
    for ln in text.splitlines():
        parts = ln.strip().split(",")
        try:
            rows.append((float(parts[0]), int(parts[1]), int(parts[2])))
        except (ValueError, IndexError):
            bad += 1
    return rows, bad


def parse_markers(text: str) -> dict[str, tuple[float, list[int]]]:
    """name -> (t, the /proc/stat 'cpu' counters: user nice system idle iowait irq softirq steal)."""
    out = {}
    for ln in text.splitlines():
        parts = ln.strip().split(",", 2)
        if len(parts) < 3:
            continue
        fields = parts[2].split()
        counters = [int(x) for x in fields[1:9]] if fields and fields[0] == "cpu" else []
        out[parts[0]] = (float(parts[1]), counters)
    return out


def busy_share(a: list[int], b: list[int]) -> float | None:
    """CPU busy share between two /proc/stat 'cpu' lines: 1 - (d idle + d iowait) / d total."""
    if len(a) < 8 or len(b) < 8:
        return None
    d = [y - x for x, y in zip(a, b)]
    total = sum(d)
    return None if total <= 0 else 1.0 - (d[3] + d[4]) / total


def _robust(xs: list[float]) -> tuple[float, float]:
    """Median and 1.4826 x MAD (a robust SD)."""
    m = statistics.median(xs)
    return m, 1.4826 * statistics.median(abs(x - m) for x in xs)


def _update_interval(rows: list[tuple[float, int, int]]) -> float | None:
    """Median time between changes of current_now (a gauge can update slower than it is polled)."""
    t_change = [rows[k][0] for k in range(1, len(rows)) if rows[k][1] != rows[k - 1][1]]
    if len(t_change) < 2:
        return None
    return statistics.median(b - a for a, b in zip(t_change, t_change[1:]))


def analyse(samples_text: str, markers_text: str, settle_s: float = SETTLE_S) -> dict:
    rows, bad = parse_samples(samples_text)
    marks = parse_markers(markers_text)
    need = ("log_start", "load_start", "load_end", "log_end")
    out: dict = {"samples": len(rows), "malformed_lines": bad, "rules": {
        "FLOOR_W": FLOOR_W, "K_NOISE": K_NOISE, "MIN_BUSY": MIN_BUSY, "MIN_SAMPLES": MIN_SAMPLES,
        "RETURN_SHARE": RETURN_SHARE, "SETTLE_S": settle_s}}
    missing = [m for m in need if m not in marks]
    if missing:
        out.update(verdict="INVALID", reason=f"markers missing: {missing}")
        return out
    t = {m: marks[m][0] for m in need}
    windows = {"idle_before": (t["log_start"] + settle_s, t["load_start"]),
               "load": (t["load_start"] + settle_s, t["load_end"]),
               "idle_after": (t["load_end"] + settle_s, t["log_end"])}
    phase = {}
    for name, (a, b) in windows.items():
        sel = [r for r in rows if a <= r[0] < b]
        watts = [i * v * UA_UV_TO_W for _, i, v in sel]
        ph = {"n": len(sel)}
        if sel:
            ph["median_W"], ph["robust_sd_W"] = _robust(watts)
            ph["median_current_raw"] = statistics.median(i for _, i, _ in sel)
            ph["median_voltage_V"] = statistics.median(v for _, _, v in sel) * 1e-6
            ph["update_interval_s"] = _update_interval(sel)
        phase[name] = ph
    out["phases"] = phase
    out["cpu_busy_load"] = busy_share(marks["load_start"][1], marks["load_end"][1])
    out["cpu_busy_idle_before"] = busy_share(marks["log_start"][1], marks["load_start"][1])

    if any(phase[p]["n"] < MIN_SAMPLES for p in phase):
        out.update(verdict="INVALID", reason=f"fewer than {MIN_SAMPLES} samples in a phase")
        return out
    if out["cpu_busy_load"] is None or out["cpu_busy_load"] < MIN_BUSY:
        out.update(verdict="INVALID", reason=f"the load did not run: CPU busy {out['cpu_busy_load']} < {MIN_BUSY}")
        return out

    before, load, after = phase["idle_before"], phase["load"], phase["idle_after"]
    step = load["median_W"] - (before["median_W"] + after["median_W"]) / 2
    noise = max(before["robust_sd_W"], after["robust_sd_W"])
    drift = abs(after["median_W"] - before["median_W"])
    out.update(step_W=step, step_direction="up" if step > 0 else "down" if step < 0 else "none",
               idle_noise_W=noise, idle_drift_W=drift)
    volts = [phase[p]["median_voltage_V"] for p in phase]
    if not all(VOLT_RANGE[0] <= v <= VOLT_RANGE[1] for v in volts):
        out.update(verdict="UNCLEAR", reason=f"voltage {volts} V outside {VOLT_RANGE}: units may not be uA/uV")
    elif abs(step) < FLOOR_W:
        out.update(verdict="FAIL", reason=f"|step| {abs(step):.4f} W < {FLOOR_W} W with the load running: "
                                          "the gauge does not see the board's draw")
    elif abs(step) < K_NOISE * noise:
        out.update(verdict="UNCLEAR", reason=f"|step| {abs(step):.3f} W < {K_NOISE} x idle noise {noise:.3f} W")
    elif drift > RETURN_SHARE * abs(step):
        out.update(verdict="UNCLEAR", reason=f"idle after differs from idle before by {drift:.3f} W "
                                             f"(> {RETURN_SHARE} x step): the reading did not come back")
    else:
        out.update(verdict="PASS", reason=f"the reading steps {step:+.3f} W under load and comes back")
    return out


# ---- the board run ---------------------------------------------------------------------------------------------

def _out(p) -> str:
    return (p.stdout or "") + (p.stderr or "")


def precheck(adb=board._adb) -> dict:
    """What the board exposes. 'readable' is True only if both nodes return integers."""
    cmds = {"id": "id", "soc": "getprop ro.soc.model; getprop ro.product.board; getprop ro.build.type",
            "power_supply": "ls /sys/class/power_supply/",
            "current_now": f"cat {PSY}/current_now", "voltage_now": f"cat {PSY}/voltage_now",
            "dumpsys_battery": "dumpsys battery",
            "power_stats_service": "service list | grep -i power"}
    got = {k: _out(adb("shell", c)).strip() for k, c in cmds.items()}

    def is_int(s: str) -> bool:
        try:
            int(s.split()[0])
            return True
        except (ValueError, IndexError):
            return False
    got["readable"] = is_int(got["current_now"]) and is_int(got["voltage_now"])
    return got


def run(out_dir: Path, root: bool = False, idle_s: int = IDLE_S, load_s: int = LOAD_S,
        adb=board._adb, temperature=board.chip_temperature, settle_s: float = SETTLE_S) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    info: dict = {"laptop_start": board.laptop_time(), "root": root, "idle_s": idle_s, "load_s": load_s}
    try:
        if root:
            info["adb_root"] = _out(adb("root")).strip()
            adb("wait-for-device", timeout=60)
        pre = precheck(adb)
        info["precheck"] = pre
        if not pre["readable"]:
            info["verdict"] = {"verdict": "DENIED", "reason": "current_now / voltage_now not readable: "
                               f"{pre['current_now'][:120]!r}" + ("" if root else "; rerun with --root")}
            return info
        n = _out(adb("shell", "nproc")).strip()
        n_load = int(n) if n.isdigit() else 8
        info["n_load"] = n_load
        local_script = out_dir / "probe.sh"
        local_script.write_text(BOARD_SCRIPT)
        adb("shell", f"mkdir -p {DEVICE_DIR}")
        adb("push", str(local_script), f"{DEVICE_DIR}/probe.sh")
        info["temp_before"] = temperature()
        info["laptop_load_phase_start_approx"] = board.laptop_time()
        p = adb("shell", f"sh {DEVICE_DIR}/probe.sh {DEVICE_DIR}/run {idle_s} {load_s} {n_load}",
                timeout=2 * idle_s + load_s + 120)
        info["board_script_output"] = _out(p).strip()[-500:]
        info["temp_after"] = temperature()
        for f in ("samples.csv", "markers.csv", "errors.txt"):
            adb("pull", f"{DEVICE_DIR}/run/{f}", str(out_dir / f))
        samples = (out_dir / "samples.csv").read_text() if (out_dir / "samples.csv").exists() else ""
        markers = (out_dir / "markers.csv").read_text() if (out_dir / "markers.csv").exists() else ""
        info["verdict"] = analyse(samples, markers, settle_s)
        return info
    finally:
        if root:
            info["adb_unroot"] = _out(adb("unroot")).strip()
            adb("wait-for-device", timeout=60)
        info["laptop_end"] = board.laptop_time()
        (out_dir / "probe.json").write_text(json.dumps(info, indent=1))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    an = sub.add_parser("analyse", help="re-read a saved run directory")
    an.add_argument("dir")
    ap.add_argument("--root", action="store_true", help="adb root for this probe only; adb unroot afterwards")
    ap.add_argument("--idle", type=int, default=IDLE_S)
    ap.add_argument("--load", type=int, default=LOAD_S)
    ap.add_argument("--out", default="results/power_probe")
    a = ap.parse_args(argv)
    if a.cmd == "analyse":
        d = Path(a.dir)
        v = analyse((d / "samples.csv").read_text(), (d / "markers.csv").read_text())
        print(json.dumps(v, indent=1))
        return 0
    out_dir = Path(a.out) / time.strftime("%Y%m%d_%H%M%S")
    info = run(out_dir, root=a.root, idle_s=a.idle, load_s=a.load)
    print(json.dumps({k: info.get(k) for k in ("laptop_start", "root", "n_load", "temp_before", "temp_after")},
                     indent=1))
    print(json.dumps(info["verdict"], indent=1))
    print(f"saved: {out_dir}")
    return 0


if __name__ == "__main__":
    board.drop_pythonpath()
    sys.exit(main())
