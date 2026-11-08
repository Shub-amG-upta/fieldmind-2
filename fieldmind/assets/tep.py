"""
=============================================================================
 TEP ASSET PACK  -- Tennessee Eastman Process (breadth B2)
=============================================================================

SIMULATED chemical plant (Downs & Vogel 1993; data Rieth et al. 2017): 52
variables, one sample per 3 min. Thresholds: configs/tep.yaml (fitted on the
fault-free training runs by data/tep/calibrate.py). Cases: data/kb_tep/
(signatures FITTED on the official faulty TRAINING runs, frozen before any
test run; human decision 2026-11-07).

Tags are plain names (data/tep/convert.VARIABLES): nothing that names the
benchmark or its variable/fault numbering reaches a prompt (memorisation).

No BALANCE family (as Cranfield: fitted relations are a later, separately
measured step). Signature vocabulary (HUMAN DECISION 2026-11-07, because TEP
faults mostly settle at a new LEVEL or change the VARIABILITY of a tag, which
a slope cannot express):
  movement   (tag, UP|DOWN, band)   the shared slope signature
  level      (tag, HIGH|LOW, "-")   from this tick's LIMIT facts (the healthy
                                    p0.1/p99.9 envelope, configs/tep.yaml)
  variability(tag, NOISY, "-")      from this pack's PATTERN facts: the sd of
                                    the sample-to-sample changes over 60 min
                                    above its healthy p99.7
  shift      (tag, SHIFT_UP|SHIFT_DOWN, "-")  INFO PATTERN facts: the 60-min mean
                                    away from the episode's first hour by more
                                    than the healthy p99.7 (accuracy-fixes step 5)
  spread     (tag, WIDE, "-")       INFO PATTERN facts: the sd of the VALUES over
                                    60 min above its healthy p99.7 (step 5)

No trip lines (the data set has no interlocks: runs that would shut down are
not in it).

Sides (DESIGN, from the flowsheet in Downs & Vogel Fig. 1): `reaction` = the
four feeds, the reactor, its cooling and the reactor feed analysis;
`separation` = condenser, separator, compressor/recycle, stripper, purge, and
the purge and product analyses.

Stdlib only.
=============================================================================
"""

from __future__ import annotations

from statistics import fmean, pstdev

from ..schemas import Fact
from . import AssetPack, SideSpec

TAGS = (
    "a_feed", "d_feed", "e_feed", "a_c_feed", "recycle_flow", "reactor_feed_rate",
    "reactor_pressure", "reactor_level", "reactor_temperature", "purge_rate",
    "separator_temperature", "separator_level", "separator_pressure", "separator_underflow",
    "stripper_level", "stripper_pressure", "stripper_underflow", "stripper_temperature",
    "stripper_steam_flow", "compressor_work", "reactor_cw_outlet_temp", "separator_cw_outlet_temp",
    "reactor_feed_a", "reactor_feed_b", "reactor_feed_c", "reactor_feed_d", "reactor_feed_e",
    "reactor_feed_f",
    "purge_gas_a", "purge_gas_b", "purge_gas_c", "purge_gas_d", "purge_gas_e", "purge_gas_f",
    "purge_gas_g", "purge_gas_h",
    "product_d", "product_e", "product_f", "product_g", "product_h",
    "d_feed_valve", "e_feed_valve", "a_feed_valve", "a_c_feed_valve", "compressor_recycle_valve",
    "purge_valve", "separator_liquid_valve", "stripper_product_valve", "stripper_steam_valve",
    "reactor_cw_valve", "condenser_cw_valve",
)

REACTION = frozenset({
    "a_feed", "d_feed", "e_feed", "a_c_feed", "reactor_feed_rate", "reactor_pressure",
    "reactor_level", "reactor_temperature", "reactor_cw_outlet_temp",
    "reactor_feed_a", "reactor_feed_b", "reactor_feed_c", "reactor_feed_d", "reactor_feed_e",
    "reactor_feed_f", "d_feed_valve", "e_feed_valve", "a_feed_valve", "a_c_feed_valve",
    "reactor_cw_valve",
})
SEPARATION = frozenset(TAGS) - REACTION


def _none(*_a, **_k):
    return []


def variability(layer, w, tick, ids, trusted, sofar) -> list:
    """PATTERN fact per trusted tag whose 60-min spread of sample-to-sample
    changes exceeds the healthy p99.7 (checks.variability, fitted on the
    fault-free training runs by data/tep/calibrate.py)."""
    v = layer.cfg.get("variability") or {}
    thr = v.get("thresholds", {})
    n = int(v.get("window_min", 60.0) * 60 / layer.dt_s)
    out = []
    for tag in w.tags:
        if tag not in trusted or tag not in thr:
            continue
        s = w.series(tag)
        if len(s) < n:
            continue
        d = [b - a for a, b in zip(s[-n:-1], s[-n + 1:])]
        sd = pstdev(d)
        if sd > thr[tag]:
            out.append(Fact(ids.next(), "PATTERN", [tag], w.window_ticks(tick), sd,
                            f"{tag} fluctuating: spread of changes {sd:.3g} over "
                            f"{v.get('window_min', 60.0):.0f} min, above healthy {thr[tag]:.3g}",
                            "WATCH", 0.8))
    return out


def shift_and_spread(layer, w, tick, ids, trusted, sofar) -> list:
    """Accuracy-fixes step 5 (pre-registered, reports/accuracy_fixes.md). INFO
    PATTERN facts -- they never raise the plant state -- per trusted tag:
      SHIFT  |mean of the last 60 min - mean of the episode's first 60 min| above
             the healthy p99.7 (checks.shift). The baseline is the first full
             window, captured once (the episode starts healthy; on a live plant
             it would be the last NORMAL hour).
      WIDE   sd of the values over 60 min above the healthy p99.7 (checks.spread).
    Both off when the config has no `shift` / `spread` section (B2 behaviour)."""
    sh, sp = layer.cfg.get("shift") or {}, layer.cfg.get("spread") or {}
    if not sh and not sp:
        return []
    base = layer.__dict__.setdefault("_tep_baseline", {})
    out = []
    for tag in w.tags:
        if tag not in trusted:
            continue
        s = w.series(tag)
        if sh and tag in sh["thresholds"]:
            n = int(sh.get("window_min", 60.0) * 60 / layer.dt_s)
            if tag not in base and len(s) >= n:
                base[tag] = fmean(s[:n])
            if tag in base and len(s) >= n:
                d = fmean(s[-n:]) - base[tag]
                thr = sh["thresholds"][tag]
                if abs(d) > thr:
                    out.append(Fact(ids.next(), "PATTERN", [tag], w.window_ticks(tick), d,
                                    f"{tag} shifted {'up' if d > 0 else 'down'} by {abs(d):.3g} from "
                                    f"the first hour, above healthy {thr:.3g}", "INFO", 0.8))
        if sp and tag in sp["thresholds"]:
            n = int(sp.get("window_min", 60.0) * 60 / layer.dt_s)
            if len(s) >= n:
                sd = pstdev(s[-n:])
                thr = sp["thresholds"][tag]
                if sd > thr:
                    out.append(Fact(ids.next(), "PATTERN", [tag], w.window_ticks(tick), sd,
                                    f"{tag} widened: spread of values {sd:.3g} over "
                                    f"{sp.get('window_min', 60.0):.0f} min, above healthy {thr:.3g}",
                                    "INFO", 0.8))
    return out


def patterns(layer, w, tick, ids, trusted, sofar) -> list:
    """The TEP pack's PATTERN family: variability, then shift and spread."""
    return (variability(layer, w, tick, ids, trusted, sofar)
            + shift_and_spread(layer, w, tick, ids, trusted, sofar))


def level_and_variability_triples(facts) -> dict:
    """Signature triples beyond the slope: level from LIMIT facts (alarm_hi ->
    HIGH, alarm_lo -> LOW) and variability from this pack's PATTERN facts."""
    sig = {}
    for f in facts:
        if f.check == "LIMIT" and f.tags:
            if f.detail.endswith("(alarm_hi)"):
                sig[(f.tags[0], "HIGH", "-")] = 1.0
            elif f.detail.endswith("(alarm_lo)"):
                sig[(f.tags[0], "LOW", "-")] = 1.0
        elif f.check == "PATTERN" and f.tags and "fluctuating" in f.detail:
            sig[(f.tags[0], "NOISY", "-")] = 1.0
        elif f.check == "PATTERN" and f.tags and " shifted up " in f.detail:
            sig[(f.tags[0], "SHIFT_UP", "-")] = 1.0
        elif f.check == "PATTERN" and f.tags and " shifted down " in f.detail:
            sig[(f.tags[0], "SHIFT_DOWN", "-")] = 1.0
        elif f.check == "PATTERN" and f.tags and " widened: " in f.detail:
            sig[(f.tags[0], "WIDE", "-")] = 1.0
    return sig


SIDES = SideSpec(
    sides=("reaction", "separation"),
    side_tags={"reaction": REACTION, "separation": SEPARATION},
    pseudo={},
    balance_side=lambda tags: "reaction" if tags and tags <= REACTION else "separation",
    pattern_side={},
    side_note={
        "reaction": "This prompt covers the REACTION side only: the feeds, the reactor, its "
                    "cooling water and the reactor feed analysis.",
        "separation": "This prompt covers the SEPARATION side only: condenser, separator, "
                      "recycle compressor, stripper, purge, and the purge and product analyses.",
    },
)

PACK = AssetPack(
    name="tep",
    tags=TAGS,
    balances=_none,
    patterns=patterns,
    balance_triples=level_and_variability_triples,
    balance_fact_sel=lambda facts, tag: None,
    trip_lines=(),
    quiet_headline="All parameters within their normal range.",
    sides=SIDES,
    prompt_dir="tep",
)
