"""bench.ext_faultexplainer: outcomes on a hand-built prompt, a fake model and (when the audited
checkout is present) the real build."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from bench import ext_faultexplainer as X

LIST = "\n".join(f"{k}. IDV({k}) cause number {k} & Step" for k in range(1, 16))
PROMPT = f"System text.\n**Available Root Causes**:\n{LIST}\n\nThe top feature changes are\nFeature: x\n"
REPO = Path(os.environ.get("FAULTEXPLAINER_REPO", "/nonexistent"))


def _doc(faults=(6, 7, 12)):
    return {"requests": [{"id": n, "fault": f, "aliases": list(X.ALIASES.get(f, ())),
                          "prompts": {"eval": PROMPT + f"start with Fault {f}", "app": PROMPT}}
                         for n, f in enumerate(faults)]}


def test_reorder_moves_only_the_root_cause_lines_and_keeps_their_labels():
    order = [3, 1, 2] + list(range(4, 16))
    out, lines = X.reorder(PROMPT, order)
    assert lines[1] == 3 and lines[2] == 1 and lines[3] == 2 and lines[15] == 15
    assert out.split("**Available Root Causes**:\n")[0] == PROMPT.split("**Available Root Causes**:\n")[0]
    assert out.endswith("\n\nThe top feature changes are\nFeature: x\n")
    assert "1. IDV(3) cause number 3 & Step\n2. IDV(1) cause number 1" in out
    with pytest.raises(ValueError):
        X.reorder(PROMPT, [1, 2, 3])


def test_picks_are_the_first_three_distinct_idv_named():
    assert X.picks("Most likely IDV(6); then IDV (7) or IDV(6) again, IDV( 4 ), IDV(13)") == [6, 7, 4]
    assert X.picks("\\subsubsection{Fault 6 ...} root cause 6 is likely") == []     # 'Fault k' never counts
    assert X.picks("IDV(16) and IDV(0) are not causes; IDV(15)") == [15]


def _fake(policy):
    """policy(lines {line: IDV}, prompt) -> the IDV the fake model names first."""
    def post(url, text, max_tokens, timeout):
        lines = X.root_lines(text)
        first = policy(lines, text)
        rest = [k for k in range(1, 16) if k != first][:2]
        return {"choices": [{"message": {"content": f"I pick IDV({first}), then IDV({rest[0]}) and IDV({rest[1]})."},
                             "finish_reason": "stop"}], "usage": {"prompt_tokens": 100, "completion_tokens": 20},
                "_latency_ms": 5.0}
    return post


def test_a_position_copier_follows_the_line_not_the_content(tmp_path):
    out = tmp_path / "rows.jsonl"
    X.run(_doc(), "http://fake", "m.gguf", "copier", str(out), forms=("app",), post=_fake(lambda lines, t: lines[1]))
    s = X.score(_doc(), [json.loads(x) for x in out.read_text().splitlines()])["copier / app"]
    assert all(o["first_is_line1"] == o["parsed"] == 3 for o in s["orderings"].values())
    for name in ("shuffle_a", "shuffle_b", "line1_last"):
        f = s["follow"][name]
        assert f["n"] == 3 and f["content"] == 0 and f["neither"] == 0 and f["position"] + f["uninformative"] == 3
    assert s["follow"]["line1_last"]["position"] == 3          # line 1 always moves: never uninformative
    assert s["orderings"]["original"]["top1_right"] == 0


def test_a_shuffle_that_keeps_the_pick_on_its_line_is_uninformative():
    base = {"label": "a", "form": "app", "status": "ok", "id": 0, "fault": 6, "ordering": "original",
            "lines": {str(k): k for k in range(1, 16)}, "picks": [6, 7, 4]}
    kept = dict(base, ordering="shuffle_a", lines={**base["lines"], "1": 2, "2": 1}, picks=[6, 1, 2])
    s = X.score(_doc((6,)), [base, kept])["a / app"]["follow"]["shuffle_a"]
    assert s == {"content": 0, "position": 0, "neither": 0, "uninformative": 1, "n": 1}


def test_a_new_pick_on_another_line_is_neither_content_nor_position():
    base = {"label": "a", "form": "app", "status": "ok", "id": 0, "fault": 6, "ordering": "original",
            "lines": {str(k): k for k in range(1, 16)}, "picks": [6, 7, 4]}
    moved = {str(k): k for k in range(1, 16)}
    moved["6"], moved["9"] = 9, 6                              # IDV(6) now on line 9, IDV(9) on line 6
    pos = dict(base, ordering="shuffle_a", lines=moved, picks=[9, 7, 4])      # took what sits on line 6
    other = dict(base, ordering="shuffle_b", lines=moved, picks=[11, 7, 4])   # a cause on neither line
    f = X.score(_doc((6,)), [base, pos, other])["a / app"]["follow"]
    assert f["shuffle_a"]["position"] == 1 and f["shuffle_a"]["neither"] == 0
    assert f["shuffle_b"]["neither"] == 1 and f["shuffle_b"]["position"] == 0


def test_a_reader_keeps_its_answer_under_shuffles_and_is_scored_with_aliases(tmp_path):
    out = tmp_path / "rows.jsonl"
    # reads the fault: names the true fault, except fault 12 where it names its alias 5
    X.run(_doc(), "http://fake", "m.gguf", "reader", str(out), forms=("eval",),
          post=_fake(lambda lines, t: 5 if t.endswith("Fault 12") else int(t.rsplit(" ", 1)[1])))
    s = X.score(_doc(), [json.loads(x) for x in out.read_text().splitlines()])["reader / eval"]
    o = s["orderings"]["original"]
    assert (o["top1_right"], o["top3_right"], o["first_is_fault_number"]) == (3, 3, 2)
    f = s["follow"]["line1_last"]
    assert f["content"] + f["uninformative"] == 3 and f["position"] == 0 and f["neither"] == 0


def test_run_resumes_without_resending_and_records_errors(tmp_path):
    out = tmp_path / "rows.jsonl"
    sent = []

    def post(url, text, max_tokens, timeout):
        sent.append(1)
        if len(sent) == 2:
            raise TimeoutError("slow board")
        return _fake(lambda lines, t: lines[1])(url, text, max_tokens, timeout)
    X.run(_doc(), "u", "m", "a", str(out), forms=("app",), names={"original", "shuffle_a"}, limit=2, post=post)
    rows = [json.loads(x) for x in out.read_text().splitlines()]
    assert len(rows) == 4 and sum(r["status"] == "error" for r in rows) == 1
    X.run(_doc(), "u", "m", "a", str(out), forms=("app",), names={"original", "shuffle_a"}, limit=2, post=post)
    assert len(sent) == 4                               # nothing re-sent, the error row is kept as recorded


@pytest.mark.skipif(not (REPO / "backend" / "test_explain.py").exists(), reason="FaultExplainer checkout not present")
def test_build_reproduces_the_papers_fault_7_evidence_and_the_leak():
    doc = X.build(REPO)
    assert doc["undetected"] == [3, 4, 9, 15]           # arXiv 2412.14492 Table 1: not detected by PCA
    r = next(q for q in doc["requests"] if q["fault"] == 7)
    assert r["top_features"][:4] == ["Stripper Pressure", "A and C Feed", "Reactor Pressure", "Product Sep Pressure"]
    assert "Value Change = -3.00%" in r["prompts"]["app"] and "Value Change = -8.90%" in r["prompts"]["app"]
    assert "\\subsubsection{Fault 7 prompt=root causes included, model=gpt-4o}" in r["prompts"]["eval"]
    assert r["prompts"]["eval"].replace("{Fault 7 prompt", "{Fault N prompt") == r["prompts"]["eval_noleak"]
    assert r["prompts"]["eval"].startswith(r["prompts"]["app"])
