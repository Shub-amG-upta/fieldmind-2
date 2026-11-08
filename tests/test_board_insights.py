"""bench/board_insights.py counts line-1 following, [2,1] copies, deviations and 1-case
answers from a run's compact log; checked on a synthetic run folder (hand-counted)."""
import gzip
import json

import bench.board_insights as bi


def _diag(ids, lines, dropped=()):
    return {"agent": "diagnostician", "case_ids": ids, "guard_dropped": list(dropped),
            "answer": {"r": [[x, []] for x in lines]}}


def test_counts_on_a_hand_built_run(tmp_path, monkeypatch):
    monkeypatch.setattr(bi, "_accuracy", lambda runs: {})      # accuracy: bench.evaluator's own tests
    asm = [
        {"tick": 0, "hypotheses": [], "multi": {"compact": [_diag(["A", "B"], [1, 2])]}},          # follows
        {"tick": 1, "hypotheses": [], "multi": {"compact": [_diag(["A", "B"], [2, 1])]}},          # copy, right
        {"tick": 2, "hypotheses": [], "multi": {"compact": [_diag(["A", "C"], [2, 1], ["B"])]}},   # copy, wrong; B cut
        {"tick": 3, "hypotheses": [], "multi": {"compact": [_diag(["B"], [1]), _diag(["A"], [])]}},  # 1-case x2
        {"tick": 4, "hypotheses": [], "multi": {"compact": [_diag(["A", "B", "C"], [2, 3])]}},     # deviates, right, no copy
    ]
    run = {"episode_id": "e1", "n_ticks": 5, "wall_clock_s": 8.0, "assessments": asm,
           "ground_truth": {"root_cause_id": "B", "fault_onset_t": 0, "tick_period_s": 30, "family": "X",
                            "tier": "-", "asset": "cranfield"}, "multi": {}}
    with gzip.open(tmp_path / "e1_multi.run.json.gz", "wt") as f:
        json.dump(run, f)
    r = bi.insights(tmp_path, None)
    assert r["answers_with_a_choice"] == 4
    assert r["line1_follow"] == 0.25 and r["copy_21"] == 0.5             # [2,3] is not a copy
    assert r["deviations"] == 3 and r["deviate_right"] == 0.667
    assert r["one_case"] == {"[1]": 1, "[]": 1}
    assert r["true_shown"] == 0.8 and r["guard_cut_true"] == 1         # ticks 0, 1, 3, 4 show B; tick 2 cut it
