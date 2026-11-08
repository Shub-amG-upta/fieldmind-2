"""Accuracy-fixes step 5: the TEP pack's INFO SHIFT and WIDE facts equal the fitting
code's arithmetic (data/tep/fit_signatures.window_shift / window_value_sd), tick by tick,
on a synthetic series with a step and a widening; the facts never raise the state; and
the signature triples carry the direction. Synthetic data: no TEP file needed."""
import math
from types import SimpleNamespace

import numpy as np

from data.tep.fit_signatures import window_shift, window_value_sd
from fieldmind.agent.l0_ingest import SensorWindow
from fieldmind.agent.world_model import derive_state
from fieldmind.assets.tep import level_and_variability_triples, shift_and_spread

W = 20                                    # 60 min of 3-min samples
SH, SP = 0.5, 0.8                         # thresholds for tag "a"; "b" never fires


class _Ids:
    def __init__(self):
        self.n = 0

    def next(self):
        self.n += 1
        return f"F{self.n}"


def _series():
    # 40 healthy samples around 10 (small wiggle), then a +2 step, then a widening on top
    x = [10 + 0.1 * math.sin(i) for i in range(40)]
    x += [12 + 0.1 * math.sin(i) for i in range(40, 70)]
    x += [12 + 3.0 * math.sin(1.7 * i) for i in range(70, 100)]
    return x


def _run(x, flip=False):
    layer = SimpleNamespace(cfg={"shift": {"window_min": 60.0, "thresholds": {"a": SH, "b": 1e9}},
                                 "spread": {"window_min": 60.0, "thresholds": {"a": SP, "b": 1e9}}},
                            dt_s=180.0)
    w = SensorWindow(window_min=60.0, sample_period_s=180.0, tags=["a", "b"], tick_s=180.0)
    per_tick = []
    for k, v in enumerate(x):
        w.append(k * 180.0, {"a": -v if flip else v, "b": 1.0})
        per_tick.append(shift_and_spread(layer, w, k, _Ids(), {"a", "b"}, []))
    return per_tick


def test_agent_facts_equal_the_fit_arithmetic_tick_by_tick():
    x = _series()
    X = np.asarray(x)[:, None]
    d = window_shift(X, W)[:, 0]          # window i ends at sample i + W - 1
    s = window_value_sd(X, W)[:, 0]
    facts = _run(x)
    for i in range(len(d)):
        k = i + W - 1
        got = {f.detail.split()[1] for f in facts[k]}
        want = set()
        if abs(d[i]) > SH:
            want.add("shifted")
        if s[i] > SP:
            want.add("widened:")
        assert got == want, (k, got, want)
    assert any("shifted" in f.detail for f in facts[60]) and not facts[30]


def test_direction_reaches_the_signature_and_state_stays_normal():
    up = [f for f in _run(_series())[60]]
    dn = [f for f in _run(_series(), flip=True)[60]]
    assert ("a", "SHIFT_UP", "-") in level_and_variability_triples(up)
    assert ("a", "SHIFT_DOWN", "-") in level_and_variability_triples(dn)
    wide = _run(_series())[95]
    assert ("a", "WIDE", "-") in level_and_variability_triples(wide)
    wm = SimpleNamespace(degraded_mode=None, trusted_tags=list(range(99)))
    assert all(f.severity == "INFO" for f in up + wide)
    assert derive_state(up + wide, "QUIET", wm) == "NORMAL"


def test_off_without_config_sections():
    layer = SimpleNamespace(cfg={}, dt_s=180.0)
    w = SensorWindow(window_min=60.0, sample_period_s=180.0, tags=["a"], tick_s=180.0)
    for k, v in enumerate(_series()):
        w.append(k * 180.0, {"a": v})
    assert shift_and_spread(layer, w, 99, _Ids(), {"a"}, []) == []
