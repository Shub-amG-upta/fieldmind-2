"""
=============================================================================
 BOILER ASSET PACK  -- 67 TPH AFBC bi-drum boiler (the original plant)
=============================================================================

The boiler-specific code MOVED here from fieldmind/agent/l1_checks.py
(_balances, _patterns), l1_symbolize.build_signature (balance pseudo-triples),
world_model._fact_ids (pseudo-tag -> BALANCE facts), l2_triage._trip_predicted
(trip lines), multi/sides.py (water/heat split) and multi/agents/diagnostician
(side notes). Bodies are unchanged; `self` became `layer` (the CheckLayer).
The pre-refactor mock runs are reproduced byte for byte (reports/b1_*).

Stdlib only.
=============================================================================
"""

from __future__ import annotations

from ..agent.l1_checks import _load_normalised_bed_slope, _slope_per_min
from ..schemas import TAGS, Fact
from . import AssetPack, SideSpec


# ---------------------------------------------------------------- L1 BALANCE
def balances(layer, w, tick, ids, trusted, blowdown) -> list[Fact]:
    """Do the physics still add up?  (Plan §4.2)

    This family carries most of the value. Limit checks tell you something
    is already wrong; balance checks tell you something is wrong BEFORE
    anything crosses a limit, and they tell you WHICH SIDE of the plant it
    is on.

    Two balances close over the six tags:

      WATER (mass)  feed - steam - blowdown  should equal  level_slope/K
      ENERGY        inferred, since there is no coal-flow sensor
    """
    out = []
    K = layer.balance["level_gain_pct_per_min_per_tph"]     # 0.22
    need = int(layer.balance["window_min"] * 60 / layer.dt_s)

    # ---------- water balance ----------
    water_tags = {"feed_water_flow", "steam_flow", "drum_level"}
    if water_tags <= trusted and len(w.series("drum_level")) >= need:
        feed = w.mean("feed_water_flow", need)
        steam = w.mean("steam_flow", need)
        actual_slope = _slope_per_min(w.series("drum_level")[-need:], layer.dt_s)
        expected_slope = (feed - steam - blowdown) * K
        residual_tph = (feed - steam - blowdown) - actual_slope / K

        if abs(residual_tph) > layer.balance["residual_tph"]:
            # Sign carries the diagnosis, so it goes in the detail text
            # rather than being left for the model to work out.
            # Sign convention: residual = measured net inflow MINUS the
            # inflow the level movement implies.
            #   positive -> more water is going in than the drum shows, so
            #               it is leaving somewhere unmeasured (leak, CBD
            #               passing) or the level reading is false
            #   negative -> level is holding/rising on less measured inflow
            #               than that requires, so a flow meter under-reads
            if residual_tph > 0:
                reading = ("measured inflow exceeds what the drum level shows "
                           "-> water is being lost between the feed meter and "
                           "the drum (leak, blowdown passing), or the level "
                           "reading is false")
            else:
                reading = ("drum level is holding on less measured inflow than "
                           "that requires -> a flow transmitter is likely "
                           "under-reading")
            out.append(Fact(ids.next(), "BALANCE",
                            ["feed_water_flow", "steam_flow", "drum_level"],
                            w.window_ticks(tick), residual_tph,
                            f"water balance residual {residual_tph:+.1f} TPH "
                            f"(feed {feed:.1f}, steam {steam:.1f}, level slope "
                            f"{actual_slope:+.2f} %/min vs expected "
                            f"{expected_slope:+.2f}): {reading}",
                            "ALARM", 0.9))
    elif not water_tags <= trusted:
        # SUSPENDED, not silently skipped. The engineer must be told that a
        # check they rely on is not running (Plan §9).
        missing = sorted(water_tags - trusted)
        out.append(Fact(ids.next(), "BALANCE", missing,
                        w.window_ticks(tick), 0.0,
                        f"water balance SUSPENDED - untrusted tag(s): "
                        f"{', '.join(missing)}", "WATCH", 1.0))

    # ---------- energy balance (inferred) ----------
    energy_tags = {"drum_pressure", "steam_flow", "bed_temp_avg"}
    if energy_tags <= trusted and len(w.series("drum_pressure")) >= need:
        p_slope = _slope_per_min(w.series("drum_pressure")[-need:], layer.dt_s)
        steam_slope = _slope_per_min(w.series("steam_flow")[-need:], layer.dt_s)
        # Load-normalised: heat ACCUMULATING means the bed is hotter than
        # the current load explains, not merely hotter than before.
        bed_slope = _load_normalised_bed_slope(w, need, layer.dt_s,
                                               layer.load_coef)
        flat_steam = abs(steam_slope) < layer.balance["steam_flat_tph_per_min"]

        # With no fuel-flow sensor at all, these three slopes still separate
        # "heat input short" from "heat not being absorbed".
        if p_slope < -layer.balance["p_falling"] and flat_steam:
            out.append(Fact(ids.next(), "BALANCE",
                            ["drum_pressure", "steam_flow"],
                            w.window_ticks(tick), p_slope,
                            f"pressure falling {p_slope:+.3f} kg/cm2/min at "
                            f"flat steam flow -> heat input short",
                            "WATCH", 0.85))
        elif bed_slope > layer.balance["bed_rising"] and flat_steam \
                and abs(p_slope) < layer.balance["p_falling"]:
            out.append(Fact(ids.next(), "BALANCE",
                            ["bed_temp_avg", "steam_flow", "drum_pressure"],
                            w.window_ticks(tick), bed_slope,
                            f"bed rising {bed_slope:+.2f} degC/min with flat "
                            f"steam and flat pressure -> heat accumulating "
                            f"in the bed, not being absorbed",
                            "WATCH", 0.85))
    return out


# ---------------------------------------------------------------- L1 PATTERN
def patterns(layer, w, tick, ids, trusted, sofar) -> list[Fact]:
    """Does a known named signature match?

    Patterns are hand-written multi-tag conjunctions. They are NOT the
    retrieval layer -- these are the two or three combinations worth
    naming outright because the name itself is what the engineer says.
    """
    out = []
    need = int(layer.balance["window_min"] * 60 / layer.dt_s)
    if len(w.series("bed_temp_avg")) < need:
        return out

    bed = _load_normalised_bed_slope(w, need, layer.dt_s, layer.load_coef)
    steam = _slope_per_min(w.series("steam_flow")[-need:], layer.dt_s)
    press = _slope_per_min(w.series("drum_pressure")[-need:], layer.dt_s)
    level = _slope_per_min(w.series("drum_level")[-need:], layer.dt_s)

    flat = layer.balance["steam_flat_tph_per_min"]
    # Bed-slope gates re-scaled for the stage-4 noise model: over a 5-min
    # window the load-normalised bed slope has a no-fault p99.7 of ~1.2
    # degC/min (OU load + per-subsystem process disturbances), so the old
    # 0.4 / 0.2 / 0.1 literals fired the "energy accumulating" pattern ~15
    # times an hour on a healthy plant. `bed_rising` (config) is 1.3 and
    # these track it. (These belong in the config; left as literals for the
    # L1/agent stage to move.)
    bed_rising = layer.balance["bed_rising"]

    if bed > bed_rising and abs(steam) < flat and abs(press) < 0.05:
        out.append(Fact(ids.next(), "PATTERN",
                        ["bed_temp_avg", "steam_flow", "drum_pressure"],
                        w.window_ticks(tick), bed,
                        "signature 'energy accumulating in bed': bed rising, "
                        "steam flat, pressure flat", "WATCH", 0.8))

    if level < -0.3 and abs(bed) < 0.5:
        out.append(Fact(ids.next(), "PATTERN",
                        ["drum_level", "bed_temp_avg"],
                        w.window_ticks(tick), level,
                        "signature 'water side only': level falling while the "
                        "heat side is untouched", "WATCH", 0.8))

    # Absence of expected evidence is information too (Plan §5.1 rule 2),
    # so a deliberately-INFO fact records a quiet heat side. It costs a few
    # prompt tokens and it lets the model rule things OUT.
    if abs(bed) < 0.3 and abs(press) < 0.02:
        out.append(Fact(ids.next(), "PATTERN",
                        ["bed_temp_avg", "drum_pressure"],
                        w.window_ticks(tick), 0.0,
                        "heat side steady (bed and pressure both flat)",
                        "INFO", 0.9))
    return out


# ------------------------------------------------- signature pseudo-triples
def balance_triples(facts) -> dict:
    """A slope-only signature cannot tell a feed-path fault from a leak: in
    both, level moves and feed moves. What separates them is the SIGN OF
    THE WATER BALANCE RESIDUAL, which is a relationship between levels, not
    a slope. Encoding it as a pseudo-tag lets the same weighted-Jaccard
    matcher use it with no special-casing."""
    sig = {}
    for f in facts:
        if f.check != "BALANCE":
            continue
        if "SUSPENDED" in f.detail:
            continue
        if set(f.tags) >= {"feed_water_flow", "steam_flow"}:
            direction = "DEFICIT" if f.value < 0 else "SURPLUS"
            band = "FAST" if abs(f.value) > 4.0 else "MED"
            sig[("water_balance", direction, band)] = 1.0
        elif "drum_pressure" in f.tags and "heat input short" in f.detail:
            sig[("energy_balance", "HEAT_SHORT", "-")] = 1.0
        elif "bed_temp_avg" in f.tags and "accumulating" in f.detail:
            sig[("energy_balance", "HEAT_ACCUMULATING", "-")] = 1.0
    return sig


def balance_fact_sel(facts, tag):
    """The two balance pseudo-tags in the signature map to BALANCE facts:
    water balance is the one naming feed and steam flow, energy balance the
    rest. None for a real tag (the caller then selects by tag name)."""
    water = {"feed_water_flow", "steam_flow"}
    if tag == "water_balance":
        return [f for f in facts if f.check == "BALANCE" and water <= set(f.tags)]
    if tag == "energy_balance":
        return [f for f in facts if f.check == "BALANCE" and not water <= set(f.tags)]
    return None


# ------------------------------------------------------------------- sides
# DESIGN, CITED: plan p.5 ("Heat diagnostician ... bed temperature, pressure,
# steam temperature, with steam flow as load").
_WATER_BALANCE_TAGS = frozenset({"feed_water_flow", "steam_flow", "drum_level"})

SIDES = SideSpec(
    sides=("water", "heat"),
    side_tags={
        "water": frozenset({"drum_level", "feed_water_flow", "steam_flow"}),
        "heat": frozenset({"bed_temp_avg", "drum_pressure", "ms_temperature", "steam_flow"}),
    },
    pseudo={"water_balance": "water", "energy_balance": "heat"},
    # CITED: balances() above, `water_tags`. A BALANCE fact whose tags all lie
    # in this set is the water balance (or its SUSPENDED notice, which names
    # only the untrusted water tags); every other BALANCE fact is energy.
    balance_side=lambda tags: "water" if tags <= _WATER_BALANCE_TAGS else "heat",
    # CITED: patterns() above. A PATTERN fact's tags include the CONTEXT tags
    # its condition reads, so its side is the side the pattern names:
    #   'energy accumulating in bed'  bed, steam, pressure  -> heat
    #   'water side only'             level, bed            -> water
    #   'heat side steady' (INFO)     bed, pressure         -> heat
    pattern_side={
        frozenset({"bed_temp_avg", "steam_flow", "drum_pressure"}): "heat",
        frozenset({"drum_level", "bed_temp_avg"}): "water",
        frozenset({"bed_temp_avg", "drum_pressure"}): "heat",
    },
    side_note={         # one line naming the side; plan p.5 agent table
        "water": "This prompt covers the WATER side only: drum level, feed water flow, steam flow.",
        "heat": "This prompt covers the HEAT side only: bed temperature, drum pressure, main "
                "steam temperature, with steam flow as the load.",
    },
)


PACK = AssetPack(
    name="boiler",
    tags=tuple(TAGS),
    balances=balances,
    patterns=patterns,
    balance_triples=balance_triples,
    balance_fact_sel=balance_fact_sel,
    # Linear extrapolation to the boiler's trips: drum level T-02 (< 10 %) and
    # bed temperature T-07 (> 940 degC), data/kb/asset_model.json interlocks.
    trip_lines=(("drum_level", "down", 10.0), ("bed_temp_avg", "up", 940.0)),
    quiet_headline="All six parameters within band; balances close.",
    sides=SIDES,
    prompt_dir=None,
)
