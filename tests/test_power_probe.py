"""bench.power_probe: does the fuel gauge follow a known CPU load step? Outcomes, not formulas:
synthetic gauges with a known behaviour, and the real board-side script run locally against a fake sysfs."""
from __future__ import annotations

import os
import random
import shutil
import subprocess
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from bench import power_probe as pp


def synth(idle_w, load_w, after_w=None, noise_w=0.0, busy_load=0.99, v_uv=4_000_000, update_s=0.1,
          idle_s=30, load_s=30, seed=0):
    """Samples and markers of a gauge with a known behaviour, sampled every 0.1 s."""
    rng = random.Random(seed)
    after_w = idle_w if after_w is None else after_w
    t0, t1, t2, t3 = 100.0, 100.0 + idle_s, 100.0 + idle_s + load_s, 100.0 + 2 * idle_s + load_s
    rows, held, last_upd = [], None, -1e9
    t = t0
    while t < t3:
        w = idle_w if t < t1 else load_w if t < t2 else after_w
        if t - last_upd >= update_s - 1e-9 or held is None:
            held = int((w + rng.gauss(0, noise_w)) / (v_uv * 1e-6) * 1e6)
            last_upd = t
        rows.append(f"{t:.2f},{held},{v_uv}")
        t += 0.1
    total = 10_000

    def stat(user, idle):
        return f"cpu  {user} 0 0 {idle} 0 0 0 0 0 0"
    u_load = int(total * busy_load)
    marks = [f"log_start,{t0},{stat(0, 0)}",
             f"load_start,{t1},{stat(50, 9950)}",
             f"load_end,{t2},{stat(50 + u_load, 9950 + total - u_load)}",
             f"log_end,{t3},{stat(100 + u_load, 19900 + total - u_load)}"]
    return "\n".join(rows) + "\n", "\n".join(marks) + "\n"


def test_a_gauge_that_follows_the_load_passes():
    v = pp.analyse(*synth(idle_w=1.0, load_w=4.0, noise_w=0.05))
    assert v["verdict"] == "PASS"
    assert v["step_direction"] == "up"
    assert v["step_W"] == pytest.approx(3.0, abs=0.05)


def test_the_old_sm8650_flat_reading_fails():
    # reports/bev_measurement.md: 5.45 mA idle, 5.25 mA with all 8 cores at 99%, at about 9.0 V
    v = pp.analyse(*synth(idle_w=0.00545 * 9.019, load_w=0.00525 * 9.019, v_uv=9_019_000))
    assert v["verdict"] == "FAIL"
    assert abs(v["step_W"]) < 0.01


def test_a_charging_gauge_whose_current_falls_under_load_passes_with_direction_down():
    v = pp.analyse(*synth(idle_w=5.0, load_w=2.0, noise_w=0.05))
    assert v["verdict"] == "PASS"
    assert v["step_direction"] == "down"


def test_a_load_that_did_not_run_is_invalid_even_if_the_reading_steps():
    v = pp.analyse(*synth(idle_w=1.0, load_w=4.0, busy_load=0.2))
    assert v["verdict"] == "INVALID"
    assert "load did not run" in v["reason"]


def test_a_reading_that_does_not_come_back_is_unclear():
    v = pp.analyse(*synth(idle_w=1.0, load_w=4.0, after_w=4.0))
    assert v["verdict"] == "UNCLEAR"
    assert "did not come back" in v["reason"]


def test_a_noisy_reading_is_unclear():
    v = pp.analyse(*synth(idle_w=1.0, load_w=2.0, noise_w=0.5))
    assert v["verdict"] == "UNCLEAR"
    assert "noise" in v["reason"]


def test_voltage_in_the_wrong_units_is_unclear_not_pass():
    v = pp.analyse(*synth(idle_w=1.0, load_w=4.0, v_uv=4_000))   # millivolts reported where microvolts are expected
    assert v["verdict"] == "UNCLEAR"
    assert "units" in v["reason"]


def test_a_gauge_slower_than_the_polling_is_reported():
    v = pp.analyse(*synth(idle_w=1.0, load_w=4.0, noise_w=0.05, update_s=1.0))
    assert v["verdict"] == "PASS"
    assert v["phases"]["load"]["update_interval_s"] == pytest.approx(1.0, abs=0.15)


def test_too_few_samples_is_invalid():
    s, m = synth(idle_w=1.0, load_w=4.0)
    s = "\n".join(s.splitlines()[::20]) + "\n"   # one sample in 2 s
    assert pp.analyse(s, m)["verdict"] == "INVALID"


# ---- the board run, with a fake adb ------------------------------------------------------------------------------

def _atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


class FakeBoard:
    """adb replaced by local execution of the real board script against fake sysfs, /proc/stat and /proc/uptime.
    responsive=True: current rises while the markers file says the load is on; False: a flat emulated gauge."""

    def __init__(self, tmp: Path, responsive: bool, readable: bool = True, fail_push: bool = False):
        self.tmp, self.responsive, self.readable, self.fail_push = tmp, responsive, readable, fail_push
        self.dev = tmp / "device"
        self.psy = tmp / "psy"
        self.psy.mkdir(parents=True)
        self.calls: list[tuple] = []
        self.user = self.idle = 0
        self.stop = threading.Event()
        self._tick()

    def _tick(self):
        loading = False
        mk = self.dev / "run" / "markers.csv"
        if mk.exists():
            txt = mk.read_text()
            loading = "load_start" in txt and "load_end" not in txt
        if loading:
            self.user += 10
        else:
            self.idle += 10
        cur = 600_000 if (loading and self.responsive) else 100_000 if self.responsive else 5_450
        # atomic replace: a real sysfs or /proc read never sees a half-written value
        _atomic(self.psy / "current_now", f"{cur}\n")
        _atomic(self.psy / "voltage_now", "4000000\n")
        _atomic(self.tmp / "stat", f"cpu  {self.user} 0 0 {self.idle} 0 0 0 0 0 0\ncpu0 0 0 0 0\n")
        _atomic(self.tmp / "uptime", f"{time.monotonic():.3f} 0.00\n")

    def _loop(self):
        while not self.stop.is_set():
            self._tick()
            time.sleep(0.01)

    def _map(self, s: str) -> str:
        return s.replace(pp.DEVICE_DIR, str(self.dev)).replace(pp.PSY, str(self.psy))

    def __call__(self, *args, timeout=60, serial=""):
        self.calls.append(args)
        out = SimpleNamespace(stdout="", stderr="")
        if args[0] == "shell":
            cmd = args[1]
            if cmd.startswith("cat ") and pp.PSY in cmd:
                if not self.readable:
                    out.stderr = f"cat: {cmd.split()[1]}: Permission denied"
                else:
                    out.stdout = Path(self._map(cmd.split()[1])).read_text()
            elif cmd == "nproc":
                out.stdout = "2\n"
            elif cmd.startswith("mkdir"):
                Path(self._map(cmd.split()[-1])).mkdir(parents=True, exist_ok=True)
            elif cmd.startswith("sh "):
                env = {"FM_PSY": str(self.psy), "FM_STAT": str(self.tmp / "stat"),
                       "FM_UPTIME": str(self.tmp / "uptime"), "PATH": "/usr/bin:/bin"}
                th = threading.Thread(target=self._loop, daemon=True)
                th.start()
                try:
                    p = subprocess.run(["sh"] + self._map(cmd).split()[1:], capture_output=True, text=True,
                                       env=env, timeout=timeout)
                finally:
                    self.stop.set()
                    th.join()
                out.stdout, out.stderr = p.stdout, p.stderr
        elif args[0] == "push":
            if self.fail_push:
                raise RuntimeError("adb push failed")
            dst = Path(self._map(args[2]))
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(args[1], dst)
        elif args[0] == "pull":
            src = Path(self._map(args[1]))
            if src.exists():
                shutil.copy(src, args[2])
        return out


def _run(tmp_path, fake, root=False):
    return pp.run(tmp_path / "out", root=root, idle_s=4, load_s=4, adb=fake, temperature=lambda: {},
                  settle_s=0.3)


def test_the_real_board_script_passes_on_a_gauge_that_follows_the_load(tmp_path):
    info = _run(tmp_path, FakeBoard(tmp_path, responsive=True))
    v = info["verdict"]
    assert "probe-done" in info["board_script_output"]
    assert v["verdict"] == "PASS", v
    assert v["step_W"] == pytest.approx(2.0, abs=0.05)    # (0.6 - 0.1) A x 4 V
    assert (tmp_path / "out" / "probe.json").exists()


def test_the_real_board_script_fails_on_a_flat_gauge(tmp_path):
    v = _run(tmp_path, FakeBoard(tmp_path, responsive=False))["verdict"]
    assert v["verdict"] == "FAIL", v
    assert v["cpu_busy_load"] >= pp.MIN_BUSY


def test_unreadable_nodes_stop_before_anything_is_pushed_or_run(tmp_path):
    fake = FakeBoard(tmp_path, responsive=True, readable=False)
    info = _run(tmp_path, fake)
    assert info["verdict"]["verdict"] == "DENIED"
    assert "--root" in info["verdict"]["reason"]
    assert not any(c[0] == "push" or (c[0] == "shell" and c[1].startswith("sh ")) for c in fake.calls)


def test_root_is_undone_even_when_the_run_fails(tmp_path):
    fake = FakeBoard(tmp_path, responsive=True, fail_push=True)
    with pytest.raises(RuntimeError):
        _run(tmp_path, fake, root=True)
    assert fake.calls[0] == ("root",)
    assert ("unroot",) in fake.calls
    assert (tmp_path / "out" / "probe.json").exists()
