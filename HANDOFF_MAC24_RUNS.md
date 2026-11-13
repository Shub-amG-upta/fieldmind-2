# 24 GB Mac runs, in order (for the Claude session on Gagan's Mac)

Written 2026-11-13 on Shubham's laptop. Everything needed is on branch `fe-baseline` (it contains `bc-build`).

| # | run | time | may start when |
|---|---|---|---|
| 1 | **4-bit vs 8-bit confirmation, Mac part:** six models at both precisions, plus the 16-bit Llama 3B | 10–12 h, one night | now: its rules (`reports/echo_4bit_prereg.md`, A1) are agreed. Amendment A2 there is about the board only |
| 2 | Prompt ablation | one night | **not built yet.** Nothing to run |

**This is the most important run of the paper right now.** It can run while the board is busy, but keep the Mac on its
charger with `caffeinate`, and note in the log if a board run was being driven at the same time.

The full details, the sha256 tables and the scoring commands are in `HANDOFF_4BIT.md`, section "MAC". The steps:

## 1. Get the code
```
cd ~/projects/fieldmind-bc
git fetch mine fe-baseline && git merge FETCH_HEAD        # "mine" = Shubham's repository, as in the earlier handoffs
env -u PYTHONPATH .venv/bin/python -m pytest -q tests/test_echo_4bit.py tests/test_echo_causes.py     # expect all pass
```

## 2. Get the five 8-bit files (built on Shubham's laptop; do not rebuild them)
Copy from Shubham's `~/fieldmind-build/gguf/` into `~/fieldmind-build/gguf/` (AirDrop or a USB drive, about 20 GB):
`Qwen2.5-0.5B-Instruct-Q8_0-pure.gguf`, `gemma-3-1b-it-qat-Q8_0-pure.gguf`, `Qwen3-1.7B-Q8_0-pure.gguf`,
`Qwen2.5-7B-Instruct-Q8_0-pure.gguf`, `Meta-Llama-3.1-8B-Instruct-Q8_0-pure.gguf`.
```
cd ~/fieldmind-build/gguf && shasum -a 256 *-Q8_0-pure.gguf
```
**Every sha256 must equal the table in `HANDOFF_4BIT.md` step 2.** A file that differs is not used.

## 3. Check the three small models hold the same weights at both precisions (10 min)
Run the weight-data script of `HANDOFF_4BIT.md` step 2b on your three board 4-bit files (Qwen 0.5B, Qwen3 1.7B,
Gemma 1B) and compare with the table there.
- **Equal:** use that model.
- **Different:** leave both of that model's arms out of step 5, and write both values in `results/echo/RUNLOG_4bit.txt`.

The 7B and 8B need no check: their 4-bit rebuild had exactly the recorded sha256.

## 4. Pilot (3 minutes, not scored)
```
LIMIT=3 OUT=/tmp/echo4bit_pilot bench/echo_4bit_runs.sh pilot ~/fieldmind-build/gguf/Llama-3.2-3B-Instruct-Q8_0-pure.gguf
```
Four steps print `start` and `end`; `/tmp/echo4bit_pilot` holds 4 `.jsonl` files.

## 5. Full run
```
G=~/fieldmind-build/gguf
caffeinate -dimsu bench/echo_4bit_runs.sh \
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
- Use exactly these labels and, for the old arms, the same files as before (`results/echo/RUNLOG.txt`).
- It can be stopped and restarted with the same command. A failed step writes `FAILED` to
  `results/echo/RUNLOG_4bit.txt`.
- The Llama 3B arms run first, so they are done even if the night is cut short.

## 6. Score and hand back
```
bench/echo_4bit_score.sh
git add -f results/echo/h_prior_*.jsonl results/echo/prior_*q8_0.jsonl results/echo/mmluprob_*.jsonl \
           results/echo/squad_*.jsonl results/echo/RUNLOG_4bit.txt results/echo/scores/4bit_*.json
git commit -m "4-bit vs 8-bit confirmation: Mac runs"
```
Push `bc-runs` as usual and tell Shubham. **Leave the server logs out** (`server4bit_*.log`, tens of MB each).
**Do not look at the scores and then rerun or drop an arm.**
