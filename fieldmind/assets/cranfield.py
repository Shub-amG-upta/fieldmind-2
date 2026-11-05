"""
=============================================================================
 CRANFIELD ASSET PACK  -- three-phase flow facility, 2015 benchmark (breadth B1)
=============================================================================

REAL rig data: Ruiz-Cárcel et al. 2015, Control Eng. Practice 42:74-88.
24 tags (Table 1), 1 Hz. Thresholds: configs/cranfield.yaml (fitted on the
normal sets by data/cranfield/calibrate.py). Cases: data/kb_cranfield/
(pre-registered, signatures derived from the rig layout).

No BALANCE family and no PATTERN family (HUMAN DECISION 2026-11-05): the only
candidate mass balance (water in vs top-separator liquid out) does not close
on normal data (reports/b1_cranfield_data.md). Relations fitted on the normal
sets are a later, separately measured step.

No trip lines: the paper publishes no interlocks for this configuration.

Sides (DESIGN, from the flow path of section 2.2): `supply` = the air and
water inlet lines up to the mixing point (each with its meter, control valve
and, for air, the delivery pressure; the water pump); `process` = everything
after the mixing point (riser, top separator, 3-phase separator, 2in line).
Faults 1-2 act on the supply, 3-6 on the process.

Stdlib only.
=============================================================================
"""

from __future__ import annotations

from . import AssetPack, SideSpec

# Table 1 order (data/cranfield/convert.VARIABLES; tests check they agree).
TAGS = (
    "pt312_air_supply_p", "pt401_riser_bottom_p", "pt408_riser_top_p", "pt403_top_sep_p",
    "pt501_3ph_sep_p", "dp_riser", "dp_vc404", "ft305_air_in", "ft104_water_in",
    "ft407_riser_top_flow", "li405_top_sep_level", "ft406_top_sep_out_flow",
    "ft407_riser_top_density", "ft406_top_sep_out_density", "ft104_water_in_density",
    "ft407_riser_top_temp", "ft406_top_sep_out_temp", "ft104_water_in_temp",
    "li504_3ph_sep_level", "vc501_position", "vc302_position", "vc101_position",
    "po1_pump_current", "pt417_2in_line_p",
)

SUPPLY = frozenset({"pt312_air_supply_p", "ft305_air_in", "vc302_position",
                    "ft104_water_in", "vc101_position", "po1_pump_current",
                    "ft104_water_in_density", "ft104_water_in_temp"})
PROCESS = frozenset(TAGS) - SUPPLY


def _none(*_a, **_k):
    return []


SIDES = SideSpec(
    sides=("supply", "process"),
    side_tags={"supply": SUPPLY, "process": PROCESS},
    pseudo={},
    # no balance family; a BALANCE fact cannot occur, the process side is a
    # safe default if one ever did
    balance_side=lambda tags: "supply" if tags and tags <= SUPPLY else "process",
    pattern_side={},
    side_note={
        "supply": "This prompt covers the SUPPLY side only: the air and water inlet lines "
                  "(flow meters, flow control valves, air delivery pressure, water pump).",
        "process": "This prompt covers the PROCESS side only: the riser, the top separator, "
                   "the 3-phase separator and the 2in line.",
    },
)

PACK = AssetPack(
    name="cranfield",
    tags=TAGS,
    balances=_none,
    patterns=_none,
    balance_triples=lambda facts: {},
    balance_fact_sel=lambda facts, tag: None,
    trip_lines=(),
    quiet_headline="All parameters within their normal range.",
    sides=SIDES,
    prompt_dir="cranfield",
)
