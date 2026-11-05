"""
=============================================================================
 PLANT SIDES  (multi-agent Phase 3, "Split by side"; plan p.5 agent table)
=============================================================================

Pure functions: which facts, findings, cases, signature triples and
note-facts belong to the water side and to the heat side. No board, no
backend. Retrieval and belief are NOT split (Phase 3 decision 4 and the
"Sides" section of reports/multi_phase3_split.md): these functions only decide
what each side's diagnostician is shown and when a side is active.

  water   drum_level, feed_water_flow, steam_flow        + water_balance
  heat    bed_temp_avg, drum_pressure, ms_temperature,
          steam_flow (as load)                           + energy_balance

The split itself is the asset's (fieldmind/assets, AssetPack.sides): the
functions below are methods of `Sides(spec)`; the module-level names are the
boiler's, unchanged, for callers built without an asset.

Stdlib only (copied to the device with the rest of fieldmind/).
=============================================================================
"""

from __future__ import annotations

SEV_RANK = {"CRITICAL": 0, "ALARM": 1, "WATCH": 2, "INFO": 3}


def _id_key(fid: str):
    """F2 before F10 (natural order of the local id)."""
    head, _, num = fid.rpartition("F")
    return (head, int(num)) if num.isdigit() else (fid, 0)


class Sides:
    """The plant-side functions for one asset's SideSpec."""

    def __init__(self, spec):
        self.spec = spec
        self.SIDES = tuple(spec.sides)
        self.SIDE_TAGS = spec.side_tags
        self.PSEUDO = spec.pseudo
        self.PATTERN_SIDE = spec.pattern_side
        self.SIDE_NOTE = spec.side_note

    def _sides_of_tags(self, tags) -> set[str]:
        tags = set(tags)
        return {s for s in self.SIDES if tags & self.SIDE_TAGS[s]}

    def fact_sides(self, fact) -> set[str]:
        """A BALANCE fact goes to the side the asset assigns its tags (the
        boiler: water when all its tags are water-balance tags, the balance
        itself or "water balance SUSPENDED - untrusted drum_level", otherwise
        heat). Any other fact belongs to every side whose tags it names
        (steam_flow: both)."""
        return self._sides_of_check(fact.check, set(fact.tags))

    def _sides_of_check(self, check: str, tags: set) -> set[str]:
        if check == "BALANCE":
            return {self.spec.balance_side(tags)}
        if check == "PATTERN" and frozenset(tags) in self.PATTERN_SIDE:
            return {self.PATTERN_SIDE[frozenset(tags)]}
        return self._sides_of_tags(tags)

    def facts_for_side(self, facts, side: str) -> list:
        return [f for f in facts if side in self.fact_sides(f)]

    def finding_sides(self, finding) -> set[str]:
        """Findings are keyed `CHECK:tag|tag` (world_model.update_findings)."""
        check, _, tags = finding.signature_key.partition(":")
        return self._sides_of_check(check, set(filter(None, tags.split("|"))))

    def active_sides(self, facts, findings) -> list[str]:
        """Sides with a non-INFO fact or an open finding, in SIDES order. Empty
        when neither side has evidence (decision 5: then both sides are asked)."""
        act = set()
        for f in facts:
            if f.severity != "INFO":
                act |= self.fact_sides(f)
        for fnd in findings:
            if not fnd.resolved:
                act |= self.finding_sides(fnd)
        return [s for s in self.SIDES if s in act]

    def sides_to_run(self, facts, findings) -> list[str]:
        """The active sides; both when neither has evidence (decision 5)."""
        return self.active_sides(facts, findings) or list(self.SIDES)

    def case_sides(self, case: dict) -> set[str]:
        """The sides a case's MOVING (non-FLAT) signature triples touch. A case
        that moves nothing (all-FLAT: RCA-09, 10, 15) belongs to both."""
        out = set()
        for k, v in (case.get("signature") or {}).items():
            if isinstance(v, list):
                if v[0] != "FLAT":
                    out |= self._sides_of_tags([k])
            else:
                tag, d, _ = k.split("|")
                if d == "FLAT":
                    continue
                out |= {self.PSEUDO[tag]} if tag in self.PSEUDO else self._sides_of_tags([tag])
        return out or set(self.SIDES)

    def cases_for_side(self, cases, side: str) -> list:
        return [c for c in cases if side in self.case_sides(c)]

    def signature_for_side(self, signature: dict, side: str) -> dict:
        """The side's (tag, direction, band) triples, pseudo-tags included."""
        return {t: w for t, w in signature.items()
                if (self.PSEUDO.get(t[0]) == side) or t[0] in self.SIDE_TAGS[side]}

    def note_sides(self, note: dict) -> set[str]:
        """A raw note (its metadata tags) goes to the sides of its tags; a note
        with no tag goes to both."""
        return self._sides_of_tags(note.get("tags") or []) or set(self.SIDES)

    def notefact_sides(self, nf: dict) -> set[str]:
        """A note-fact goes to the sides of the tags among its subjects; one that
        names no tag (equipment only, or nothing) goes to both."""
        return self._sides_of_tags(s for s, _ in nf.get("pairs", [])) or set(self.SIDES)

    def other_side_line(self, facts, side: str) -> str:
        """One line about the OTHER side, written by code: its most severe
        non-INFO fact, cut at its first ':' (the same cut l1_symbolize.headline
        makes, so the line stays near the plan's ~30 tokens), or `steady`."""
        other = next(s for s in self.SIDES if s != side)
        ranked = sorted((f for f in self.facts_for_side(facts, other) if f.severity != "INFO"),
                        key=lambda f: (SEV_RANK.get(f.severity, 9), _id_key(f.id)))
        body = (f"[{ranked[0].check}/{ranked[0].severity}] {ranked[0].detail.split(':')[0]}"
                if ranked else "steady")
        return f"{other} side: {body}"

    def primary_side(self, facts, findings=()) -> str:
        """The side with the more severe evidence, non-INFO facts and open
        findings (decision 1); a tie goes to the first side (the boiler: water)."""
        best = {}
        for s in self.SIDES:
            sev = [SEV_RANK.get(f.severity, 9) for f in self.facts_for_side(facts, s)
                   if f.severity != "INFO"]
            sev += [SEV_RANK.get(f.severity, 9) for f in findings
                    if not f.resolved and s in self.finding_sides(f)]
            best[s] = min(sev, default=9)
        first, second = self.SIDES[0], self.SIDES[1]
        return second if best[second] < best[first] else first

    def side_fingerprint(self, signature: dict, findings, notefacts, side: str,
                         case_ids=()) -> tuple:
        """What a side's diagnosis depends on (plan: "its signature, its open
        findings or its note-facts"). Equal fingerprints = unchanged evidence.
        A finding counts with its severity, so an escalation is a change; only the
        side's own open findings and its own note-facts (`notefacts`: the board's
        checked note-fact dicts) count. `case_ids`: the cases the side is shown
        (phase review, commit 3: without them a re-used answer could rank a case
        list retrieval no longer returns)."""
        return (frozenset(self.signature_for_side(signature, side)),
                frozenset((f.signature_key, f.severity) for f in findings
                          if not f.resolved and side in self.finding_sides(f)),
                frozenset(nf["id"] for nf in notefacts
                          if nf.get("status") == "ok" and side in self.notefact_sides(nf)),
                frozenset(case_ids))


def for_asset(asset) -> Sides:
    """The asset's side functions (AssetPack.sides must be set)."""
    if asset.sides is None:
        raise ValueError(f"asset {asset.name!r} has no side split (multi.split needs one)")
    return Sides(asset.sides)


# ---- the boiler's, at module level (callers built without an asset) -------
def _boiler_sides() -> Sides:
    from ..assets.boiler import SIDES as _SPEC
    return Sides(_SPEC)


_B = _boiler_sides()
SIDES = _B.SIDES
SIDE_TAGS = _B.SIDE_TAGS
PSEUDO = _B.PSEUDO
PATTERN_SIDE = _B.PATTERN_SIDE
_sides_of_tags = _B._sides_of_tags
_sides_of_check = _B._sides_of_check
fact_sides = _B.fact_sides
facts_for_side = _B.facts_for_side
finding_sides = _B.finding_sides
active_sides = _B.active_sides
sides_to_run = _B.sides_to_run
case_sides = _B.case_sides
cases_for_side = _B.cases_for_side
signature_for_side = _B.signature_for_side
note_sides = _B.note_sides
notefact_sides = _B.notefact_sides
other_side_line = _B.other_side_line
primary_side = _B.primary_side
side_fingerprint = _B.side_fingerprint
