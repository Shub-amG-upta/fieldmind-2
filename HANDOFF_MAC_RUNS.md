# Runs for the 24 GB Mac and the QIDK board (branch `bc-runs`)

Written 2026-11-12. Everything here is ready to run. Results go in `results/echo/` (Mac) or `results/benchmarks/` (board). Commit them on
`bc-runs` and push; scoring and write-up happen on `bc-build`.

**Before the first full run:** the rules must be agreed and dated under "Agreed":
- for ECHO: `reports/echo_causes_prereg.md`;
- for the board items: the file named with each item.

The pilots below can run before that. They are not scored.

---

## ECHO (on the Mac): why does the model copy line 1?

One script runs everything for each model, one server at a time. It is resumable: a stopped run picks up where it was.
For each model it runs:

| step | what | why |
|---|---|---|
| R | the 450 questions in 4 orders | E5, size curve |
| L | letters off / on | – |
| relabel | label vs position | E6 |
| prior | what the model prefers before reading | E7 |
| mmlu | 300 public questions, options rotated | E8, control |

For m1–m4, R and L are already done, so the script skips them by itself.

### 1. Get the code
```
git fetch mine && git switch bc-runs     # or: git switch -c bc-runs mine/bc-runs
env -u PYTHONPATH .venv/bin/python -m pytest -q tests/test_echo_causes.py tests/test_echo_test.py   # expect all pass
```

### 2. Get the model files
**The board's three small files:** copy them and check them against `bench.board.CANDIDATES`.
```
for f in Qwen2.5-0.5B-Instruct-Q4_0-pure-embq8.gguf gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf Qwen3-1.7B-Q4_0-pure-embq8.gguf; do
  adb pull /data/local/tmp/llm/$f ~/fieldmind-build/gguf/board/$f
done
env -u PYTHONPATH .venv/bin/python -c "
import hashlib, pathlib; from bench.board import CANDIDATES
for f, want in CANDIDATES.items():
    p = pathlib.Path.home() / 'fieldmind-build/gguf/board' / f
    if p.exists(): print(f, 'OK' if hashlib.sha256(p.read_bytes()).hexdigest() == want else 'MISMATCH')"
```
**The 14B** (optional, do it last). It needs about 70 GB of free disk while building. Record the revision it prints.
```
hf download Qwen/Qwen2.5-14B-Instruct --local-dir ~/fieldmind-build/hf/Qwen2.5-14B-Instruct
bench/build_candidate_gguf.sh Qwen2.5-14B-Instruct ~/fieldmind-build/hf/Qwen2.5-14B-Instruct
```

### 3. Pilot (2 minutes, not scored)
```
LIMIT=2 OUT=/tmp/echo_pilot bench/echo_mac_runs.sh pilot ~/fieldmind-build/gguf/board/Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf
OUT=/tmp/echo_pilot bench/echo_mac_score.sh
```
Every step should print `start` and `end`, and `/tmp/echo_pilot` should hold 5 `.jsonl` files.

### 4. Full run (after the rules are agreed)
```
G=~/fieldmind-build/gguf
bench/echo_mac_runs.sh \
  m1_q4_0            $G/board/Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf \
  m5_qwen25_05b_q4_0 $G/board/Qwen2.5-0.5B-Instruct-Q4_0-pure-embq8.gguf \
  m6_gemma3_1b_q4_0  $G/board/gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf \
  m7_qwen3_17b_q4_0  $G/board/Qwen3-1.7B-Q4_0-pure-embq8.gguf \
  m2_q8_0            <the Q8_0 file you used before> \
  m2b_bf16           <the 16-bit file you used before> \
  m3_qwen25_7b_q4_0  <the Qwen 7B file you used before> \
  m4_llama31_8b_q4_0 <the Llama 8B file you used before> \
  m8_qwen25_14b_q4_0 $G/Qwen2.5-14B-Instruct-Q4_0-pure-embq8.gguf
```
- **Use the same labels and files as the first replay for m1–m4.** That is how R and L get skipped (`results/echo/RUNLOG.txt` has the paths).
- **About two nights in total.** It can be stopped and restarted at any time.

### 5. Score and hand back
```
bench/echo_mac_score.sh
git add results/echo && git commit -m "echo causes: E5-E8 runs on the 24 GB Mac" && git push mine bc-runs
```

---

## SCHED (on the QIDK): scheduling on the phone

**Every board run:**
- `/board-up` first;
- chip temperature logged before and after, with a cooling gap between runs;
- laptop time only.

| # | what | command | when |
|---|---|---|---|
| S1 | Reading-speed check against arXiv 2605.27435, 30 min | `env -u PYTHONPATH .venv/bin/python bench/paperB_board.py plan --item 8`, then run what it prints | **now** |
| S2 | `calibrated_finish`, 3–4 h | `bench/paperB_board.py plan --item 6` | after `reports/sched_fix.md` part D is agreed |
| S3 | More episodes, 3 repeats, 2–3 nights | `bench/paperB_board.py plan --item 7` | after its cells are agreed |

**After S1, restore the lane to its normal flags.**

**Agreed 2026-11-13 00:35 (laptop time) by Gagan (human instruction: "s2, s3, f3 just agree"), on behalf of the team. Shubham was not consulted before this agreement.** S2 (part D), S3 (item 7's cells as listed in `bench/paperB_board.py`: ITEM7_CELLS, ITEM7_EPISODES, 3 repeats) and F3 (`reports/ext_faultexplainer_prereg.md`) are agreed as written, and they run on the SM8750, the new board (the SM8650 was exchanged).

---

## OUTSIDE CHECK (on the QIDK): FaultExplainer

| # | what | command | when |
|---|---|---|---|
| F3 | Our 3B on the NPU through FaultExplainer's own prompts, original and shuffled, 1.5–2.6 h | `bench/paperB_board.py plan --item 1` | after `reports/ext_faultexplainer_prereg.md` is agreed |

It needs FaultExplainer's repository at commit `2fcfee9` (`FAULTEXPLAINER_REPO=<path>`; see the prereg).

---

## FIXES and ENERGY (on the QIDK, later)

| # | what | when |
|---|---|---|
| X2 | The published fixes that helped on the Mac (`--item 2`, cut down) | after ECHO is scored |
| P2 | Energy on the runs above (`bench/energy.py`) | when the power meter arrives |
| P3 | The model that reads best, on the NPU: does it fit, and what does it cost? | after ECHO is scored |

---

**Run checks:**
- **A step fails:** the script stops and writes `FAILED` to `RUNLOG.txt`. Rerun the same command and it resumes.
- **A file's sha256 is wrong:** stop, and don't use the file.
