"""bench.board module-9 settings: one Hexagon variable or server flag per start, whitelisted, default unchanged."""
from __future__ import annotations

import pytest

from bench import board

STANDARD = board.lane_command("npu", "m.gguf")


def test_no_settings_gives_the_standard_command_byte_for_byte():
    assert board.lane_command("npu", "m.gguf", nd_env=(), nd_args=()) == STANDARD
    assert board.nd_knobs("", "") == ([], [])


def test_a_hexagon_variable_goes_before_the_binary_on_the_board_command():
    cmd = board.lane_command("npu", "m.gguf", nd_env=["GGML_HEXAGON_NHVX=1"])
    head, tail = cmd.split("./bin/llama-server", 1)
    assert head.endswith("GGML_HEXAGON_NHVX=1 ")
    assert tail == STANDARD.split("./bin/llama-server", 1)[1]


def test_server_flags_are_appended_after_the_standard_flags():
    cmd = board.lane_command("npu", "m.gguf", nd_args=["-fa", "off", "-ub", "32"])
    assert cmd == STANDARD + " -fa off -ub 32"


@pytest.mark.parametrize("env", ["GGML_HEXAGON_NHVX=1;rm", "LD_PRELOAD=x", "GGML_HEXAGON_NHVX=$(id)",
                                 "GGML_HEXAGON_PROFILE=1", "GGML_HEXAGON_NHVX="])
def test_variables_outside_the_whitelist_are_refused(env):
    with pytest.raises(ValueError):
        board.nd_knobs(env, "")
    with pytest.raises(ValueError):
        board.lane_command("npu", "m.gguf", nd_env=[env])


@pytest.mark.parametrize("args", ["-fa", "-fa maybe", "-ub 0", "-ub 99999", "-ub x", "-c 8192", "--cache-ram 100",
                                  "-fa off;reboot x"])
def test_flags_outside_the_whitelist_are_refused(args):
    with pytest.raises(ValueError):
        board.nd_knobs("", args)


def test_start_refuses_bad_settings_before_touching_the_board(monkeypatch):
    calls = []
    monkeypatch.setattr(board, "_adb", lambda *a, **k: calls.append(a))
    monkeypatch.setattr(board, "check_model", lambda *a, **k: calls.append("sha") or "x")
    with pytest.raises(ValueError):
        board.start_lane("npu", "m.gguf", nd_env=["LD_PRELOAD=x"])
    assert calls == []
