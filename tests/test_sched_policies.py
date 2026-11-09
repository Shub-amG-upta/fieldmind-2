"""Real-time scheduling policies (plan "Scheduler", Phase 5; reports/sched_stage_a.md):
priority order inside a lane, the four placement policies, measured-rate updates and
deadline accounting in ticks. Outcomes only: which job ran first, which lane a job got,
what the run recorded."""

import threading
import time

import pytest

from fieldmind.multi.lanes import SimLane
from fieldmind.multi.realtime import RATE_EWMA, RealtimeRunner
from fieldmind.multi.scheduler import Scheduler
from fieldmind.runtime.llm_backend import MockBackend
from fieldmind.schemas import AgentEnvelope


def _sched(policy, fixed=None):
    lanes = [SimLane("npu", MockBackend(), 1000.0, 10.0), SimLane("cpu", MockBackend(), 100.0, 5.0),
             SimLane("bev", MockBackend(), 2000.0, 10.0, kind="decider")]
    return Scheduler(lanes, {"mode": "lockstep", "placement": policy, "deadlines_s": {},
                             "fixed_placement": fixed or {"diag_water": "npu", "diag_heat": "npu",
                                                          "verifier": "cpu", "bev": "bev"}})


def _wait(pred, timeout=5.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if pred():
            return True
        time.sleep(0.005)
    return False


def _blocker(sched, rt, lane_agent, tick=1, prompt=500, cap=50):
    """A job that holds its lane until released."""
    gate = threading.Event()
    j = sched.new_job(lane_agent, tick, 2, cap, 0.0, work=lambda: (gate.wait(5), "held")[1],
                      side="block", prompt_tokens=prompt)
    rt.submit(j)
    assert _wait(lambda: rt.running.get(j.lane) is j)
    return j, gate


# ---------------------------------------------------------------- priority inside a lane
def test_a_p1_job_runs_before_an_earlier_waiting_p3_job_on_the_same_lane():
    sched = _sched("fixed", {"diag_water": "npu", "verifier": "npu", "x": "npu", "bev": "bev"})
    rt = RealtimeRunner(sched)
    order = []
    _, gate = _blocker(sched, rt, "x")
    p3 = sched.new_job("verifier", 2, 3, 30, 0.0, work=lambda: order.append("P3"), side="all")
    p1 = sched.new_job("diag_water", 2, 1, 60, 0.0, work=lambda: order.append("P1"), side="water")
    rt.submit(p3)
    rt.submit(p1)
    gate.set()
    assert rt.wait_idle(5)
    rt.close()
    assert order == ["P1", "P3"]


# ---------------------------------------------------------------- placement policies
def test_earliest_finish_takes_the_idle_fast_lane_then_moves_off_it_when_it_is_busy():
    sched = _sched("earliest_finish")
    rt = RealtimeRunner(sched)
    # npu: 500/1000 + 50/10 = 5.5 s; cpu: 500/100 + 50/5 = 15 s
    a = sched.new_job("diag_water", 1, 2, 50, 0.0, work=lambda: "a", side="water", prompt_tokens=500)
    rt.submit(a)
    assert a.lane == "npu"
    assert rt.wait_idle(5)
    # a long call on the npu (5000/1000 + 200/10 = 25 s predicted) makes the cpu earlier
    _, gate = _blocker(sched, rt, "diag_heat", prompt=5000, cap=200)
    b = sched.new_job("diag_water", 2, 2, 50, 0.0, work=lambda: "b", side="water", prompt_tokens=500)
    rt.submit(b)
    assert b.lane == "cpu"
    gate.set()
    assert rt.wait_idle(5)
    rt.close()


def test_earliest_finish_refuses_a_job_without_a_prompt_size():
    sched = _sched("earliest_finish")
    rt = RealtimeRunner(sched)
    j = sched.new_job("diag_water", 1, 2, 50, 0.0, work=lambda: "x", side="water")
    with pytest.raises(ValueError):
        rt.submit(j)
    rt.close()


def test_tick_alternation_puts_odd_ticks_on_the_npu_and_even_ticks_on_the_cpu():
    sched = _sched("tick_alternation")
    rt = RealtimeRunner(sched)
    lanes = {}
    for tick in (3, 4, 5, 6):
        j = sched.new_job("diag_water", tick, 2, 50, 0.0, work=lambda: "x", side=f"s{tick}",
                          prompt_tokens=100)
        rt.submit(j)
        lanes[tick] = j.lane
    assert rt.wait_idle(5)
    rt.close()
    assert lanes == {3: "npu", 4: "cpu", 5: "npu", 6: "cpu"}


def test_priority_reserved_keeps_the_npu_for_urgent_work():
    sched = _sched("priority_reserved")
    rt = RealtimeRunner(sched)
    # with no P1 anywhere, a P2 job goes to the earlier lane (the npu)
    a = sched.new_job("diag_water", 1, 2, 50, 0.0, work=lambda: "a", side="water", prompt_tokens=500)
    rt.submit(a)
    assert a.lane == "npu"
    assert rt.wait_idle(5)
    # a P1 is running: a P2 job is kept off the npu even though the npu would be earlier
    gate = threading.Event()
    p1 = sched.new_job("diag_heat", 2, 1, 50, 0.0, work=lambda: (gate.wait(5), "p1")[1],
                       side="heat", prompt_tokens=10)
    rt.submit(p1)
    assert p1.lane == "npu" and _wait(lambda: rt.running["npu"] is p1)
    b = sched.new_job("diag_water", 2, 2, 50, 0.0, work=lambda: "b", side="water", prompt_tokens=10)
    rt.submit(b)
    assert b.lane == "cpu"
    gate.set()
    assert rt.wait_idle(5)
    rt.close()


def test_decision_model_jobs_keep_their_own_lane_under_every_policy():
    for policy in ("earliest_finish", "tick_alternation", "priority_reserved"):
        sched = _sched(policy)
        rt = RealtimeRunner(sched)
        j = sched.new_job("bev_explain", 4, 3, 0, 0.0, work=lambda: "x", side="water", prompt_tokens=100)
        rt.submit(j)
        assert j.lane == "bev", policy
        assert rt.wait_idle(5)
        rt.close()


# ---------------------------------------------------------------- measured rates
def test_a_measured_call_moves_the_lane_rate_toward_what_was_measured():
    sched = _sched("earliest_finish")
    rt = RealtimeRunner(sched)
    env = AgentEnvelope(agent="diag_water", tick=1)
    env.calls = [{"status": "ok", "prefill": 400, "decode": 20, "prefill_ms": 1000.0, "decode_ms": 4000.0}]
    j = sched.new_job("diag_water", 1, 2, 50, 0.0, work=lambda: env, side="water", prompt_tokens=400)
    rt.submit(j)
    assert rt.wait_idle(5)
    rt.close()
    pre, dec = rt.rates["npu"]
    # measured 400 tok/s prefill and 5 tok/s decode; planning rates 1000 and 10
    assert pre == pytest.approx((1 - RATE_EWMA) * 1000 + RATE_EWMA * 400)
    assert dec == pytest.approx((1 - RATE_EWMA) * 10 + RATE_EWMA * 5)
    assert rt.rates["cpu"] == [100.0, 5.0]                     # untouched lane


# ---------------------------------------------------------------- deadlines in ticks
class _Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def test_deadlines_are_counted_in_ticks_of_the_wall_clock():
    clock = _Clock()
    sched = _sched("fixed")
    rt = RealtimeRunner(sched, clock=clock, wall_tick_s=10.0, deadline_ticks={1: 1 / 3, 2: 1.0, 3: 2.0})

    def finish_at(t):
        def work():
            clock.t = t
            return "x"
        return work
    on_time = sched.new_job("diag_water", 1, 2, 50, 0.0, work=finish_at(9.0), side="water")
    late = sched.new_job("verifier", 1, 3, 30, 0.0, work=finish_at(25.0), side="all")
    rt.submit(on_time, tick_wall_s=0.0)        # P2: 1 tick = 10 s; done 9 s after its tick
    assert rt.wait_idle(5)
    rt.submit(late, tick_wall_s=0.0)           # P3: 2 ticks = 20 s; done 25 s after its tick
    assert rt.wait_idle(5)
    rt.close()
    spans = {s["job"]: s for s in rt.telemetry()["spans"]}
    assert spans[on_time.job_id]["met"] is True and spans[on_time.job_id]["age_ticks"] == pytest.approx(0.9)
    assert spans[late.job_id]["met"] is False and spans[late.job_id]["deadline_s"] == pytest.approx(20.0)
    t = rt.telemetry()["deadline"]
    assert t == {"P2": {"n": 1, "missed": 0}, "P3": {"n": 1, "missed": 1}}
