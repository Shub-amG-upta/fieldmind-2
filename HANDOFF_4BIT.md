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

### 2. Build the five 8-bit files (about 30 min; needs the 16-bit GGUFs the first build left in `~/fieldmind-build/gguf`)
```
for n in Qwen2.5-0.5B-Instruct gemma-3-1b-it-qat Qwen3-1.7B Qwen2.5-7B-Instruct Meta-Llama-3.1-8B-Instruct; do
  bench/echo_4bit_runs.sh --q8 $n
done
```
- **Each must print `"verdict": "OK…"`.** If one does not, stop and don't use the file.
- **If a model's 4-bit build needed extra arguments** (see `logs/quantize_<name>.log`), pass the same ones after the name.
- **If a `-16bit.gguf` is missing,** rebuild it with `bench/build_candidate_gguf.sh <name> <hf_source_dir>` first.

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

## QIDK (after the Mac's Llama 3B arms; about 1.5 h with cooling)

Both files are in `bench.board.CANDIDATES`. For each of the two files, in this order: 4-bit, then 8-bit.

```
.venv/bin/python -m bench.board stop
.venv/bin/python -m bench.board temp                       # log it; wait for the usual cooling rule
.venv/bin/python -m bench.board start npu Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf
env -u PYTHONPATH .venv/bin/python bench/echo_4bit.py run prior reports/data/echo_4bit_requests.json \
    --url http://127.0.0.1:8080 --lane npu --forms original \
    --model Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf --label npu_q4_0 --out results/echo/h_prior_npu_q4_0.jsonl
.venv/bin/python -m bench.board temp
```
Then the same with `Llama-3.2-3B-Instruct-Q8_0-pure.gguf`, label `npu_q8_0`, output `h_prior_npu_q8_0.jsonl`.

- **Check the lane log** shows all layers on HTP0 for both files, as in every board run.
- **Save the two temperature readings per arm** in `results/echo/RUNLOG_4bit.txt` (laptop time).
- **400 calls per file,** about 3.3 s (4-bit) and 4.3 s (8-bit) each.

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
