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


# ---- the Cranfield and TEP sets (reports/reading_cranfield_tep_build.md) -------------------------------------------
import gzip  # noqa: E402

from bench import echo_4bit as B  # noqa: E402

DATA = REQ.parent
TEP = DATA / "reading_requests_tep.json"
CRANFIELD = DATA / "reading_requests_cranfield.json"
SET_R = DATA / "echo_requests.json"


@pytest.mark.parametrize("path", [TEP, CRANFIELD])
def test_both_new_sets_load_and_every_list_form_and_per_case_prompt_builds(path):
    d = json.loads(path.read_text())
    assert len(R.code_records(d)) == len(d["requests"]) > 100
    for r in d["requests"]:
        p = r["prompt"]
        assert C._right(r, None)[1] is not None                      # scored requests only
        assert not r["saved_replies"]                                 # no model row carried in
        for form in ("no_belief", "no_example", "neither"):
            assert R.list_form(p, form) != p and E.case_lines(R.list_form(p, form)) == E.case_lines(p)
        assert all(R.per_case_prompt(p, ln) for ln in E.case_lines(p))


def test_the_tep_set_is_held_out_from_set_r_and_set_h():
    t = json.loads(TEP.read_text())
    old = [json.loads(SET_R.read_text()), json.loads(REQ.read_text())]
    assert t["held_out"] is True and {r["asset"] for r in t["requests"]} == {"tep"}
    assert not {r["episode"] for r in t["requests"]} & {r["episode"] for d in old for r in d["requests"]}
    assert not {r["prompt"] for r in t["requests"]} & {r["prompt"] for d in old for r in d["requests"]}
    assert all(r["episode"].endswith("_r13") for r in t["requests"])


def test_held_out_refuses_a_set_sharing_an_episode_or_a_prompt_with_an_earlier_set():
    r_doc, h_doc = json.loads(SET_R.read_text()), json.loads(REQ.read_text())
    t = json.loads(TEP.read_text())
    same_episode = {**t, "requests": [dict(t["requests"][0], episode=r_doc["requests"][0]["episode"])]}
    same_prompt = {**t, "requests": [dict(t["requests"][0], prompt=h_doc["requests"][0]["prompt"])]}
    for doc in (same_episode, same_prompt):
        with pytest.raises(SystemExit):
            B.held_out(doc, [r_doc, h_doc])
    assert len(B.held_out(t, [r_doc, h_doc])["requests"]) == len(t["requests"])


def test_a_per_plant_cap_draws_a_seeded_subset_of_the_scored_requests():
    t = json.loads(TEP.read_text())
    a, b = B.held_out(t, [], 50, 7), B.held_out(t, [], 50, 7)
    assert len(a["requests"]) == 50 and [r["prompt"] for r in a["requests"]] == [r["prompt"] for r in b["requests"]]
    assert {r["prompt"] for r in a["requests"]} <= {r["prompt"] for r in t["requests"]}
    assert a["scored_available"] == len(t["requests"])
    assert [r["prompt"] for r in B.held_out(t, [], 50, 8)["requests"]] != [r["prompt"] for r in a["requests"]]


def test_the_cranfield_set_is_set_r_scored_cranfield_prompts_labelled_not_held_out():
    c, r_doc = json.loads(CRANFIELD.read_text()), json.loads(SET_R.read_text())
    want = [r["prompt"] for r in r_doc["requests"] if r["asset"] == "cranfield" and C._right(r, None)[1] is not None]
    assert c["held_out"] is False and c["plant"] == "cranfield"
    assert [r["prompt"] for r in c["requests"]] == want and [r["id"] for r in c["requests"]] == list(range(len(want)))


def _mock_run(tmp_path, prompt, reply, backend="mock", episode="tep_board_F01_r13"):
    run = {"episode_id": episode, "backend": backend,
           "ground_truth": {"asset": "tep", "root_cause_id": "PF-01", "fault_onset_t": 0, "tick_period_s": 180},
           "assessments": [{"tick": 200, "envelopes": [{"agent": "diagnostician", "status": "ok", "tick": 200,
                                                        "prompt": prompt, "raw_reply": reply}]}]}
    d = tmp_path / backend
    d.mkdir(exist_ok=True)
    (d / f"{episode}_multi.run.json.gz").write_bytes(gzip.compress(json.dumps(run).encode()))
    return str(d)


def test_mock_prompts_accepts_the_mocks_spaced_reply_and_still_refuses_a_reply_the_grammar_rejects(tmp_path):
    p = json.loads(TEP.read_text())["requests"][0]["prompt"]
    assert not E.has_letters(p)                       # TEP prompts show no group letters
    good = '{"g": "F", "r": [[1, [1]], [2, [1]]], "sep": 1, "n": [], "x": []}'    # the mock's own form
    bad = '{"g": "F", "r": [[9, [1]]], "sep": 1, "n": [], "x": []}'             # case line 9 is not shown
    dev = {"tep_board_F01_r13"}
    ok = E.select([_mock_run(tmp_path, p, good)], 10, 0, dev=dev, mock_prompts=True)
    assert len(ok["requests"]) == 1 and ok["requests"][0]["saved_replies"] == [] and ok["refused"] == 0
    assert E.select([_mock_run(tmp_path, p, good)], 10, 0, dev=dev)["refused"] == 1      # board rule unchanged
    (tmp_path / "mock" / "tep_board_F01_r13_multi.run.json.gz").unlink()
    assert E.select([_mock_run(tmp_path, p, bad)], 10, 0, dev=dev, mock_prompts=True)["refused"] == 1


def test_mock_prompts_refuses_a_run_that_is_not_a_mock_run(tmp_path):
    p = json.loads(TEP.read_text())["requests"][0]["prompt"]
    with pytest.raises(SystemExit):
        E.select([_mock_run(tmp_path, p, "{}", backend="llamaserver")], 10, 0, dev={"tep_board_F01_r13"},
                 mock_prompts=True)


@pytest.mark.parametrize("run", [1, 2, 6, 7, 12])
def test_new_dev_runs_refuse_any_run_in_the_split_or_twinned_with_one(run, tmp_path):
    from data.tep import convert as cv
    with pytest.raises(ValueError):
        cv.convert_new_dev((run,), tmp_path)
    assert not any(tmp_path.iterdir())
    assert cv.NEW_DEV_RUNS == (13,)


class _Reader:
    """A fake model that reads the evidence: high probability on line 1 exactly when line 1 is in the true group,
    whatever the form; per case, yes exactly for cases in the group."""

    @staticmethod
    def _key(prompt):          # the prompt without the two lines a list form may remove
        return "\n".join(ln for ln in prompt.splitlines()
                         if not ln.startswith(("WORLD MODEL: belief (from code):", "Example: ")))

    def __init__(self, doc):
        self.by_key = {self._key(r["prompt"]): r for r in doc["requests"]}
        self.doc = doc

    def generate(self, prompt, **kw):
        if "CASE TO CHECK:" in prompt:
            py = 0.9 if _in_group(self.doc, prompt) else 0.1
            tp = [{"token": "yes", "logprob": math.log(py), "top": [("yes", math.log(py)), ("no", math.log(1 - py))]}]
            return SimpleNamespace(status="ok", text="yes" if py > 0.5 else "no", model="fake.gguf", prefill_tokens=1,
                                   decode_tokens=1, latency_ms=1.0, token_probs=tp)
        r = self.by_key[self._key(prompt)]
        p1 = 0.9 if C._right(r, E.case_lines(r["prompt"])[1])[1] else 0.3
        tp = [{"token": '{"', "logprob": 0.0, "top": []}, {"token": 'r":[[', "logprob": 0.0, "top": []},
              {"token": "1", "logprob": math.log(p1), "top": [("1", math.log(p1)), ("2", math.log(1 - p1))]}]
        return SimpleNamespace(status="ok", text='{"r":[[1,[1]]],"sep":null,"n":[],"x":[]}', model="fake.gguf",
                               prefill_tokens=1, decode_tokens=1, latency_ms=1.0, token_probs=tp)


@pytest.mark.parametrize("path", [TEP, CRANFIELD])
def test_the_whole_run_and_score_path_works_on_both_new_sets(path, tmp_path):
    d = json.loads(path.read_text())
    doc = {**d, "requests": d["requests"][:40]}
    be = _Reader(doc)
    prior, lst, pc = tmp_path / "prior.jsonl", tmp_path / "list.jsonl", tmp_path / "pc.jsonl"
    assert C.run_prior(doc, be, str(prior), "rd", forms=("original",)) == {"ok": 40}
    assert R.run_list(doc, be, str(lst), "rd") == {"ok": 120}
    R.run_per_case(doc, be, str(pc), "rd")
    rows = [json.loads(x) for p in (prior, lst, pc) for x in p.read_text().splitlines()]
    s = R.score_source(doc, rows, ["rd"], 100, 1)["rd"]
    if 0 < sum(C._right(r, E.case_lines(r["prompt"])[1])[1] for r in doc["requests"]) < 40:
        assert s["auc"]["original"] == 1.0 and s["auc"]["no_belief"] == 1.0 and s["drop"]["no_belief"]["diff"] == 0.0
    f = R.score_fix(doc, rows, ["rd"], 100, 1)["rd"]
    assert f["n"] == 40 and f["vs_line1"]["diff"] >= 0


# ---- Amendment A2: H1-H3
def _rows_for(doc, label, form, p1, picks1, ms):
    """List rows: p(line 1) from p1(req), picks line 1 iff picks1(req), latency ms."""
    out = []
    for r in doc["requests"]:
        k = len(E.case_lines(r["prompt"]))
        rest = (1 - p1(r)) / max(k - 1, 1)
        row = {"label": label, "id": r["id"], "status": "ok", "latency_ms": ms,
               "reply": '{"r":[[1,[1]]]}' if picks1(r) else '{"r":[[2,[1]]]}',
               "first_line_logprobs": {str(j): math.log(p1(r) if j == 1 else max(rest, 1e-9)) for j in range(1, k + 1)}}
        row.update({"ordering": "original"} if form == "original" else {"form": form, "line": None})
        out.append(row)
    return out


def _pc_rows(doc, label, p_line1, ms):
    out = []
    for r in doc["requests"]:
        for line in E.case_lines(r["prompt"]):
            py = p_line1(r) if line == 1 else 0.3
            out.append({"label": label, "id": r["id"], "form": "per_case", "line": line, "status": "ok",
                        "reply": "yes" if py >= 0.5 else "no", "p_yes": py, "latency_ms": ms,
                        "prefill": 1, "decode": 1})
    return out


def test_confirm_reads_h1_h2_h3_by_the_agreed_rule(doc):
    good = lambda r: C._right(r, E.case_lines(r["prompt"]).get(1))[1] == 1.0          # noqa: E731
    know = lambda r: 0.9 if good(r) else 0.3                                          # noqa: E731
    always, mostly = (lambda r: True), (lambda r: r["id"] % 2 != 0)                    # noqa: E731
    rows = []
    # 4-bit: copies always; without the example the signal goes but copying cannot rise -> H2 fails on one of its two parts
    rows += _rows_for(doc, "q4", "original", know, always, 1000) + _rows_for(doc, "q4", "no_example", lambda r: 0.6, always, 1000)
    rows += _pc_rows(doc, "q4", know, 200)
    # 8-bit: leaves line 1 on every other request (so every episode has departures), without the example copies always and loses the signal -> H1, H2 hold
    rows += _rows_for(doc, "q8", "original", know, mostly, 1000)
    rows += _rows_for(doc, "q8", "no_example", lambda r: 0.6, always, 1000) + _pc_rows(doc, "q8", know, 500)   # one-token call at 1/2: too slow
    s = R.score_confirm(doc, rows, "q4", "q8", 300, 1)
    assert s["q4"]["H1"]["holds"] and s["q4"]["H1"]["time_ratio"] == pytest.approx(0.2)
    assert not s["q8"]["H1"]["holds"] and s["q8"]["H2"]["holds"] and not s["q4"]["H2"]["holds"]
    assert s["q4"]["H2"]["auc_drop"]["diff"] == pytest.approx(0.5) and s["q4"]["H2"]["line1_share_diff"]["diff"] == 0
    assert s["H1"] == "partly" and s["H2"] == "partly"
    assert s["H3"]["line1_share_low_minus_high"]["diff"] == pytest.approx(0.5, abs=0.02) and s["H3"]["reading"] == "confirmed"
    # the one-token call slower than a third of the list call -> H1 fails on time alone
    slow = [dict(r, latency_ms=500) if r.get("form") == "per_case" else r for r in rows]
    assert R.score_confirm(doc, slow, "q4", "q8", 300, 1)["H1"] == "not confirmed"
