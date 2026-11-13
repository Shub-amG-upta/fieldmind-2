# Mac run: the reading test (for the Claude session on Gagan's 24 GB Mac)

Written 2026-11-14 on Shubham's laptop. Branch `fe-baseline`. Rules: `reports/reading_test_prereg.md`.
**The full run starts only after that file is agreed and dated under "Agreed".** The pilot can run before.

**What it tests:** whether the model's hidden signal comes from the evidence or from the code's belief line, and whether
judging each case alone (yes/no) beats the code's first answer. **Time:** one night, about 8–10 hours.

## 1. Get the code
```
cd ~/projects/fieldmind-bc
git fetch mine fe-baseline && git merge FETCH_HEAD
env -u PYTHONPATH .venv/bin/python -m pytest -q tests/test_reading_test.py tests/test_echo_4bit.py   # expect all pass
```

## 2. Pilot (5 minutes, not scored)
```
LIMIT=2 OUT=/tmp/reading_pilot bench/reading_test_runs.sh pilot ~/fieldmind-build/gguf/board/Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf
```
`/tmp/reading_pilot` should hold `reading_list_pilot.jsonl` (6 rows) and `reading_per_case_pilot.jsonl` (7 rows),
all `"status": "ok"`.

## 3. Full run (after "Agreed")
```
G=~/fieldmind-build/gguf
caffeinate -dimsu bench/reading_test_runs.sh \
  m1_q4_0             $G/board/Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf \
  m2_q8_0             $G/Llama-3.2-3B-Instruct-Q8_0-pure.gguf \
  m3_qwen25_7b_q8_0   $G/Qwen2.5-7B-Instruct-Q8_0-pure.gguf \
  m4_llama31_8b_q8_0  $G/Meta-Llama-3.1-8B-Instruct-Q8_0-pure.gguf \
  m7_qwen3_17b_q8_0   $G/Qwen3-1.7B-Q8_0-pure.gguf
```
- Use exactly these labels and the same files as the 4-bit run (`results/echo/RUNLOG_4bit.txt`).
- Restart with the same command if it stops; a failed step writes `FAILED` to `results/echo/RUNLOG_reading.txt`.
- The 3B arms go first.

## 4. Hand back
```
git add -f results/echo/reading_*.jsonl results/echo/RUNLOG_reading.txt
git commit -m "reading test: Mac runs (not scored)"
```
Push `bc-runs` and tell Shubham. Leave the server logs out. **Do not score, rerun or drop anything after looking.**

---

## 5. The same test on TEP and Cranfield (only after Amendment A1 is agreed)
The rules are in `reports/reading_test_prereg.md`, Amendment A1. These are two new request files, with the same
arms, labels and files as above:

| set | file | requests | what it is |
|---|---|---|---|
| TEP | `reports/data/reading_requests_tep.json` | 400 | **held out**: new dev run 13, never used before |
| Cranfield | `reports/data/reading_requests_cranfield.json` | 141 | **not held out**: set R's scored Cranfield prompts |

**Changes from set H:**
- **The script sends the `original` form too.** For set H those rows came from the 4-bit run; the new sets have
  none.
- **Outputs get the suffix:** `h_prior_<label>_tep.jsonl`, `reading_list_<label>_tep.jsonl`,
  `reading_per_case_<label>_tep.jsonl`, and the same with `_cranfield`.
- **The script refuses** another request file without `SUFFIX`.

**Pilot (not scored):**
```
LIMIT=2 REQ=reports/data/reading_requests_tep.json SUFFIX=_tep OUT=/tmp/reading_pilot2 \
  bench/reading_test_runs.sh pilot ~/fieldmind-build/gguf/board/Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf
```
Expect 2 rows in `h_prior_pilot_tep.jsonl`, 6 in `reading_list_pilot_tep.jsonl` and 7 in
`reading_per_case_pilot_tep.jsonl`, all `"status": "ok"`. For Cranfield (`_cranfield`), expect 2, 6 and 5.

**Full run (TEP first, then Cranfield):**
```
G=~/fieldmind-build/gguf
ARMS=(m1_q4_0 $G/board/Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf  m2_q8_0 $G/Llama-3.2-3B-Instruct-Q8_0-pure.gguf
      m3_qwen25_7b_q8_0 $G/Qwen2.5-7B-Instruct-Q8_0-pure.gguf  m4_llama31_8b_q8_0 $G/Meta-Llama-3.1-8B-Instruct-Q8_0-pure.gguf
      m7_qwen3_17b_q8_0 $G/Qwen3-1.7B-Q8_0-pure.gguf)
REQ=reports/data/reading_requests_tep.json SUFFIX=_tep caffeinate -dimsu bench/reading_test_runs.sh $ARMS
REQ=reports/data/reading_requests_cranfield.json SUFFIX=_cranfield caffeinate -dimsu bench/reading_test_runs.sh $ARMS
```

**Calls per arm:**

| set | original | list | per-case |
|---|---|---|---|
| TEP | 400 | 1,200 | 1,466 |
| Cranfield | 141 | 423 | 304 |
| set H, for comparison | – | 1,200 | 1,354 |

**Time (estimated from set H's night, not timed):** TEP about 10–12 h, Cranfield about 3 h.

**Hand back:**
```
git add -f results/echo/h_prior_*_tep.jsonl results/echo/h_prior_*_cranfield.jsonl \
           results/echo/reading_*_tep.jsonl results/echo/reading_*_cranfield.jsonl results/echo/RUNLOG_reading.txt
git commit -m "reading test, TEP and Cranfield: Mac runs (not scored)"
```
Same rule: **no score, rerun or drop after looking.**
