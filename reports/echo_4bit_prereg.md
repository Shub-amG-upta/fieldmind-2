# Does the 4-bit file lose what the 8-bit file knows? Pre-registration

**Status: AGREED 2026-11-13 (A1 below), before any full run. Was DRAFT, written 2026-11-13 before any of these runs.**
The plumbing pilot on this laptop (3 requests per test) is not scored.

**Where this comes from:** `reports/echo_hidden_signal_exploratory.md`. That analysis was done after looking at saved
runs, so it proves nothing by itself. This run is the test of it.

| item | value |
|---|---|
| Code | `bench/echo_4bit.py`, `bench/echo_4bit_runs.sh`, `bench/echo_4bit_score.sh` (tests: `tests/test_echo_4bit.py`) |
| Settings | as `reports/echo_causes_prereg.md`: pinned llama.cpp `99b95488c`, `-c 4096 -np 1 --cache-ram 0 -ngl 99`, temperature 0, seed 0, the system's grammar, diagnostician cap 60, top-20 token probabilities |
| Nature of the numbers | laptop replays, **not NPU results**, except the two `npu_` arms. Boiler data is synthetic. MMLU and SQuAD are public |
| Intervals | 95%, 2,000 resamples, seed 20261111. Agent prompts resample **episodes**; MMLU and SQuAD resample **questions** |

## The question
For the same weights at two precisions, the answers are nearly the same line. **Does the 4-bit file's probability on
line 1 still say whether line 1 is right, as the 8-bit file's does?**

## Data

### Set H: held-out agent prompts (the primary test)
- `reports/data/echo_4bit_requests.json`, sha256 `7545212c…9c131`.
- **400 scored boiler requests from 9 dev episodes** that are in no earlier request set (the builder refuses an
  episode or prompt that is in set R).

  | episode | requests |
  |---|---|
  | `dev_A03_bfp_suction` | 37 |
  | `dev_A05_fcv_caught` | 22 |
  | `dev_A06_fcv_seize_repeat` | 18 |
  | `dev_B03_tube_leak_slow` | 95 |
  | `dev_B05_tube_leak_repeat` | 61 |
  | `dev_C03_wet_coal_mild` | 19 |
  | `dev_C04_feeder_trip_caught` | 54 |
  | `dev_C05_low_cv_coal` | 67 |
  | `dev_C06_wet_coal_repeat` | 27 |

- **Source:** the teammate's saved board runs `results/benchmarks/m6_new_r1` (branch `nd-paper`, commit `628f2d8fd`),
  every scored diagnostician request, seed 20261113. 185 unscored requests were dropped.
- **Line 1 is in the true group on 196 and not on 204.** Seven episodes hold both outcomes. This count reads the
  code's line 1 only, no model output.
- **Limit, stated now:** new episodes of the **same synthetic plant and the same agent**. This tests whether the effect
  repeats on new faults and new prompts, not whether it exists outside this agent.

### Set R (secondary)
`reports/data/echo_requests.json` (450 dev requests, three plants). The new 8-bit arms are run on it. The 4-bit arms
and the Llama 3B arms already are.

### MMLU (public recall control)
`reports/data/nd_public_requests.json`, 300 questions, original order, with the probabilities of the four letters.

### SQuAD (public evidence test)
- `reports/data/echo_4bit_squad.json`, sha256 `655cb1d9…84d65`: 300 questions from SQuAD v1.1 dev (CC BY-SA 4.0;
  `dev-v1.1.json` sha256 `95aa6a52…972c9`), seed 20261113.
- One question per paragraph, passages up to 1,200 characters, answers up to 5 words.
- **Three forms per question:**
  - `none`: the question alone;
  - `oracle`: with its passage;
  - `swap`: with the passage after every gold answer was replaced by another question's answer.
- **Scoring:** the reply contains the answer as whole words (SQuAD's own normalisation).
- **Limits, stated now:**
  - the swapped-in answer matches the original only as "number" or "text", so some swapped passages read oddly;
  - both precisions see the same passages;
  - this is in the spirit of Pandey (arXiv 2603.11513), not that paper's data.

## Arms (PROPOSED)
Each pair is the same weights at two precisions.

| model | 4-bit arm (Q4_0, the NPU's recipe) | 8-bit arm (every matrix Q8_0) |
|---|---|---|
| Llama 3.2 3B | `m1_q4_0` (the board's file) | `m2_q8_0` |
| Qwen2.5 0.5B | `m5_qwen25_05b_q4_0` | `m5_qwen25_05b_q8_0` (new) |
| Gemma 3 1B | `m6_gemma3_1b_q4_0` | `m6_gemma3_1b_q8_0` (new) |
| Qwen3 1.7B | `m7_qwen3_17b_q4_0` | `m7_qwen3_17b_q8_0` (new) |
| Qwen2.5 7B | `m3_qwen25_7b_q4_0` | `m3_qwen25_7b_q8_0` (new) |
| Llama 3.1 8B | `m4_llama31_8b_q4_0` | `m4_llama31_8b_q8_0` (new) |

- **16-bit control:** `m2b_bf16` (Llama 3B), paired with `m2_q8_0`.
- **On the NPU (QIDK SM8650):** `npu_q4_0` and `npu_q8_0`, Llama 3B, set H, the real prompt only.
- **New 8-bit files:** `llama-quantize --pure … Q8_0` from the 16-bit GGUF, at the pinned commit
  (`bench/echo_4bit_runs.sh --q8 <name>`). Their sha256 is recorded in `RUNLOG_4bit.txt`.
- **Gemma caveat, stated now:** the Gemma file comes from a checkpoint trained for 4-bit use, so its pair is not a
  clean test of rounding. It is reported, and does not count for the "general" verdict.

## Measures
1. **Primary, agent prompts:** AUC of p(line 1) for "line 1 is in the true group" on set H, and the paired difference
   AUC(8-bit) − AUC(4-bit) on the requests both arms answered.
2. **Also reported:**
   - the AUC inside episodes;
   - exact-case credit;
   - the share of answers on line 1;
   - set R per plant;
   - every row left out, with the reason.
3. **MMLU:** AUC of the probability on the chosen letter for "the answer is right", and the paired difference.
4. **SQuAD:** share of `swap` replies that hold the swapped-in answer (`swap_follows`), and the paired difference.
   Reported beside it:
   - `none_right`;
   - `oracle_right`;
   - `use_unknown` (right with the passage, among questions wrong without it);
   - `keep_known`;
   - `swap_follows_known`.

## Outcome rules (PROPOSED)

**Per model, on set H:**

| reading | rule |
|---|---|
| **reads at 8-bit** | AUC(8-bit) ≥ 0.65 and its interval lies above 0.5 |
| **4-bit loses the reading** | reads at 8-bit, and the difference is ≥ +0.10 with an interval that excludes 0 |
| **4-bit keeps the reading** | reads at 8-bit, and the whole interval of the difference lies below +0.10 |
| **nothing to lose** | does not read at 8-bit |
| **undetermined** | anything else |

**Overall:**

| verdict | rule |
|---|---|
| **replicated** | "4-bit loses the reading" for Llama 3B on set H (Mac) |
| **replicated on the NPU** | the same rule for `npu_q4_0` against `npu_q8_0` |
| **general** | replicated, and "loses" for at least 2 of the 4 other models (Gemma not counted) |
| **specific to Llama 3B** | replicated, and "keeps" or "nothing to lose" for all 4 others |
| **mixed** | replicated, and neither of the two above; reported model by model |
| **not replicated** | Llama 3B is not "loses" on set H. The exploratory finding is then withdrawn as a claim |

**Public tests:**

| test | reading | rule |
|---|---|---|
| MMLU | 4-bit loses on recall too | difference ≥ +0.05, interval excluding 0 |
| SQuAD | 8-bit follows the passage more | `swap_follows` difference ≥ +0.05, interval excluding 0 |
| SQuAD | no difference | the whole interval lies inside ±0.05 |

**Where the thresholds come from (all DESIGN):**

| threshold | basis | range considered |
|---|---|---|
| 0.10 | about half the exploratory effect (0.19 on the Mac boiler, 0.225 on the NPU) | 0.05–0.15 |
| 0.65 | midway between chance and the exploratory 8-bit value (0.78) | 0.60–0.70 |
| 0.05 | as in the earlier echo pre-registrations | – |

## Expected, stated before running
| item | expectation | reason |
|---|---|---|
| Llama 3B, set H, Mac and NPU | 8-bit reads; 4-bit loses | the exploratory result |
| 8-bit against 16-bit | \|difference\| < 0.05 | they were equal in every earlier test |
| Qwen3 1.7B, Qwen 7B, Llama 8B | **no stated direction** | they read at 4-bit already; their 8-bit files were never run |
| Qwen 0.5B, Gemma 1B | nothing to lose | they copied the worked example at 4-bit |
| MMLU, Llama 3B | no 4-bit loss | the rotation proxy gave 0.72 against 0.73; Proskurina et al. report small shifts on recall tasks |
| SQuAD | **no stated direction** | never run |

## Run checks (fixed now)
- **An arm with more than 5% failed calls in any step is rerun before scoring.**
- **A new 8-bit file is used only if** `bench.gguf_types` reports every matrix Q8_0.
- **Stop rule for set H:** if Llama 3B 4-bit answers line 1 on fewer than 80% of set H requests, the replay is not
  showing the board's behaviour. Stop and find why before reading any other number.
- **Nothing is rerun, dropped or re-thresholded after the scores are seen.** Any later analysis is labelled post hoc.

## What has already been seen
- **Set H's prompts:** the code-side count above (line 1 right or wrong). No model output on them was scored.
- **The m6 runs they come from:** compared tick by tick for run-to-run differences in the published cause. Not for
  probabilities, and not for line-1 correctness.
- **Pilot:** 3 requests per test, on this laptop, with both Llama 3B files. Looked at only for plumbing (calls
  succeed, probabilities are saved, SQuAD replies are short answers).
- **Set R, Llama 3B:** fully seen. It is the exploratory result (boiler: 0.590 against 0.781).

## Agreed
**A1, 2026-11-13, before any full run.** The human agreed every PROPOSED item in this file as written, unchanged
("agreed"):
- the arms (six models at Q4_0 and Q8_0, the 16-bit control, the two NPU arms);
- Gemma not counted for "general";
- the outcome rules and thresholds (0.65; +0.10; 0.05);
- the overall verdicts;
- the public-test rules.

**Open choice settled by "as written": the SQuAD set keeps all 300 questions.** The crude type-only answer swap
(noted in `reports/echo_4bit_build.md`) is not restricted to the numeric answers.

Before this commit the only calls were the laptop plumbing pilot (3 requests per test, not scored).

## Amendment A2: the two NPU arms (PROPOSED 2026-11-13, before any NPU call)

**A2 agreed 2026-11-13 16:30 (laptop time) by Shubham ("runa i agree", given as "run A, I agree" to
HANDOFF_QIDK_RUNS.md run A), as written below, unchanged, before any `npu_` call.**
**Why:** the board was exchanged on 2026-11-13, and the new chip fails at its default thread setting. Nothing below was
written after seeing a reply: no `npu_` call has been made. **Needs the human's "agreed", dated, before the first NPU
call.** The Mac arms are not affected.

1. **Chip.** Both NPU arms run on the **SM8750** (QIDK serial `1d9c8f40`, Hexagon v79), not the SM8650 named under
   "Arms".
   - "Replicated on the NPU" keeps its rule, but now it is also a second chip.
   - The exploratory NPU numbers (SM8650, default threads) are printed beside, never pooled.
2. **Threads.** Both arms start with `GGML_HEXAGON_NHVX=2` (`ND_LANE_ENV`, the whitelisted setting copied from branch
   `nd-paper` into `bench/board.py`). Every other flag is the standard lane command.

   | | value |
   |---|---|
   | basis (CITED, `nd-paper` `reports/nd/m9_llama100_sm8750.md`, Llama 3B, 100 agent prompts × 5) | default 6 threads: **42 of 1,000** calls failed with "@"; 2 threads: **0 of 1,000**, at 1.28× the latency; 1 thread: 0 of 1,000, at 1.95× |
   | range considered | 1 or 2. 6 is rejected (the failures) |
   | affects | run time; at 2 threads repeated calls are bit-identical, at 6 about 0.3–0.5% of positions vary. So the NPU probabilities are those of the 2-thread path |
   | check | the lane log's HVX thread line shows 2 (m9 read `threads 1, hvx 1` for one thread). Otherwise the arm is not started |

3. **How an "@" reply is counted.**
   - The reply grammar cannot continue after "@" (token 31), so the server answers HTTP 500. The row's status is then
     not `ok` (m9: "every failed call is an HTTP 500").
   - Such a row is a **failed call**: it is left out of scoring with the reason "call failed", and it counts toward
     the existing 5% rule.
   - No reply is repaired, re-parsed or resent by hand.
4. **Rerun, fixed now.**
   - If an arm has **more than 20 failed calls of 400** (5%), its file is **moved** (not deleted) to
     `results/echo/npu_failed/<file>_try1.jsonl`. After the usual cooling, the whole arm is run once more with the same
     settings.
   - If the second try also has more than 20, the NPU verdict is **"not run: hardware failures"**, reported with both
     counts.
   - **The thread count is not changed after any reply has been seen.**
5. **Unchanged:**
   - the order (4-bit, then 8-bit);
   - set H, real prompt only (`--forms original`);
   - the files: Q4_0 `5aa3ece5…`, Q8_0 `d91f61ab…`, both checked on the board by `bench.board`;
   - temperatures before and after each arm, in laptop time;
   - the sampler at its light setting;
   - the rules and thresholds.

## Amendment A3: the same two NPU arms on the SM8650 (agreed 2026-11-13 21:57, before any SM8650 call)
**Agreed by Shubham** ("lets do 6 then 1 then 2, 3 is already done"), after being told the arms, the 2-thread choice
and why. Nothing here changes A1 or A2, and no SM8650 `npu8650_` call had been made.

- **Board:** the SM8650 (Hexagon v75), serial recorded at run time from `adb devices` and `ro.soc.model`.
- **Arms:** `npu8650_q4_0` (Q4_0 `5aa3ece5…`) then `npu8650_q8_0` (Q8_0 `d91f61ab…`), set H, real prompt only,
  exactly as A2's arms. Output `results/echo/h_prior_npu8650_<q4_0|q8_0>.jsonl`.
- **Threads:** `GGML_HEXAGON_NHVX=2`, the same as on the SM8750, so the two chips are compared at one setting
  (Gagan's 2-thread test on the SM8650 is done, per Shubham). The lane log must show `threads 2`.
- **Failed calls and rerun:** A2's rule (more than 20 of 400: move the file aside, rerun once, never change threads).
- **Cooling:** to the SM8650's idle temperature + 5 °C, idle measured before the first arm, at most 900 s per wait.
- **Reading:** the A1 outcome rules apply to the pair `npu8650_q4_0:npu8650_q8_0`. "Replicated on the NPU" is
  reported per chip. The two chips are shown side by side and never pooled.

## Result, NPU arms only (scored 2026-11-14 on Shubham's laptop; Mac arms not yet in)
Set H, real prompt only, 400 requests (196 line-1-right, 204 wrong), 9 episodes, 2,000 episode resamples. Board NPU
results, Llama 3.2 3B, 2 threads. Plant data synthetic. Scores `results/echo/scores/4bit_H_npu.json`, `4bit_H_npu8650.json`.

| chip | AUC 4-bit [95%] | AUC 8-bit [95%] | difference [95%] (primary) | within episode, diff [95%] (reported) | line 1 share 4-bit / 8-bit |
|---|---|---|---|---|---|
| SM8750 | 0.750 [0.501, 0.855] | 0.835 [0.607, 0.931] | **+0.085 [0.055, 0.143]** | +0.134 [0.077, 0.212] | 0.998 / 0.900 |
| SM8650 | 0.745 [0.504, 0.849] | 0.829 [0.600, 0.927] | **+0.085 [0.056, 0.138]** | +0.135 [0.073, 0.204] | 0.998 / 0.898 |

**By the agreed rules (primary measure, pooled AUC):**
- "Reads at 8-bit": **yes on both chips** (0.835 and 0.829, intervals above 0.5).
- "4-bit loses the reading" needs a difference of at least +0.10: **not met** (+0.085 on both).
- "4-bit keeps the reading" needs the whole interval below +0.10: **not met** (upper ends 0.143 and 0.138).
- **NPU reading on both chips: undetermined.** The within-episode difference would clear +0.10, but it is a reported
  measure, not the primary one, and is not used to decide.

**Against the exploratory result:** the 4-bit file is **not** at chance on new episodes (0.75, against 0.556 in the
exploratory analysis), and the gap is smaller (+0.085 against +0.225). The two chips agree to within 0.006.
