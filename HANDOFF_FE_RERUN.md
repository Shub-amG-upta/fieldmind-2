# Handoff: FaultExplainer rerun on the SM8750 (for the Claude session on Gagan's Mac)

Written 2026-11-13 on Shubham's laptop. The rules are **Amendment A2** in `reports/ext_faultexplainer_prereg.md`,
agreed by Shubham on 2026-11-13 before any rerun call. Read A2 first; this file only turns it into steps.

**What this is:** the first FaultExplainer run (F1, 13 Nov 01:56) is invalid because 104 of 108 replies were "@"
garbage. This reruns it with 2 NPU threads, and adds the same model at 8-bit.

**Time:** about 4–5 hours of board time for both arms with cooling (estimate; the first four calls of F1 took 33–46 s
each at 6 threads).

**Rules that hold for every step:**
- **Do not read replies or picks, and do not run `score`.** Use `health` only: it reads no pick. Scoring happens on
  Shubham's laptop, beside the code-only baseline.
- Laptop time only. Log chip temperature before and after every block.
- Do not delete anything on the board without Gagan's OK.
- If a step's check fails, stop at that step and report. Do not rerun, drop or change an arm on your own.

---

## 1. Get the code
The garbage rule and `health` are on branch `fe-baseline` of Shubham's repository.
```
cd ~/projects/fieldmind-bc
git fetch <Shubham's remote> fe-baseline && git merge FETCH_HEAD
env -u PYTHONPATH .venv/bin/python -m pytest -q tests/test_ext_faultexplainer.py tests/test_ext_faultexplainer_baseline.py
```
Expect every test to pass (21 passed and 1 skipped on Shubham's laptop; the skipped one runs where the FaultExplainer
checkout is present).

## 2. Board: is the 8-bit file there?
S3 must be stopped first (Shubham said he will stop it; confirm nothing is running on the board).
```
adb -s 1d9c8f40 shell sha256sum /data/local/tmp/llm/Llama-3.2-3B-Instruct-Q8_0-pure.gguf
```
- **It prints `d91f61aba2e998c3fbfb46a4cd0710e8ed4c9b9fca2d4290f6dfc80ad0738fc2`:** go on.
- **The file is missing:** check the space (`adb -s 1d9c8f40 shell df -h /data/local/tmp`). It needs 3,421,899,488
  bytes. Push `~/fieldmind-build/gguf/Llama-3.2-3B-Instruct-Q8_0-pure.gguf`, then run the `sha256sum` line again.
- **Not enough room, or the sha256 differs:** stop and report. The 4-bit arm (steps 3–5) can still run.

The file must also be in `bench.board.CANDIDATES`. The entry exists in the `nd-paper` checkout's `bench/board.py`.

## 3. Start the NPU lane with 2 threads
Start the lane the way the m9 runs set the thread count (`ND_LANE_ENV`, as in `results/nd/run_m9_temp.sh`), from the
checkout whose `bench/board.py` supports it (`nd-paper`):
```
cd ~/projects/fieldmind
ND_LANE_ENV="GGML_HEXAGON_NHVX=2" env -u PYTHONPATH .venv/bin/python -m bench.board start npu \
    Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf > ~/projects/fieldmind-bc/results/ext/fe_lane_q4.txt 2>&1
```
**Confirm in the lane's startup log, and copy the lines into `results/ext/fe_lane_q4.txt`:**
- every layer is on HTP0, including the output layer, with a nonzero HTP0 buffer;
- the thread line shows 2 threads (the line your m9 report quotes as `threads 2, hmx 1`).

If either is missing, stop: the run would not be the agreed setting.

## 4. The 8-call check (not scored)
Cool the chip first (the `cool` and `temp` functions of `results/run_s3_sm8750.sh`: idle + 5 °C, at most 900 s).
```
cd ~/projects/fieldmind-bc
PYTHONPATH= .venv/bin/python bench/ext_faultexplainer.py run reports/data/ext_faultexplainer_requests.json \
    --url http://127.0.0.1:8080 --model Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf \
    --label check_nhvx2 --forms app --limit 2 --out results/ext/fe_check_nhvx2.jsonl
PYTHONPATH= .venv/bin/python bench/ext_faultexplainer.py health results/ext/fe_check_nhvx2.jsonl
```
That is 8 calls (2 requests, `app` form, 4 orderings).

| `health` says | do |
|---|---|
| `garbage` 0 and `errors` 0 | the setting passes: go to step 5 with `NHVX=2` |
| any garbage or error | stop the lane, start it again with `GGML_HEXAGON_NHVX=1`, repeat this step with label `check_nhvx1` and file `fe_check_nhvx1.jsonl` |
| `NHVX=1` also fails | use the CPU lane (`bench.board start cpu …`, port 8081), label `check_cpu`; if that passes, the arms run on the CPU lane and are labelled so |
| the CPU lane fails too | stop and report |

Write down which setting passed. **Both arms use it.**

## 5. Arm F1r: the 3B at 4-bit
Three blocks of 36 calls, one per form, in this order: `eval`, `eval_noleak`, `app`. Before each block: cool as in
step 4 and log the temperature. After each block: log the temperature.
```
PYTHONPATH= .venv/bin/python bench/ext_faultexplainer.py run reports/data/ext_faultexplainer_requests.json \
    --url http://127.0.0.1:8080 --model Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf \
    --label F1r_npu_nhvx2 --forms <form> --out results/ext/faultexplainer_F1r.jsonl
```
- Use the label that matches the setting: `F1r_npu_nhvx2`, `F1r_npu_nhvx1` or `F1r_cpu`.
- The same output file for all three blocks. The run resumes: a call already in the file is not sent again.
- After the third block:
  ```
  PYTHONPATH= .venv/bin/python bench/ext_faultexplainer.py health results/ext/faultexplainer_F1r.jsonl
  ```
  - `calls` must be 108.
  - **`may_be_scored` false** (more than 5% garbage): the arm is invalid. Report it as it is and go on to step 6.
    Do not rerun it.

## 6. Arm F2: the same model at 8-bit
Stop the lane. Start it with the 8-bit file and **the same setting**, saving to `results/ext/fe_lane_q8.txt`, and make
the same two log checks as in step 3. Then the same three blocks with cooling:
```
PYTHONPATH= .venv/bin/python bench/ext_faultexplainer.py run reports/data/ext_faultexplainer_requests.json \
    --url http://127.0.0.1:8080 --model Llama-3.2-3B-Instruct-Q8_0-pure.gguf \
    --label F2_npu_nhvx2_q8 --forms <form> --out results/ext/faultexplainer_F2.jsonl
PYTHONPATH= .venv/bin/python bench/ext_faultexplainer.py health results/ext/faultexplainer_F2.jsonl
```
There is no separate 8-call check for the 8-bit file. Its validity is the 5% rule on the full arm.

## 7. Hand back
```
bench.board stop        # both lanes
git add -f results/ext/fe_check_*.jsonl results/ext/faultexplainer_F1r.jsonl results/ext/faultexplainer_F2.jsonl \
           results/ext/fe_lane_q4.txt results/ext/fe_lane_q8.txt <your temperature log> <the three health outputs>
git commit -m "FaultExplainer rerun (A2): F1r and F2 on the SM8750, <setting>; health only, not scored"
```
Push `bc-runs` as usual and tell Shubham. Leave out any server log over 10 MB.

**In the commit message or a short note, state:**
- which setting passed the check, and what the failed ones showed;
- the three `health` outputs;
- start and end time and temperature of every block;
- anything that deviated from this file.

---

## What Shubham's side could not check
- Whether `NHVX=2` avoids the "@" failure on these prompts. The 0-of-1,000 result is on agent prompts of about 750
  tokens; these are 2,471–2,642. Step 4 is the test.
- Whether the 8-bit file is on the SM8750, and whether there is room for it.
- The exact wording of the thread line in the lane log.
- The speed of the 8-bit file on this board.
