# HANDOFF_SCHED.md: board run, 2026-11-10/11 (Gagan's Mac + QIDK)

Run by Claude on Gagan's laptop, from `sched-study` at 8b24f50 (identical in `Gagan-453/field-mind` and
`Shub-amG-upta/fieldmind-2`), in a separate worktree with its own venv (same package versions as the main venv, plus
scipy 1.18.1 and pyreadr). Board `ab8f6592` (SM8650), llama.cpp b11371 / 99b95488c. All plant data is synthetic. The
agent ran on the laptop for steps 2–5; tick times are laptop times. No energy figures.

## Steps
| step | when (laptop) | result |
|---|---|---|
| 0 tests | 21:05 | the 5 handoff test files: 42 passed, 0 skipped (after generating `data/episodes_dev`, which is identical to the main repo's copy, and `data.cranfield.convert`); Cranfield data tests 12 passed |
| 1 launcher, bundle | 20:45–21:00 | launcher sha256 `3197115a34de696af6e55d002155f8e05cd268b394e9706207644a09b076e6be`, **the same as Shubham's**; bundle 777 files, 40.4 MB |
| 1 push, identity | 21:25 | "pushed 777 files; every sha256 matches"; identity dev_B01 170/170 ticks, cf_F5 75/75, both `"identical": true` |
| 1 hard path | 21:27 | no mask: dev_B01 p50 26.7 / p95 33.4 / max 34.7 ms; cf_F5 51.4 / 69.0 / 69.6 ms; 0 ticks over 200 ms. `--cpu-mask 80`: 26.7 / 33.2 / 34.9 and 51.2 / 69.0 / 69.9 ms. Core layout in `results/device/core_layout.txt` (cpu7 3.30 GHz) |
| 2 lockstep | 21:27–21:51 | 4 / 4 tests, 0 unusable answers, Laya 0 failed / 0 rejected (`results/benchmarks/sched_v3*_lockstep_*`) |
| 3 lane rates | 21:52–21:54 | alone: NPU prefill 896.61 / decode 18.16 tok/s, CPU 100.05 / 19.70. together_over_alone: NPU 0.811 / 0.709, CPU 0.793 / 0.951. Committed as "sched C: measured lane rates" |
| 4 sweep | 21:56–03:26 | 32 / 32 cells, every load exit 0 (`step4_sweep.log`) |
| 5 repeats | 03:26–03:53 | both exit 0; the t3 boiler cells now have 4 runs each |

Tables: `table.txt` and `table_per_run.txt` (from `bench.sched_study table [--per-run]` after step 5).

## Capacity (from table.txt)
| config | policy | boiler | cranfield |
|---|---|---|---|
| v3 | fixed | 3 s | none |
| v3 | earliest_finish | 3 s | none |
| v3x | fixed | 2 s | 4 s |
| v3x | earliest_finish | 2 s | none |

## Things Shubham should know
1. **Handoff step 3 command fails as written.** `bench/sched_study.py rates --n 6` gives
   `ModuleNotFoundError: No module named 'bench'` when run as a script. `python -m bench.sched_study rates --n 6` was used
   (`step3_rates.log`). `run` works as a script because it shells out to `scripts/benchmark.sh`.
2. **A test can only pass before step 3.** `tests/test_sched_study.py::test_the_board_runner_refuses_real_time_with_unmeasured_lane_rates`
   reads the live `configs/sched_study.yaml`, so it fails once step 3 sets `lane_rates_measured: true`. Left unchanged.
3. **The toolchain tag moved.** `ghcr.io/snapdragon-toolchain/arm64-android:v0.7` now resolves to digest `91714433…`, not
   the `c012b817…` the pinned llama.cpp package was built with. The launcher was built with the new tag and still matches your
   sha256.
4. **P1 in v3 boiler cells is missed 37/37 (35/35 at 2 s) under every policy and load,** while v3x boiler misses 0/34 at
   5 s and 4 s. This looks like a definition or counting difference between v3 and v3x rather than a load effect. Not
   investigated.
5. **Laya cells:** every v3x cell's Laya calls had 0 failed (the runner rejects an episode otherwise).
6. **Rates were measured warm** (chip 52.1 °C before, 64.8 °C after); the handoff does not ask for cooling before step 3.
