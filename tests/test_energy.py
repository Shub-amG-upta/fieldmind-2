"""bench.energy: outcomes on a hand-built meter log and run folder (no meter exists yet)."""

from __future__ import annotations

import gzip
import json

import pytest

from bench import energy as E


def meter(tmp_path, rows, header="t,V,A"):
    p = tmp_path / "meter.csv"
    p.write_text(header + "\n" + "\n".join(",".join(str(x) for x in r) for r in rows) + "\n")
    return str(p)


def test_a_constant_load_integrates_to_power_times_time(tmp_path):
    # 12 V x 0.5 A = 6 W, sampled every second from t=100 to t=200
    s = E.read_meter(meter(tmp_path, [(100 + k, 12, 0.5) for k in range(101)]), "t", volt_col="V", amp_col="A")
    w = E.window(s, 110.5, 150.5)
    assert w["joules"] == pytest.approx(240.0) and w["mean_w"] == pytest.approx(6.0) and w["seconds"] == 40.0


def test_a_step_in_power_is_split_at_the_window_edge(tmp_path):
    rows = [(t, 10 if t < 50 else 20) for t in range(0, 101)]
    s = E.read_meter(meter(tmp_path, rows, header="t,W"), "t", power_col="W")
    w = E.window(s, 40, 60)
    # 9 s at 10 W, the 49->50 ramp (15 W), 10 s at 20 W
    assert w["joules"] == pytest.approx(9 * 10 + 15 + 10 * 20)


def test_a_window_the_meter_does_not_cover_or_with_a_gap_gets_no_number(tmp_path):
    s = E.read_meter(meter(tmp_path, [(t, 1) for t in list(range(0, 30)) + list(range(40, 60))], header="t,W"),
                     "t", power_col="W")
    assert E.window(s, 10, 20) is not None
    assert E.window(s, 20, 45) is None            # 30 -> 40 is a 10 s gap
    assert E.window(s, 50, 70) is None            # the meter stops at 59
    assert E.window(s, 50, 61) is None            # 2 s past the last sample: inside MAX_GAP_S, still uncovered


def test_runs_use_the_recorded_process_window_and_subtract_idle(tmp_path):
    d = tmp_path / "test"
    d.mkdir()
    (d / "test.json").write_text(json.dumps({"runs": [
        {"episode": "dev_X", "run": 1, "stem": "dev_X_multi", "child_t0_unix": 1000.0, "child_t1_unix": 1100.0},
        {"episode": "dev_Y", "run": 1, "stem": "dev_Y_multi"}]}))              # an old run: no window
    (d / "dev_X_multi.run.json.gz").write_bytes(gzip.compress(json.dumps(
        {"episode_id": "dev_X", "assessments": [{"tick": k} for k in range(50)]}).encode()))
    s = E.read_meter(meter(tmp_path, [(990 + k, 9.0) for k in range(130)], header="t,W"), "t", power_col="W")
    rows = E.runs(s, d, idle_w=4.0)
    x, y = rows
    assert x["energy"]["joules"] == pytest.approx(900.0)
    assert x["joules_above_idle"] == pytest.approx(500.0) and x["joules_above_idle_per_tick"] == pytest.approx(10.0)
    assert y["energy"] is None and "no process window" in y["why"]


def test_rows_that_are_not_numbers_are_skipped_not_guessed(tmp_path):
    s = E.read_meter(meter(tmp_path, [(1, 5), ("t", "W"), (2, ""), (3, 5)], header="t,W"), "t", power_col="W")
    assert s == [(1.0, 5.0), (3.0, 5.0)]
