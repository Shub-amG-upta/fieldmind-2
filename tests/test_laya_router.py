"""bench.run_laya: decider-role calls go to the System One server, everything else to
the mock, and nothing else about a run changes (reports/laya_l1.md, Track A6)."""

import json
from pathlib import Path

import pytest

import bench.harness as harness
from bench import run_laya
from fieldmind.runtime.llm_backend import LLMReply, MockBackend

ROOT = Path(__file__).resolve().parent.parent
EPISODE = ROOT / "data" / "episodes_dev" / "dev_B02_tube_leak_fast"


class _Recorder:
    def __init__(self, tag):
        self.tag, self.roles = tag, []

    def generate(self, prompt, role="generic", max_tokens=512, mock_hint=None):
        self.roles.append(role)
        return LLMReply(text=self.tag)


def test_router_sends_only_decider_role_calls_to_the_server():
    mock, http = _Recorder("mock"), _Recorder("http")
    r = run_laya.RouterBackend(mock, http)
    for role in ("diagnostician", "verifier", "decider", "text_reader", "decider", "query"):
        r.generate("p", role=role)
    assert http.roles == ["decider", "decider"]
    assert mock.roles == ["diagnostician", "verifier", "text_reader", "query"]
    assert r.routed == {"http": 2, "mock": 4}


class _MockDeciderOverHttp:
    """Stands in for the server: answers a decider call exactly as the mock would, so
    a routed run must reproduce the plain mock run tick for tick."""
    def __init__(self):
        self.calls = 0

    def generate(self, prompt, role="generic", max_tokens=512, mock_hint=None):
        self.calls += 1
        hint = mock_hint or {}
        body = MockBackend._mock_bev(hint) if "bev" in hint else MockBackend._mock_decider(hint)
        return LLMReply(text=json.dumps(body), backend="bev", model="stub", decode_tokens=0)


def _decisions(run):
    return [(a["tick"], a["state"], [h.get("case_ref") for h in a["hypotheses"]],
             [x.get("id") for x in a["actions"]], a["escalate"]) for a in run["assessments"]]


def _run(overlay, monkeypatch, stub=None):
    import run_demo
    cfg = run_demo.load_config(str(ROOT / "configs" / "base.yaml"), "mock",
                               ",".join(str(ROOT / "configs" / o) for o in overlay))
    if stub is not None:
        original = harness.make_backend
        monkeypatch.setattr(harness, "make_backend",
                            lambda llm: run_laya.RouterBackend(original(llm), stub))
    return harness.run_episode(harness.Episode(EPISODE), cfg, arch="multi")


@pytest.mark.skipif(not EPISODE.exists(), reason="dev episodes not generated")
def test_routed_run_with_the_decider_reproduces_the_plain_run(monkeypatch):
    plain = _run(["bev3.yaml"], monkeypatch)
    stub = _MockDeciderOverHttp()
    routed = _run(["bev3.yaml"], monkeypatch, stub)
    assert stub.calls > 0                                   # the decider's calls did go through the router
    assert _decisions(routed) == _decisions(plain)


@pytest.mark.skipif(not EPISODE.exists(), reason="dev episodes not generated")
def test_routed_run_with_bev_off_never_calls_the_server(monkeypatch):
    plain = _run(["v3.yaml"], monkeypatch)
    stub = _MockDeciderOverHttp()
    routed = _run(["v3.yaml"], monkeypatch, stub)
    assert stub.calls == 0
    assert _decisions(routed) == _decisions(plain)


def test_install_refuses_a_real_backend(monkeypatch):
    monkeypatch.setattr(harness, "make_backend", lambda llm: object())
    run_laya.install("http://127.0.0.1:1")
    with pytest.raises(SystemExit):
        harness.make_backend({"backend": "llamaserver"})
