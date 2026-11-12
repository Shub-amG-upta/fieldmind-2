"""bench.echo_causes: label vs position, the prior, the MMLU control. Outcomes from fake models whose behaviour is
known (a first-line copier, a label-1 copier, a reader), on the real replay requests."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pytest

from bench import echo_causes as C
from bench import echo_test as E
from fieldmind.multi import grammar
from fieldmind.runtime.llm_backend import LLMReply

ROOT = Path(__file__).resolve().parent.parent
REQ = ROOT / "reports/data/echo_requests.json"
MMLU = ROOT / "reports/data/nd_public_requests.json"


def reqs(n=None):
    doc = json.loads(REQ.read_text())
    return {**doc, "requests": doc["requests"][:n]} if n else doc


class Fake:
    """Answers {"r":[[label,[1]]],...} with the label chosen by `pick(prompt)`."""
    def __init__(self, pick, probs=None):
        self.pick, self.probs, self.prompts, self.kw = pick, probs, [], []

    def generate(self, prompt, role="generic", max_tokens=512, grammar=None, top_logprobs=None, **kw):
        self.prompts.append(prompt)
        self.kw.append({"grammar": grammar, "top_logprobs": top_logprobs})
        lab = self.pick(prompt)
        text = lab if isinstance(lab, str) else json.dumps({"r": [[lab, [1]]], "sep": None, "n": [], "x": []},
                                                            separators=(",", ":"))
        tp = self.probs(prompt) if (self.probs and top_logprobs) else None
        return LLMReply(text=text, backend="fake", model="fake.gguf", latency_ms=1.0, status="ok",
                        prefill_tokens=100, decode_tokens=5, token_probs=tp)


def shown(prompt):
    """[(label, case)] of the case block, in display order."""
    block = prompt.split("RETRIEVED CASES:\n", 1)[1].split("\n\n", 1)[0]
    return [(int(m.group(1)), m.group(2)) for m in (re.match(r"(\d+)\. (\S+)", ln) for ln in block.splitlines()) if m]


# ------------------------------------------------------------------ relabel
def test_relabel_forms_split_first_line_label_one_and_top_case_on_every_request():
    doc = reqs()
    n_distinct = 0
    for req in doc["requests"]:
        top = E.case_lines(req["prompt"])[1]
        for form, (disp, labs) in C.relabel_forms(len(E.case_lines(req["prompt"])), req["id"], doc["seed"]).items():
            p, cases, pos = C.relabel(req["prompt"], disp, labs)
            sh = shown(p)
            assert sh[0][0] != 1                                   # label 1 is never on the first line shown
            assert {a: b for a, b in sh} == cases                  # the answer key is what the model sees
            if form == "relabel_orig":
                assert sh[0][1] == top                             # code's order: top case shown first
            else:
                assert sh[0][1] != top                             # shuffled: top case not first
                if len(sh) >= 3:
                    assert cases[1] != top                         # and not labelled 1
                    n_distinct += 1
            # every byte outside the case block is kept
            strip = lambda s: re.sub(r"RETRIEVED CASES:\n.*?\n\n", "", s, flags=re.S)  # noqa: E731
            assert strip(p) == strip(req["prompt"])
            # the rebuilt grammar accepts every label shown
            g = E.rules_for(p)
            for lab, _ in sh:
                assert grammar.accepts(g, json.dumps({"r": [[lab, [1]]], "sep": None, "n": [], "x": []},
                                                     separators=(",", ":")))
    assert n_distinct == sum(len(E.case_lines(r["prompt"])) >= 3 for r in doc["requests"])


def _score(test, backend, doc, tmp_path, label="m"):
    out = tmp_path / f"{test}.jsonl"
    C.RUN[test](doc, backend, str(out), label)
    rows = [json.loads(ln) for ln in out.read_text().splitlines()]
    return C.summarise(C.ITEMS[test](doc, rows))[label], rows


def test_a_first_line_copier_and_a_label_one_copier_come_apart(tmp_path):
    doc = reqs(60)
    first = Fake(lambda p: shown(p)[0][0])
    one = Fake(lambda p: 1)
    rf, _ = _score("relabel", first, doc, tmp_path / "f")
    r1, _ = _score("relabel", one, doc, tmp_path / "o")
    for form in ("relabel_orig", "relabel_shuf"):
        assert rf[form]["first_shown"]["mean"] == 1.0 and rf[form]["label1"]["mean"] == 0.0
        assert r1[form]["label1"]["mean"] == 1.0 and r1[form]["first_shown"]["mean"] == 0.0
    # in the code's order the first line IS the top case; shuffled it never is
    assert rf["relabel_orig"]["top_case"]["mean"] == 1.0 and rf["relabel_shuf"]["top_case"]["mean"] == 0.0
    assert r1["relabel_shuf"]["top_case_distinct"]["mean"] == 0.0


def test_a_reader_of_the_top_case_follows_it_wherever_it_is(tmp_path):
    doc = reqs(60)
    tops = {r["id"]: E.case_lines(r["prompt"])[1] for r in doc["requests"]}

    class Reader(Fake):                                        # knows each request's top case and finds it
        def generate(self, prompt, **kw):
            rid = len(self.prompts) // 2                       # two forms per request, in order
            self.pick = lambda p, t=tops[doc["requests"][rid]["id"]]: next(lab for lab, c in shown(p) if c == t)
            return super().generate(prompt, **kw)
    r, _ = _score("relabel", Reader(None), doc, tmp_path)
    for form in ("relabel_orig", "relabel_shuf"):
        assert r[form]["top_case"]["mean"] == 1.0
    assert r["relabel_shuf"]["first_shown"]["mean"] == 0.0
    assert r["relabel_shuf"]["label1_distinct"]["mean"] == 0.0


def test_relabel_resumes_without_sending_again(tmp_path):
    doc = reqs(5)
    b = Fake(lambda p: 1)
    out = tmp_path / "r.jsonl"
    C.run_relabel(doc, b, str(out), "m")
    C.run_relabel(doc, b, str(out), "m")
    assert len(b.prompts) == 10 and len(out.read_text().splitlines()) == 10


# ------------------------------------------------------------------ prior
def probs_for(model_lp, prior_lp):
    """token_probs like llama-server's: the answer's first case line at the 3rd token ('{"r":[[' then digit)."""
    def f(prompt):
        lp = prior_lp if "1. N/A" in prompt.split("RETRIEVED CASES:\n", 1)[1][:8] else model_lp
        alts = [(str(j), v) for j, v in lp.items()]
        best = max(lp, key=lp.get)
        return [{"token": '{"', "logprob": 0.0, "top": []}, {"token": 'r":[[', "logprob": 0.0, "top": []},
                {"token": str(best), "logprob": lp[best], "top": alts}]
    return f


def test_the_prior_comes_from_the_content_free_prompt_and_moves_the_pick(tmp_path):
    doc = reqs(40)
    # the model says line 1 (log p -0.5 vs -1.0), but the empty prompt says line 1 even more (-0.1 vs -2.5):
    # calibrated, line 2 wins (-0.4 vs +1.5)
    b = Fake(lambda p: 1, probs=probs_for({1: -0.5, 2: -1.0}, {1: -0.1, 2: -2.5}))
    r, rows = _score("prior", b, doc, tmp_path)
    assert sum("1. N/A" in p for p in b.prompts) == len(doc["requests"])     # one content-free call each
    assert all(k["top_logprobs"] == C.TOP_LOGPROBS for k in b.kw)
    cal = r["calibrate"]
    assert cal["model_line1"]["mean"] == 1.0 and cal["cal_line1"]["mean"] == 0.0 and cal["moved"]["mean"] == 1.0
    assert cal["prior_argmax_line1"]["mean"] == 1.0 and cal["prior_line1"]["mean"] > 0.85
    # the paired difference is the mean of per-request differences: right on line 1 (the model's pick) and calibrated
    assert cal["cal_minus_line1"]["mean"] == pytest.approx(cal["cal_right"]["mean"] - cal["line1_right"]["mean"], abs=1e-3)
    assert cal["model_minus_line1"]["mean"] == 0.0               # the model's pick IS line 1 here


def test_a_flat_prior_moves_nothing(tmp_path):
    doc = reqs(40)
    b = Fake(lambda p: 1, probs=probs_for({1: -0.5, 2: -1.0}, {1: -0.7, 2: -0.7}))
    r, _ = _score("prior", b, doc, tmp_path)
    assert r["calibrate"]["moved"]["mean"] == 0.0 and r["calibrate"]["cal_line1"]["mean"] == 1.0


def test_no_probabilities_means_no_prior_item(tmp_path):
    doc = reqs(10)
    out = tmp_path / "p.jsonl"
    C.run_prior(doc, Fake(lambda p: 1), str(out), "m")
    rows = [json.loads(ln) for ln in out.read_text().splitlines()]
    assert len(rows) == 20 and all(row["first_line_logprobs"] == {} for row in rows)
    assert C.prior_items(doc, rows) == []                    # nothing read, nothing claimed


# ------------------------------------------------------------------ mmlu
def mdoc(n=40):
    d = json.loads(MMLU.read_text())
    return {**d, "requests": d["requests"][:n]}


def test_mmlu_forms_put_each_option_at_each_letter_once():
    for req in mdoc()["requests"]:
        forms = C.mmlu_forms(req["prompt"], req["answer"])
        opts = C.mmlu_options(req["prompt"])
        assert forms["cyc0"][0] == req["prompt"] and forms["cyc0"][1] == req["answer"]
        for letter in C.LETTERS:
            assert sorted(C.mmlu_options(p)[letter] for p, _, _ in forms.values()) == sorted(opts.values())
        for p, correct, sh in forms.values():
            assert C.mmlu_options(p)[correct] == opts[req["answer"]]
            assert p.split("\nA. ")[0] == req["prompt"].split("\nA. ")[0]


def test_mmlu_a_reader_is_invariant_and_an_a_copier_is_not(tmp_path):
    doc = mdoc()
    ans = {r["prompt"].split("\nA. ")[0]: C.mmlu_options(r["prompt"])[r["answer"]] for r in doc["requests"]}

    def reader(p):
        o = C.mmlu_options(p)
        return next(k for k, v in o.items() if v == ans[p.split("\nA. ")[0]])
    rr, _ = _score("mmlu", Fake(reader), doc, tmp_path / "r")
    ra, _ = _score("mmlu", Fake(lambda p: "A"), doc, tmp_path / "a")
    assert rr["all_orders"]["invariance"]["mean"] == 1.0 and rr["cyc2"]["right"]["mean"] == 1.0
    assert ra["all_orders"]["invariance"]["mean"] == 0.0 and ra["cyc1"]["letter_A"]["mean"] == 1.0
    # each option is at A once in 4 orders, so an A-copier is right on exactly 1 of 4
    assert sum(ra[f"cyc{s}"]["right"]["mean"] for s in range(4)) == pytest.approx(1.0)


# ------------------------------------------------------------------ intervals
def test_intervals_resample_units_and_collapse_when_units_agree():
    same = [("m", "f", f"u{i}", {"x": 1.0 if j < 1 else 0.0}) for i in range(10) for j in range(2)]
    differ = [("m", "f", f"u{i}", {"x": 1.0 if i < 5 else 0.0}) for i in range(10) for _ in range(2)]
    s = C.summarise(same, boot=300)["m"]["f"]["x"]
    d = C.summarise(differ, boot=300)["m"]["f"]["x"]
    assert s["mean"] == d["mean"] == 0.5
    assert s["ci95"] == [0.5, 0.5]                        # every unit has the same mean: no spread
    assert d["ci95"][0] < 0.35 and d["ci95"][1] > 0.65


def test_mmlu_one_copied_order_breaks_invariance(tmp_path):
    # reads in 3 orders, but in the order that shows the original option B at A it answers "A": that question keeps
    # one pick in all 4 orders only when its answer IS B (copying and reading then agree)
    doc = mdoc()
    q = {r["prompt"].split("\nA. ")[0]: r for r in doc["requests"]}

    def half(p):
        r = q[p.split("\nA. ")[0]]
        opts, o = C.mmlu_options(r["prompt"]), C.mmlu_options(p)
        if o["A"] == opts["B"]:
            return "A"
        return next(k for k, v in o.items() if v == opts[r["answer"]])
    res, _ = _score("mmlu", Fake(half), doc, tmp_path)
    want = sum(r["answer"] == "B" for r in doc["requests"]) / len(doc["requests"])
    assert 0 < want < 1
    assert res["all_orders"]["invariance"]["mean"] == pytest.approx(want, abs=1e-4)


# ------------------------------------------------------------------ saved data (E1-E3)
def _truthful(doc):
    """{id: true case} of the scored requests."""
    return {r["id"]: r["target"] for r in doc["requests"]
            if r["target"] not in (None, "NONE") and r["evidence_tick"] * r["tick_s"] >= r["onset_s"]}


def test_ceiling_counts_the_true_case_where_it_is_shown():
    doc = reqs()
    items = C.ceiling_items(doc)
    s = C.summarise(items)["retrieval"]
    truth = _truthful(doc)
    shown_ = [r for r in doc["requests"] if r["id"] in truth]
    in_list = sum(truth[r["id"]] in E.case_lines(r["prompt"]).values() for r in shown_) / len(shown_)
    at1 = sum(E.case_lines(r["prompt"])[1] == truth[r["id"]] for r in shown_) / len(shown_)
    assert s["pooled"]["case_in_list"]["mean"] == pytest.approx(in_list, abs=1e-4)
    assert s["pooled"]["line1_right"]["mean"] == pytest.approx(at1, abs=1e-4)
    # where it is: the shares of lines 1-4 add up to "in the list"
    assert sum(s["pooled"][f"case_at_line{j}"]["mean"] for j in range(1, 5)) == pytest.approx(in_list, abs=1e-3)
    assert s["pooled"]["case_in_list"]["n"] == sum(s[p]["case_in_list"]["n"] for p in ("boiler", "cranfield", "tep"))


def _replay(doc, pick, tmp_path, label="m"):
    out = tmp_path / f"{label}.jsonl"
    E.run_replay(doc, Fake(pick), str(out), label)
    return [json.loads(ln) for ln in out.read_text().splitlines()]


def test_vote_a_line1_copier_scores_line1_and_a_reader_scores_the_ceiling(tmp_path):
    doc = reqs(90)
    truth = _truthful(doc)
    copier = _replay(doc, lambda p: 1, tmp_path, "copy")
    tops = {r["id"]: r for r in doc["requests"]}

    def reader(p):                       # names the true case when shown, else line 1
        for rid, t in truth.items():
            body = tops[rid]["prompt"].split("RETRIEVED CASES:\n")[0]
            if p.startswith(body):
                hit = [lab for lab, c in shown(p) if c == t]
                return hit[0] if hit else 1
        return 1
    rd = _replay(doc, reader, tmp_path, "read")
    vc = C.summarise(C.vote_items(doc, copier))["copy"]["vote"]
    vr = C.summarise(C.vote_items(doc, rd))["read"]["vote"]
    # a copier's vote is the case shown first most often across the 4 orders (they are not balanced: line1_last
    # always moves the top case last), counted here from the orders themselves, not from the replies
    want = []
    for r in doc["requests"]:
        if r["id"] not in truth:
            continue
        orig = E.case_lines(r["prompt"])
        firsts = [orig[o[0]] for o in E.orderings(len(orig), r["id"], doc["seed"]).values()]
        best = max(firsts.count(c) for c in firsts)
        v = orig[1] if firsts.count(orig[1]) == best else next(c for c in firsts if firsts.count(c) == best)
        want.append(v == truth[r["id"]])
    assert vc["vote_right"]["mean"] == pytest.approx(sum(want) / len(want), abs=1e-3)
    assert vc["orig_minus_line1"]["mean"] == 0.0
    ceil = C.summarise([i for i in C.ceiling_items(doc) if i[1] == "pooled"])["retrieval"]["pooled"]
    assert vr["vote_right"]["mean"] == pytest.approx(ceil["case_in_list"]["mean"], abs=1e-3)
    assert vr["vote_minus_line1"]["mean"] == pytest.approx(ceil["case_in_list"]["mean"] - ceil["line1_right"]["mean"], abs=1e-3)


def test_hint_a_true_case_seeker_beats_random_and_a_random_mover_does_not(tmp_path):
    doc = reqs(150)
    truth = _truthful(doc)
    pre = {r["id"]: r["prompt"].split("RETRIEVED CASES:\n")[0] for r in doc["requests"]}

    def seeker(p):                       # leaves line 1 only to name the true case
        rid = next(i for i, b in pre.items() if p.startswith(b))
        hit = [lab for lab, c in shown(p) if c == truth.get(rid)]
        return hit[0] if hit and hit[0] != 1 else 1

    def last(p):                         # always the last line: a pick that ignores the content
        return shown(p)[-1][0]
    hs = C.summarise(C.hint_items(doc, _replay(doc, seeker, tmp_path, "seek")))["seek"]["shuffled"]
    hl = C.summarise(C.hint_items(doc, _replay(doc, last, tmp_path, "last")), boot=200)["last"]["shuffled"]
    assert hs["dev_right"]["mean"] == 1.0 and hs["dev_minus_random"]["mean"] > 0.3
    lo, hi = hl["dev_minus_random"]["ci95"]
    assert lo <= 0.0 <= hi or abs(hl["dev_minus_random"]["mean"]) < 0.1     # no better than a random other line


def test_hint_uses_only_the_shuffles_and_a_random_baseline_without_line1(tmp_path):
    doc = reqs(150)
    truth = _truthful(doc)
    rows = _replay(doc, lambda p: shown(p)[-1][0], tmp_path, "last")      # always leaves line 1
    items = [i for i in C.hint_items(doc, rows)]
    assert len(items) == 2 * len(truth)                                      # shuffle_a and shuffle_b only
    # the random other line, by another route: the true case is among the other lines exactly when it is shown
    # and not on line 1, and then a uniform pick finds it with chance 1 / (k - 1)
    want = []
    for row in rows:
        if row["ordering"] in ("shuffle_a", "shuffle_b") and row["id"] in truth:
            cases = {int(a): b for a, b in row["cases"].items()}
            t = truth[row["id"]]
            want.append((t in cases.values() and cases[1] != t) / (len(cases) - 1))
    s = C.summarise(items)["last"]["shuffled"]
    assert s["dev_random"]["mean"] == pytest.approx(sum(want) / len(want), abs=1e-4)
