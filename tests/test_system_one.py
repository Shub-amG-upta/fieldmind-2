"""Laya as the System One model: request shuffling, the reply bridge to bev-decide's
shape, onset dating and the pick-accuracy join (reports/laya_l1.md). Runs in the
project venv: nothing here imports laya or torch."""

import json
import random

import pytest

from bench import laya_serve, system_one
from bench.system_one import (ReplyError, after_onset, bootstrap_by_episode, request_seed,
                              shuffle_request, to_bev_reply)
from bench.system_one_eval import build_rows, summarize
from fieldmind.multi.agents import bev, decider

REQ = {"state": "[RATE/WATCH] drum_level -0.70 %/min sustained 3 min",
       "questions": {
           "root_cause": {"type": "choice", "instructions": "Which root cause?",
                          "criteria": {"RCA-01": "valve seize", "RCA-11": "tube leak",
                                       "RCA-13": "wet coal", "RCA-07": "feeder trip"}},
           "note0": {"type": "noul", "instructions": "Does this note support it?"}}}


# ---------------------------------------------------------------- shuffling
def test_shuffle_moves_choice_options_and_keeps_everything_else():
    for seed in range(50):
        s = shuffle_request(REQ, seed)
        a, b = REQ["questions"]["root_cause"]["criteria"], s["questions"]["root_cause"]["criteria"]
        assert list(b) != list(a)                       # the order changed
        assert b == a                                   # same keys, same texts
        assert s["questions"]["note0"] == REQ["questions"]["note0"]
        assert s["state"] == REQ["state"]
    assert list(REQ["questions"]["root_cause"]["criteria"]) == ["RCA-01", "RCA-11", "RCA-13", "RCA-07"]


def test_the_same_request_always_gets_the_same_shuffle():
    body = json.dumps(REQ)
    s1 = shuffle_request(REQ, request_seed(body))
    s2 = shuffle_request(REQ, request_seed(body))
    assert list(s1["questions"]["root_cause"]["criteria"]) == list(s2["questions"]["root_cause"]["criteria"])


# ---------------------------------------------------------------- reply bridge
LAYA_ANSWERS = {"root_cause": {"type": "choice", "choice": "RCA-11",
                               "probabilities": {"RCA-01": 0.2, "RCA-11": 0.4, "RCA-13": 0.1, "RCA-07": 0.1},
                               "confidence": 0.1},
                "note0": {"type": "noul", "noul": 0.8}}


def _reply():
    return to_bev_reply(LAYA_ANSWERS, REQ["questions"], model="laya-test", prompt_tokens=200,
                        model_ms=12.0, truncated=False)


def test_reply_passes_the_decider_gate_check():
    ok, why, ranking = decider.check_answer(_reply()["answers"]["root_cause"],
                                            list(REQ["questions"]["root_cause"]["criteria"]))
    assert ok, why
    assert ranking[0] == "RCA-11"


def test_reply_passes_the_bev_ideas_gate_check_for_choice_and_yes_no():
    spec = {qid: {"type": q["type"], "options": list((q.get("criteria") or {}).keys())}
            for qid, q in REQ["questions"].items()}
    ok, why, out = bev.check_answers(_reply()["answers"], spec)
    assert ok, why
    assert out["note0"]["p"] == pytest.approx(0.8)          # P(yes) kept, not 1 - P(yes)
    assert out["root_cause"]["ranking"][0] == "RCA-11"
    assert sum(out["root_cause"]["p"].values()) == pytest.approx(1.0)   # renormalised over the offered


def test_reply_choice_is_the_most_probable_option_not_layas_label():
    ans = json.loads(json.dumps(LAYA_ANSWERS))
    ans["root_cause"]["choice"] = "RCA-01"                     # a label that disagrees with the numbers
    assert to_bev_reply(ans, REQ["questions"], model="x", prompt_tokens=None, model_ms=0,
                        truncated=False)["answers"]["root_cause"]["choice"] == "RCA-11"


def test_a_missing_option_is_an_error_not_a_silent_answer():
    ans = json.loads(json.dumps(LAYA_ANSWERS))
    del ans["root_cause"]["probabilities"]["RCA-07"]
    with pytest.raises(ReplyError):
        to_bev_reply(ans, REQ["questions"], model="x", prompt_tokens=None, model_ms=0, truncated=False)


class _FakeAgent:
    """Stands in for laya's Agent: prefers the option LISTED FIRST, so the order it
    was given is visible in its answer."""
    def __init__(self):
        self.seen = []

    def predict(self, state, questions):
        self.seen.append({q: list((v.get("criteria") or {})) for q, v in questions.items()})
        out = {}
        for qid, q in questions.items():
            if q["type"] == "noul":
                out[qid] = {"type": "noul", "noul": 0.3}
            else:
                keys = list(q["criteria"])
                out[qid] = {"type": "choice", "choice": keys[0],
                            "probabilities": {k: (0.9 if i == 0 else 0.1 / (len(keys) - 1))
                                              for i, k in enumerate(keys)}}
        return {"answers": out, "usage": {"input_tokens": 100, "truncated": False}}


def _fake_laya(monkeypatch):
    m = laya_serve.Laya.__new__(laya_serve.Laya)
    m.agent, m.name, m.layout = _FakeAgent(), "fake", "sequential"
    monkeypatch.setattr(laya_serve, "options_cut", lambda tok, q: 0)
    m.agent.tok = None
    return m


def test_server_shuffle_reaches_the_model_and_the_reply_names_original_keys(monkeypatch):
    m = _fake_laya(monkeypatch)
    body = json.dumps(REQ)
    plain = m.answer(body, None)
    shuf = m.answer(body, system_one.SEED)
    asked = m.agent.seen[1]["root_cause"]
    assert asked != list(REQ["questions"]["root_cause"]["criteria"])     # the model saw the other order
    assert shuf["asked_order"]["root_cause"] == asked
    # a first-listed-picking model follows the shuffle: its pick moves to the new first option
    assert plain["answers"]["root_cause"]["choice"] == "RCA-01"
    assert shuf["answers"]["root_cause"]["choice"] == asked[0]
    assert set(shuf["answers"]["root_cause"]["probabilities"]) == set(REQ["questions"]["root_cause"]["criteria"])


# ---------------------------------------------------------------- onset and accuracy
def test_onset_dates_tick_k_at_k_plus_one_ticks():
    assert after_onset(19, 30.0, 600.0)          # tick 19 publishes at 600 s
    assert not after_onset(18, 30.0, 600.0)      # 570 s: before onset
    assert not after_onset(100, 30.0, None)      # a normal episode has no onset


def _req(ep, tick, offered, group, belief=None, retr=(), bev_choice=None, after=True, held=False):
    return {"episode": ep, "tick": tick, "offered": offered, "true_group": group, "heldout": held,
            "belief_top": belief or offered[0], "retriever_tops": list(retr), "after_onset": after,
            "answer_backend": "bev" if bev_choice else "mock", "answer_choice": bev_choice}


def _ans(ep, tick, choice, order=None):
    rep = {"answers": {"root_cause": {"type": "choice", "choice": choice, "probabilities": {}}},
           "truncated": False, "options_cut": 1}
    if order:
        rep["asked_order"] = {"root_cause": order}
    return {"episode": ep, "tick": tick, "reply": rep}


def test_pick_accuracy_join_on_a_two_episode_toy_set():
    reqs = [_req("e1", 10, ["A", "B", "C"], ["B"], retr=["A"], bev_choice="B"),
            _req("e1", 11, ["A", "B"], ["B"], retr=["B"]),
            _req("e1", 2, ["A", "B"], ["B"], after=False),            # before onset: not scored
            _req("e2", 10, ["C", "D"], ["X"], held=True)]              # held out: never offered
    normal = [_ans("e1", 10, "B"), _ans("e1", 11, "A"), _ans("e1", 2, "B"), _ans("e2", 10, "C")]
    shuffled = [_ans("e1", 10, "C", ["C", "A", "B"]), _ans("e1", 11, "A", ["B", "A"]),
                _ans("e2", 10, "D", ["D", "C"])]
    rows = build_rows(reqs, normal, shuffled)
    assert [(r["episode"], r["tick"]) for r in rows] == [("e1", 10), ("e1", 11), ("e2", 10)]
    s = summarize(rows)
    assert s["laya"]["p"] == pytest.approx(1 / 3)            # B right, A wrong, C wrong
    assert s["retriever"]["p"] == pytest.approx(1 / 2)       # A wrong, B right; e2 has none
    assert s["laya_where_retriever"]["p"] == pytest.approx(1 / 2)
    assert s["belief"]["p"] == pytest.approx(0.0)            # A, A, C
    assert s["bev"]["p"] == pytest.approx(1.0) and s["bev"]["n"] == 1
    assert s["invariant"] == pytest.approx(1 / 3)            # only e1 t11 kept its pick
    assert s["laya_first_shuf"] == pytest.approx(2 / 3)      # C first, B not first..., D first
    assert s["chance"] == pytest.approx((1 / 3 + 1 / 2 + 0) / 3)


def test_episode_bootstrap_is_exact_on_constant_data_and_repeatable():
    rows = [{"episode": f"e{i % 4}", "x": True} for i in range(40)]
    assert bootstrap_by_episode(rows, "x") == (1.0, 1.0, 1.0)
    rng = random.Random(1)
    rows = [{"episode": f"e{i % 5}", "x": rng.random() < 0.5} for i in range(100)]
    assert bootstrap_by_episode(rows, "x") == bootstrap_by_episode(rows, "x")
    p, lo, hi = bootstrap_by_episode(rows, "x")
    assert lo <= p <= hi


# ---------------------------------------------------------------- board lane (bench.board)
def test_laya_lane_command_keeps_the_lane_rules_and_fits_a_request_in_one_batch():
    from bench import board
    cmd = board.laya_command("laya-7b928d8-Q8_0.gguf", "npu")
    for part in ("--device HTP0 -ngl 99", "-c 4096", "-np 1", "-ub 4096", "-b 4096",
                 "-fit off", "--cache-ram 0", "-lv 4", f"--port {board.LAYA_PORT}",
                 "LD_LIBRARY_PATH=", "ADSP_LIBRARY_PATH="):
        assert part in cmd, part
    assert board.LAYA_PORT not in (board.BEV_PORT, *board.LANE_PORT.values())
    assert "--device none -ngl 0" in board.laya_command("laya-7b928d8-Q8_0.gguf", "cpu")


def test_laya_lane_refuses_an_unrecorded_file(monkeypatch):
    from bench import board
    monkeypatch.setattr(board, "board_sha256", lambda f, s="": "0" * 64)
    with pytest.raises(board.ModelNotAllowed):
        board.check_laya("laya-other.gguf")
    with pytest.raises(board.ModelNotAllowed):                      # recorded name, wrong bytes
        board.check_laya("laya-7b928d8-Q8_0.gguf")
