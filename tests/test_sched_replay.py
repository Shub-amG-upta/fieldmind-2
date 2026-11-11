"""bench.sched_replay: the world model on hand-built job streams. Outcomes: when a
call ends, which job runs, when an answer is released."""

import pytest

from bench import sched_replay as R

WORLD = {"alone": {"npu": {"prefill": 1000.0, "decode": 10.0}, "cpu": {"prefill": 100.0, "decode": 10.0}},
         "together_over_alone": {"npu": {"prefill": 0.5, "decode": 0.5}, "cpu": {"prefill": 0.5, "decode": 0.5}}}


def job(jid, agent, side, submit, lane="npu", pre=1000, dec=10, prio=2, followup=None, tick=None):
    return {"job": jid, "agent": agent, "side": side, "priority": prio, "evidence_tick": 1,
            "tick_s": submit if tick is None else tick, "submit_s": submit, "deadline_s": 5.0,
            "lane": lane, "run_s": 0.0, "est": pre, "prefill": pre, "decode": dec, "matched": True,
            "followup_s": followup}


def run(jobs, policy="fixed"):
    out = R.simulate({"wall_tick_s": 5.0, "jobs": jobs}, "v3", "boiler", policy, WORLD)
    return {r["job"]: r for r in out}, out


def test_a_call_alone_takes_its_tokens_over_the_lane_speeds():
    by, _ = run([job("a", "diag_water", "water", 0.0)])
    assert by["a"]["end"] == pytest.approx(1000 / 1000 + 10 / 10)       # 2 s


def test_two_lanes_working_at_once_slow_each_other_while_they_overlap():
    # fixed: diag_water on the npu, the verifier on the cpu; both start at 0
    by, _ = run([job("a", "diag_water", "water", 0.0), job("v", "verifier", "all", 0.0, lane="cpu", pre=100, dec=10)])
    # together both run at half speed: the cpu call (alone 2 s) needs 4 s; the npu call (alone 2 s) also 4 s
    assert by["a"]["end"] == pytest.approx(4.0) and by["v"]["end"] == pytest.approx(4.0)


def test_a_newer_job_replaces_one_still_waiting():
    # b waits behind a; c (same agent and side) arrives before a ends and replaces b
    by, _ = run([job("a", "diag_heat", "heat", 0.0), job("b", "diag_water", "water", 0.5),
                 job("c", "diag_water", "water", 1.0)])
    assert "b" not in by and by["c"]["start"] == pytest.approx(2.0)


def test_a_follow_up_delays_the_release_not_the_call():
    by, _ = run([job("a", "diag_water", "water", 0.0, followup=0.4)])
    assert by["a"]["end"] == pytest.approx(2.0) and by["a"]["release"] == pytest.approx(2.4)



def test_a_call_slows_from_the_moment_the_other_lane_starts():
    # a: 1 s reading + 1 s writing alone; at 1.5 s the cpu starts, so a's last half-second
    # of writing (5 tokens) runs at half speed: it ends at 2.5 s, not 2 s
    by, _ = run([job("a", "diag_water", "water", 0.0),
                 job("v", "verifier", "all", 1.5, lane="cpu", pre=100, dec=10)])
    assert by["a"]["end"] == pytest.approx(2.5)
