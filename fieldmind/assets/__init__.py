"""
=============================================================================
 ASSET PACKS  (breadth phase B1)
=============================================================================

Everything that ties the agent to ONE plant lives in an asset pack: its tag
list, the plant-physics checks of L1 (BALANCE, PATTERN), the balance
pseudo-tags of the signature, the trip lines triage extrapolates to, the
plant sides the multi-agent diagnosticians are split by, and the prompt
wording. The scheduler, lanes, blackboard, gate, belief update and merge rules
read the pack and never name a tag themselves.

`load_asset(cfg)` picks the pack named by the top-level config key `asset`
(default "boiler", so a config without the key behaves exactly as before).

Stdlib only (copied to the device with the rest of fieldmind/).
=============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True)
class SideSpec:
    """How a plant is split between side diagnosticians (fieldmind/multi/sides).

    sides         side names, in order; the first one wins a severity tie
    side_tags     side -> tags whose facts belong to it (a tag may be in both)
    pseudo        balance pseudo-tag of the signature -> its side
    balance_side  BALANCE fact tags -> side (a SUSPENDED notice included)
    pattern_side  PATTERN fact tag set -> side
    side_note     side -> the one line naming the side in its prompt
    """
    sides: tuple
    side_tags: dict
    pseudo: dict
    balance_side: Callable
    pattern_side: dict
    side_note: dict


@dataclass(frozen=True)
class AssetPack:
    name: str
    tags: tuple
    # L1 plant physics: (layer, window, tick, ids, trusted, blowdown) -> [Fact]
    balances: Callable
    # L1 named patterns: (layer, window, tick, ids, trusted, facts so far) -> [Fact]
    patterns: Callable
    # signature pseudo-triples from BALANCE facts: facts -> {(tag, dir, band): w}
    balance_triples: Callable
    # belief: non-INFO fact ids for a pseudo-tag, or None if `tag` is a real tag
    balance_fact_sel: Callable
    # triage trip extrapolation: (tag, direction "down"|"up", trip value)
    trip_lines: tuple = ()
    quiet_headline: str = "All parameters within band; balances close."
    sides: SideSpec | None = None
    # sub-folder of the prompt folders holding this asset's wording (None = the
    # top-level templates, i.e. the boiler's)
    prompt_dir: str | None = None
    extra: dict = field(default_factory=dict)


def load_asset(cfg: dict | None) -> AssetPack:
    """The pack named by cfg["asset"] (default "boiler")."""
    name = (cfg or {}).get("asset", "boiler")
    if name == "boiler":
        from .boiler import PACK
        return PACK
    if name == "cranfield":
        from .cranfield import PACK
        return PACK
    raise ValueError(f"unknown asset {name!r} (known: boiler, cranfield)")


def default_asset() -> AssetPack:
    """The default pack, for call sites built without a config (unit tests)."""
    from .boiler import PACK
    return PACK
