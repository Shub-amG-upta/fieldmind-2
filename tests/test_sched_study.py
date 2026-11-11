"""The scheduling study runner (bench/sched_study.py) and the benchmark runner's
real-time settings. Outcomes: what a saved run used and recorded, what the
table recounts from spans, and what the board runner refuses."""

import argparse
import gzip
import json
from pathlib import Path

import pytest

import bench.benchmark as B
import bench.sched_study as S
from fieldmind.multi.realtime import summarize
from tests.test_benchmark import bench

ROOT = Path(__file__).resolve().parent.parent
needs_dev = pytest.mark.skipif(not (ROOT / "data/episodes_dev/dev_B01_tube_leak").exists(),
                               reason="dev episodes not generated")


@pytest.fixture(scope="module")
def alternation_run(tmp_path_factory):
    root = tmp_path_factory.mktemp("sched")
    p = bench(root, "s", "dev_B01_tube_leak", "--backend", "mock", "--plain", "--mode", "realtime",
              "--tick-s", "0.03", "--overlay", "configs/v3.yaml,configs/sched_study.yaml",
              "--placement", "tick_alternation")
    assert p.returncode == 0, p.stdout[-2000:] + p.stderr[-2000:]
    d = root / "s"
    run = json.loads(gzip.decompress((d / "dev_B01_tube_leak_multi.run.json.gz").read_bytes()))
    return d, run


@needs_dev
def test_the_policy_named_on_the_command_line_is_the_one_the_run_used(alternation_run):
    d, run = alternation_run
    rt = run["multi"]["realtime"]
    assert rt["policy"] == "tick_alternation"
    assert json.loads((d / "test.json").read_text())["params"]["placement"] == "tick_alternation"
    llm = [s for s in rt["spans"] if s["lane"] in ("npu", "cpu")]
    assert {s["lane"] for s in llm} == {"npu", "cpu"}
    assert all(s["lane"] == ("npu" if s["evidence_tick"] % 2 else "cpu") for s in llm)


@needs_dev
def test_the_sweep_overlap_equals_the_runners_own_count(alternation_run):
    """Independent route: a start/end event sweep (sched_study) against the
    runner's pairwise interval overlap (realtime.summarize), same spans."""
    _, run = alternation_run
    spans = run["multi"]["realtime"]["spans"]
    a = S._overlap_s(spans, "npu", "cpu")
    b = summarize(spans)["both_lanes_busy_s"]
    assert a == pytest.approx(b, abs=1e-3)


def test_deadline_misses_are_recounted_from_the_spans():
    spans = [  # wall tick 10 s; P2 deadline 10 s, P3 20 s
        {"lane": "npu", "priority": 2, "tick_s": 0.0, "start_s": 1.0, "end_s": 9.0, "deadline_s": 10.0},
        {"lane": "npu", "priority": 2, "tick_s": 10.0, "start_s": 12.0, "end_s": 21.0, "deadline_s": 10.0},
        {"lane": "cpu", "priority": 3, "tick_s": 0.0, "start_s": 2.0, "end_s": 25.0, "deadline_s": 20.0},
        {"lane": "cpu", "priority": 4, "tick_s": 0.0, "start_s": 2.0, "end_s": 99.0, "deadline_s": None},
    ]
    run = {"multi": {"realtime": {"wall_tick_s": 10.0, "spans": spans}}, "n_ticks": 3}
    m = S.run_metrics(run, {})
    assert m["deadline"]["P2"] == {"n": 2, "missed": 1}
    assert m["deadline"]["P3"] == {"n": 1, "missed": 1}
    assert m["calls"] == {"npu": 2, "cpu": 2}
    assert sorted(m["ages"]) == pytest.approx([0.9, 1.1, 2.5, 9.9])


def test_the_matrix_is_what_was_registered():
    """Amendment 1: 4 lockstep references, then a speed sweep, slowest first:
    2 configs x 2 policies x 4 loads x 2 plants."""
    cells = S.cells()
    names = [c["name"] for c in cells]
    assert len(names) == len(set(names)) == 4 + 2 * 2 * 4 * 2
    assert all(c["mode"] == "lockstep" for c in cells[:4])
    sweep = cells[4:]
    assert all(c["mode"] == "realtime" for c in sweep)
    assert [c["tick_s"] for c in sweep[::8]] == [5.0, 4.0, 3.0, 2.0]
    assert {c["policy"] for c in sweep} == {"fixed", "earliest_finish"}
    assert all(c["name"].endswith("_dry") and c["run_tick_s"] == 0.05 for c in S.cells(0.05)[4:])
    cmd = S.command(cells[-1], "llamaserver")
    assert "--placement" in cmd and "--backend" not in cmd and cmd[cmd.index("--tick-s") + 1] == "2"


def test_capacity_is_the_fastest_load_kept_up_without_a_gap():
    keep = S.KEEP_UP_P2_MISS
    assert S.capacity({5.0: 0.0, 4.0: keep, 3.0: keep + 0.01, 2.0: 0.0}) == 4.0   # no claim past a failure
    assert S.capacity({5.0: 0.0, 4.0: None, 3.0: 0.0, 2.0: 0.0}) == 5.0           # nor past a gap
    assert S.capacity({5.0: 0.5, 4.0: 0.0, 3.0: 0.0, 2.0: 0.0}) is None
    assert S.capacity({5.0: 0.0, 4.0: 0.0, 3.0: 0.0, 2.0: 0.0}) == 2.0


def _args(**kw):
    base = dict(arch="multi", overlay="configs/v3.yaml,configs/sched_study.yaml", merge_rule=None,
                placement="earliest_finish", bev=None, mode="realtime", tick_s=5.0,
                backend="llamaserver", no_prompts=False, bev_device="npu")
    base.update(kw)
    return argparse.Namespace(**base)


def test_the_board_runner_refuses_real_time_with_unmeasured_lane_rates(tmp_path):
    # its own overlay: the live configs/sched_study.yaml has measured rates since 2026-11-10
    unmeasured = tmp_path / "unmeasured.yaml"
    unmeasured.write_text("multi:\n  lane_rates_measured: false\n")
    ov = f"configs/v3.yaml,configs/sched_study.yaml,{unmeasured}"
    with pytest.raises(SystemExit, match="not measured"):
        B.settings(_args(overlay=ov))
    cfg, params = B.settings(_args(overlay=ov, backend="mock"))   # plumbing on the laptop is allowed
    assert cfg["multi"]["placement"] == "earliest_finish" and params["placement"] == "earliest_finish"
    assert cfg["multi"]["merge_rule"] == "hybrid"           # real time runs the best system's rule


class _FakeLane:
    """A stand-in llama-server: /v1/chat/completions answers after `busy_s`,
    reporting fixed timings; records when each call ran."""

    def __init__(self, prefill, decode, busy_s=0.05):
        import http.server
        import threading
        lane = self
        self.spans = []
        self.lock = threading.Lock()

        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"]))
                import time
                t0 = time.monotonic()
                time.sleep(busy_s)
                with lane.lock:
                    lane.spans.append((t0, time.monotonic()))
                body = json.dumps({"model": "m.gguf", "timings": {
                    "prompt_n": 100, "predicted_n": 20, "prompt_per_second": prefill,
                    "predicted_per_second": decode, "prompt_ms": 100 / prefill * 1000}}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)

        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()


def test_lane_rates_reports_each_lane_alone_and_both_at_once():
    a, b = _FakeLane(800.0, 16.0), _FakeLane(120.0, 9.0)
    res = S.lane_rates({"npu": a.url, "cpu": b.url}, ["p1", "p2", "p3"])
    a.srv.shutdown()
    b.srv.shutdown()
    assert res["alone"]["npu"]["prefill_tok_s"] == 800.0 and res["alone"]["cpu"]["decode_tok_s"] == 9.0
    assert res["alone"]["npu"]["n"] == 3 and len(res["samples"]["together"]["cpu"]) == 3
    assert res["together_over_alone"]["npu"] == {"prefill_tok_s": 1.0, "decode_tok_s": 1.0}
    assert res["models"] == {"npu": ["m.gguf"], "cpu": ["m.gguf"]}
    # alone: never both lanes at once; together: each of the 3 prompts on both at once
    overlaps = sum(1 for x in a.spans for y in b.spans if x[0] < y[1] and y[0] < x[1])
    assert overlaps == 3


# ---- answers released with their follow-up (PLAN_LAPTOP_ECHO_SCHED.md stage 1 step 3)

def _span(job, agent, lane, prio, tick_s, start, end, side="water", ev=10, submit=None, deadline=2.0, **kw):
    return {"job": job, "agent": agent, "lane": lane, "priority": prio, "side": side,
            "evidence_tick": ev, "tick_s": tick_s, "submit_s": start if submit is None else submit,
            "start_s": start, "end_s": end, "deadline_s": deadline, **kw}


def _rt_run(spans):
    return {"multi": {"realtime": {"spans": spans, "wall_tick_s": 5.0}}, "n_ticks": 1}


def test_a_call_is_late_when_its_follow_up_finishes_after_the_deadline():
    # the call ends at 1.5 s (inside 2.0 s); its follow-up ends at 2.4 s: the answer is late
    spans = [_span("j1", "diag_water", "npu", 1, 0.0, 0.1, 1.5),
             _span("j2", "bev_explain", "bev", 3, 0.0, 1.5003, 2.4, submit=1.5003, deadline=10.0)]
    m = S.run_metrics(_rt_run(spans), {})
    assert m["deadline"]["P1"] == {"n": 1, "missed": 0}      # judged at the call's own end
    assert m["released"]["P1"] == {"n": 1, "missed": 1}      # judged when the answer is handed on
    assert m["released"]["P3"] == {"n": 0, "missed": 0}      # the follow-up is not counted again


def test_a_call_without_follow_up_is_judged_at_its_own_end():
    spans = [_span("j1", "diag_water", "npu", 2, 0.0, 0.1, 2.5)]
    m = S.run_metrics(_rt_run(spans), {})
    assert m["released"]["P2"] == {"n": 1, "missed": 1} == m["deadline"]["P2"]


def test_recorded_parent_links_win_over_matching():
    # submitted long after the call ended: matching would refuse it, the record links it
    spans = [_span("j1", "diag_water", "npu", 1, 0.0, 0.1, 1.0, parent=None),
             _span("j2", "bev_explain", "bev", 3, 0.0, 1.9, 2.1, submit=1.9, deadline=10.0, parent="j1")]
    assert S.followups(spans) == {"j1": spans[1]}


def test_matching_refuses_a_follow_up_with_no_call_or_two():
    lone = [_span("j2", "bev_explain", "bev", 3, 0.0, 1.0, 1.2, deadline=10.0)]
    with pytest.raises(ValueError):
        S.followups(lone)
    two = [_span("j1", "diag_water", "npu", 1, 0.0, 0.1, 1.0),
           _span("j3", "diag_water", "cpu", 1, 0.0, 0.2, 1.0),
           _span("j2", "bev_explain", "bev", 3, 0.0, 1.0001, 1.2, submit=1.0001, deadline=10.0)]
    with pytest.raises(ValueError):
        S.followups(two)


@needs_dev
def test_realtime_records_each_follow_ups_call_and_matching_agrees(tmp_path):
    p = bench(tmp_path, "x", "dev_A02_fcv_seize_fast", "--backend", "mock", "--plain", "--mode", "realtime",
              "--tick-s", "0.05", "--overlay", S.overlay("v3x", "boiler"), "--bev", "explain=on,clear_skip=on")
    assert p.returncode == 0, p.stdout[-2000:] + p.stderr[-2000:]
    run = json.loads(gzip.decompress((tmp_path / "x" / "dev_A02_fcv_seize_fast_multi.run.json.gz").read_bytes()))
    spans = run["multi"]["realtime"]["spans"]
    kids = [s for s in spans if s["agent"] == "bev_explain"]
    assert kids, "the v3x mock run made no follow-up"
    jobs = {s["job"]: s for s in spans}
    assert all(jobs[k["parent"]]["agent"].startswith("diag_") for k in kids)
    assert all(s["parent"] is None for s in spans if s["agent"] != "bev_explain")
    recorded = S.followups(spans)
    matched = S.followups([{k: v for k, v in s.items() if k != "parent"} for s in spans])
    assert {c: k["job"] for c, k in recorded.items()} == {c: k["job"] for c, k in matched.items()}


def test_matching_needs_the_same_side_and_an_immediate_submit():
    calls = [_span("jw", "diag_water", "npu", 1, 0.0, 0.1, 1.0, side="water"),
             _span("jh", "diag_heat", "cpu", 1, 0.0, 0.2, 1.0, side="heat")]
    heat_kid = _span("k1", "bev_explain", "bev", 3, 0.0, 1.0002, 1.3, side="heat", submit=1.0002, deadline=10.0)
    assert {c: k["job"] for c, k in S.followups(calls + [heat_kid]).items()} == {"jh": "k1"}
    late = _span("k2", "bev_explain", "bev", 3, 0.0, 1.2, 1.5, side="water", submit=1.2, deadline=10.0)
    with pytest.raises(ValueError):                  # 0.2 s after the call: not its follow-up
        S.followups(calls + [late])


# ---- in-situ lane behaviour (bench.sched_study insitu; the calibrated policy's constants)

def _insitu_run():
    # npu call j1 alone (0-2 s); npu call j2 and cpu call j3 both run 10-12 s (fully overlapped)
    spans = [_span("j1", "diag_water", "npu", 2, 0.0, 0.0, 2.0, ev=1),
             _span("j2", "diag_water", "npu", 2, 10.0, 10.0, 12.0, ev=2),
             _span("j3", "diag_heat", "cpu", 2, 10.0, 10.0, 12.0, side="heat", ev=2)]
    for s in spans:
        s["run_s"] = s["end_s"] - s["start_s"]
    def call(lat, pre, pre_ms, dec, dec_ms):
        return {"status": "ok", "latency_ms": lat * 1000, "prefill": pre, "prefill_ms": pre_ms,
                "decode": dec, "decode_ms": dec_ms}
    assessments = [
        {"tick": 1, "envelopes": [{"backend": "npu", "tick": 1, "calls": [call(2.0, 1000, 1000, 20, 1000)]}],
         "multi": {"results": [{"job_id": "j1", "prompt_tokens": 800}]}},
        {"tick": 2, "envelopes": [{"backend": "npu", "tick": 2, "calls": [call(2.0, 500, 1000, 10, 1000)]},
                                  {"backend": "cpu", "tick": 2, "calls": [call(2.0, 100, 1000, 5, 1000)]}],
         "multi": {"results": [{"job_id": "j2", "prompt_tokens": 400}, {"job_id": "j3", "prompt_tokens": 80}]}}]
    return {"multi": {"realtime": {"spans": spans}}, "assessments": assessments}


def test_insitu_separates_alone_from_together_and_measures_the_estimate():
    out = S.insitu([_insitu_run()])
    npu = out["lanes"]["npu"]
    assert npu["alone"] == {"prefill": 1000.0, "decode": 20.0} and npu["n_alone"] == 1
    assert npu["together"] == {"prefill": 500.0, "decode": 10.0} and npu["n_together"] == 1
    assert npu["together_over_alone"] == {"prefill": 0.5, "decode": 0.5}
    assert out["lanes"]["cpu"]["n_alone"] == 0 and out["lanes"]["cpu"]["together"]["prefill"] == 100.0
    assert out["prompt_real_over_estimate"] == 1.25            # 1000/800, 500/400, 100/80
    assert out["answer_tokens"]["diag_water"]["n"] == 2


def test_a_span_is_not_matched_to_a_call_of_another_length():
    run = _insitu_run()
    run["assessments"][0]["envelopes"][0]["calls"][0]["latency_ms"] = 2100.0   # 0.1 s off
    assert "j1" not in S.span_calls(run) and "j2" in S.span_calls(run)


def test_a_half_overlapped_call_counts_neither_alone_nor_together():
    run = _insitu_run()
    cpu = run["multi"]["realtime"]["spans"][2]
    cpu.update(start_s=9.0, end_s=13.0, submit_s=9.0, run_s=4.0)        # half of it beside the npu call
    run["assessments"][1]["envelopes"][1]["calls"][0]["latency_ms"] = 4000.0
    lanes = S.insitu([run])["lanes"]
    assert lanes["cpu"]["n_alone"] == 0 and lanes["cpu"]["n_together"] == 0
