"""Breadth B1, Step 2-3: the Cranfield asset pack, its config and the new
evaluator metric. Each test fails if the rule it names is broken."""
import json
from pathlib import Path

import pytest
import yaml

from bench.evaluator import t7_detection
from data.cranfield import convert as cv
from fieldmind.assets import load_asset
from fieldmind.assets.cranfield import PROCESS, SUPPLY, TAGS
from fieldmind.agent.l0_ingest import SensorWindow
from fieldmind.agent.l1_checks import CheckLayer
from fieldmind.kb.stores import CaseLibrary

ROOT = Path(__file__).resolve().parent.parent
LIB = json.loads((ROOT / "data/kb_cranfield/case_library.json").read_text())["cases"]


def test_pack_tags_are_the_converters_table1_order():
    assert list(TAGS) == cv.TAGS
    assert load_asset({"asset": "cranfield"}).tags == TAGS


def test_sides_partition_every_tag():
    assert SUPPLY | PROCESS == set(TAGS) and not SUPPLY & PROCESS


def test_case_signatures_use_known_tags_and_derived_bands_only():
    """Pre-registered rule: moving triples carry band '*' (direction derived,
    speed not), FLAT carries '-'. A concrete band would be an invented number."""
    for c in LIB:
        for sec in ("signature", "contradicting_signature"):
            for tag, (d, b) in c[sec].items():
                assert tag in TAGS, (c["case_id"], tag)
                assert (d, b) in {("UP", "*"), ("DOWN", "*"), ("FLAT", "-")}, (c["case_id"], tag, d, b)


def test_band_wildcard_matches_any_band_and_leaves_concrete_bands_alone():
    sig = {("vc302_position", "UP", "FAST"): 1.0, ("ft104_water_in", "FLAT", "-"): 0.35}
    wild = CaseLibrary._to_triples({"vc302_position": ["UP", "*"], "ft104_water_in": ["FLAT", "-"]})
    assert CaseLibrary.resolve_wildcards(wild, sig) == {("vc302_position", "UP", "FAST"): 1.0,
                                                        ("ft104_water_in", "FLAT", "-"): 0.35}
    # direction must still match: an UP expectation never takes a DOWN observation
    down = {("vc302_position", "DOWN", "MED"): 1.0}
    assert CaseLibrary.resolve_wildcards(wild, down)[("vc302_position", "UP", "*")] == 1.0
    concrete = {("drum_level", "DOWN", "FAST"): 1.0}
    assert CaseLibrary.resolve_wildcards(concrete, {("drum_level", "DOWN", "MED"): 1.0}) is concrete


def test_wildcard_case_wins_retrieval_on_its_own_direction():
    lib = CaseLibrary.__new__(CaseLibrary)
    lib.cases = [c for c in LIB if c["case_id"] in ("CF-1", "CF-2")]
    lib.weights = {c["case_id"]: 1.0 for c in lib.cases}
    sig = {("vc302_position", "UP", "SLOW"): 1.0, ("pt312_air_supply_p", "UP", "MED"): 1.0,
           ("vc101_position", "FLAT", "-"): 0.35, ("ft104_water_in", "FLAT", "-"): 0.35}
    assert lib.match(sig)[0]["case_id"] == "CF-1"


def test_stuck_tolerance_per_tag_and_scalar():
    cfg = yaml.safe_load((ROOT / "configs/base.yaml").read_text())["checks"]
    def run(eps):
        w = SensorWindow(window_min=5.0, sample_period_s=1.0, tags=["a", "b"])
        for i in range(200):
            w.append(float(i), {"a": 1.0, "b": 1.0 + 1e-6 * (i % 2)})
        c = dict(cfg, limits={}, rates={}, rates_long={}, balance={"window_min": 5.0},
                 validity={"stuck_minutes": 3.0, "stuck_mad_eps": eps,
                           "physical_range": {"a": [-9, 9], "b": [-9, 9]},
                           "max_step": {"a": 9, "b": 9}})
        return {f.tags[0] for f in CheckLayer(c, load_asset({"asset": "cranfield"})).run(
            w, tick=6, trusted={"a", "b"}) if f.check == "VALIDITY"}
    assert run(1e-12) == {"a"}                       # scalar: exactly-constant 'a' is frozen
    assert run({"a": 0.0, "b": 1e-12}) == set()      # per tag: check off for 'a'
    assert run({"a": 1e-12, "b": 1e-3}) == {"a", "b"}


def test_generated_config_is_all_numbers_and_up_to_date():
    from data.cranfield import calibrate
    text = calibrate.build()
    assert calibrate._all_numbers(yaml.safe_load(text)) == []
    assert (ROOT / "configs/cranfield.yaml").read_text() == text


def _run(states, wins, tick_s=30):
    return {"ground_truth": {"fault_windows": wins, "tick_period_s": tick_s},
            "assessments": [{"tick": k, "state": s} for k, s in enumerate(states)]}


def test_t7_detection_counts_inside_before_and_after_windows():
    # ticks published at 30, 60, ..., 300 s; fault window [100, 200)
    st = ["NORMAL", "ALARM", "NORMAL", "NORMAL", "ALARM", "ALARM", "NORMAL", "ALARM", "NORMAL", "NORMAL"]
    d = t7_detection(_run(st, [[100, 200]]))
    # inside: 120 (k=3), 150 (k=4), 180 (k=5) -> NORMAL, ALARM, ALARM
    assert d["n_fault_ticks"] == 3 and d["detection_rate"] == round(2 / 3, 3)
    # before: 30, 60, 90 -> one ALARM (60)
    assert d["far_before_fault"] == round(1 / 3, 3)
    # after: 210 ... 300 -> one ALARM (240) of four
    assert d["far_after_fault"] == 0.25
    assert d["detection_delay_s"] == 50.0           # first alarm at 150 s, window from 100 s
    assert t7_detection({"ground_truth": {}, "assessments": []}) == {"applicable": False}
