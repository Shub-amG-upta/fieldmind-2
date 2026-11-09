"""The crash-safe call log and resume. Each test fails if the rule it names is broken."""
import json
from pathlib import Path

import pytest

from bench.call_journal import (BoardConnectionLost, CallJournal, JournalBackend,
                                ResumeDiverged, read_records)
from bench.harness import Episode, run_episode
from bench.stage_monitor_multi import episode_dir
from fieldmind.runtime.llm_backend import LLMReply
from run_demo import load_config

ROOT = Path(__file__).resolve().parent.parent
EP = ROOT / "data/episodes_cranfield_dev/cf_F5_5.1_slugging_conditions"
needs_ep = pytest.mark.skipif(not EP.exists(), reason="Cranfield episodes not built")


class Fake:
    name = "fake"
    model_file = "fake.gguf"

    def __init__(self, status="ok", error=""):
        self.calls, self.status, self.error = 0, status, error

    def generate(self, prompt, role="generic", max_tokens=512, mock_hint=None):
        self.calls += 1
        return LLMReply(text=f"answer {self.calls}", status=self.status, error=self.error,
                        latency_ms=1234.5, prefill_tokens=10, decode_tokens=5)

    def close(self):
        pass


def _backend(path, inner=None):
    j = CallJournal(path)
    return JournalBackend(inner or Fake(), "npu", j), j


def test_answer_is_on_disk_when_the_agent_gets_it(tmp_path):
    p = tmp_path / "c.jsonl"
    b, _ = _backend(p)
    reply = b.generate("q")
    assert [r["reply"]["text"] for r in read_records(p) if r["event"] == "done"] == [reply.text]


def test_resume_replays_without_calling_and_keeps_the_timing(tmp_path):
    p = tmp_path / "c.jsonl"
    b, j = _backend(p)
    b.generate("q1"), b.generate("q2")
    j.close()
    fresh = Fake()
    b2, j2 = _backend(p, fresh)
    r1, r2 = b2.generate("q1"), b2.generate("q2")
    assert fresh.calls == 0 and (r1.text, r2.text) == ("answer 1", "answer 2")
    assert r1.latency_ms == 1234.5
    r3 = b2.generate("q3")
    assert fresh.calls == 1 and r3.text == "answer 1"
    assert j2.summary() == {"sessions": 2, "replayed_calls": 2, "live_calls": 1, "resumed": True,
                            "calls_recorded_failed_after_server_death": 0}


def test_a_different_prompt_on_resume_stops_the_run(tmp_path):
    p = tmp_path / "c.jsonl"
    b, j = _backend(p)
    b.generate("q1")
    j.close()
    b2, _ = _backend(p)
    with pytest.raises(ResumeDiverged):
        b2.generate("other prompt")


def test_a_torn_last_line_is_dropped_and_the_log_stays_whole(tmp_path):
    p = tmp_path / "c.jsonl"
    b, j = _backend(p)
    b.generate("q1")
    j.close()
    with p.open("a") as f:
        f.write('{"event": "done", "key": "abc", "rep')
    fresh = Fake()
    b2, j2 = _backend(p, fresh)
    assert b2.generate("q1").text == "answer 1" and fresh.calls == 0
    b2.generate("q2")
    j2.close()
    for line in p.read_text().splitlines():
        json.loads(line)


def test_a_lost_connection_stops_the_run_and_is_not_logged(tmp_path):
    p = tmp_path / "c.jsonl"
    b, _ = _backend(p, Fake(status="error", error="connection: [Errno 111] refused"))
    with pytest.raises(BoardConnectionLost, match="Connection refused"):
        b.generate("q")
    assert not [r for r in read_records(p) if r["event"] == "done"]


def test_a_real_timeout_on_a_healthy_or_urlless_lane_stays_a_result(tmp_path):
    p = tmp_path / "c.jsonl"
    b, _ = _backend(p, Fake(status="timeout", error="llama-server exceeded 120s"))
    assert b.generate("q").status == "timeout"
    assert [r for r in read_records(p) if r["event"] == "done"]


def test_cranfield_episodes_resolve_to_their_own_folders():
    assert episode_dir("cf_F5_5.1_slugging_conditions").parent.name == "episodes_cranfield_dev"
    assert episode_dir("cf_F5_5.2_slugging_conditions").parent.name == "episodes_cranfield"
    assert episode_dir("ep_A01_fcv_seize").parent.name == "episodes"
    assert episode_dir("dev_A01_fcv_seize").parent.name == "episodes_dev"


def _ranks(run):
    return [(a["tick"], a["state"], a["triage"], [h.get("case_ref") for h in a.get("hypotheses") or []],
             a.get("confidence")) for a in run["assessments"]]


@needs_ep
def test_cut_and_resumed_run_publishes_exactly_what_an_uncut_run_does(tmp_path):
    from bench.call_journal import wrap_lane_with
    cfg = lambda: load_config(str(ROOT / "configs/base.yaml"), "mock",
                              f"{ROOT}/configs/v3.yaml,{ROOT}/configs/cranfield.yaml")
    whole = run_episode(Episode(EP), cfg(), arch="multi")

    class Cut(Exception):
        pass

    p = tmp_path / "c.jsonl"
    seen = []

    def stop_at(d):
        seen.append(d["tick"])
        if len(seen) == 30:
            raise Cut()

    j = CallJournal(p)
    with pytest.raises(Cut):
        run_episode(Episode(EP), cfg(), arch="multi", wrap_lane=wrap_lane_with(j), on_assessment=stop_at)
    j.close()
    n_logged = sum(r["event"] == "done" for r in read_records(p))
    assert n_logged > 0

    j2 = CallJournal(p)
    resumed = run_episode(Episode(EP), cfg(), arch="multi", wrap_lane=wrap_lane_with(j2))
    j2.close()
    assert _ranks(resumed) == _ranks(whole)
    assert j2.replayed == n_logged and j2.live > 0


class Dies(Fake):
    def generate(self, prompt, role="generic", max_tokens=512, mock_hint=None):
        self.calls += 1
        raise ConnectionResetError("server gone")


def test_a_call_that_kills_the_server_twice_becomes_a_failed_call_and_replays(tmp_path):
    p = tmp_path / "c.jsonl"
    for _ in range(2):
        b, j = _backend(p, Dies())
        with pytest.raises(ConnectionResetError):
            b.generate("bad")
        j.close()
    untouched = Fake()
    b, j = _backend(p, untouched)
    r = b.generate("bad")
    assert r.status == "error" and untouched.calls == 0 and j.summary()["calls_recorded_failed_after_server_death"] == 1
    assert b.generate("next").status == "ok"
    j.close()
    again = Fake()
    b, j = _backend(p, again)
    assert b.generate("bad").status == "error" and b.generate("next").text == "answer 1" and again.calls == 0


def test_one_death_is_tried_again(tmp_path):
    p = tmp_path / "c.jsonl"
    b, j = _backend(p, Dies())
    with pytest.raises(ConnectionResetError):
        b.generate("q")
    j.close()
    live = Fake()
    b, _ = _backend(p, live)
    assert b.generate("q").status == "ok" and live.calls == 1
