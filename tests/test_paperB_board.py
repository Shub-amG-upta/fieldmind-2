"""bench.paperB_board: every planned board command is one the runner accepts, on files that exist.
(The runner's --placement once lacked calibrated_finish: item 6 would have failed at start-up.)"""

from __future__ import annotations

import shlex
from pathlib import Path

import pytest

from bench import benchmark, paperB_board as P

ROOT = Path(__file__).resolve().parent.parent
needs_data = pytest.mark.skipif(not (ROOT / "data/episodes_cranfield_dev").is_dir(), reason="episodes not generated")


@needs_data
def test_every_planned_benchmark_command_parses_and_names_existing_overlays():
    lines = [ln for ln in P.plan() if ln.startswith("scripts/benchmark.sh")]
    assert len(lines) > 30
    ap = benchmark.parser()
    for ln in lines:
        args = ap.parse_args(shlex.split(ln)[1:])          # argparse exits on an unknown choice
        for ov in args.overlay.split(","):
            assert (ROOT / ov).exists(), ov
        assert all(benchmark.episode_dir(e).exists() for e in args.episodes), ln


@needs_data
def test_the_plan_covers_each_item_and_check_finds_nothing_missing():
    text = "\n".join(P.plan())
    assert "--placement calibrated_finish" in text and "ext_faultexplainer.py run" in text
    assert "configs/debias_psc.yaml" in text and "-b 128 -ub 128 -fa off" in text
    assert "paperB_noexample_v3x" not in text                  # v3x has no example to drop
    assert P.check() == []


def test_mock_plans_carry_the_mock_flag_and_board_plans_do_not():
    assert all("--backend mock" in ln for ln in P.plan(2, "mock") if ln.startswith("scripts/"))
    assert not any("--backend mock" in ln for ln in P.plan(2) if ln.startswith("scripts/"))
