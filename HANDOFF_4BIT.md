# Runs: does the 4-bit file lose what the 8-bit file knows? (branch `bc-runs`)

Written 2026-11-13. The rules are in `reports/echo_4bit_prereg.md`. **The full run starts only after that file is agreed
and dated under "Agreed".** The pilot below can run before that; it is not scored.

**What this tests:** the same weights at 4 bits and at 8 bits give almost the same answers. We check whether the 4-bit
file still "knows" when its answer is wrong, as the 8-bit file seems to.

**Time:** one long night on the 24 GB Mac (10–12 h), plus about 1.5 h on the QIDK.

---

## MAC

### 1. Get the code and check it
```
git fetch mine && git switch bc-runs && git merge mine/bc-build
env -u PYTHONPATH .venv/bin/python -m pytest -q tests/test_echo_4bit.py tests/test_echo_causes.py   # expect all pass
```

### 2. Get the five 8-bit files (already built on Shubham's laptop; do not rebuild them)
They were built on 2026-11-13 at the pinned commit (log: Shubham's `~/fieldmind-build/gguf/RUNLOG_q8_builds.txt`).
Copy them (AirDrop or a USB drive, about 20 GB) into `~/fieldmind-build/gguf/`, then check every sha256:
```
cd ~/fieldmind-build/gguf && shasum -a 256 Qwen2.5-0.5B-Instruct-Q8_0-pure.gguf gemma-3-1b-it-qat-Q8_0-pure.gguf \
  Qwen3-1.7B-Q8_0-pure.gguf Qwen2.5-7B-Instruct-Q8_0-pure.gguf Meta-Llama-3.1-8B-Instruct-Q8_0-pure.gguf
```
| file | sha256 (must match) |
|---|---|
| `Qwen2.5-0.5B-Instruct-Q8_0-pure.gguf` | `4e54d3d6d0ae447f3146fb5e6ac5af6895b78a7c071a7ffa44fc1573d2ee256d` |
| `gemma-3-1b-it-qat-Q8_0-pure.gguf` | `ec573a51c782d592db2082f5dc7c8f40c9264527cde32d5dda6b1594b3ec300f` |
| `Qwen3-1.7B-Q8_0-pure.gguf` | `65bb9528644297a1e7ce8e749c866a6003e924739339c2bcff1fb7b10b6d96b3` |
| `Qwen2.5-7B-Instruct-Q8_0-pure.gguf` | `a97538912394c4dde85aec312ede40837ce5f423bf044a30466f216fc291125b` |
| `Meta-Llama-3.1-8B-Instruct-Q8_0-pure.gguf` | `86ba8355dd83c3d92445151830c2e42a5328d7ca6492f965b8c95a8ba3c7bd2a` |

### 2b. Check the three small models have the same weights at both precisions (10 min)
For the 7B and 8B this is already settled: Shubham's rebuild of their 4-bit file had exactly the recorded sha256. For
the three small models the 4-bit rebuild differed in the whole-file sha256, which can be the header alone. So compare
the **weight data** of your board 4-bit file with Shubham's rebuild:
```
cd ~/fieldmind-build && for f in gguf/board/Qwen2.5-0.5B-Instruct-Q4_0-pure-embq8.gguf \
    gguf/board/Qwen3-1.7B-Q4_0-pure-embq8.gguf gguf/board/gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf; do
  PYTHONPATH=llama.cpp/gguf-py venv-convert/bin/python - $f <<'PY'
import hashlib, sys
from gguf import GGUFReader
p = sys.argv[1]; r = GGUFReader(p); h = hashlib.sha256()
with open(p, "rb") as f:
    f.seek(r.data_offset)
    for c in iter(lambda: f.read(1 << 24), b""): h.update(c)
print(p, "weight-data sha256", h.hexdigest())
PY
done
```
| board 4-bit file | weight-data sha256 of Shubham's rebuild (must match) |
|---|---|
| `Qwen2.5-0.5B-Instruct-Q4_0-pure-embq8.gguf` | `cecb67e4380ca0124c660d79308a7325dc2f4ce826fe9c1d72f57c35c44456c1` |
| `Qwen3-1.7B-Q4_0-pure-embq8.gguf` | `5a14f5ac9a84565f79d302235b1f9a7e736196cfab9d43afa07a770f47c45ea2` |
| `gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf` | `08ff61c8da9f8e1d83b34aed2da3cb1c452fc981b67da02330ec54352d8527a5` |

- **Equal:** that model's 8-bit file is the same weights. Use it.
- **Different:** do not run that model's two arms (leave both out of the full-run command). Write both values in
  `results/echo/RUNLOG_4bit.txt`. That model is then reported as "not run: source not matched".
- Write the three results in `results/echo/RUNLOG_4bit.txt` either way.

### 3. Pilot (3 minutes, not scored)
```
LIMIT=3 OUT=/tmp/echo4bit_pilot bench/echo_4bit_runs.sh pilot ~/fieldmind-build/gguf/Llama-3.2-3B-Instruct-Q8_0-pure.gguf
```
Four steps should print `start` and `end`, and `/tmp/echo4bit_pilot` should hold 4 `.jsonl` files.

### 4. Full run (after the rules are agreed)
```
G=~/fieldmind-build/gguf
bench/echo_4bit_runs.sh \
  m1_q4_0             $G/board/Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf \
  m2_q8_0             $G/Llama-3.2-3B-Instruct-Q8_0-pure.gguf \
  m2b_bf16            $G/Llama-3.2-3B-Instruct-16bit.gguf \
  m7_qwen3_17b_q4_0   $G/board/Qwen3-1.7B-Q4_0-pure-embq8.gguf \
  m7_qwen3_17b_q8_0   $G/Qwen3-1.7B-Q8_0-pure.gguf \
  m4_llama31_8b_q4_0  $G/Meta-Llama-3.1-8B-Instruct-Q4_0-pure-embq8.gguf \
  m4_llama31_8b_q8_0  $G/Meta-Llama-3.1-8B-Instruct-Q8_0-pure.gguf \
  m3_qwen25_7b_q4_0   $G/Qwen2.5-7B-Instruct-Q4_0-pure-embq8.gguf \
  m3_qwen25_7b_q8_0   $G/Qwen2.5-7B-Instruct-Q8_0-pure.gguf \
  m5_qwen25_05b_q4_0  $G/board/Qwen2.5-0.5B-Instruct-Q4_0-pure-embq8.gguf \
  m5_qwen25_05b_q8_0  $G/Qwen2.5-0.5B-Instruct-Q8_0-pure.gguf \
  m6_gemma3_1b_q4_0   $G/board/gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf \
  m6_gemma3_1b_q8_0   $G/gemma-3-1b-it-qat-Q8_0-pure.gguf
```
- **Use exactly these labels.** The scorer pairs arms by label, and the set R step is skipped for arms that already
  have it.
- **Use the same files as before for the old arms** (`results/echo/RUNLOG.txt` has their paths and sha256).
- **It can be stopped and restarted.** A failed step writes `FAILED` to `results/echo/RUNLOG_4bit.txt`; rerun the same
  command.
- **Order matters if time runs out:** the Llama 3B arms are first, then the models most likely to show something.

---

## QIDK (SM8750; only after Amendment A2 in the pre-registration is agreed; about 1.5 h with cooling)

**This is the SM8750 board, at 2 NPU threads** (`GGML_HEXAGON_NHVX=2`). At the default 6 threads this chip returns
bursts of "@" (42 of 1,000 calls in m9). The rules are in `reports/echo_4bit_prereg.md`, Amendment A2.

### Q1. Put the 8-bit 3B on the board (once, about 20 min)
```
adb shell df -h /data                                       # need about 3.5 GB free; if not, stop and ask
adb shell ls -la /data/local/tmp/llm/Llama-3.2-3B-Instruct-Q8_0-pure.gguf   # already there? then skip the push
adb push ~/fieldmind-build/gguf/Llama-3.2-3B-Instruct-Q8_0-pure.gguf /data/local/tmp/llm/
adb shell sha256sum /data/local/tmp/llm/Llama-3.2-3B-Instruct-Q8_0-pure.gguf
#   must be d91f61aba2e998c3fbfb46a4cd0710e8ed4c9b9fca2d4290f6dfc80ad0738fc2
```
Both files are now in `bench.board.CANDIDATES` on this branch, and `bench.board start` reads `ND_LANE_ENV`.

### Q2. Run the two arms, in this order: 4-bit, then 8-bit
```
.venv/bin/python -m bench.board stop
.venv/bin/python -m bench.board temp                       # log it; wait for the usual cooling rule
ND_LANE_ENV="GGML_HEXAGON_NHVX=2" .venv/bin/python -m bench.board start npu Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf
.venv/bin/python -m bench.board log npu | grep -i -E "hvx|offloaded|HTP0"   # must show 2 HVX threads, all layers on HTP0
env -u PYTHONPATH .venv/bin/python bench/echo_4bit.py run prior reports/data/echo_4bit_requests.json \
    --url http://127.0.0.1:8080 --lane npu --forms original \
    --model Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf --label npu_q4_0 --out results/echo/h_prior_npu_q4_0.jsonl
.venv/bin/python -m bench.board temp
```
Then the same with `Llama-3.2-3B-Instruct-Q8_0-pure.gguf`, label `npu_q8_0`, output `h_prior_npu_q8_0.jsonl`.

- **The start command's printout must show `"nd_env": ["GGML_HEXAGON_NHVX=2"]`.** If the log does not show 2 HVX
  threads, stop: do not run the arm.
- **Save the two temperature readings per arm** in `results/echo/RUNLOG_4bit.txt` (laptop time).
- **Count the failed calls** (the run prints its status counts at the end). An "@" reply is an HTTP 500, so it shows up
  as a failed call.
  - 20 or fewer of 400: fine.
  - More than 20: move the file (do not delete it):
    ```
    mkdir -p results/echo/npu_failed
    mv results/echo/h_prior_npu_q4_0.jsonl results/echo/npu_failed/h_prior_npu_q4_0_try1.jsonl
    ```
    Then cool the board and rerun that arm once, same settings. If it fails again, stop. Do not change the thread count.
- **400 calls per file.** The 4-bit took 3.29 s a call at 2 threads in m9. The 8-bit at 2 threads is not measured yet.

---

## Score and hand back
```
bench/echo_4bit_score.sh
git add -f results/echo/h_prior_*.jsonl results/echo/prior_*q8_0.jsonl results/echo/mmluprob_*.jsonl \
           results/echo/squad_*.jsonl results/echo/RUNLOG_4bit.txt results/echo/scores/4bit_*.json
git commit -m "4-bit vs 8-bit confirmation: runs on the 24 GB Mac and the QIDK" && git push mine bc-runs
```
**Leave the server logs out of the commit** (`server4bit_*.log`). They are tens of MB each, and they made the last
fetch take 20 minutes.

**Do not look at the scores and then rerun or drop an arm.** If something looks wrong, write it down and send it back
as it is.
