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


def _sched(policy, fixed=None, adapt=False):
    lanes = [SimLane("npu", MockBackend(), 1000.0, 10.0), SimLane("cpu", MockBackend(), 100.0, 5.0),
             SimLane("bev", MockBackend(), 2000.0, 10.0, kind="decider")]
    return Scheduler(lanes, {"mode": "lockstep", "placement": policy, "deadlines_s": {},
                             "fixed_placement": fixed or {"diag_water": "npu", "diag_heat": "npu",
                                                          "verifier": "cpu", "bev": "bev"},
                             "adapt_rates": adapt})


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
def _measured_call(adapt):
    sched = _sched("earliest_finish", adapt=adapt)
    rt = RealtimeRunner(sched)
    env = AgentEnvelope(agent="diag_water", tick=1)
    env.calls = [{"status": "ok", "prefill": 400, "decode": 20, "prefill_ms": 1000.0, "decode_ms": 4000.0}]
    j = sched.new_job("diag_water", 1, 2, 50, 0.0, work=lambda: env, side="water", prompt_tokens=400)
    rt.submit(j)
    assert rt.wait_idle(5)
    rt.close()
    return rt


def test_without_adapt_rates_the_lanes_keep_their_planning_rates():
    rt = _measured_call(adapt=False)
    assert rt.rates == {"npu": [1000.0, 10.0], "cpu": [100.0, 5.0], "bev": [2000.0, 10.0]}
    assert rt.telemetry()["adapt_rates"] is False


def test_a_measured_call_moves_the_lane_rate_toward_what_was_measured():
    rt = _measured_call(adapt=True)
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


# ---------------------------------------------------------------- follow-up chaining (explain)
def test_a_follow_up_runs_at_once_and_its_parent_is_released_with_it():
    sched = _sched("fixed")
    rt = RealtimeRunner(sched)
    made = {}

    def followup(result):
        if result.job.agent != "diag_water":
            return None
        f = sched.new_job("bev_explain", result.job.evidence_tick, 3, 0, 0.0,
                          work=lambda: "cites", side="water", prompt_tokens=50)
        made["f"] = f
        return f
    rt.followup = followup
    parent = sched.new_job("diag_water", 7, 2, 50, 0.0, work=lambda: "ranking", side="water")
    rt.submit(parent, tick_wall_s=0.0)
    assert rt.wait_idle(5)
    got = rt.drain()
    rt.close()
    assert [r.job.agent for r in got] == ["diag_water", "bev_explain"]     # released together, parent first
    assert made["f"].lane == "bev" and got[1].evidence_tick == 7
    assert got[1].tick_epoch_s == got[0].tick_epoch_s                      # same wall tick as its parent


def test_a_replaced_follow_up_drops_its_parent_and_the_runner_still_goes_idle():
    sched = _sched("fixed")
    rt = RealtimeRunner(sched)
    _, gate = _blocker(sched, rt, "bev_x")           # hold the bev lane so the follow-up waits
    rt.followup = lambda r: (sched.new_job("bev_explain", r.job.evidence_tick, 3, 0, 0.0, work=lambda: "c",
                                           side="water", prompt_tokens=10)
                             if r.job.agent == "diag_water" else None)
    first = sched.new_job("diag_water", 1, 2, 50, 0.0, work=lambda: "r1", side="water")
    rt.submit(first)
    assert _wait(lambda: len(rt.chained) == 1)
    second = sched.new_job("diag_water", 2, 2, 50, 0.0, work=lambda: "r2", side="water")
    rt.submit(second)                                 # its follow-up replaces the waiting one
    assert _wait(lambda: len(rt.chained) == 1 and next(iter(rt.chained.values())).job is second)
    gate.set()
    assert rt.wait_idle(5)
    agents = [(r.job.agent, r.evidence_tick) for r in rt.drain()]
    rt.close()
    assert ("diag_water", 1) not in agents and ("diag_water", 2) in agents


def test_the_runner_is_not_idle_while_a_finished_job_is_being_handed_on():
    """Between a call ending and its result reaching the done queue (or its follow-up
    being queued) nothing is running or waiting; idle() must still say no, or a final
    wait_idle() + drain() loses that result."""
    sched = _sched("fixed")
    rt = RealtimeRunner(sched)
    inside, release = threading.Event(), threading.Event()

    def followup(result):
        inside.set()
        release.wait(5)
        return None
    rt.followup = followup
    rt.submit(sched.new_job("diag_water", 1, 2, 50, 0.0, work=lambda: "x", side="water"))
    assert inside.wait(5)
    assert rt.idle() is False
    release.set()
    assert rt.wait_idle(5)
    assert [r.job.agent for r in rt.drain()] == ["diag_water"]
    rt.close()


# ---------------------------------------------------------------- calibrated_finish (reports/sched_fix.md)
NO_SLOWDOWN = {"npu": {"prefill": 1.0, "decode": 1.0}, "cpu": {"prefill": 1.0, "decode": 1.0}}
HALF_SPEED = {"npu": {"prefill": 0.5, "decode": 0.5}, "cpu": {"prefill": 0.5, "decode": 0.5}}


def _cal_sched(contention, policy="calibrated_finish"):
    sched = _sched(policy)
    if contention is not None:
        sched.cfg["contention"] = contention
    return sched


def _teach(sched, rt, agent, side, n, decode, prefill=None, est=500):
    """n finished calls of `agent` that wrote `decode` tokens (prefill tokens default: the estimate)."""
    for i in range(n):
        env = AgentEnvelope(agent=agent, tick=i)
        env.calls = [{"status": "ok", "prefill": prefill or est, "decode": decode,
                      "prefill_ms": 100.0, "decode_ms": 100.0}]
        j = sched.new_job(agent, i, 2, 50, 0.0, work=lambda e=env: e, side=side, prompt_tokens=est)
        rt.submit(j)
        assert rt.wait_idle(5)


def test_calibrated_finish_refuses_to_run_without_measured_contention():
    with pytest.raises(ValueError):
        RealtimeRunner(_cal_sched(None))


def test_calibrated_finish_learns_what_an_agent_writes_and_how_far_the_estimate_is_off():
    sched = _cal_sched(NO_SLOWDOWN)
    rt = RealtimeRunner(sched)
    _teach(sched, rt, "diag_water", "water", 15, decode=8, prefill=1000, est=500)
    cal = rt.telemetry()["calibration"]
    rt.close()
    assert cal["answer_tokens"]["diag_water"] == pytest.approx(8, abs=0.5)      # from the cap of 50
    assert cal["prompt_real_over_estimate"] == pytest.approx(2.0, abs=0.05)     # from 1.0


def _busy_npu_choice(policy, contention):
    """The npu holds a job with a 5,000-token prompt and a 200-token cap. Both agents have
    been writing 5 tokens. Where does a new 500-token job with a 50-token cap go?"""
    sched = _cal_sched(contention, policy)
    rt = RealtimeRunner(sched)
    if policy == "calibrated_finish":
        _teach(sched, rt, "diag_heat", "heat", 15, decode=5)
        _teach(sched, rt, "diag_water", "water", 15, decode=5)
    _, gate = _blocker(sched, rt, "diag_heat", prompt=5000, cap=200)
    b = sched.new_job("diag_water", 99, 2, 50, 0.0, work=lambda: "b", side="water", prompt_tokens=500)
    rt.submit(b)
    gate.set()
    assert rt.wait_idle(5)
    rt.close()
    return b.lane


def test_earliest_finish_moves_the_job_to_the_cpu_because_it_charges_the_full_cap():
    # charged at the cap the npu looks busy for 25 s; the cpu (15 s) wins
    assert _busy_npu_choice("earliest_finish", None) == "cpu"


def test_calibrated_finish_keeps_the_job_on_the_npu_once_it_knows_answers_are_short_and_lanes_collide():
    # npu free in about 5 s, then 1 s; the cpu alone 6 s, slower while the npu works: npu wins
    assert _busy_npu_choice("calibrated_finish", HALF_SPEED) == "npu"


def test_without_contention_the_calibrated_cpu_prediction_would_win():
    # the same case with lanes that do not slow each other: the cpu (6 s) beats waiting (6.5 s)
    assert _busy_npu_choice("calibrated_finish", NO_SLOWDOWN) == "cpu"


def test_only_calibrated_finish_records_a_calibration_block():
    for policy in ("earliest_finish", "fixed"):
        rt = RealtimeRunner(_sched(policy))
        assert "calibration" not in rt.telemetry()
        rt.close()


def _prompt_ratio_choice(prefill):
    """Answers are 5 tokens; the npu holds an unlearned job (100-token prompt, 55-token cap,
    about 5.5 s). A new 500-token-estimate job: the cpu reads prompts 10x slower, so how
    far the estimate undercounts decides whether waiting for the npu pays."""
    sched = _cal_sched(NO_SLOWDOWN)
    rt = RealtimeRunner(sched)
    _teach(sched, rt, "diag_water", "water", 15, decode=5, prefill=prefill, est=500)
    _, gate = _blocker(sched, rt, "x", prompt=100, cap=55)
    b = sched.new_job("diag_water", 99, 2, 50, 0.0, work=lambda: "b", side="water", prompt_tokens=500)
    rt.submit(b)
    gate.set()
    assert rt.wait_idle(5)
    rt.close()
    return b.lane


def test_a_prompt_estimate_that_undercounts_makes_the_slow_reading_cpu_lose():
    assert _prompt_ratio_choice(prefill=500) == "cpu"     # estimate right: cpu 6 s vs npu 6.6 s
    assert _prompt_ratio_choice(prefill=1000) == "npu"    # real prompts twice as long: cpu 11 s vs npu 7.2 s
