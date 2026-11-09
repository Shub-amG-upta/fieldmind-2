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
    cells = S.cells()
    names = [c["name"] for c in cells]
    assert len(names) == len(set(names)) == 4 + 2 * 2 * 4 * 2
    assert all(c["mode"] == "lockstep" for c in cells[:4])
    assert all(n.endswith("_dry") for n in [c["name"] for c in S.cells(0.05)][4:])
    cmd = S.command(cells[-1], "llamaserver")
    assert "--placement" in cmd and "--backend" not in cmd


def _args(**kw):
    base = dict(arch="multi", overlay="configs/v3.yaml,configs/sched_study.yaml", merge_rule=None,
                placement="earliest_finish", bev=None, mode="realtime", tick_s=5.0,
                backend="llamaserver", no_prompts=False, bev_device="npu")
    base.update(kw)
    return argparse.Namespace(**base)


def test_the_board_runner_refuses_real_time_with_unmeasured_lane_rates():
    with pytest.raises(SystemExit, match="not measured"):
        B.settings(_args())
    cfg, params = B.settings(_args(backend="mock"))         # plumbing on the laptop is allowed
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
