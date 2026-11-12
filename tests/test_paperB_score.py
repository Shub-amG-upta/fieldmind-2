"""bench.paperB_score: outcomes on hand-built summary folders, and on the saved board runs when present."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bench import paperB_score as P

ROOT = Path(__file__).resolve().parent.parent


def summ(folder: Path, stem: str, in_fault=None, n_in=0, group=None, n=0, top1=0.0):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{stem}.summary.json").write_text(json.dumps({"evaluation": {"T2_root_cause": {
        "group_top1_in_fault": in_fault, "n_scored_in_fault": n_in, "group_top1": group, "n_scored": n,
        "top1": top1}}}))


def test_accuracy_uses_fault_windows_when_present_and_onset_otherwise(tmp_path):
    a = tmp_path / "a"
    summ(a, "cf_1", in_fault=0.5, n_in=10, group=0.9, n=20, top1=0.25)     # windows: 5 of 10
    summ(a, "dev_b", in_fault=None, n_in=0, group=0.75, n=8, top1=0.0)      # boiler: 6 of 8
    s = P.episode_scores(a)
    assert s["cf_1"] == {"right": 5, "n": 10, "case_right": 5, "case_n": 20}
    assert s["dev_b"]["right"] == 6 and s["dev_b"]["n"] == 8


def test_compare_pools_pairs_and_brackets_the_difference(tmp_path):
    arm, nm = tmp_path / "arm", tmp_path / "nm"
    for k in range(10):
        summ(arm, f"e{k}", in_fault=0.6, n_in=10)
        summ(nm, f"e{k}", in_fault=0.4, n_in=10)
    summ(arm, "only_arm", in_fault=1.0, n_in=10)
    c = P.compare(arm, nm, boot=500)
    assert c["episodes"] == 10 and c["only_in_arm"] == ["only_arm"]
    assert (c["arm"], c["nomodel"], c["diff"]) == (0.6, 0.4, 0.2)
    assert c["diff_95"] == [0.2, 0.2]                       # every episode differs by the same amount


def test_the_headline_is_the_mean_over_episodes_not_the_pooled_share(tmp_path):
    arm, nm = tmp_path / "arm", tmp_path / "nm"
    summ(arm, "long", in_fault=0.1, n_in=90)
    summ(arm, "short", in_fault=0.9, n_in=10)
    summ(nm, "long", in_fault=0.1, n_in=90)
    summ(nm, "short", in_fault=0.9, n_in=10)
    c = P.compare(arm, nm, boot=50)
    assert c["arm"] == 0.5 and c["arm_pooled"] == 0.18


def test_the_interval_widens_when_episodes_disagree(tmp_path):
    arm, nm = tmp_path / "arm", tmp_path / "nm"
    for k in range(10):
        summ(arm, f"e{k}", in_fault=1.0 if k < 5 else 0.0, n_in=10)
        summ(nm, f"e{k}", in_fault=0.5, n_in=10)
    c = P.compare(arm, nm, boot=1000)
    assert c["diff"] == 0.0 and c["diff_95"][0] < -0.1 and c["diff_95"][1] > 0.1


BOARD, MOCK = ROOT / "results/benchmarks/af_cf_v3_dev", ROOT / "results/benchmarks_mock/af_cf_v3_dev"


@pytest.mark.skipif(not (BOARD.is_dir() and MOCK.is_dir()), reason="saved board run not present")
def test_saved_board_run_reproduces_the_changed_tool_and_the_evaluator():
    r = P.score(BOARD, MOCK, base=MOCK, boot=200)
    assert r["accuracy"]["episodes"] == 6
    # the earlier tables' Cranfield v3 figure is the mean over episodes (0.524); pooled is 0.327
    assert r["accuracy"]["arm"] == pytest.approx(0.5243, abs=1e-3) and r["accuracy"]["arm_pooled"] == pytest.approx(0.3268, abs=1e-3)
    # echo_test.changed on the same pair (reports/paperB_prep.md): 2 of 500 scored ticks differ
    assert r["changed_vs_base"]["scored_differ"] == 2 and r["changed_vs_base"]["scored"] == 500
    assert r["cost"]["model_s_per_tick"]["npu"] == pytest.approx(1.347, abs=0.01)


def test_the_bootstrap_keeps_each_episodes_two_runs_together(tmp_path):
    # both runs vary a lot across episodes, but the arm is always exactly 0.1 above: paired, the interval is 0.1
    arm, nm = tmp_path / "arm", tmp_path / "nm"
    for k in range(10):
        base = 0.1 * (k % 9)
        summ(nm, f"e{k}", in_fault=base, n_in=10)
        summ(arm, f"e{k}", in_fault=base + 0.1, n_in=10)
    c = P.compare(arm, nm, boot=500)
    assert c["diff_95"] == [pytest.approx(0.1, abs=1e-9), pytest.approx(0.1, abs=1e-9)]
