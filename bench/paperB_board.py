#!/usr/bin/env python3
"""
=============================================================================
 PAPER B BOARD RUNS  --  every board command of PLAN_PAPER_B.md, in one place
=============================================================================

    .venv/bin/python bench/paperB_board.py plan [--item 1|2|6|7|8] [--backend mock]
    .venv/bin/python bench/paperB_board.py check          (overlays, episodes, files exist)

Prints the commands; runs nothing. Each item's arms, episodes and rules are
pre-registered in its report (DRAFT until agreed):

  item 1  external audit, FaultExplainer F1 on the NPU lane   reports/ext_faultexplainer_prereg.md
  item 2  published fixes (no example / no letters / calibrate / PriDe / PSC)
                                                                 reports/paperB_item2_prereg.md
  item 6  calibrated_finish on the board (sched fix part D)     reports/sched_fix.md
  item 7  more episodes for the key sweep cells                 (PROPOSED below)
  item 8  NPU reading speed with arXiv 2605.27435's settings    reports/paperB_prep.md

Board rules (CLAUDE.md) apply to every command: lanes started with /board-up
(bench/board.py), chip temperature before and after, cooling gaps, sha256 of
every pushed file, laptop time only.
=============================================================================
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bench import sched_study as S  # noqa: E402

BOARD_FILE = "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf"     # the sweep's lane file (configs/sched_study.yaml)
ASSET = {"boiler": None, "cranfield": "configs/cranfield.yaml", "tep": "configs/tep.yaml"}
# item 2 episode sets (PROPOSED): the sets the existing v3 board runs used, so each arm sits next to a base
# run of the same build and file (results/benchmarks/af_cf_v3_dev, af_tep_v3_board); boiler: the sweep's two.
ITEM2_EPISODES = {"cranfield": "data/episodes_cranfield_dev", "tep": "data/episodes_tep_board",
                  "boiler": ["dev_B01_tube_leak", "dev_A02_fcv_seize_fast"]}
ITEM2_ARMS = {"noexample": "configs/debias_noexample.yaml", "noletters": "configs/debias_noletters.yaml",
              "calibrate": "configs/debias_calibrate.yaml", "pride": "configs/debias_pride.yaml",
              "psc": "configs/debias_psc.yaml"}
# v3x has no example under explain v2 and no letters already: those two arms are not run on it
ITEM2_SYSTEMS = {"v3": ("boiler", "cranfield", "tep"), "v3x": ("cranfield", "tep")}
SKIP = {("v3x", "noexample"), ("v3x", "noletters")}
# item 6: sched_fix.md part D
ITEM6 = [("v3x", "cranfield", t) for t in (5.0, 4.0, 3.0, 2.0)] + [("v3", "boiler", t) for t in (4.0, 3.0)]
# item 7 (PROPOSED): the cells that set capacity, on 6 Cranfield dev episodes and 6 boiler dev episodes, 3 repeats
ITEM7_CELLS = [("v3x", "cranfield", "fixed", 4.0), ("v3x", "cranfield", "fixed", 3.0),
               ("v3", "boiler", "fixed", 3.0), ("v3", "boiler", "fixed", 2.0)]
ITEM7_EPISODES = {"cranfield": "data/episodes_cranfield_dev",
                  "boiler": ["dev_A01_fcv_seize", "dev_A02_fcv_seize_fast", "dev_B01_tube_leak",
                             "dev_C01_wet_coal", "dev_D01_high_cv_coal", "dev_N01_normal"]}
ITEM7_REPEATS = 3
# item 8: the NPU lane restarted with the paper's settings, then the existing lane-rate probe
ITEM8_FLAGS = "-b 128 -ub 128 -fa off"


def episodes(spec) -> list[str]:
    if isinstance(spec, list):
        return list(spec)
    return sorted(p.name for p in (ROOT / spec).iterdir() if p.is_dir())


def system_overlay(system: str, asset: str) -> str:
    """The sweep's overlays for a system (bench.sched_study.CONFIGS), with the plant's own overlay."""
    out = []
    for o in S.CONFIGS[system]["overlays"]:
        if o == "{asset}":
            if ASSET[asset]:
                out.append(ASSET[asset])
        else:
            out.append(o)
    return ",".join(out)


def _bench(name, eps, overlay, mode="lockstep", placement="fixed", tick_s=None, bev=None, backend=None):
    cmd = ["scripts/benchmark.sh", name, *eps, "--overlay", overlay, "--placement", placement,
           "--mode", mode, "--plain"]
    if tick_s:
        cmd += ["--tick-s", f"{tick_s:g}"]
    if bev:
        cmd += ["--bev", bev]
    if backend == "mock":
        cmd += ["--backend", "mock"]
    return " ".join(cmd)


def plan(item: int | None = None, backend: str | None = None) -> list[str]:
    out = []
    if item in (None, 1):
        out += ["# item 1: FaultExplainer F1 on the NPU lane (lanes up; 108 calls, about 1.5-2.6 h)",
                "PYTHONPATH= .venv/bin/python bench/ext_faultexplainer.py run reports/data/ext_faultexplainer_requests.json"
                f" --url http://127.0.0.1:8080 --model {BOARD_FILE} --label F1_board_npu"
                " --out results/ext/faultexplainer_F1.jsonl"]
    if item in (None, 2):
        out.append("# item 2: one lockstep pass per arm, system and plant")
        for system, assets in ITEM2_SYSTEMS.items():
            for arm, ov in ITEM2_ARMS.items():
                if (system, arm) in SKIP:
                    continue
                for asset in assets:
                    out.append(_bench(f"paperB_{arm}_{system}_{asset}", episodes(ITEM2_EPISODES[asset]),
                                      system_overlay(system, asset) + "," + ov,
                                      bev=S.CONFIGS[system]["bev"], backend=backend))
    if item in (None, 6):
        out.append("# item 6: calibrated_finish, sched_fix.md part D")
        for system, asset, t in ITEM6:
            out.append(_bench(f"sched_{system}_calibrated_finish_t{t:g}_{asset}", S.EPISODES[asset],
                              system_overlay(system, asset), mode="realtime", placement="calibrated_finish",
                              tick_s=t, bev=S.CONFIGS[system]["bev"], backend=backend))
    if item in (None, 7):
        out.append(f"# item 7: the capacity-setting cells on more episodes, {ITEM7_REPEATS} repeats each")
        for system, asset, policy, t in ITEM7_CELLS:
            for r in range(1, ITEM7_REPEATS + 1):
                out.append(_bench(f"paperB_more_{system}_{policy}_t{t:g}_{asset}_rep{r}",
                                  episodes(ITEM7_EPISODES[asset]), system_overlay(system, asset),
                                  mode="realtime", placement=policy, tick_s=t,
                                  bev=S.CONFIGS[system]["bev"], backend=backend))
    if item in (None, 8):
        from bench import board
        cmd = board.lane_command("npu", BOARD_FILE) + " " + ITEM8_FLAGS
        out += ["# item 8: restart ONLY the NPU lane with the paper's settings, probe, then restore it",
                f"adb shell 'pkill -f \"port {board.LANE_PORT['npu']}\"; nohup sh -c \"{cmd}\" "
                f"> {board.DEVICE_LOGS}/npu_item8.log 2>&1 &'",
                "PYTHONPATH= .venv/bin/python bench/sched_study.py rates --n 6   # the existing two-lane probe",
                "# then restart the NPU lane normally (/board-up) before any other run"]
    return out


def check() -> list[str]:
    """Problems that would stop a planned command: missing overlays or episodes."""
    bad = []
    for ov in list(ITEM2_ARMS.values()) + [o for o in ASSET.values() if o]:
        if not (ROOT / ov).exists():
            bad.append(f"missing overlay {ov}")
    dirs = [ROOT / "data" / d for d in ("episodes_dev", "episodes_cranfield_dev", "episodes_tep_board")]
    have = {p.name for d in dirs if d.is_dir() for p in d.iterdir()}
    for spec in list(ITEM2_EPISODES.values()) + list(ITEM7_EPISODES.values()):
        if isinstance(spec, str):
            if not (ROOT / spec).is_dir():
                bad.append(f"missing episode folder {spec}")
        else:
            bad += [f"missing episode {e}" for e in spec if e not in have]
    if not (ROOT / "reports/data/ext_faultexplainer_requests.json").exists():
        bad.append("missing reports/data/ext_faultexplainer_requests.json")
    return bad


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", choices=["plan", "check"])
    ap.add_argument("--item", type=int, choices=[1, 2, 6, 7, 8], default=None)
    ap.add_argument("--backend", choices=["mock"], default=None, help="mock: plumbing commands only")
    a = ap.parse_args(argv)
    if a.what == "check":
        bad = check()
        print("\n".join(bad) if bad else "ok: every overlay, episode and request file exists")
        return 1 if bad else 0
    print("\n".join(plan(a.item, a.backend)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
