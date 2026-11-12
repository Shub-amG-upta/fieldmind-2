"""bench.echo_4bit: the 4-bit against 8-bit confirmation. Outcomes from arms whose behaviour is known
(a reader, a blind arm, a passage follower, a memoriser), on the real request files where they exist."""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

import pytest

from bench import echo_4bit as F
from bench import echo_causes as C
from bench import echo_test as E
from fieldmind.runtime.llm_backend import LLMReply

ROOT = Path(__file__).resolve().parent.parent
REQ = json.loads((ROOT / "reports/data/echo_requests.json").read_text())
MMLU = json.loads((ROOT / "reports/data/nd_public_requests.json").read_text())


def line1_right(req):
    return C._right(req, E.case_lines(req["prompt"]).get(1))[1]


def prior_row(label, req, p1, status="ok", pick=1, lines=None):
    """A `run prior` row whose probability on line 1 is p1, the rest shared by the other
    lines shown (`lines` = how many lines carry a reading; default all of them)."""
    k = lines or len(E.case_lines(req["prompt"]))
    lp = {"1": math.log(p1), **{str(j): math.log((1 - p1) / (k - 1)) for j in range(2, k + 1)}}
    return {"label": label, "id": req["id"], "ordering": "original", "status": status,
            "reply": json.dumps({"r": [[pick, [1]]], "sep": None, "n": [], "x": []}, separators=(",", ":")),
            "first_line_logprobs": lp}


# ------------------------------------------------------------------ AUC
def test_auc_known_values_ties_and_empty_classes():
    assert F.auc([3, 4], [1, 2]) == 1.0
    assert F.auc([1, 2], [3, 4]) == 0.0
    assert F.auc([1, 1], [1, 1]) == 0.5
    assert F.auc([2, 1], [1]) == 0.75            # one win, one tie
    assert F.auc([], [1]) is None and F.auc([1], []) is None


def test_auc_equals_a_direct_count_of_pairs():
    rng = random.Random(7)
    for _ in range(20):
        pos = [rng.choice([0.1, 0.2, 0.3, 0.5, 0.9]) for _ in range(rng.randint(1, 12))]
        neg = [rng.choice([0.1, 0.2, 0.3, 0.5, 0.9]) for _ in range(rng.randint(1, 12))]
        direct = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in pos for n in neg) / (len(pos) * len(neg))
        assert F.auc(pos, neg) == pytest.approx(direct, abs=1e-12)


# ------------------------------------------------------------------ signal
def scored(n=120):
    return [r for r in REQ["requests"] if line1_right(r) is not None][:n]


def test_a_reader_scores_1_a_blind_arm_half_and_the_pair_is_their_difference():
    reqs = scored()
    assert {line1_right(r) for r in reqs} == {0.0, 1.0}
    rows = ([prior_row("reader", r, 0.9 if line1_right(r) else 0.4) for r in reqs]
            + [prior_row("blind", r, 0.7, pick=1 if r["id"] % 4 else 2) for r in reqs]
            + [prior_row("reader_again", r, 0.9 if line1_right(r) else 0.4) for r in reqs])
    recs, skipped = F.signal_rows(REQ, rows)
    assert skipped == {} and len(recs) == 3 * len(reqs)
    out = F.summarise_auc(recs, [("blind", "reader"), ("reader", "blind"), ("reader", "reader_again")], boot=200)
    assert out["arms"]["reader"]["auc"] == 1.0 and out["arms"]["blind"]["auc"] == 0.5
    assert out["arms"]["reader"]["positive"] == sum(line1_right(r) == 1.0 for r in reqs)
    assert out["arms"]["reader"]["line1_share"] == 1.0
    assert out["arms"]["blind"]["line1_share"] == pytest.approx(sum(r["id"] % 4 != 0 for r in reqs) / len(reqs), abs=1e-4)
    up, down, same = (out["pairs"][k] for k in ("blind:reader", "reader:blind", "reader:reader_again"))
    assert up["diff"] == 0.5 and up["diff_ci95"] == [0.5, 0.5] and up["share_of_resamples_at_or_below_0"] == 0.0
    assert down["diff"] == -0.5 and down["share_of_resamples_at_or_below_0"] == 1.0
    assert same["diff"] == 0.0 and same["diff_ci95"] == [0.0, 0.0]


def test_the_probability_is_read_over_the_lines_shown():
    req = next(r for r in scored() if len(E.case_lines(r["prompt"])) == 4)
    full, _ = F.signal_rows(REQ, [prior_row("a", req, 0.8)])
    assert full[0]["score"] == pytest.approx(0.8, rel=1e-9)          # every line read: exactly what was written
    recs, _ = F.signal_rows(REQ, [prior_row("a", req, 0.8, lines=2)])
    k = 4
    # lines 3..k have no reading and take the floor (lowest reading minus 1 nat), so p1 is a little under 0.8
    floor = math.exp(math.log(0.2) - 1.0)
    assert recs[0]["score"] == pytest.approx(0.8 / (1.0 + (k - 2) * floor), rel=1e-9)
    assert recs[0]["unit"] == req["episode"] and recs[0]["picks_line1"] == 1.0


def test_unscored_failed_and_unreadable_rows_are_left_out_and_counted():
    unscored = next(r for r in REQ["requests"] if line1_right(r) is None)
    a, b, c = scored(3)
    rows = [prior_row("x", unscored, 0.9), prior_row("x", a, 0.9, status="timeout"),
            {**prior_row("x", b, 0.9), "first_line_logprobs": {}}, prior_row("x", c, 0.9),
            {**prior_row("x", c, 0.1), "ordering": "content_free"}]
    recs, skipped = F.signal_rows(REQ, rows)
    assert [r["id"] for r in recs] == [c["id"]] and recs[0]["score"] > 0.5      # the content-free row is not read
    assert skipped == {"not scored": 1, "call failed": 1, "no first case line": 1}


def test_within_unit_auc_ignores_a_signal_that_only_separates_episodes():
    rec = lambda u, y, s, i: {"label": "a", "id": i, "unit": u, "score": s, "y": y}  # noqa: E731
    between = [rec("e1", 1.0, 0.9, 0), rec("e1", 1.0, 0.9, 1), rec("e2", 0.0, 0.1, 2), rec("e2", 0.0, 0.1, 3)]
    out = F.summarise_auc(between)["arms"]["a"]
    assert out["auc"] == 1.0 and out["auc_within_unit"] is None       # no episode holds both classes
    mixed = between + [rec("e3", 1.0, 0.2, 4), rec("e3", 0.0, 0.8, 5)]  # inside e3 the score is backwards
    out = F.summarise_auc(mixed)["arms"]["a"]
    assert out["auc_within_unit"] == 0.0 and out["auc"] > 0.5


def test_a_pair_is_scored_on_the_requests_both_arms_answered():
    reqs = scored(40)
    first, rest = reqs[:20], reqs[20:]
    assert {line1_right(r) for r in first} == {0.0, 1.0} and {line1_right(r) for r in rest} == {0.0, 1.0}
    read = lambda r: 0.9 if line1_right(r) else 0.4                                # noqa: E731
    # "lo" reads on the first 20 and is backwards on the rest; "hi" answered only the first 20
    rows = ([prior_row("lo", r, read(r)) for r in first] + [prior_row("lo", r, 1.3 - read(r)) for r in rest]
            + [prior_row("hi", r, read(r)) for r in first])
    recs, _ = F.signal_rows(REQ, rows)
    out = F.summarise_auc(recs, [("lo", "hi")])
    pair = out["pairs"]["lo:hi"]
    assert out["arms"]["lo"]["auc"] < 1.0                           # over all 40 it is not a reader
    assert pair["n_common"] == 20 and pair["auc_low"] == 1.0 and pair["diff"] == 0.0


def test_held_out_keeps_scored_requests_and_refuses_an_old_episode():
    doc = F.held_out(REQ, exclude=[])
    assert len(doc["requests"]) == sum(line1_right(r) is not None for r in REQ["requests"])
    assert [r["id"] for r in doc["requests"]] == list(range(len(doc["requests"])))
    assert doc["dropped_unscored"] == len(REQ["requests"]) - len(doc["requests"])
    assert REQ["requests"][5]["id"] == 5                              # the source file is not changed
    with pytest.raises(SystemExit):
        F.held_out(REQ, exclude=[REQ])


# ------------------------------------------------------------------ run paths
class Fake:
    def __init__(self, answer, probs=None):
        self.answer, self.probs, self.prompts, self.kw = answer, probs, [], []

    def generate(self, prompt, role="generic", max_tokens=512, grammar=None, top_logprobs=None, **kw):
        self.prompts.append(prompt)
        self.kw.append({"grammar": grammar, "top_logprobs": top_logprobs, "max_tokens": max_tokens})
        tp = self.probs(prompt) if (self.probs and top_logprobs) else None
        return LLMReply(text=self.answer(prompt), backend="fake", model="fake.gguf", latency_ms=1.0, status="ok",
                        prefill_tokens=10, decode_tokens=2, token_probs=tp)


def test_run_prior_can_send_the_real_prompt_only(tmp_path):
    doc = {**REQ, "requests": REQ["requests"][:4]}
    reply = json.dumps({"r": [[1, [1]]], "sep": None, "n": [], "x": []}, separators=(",", ":"))
    probs = lambda p: [{"token": '{"', "logprob": 0.0, "top": []}, {"token": 'r":[[', "logprob": 0.0, "top": []},  # noqa: E731
                       {"token": "1", "logprob": -0.2, "top": [("1", -0.2), ("2", -1.7)]}]
    be = Fake(lambda p: reply, probs)
    out = tmp_path / "p.jsonl"
    C.run_prior(doc, be, str(out), "a", forms=("original",))
    rows = [json.loads(ln) for ln in out.read_text().splitlines()]
    assert [r["ordering"] for r in rows] == ["original"] * 4 and be.prompts == [r["prompt"] for r in doc["requests"]]
    assert rows[0]["first_line_logprobs"] == {"1": -0.2, "2": -1.7}
    C.run_prior(doc, be, str(out), "a")                                # the default still sends both; resumes
    rows = [json.loads(ln) for ln in out.read_text().splitlines()]
    assert sorted(r["ordering"] for r in rows) == ["content_free"] * 4 + ["original"] * 4 and len(be.prompts) == 8


def test_letter_logprobs_reads_the_letter_token_and_its_alternatives():
    tp = [{"token": " ", "logprob": -0.01, "top": []},
          {"token": " B", "logprob": -0.4, "top": [(" B", -0.4), ("A", -1.5), ("B", -3.0), ("x", -0.1), ("D", None)]}]
    assert F.letter_logprobs(tp) == {"B": -0.4, "A": -1.5}
    assert F.letter_logprobs([{"token": "x", "logprob": -1.0, "top": []}]) is None and F.letter_logprobs(None) is None


def test_mmluprob_a_knower_scores_1_and_a_blind_arm_half(tmp_path):
    doc = {**MMLU, "requests": MMLU["requests"][:30]}
    by_prompt = {r["prompt"]: r for r in doc["requests"]}
    wrong = lambda r: r["id"] % 3 == 0                                             # noqa: E731
    answer = lambda p: ("A" if by_prompt[p]["answer"] != "A" else "B") if wrong(by_prompt[p]) else by_prompt[p]["answer"]  # noqa: E731

    def probs(conf):
        def f(p):
            a = answer(p)
            c = conf(by_prompt[p])
            other = next(x for x in "ABCD" if x != a)
            return [{"token": a, "logprob": math.log(c), "top": [(a, math.log(c)), (other, math.log(1 - c))]}]
        return f
    for label, conf in (("knower", lambda r: 0.5 if wrong(r) else 0.9), ("blind", lambda r: 0.7)):
        be = Fake(answer, probs(conf))
        F.run_mmluprob(doc, be, str(tmp_path / "m.jsonl"), label)
        assert be.kw[0] == {"grammar": C.MMLU_GRAMMAR, "top_logprobs": C.TOP_LOGPROBS, "max_tokens": C.MMLU_CAP}
    rows = [json.loads(ln) for ln in (tmp_path / "m.jsonl").read_text().splitlines()]
    recs, skipped = F.mmluprob_rows(doc, rows)
    assert skipped == {} and len(recs) == 60
    out = F.summarise_auc(recs, [("blind", "knower")], boot=100)
    assert out["arms"]["knower"]["auc"] == 1.0 and out["arms"]["blind"]["auc"] == 0.5
    assert out["arms"]["knower"]["negative"] == 10 and out["pairs"]["blind:knower"]["diff"] == 0.5
    F.run_mmluprob(doc, be, str(tmp_path / "m.jsonl"), "blind")                    # resumes: nothing sent again
    assert len(be.prompts) == 30


# ------------------------------------------------------------------ squad
RAW = {"data": [{"paragraphs": [
    {"context": "The Nile is the longest river. It flows through Cairo. The Nile ends at the sea.",
     "qas": [{"id": "q1", "question": "Which river flows through Cairo?", "answers": [{"text": "The Nile"}, {"text": "Nile"}]},
             {"id": "q1b", "question": "ignored second question?", "answers": [{"text": "Cairo"}]}]},
    {"context": "Paris hosted the games in 1924, and again in 2024.",
     "qas": [{"id": "q2", "question": "When did Paris first host?", "answers": [{"text": "1924"}]}]},
    {"context": "Mount Everest was first climbed in 1953 by Hillary.",
     "qas": [{"id": "q3", "question": "When was Everest first climbed?", "answers": [{"text": "1953"}]}]},
    {"context": "The capital of Peru is Lima, on the coast.",
     "qas": [{"id": "q4", "question": "What is the capital of Peru?", "answers": [{"text": "Lima"}]}]},
    {"context": "x" * (F.SQUAD_MAX_CONTEXT + 1),
     "qas": [{"id": "long", "question": "too long?", "answers": [{"text": "x"}]}]},
    {"context": "A sentence with a long answer in it for this test here.",
     "qas": [{"id": "wordy", "question": "wordy?", "answers": [{"text": "a long answer in it for this test"}]}]},
]}]}


def test_contains_matches_whole_words_and_ignores_case_articles_and_punctuation():
    assert F.contains("It is the Nile, of course.", ["The Nile"])
    assert F.contains("NILE", ["the nile"])
    assert not F.contains("in 1999", ["1"]) and not F.contains("Limassol", ["Lima"])
    assert F.contains("19 24", ["19 24"]) and not F.contains("24 19", ["19 24"])
    assert not F.contains("anything", ["the"])                       # an answer of only articles matches nothing


def test_squad_select_swaps_every_gold_answer_for_one_of_the_same_kind():
    doc = F.squad_select(RAW, 4, seed=3)
    assert doc == F.squad_select(RAW, 4, seed=3)                     # seeded
    got = {r["qid"]: r for r in doc["requests"]}
    assert set(got) == {"q1", "q2", "q3", "q4"} and doc["eligible"] == 4   # one question per paragraph; long ones out
    assert [r["id"] for r in doc["requests"]] == [0, 1, 2, 3]
    for r in doc["requests"]:
        assert not F.contains(r["swapped"], r["answers"])            # no gold answer survives
        assert F.contains(r["swapped"], [r["substitute"]])           # the new answer is there
        assert not F.contains(r["context"], [r["substitute"]])       # and was not there before
        assert any(ch.isdigit() for ch in r["substitute"]) == any(ch.isdigit() for ch in r["answers"][0])
    assert got["q2"]["substitute"] == "1953" and got["q3"]["substitute"] == "1924"
    assert got["q1"]["swapped"].count(got["q1"]["substitute"]) == 2  # both mentions replaced
    forms = F.squad_forms(got["q4"])
    assert "Passage" not in forms["none"] and "Lima" in forms["oracle"] and "Lima" not in forms["swap"]
    assert got["q4"]["substitute"] in forms["swap"]


def test_squad_select_drops_a_question_whose_gold_answer_survives_the_swap():
    extra = {"context": "The Amazon is vast. Many call the amazon basin the lungs of the planet.",
             "qas": [{"id": "survives", "question": "Which river is vast?", "answers": [{"text": "Amazon"}]}]}
    raw = {"data": [{"paragraphs": RAW["data"][0]["paragraphs"] + [extra]}]}
    doc = F.squad_select(raw, 10, seed=3)
    # "Amazon" is replaced, "amazon" (lower case) is not, and scoring ignores case: the question cannot be used
    assert "survives" not in {r["qid"] for r in doc["requests"]} and doc["swap_failed"] == 1
    assert doc["eligible"] == 5 and len(doc["requests"]) == 4


def squad_rows(doc, label, none, oracle, swap):
    return [{"label": label, "id": r["id"], "ordering": form, "status": "ok", "reply": fn(r)}
            for r in doc["requests"] for form, fn in (("none", none), ("oracle", oracle), ("swap", swap))]


def test_squad_a_follower_and_a_memoriser_and_their_paired_difference(tmp_path):
    doc = F.squad_select(RAW, 4, seed=3)
    knows = lambda r: r["qid"] in ("q1", "q2")                                      # noqa: E731
    none = lambda r: r["answers"][0] if knows(r) else "no idea"                     # noqa: E731
    gold = lambda r: f"It is {r['answers'][0]}."                                    # noqa: E731
    rows = (squad_rows(doc, "follower", none, gold, lambda r: r["substitute"])
            + squad_rows(doc, "memoriser", none, lambda r: gold(r) if knows(r) else "no idea", none))
    items = F.squad_items(doc, rows)
    s = C.summarise(items)
    fo, me = s["follower"]["squad"], s["memoriser"]["squad"]
    assert fo["none_right"] == {"mean": 0.5, "n": 4} and fo["oracle_right"]["mean"] == 1.0
    assert fo["use_unknown"] == {"mean": 1.0, "n": 2} and me["use_unknown"] == {"mean": 0.0, "n": 2}
    assert fo["swap_follows"]["mean"] == 1.0 and fo["swap_memory"]["mean"] == 0.0
    assert me["swap_follows"]["mean"] == 0.0 and me["swap_memory_known"] == {"mean": 1.0, "n": 2}
    pair = F.paired_means(items, [("memoriser", "follower")], boot=100)["memoriser:follower"]
    assert pair["swap_follows"] == {"diff": 1.0, "n": 4, "ci95": [1.0, 1.0]}
    assert pair["swap_follows_known"]["n"] == 2 and pair["use_unknown"]["diff"] == 1.0
    assert pair["none_right"]["diff"] == 0.0
    # a question missing one form is not scored
    assert len(F.squad_items(doc, rows[:-1])) == len(items) - 1


def test_run_squad_sends_three_forms_without_a_grammar_and_resumes(tmp_path):
    doc = F.squad_select(RAW, 4, seed=3)
    be = Fake(lambda p: "x")
    out = tmp_path / "s.jsonl"
    assert F.run_squad(doc, be, str(out), "a") == {"ok": 12}
    assert be.kw[0] == {"grammar": None, "top_logprobs": None, "max_tokens": F.SQUAD_CAP}
    assert be.prompts[:3] == list(F.squad_forms(doc["requests"][0]).values())
    F.run_squad(doc, be, str(out), "a")
    assert len(be.prompts) == 12
