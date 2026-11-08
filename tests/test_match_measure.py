"""Accuracy-fixes step 4 (REVERTED on dev, code kept, default jaccard): the cosine match
measure. Hand-computed: tick signature {x, y, z, u, v} (all 1.0); case SMALL {x, y};
case BIG {x, y, z, p, q, r, s}.
  Jaccard: SMALL 2/5 = 0.400, BIG 3/9 = 0.333 -> SMALL first
  cosine : SMALL 2/sqrt(2*5) = 0.632, BIG 3/sqrt(7*5) = 0.507 -> SMALL first, larger margin
and a FLAT (0.35) triple: case {x:1, f:0.35}, signature {x:1, f:0.35}: cosine exactly 1."""
import json

import pytest

from fieldmind.kb.stores import CaseLibrary


def _lib(tmp_path, cases):
    p = tmp_path / "lib.json"
    p.write_text(json.dumps({"cases": cases}))
    return CaseLibrary(p)


def _case(cid, trip):
    return {"case_id": cid, "root_cause": cid, "provenance": "curated_case", "weight": 1.0,
            "signature": {f"{t}|UP|SLOW": w for t, w in trip.items()}}


SIG = {(t, "UP", "SLOW"): 1.0 for t in "xyzuv"}


def _scores(lib, measure):
    return {c["case_id"]: c["raw_score"] for c in lib.match(SIG, k=5, measure=measure)}


def test_hand_computed_jaccard_and_cosine(tmp_path):
    lib = _lib(tmp_path, [_case("SMALL", {"x": 1, "y": 1}),
                          _case("BIG", {t: 1 for t in "xyzpqrs"})])
    assert _scores(lib, "jaccard") == {"SMALL": 0.4, "BIG": 0.333}
    assert _scores(lib, "cosine") == {"SMALL": 0.632, "BIG": 0.507}


def test_cosine_of_a_case_equal_to_the_signature_is_one_with_flat_weights(tmp_path):
    lib = _lib(tmp_path, [{"case_id": "A", "root_cause": "A", "provenance": "curated_case",
                           "signature": {"x|UP|SLOW": 1.0, "f|FLAT|-": 0.35}}])
    sig = {("x", "UP", "SLOW"): 1.0, ("f", "FLAT", "-"): 0.35}
    assert lib.match(sig, measure="cosine")[0]["raw_score"] == 1.0


def test_unknown_measure_is_refused(tmp_path):
    with pytest.raises(ValueError):
        _lib(tmp_path, [_case("A", {"x": 1})]).match(SIG, measure="dice")
