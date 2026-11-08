"""Accuracy-fixes step 1: group top-1 scored only on ticks published inside a fault
window, dated (k+1) * tick as in T7. Hand-counted on a 30 s tick, window [100, 200) s:
(k+1)*30 in [100, 200) -> k = 3, 4, 5 (published at 120, 150, 180 s)."""
from bench.evaluator import _in_fault, t2_root_cause

GMAP = {"A": "gA", "A2": "gA", "B": "gB"}


def _run(refs, wins=((100, 200),), belief=None):
    asm = [{"tick": k, "hypotheses": [{"case_ref": r}] if r else [],
            "belief_ranking": [{"case_ref": (belief or refs)[k], "log_odds": 0.0}]}
           for k, r in enumerate(refs)]
    return {"ground_truth": {"fault_windows": [list(w) for w in wins]}, "assessments": asm}


def test_only_ticks_published_inside_the_window_are_scored():
    #        k: 0    1    2    3    4     5    6    7
    refs = ["A", "A", "A", "B", "A2", "A", "A", "A"]   # right group everywhere but k=3
    r = _in_fault(_run(refs), GMAP, "gA", 30.0)
    assert r["n_scored_in_fault"] == 3
    assert r["group_top1_in_fault"] == 0.667          # k=4,5 right, k=3 wrong


def test_belief_ranking_is_scored_separately():
    refs = ["A"] * 8
    belief = ["B"] * 8
    r = _in_fault(_run(refs, belief=belief), GMAP, "gA", 30.0)
    assert r["group_top1_in_fault"] == 1.0 and r["belief_group_in_fault"] == 0.0


def test_two_windows_and_an_empty_tick():
    refs = ["A", "B", "", "A", "B", "A", "A", "A"]
    # windows [0, 70) -> k=0,1 ; [150, 181) -> k=4,5 ; k=2 inside nothing anyway
    r = _in_fault(_run(refs, wins=((0, 70), (150, 181))), GMAP, "gA", 30.0)
    assert r["n_scored_in_fault"] == 4 and r["group_top1_in_fault"] == 0.5


def test_no_windows_gives_none_and_t2_carries_the_keys():
    run = _run(["A"] * 4)
    run["ground_truth"] = {"root_cause_id": "RCA-14", "fault_onset_t": 0}
    r = t2_root_cause(run)
    assert r["group_top1_in_fault"] is None and r["n_scored_in_fault"] == 0
