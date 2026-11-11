# Handoff: the echo replay, on a Mac (no QIDK)

For: Gagan, and the Claude session on his laptop. Written 2026-11-11 by Shubham's laptop session.
Branch: `sched-study`. Read the whole file before running anything.

---

## 1. What this test answers

At each tick the diagnostician gets a numbered list of candidate causes; the retrieval code puts its best guess on
line 1. In every saved board run, Llama 3.2 3B (the 4-bit board file, on the NPU) picks line 1 in 98–100% of
answers, **and still does when the list is shuffled**. When a prompt format made it choose for itself, its picks were
right about as often as a random pick. `reports/echo_saved.md` (tested tool, dev runs) has the numbers.

The open question: **is that copying caused by the 4-bit file, by the 3B size, or by the prompt?** We answer it by
sending the same saved prompts again, in the original and in shuffled orders, to several model files, and seeing which
ones keep picking line 1.

| outcome | meaning | paper |
|---|---|---|
| 1 | larger models stop copying and are right when they leave line 1 | B: a capability threshold |
| 2 | every model copies | B: a prompt or task effect |
| 3 | the higher-precision 3B reads the cases, the 4-bit file copies | C, standalone: quantization breaks reasoning |
| 4 | larger models leave line 1 but are wrong | none: check the case data first |

The exact rules are in `reports/echo_prereg.md`.

## 2. Why this needs no QIDK

1. **The question is about the model, not the chip.** Whether a model reads a list of options or copies its first line
   is a property of its weights and the prompt. The chip changes only the arithmetic. Your m4 probe measured that
   change: about 0.01 nats per token on the NPU, which flips near-ties. Echo is not a near-tie effect: the model picks
   line 1 in 100% of shuffled answers, so the choice does not depend on tiny numerical differences.
2. **The board's answers are already saved.** Every request in the replay set comes from a saved board run with the
   board's reply. The replay compares against them (fidelity check), so the board's side of the comparison exists
   without running it again.
3. **The comparisons need files and models the board can't easily run.**
   - 8-bit and 16-bit versions of the 3B.
   - 7–8B models.

   A Mac runs all of them with one backend, so every arm is compared under the same conditions.
4. **The board is needed elsewhere.** Energy measurements and the scheduling repeats can only be done on the QIDK.

**What the laptop cannot show:** that the copying looks the same on the NPU itself. That is an optional last check,
about an hour: the 4-bit file, original and shuffled orders, on the board's NPU lane. It can share a session with your
nondeterminism arms N/C. It is not needed to decide the outcome.

## 3. What is already done (Shubham's laptop, Apple M2 8 GB)

- **Tools:**
  - `bench/echo_test.py` with `saved`, `select`, `pairs`, `run`, `score` (with `--bootstrap`);
  - 18 tests in `tests/test_echo_test.py`, mutation-checked.
- **Request sets, fixed before any replay call:**
  - **R:** `reports/data/echo_requests.json`, 450 requests (150 per plant), from dev board runs `bevideas_A1`,
    `cranfield_dev_v3` and `af_tep_v3_board`, with seed 0. The rebuilt grammar accepts every saved reply (0 refused).
  - **L:** `reports/data/echo_letter_pairs.json`, 450 pairs of the same prompt with the group letters on and off, from
    mock dev runs, with seed 0. Only pairs that differ in the letters alone are kept.
- **Pre-registration draft:** `reports/echo_prereg.md`. Its stop rule and outcome thresholds are PROPOSED.
- **The pinned llama.cpp built for macOS:**
  - commit `99b95488c` (`llama-server --version` prints `build 11371, commit 99b95488c`);
  - `llama-quantize` and `llama-server`.
- **Weights:** `unsloth/Llama-3.2-3B-Instruct` @ `006f5dcd1393c3add266de40994ba96225e9689d`. This is the source the board
  file was built from (`reports/phase0b_board_setup.md`); ungated, licence `llama3.2`.
- **Board file rebuilt, and its sha256 does NOT match the board's file.**
  - Ours: 2,012,613,344 B, sha256 `dace5753…`. Board: 2,012,612,832 B, sha256 `5aa3ece5…`.
  - The sizes differ by 512 bytes, which points at the header rather than the weights, but that is not proven.
  - Section 5c says how to settle it. Until then the laptop rebuild is **not** called the board file.
- `bench/build_candidate_gguf.sh` now runs on macOS too (`stat` and `sha256` differ from Linux).

**No replay call has been made.** The pre-registration forbids it until the thresholds are agreed.

## 4. Before the first model call: agree the thresholds

Read `reports/echo_prereg.md` with Shubham. Agree or change the PROPOSED items:
- **the stop rule:** original-order rank-1 agrees with the saved board rank-1 on at least 80% of requests;
- **"copies position":** shuffled line-1 share >= 0.8 and position invariance <= 0.5;
- **"reads the cases":** invariance >= 0.8 and shuffled rank-1 accuracy within 0.05 of the original;
- **"helps beyond line 1":** deviation accuracy above line 1's and a random line's, with 95% intervals not overlapping;
- **the bootstrap seed:** 20261111.

Write the agreement under "Amendments" with the date and who agreed, and commit it. **Only then** start section 6.

## 5. Build the model files on your Mac

You need a Mac with enough memory for the largest arm (a 7–8B Q4_0 file is about 4.5 GB, a 3B 16-bit file about
6.4 GB). Every command runs with `PYTHONPATH` unset.

```bash
# 5a. the pinned llama.cpp (host tools only, Metal on)
mkdir -p ~/fieldmind-build && cd ~/fieldmind-build
git clone --filter=blob:none https://github.com/ggml-org/llama.cpp.git llama.cpp
git -C llama.cpp checkout 99b95488cac0f00ce3f05af113a8c1e287753f87
uv venv -p 3.13 venv-convert
uv pip install -p venv-convert/bin/python cmake ninja
(cd llama.cpp/requirements && uv pip install -p ~/fieldmind-build/venv-convert/bin/python -r requirements-convert_hf_to_gguf.txt)
PATH=$HOME/fieldmind-build/venv-convert/bin:$PATH cmake -S llama.cpp -B llama.cpp/build-host -G Ninja \
    -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF
PATH=$HOME/fieldmind-build/venv-convert/bin:$PATH cmake --build llama.cpp/build-host --target llama-quantize llama-server -j 8
llama.cpp/build-host/bin/llama-server --version      # must print: build 11371, commit 99b95488c

# 5b. the 3B weights the board file was built from
hf download unsloth/Llama-3.2-3B-Instruct --revision 006f5dcd1393c3add266de40994ba96225e9689d \
    --local-dir ~/fieldmind-build/hf/Llama-3.2-3B-Instruct

# 5c. M1 is THE BOARD'S OWN FILE, sha256 5aa3ece50ab33d09a7181888a75f8755f924c662dc99626e7f45440adfeadcdb
#     (bench.board.CANDIDATES). Take it from wherever you have a copy, or pull it once from the board.
#     That is file storage only: nothing runs on the QIDK.
adb pull /data/local/tmp/llm/Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf ~/fieldmind-build/gguf/board/
shasum -a 256 ~/fieldmind-build/gguf/board/Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf   # must be 5aa3ece5...
#     Rebuilding with the recipe on Shubham's Mac gave a DIFFERENT file (dace5753..., 512 B longer).
#     Settle whether only the header differs: hash the weight data alone, and dump the headers.
cd ~/fieldmind-build && PYTHONPATH=llama.cpp/gguf-py venv-convert/bin/python - <<'PY'
import hashlib, sys
from gguf import GGUFReader
p = "gguf/board/Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf"
r = GGUFReader(p); h = hashlib.sha256()
with open(p, "rb") as f:
    f.seek(r.data_offset)
    for c in iter(lambda: f.read(1 << 24), b""): h.update(c)
print("header bytes", r.data_offset, "weight-data sha256", h.hexdigest())
for k, fld in r.fields.items():
    if k not in ("tokenizer.ggml.tokens", "tokenizer.ggml.merges", "tokenizer.ggml.token_type"):
        try: print(k, str(fld.contents())[:100])
        except Exception: print(k, "?")
PY
#     Shubham's rebuild: header 7,838,176 B, weight-data sha256
#     644749ed0992ce9857be54413f2da27173205f5111827e428a04a4edb23a7e81.
#     Same weight-data hash: the weights are identical and only the header differs. Record which header
#     fields differ in the report; M2 (built by the same pipeline as the rebuild) is then comparable.
#     Different hash: the rebuild is not the board's model. Report it and build M2 from whatever produced
#     the board file before comparing M1 with M2.
#     Optionally also run the recipe yourself (bench/build_candidate_gguf.sh) and compare with dace5753...:
#     the same result on two Macs shows the pipeline is deterministic.

# 5d. M2: the same 3B at Q8_0, and M2b: the 16-bit file itself
~/fieldmind-build/llama.cpp/build-host/bin/llama-quantize --pure \
    ~/fieldmind-build/gguf/Llama-3.2-3B-Instruct-16bit.gguf ~/fieldmind-build/gguf/Llama-3.2-3B-Instruct-Q8_0-pure.gguf Q8_0
#     M2b uses ~/fieldmind-build/gguf/Llama-3.2-3B-Instruct-16bit.gguf as it is (BF16)
```

**M3 and M4, the larger models: PROPOSED, confirm with Shubham before building.**
- **Models:** one 7–8B instruct model each from two families, e.g. Qwen2.5-7B-Instruct and Llama-3.1-8B-Instruct.
- **Build:** with the same recipe (`bench/build_candidate_gguf.sh <name> <hf dir>`, Q4_0 with embeddings Q8_0), so model
  size changes while the 4-bit format stays the same as M1's.
- **Record** each repo, revision sha and file sha256 in the report.

Record the sha256 of every file you build. Shubham's laptop rebuilt M1 and M2. If your sha256 values match, both
machines built identical files.

## 6. Run the replay (only after section 4)

One `llama-server` at a time, the same flags for every arm (the lanes' flags, Metal on):

```bash
~/fieldmind-build/llama.cpp/build-host/bin/llama-server -m <file.gguf> --port 8090 \
    -c 4096 -np 1 --cache-ram 0 -ngl 99
```

For each arm (label examples: `m1_q4_0`, `m2_q8_0`, `m2b_bf16`, `m3_<model>`, `m4_<model>`):

```bash
# 6a. pilot, M1 only, first time: 20 requests, original order. Read only the call time and the fidelity line.
.venv/bin/python bench/echo_test.py run reports/data/echo_requests.json --url http://127.0.0.1:8090 \
    --model <file> --label pilot_m1 --only original --limit 20 --out results/echo/pilot.jsonl
.venv/bin/python bench/echo_test.py score reports/data/echo_requests.json results/echo/pilot.jsonl \
    | grep original_agrees_with_saved_rank1
#     below 0.80 = stop rule: the replay is not reproducing the system. Stop and report.

# 6b. the replay set R, all four orderings (resumes if interrupted)
.venv/bin/python bench/echo_test.py run reports/data/echo_requests.json --url http://127.0.0.1:8090 \
    --model <file> --label <arm> --out results/echo/R_<arm>.jsonl

# 6c. the letter set L, original order, letters off and on
.venv/bin/python bench/echo_test.py run reports/data/echo_letter_pairs.json --url http://127.0.0.1:8090 \
    --model <file> --label <arm>_letters_off --field prompt --only original --out results/echo/L_<arm>.jsonl
.venv/bin/python bench/echo_test.py run reports/data/echo_letter_pairs.json --url http://127.0.0.1:8090 \
    --model <file> --label <arm>_letters_on --field prompt_letters --only original --out results/echo/L_<arm>.jsonl
```

**Size:** each arm is 1,800 calls (R) and 900 calls (L). The pilot's call time × 2,700 gives the hours per arm.

**Order:** M1, then M2 (deciding outcome 3 needs only these two), then M2b, M3, M4.

Log the laptop model and memory, the server command line, and the start and end times of every arm.

## 7. Score and report

```bash
.venv/bin/python bench/echo_test.py score reports/data/echo_requests.json results/echo/R_*.jsonl --bootstrap 2000
.venv/bin/python bench/echo_test.py score reports/data/echo_letter_pairs.json results/echo/L_*.jsonl --bootstrap 2000
# and each plant on its own (the pre-registration reports both):
for plant in boiler cranfield tep; do
  .venv/bin/python bench/echo_test.py score reports/data/echo_requests.json results/echo/R_*.jsonl --bootstrap 2000 --plant $plant
done
```

Write `reports/echo_replay.md` in the project's report format:
- one row per arm, pooled and per plant: line-1 share per ordering, position invariance, rank-1 right (exact and group), deviation accuracy
  against line 1 and a random line, all with 95% intervals;
- the letter arm: letters off against on;
- the outcome the pre-registered rules give, applied exactly. A combination the rules do not name is reported as
  found, with no outcome label.

Commit `results/echo/` with `git add -f`, because `results/` is gitignored. Tell Shubham before pushing.

**Rules that still apply:**
- dev requests only (the tool refuses others);
- no thresholds changed after the first call;
- every number labelled as a laptop replay of the model, not an NPU result;
- if a number moves and you can't say why, stop and write it down.

## 8. Shubham's laptop: state at handoff (2026-11-11, Apple M2 8 GB, laptop times)

| file (`~/fieldmind-build/gguf/`) | bytes | sha256 | check |
|---|---|---|---|
| `Llama-3.2-3B-Instruct-16bit.gguf` (BF16, from `unsloth/...@006f5dcd`) | 6,433,688,288 | `f9e8a86e31f69ff852b7fe5fe18eee2fcae8c1efedeb2af13e64a25a81a2d0c9` | converted at the pinned commit |
| `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf` (recipe rebuild) | 2,012,613,344 | `dace5753a5f65563cddf239d856e107d5683740f4c0735e7ee24b670286d0e37` | 196 Q4_0, token_embd Q8_0, output tied. **Does not match the board's `5aa3ece5…` (2,012,612,832 B)**; weight-data sha256 `644749ed…`, header 7,838,176 B |
| `Llama-3.2-3B-Instruct-Q8_0-pure.gguf` (M2) | 3,421,899,488 | `d91f61aba2e998c3fbfb46a4cd0710e8ed4c9b9fca2d4290f6dfc80ad0738fc2` | 197 Q8_0 (`bench.gguf_types`: every matrix Q4_0/Q8_0) |

- **The server works on this Mac.** A load test of the rebuild (`-ngl 99`, Metal, one dummy prompt, not a replay
  request) wrote about 40 tok/s.
- **Rough size of the replay here:** about 1.5–2 h per arm. That is an estimate from the load test; the pilot gives
  the real figure.
- **No replay call was made.** The thresholds are not yet agreed.
- **What this Mac can still do:** M1 and M2 once the thresholds are agreed (8 GB is enough for both). The 16-bit file
  (6.4 GB) and the 7–8B arms are better run on your M5.
- **Run every arm on one machine,** so machine differences do not enter the comparison. Simplest: you run all arms;
  this Mac repeats M1 as a cross-machine check.
