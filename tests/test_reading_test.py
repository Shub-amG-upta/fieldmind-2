"""bench.reading_test: prompt forms, the per-case run and both scores, on real set H prompts with fake models
whose behaviour is known."""

from __future__ import annotations

import json
import math
from pathlib import Path
from types import SimpleNamespace

import pytest

from bench import echo_causes as C
from bench import echo_test as E
from bench import reading_test as R

REQ = Path(__file__).resolve().parent.parent / "reports/data/echo_4bit_requests.json"


@pytest.fixture(scope="module")
def doc():
    d = json.loads(REQ.read_text())
    return {**d, "requests": d["requests"][:60]}


def test_drop_belief_and_example_remove_only_their_line(doc):
    p = doc["requests"][0]["prompt"]
    nb, ne, both = R.list_form(p, "no_belief"), R.list_form(p, "no_example"), R.list_form(p, "neither")
    assert "WORLD MODEL" not in nb and "Example: " in nb and "OTHER SIDE" in nb
    assert "Example: " not in ne and "WORLD MODEL" in ne
    assert "WORLD MODEL" not in both and "Example: " not in both
    assert len(p.splitlines()) - len(nb.splitlines()) == 1 and len(p.splitlines()) - len(both.splitlines()) == 2
    assert E.case_lines(nb) == E.case_lines(p)
    with pytest.raises(ValueError):
        R.drop_belief(nb)


def test_per_case_prompt_holds_one_case_and_no_list_belief_or_example(doc):
    p = doc["requests"][0]["prompt"]
    cases = E.case_lines(p)
    for line, cid in cases.items():
        q = R.per_case_prompt(p, line)
        assert cid in q and all(o not in q for o in cases.values() if o != cid)
        assert "RETRIEVED CASES" not in q and "WORLD MODEL" not in q and "Example:" not in q
        assert p.split("FACTS:\n", 1)[1].split("\n\n", 1)[0] in q and R.QUESTION in q
        assert f"\n{line}. " not in q.split("CASE TO CHECK:\n", 1)[1].split("\n", 1)[0]   # no line number shown


def test_yes_prob_reads_the_answer_token_alternatives():
    tp = [{"token": "yes", "logprob": math.log(0.6), "top": [("yes", math.log(0.6)), (" no", math.log(0.2))]}]
    assert R.yes_prob(tp) == pytest.approx(0.75)
    assert R.yes_prob([{"token": "maybe", "logprob": -0.1, "top": []}]) is None
    assert R.yes_prob(None) is None


def _fake(policy):
    """policy(per-case prompt) -> p(yes)."""
    def generate(prompt, **kw):
        py = policy(prompt)
        return SimpleNamespace(status="ok", text="yes" if py >= 0.5 else "no", model="fake.gguf",
                               prefill_tokens=100, decode_tokens=1, latency_ms=1.0,
                               token_probs=[{"token": "yes", "logprob": math.log(max(py, 1e-9)),
                                             "top": [("yes", math.log(max(py, 1e-9))),
                                                     ("no", math.log(max(1 - py, 1e-9)))]}])
    return SimpleNamespace(generate=generate)


def _req_of(doc, prompt):
    for r in doc["requests"]:
        if prompt.split("FACTS:\n", 1)[1].split("CASE TO CHECK", 1)[0] in r["prompt"]:
            return r


def _in_group(doc, q):
    """Is the case in this per-case prompt in the true fault group? (what a perfect reader would judge)"""
    r = _req_of(doc, q)
    cid = q.split("CASE TO CHECK:\n", 1)[1].split()[0]
    return bool(r and C._right(r, cid)[1])


def test_an_evidence_reader_picks_the_true_case_and_a_constant_model_falls_to_case_id_not_line(doc, tmp_path):
    out = tmp_path / "pc.jsonl"
    # a perfect reader: yes only for cases in the true fault group
    reader = _fake(lambda q: 0.9 if _in_group(doc, q) else 0.1)
    R.run_per_case(doc, reader, str(out), "reader")
    assert R.run_per_case(doc, reader, str(out), "reader") == {}             # resumes: nothing sent twice
    const = _fake(lambda q: 0.5)
    R.run_per_case(doc, const, str(out), "const")
    rows = [json.loads(x) for x in out.read_text().splitlines()]
    s = R.score_fix(doc, rows, ["reader", "const"], 200, 1)
    rd = s["reader"]
    in_list = [r for r in doc["requests"] if C._right(r, None)[1] is not None
               and any(C._right(r, c)[1] for c in E.case_lines(r["prompt"]).values())]
    assert rd["vs_line1"]["b"] == pytest.approx(len(in_list) / rd["n"])       # right whenever the true group is listed
    assert rd["vs_line1"]["diff"] > 0 and rd["vs_line1"]["diff_ci95"][0] > 0
    # the constant model ties every case: the pick is the lowest case id, so its line-1 share is not 1
    recs = R.per_case_records(doc, rows)["const"]
    for rid, rec in recs.items():
        cases = E.case_lines(doc["requests"][rid]["prompt"])
        assert rec["top_is_line1"] == float(min(cases.values()) == cases[1])
    assert s["const"]["top_is_line1"] < 1.0


def _list_rows(doc, label, form, score_of):
    rows = []
    for r in doc["requests"]:
        k = len(E.case_lines(r["prompt"]))
        p1 = score_of(r)
        rest = (1 - p1) / max(k - 1, 1)
        lp = {str(j): math.log(p1 if j == 1 else max(rest, 1e-9)) for j in range(1, k + 1)}
        rows.append({"label": label, "id": r["id"], "form": form, "ordering": "original" if form == "original" else None,
                     "status": "ok", "reply": '{"r":[[1,[1]]]}', "first_line_logprobs": lp})
    return rows


def test_source_score_shows_a_drop_when_the_signal_lived_in_the_removed_line(doc):
    truth = lambda r: C._right(r, E.case_lines(r["prompt"]).get(1))[1]                 # noqa: E731
    know = lambda r: 0.9 if truth(r) else 0.4                                          # noqa: E731
    rows = (_list_rows(doc, "belief_reader", "original", know)
            + _list_rows(doc, "belief_reader", "no_belief", lambda r: 0.6)            # signal gone
            + _list_rows(doc, "evidence_reader", "original", know)
            + _list_rows(doc, "evidence_reader", "no_belief", know))                  # signal kept
    for r in rows:
        r.pop("form") if r["form"] == "original" else None
    s = R.score_source(doc, rows, ["belief_reader", "evidence_reader"], 200, 1)
    b, e = s["belief_reader"], s["evidence_reader"]
    assert b["auc"]["original"] == 1.0 and b["auc"]["no_belief"] == 0.5 and b["drop"]["no_belief"]["diff"] == 0.5
    assert e["auc"]["no_belief"] == 1.0 and e["drop"]["no_belief"]["diff"] == 0.0
    assert 0.0 <= s["code_belief_auc"] <= 1.0
