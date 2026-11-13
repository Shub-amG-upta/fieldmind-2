# QIDK runs, in order (for the Claude session on Gagan's Mac)

Written 2026-11-13 on Shubham's laptop. Board: **SM8750 `1d9c8f40`, always at 2 NPU threads** (`GGML_HEXAGON_NHVX=2`).
Everything needed is on branch `fe-baseline` (it contains `bc-build`).

| # | run | time | may start when |
|---|---|---|---|
| A | 4-bit vs 8-bit confirmation, NPU part (Llama 3B, 4-bit then 8-bit, 400 calls each) | about 1.5 h | now: its Amendment A2 is agreed (2026-11-13) |
| B | FaultExplainer 8-bit run (F2, 108 calls) | about 3 h or more | now (its Amendment A2 in `reports/ext_faultexplainer_prereg.md` is agreed) |

**A is the more important run. If its amendment is not agreed when you start, do B first and A after.**

**Already done on Shubham's laptop (2026-11-13), do not repeat:** the FaultExplainer 8-call check (8 of 8 clean at
2 threads) and the 4-bit run F1r (108 calls, 0 errors, 0 garbage). So the setting is fixed at `NHVX=2`.

**Rules for both runs:** laptop time only; temperature before and after every block; do not read replies or scores
and then rerun or drop anything; if a check fails, stop and report.

---

## 0. Setup (once)
```
cd ~/projects/fieldmind-bc
git fetch mine fe-baseline && git merge FETCH_HEAD        # "mine" = Shubham's repository, as in the earlier handoffs
env -u PYTHONPATH .venv/bin/python -m pytest -q tests/test_ext_faultexplainer.py tests/test_ext_faultexplainer_baseline.py \
    tests/test_echo_4bit.py tests/test_nd_board_knobs.py tests/test_board_env.py        # expect all pass
env -u PYTHONPATH .venv/bin/python -m bench.board stop    # a lane from Shubham's laptop may still be running
```
**Put the 8-bit Llama 3B on the board** (the board had 4.6 GB free at 15:04; the file is 3.4 GB):
```
adb -s 1d9c8f40 shell ls -la /data/local/tmp/llm/Llama-3.2-3B-Instruct-Q8_0-pure.gguf    # there already? skip the push
adb -s 1d9c8f40 push ~/fieldmind-build/gguf/Llama-3.2-3B-Instruct-Q8_0-pure.gguf /data/local/tmp/llm/
adb -s 1d9c8f40 shell sha256sum /data/local/tmp/llm/Llama-3.2-3B-Instruct-Q8_0-pure.gguf
#   must be d91f61aba2e998c3fbfb46a4cd0710e8ed4c9b9fca2d4290f6dfc80ad0738fc2 ; otherwise stop
```

## A. 4-bit vs 8-bit confirmation, NPU part
Follow `HANDOFF_4BIT.md`, section "QIDK", step Q2 exactly (Q1 is the push above). In short, for the 4-bit file and then
the 8-bit file:
```
env -u PYTHONPATH .venv/bin/python -m bench.board stop
env -u PYTHONPATH .venv/bin/python -m bench.board temp
ND_LANE_ENV="GGML_HEXAGON_NHVX=2" env -u PYTHONPATH .venv/bin/python -m bench.board start npu <model file>
env -u PYTHONPATH .venv/bin/python -m bench.board log npu | grep -i -E "hwinfo|offloaded|HTP0 model buffer"
env -u PYTHONPATH .venv/bin/python bench/echo_4bit.py run prior reports/data/echo_4bit_requests.json \
    --url http://127.0.0.1:8080 --lane npu --forms original \
    --model <model file> --label <npu_q4_0 | npu_q8_0> --out results/echo/h_prior_<label>.jsonl
env -u PYTHONPATH .venv/bin/python -m bench.board temp
```
- Model files: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf` (label `npu_q4_0`), then
  `Llama-3.2-3B-Instruct-Q8_0-pure.gguf` (label `npu_q8_0`).
- **The log must show `HTP0 hwinfo: threads 2, hvx 2`,** every layer offloaded, and a nonzero HTP0 buffer. If not, stop.
- More than 20 failed calls of 400: move the file aside and rerun that arm once (`HANDOFF_4BIT.md` has the commands).
  Never change the thread count.

## B. FaultExplainer 8-bit run (F2)
```
env -u PYTHONPATH .venv/bin/python -m bench.board stop
ND_LANE_ENV="GGML_HEXAGON_NHVX=2" env -u PYTHONPATH .venv/bin/python -m bench.board start npu \
    Llama-3.2-3B-Instruct-Q8_0-pure.gguf > results/ext/fe_lane_q8.txt 2>&1
env -u PYTHONPATH .venv/bin/python -m bench.board log npu | grep -E "llama_model_loader: - type|HTP0 hwinfo|offloaded|HTP0 model buffer|n_slots" >> results/ext/fe_lane_q8.txt
cat results/ext/fe_lane_q8.txt     # must show: threads 2, hvx 2; offloaded 29/29 layers; a nonzero HTP0 buffer; q8_0: 197 tensors
caffeinate -dimsu zsh results/run_fe_rerun_sm8750.sh arm F2_npu_nhvx2_q8 Llama-3.2-3B-Instruct-Q8_0-pure.gguf results/ext/faultexplainer_F2.jsonl
```
- The script cools before each of the three blocks (`eval`, `eval_noleak`, `app`), logs times and temperatures to
  `results/ext/fe_rerun_log.txt`, and prints `health` at the end. It reads no reply and no pick. It resumes if stopped.
- **At the end `calls` must be 108.** If `may_be_scored` is false, report it as it is. Do not rerun.
- **Do not run `score`.** Scoring is done on Shubham's laptop beside the 4-bit run and the baseline.
- For reference, the 4-bit run took 12:20–15:04 with cooling, at about 11 tokens/s. The 8-bit speed is not known.

## Hand back
```
env -u PYTHONPATH .venv/bin/python -m bench.board stop
git add -f results/ext/faultexplainer_F2.jsonl results/ext/fe_lane_q8.txt results/ext/fe_rerun_log.txt \
           results/echo/h_prior_npu_*.jsonl results/echo/RUNLOG_4bit.txt
git commit -m "QIDK runs at NHVX=2: FaultExplainer F2 (8-bit) and the 4-bit confirmation's NPU arms; not scored"
```
Push `bc-runs` as usual and tell Shubham. Leave out server logs over 10 MB. State in the commit message which runs
finished, the `health` output, the failed-call counts, and anything that deviated from this file.
