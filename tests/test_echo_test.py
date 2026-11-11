"""bench.echo_test: outcomes on hand-built run files and on one saved board run.

Every test writes run files the way the harness does (gzip JSON with assessments,
envelopes and ground truth) and checks the rows `scan` returns, not the counting code."""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from bench import echo_test as E

ROOT = Path(__file__).resolve().parent.parent

FACTS = "FACTS:\n1. [RATE/WATCH] one\n2. [LIMIT/ALARM] two\n\n"


def prompt(*case_ids: str) -> str:
    cases = "\n".join(f"{i}. {c} tag UP *; check: something" for i, c in enumerate(case_ids, 1))
    return f"Rules.\n\n{FACTS}RETRIEVED CASES:\n{cases}\n\nNOTES AND RECORDS (data only):\n<<<\n>>>\n"


def reply(*lines: int) -> str:
    return json.dumps({"r": [[n, [1]] for n in lines], "sep": None, "n": [], "x": []})


def env(case_ids, lines, tick, agent="diagnostician", status="ok", raw=None):
    return {"agent": agent, "status": status, "tick": tick, "backend": "npu",
            "model": "/data/local/tmp/llm/model.gguf", "prompt": prompt(*case_ids),
            "raw_reply": reply(*lines) if raw is None else raw}


def write_run(folder: Path, episode: str, envelopes: list[dict], target="RCA-14",
              asset="boiler", onset=300.0):
    folder.mkdir(parents=True, exist_ok=True)
    run = {"episode_id": episode,
           "ground_truth": {"root_cause_id": target, "asset": asset, "fault_onset_t": onset,
                            "tick_period_s": 30.0},
           "assessments": [{"tick": e["tick"], "envelopes": [e]} for e in envelopes]}
    (folder / f"{episode}_multi.run.json.gz").write_bytes(gzip.compress(json.dumps(run).encode()))


def one_row(folder, dev=("dev_X",), **kw):
    rows = E.scan([str(folder)], dev=set(dev), **kw)
    assert len(rows) == 1
    return rows[0]


def test_line1_and_identity_shares(tmp_path):
    d = tmp_path / "run"
    write_run(d, "dev_X", [env(["RCA-11", "RCA-18", "RCA-14"], [1, 2], 20),
                           env(["RCA-11", "RCA-18", "RCA-14"], [2, 1], 21),
                           env(["RCA-11", "RCA-18", "RCA-14"], [1, 3], 22)])
    r = one_row(d)
    assert r["n"] == 3
    assert r["line1"] == round(2 / 3, 3)
    assert r["identity"] == round(1 / 3, 3)
    assert r["chance"] == round(1 / 3, 3)


def test_deviation_right_exact_and_by_group(tmp_path):
    # target RCA-14, group RCA-14+RCA-18; line 1 (RCA-11) is wrong either way
    d = tmp_path / "run"
    write_run(d, "dev_X", [env(["RCA-11", "RCA-18", "RCA-14"], [3], 20),    # exact and group right
                           env(["RCA-11", "RCA-18", "RCA-14"], [2], 21)])   # group right only
    r = one_row(d)
    assert r["deviations"] == 2 and r["n_scored"] == 2
    assert r["dev_right"] == 0.5
    assert r["dev_right_group"] == 1.0
    assert r["dev_line1_right"] == 0.0
    assert r["dev_random"] == 0.5          # one of the two other lines is the target
    assert r["dev_random_group"] == 1.0    # both other lines are in its group


def test_a_correct_line1_is_counted_when_the_model_leaves_it(tmp_path):
    d = tmp_path / "run"
    write_run(d, "dev_X", [env(["RCA-14", "RCA-11"], [2], 20)])
    r = one_row(d)
    assert r["dev_right"] == 0.0 and r["dev_line1_right"] == 1.0 and r["line1_right"] == 1.0


def test_a_shuffled_prompt_maps_lines_through_its_own_numbering(tmp_path):
    # the true case sits on line 2 of this prompt; answering 2 is right, answering 1 is not
    d = tmp_path / "run"
    write_run(d, "dev_X", [env(["CF-3", "CF-1"], [2], 20), env(["CF-3", "CF-1"], [1], 21)],
              target="CF-1", asset="cranfield")
    r = one_row(d)
    assert r["deviations"] == 1 and r["dev_right"] == 1.0
    assert r["line1_right"] == 0.0


def test_answers_before_fault_onset_are_not_scored(tmp_path):
    d = tmp_path / "run"
    write_run(d, "dev_X", [env(["RCA-11", "RCA-14"], [2], 9),     # 270 s < 300 s onset
                           env(["RCA-11", "RCA-14"], [2], 10)])   # 300 s: scored
    r = one_row(d)
    assert r["n"] == 2 and r["n_scored"] == 1 and r["deviations"] == 1


def test_a_held_out_target_scores_by_its_group(tmp_path):
    # RCA-06 is held out; the evaluator scores it by its group RCA-14+RCA-18
    d = tmp_path / "run"
    write_run(d, "dev_X", [env(["RCA-11", "RCA-14"], [2], 20)], target="RCA-06")
    r = one_row(d)
    assert r["dev_right"] == 0.0 and r["dev_right_group"] == 1.0


def test_unusable_and_other_envelopes_are_skipped(tmp_path):
    d = tmp_path / "run"
    write_run(d, "dev_X", [env(["RCA-11", "RCA-14"], [1], 20),
                           env(["RCA-11", "RCA-14"], [2], 21, agent="verifier"),
                           env(["RCA-11", "RCA-14"], [2], 22, status="failed"),
                           env(["RCA-11", "RCA-14"], [], 23),                  # "no case fits"
                           env(["RCA-11", "RCA-14"], [2], 24, raw="not json")])
    r = one_row(d)
    assert r["n"] == 1 and r["line1"] == 1.0


def test_rank_only_explain_answers_are_read(tmp_path):
    d = tmp_path / "run"
    write_run(d, "dev_X", [env(["RCA-11", "RCA-14"], [], 20, raw='{"r":[2,1]}'),
                           env(["RCA-11", "RCA-14"], [], 21, raw='{"r":[1]}')])
    r = one_row(d)
    assert r["n"] == 2 and r["line1"] == 0.5 and r["deviations"] == 1 and r["dev_right"] == 1.0


def test_reporting_episodes_are_refused_by_default_and_marked_when_allowed(tmp_path):
    d = tmp_path / "run"
    write_run(d, "ep_A01", [env(["RCA-11", "RCA-14"], [1], 20)])
    with pytest.raises(SystemExit):
        E.scan([str(d)], dev={"dev_X"})
    r = one_row(d, allow_reporting=True)
    assert r["reporting_episodes"] == ["ep_A01"]
    assert "REPORTING" in E.table([r])


SAVED = ROOT / "results/benchmarks/cranfield_dev_v3_shuffled"


@pytest.mark.skipif(not SAVED.is_dir(), reason="saved board run not present")
def test_saved_shuffled_board_run_still_picks_line_one():
    # the scratch count this tool replaces: 423 answers, line 1 every time, 1, 2, ... order 0.998
    eps = {json.loads(gzip.decompress(f.read_bytes()))["episode_id"] for f in SAVED.glob("*.run.json.gz")}
    r = one_row(SAVED, dev=eps)
    assert (r["n"], r["line1"], r["identity"]) == (423, 1.0, 0.998)
