"""Breadth B2, Step 1: the 10-min signature window, the 30 s fact-window tick
and the evaluator's 30 s tick are parameters (an asset with 3-min samples, TEP,
needs other values). Defaults keep the boiler and Cranfield byte-identical
(identity runs in reports/b2_tep_pack.md); these tests check the parameters
are actually honoured."""
from bench.evaluator import t5_false_positives, t2_root_cause
from fieldmind.agent.l0_ingest import SensorWindow
from fieldmind.agent.orchestrator import slopes_10min


def _ramp_then_flat(dt):
    """Value rises 1 unit/min for 50 min, then is flat for 10 min."""
    w = SensorWindow(window_min=120.0, sample_period_s=dt, tags=["x"])
    t = 0.0
    while t <= 3600.0:
        w.append(t, {"x": min(t, 3000.0) / 60.0})
        t += dt
    return w


def test_signature_window_length_is_honoured():
    w = _ramp_then_flat(60.0)
    assert abs(slopes_10min(w)["x"]) < 1e-9                  # last 10 min: flat
    assert slopes_10min(w, 60.0)["x"] > 0.5                   # last 60 min: mostly rising


def test_fact_window_uses_the_tick_length():
    w30 = SensorWindow(window_min=60.0, sample_period_s=180.0, tags=["x"])
    w180 = SensorWindow(window_min=60.0, sample_period_s=180.0, tags=["x"], tick_s=180.0)
    for i in range(20):
        w30.append(i * 180.0, {"x": 0.0}); w180.append(i * 180.0, {"x": 0.0})
    assert w30.window_ticks(100) == (0, 100)                 # 20 samples x 180 s / 30 s = 120 ticks
    assert w180.window_ticks(100) == (80, 100)               # = 20 ticks of 180 s


def _run(tick_s, states, onset=None):
    gt = {"family": "N" if onset is None else "F", "tick_period_s": tick_s,
          "root_cause_id": "NONE" if onset is None else "X", "fault_onset_t": onset}
    return {"ground_truth": gt,
            "assessments": [{"tick": k, "state": s, "hypotheses": [{"case_ref": "X"}]}
                            for k, s in enumerate(states)]}


def test_false_positives_per_hour_use_the_episode_tick():
    states = ["ALARM"] + ["NORMAL"] * 19                     # 1 alarm in 20 ticks
    assert t5_false_positives(_run(30.0, states), 30.0)["fp_per_hour"] == 6.0     # 20 x 30 s = 10 min
    assert t5_false_positives(_run(180.0, states), 180.0)["fp_per_hour"] == 1.0   # 20 x 180 s = 1 h


def test_root_cause_onset_filter_uses_the_episode_tick(monkeypatch):
    import bench.evaluator as ev
    monkeypatch.setattr(ev, "_groups", lambda asset="boiler": ({"X": "X"}, {}, set()))
    # onset at 900 s: with 180 s ticks, ticks 5.. are scored (5 x 180 = 900) -> 15 of 20
    assert t2_root_cause(_run(180.0, ["ALARM"] * 20, onset=900.0))["n_scored"] == 15
    # with 30 s ticks the same onset leaves only tick 30+ -> none of 20 scored
    assert t2_root_cause(_run(30.0, ["ALARM"] * 20, onset=900.0))["n_scored"] == 0
