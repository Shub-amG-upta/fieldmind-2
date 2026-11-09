"""The agent on the phone (bench/device_agent.py, reports/sched_stage_b.md), checked
on the laptop: the bundled app folder runs the agent with no site-packages (stdlib +
vendored PyYAML only) and gives the same assessments; the identity comparison sees
a real difference and ignores clock readings; the board command carries every
library path."""

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

import bench.device_agent as D

ROOT = Path(__file__).resolve().parent.parent
needs_dev = pytest.mark.skipif(not (ROOT / "data/episodes_dev/dev_B01_tube_leak").exists(),
                               reason="dev episodes not generated")
ARGS = ["--backend", "mock", "--arch", "multi", "--episodes-dir", "data/episodes_dev",
        "--episode", "dev_B01_tube_leak", "--overlay", "configs/v3.yaml,configs/sched_study.yaml",
        "--tag", "ident"]


@pytest.fixture(scope="module")
def two_runs(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("dev")
    app = tmp / "app"
    D.stage_app(app)
    env = {"PATH": "/usr/bin:/bin", "HOME": str(tmp)}
    # -S: no site-packages, -E: no PYTHON* variables: only the stdlib and app/
    p = subprocess.run([sys.executable, "-S", "-E", "run_demo.py", *ARGS, "--out", str(tmp / "a")],
                       cwd=app, capture_output=True, text=True, env=env, timeout=600)
    assert p.returncode == 0, p.stdout[-1500:] + p.stderr[-1500:]
    q = subprocess.run([sys.executable, "run_demo.py", *ARGS, "--out", str(tmp / "b")],
                       cwd=ROOT, capture_output=True, text=True, timeout=600,
                       env={k: v for k, v in __import__("os").environ.items() if k != "PYTHONPATH"})
    assert q.returncode == 0, q.stderr[-1500:]
    a = json.loads((tmp / "a" / "runs_mock_ident.json").read_text())
    b = json.loads((tmp / "b" / "runs_mock_ident.json").read_text())
    return app, a, b


@needs_dev
def test_the_app_folder_alone_runs_the_agent_and_gives_the_same_assessments(two_runs):
    app, a, b = two_runs
    assert not list(app.rglob("*.so"))                     # PyYAML without libyaml
    r = D.compare_runs(a, b)
    assert r["identical"] and r["ticks"] > 100


@needs_dev
def test_identity_sees_a_changed_answer_and_ignores_clock_readings(two_runs):
    _, a, b = two_runs
    c = copy.deepcopy(b)
    t = c[0]["assessments"][120]
    t["tick_latency_ms"] += 50.0
    t["multi"]["p0_ms"] = 999.0
    assert D.compare_runs(a, c)["identical"]
    t["hypotheses"] = list(reversed(t["hypotheses"]))
    r = D.compare_runs(a, c)
    assert not r["identical"] and r["first_difference"]["keys"] == ["hypotheses"]
    c = copy.deepcopy(b)
    c[0]["assessments"].pop()
    assert not D.compare_runs(a, c)["identical"]


def test_the_board_command_carries_both_library_paths_and_quotes_arguments():
    line = D.board_command(["--overlay", "configs/v3.yaml,configs/x.yaml", "--bev", "explain=on;x"],
                           cpu_mask="80")
    assert f"LD_LIBRARY_PATH={D.BOARD_ROOT}/python/lib:/data/local/tmp/llm/llama.cpp/lib " in line
    assert "ADSP_LIBRARY_PATH=/data/local/tmp/llm/llama.cpp/lib " in line
    assert f"PYTHONHOME={D.BOARD_ROOT}/python " in line and "FIELDMIND_ON_DEVICE=1" in line
    assert "taskset 80 " + D.BOARD_ROOT + "/bin/fieldmind-python run_demo.py" in line
    assert "'explain=on;x'" in line


def test_hard_path_percentiles_count_ticks_over_the_budget():
    runs = [{"assessments": [{"multi": {"p0_ms": float(x)}} for x in range(1, 101)]
             + [{"multi": {"p0_ms": 250.0}}, {"multi": {}}]}]
    h = D.hard_path(runs)
    assert h["n"] == 101 and h["max_ms"] == 250.0 and h["over_200ms"] == 1
    assert h["p50_ms"] == 51.0
