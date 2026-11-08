"""explain_v2 (reports/accuracy_fixes.md, fix 1): the no-example rank-only prompt, the
empty-side skip, and the case-line triple cap. Outcomes: the text a prompt shows, the
skip decision and its log record."""
from types import SimpleNamespace

import pytest

from fieldmind.multi import compact
from fieldmind.multi.agents.bev import explain_prompt, switches
from fieldmind.multi.agents.diagnostician import DiagnosticianAgent

SIG = {"a|UP|SLOW": 1.0, "b|DOWN|*": 1.0, "c|HIGH|-": 1.0, "d|SHIFT_UP|-": 1.0, "e|WIDE|-": 1.0}


def test_uncapped_case_line_is_every_triple_in_case_order():
    assert compact.signature_text(SIG) == "a UP SLOW, b DOWN *, c HIGH, d SHIFT_UP, e WIDE"
    assert compact.signature_text(SIG, 5) == compact.signature_text(SIG)      # cap >= size: same text


def test_cap_puts_the_ticks_own_triples_first_and_counts_the_rest():
    tick = {("e", "WIDE", "-"): 1.0, ("b", "DOWN", "FAST"): 1.0}          # "*" matches any band
    assert compact.signature_text(SIG, 3, tick) == "b DOWN *, e WIDE, a UP SLOW (+2 more)"
    assert compact.signature_text(SIG, 2, {}) == "a UP SLOW, b DOWN * (+3 more)"


def test_cap_reaches_the_switches_and_is_validated():
    assert compact.compact_switches({"case_triples_max": 8})["case_triples_max"] == 8
    assert "case_triples_max" not in compact.compact_switches({})      # unset: run records unchanged
    with pytest.raises(ValueError):
        compact.compact_switches({"case_triples_max": 0})


def test_v2_prompt_is_v1_without_the_copied_example():
    v1 = compact.load_prompt("diag_rank_only.txt")
    v2 = compact.load_prompt("diag_rank_only_v2.txt")
    assert 'Example: {{"r":[2,1]}}' in v1 and "Example" not in v2
    assert v1.replace('Example: {{"r":[2,1]}}\n', "") == v2


def test_switches_parse_empty_skip_and_explain_prompt():
    m = {"bev": {"explain": "on", "empty_skip": "on", "explain_prompt": "v2"}}
    assert switches(m)["empty_skip"] == "on" and explain_prompt(m) == "v2"
    assert explain_prompt({}) == "v1" and switches({})["empty_skip"] == "off"
    with pytest.raises(ValueError):
        explain_prompt({"bev": {"explain_prompt": "v3"}})


def _agent(mode):
    return SimpleNamespace(skip_log=[], bev_sw={"empty_skip": mode})


def _fp(case_ids):
    return (frozenset(), frozenset(), frozenset(), frozenset(case_ids))


def test_empty_skip_only_when_no_case_is_shown():
    a = _agent("on")
    assert DiagnosticianAgent._empty_skip(a, _fp([]), "reaction", 7) is True
    assert DiagnosticianAgent._empty_skip(a, _fp(["note:N1"]), "reaction", 8) is True   # notes are not cases
    assert DiagnosticianAgent._empty_skip(a, _fp(["PF-06"]), "reaction", 9) is False
    assert [r["evidence_tick"] for r in a.skip_log] == [7, 8]
    assert a.skip_log[0]["idea"] == "empty_skip" and a.skip_log[0]["mode"] == "on"


def test_one_case_fires_only_for_exactly_one_case_and_logs_it():
    a = SimpleNamespace(skip_log=[], bev_sw={"one_code": "on"})
    assert DiagnosticianAgent._one_case(a, _fp(["PF-05"]), "separation", 3) is True
    assert DiagnosticianAgent._one_case(a, _fp(["PF-05", "note:N2"]), "separation", 4) is True
    assert DiagnosticianAgent._one_case(a, _fp(["PF-05", "PF-11"]), "separation", 5) is False
    assert DiagnosticianAgent._one_case(a, _fp([]), "separation", 6) is False
    assert [(r["evidence_tick"], r["case"], r["skipped"]) for r in a.skip_log] == [
        (3, "PF-05", True), (4, "PF-05", True)]


def test_code_answer_is_a_checked_zero_cost_envelope():
    from fieldmind.multi.agents._call import code_answer
    from fieldmind.multi.agents.diagnostician import ONE_CASE_ANSWER
    env = code_answer(ONE_CASE_ANSWER, "diagnostician", 12, compact.check_rank_only_shape)
    assert env.status == "ok" and env.payload == {"r": [1]}
    assert env.backend == "code" and env.tokens == {"prefill": 0, "decode": 0} and env.calls == []
    bad = code_answer('{"x":1}', "diagnostician", 12, compact.check_rank_only_shape)
    assert bad.status == "invalid_schema"


def test_one_code_needs_explain_on():
    from fieldmind.multi.agents.bev import switches as sw
    assert sw({"bev": {"one_code": "on"}})["one_code"] == "on"
    with pytest.raises(ValueError, match="one_code needs"):
        DiagnosticianAgent(SimpleNamespace(), {}, {"split": True, "split_on_change": True,
                                                  "compact": {"schema": True, "group_letters": False},
                                                  "bev": {"one_code": "on"}})
