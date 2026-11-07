# QIDK handoff: Laya on the NPU, then explain + clear_skip on the boiler, Cranfield and TEP

For whoever runs the board (and that laptop's Claude). Follow the steps in order; every command is here.
Background and every number so far: `reports/laya_l1.md`. Nothing here changes the agent, the Llama/Gemma
lanes or any threshold.

## What this is, in three lines
- **Laya** (convaiinnovations, 421M, Apache 2.0) is a System One decision model like bev-decider. It takes
  bev-decider's place in the bev slot: with `explain` on, Llama only ranks the cases and Laya picks the
  citations, the separating case and the notes; `clear_skip` (code only) skips Llama on clear ticks.
- The board's pinned `llama-server` (`b11371`) **serves Laya itself** on `POST /v1/systemone`, the protocol the
  bev slot already speaks. No new binary. Laya runs as a third lane on **port 8083**, on HTP0.
- The benchmark runner knows Laya now: it starts the Laya lane, checks its file's sha256 and that every layer
  is on HTP0, keeps it up across episodes, and refuses an episode in which any Laya call failed.

## Order and time (board time, estimates)
| step | what | about |
|---|---|---|
| 1–3 | pull, build the model file, push it to the board | 15 min (needs internet once) |
| 4 | Laya alone on the NPU: placement + answers against the laptop | 15 min |
| 5a | Cranfield dev, 6 episodes | 45 min |
| 5b | boiler dev quick set, 10 episodes | 45 min |
| 5c | TEP board subset, 22 episodes | 7 h (resumable, can be split over days) |
| 5d | optional: bev explain + clear_skip on the boiler (the missing bev arm) | 45 min |

## 1. Get the code
```bash
cd ~/field-mind                       # your clone
git fetch https://github.com/Shub-amG-upta/fieldmind-2 laya
git switch -c laya FETCH_HEAD         # or: git switch laya && git merge --ff-only FETCH_HEAD
env -u PYTHONPATH .venv/bin/python -m pytest tests/test_laya_runner.py tests/test_system_one.py tests/test_laya_router.py -q
```
All tests must pass. The episodes are the ones you already have: `data/episodes_dev` (boiler dev),
`data/episodes_cranfield_dev`, `data/episodes_tep_board` (HANDOFF_QIDK_BREADTH.md made the last two).

## 2. Build the model file (one command)
```bash
scripts/laya_build_gguf.sh
```
It makes `.venv-laya-convert`, installs the exact versions in `bench/requirements-laya-convert.txt` (torch from
the CPU index), clones llama.cpp `b11371` into `device/models/laya/`, downloads Laya revision
`7b928d828b7b0e022f929d9bd2e44165aa270148`, converts it to Q8_0 and checks the sha256 against
`bench.board.LAYA_FILES`. It must end with:
```
OK  device/models/laya/laya-7b928d8-Q8_0.gguf  sha256 a972d557cc47ef3caf7ddfb81a51e92974cf9a977c5f15ceef967f667740b7b6 ...
```
If it prints **STOP** (a different sha256): do not edit `LAYA_FILES`; send Shubham both values and ask him to
copy his file (449,396,448 bytes) instead. (Built twice on his laptop, once from a clean venv: identical.)

## 3. Push it to the board
```bash
adb push device/models/laya/laya-7b928d8-Q8_0.gguf /data/local/tmp/llm/
adb shell sha256sum /data/local/tmp/llm/laya-7b928d8-Q8_0.gguf    # must print a972d557...
```

## 4. Laya alone on the NPU (placement, answers, speed)
```bash
mkdir -p results/laya_board
.venv/bin/python -m bench.board temp | tee results/laya_board/temp_before.json
.venv/bin/python -m bench.board start laya laya-7b928d8-Q8_0.gguf | tee results/laya_board/start_npu.json
.venv/bin/python -m bench.board log laya > results/laya_board/lane_laya_npu.log
grep -E "offloaded|HTP0|CPU.*buffer|decision model" results/laya_board/lane_laya_npu.log
```
**Go on only if** the log shows `offloaded N/N layers` (both numbers equal), a nonzero `HTP0 model buffer`,
and `decision model type: laya`. If not: stop, keep the log, send it (the runner would refuse anyway).
Note where the small F32 table `token_types.weight` (1024 × 3, the question-type embedding) lands.

```bash
# the same 278 Cranfield requests the laptop checked, against the PyTorch answers committed in the branch
.venv/bin/python -m bench.laya_parity http://localhost:8083 cranfield_dev \
    --label board_npu_Q8_0 --base reports/data/laya_parity | tee results/laya_board/parity_npu.txt
cp results/laya_l1/parity_board_npu_Q8_0.json results/laya_board/
```
Expected from the laptop: top answer identical on ~269 of 278 (Q8_0's 9 near-ties), max |Δp| about 0.03.
Much worse (say under 260 of 278) means the NPU computes something else: stop and send the files.
Leave the Laya lane running: step 5 uses it.

## 5. explain + clear_skip with Laya (the runner starts and checks everything)
The Llama (NPU) and Gemma (CPU) lanes are started per episode as always; the Laya lane stays up. Temperatures
and cooling are handled by the runner. Re-running the same command continues where it stopped.

```bash
# 5a  Cranfield dev (first: shortest)
scripts/benchmark.sh laya_es_cranfield_dev $(ls data/episodes_cranfield_dev) \
    --overlay configs/bev_ideas.yaml,configs/cranfield.yaml,configs/laya_board.yaml --bev "explain=on,clear_skip=on"

# 5b  boiler dev quick set (the same 10 episodes as bevideas_A1-A3)
scripts/benchmark.sh laya_es_boiler_dev dev_A01_fcv_seize dev_A02_fcv_seize_fast dev_B01_tube_leak \
    dev_B02_tube_leak_fast dev_C01_wet_coal dev_C02_feeder_trip dev_D01_high_cv_coal dev_D03_high_cv_severe \
    dev_N01_normal dev_N02_normal \
    --overlay configs/bev_ideas.yaml,configs/laya_board.yaml --bev "explain=on,clear_skip=on"

# 5c  TEP board subset (long; split over sessions if needed: same command resumes)
scripts/benchmark.sh laya_es_tep_board $(ls data/episodes_tep_board) \
    --overlay configs/bev_ideas.yaml,configs/tep.yaml,configs/laya_board.yaml --bev "explain=on,clear_skip=on"
```
Each `RESULTS.md` header must say **"Laya on llama-server on npu"** and the bev-ideas table must show
`failed 0` for explain. A failed Laya call makes the runner refuse the episode (saved as `*.rejected-*`):
look at `bench.board log laya`, fix, run the same command again.

```bash
# 5d  optional: the bev arm the boiler is missing (bev-decide instead of Laya; same switches)
.venv/bin/python -m bench.board stop laya          # one System One server at a time
scripts/benchmark.sh bev_es_boiler_dev dev_A01_fcv_seize dev_A02_fcv_seize_fast dev_B01_tube_leak \
    dev_B02_tube_leak_fast dev_C01_wet_coal dev_C02_feeder_trip dev_D01_high_cv_coal dev_D03_high_cv_severe \
    dev_N01_normal dev_N02_normal --overlay configs/bev_ideas.yaml --bev "explain=on,clear_skip=on"
```

At the end:
```bash
.venv/bin/python -m bench.board stop laya
.venv/bin/python -m bench.board temp | tee results/laya_board/temp_after.json
```

## If something goes wrong
| you see | do |
|---|---|
| `STOP ... sha256 ... != recorded` in step 2 | send both values; use Shubham's copy of the file |
| `... is not in bench.board.LAYA_FILES` / board sha256 mismatch | re-push the file, re-check `sha256sum` on the board |
| `Laya is not fully on the NPU` | send `bench.board log laya`; do not run step 5 on the CPU instead |
| `did not load the file as a Laya decision model` | the board's llama-server is not `b11371`: `llama-server --version` must print `commit 99b95488c` |
| an episode `not kept: N bev idea call(s) failed` | `bench.board log laya`; restart the lane (`stop laya`, `start laya ...`); same command again |
| the board drops off USB | the runner waits and resumes, as for the breadth runs |
| `bench.board stop` (no argument) | stops **every** llama-server, Laya's too; prefer `stop laya` for the Laya lane |

## Do not
- Edit `bench.board.LAYA_FILES`, any threshold, or `configs/base.yaml`.
- Put the F16 file on the NPU (project rule: Q4_0 / Q8_0 only on HTP; Shubham's decision).
- Run reporting episodes (`ep_*`) with these switches.

## Send back
`results/benchmarks/laya_es_cranfield_dev/`, `laya_es_boiler_dev/`, `laya_es_tep_board/` (and
`bev_es_boiler_dev/` if run), and `results/laya_board/`. Commit them on a branch of your own (as
`breadth-board-runs`) and push it to Shubham's repo.
