# QIDK handoff: the agent on the phone, then the scheduling study

For whoever runs the board (and that laptop's Claude). Follow the steps in order; every command is here.
Background: `reports/sched_stage_a.md` (real-time engine), `reports/sched_stage_b.md` (agent on the phone),
`reports/sched_prereg.md` (the study, fixed before any run). Nothing here changes a threshold, band or
deadline.

## What this is, in three lines
- **Stage B**: the whole agent (not just the model calls) runs on the QIDK: official CPython 3.14.10 for
  Android + a 3-line launcher, the agent's files, the study's episodes. First check: mock backend on the
  board gives the same assessments as mock on the laptop, and the hard path stays under 200 ms.
- **Stage C**: the scheduling study. Llama 3.2 3B on **both** lanes; four placement policies; real time at
  10 s and 5 s per 30 s plant tick; three dev episodes; with and without Laya explain + clear_skip.
- **Read "Open decision" in `reports/sched_prereg.md` before step 4.** The registered loads may be too light
  to separate the policies; Shubham decides whether to add a heavier load before board time is spent.

## Order and time (board time, estimates)
| step | what | about |
|---|---|---|
| 0 | pull, tests | 10 min |
| 1 | launcher, bundle, push, identity, hard path | 30 min (docker image pull once: ~2 GB) |
| 2 | lockstep references (4 tests) | ~1 h (earlier v3 lockstep: 1.0–2.0 s per tick) |
| 3 | lane rates: Llama 3B on each lane alone and both at once | 15 min |
| 4 | real-time cells, 10 s then 5 s per tick | 10.8 h (resumable; split over sessions) |
| 5 | the two repeat cells | 45 min |

## 0. Get the code
```bash
cd ~/field-mind
git fetch https://github.com/Shub-amG-upta/fieldmind-2 sched-study
git switch -c sched-study FETCH_HEAD
env -u PYTHONPATH .venv/bin/python -m pytest -q tests/test_sched_policies.py tests/test_sched_study.py \
    tests/test_device_agent.py tests/test_rt_explain.py tests/test_realtime.py
```
All must pass. Episodes needed: `data/episodes_dev` (dev_B01, dev_A02) and `data/episodes_cranfield_dev`
(cf_F5). The board needs the Llama GGUF and the Laya GGUF already pushed (HANDOFF_LAYA.md steps 2–3).

## 1. The agent on the phone
Nothing else may run on the board (stop the lanes: `.venv/bin/python -m bench.board stop`).
```bash
docker pull --platform linux/amd64 ghcr.io/snapdragon-toolchain/arm64-android:v0.7   # once
env -u PYTHONPATH .venv/bin/python -m bench.device_agent launcher   # downloads Python (sha256 pinned), builds
env -u PYTHONPATH .venv/bin/python -m bench.device_agent bundle
env -u PYTHONPATH .venv/bin/python -m bench.device_agent push       # must end "every sha256 matches"
env -u PYTHONPATH .venv/bin/python -m bench.device_agent identity   # exit 0 = identical
env -u PYTHONPATH .venv/bin/python -m bench.device_agent hardpath
env -u PYTHONPATH .venv/bin/python -m bench.device_agent hardpath --cpu-mask 80   # agent pinned to cpu7
```
- `launcher` prints the launcher's sha256; on Shubham's Mac it was
  `3197115a34de696af6e55d002155f8e05cd268b394e9706207644a09b076e6be` (record yours; a different value is
  not an error by itself, the build is not proven reproducible).
- `identity` runs dev_B01 and cf_F5 with the mock backend on the laptop and on the board and compares every
  tick with clock readings removed. Each line must say `"identical": true`. If not: **stop**, send
  `results/device/identity/identity.json` (its `first_difference` names the tick and fields).
- `hardpath` prints p50 / p95 / max of the hard path per tick and how many ticks were over 200 ms. Send both
  outputs. (Laptop for comparison: p50 18 ms, p95 23 ms on dev_B01; laptop timings are not board timings.)
- Before choosing a mask, record the core layout: `adb shell 'for c in /sys/devices/system/cpu/cpu[0-9]*; do
  echo $c $(cat $c/cpufreq/cpuinfo_max_freq); done'`.

## 2. Lockstep references
The runner restarts the lanes per episode with the config's files (Llama 3B on both lanes, Laya for v3x),
checks the sha256 and NPU placement, logs chip temperature, and waits for the chip to cool.
```bash
env -u PYTHONPATH .venv/bin/python bench/sched_study.py run --only _lockstep_
```
Four tests: `sched_v3_lockstep_boiler`, `sched_v3_lockstep_cranfield`, `sched_v3x_lockstep_boiler`,
`sched_v3x_lockstep_cranfield`. Laya must be up for the v3x ones
(`.venv/bin/python -m bench.board start laya laya-7b928d8-Q8_0.gguf`).

## 3. Lane rates (Llama 3B on both lanes)
Start both lanes with Llama (`.venv/bin/python -m bench.board start npu Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`,
same for `cpu`), then:
```bash
env -u PYTHONPATH .venv/bin/python bench/sched_study.py rates --n 6
```
It replays six diagnostician prompts the agent really sent (from step 2's run file) on each lane alone, then
on both at once, and saves `results/sched_rates/rates_<time>.json`. Then edit `configs/sched_study.yaml`:
```yaml
  lanes:
    npu: {model_file: ..., prefill_tok_s: <alone.npu.prefill_tok_s>, decode_tok_s: <alone.npu.decode_tok_s>}
    cpu: {model_file: ..., prefill_tok_s: <alone.cpu.prefill_tok_s>, decode_tok_s: <alone.cpu.decode_tok_s>}
  lane_rates_measured: true
```
with a comment naming the rates file, and commit the yaml and the rates file together
(`git commit -m "sched C: measured lane rates"`). `together_over_alone` is the plan's shared-memory risk
check (below 1.0 = a lane slows down when the other runs): send it, do not act on it.

## 4. The real-time cells
```bash
env -u PYTHONPATH .venv/bin/python bench/sched_study.py run --only _t10_
env -u PYTHONPATH .venv/bin/python bench/sched_study.py run --only _t5_
```
Each cell is one benchmark test (`sched_<config>_<policy>_t<load>_<plant>`); a stopped cell resumes. The v3x
cells need Laya up. Leave at least the runner's cooling gap between cells.

## 5. Repeats (run-to-run spread)
```bash
scripts/benchmark.sh sched_v3_fixed_t5_boiler dev_B01_tube_leak dev_A02_fcv_seize_fast --again \
    --overlay configs/v3.yaml,configs/sched_study.yaml --placement fixed --mode realtime --tick-s 5 --plain
scripts/benchmark.sh sched_v3_earliest_finish_t5_boiler dev_B01_tube_leak dev_A02_fcv_seize_fast --again \
    --overlay configs/v3.yaml,configs/sched_study.yaml --placement earliest_finish --mode realtime --tick-s 5 --plain
```

## Tables
```bash
env -u PYTHONPATH .venv/bin/python bench/sched_study.py table            # one row per cell
env -u PYTHONPATH .venv/bin/python bench/sched_study.py table --per-run  # one row per episode run
```

## If something goes wrong
- `the overlay's lane rates are not measured`: step 3 is not done (the runner refuses real time without it).
- `identity` not identical: stop and send the file; do not run the study with the agent on the board until it
  is understood. The study itself (steps 2–5) runs the agent on the laptop as before and does not depend on it.
- The board runner's usual protections apply (sha256, NPU placement, a failed Laya call rejects the episode).

## Do not
- Edit thresholds, deadlines, `rt_deadline_ticks`, the matrix in `bench/sched_study.py`, or
  `bench.board` model tables. A change to the study is an amendment in `reports/sched_prereg.md` first.
- Put a model other than the Llama GGUF on the CPU lane for these tests.

## Send back
`results/device/` (identity, hardpath), `results/sched_rates/`, `results/benchmarks/sched_*` (whole folders),
and the two `table` outputs.
