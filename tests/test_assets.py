"""Breadth phase B1: the asset pack is the only place a plant is named.

Each test builds a toy asset that differs from the boiler and checks that the
component under test follows the PACK, not boiler code. A component that
ignored the pack (the pre-B1 behaviour) fails here. The boiler itself is
checked end to end by the run-identity comparison in reports/b1_*.
"""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from fieldmind.agent import world_model as wmod
from fieldmind.agent.l0_ingest import SensorWindow
from fieldmind.agent.l1_checks import CheckLayer
from fieldmind.agent.l1_symbolize import build_signature, headline
from fieldmind.agent.l2_triage import triage
from fieldmind.agent.orchestrator import refresh_trust_and_residuals
from fieldmind.assets import AssetPack, SideSpec, default_asset, load_asset
from fieldmind.multi import sides
from fieldmind.schemas import Fact

ROOT = Path(__file__).resolve().parent.parent
CHECKS = yaml.safe_load((ROOT / "configs/base.yaml").read_text())["checks"]


def _marker_balance(layer, w, tick, ids, trusted, blowdown):
    return [Fact(ids.next(), "BALANCE", ["x_in", "x_out"], (0, tick), 2.5,
                 "toy balance residual", "ALARM", 1.0)]


TOY = AssetPack(
    name="toy", tags=("x_in", "x_out", "p"),
    balances=_marker_balance,
    patterns=lambda layer, w, tick, ids, trusted, sofar: [],
    balance_triples=lambda facts: {("x_balance", "LOSS", "-"): 1.0}
    if any(f.check == "BALANCE" for f in facts) else {},
    balance_fact_sel=lambda facts, tag: ([f for f in facts if f.check == "BALANCE"]
                                         if tag == "x_balance" else None),
    trip_lines=(("p", "up", 10.0),),
    quiet_headline="toy quiet",
    sides=SideSpec(sides=("gas", "liquid"),
                   side_tags={"gas": frozenset({"p"}), "liquid": frozenset({"x_in", "x_out"})},
                   pseudo={"x_balance": "liquid"},
                   balance_side=lambda tags: "liquid",
                   pattern_side={}, side_note={"gas": "g", "liquid": "l"}),
)


def test_default_asset_is_boiler_and_unknown_raises():
    assert load_asset({}).name == "boiler"
    assert load_asset({"asset": "boiler"}) is default_asset()
    with pytest.raises(ValueError):
        load_asset({"asset": "no_such_plant"})
    assert CheckLayer(CHECKS).asset is default_asset()


def test_check_layer_runs_the_asset_balances():
    w = SensorWindow(window_min=10.0, sample_period_s=5.0, tags=list(TOY.tags))
    for i in range(60):
        w.append(i * 5.0, {"x_in": 1.0, "x_out": 1.0, "p": 1.0})
    cfg = dict(CHECKS, limits={}, rates={}, rates_long={},
               validity={"stuck_minutes": 99, "stuck_mad_eps": 0.0,
                         "physical_range": {t: [-1e9, 1e9] for t in TOY.tags},
                         "max_step": {t: 1e9 for t in TOY.tags}})
    facts = CheckLayer(cfg, TOY).run(w, tick=10, trusted=set(TOY.tags))
    assert [f.detail for f in facts] == ["toy balance residual"]


def test_signature_uses_the_asset_pseudo_triples_not_the_boilers():
    f = Fact("F1", "BALANCE", ["feed_water_flow", "steam_flow", "drum_level"], (0, 1),
             -5.0, "water balance residual", "ALARM", 0.9)
    toy = build_signature([f], {}, {"x": [0, 1, 2]}, TOY)
    assert ("x_balance", "LOSS", "-") in toy and not any(k[0] == "water_balance" for k in toy)
    boil = build_signature([f], {}, {"x": [0, 1, 2]})
    assert ("water_balance", "DEFICIT", "FAST") in boil


def test_belief_cites_the_asset_balance_facts_for_its_pseudo_tag():
    f = Fact("F7", "BALANCE", ["x_in", "x_out"], (0, 1), 2.5, "toy", "ALARM", 1.0)
    assert wmod._fact_ids([f], "x_balance", TOY) == ["F7"]
    assert wmod._fact_ids([f], "x_balance") == []          # boiler: no such pseudo-tag


def test_triage_extrapolates_to_the_asset_trip_lines():
    f = Fact("F1", "RATE", ["p"], (0, 1), 1.0, "p rising", "WATCH", 0.8)
    wm = SimpleNamespace(residuals={"last_p": 8.0}, open_findings=[])
    cfg = {"triage": {"trip_horizon_min": 5.0}}
    assert triage([f], wm, cfg, TOY)[0] == "URGENT"        # 2 min to the trip line
    assert triage([f], wm, cfg)[0] == "WATCH"              # the boiler has no trip on p


def test_trust_and_world_model_follow_the_window_tags():
    w = SensorWindow(window_min=10.0, sample_period_s=5.0, tags=list(TOY.tags))
    w.append(0.0, {"x_in": 1.0, "x_out": 1.0, "p": 3.0})
    wm = wmod.new_world_model("e", [], TOY.tags)
    assert wm.trusted_tags == set(TOY.tags) and list(wm.baselines) == list(TOY.tags)
    refresh_trust_and_residuals(wm, [], w)
    assert wm.trusted_tags == set(TOY.tags) and wm.residuals["last_p"] == 3.0


def test_sides_follow_the_asset_spec():
    sd = sides.for_asset(TOY)
    f = Fact("F1", "LIMIT", ["p"], (0, 1), 1.0, "p high", "ALARM", 1.0)
    bal = Fact("F2", "BALANCE", ["x_in", "x_out"], (0, 1), 1.0, "b", "ALARM", 1.0)
    assert sd.fact_sides(f) == {"gas"} and sd.fact_sides(bal) == {"liquid"}
    assert sd.sides_to_run([], []) == ["gas", "liquid"]
    assert sd.primary_side([bal]) == "liquid"
    with pytest.raises(ValueError):
        sides.for_asset(replace(TOY, sides=None))


def test_quiet_headline_is_the_assets():
    assert headline([], TOY.quiet_headline) == "toy quiet"
    assert headline([]) == "All six parameters within band; balances close."
