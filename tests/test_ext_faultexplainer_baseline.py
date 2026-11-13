"""bench.ext_faultexplainer code-only baseline: outcomes on hand-built requests.
No real request's ranking is asserted here (reports/ext_faultexplainer_baseline_prereg.md: the real
requests are scored only after the rules are agreed)."""

from __future__ import annotations

import itertools
import json

import pytest

from bench import ext_faultexplainer as X
from bench.echo_test import orderings

# a 15-line list in FaultExplainer's layout; causes 4, 9 and 12 carry distinctive words
CAUSES = {k: f"spare item number {k} & Step" for k in range(1, 16)}
CAUSES.update({4: "Reactor Cooling Water Inlet Temperature & Step", 9: "Stripper Steam Valve & Sticking",
               12: "Condenser Cooling Water Inlet Temperature & Random Variation"})


def _prompt(causes=CAUSES):
    body = "\n".join(f"{k}. IDV({k}) {causes[k]}" for k in range(1, 16))
    return f"System text.\n**Available Root Causes**:\n{body}\n\nThe top feature changes are\nFeature: x\n"


def _doc(items):
    """items: [(fault, top_features)]"""
    return {"requests": [{"id": n, "fault": f, "aliases": list(X.ALIASES.get(f, ())), "top_features": feats,
                          "prompts": {form: _prompt() for form in X.FORMS}} for n, (f, feats) in enumerate(items)]}


def test_content_words_are_lower_case_letters_of_three_or_more_outside_the_stop_list():
    assert X.content_words("A/C Feed Ratio, B Composition (Stream 4) & the Step") == \
        {"feed", "ratio", "composition", "stream", "step"}
    assert X.content_words("Temp of the D") == {"temp"}          # 'of' too short, 'the' stopped, 'D' too short
    assert "temp" not in X.content_words("Temperature")           # whole words only: no stemming


def test_the_cause_sharing_a_word_with_the_top_feature_is_ranked_first():
    ranked, scores = X.overlap_rank(["Stripper Level", "zzz", "yyy", "xxx", "www", "vvv"], _prompt())
    assert ranked[0] == 9 and scores[9] == 6
    assert all(v == 0 for k, v in scores.items() if k != 9)


def test_the_rank_weights_decide_between_two_causes_matched_by_different_features():
    hi_first = X.overlap_rank(["Condenser Duty", "Stripper Level", "a", "b", "c", "d"], _prompt())
    lo_first = X.overlap_rank(["Stripper Level", "Condenser Duty", "a", "b", "c", "d"], _prompt())
    assert hi_first[0][:2] == [12, 9] and hi_first[1][12] == 6 and hi_first[1][9] == 5
    assert lo_first[0][:2] == [9, 12] and lo_first[1][9] == 6 and lo_first[1][12] == 5
    # weights add up: a cause matched at ranks 4 and 5 (3 + 2) beats one matched once at rank 3 (4)
    r, s = X.overlap_rank(["a", "b", "Stripper Level", "Cooling Loop", "Inlet Flow", "c"], _prompt())
    assert s[9] == 4 and s[4] == 3 + 2 and r[0] == 4


def test_ties_go_to_the_lower_idv_and_the_top_three_is_always_three():
    ranked, scores = X.overlap_rank(["Cooling Water Flow", "a", "b", "c", "d", "e"], _prompt())
    assert scores[4] == scores[12] == 6 and ranked[:2] == [4, 12]        # tie: 4 before 12
    assert ranked[2] == 1                                                # then the zero-score causes, lowest first
    none = X.overlap_rank(["qqq", "rrr", "sss", "ttt", "uuu", "vvv"], _prompt())[0]
    assert none[:3] == [1, 2, 3]


def test_a_shortened_word_does_not_match_its_long_form():
    # "Temp" is inside "Temperature" (causes 4 and 12) but is not the same word: nothing scores
    ranked, scores = X.overlap_rank(["Sep Temp", "a", "b", "c", "d", "e"], _prompt())
    assert set(scores.values()) == {0} and ranked[:3] == [1, 2, 3]


def test_more_features_than_weights_is_refused():
    with pytest.raises(ValueError):
        X.overlap_rank(["a"] * 7, _prompt())


def test_baseline_rows_are_read_by_score_with_the_expected_counts(tmp_path):
    # fault 12 (aliases 5, 15): matched first. fault 9 (alias 3): matched first. fault 6: nothing matches -> 1, 2, 3.
    doc = _doc([(12, ["Condenser Duty", "a", "b", "c", "d", "e"]),
                (9, ["Stripper Level", "a", "b", "c", "d", "e"]),
                (6, ["qqq", "rrr", "sss", "ttt", "uuu", "vvv"]),
                (4, ["a", "Stripper Level", "b", "c", "d", "Reactor Level"])])   # 9 scores 5, 4 scores 1: top-3 only
    out = tmp_path / "code.jsonl"
    msg = X.baseline(doc, str(out))
    rows = [json.loads(x) for x in out.read_text().splitlines()]
    assert msg.startswith("48 new rows") and len(rows) == 4 * 3 * 4               # requests x forms x orderings
    assert X.baseline(doc, str(out)).startswith("0 new rows")                      # resumes, writes nothing twice
    s = X.score(doc, rows)
    assert set(s) == {"code_overlap / app", "code_overlap / eval", "code_overlap / eval_noleak"}
    for form in s.values():
        for o in form["orderings"].values():
            assert (o["n"], o["parsed"], o["top1_right"], o["top3_right"]) == (4, 4, 2, 3)
    by = {(r["id"], r["form"], r["ordering"]): r for r in rows}
    assert by[(3, "app", "original")]["picks"] == [9, 4, 1] and by[(3, "app", "original")]["n_scoring"] == 2
    assert by[(2, "app", "original")]["picks"] == [1, 2, 3] and by[(2, "app", "original")]["n_scoring"] == 0


def test_the_code_picks_do_not_move_when_the_list_is_shuffled(tmp_path):
    doc = _doc([(12, ["Condenser Duty", "Stripper Level", "a", "b", "c", "d"]),
                (6, ["qqq", "rrr", "sss", "ttt", "uuu", "vvv"])])
    out = tmp_path / "code.jsonl"
    X.baseline(doc, str(out), forms=("app",))
    rows = [json.loads(x) for x in out.read_text().splitlines()]
    for rid in (0, 1):
        got = {r["ordering"]: r["picks"] for r in rows if r["id"] == rid}
        assert set(got) == set(orderings(15, rid, X.SEED)) and len({tuple(v) for v in got.values()}) == 1
    # the list really was reordered: line 1 is not the same cause in every ordering
    assert len({r["lines"]["1"] for r in rows if r["id"] == 0}) > 1
    # so against `original` every shuffled first pick followed the content, never the position
    f = X.score(doc, rows)["code_overlap / app"]["follow"]
    assert all(c["position"] == 0 and c["neither"] == 0 and c["content"] + c["uninformative"] == c["n"] == 2
               for c in f.values())


def test_references_uniform_matches_a_count_over_every_triple():
    doc = _doc([(12, ["a"] * 6), (6, ["a"] * 6), (11, ["a"] * 6), (13, ["a"] * 6)])
    ref = X.references(doc, [])
    triples = list(itertools.combinations(range(1, 16), 3))
    by_count = sum(sum(bool(set(t) & {r["fault"], *r["aliases"]}) for t in triples) / len(triples)
                   for r in doc["requests"])
    assert ref["uniform"]["top3_right_expected"] == pytest.approx(by_count, abs=5e-4)
    assert ref["uniform"]["top1_right_expected"] == pytest.approx((3 + 1 + 3 + 1) / 15, abs=5e-4)
    assert ref["n"] == 4


def test_references_first_three_lines_and_the_arms_most_frequent_answer(tmp_path):
    doc = _doc([(1, ["a"] * 6), (2, ["a"] * 6), (3, ["a"] * 6), (14, ["a"] * 6)])
    ref = X.references(doc, [])
    # original order: lines 1-3 are IDV 1, 2, 3. Line 1 is right for fault 1 only; the top three for faults 1, 2, 3.
    assert ref["first_three_lines"]["original"] == {"top1_right": 1, "top3_right": 3}
    # an arm that always answers 14, 4, 11: right for fault 14 only (4 and 11 are its aliases, not the others')
    rows = [{"label": "const", "form": "app", "ordering": "original", "id": r["id"], "status": "ok",
             "picks": [14, 4, 11]} for r in doc["requests"]]
    rows.append({"label": "const", "form": "app", "ordering": "original", "id": 0, "status": "error"})
    mf = X.references(doc, rows)["most_frequent"]["const / app"]["original"]
    assert mf == {"answer": [4, 11, 14], "first": [14], "n": 4, "top1_right": 1, "top3_right": 1}
