"""Breadth B2: the TEP pack, its converter and the fitted library. Each test
fails if the rule it names is broken. Data-dependent tests skip when the TEP
files are absent (not in git: data/reference/tep/, ~1.4 GB)."""
import json
from pathlib import Path

import pytest
import yaml

from data.tep import convert as cv
from fieldmind.agent.l0_ingest import SensorWindow
from fieldmind.agent.l1_checks import CheckLayer
from fieldmind.assets import load_asset
from fieldmind.assets.tep import REACTION, SEPARATION, TAGS, level_and_variability_triples
from fieldmind.kb.stores import CaseLibrary
from fieldmind.schemas import Fact

ROOT = Path(__file__).resolve().parent.parent
HAVE_DATA = (cv.REF / "TEP_Faulty_Training.RData").exists()
LIB = json.loads((ROOT / "data/kb_tep/case_library.json").read_text())["cases"]
CFG = yaml.safe_load((ROOT / "configs/tep.yaml").read_text())


def test_pack_tags_match_converter_and_name_nothing_benchmark_specific():
    assert list(TAGS) == cv.TAGS and load_asset({"asset": "tep"}).tags == TAGS
    assert not any(t.startswith(("xmeas", "xmv", "idv")) for t in TAGS)
    assert REACTION | SEPARATION == set(TAGS) and not REACTION & SEPARATION


def test_prompts_and_cases_never_name_the_benchmark():
    texts = [p.read_text().lower() for p in (ROOT / "fieldmind/multi/prompts/tep").glob("*.txt")]
    texts += [p.read_text().lower() for p in (ROOT / "fieldmind/agent/prompts/tep").glob("*.txt")]
    texts += [json.dumps({k: c[k] for k in ("case_id", "title", "root_cause", "discriminating_evidence")}).lower()
              for c in LIB]
    for word in ("tennessee", "eastman", "idv", "xmeas", "xmv", "stream 4"):
        assert not any(word in t for t in texts), word


def test_library_uses_known_tags_and_only_the_three_triple_kinds():
    for c in LIB:
        assert c["case_id"].startswith("PF-") and c["contradicting_signature"] == {}
        for k in c["signature"]:
            tag, d, b = k.split("|")
            assert tag in TAGS
            assert (d, b) in {("UP", "*"), ("DOWN", "*"), ("HIGH", "-"), ("LOW", "-"), ("NOISY", "-")}


def test_level_and_variability_triples_come_from_facts():
    facts = [Fact("F1", "LIMIT", ["reactor_pressure"], (0, 1), 2800.0,
                  "reactor_pressure = 2800.0 > 2729.0 (alarm_hi)", "ALARM", 1.0),
             Fact("F2", "LIMIT", ["a_feed"], (0, 1), 0.1, "a_feed = 0.1 < 0.155 (alarm_lo)", "ALARM", 1.0),
             Fact("F3", "PATTERN", ["compressor_work"], (0, 1), 9.0,
                  "compressor_work fluctuating: spread of changes 9 over 60 min, above healthy 3", "WATCH", 0.8)]
    assert level_and_variability_triples(facts) == {
        ("reactor_pressure", "HIGH", "-"): 1.0, ("a_feed", "LOW", "-"): 1.0, ("compressor_work", "NOISY", "-"): 1.0}


def test_variability_check_fires_above_its_threshold_only():
    c = dict(CFG["checks"])
    c.update(limits={}, rates={}, rates_long={})
    w = SensorWindow(window_min=60.0, sample_period_s=180.0, tags=list(TAGS), tick_s=180.0)
    thr = c["variability"]["thresholds"]["compressor_work"]
    big = 100.0 * c["variability"]["thresholds"]["reactor_pressure"]
    for i in range(20):
        row = {t: 0.0 for t in TAGS}
        row["compressor_work"] = (i % 2) * 3.0 * thr        # changes of +-3 thr: spread 3 thr
        row["reactor_pressure"] = i * big                   # steady ramp: constant changes, spread 0
        w.append(i * 180.0, row)
    facts = CheckLayer(c, load_asset({"asset": "tep"})).run(w, tick=19, trusted=set(TAGS))
    noisy = [f.tags[0] for f in facts if f.check == "PATTERN"]
    # a trend is not variability: the ramp's VALUES spread widely, its changes do not
    assert noisy == ["compressor_work"]


@pytest.mark.skipif(not HAVE_DATA, reason="TEP data not present")
def test_fit_arithmetic_equals_the_agents_checks():
    """The fitting code's slope, direction and variability equal the agent's
    own functions on a real training run (fitted triples speak the agent's language)."""
    import numpy as np
    from data.tep.fit_signatures import directions, window_slopes, window_step_sd
    from fieldmind.agent.l1_symbolize import direction_and_band
    from fieldmind.agent.orchestrator import slopes_10min
    from statistics import pstdev
    X = cv.read_block("TEP_Faulty_Training.RData", 1, 12)[:80]
    bands, W = CFG["checks"]["bands"], 20
    S, V = window_slopes(X, W), window_step_sd(X, W)
    D = directions(S, np.array([bands[t][0] for t in TAGS]))
    w = SensorWindow(window_min=60.0, sample_period_s=180.0, tags=list(TAGS), tick_s=180.0)
    for i, row in enumerate(X):
        w.append(i * 180.0, dict(zip(TAGS, row)))
        if i >= W - 1:
            sl, k = slopes_10min(w, 60.0), i - W + 1
            for j, t in enumerate(TAGS):
                assert abs(sl[t] - S[k, j]) < 1e-9
                d, _ = direction_and_band(t, sl[t], bands)
                assert {"UP": 1, "DOWN": -1, "FLAT": 0}[d] == D[k, j]
                s = w.series(t)[-W:]
                assert abs(pstdev([b - a for a, b in zip(s[:-1], s[1:])]) - V[k, j]) < 1e-9


@pytest.mark.skipif(not HAVE_DATA, reason="TEP data not present")
def test_fault_runs_equal_their_fault_free_twin_until_the_onset():
    assert cv.check() == []


def test_split_is_the_preregistered_one():
    assert cv.DEV_RUNS == (1,) and cv.REPORT_RUNS == (2, 3, 4, 5, 6)
    assert cv.NORMAL_DEV_RUNS == (1, 2) and cv.NORMAL_REPORT_RUNS == tuple(range(3, 13))


def test_wildcard_and_level_triples_match_in_retrieval():
    lib = CaseLibrary.__new__(CaseLibrary)
    lib.cases = [c for c in LIB if c["case_id"] in ("PF-14", "PF-17")]
    lib.weights = {c["case_id"]: 1.0 for c in lib.cases}
    sig = {("reactor_temperature", "UP", "MED"): 1.0, ("reactor_cw_outlet_temp", "DOWN", "SLOW"): 1.0,
           ("reactor_cw_valve", "UP", "FAST"): 1.0, ("reactor_cw_outlet_temp", "LOW", "-"): 1.0}
    assert lib.match(sig)[0]["case_id"] == "PF-17"      # the level triple is what separates them
