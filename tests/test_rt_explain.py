"""explain in real time (reports/sched_stage_a.md): with an instant mock model, every side
answer real time composes from Llama's ranking and the decision model's picks equals the
one lockstep composed for the same evidence tick and side. Which ticks call the model can
differ (answers fold one tick later in real time; on dev_B02 only 4 of 18 overlap), so the
check is identity on the overlap, which must be most of lockstep's answers on dev_B01."""

import json
from pathlib import Path

import pytest

import bench.harness as H
import run_demo

ROOT = Path(__file__).resolve().parent.parent
EP = ROOT / "data" / "episodes_dev" / "dev_B01_tube_leak"


def _run(mode):
    cfg = run_demo.load_config(str(ROOT / "configs/base.yaml"), "mock", str(ROOT / "configs/bev_ideas.yaml"))
    run_demo.apply_bev(cfg, "explain=on,clear_skip=on")
    return H.run_episode(H.Episode(EP), cfg, arch="multi", mode=mode,
                         tick_s=0.05 if mode == "realtime" else None)


def _composed(run):
    out = {}
    for a in run["assessments"]:
        for c in (a.get("multi") or {}).get("compact", []):
            if c.get("agent") == "bev" and c.get("idea") == "explain" and "composed" in c:
                out[(c["evidence_tick"], c.get("side"))] = json.dumps(c["composed"], sort_keys=True)
    return out


@pytest.mark.skipif(not EP.exists(), reason="dev episodes not generated")
def test_real_time_explain_composes_what_lockstep_composes():
    lock, rt = _composed(_run("lockstep")), _composed(_run("realtime"))
    both = set(lock) & set(rt)
    assert len(both) >= 0.8 * len(lock) > 0
    assert all(lock[k] == rt[k] for k in both)
    # the decision model's picks reached the answer: a ranking folded without its
    # follow-up carries no citations at all
    assert sum(any(c for _, c in json.loads(rt[k])["r"]) for k in both) >= 0.8 * len(both)


@pytest.mark.skipif(not EP.exists(), reason="dev episodes not generated")
def test_a_late_follow_up_still_cites_when_its_side_answer_is_accepted(monkeypatch):
    """A slow decision lane (3 wall ticks per call): rankings and their follow-ups
    arrive two or more ticks after their evidence. fold_sides accepts such an answer
    while the side's evidence is unchanged; its follow-up must be used with it, not
    dropped by a stricter one-tick rule (which would leave the answer uncited)."""
    import time
    from fieldmind.multi.agents.bev import BevAgent
    slow = BevAgent._call

    def call(self, *a, **k):
        time.sleep(0.15)
        return slow(self, *a, **k)
    monkeypatch.setattr(BevAgent, "_call", call)
    run = _run("realtime")
    late = []
    for a in run["assessments"]:
        for c in (a.get("multi") or {}).get("compact", []):
            if c.get("agent") == "bev" and c.get("idea") == "explain" and "composed" in c \
                    and a["tick"] - c["evidence_tick"] >= 2:
                late.append(any(cs for _, cs in c["composed"]["r"]))
    assert len(late) >= 5
    assert sum(late) >= 0.8 * len(late)


A02 = ROOT / "data" / "episodes_dev" / "dev_A02_fcv_seize_fast"


@pytest.mark.skipif(not A02.exists(), reason="dev episodes not generated")
def test_hybrid_runs_in_real_time_on_every_tick_lockstep_runs_it():
    """The merge rule in real time (A3): the gate publishes hybrid's ranking on every
    non-quiet tick, and its regime (read from belief alone) is the lockstep one."""
    def rules(mode):
        cfg = run_demo.load_config(str(ROOT / "configs/base.yaml"), "mock", str(ROOT / "configs/v3.yaml"))
        run = H.run_episode(H.Episode(A02), cfg, arch="multi", mode=mode,
                            tick_s=0.05 if mode == "realtime" else None)
        return {a["tick"]: c for a in run["assessments"]
                for c in (a.get("multi") or {}).get("compact", []) if c.get("agent") == "rule"}
    lock, rt = rules("lockstep"), rules("realtime")
    assert len(lock) > 40 and set(rt) == set(lock)
    assert {c["rule"] for c in rt.values()} == {"hybrid"}
    assert all(rt[t]["regime"] == lock[t]["regime"] for t in lock)
