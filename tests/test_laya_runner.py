"""The benchmark runner with Laya as the System One server (reports/laya_l1.md, Track C):
which server a lane file needs, the placement proof read from llama-server's log, and the
per-episode lane restart that must leave Laya's llama-server up."""

import argparse

import pytest

from bench import benchmark, board

GOOD_NPU_LOG = """\
0.00.650 I srv    load_model: loading model '/data/local/tmp/llm/laya-7b928d8-Q8_0.gguf'
0.09.571 I decision model reads the embeddings output, enabling embedding mode
0.09.700 I load_tensors: offloaded 31/31 layers to GPU
0.09.701 I load_tensors:        HTP0 model buffer size =   420.12 MiB
0.09.964 I srv          init: decision model type: laya
"""


def test_server_follows_the_lane_file():
    assert benchmark.system_one_server("bev-decider-0.4B-backbone-Q8_0.gguf") == "bev"
    assert benchmark.system_one_server("laya-7b928d8-Q8_0.gguf") == "laya"
    with pytest.raises(SystemExit):
        benchmark.system_one_server("laya-other.gguf")


def test_npu_log_with_every_layer_on_htp0_passes():
    assert benchmark.laya_log_problem(GOOD_NPU_LOG, "laya-7b928d8-Q8_0.gguf", "npu") is None


@pytest.mark.parametrize("edit, why", [
    (("offloaded 31/31", "offloaded 29/31"), "not fully on the NPU"),
    (("HTP0 model buffer size =   420.12", "HTP0 model buffer size =     0.00"), "not fully on the NPU"),
    (("decision model type: laya", "decision model type: none"), "not load the file as a Laya"),
    (("laya-7b928d8-Q8_0.gguf", "laya-7b928d8-F16.gguf"), "does not name"),
])
def test_npu_log_problems_are_named(edit, why):
    log = GOOD_NPU_LOG.replace(*edit)
    problem = benchmark.laya_log_problem(log, "laya-7b928d8-Q8_0.gguf", "npu")
    assert problem and why in problem


def test_cpu_placement_refuses_a_lane_that_went_to_the_npu():
    assert "loaded onto the NPU" in benchmark.laya_log_problem(GOOD_NPU_LOG, "laya-7b928d8-Q8_0.gguf", "cpu")
    cpu_log = GOOD_NPU_LOG.replace("HTP0 model buffer size =   420.12", "CPU_Mapped model buffer size =   420.12")
    assert benchmark.laya_log_problem(cpu_log, "laya-7b928d8-Q8_0.gguf", "cpu") is None


def test_lane_restart_can_leave_layas_llama_server_up(monkeypatch):
    sent = []
    monkeypatch.setattr(board, "_adb", lambda *a, **k: (sent.append(" ".join(a)),
                                                       type("R", (), {"stdout": ""})())[1])
    board.stop_lanes(keep_laya=True)
    cmd = sent[-1]
    assert "pkill llama-server" not in cmd                       # not every llama-server
    for port in board.LANE_PORT.values():
        assert f"port {port}" in cmd
    assert f"port {board.LAYA_PORT}" not in cmd
    board.stop_lanes()
    assert "pkill llama-server" in sent[-1]                       # the old behaviour by default


def _args(overlay, bev="explain=on,clear_skip=on", arch="multi"):
    return argparse.Namespace(overlay=overlay, arch=arch, backend="llamaserver", merge_rule=None, bev=bev,
                              mode="lockstep", tick_s=30.0, no_prompts=False, bev_device="npu")


@pytest.mark.parametrize("plant", ["", "configs/cranfield.yaml,", "configs/tep.yaml,"])
def test_board_overlay_gives_laya_explain_and_clear_skip_on_every_plant(plant):
    cfg, p = benchmark.settings(_args(f"configs/bev_ideas.yaml,{plant}configs/laya_board.yaml"))
    assert p["system_one"] == "laya" and p["models"]["bev"] == "laya-7b928d8-Q8_0.gguf"
    assert cfg["multi"]["lanes"]["bev"]["url"] == f"http://localhost:{board.LAYA_PORT}"
    assert cfg["multi"]["bev"]["explain"] == "on" and cfg["multi"]["bev"]["clear_skip"] == "on"


def test_a_laya_lane_pointing_elsewhere_is_refused(tmp_path, monkeypatch):
    bad = tmp_path / "bad.yaml"
    bad.write_text('multi: {lanes: {bev: {url: "http://localhost:8090", model_file: "laya-7b928d8-Q8_0.gguf"}}}\n')
    monkeypatch.setattr(benchmark, "ROOT", benchmark.ROOT)
    with pytest.raises(SystemExit):
        benchmark.settings(_args(f"configs/bev_ideas.yaml,{bad}"))


def test_bev_decide_tests_keep_their_settings():
    cfg, p = benchmark.settings(_args("configs/bev_ideas.yaml"))
    assert "system_one" not in p                  # older bev tests' test.json stay identical
    assert benchmark.server_label(p) == "bev-decide"
