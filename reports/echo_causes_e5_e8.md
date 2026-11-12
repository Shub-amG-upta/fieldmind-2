# Echo causes E5–E8 (24 GB Mac runs, first batch) — report

## Status
PARTIAL. Scored the teammate's E5–E8 runs (`origin/bc-runs` at `f96bf08`, merged into `bc-build`) under the agreed
pre-registration (`reports/echo_causes_prereg.md`, A1).

| arm | E5 size (R) | E6 relabel | E7 prior | E8 MMLU |
|---|---|---|---|---|
| m5 Qwen2.5 0.5B Q4_0 | done | done | done | done |
| m6 Gemma3 1B Q4_0 | done | done | done | done |
| m7 Qwen3 1.7B Q4_0 | done | done | done | done (format failure) |
| m1 Llama 3B Q4_0 (board file) | earlier | done | done | done |
| m2 Llama 3B Q8_0 | earlier | done | done | done |
| m2b Llama 3B 16-bit | earlier | done | done | done |
| m3 Qwen2.5 7B Q4_0 | earlier | done | **running** | **running** |
| m4 Llama3.1 8B Q4_0 | earlier | **not yet** | **not yet** | **not yet** |
| m8 Qwen2.5 14B Q4_0 | **not built** | – | – | – |

**What the numbers are:**
- **Laptop replays** (Apple Metal, `llama-server`, `-c 4096 -np 1`, temperature 0). **Not NPU results.**
- Plant data: synthetic (boiler), real (Cranfield), public (TEP). MMLU: public.
- 95% intervals: 2,000 resamples (episodes for set R; questions for MMLU), seed 20261111.
- Scores: `results/echo/scores/{R_pooled,R_<plant>,relabel,prior,mmlu,e_vote_all,e_hint_all}.json`.

**Run checks:**
- No failed calls: every row is `ok`, and every file has its full count (R 1,800, relabel 900, prior 900, MMLU 1,200).
- `RUNLOG.txt` has no `FAILED`.
- The m1, m5, m6 and m7 files match `bench.board.CANDIDATES` by sha256.
- m2, m2b, m3 and m4 are the laptop files of the first replay (same labels, so R and L were skipped).

## Results

### E5. Size curve: share picking line 1, and accuracy (group, scored requests, n = 439)
Code's line 1 is right (group) on **0.401**; the retrieval ceiling is 0.611 (E1).

| arm | line 1, original | line 1, shuffled (a / b / last) | position invariance | model right, original | model right, shuffled a |
|---|---|---|---|---|---|
| 0.5B | 0.127 | 0.118 / 0.109 / 0.104 | 0.040 | 0.212 | 0.246 |
| Gemma 1B | 0.211 | 0.224 / 0.222 / 0.220 | 0.056 | 0.194 | 0.257 |
| Qwen3 1.7B | 0.896 | 0.738 / 0.749 / 0.764 | 0.091 | 0.419 | 0.294 |
| Llama 3B 4-bit | 0.991 | 0.971 / 0.973 / 0.978 | 0.000 | 0.401 | 0.198 |
| Llama 3B 8-bit | 0.913 | 0.887 / 0.864 / 0.880 | 0.080 | 0.417 | 0.226 |
| Llama 3B 16-bit | 0.922 | 0.891 / 0.871 / 0.887 | 0.071 | 0.415 | 0.223 |
| Qwen 7B | 0.629 | 0.482 / 0.482 / 0.473 | 0.338 | 0.392 | 0.394 |
| Llama 8B | 0.580 | 0.356 / 0.400 / 0.416 | 0.478 | 0.385 | 0.362 |

**By the agreed rules (`reports/echo_prereg.md`):**
- **"Copies position":** the Llama 3B at all three precisions.
- **No label:** 0.5B, Gemma 1B and Qwen3 1.7B (shuffled line 1 is below 0.8, invariance below 0.5).
- **"Reads the cases":** no arm.

**Line-1 copying is not monotonic in size.** It peaks at the 3B.
- **Below 3B:** the models copy something else (see below).
- **Above 3B:** the models leave line 1.

**No arm beats line 1.** The best are Qwen3 1.7B (0.419) and the 8-bit 3B (0.417). The paired E7 difference for Qwen3 is
+0.018 [−0.00, 0.04].

**Qwen 7B on a shuffled list still reaches 0.394**, close to the code's 0.401. So it rebuilds most of the code's ranking
from the evidence. It does not beat that ranking.

**The 0.5B and Gemma 1B copy the prompt's worked example, not line 1.**
- The example is `{"r":[[2,[1,3]],[1,[1]]],...}`.
- In set R, the first case they name is "2" on 1,594 of 1,800 calls (0.5B, 89%) and 1,397 of 1,800 (Gemma, 78%), in
  every order.
- This is the copied-example effect already seen on Cranfield.

### E2 and E3 for the new arms (pre-registered rules)
| arm | E3: departures − random other line (group) | departures | E2: vote − line 1 (group) |
|---|---|---|---|
| 0.5B | +0.003 [−0.015, 0.022] | 778 | −0.164 [−0.291, −0.051] |
| Gemma 1B | +0.014 [−0.009, 0.041] | 685 | −0.175 [−0.320, −0.048] |
| Qwen3 1.7B | **+0.132 [0.055, 0.206]** | 225 | −0.048 [−0.107, 0.016] |

- **"Reads a little":** Qwen3 1.7B, like the four arms in `reports/echo_causes_e1_e3.md`.
- **No signal:** the two example copiers, with intervals around 0. This is the expected result for a model that does
  not read, so E3 can return zero on real data, not only on fakes.
- **Voting helps no arm** (E2).

### E6. Label vs position (`relabel_shuf`, requests where first shown, label 1 and top case differ, n = 264)
| arm | first shown | label 1 | code's top case | chance | verdict (agreed rule) |
|---|---|---|---|---|---|
| 0.5B | **0.985** [0.96, 1.00] | 0.000 | 0.015 | 0.275 | **copies the position** |
| Gemma 1B | 0.322 | 0.087 | 0.356 | 0.275 | mixed |
| Qwen3 1.7B | 0.549 | 0.212 | 0.155 | 0.275 | mixed |
| Llama 3B 4-bit | 0.553 [0.49, 0.62] | 0.318 [0.26, 0.37] | 0.099 | 0.275 | mixed |
| Llama 3B 8-bit | 0.371 | 0.432 | 0.155 | 0.275 | mixed |
| Llama 3B 16-bit | 0.367 | 0.436 | 0.159 | 0.275 | mixed |
| Qwen 7B | 0.572 | 0.076 | 0.303 | 0.275 | mixed |

**A confound found in E6 (not in the pre-registration).**
- The relabelled forms often put label "2" (the example's first number) on the first line. With 2 lines this happens
  always, because label 1 may not be first.
- So "first shown" mixes position with copying the example's "2".

**Exploratory split, NOT pre-registered.** I re-scored only requests with 4+ lines where the four candidates are four
different lines (first shown, label 1, label 2, top case), n = 68, no intervals:

| arm | first shown | label 1 | label 2 (example) | top case | chance |
|---|---|---|---|---|---|
| 0.5B | **1.000** | 0 | 0 | 0 | 0.25 |
| Gemma 1B | 0 | 0.074 | **0.882** | 0.044 | 0.25 |
| Qwen3 1.7B | 0.309 | 0.309 | 0.324 | 0.059 | 0.25 |
| Llama 3B 4-bit | 0.353 | **0.529** | 0.074 | 0.044 | 0.25 |
| Llama 3B 8-bit | 0.294 | **0.529** | 0.044 | 0.132 | 0.25 |
| Llama 3B 16-bit | 0.250 | **0.574** | 0.044 | 0.132 | 0.25 |
| Qwen 7B | **0.559** | 0.074 | 0.044 | 0.324 | 0.25 |

**What it suggests** (n = 68, a hypothesis for a pre-registered test, not a result):
- **Each model family copies a different cue:**
  - the Llama 3B copies the **label "1"** more than the first position, at every precision (as Zheng et al. 2024 report for option labels);
  - the 0.5B copies the **first position**;
  - Gemma copies the **example's "2"**;
  - Qwen 7B copies the **position** and reads some.
- **4-bit moves the 3B slightly towards position** (first shown 0.35 against 0.25–0.29).

### E7. Prior before reading, and calibration (original order)
| arm | prior on line 1 | prior's top is line 1 | calibrated pick is line 1 | calibrated − line 1 (group) | verdicts (agreed rules) |
|---|---|---|---|---|---|
| Llama 3B 4-bit | **0.879** [0.86, 0.90] | 1.00 | 0.00 | **−0.237 [−0.40, −0.10]** | prior; calibration hurts |
| Llama 3B 8-bit | **0.800** [0.77, 0.83] | 1.00 | 0.03 | **−0.210 [−0.35, −0.08]** | prior; calibration hurts |
| Llama 3B 16-bit | **0.804** [0.77, 0.83] | 1.00 | 0.03 | **−0.212 [−0.36, −0.09]** | prior; calibration hurts |
| Qwen3 1.7B | **0.633** [0.58, 0.67] | 0.89 | 0.53 | −0.018 [−0.09, 0.05] | prior; neither |
| 0.5B | 0.591 [0.53, 0.65] | 0.71 | 0.02 | **−0.223 [−0.39, −0.07]** | no prior; calibration hurts |
| Gemma 1B | 0.494 [0.38, 0.59] | 0.41 | 0.14 | **−0.196 [−0.34, −0.07]** | no prior; calibration hurts |

**Further analysis on the same rows (exploratory):**
- **The evidence lowers the 3B's confidence in line 1, but almost never overturns it.** Its probability on line 1 is
  0.66 with the real prompt, against 0.88 on the content-free copy. It is lower on 99% of requests. The 8-bit and 16-bit
  files show the same (0.62 against 0.80, on 88–90%).
- **Qwen3 1.7B is the one model that moves towards line 1 after reading** (0.71 against 0.63).
- **Calibration does not send picks to the bottom of the list,** which I tested and was wrong. It moves them to **line 2**
  on about 90% of requests with 3+ lines (3B 4-bit, 3B 16-bit, Gemma). Why line 2 is not explained.
- **4-bit raises the prior on line 1** (0.88 against 0.80 for 8- and 16-bit, intervals not overlapping). Compression
  strengthens the prior; it does not create it.

### E8. MMLU control (300 questions, 4 cyclic orders)
| arm | accuracy (4 orders) | answers "A" | invariance | invariance when right in the original order | verdict |
|---|---|---|---|---|---|
| Llama 3B 4-bit | 0.52–0.56 | 0.14–0.19 | 0.443 | 0.618 [0.54, 0.69] | does not read when it knows (< 0.8) |
| Llama 3B 8-bit | 0.56–0.60 | 0.20–0.25 | 0.500 | 0.669 [0.60, 0.74] | same |
| Llama 3B 16-bit | 0.56–0.60 | 0.20–0.25 | 0.500 | 0.653 [0.58, 0.72] | same |
| 0.5B | 0.35–0.40 | 0.18–0.24 | 0.263 | 0.339 | same |
| Gemma 1B | 0.31–0.41 | 0.22–0.30 | 0.183 | 0.312 | same |
| Qwen3 1.7B | 0.23–0.27 | **0.997–1.000** | 0 | 0 | **does not use the format** (agreed rule, ≥ 0.90 on one letter); not counted |

- **On MMLU the 3B does not prefer "A"** (0.14–0.25, at or below 0.25 chance).
- **Its line-1 copying on our prompt (0.97) is therefore not a general "pick the first option" habit.**
- It is still order-sensitive on MMLU: a third of the answers it gets right change with the order.

## What this means (as tested, nothing beyond)
1. **Echo is not one bias.** Under the agreed rules:
   - the Llama 3B copies position (E5), but carries a strong line-1 prior before reading (E7, 0.80–0.88);
   - the two smallest models copy the worked example's "2";
   - larger models leave line 1.

   The exploratory E6 split suggests the 3B's cue is the label "1". That is not yet a pre-registered result.
2. **Compression is not the cause, but it adds to it.** 4-bit raises line-1 copying (0.97 against 0.88) and the prior
   on line 1 (0.88 against 0.80). It lowers MMLU accuracy by about 4 points. 8-bit and 16-bit are indistinguishable on
   every test.
3. **Size is not the cause.** Line-1 copying peaks at 3B. No size from 0.5B to 8B beats the code's line 1.
4. **The published fixes do not help here:**
   - calibration hurts every model except Qwen3, where it does nothing;
   - voting helps none.

   In our prompt the first position carries real information, because the code ranks its best guess first. Removing
   it removes information; that is consistent with these results, but not tested directly.
5. **The echo is tied to our prompt.** The same 3B shows no first-option preference on MMLU.
   - The prompt cues it can copy are a ranked list, a "belief (from code)" line and a worked example.
   - Which cue does the work is untested. A pre-registered prompt ablation would test it.

## Verification
| step | result |
|---|---|
| ran the module | `bench/echo_mac_score.sh`, plus `echo_causes.py score vote|hint` on all R files; outputs above |
| self-tests | `tests/test_echo_causes.py`, `tests/test_echo_test.py`: 36 passed |
| independent re-derivation | (1) E6 3B 4-bit label-1 share (distinct): 0.3182 (tool) vs 0.3182, by a regex over the raw reply text with my own filter; difference 0. (2) E8 invariance when right: 3B 4-bit 0.6178 vs 0.6178; 16-bit 0.653 vs 0.6534, from the raw MMLU rows with my own mapping of letters to options; difference < 0.001 |
| mutation check | Not repeated: no scoring code changed since `a6f561b` (9 of 9 mutations caught there). New analysis code in this report is exploratory, run inline, and not committed as a tool |

## Direction checks
| claim | expected | measured | |
|---|---|---|---|
| a model that does not read gets E3 ≈ 0 | ≈ 0 | 0.5B +0.003, Gemma +0.014 (intervals include 0) | OK |
| evidence moves a reader's probability off its prior | p(line 1) real ≠ prior | 3B: 0.66 vs 0.88, lower on 99% | OK (direction stated after the first row was seen; recorded as exploratory) |
| calibration of a weak reader on an informative order does not beat line 1 | ≤ 0 | −0.20 to −0.24 (5 arms), −0.02 (Qwen3) | OK (prediction in the proposal doc, written before scoring) |

## Constants introduced
None. All thresholds are from the agreed pre-registrations.

## Numbers that changed
None. These are first runs. m1–m4 R results are the earlier replay, unchanged.

## Disagreements recorded, not resolved
- **E5 "copies position" vs E6 "mixed" for the 3B.** E5 shuffles cases but keeps labels in order (line 1 = label 1). E6 separates them.
  - Both hold if the 3B copies "label 1 on the first line" and splits when the two are separated.
  - The exploratory split points to the label.
- **E6 vs Zheng et al. (2024):** they find label preference dominant across 20 models.
  - Our Llama 3B agrees (exploratory).
  - The 0.5B and Qwen 7B lean to position, which is not what they report. Our task, list length and prompt differ.
  - Unexplained.
- **Kolakaluri (2026): 4-bit increases position bias.** We see the same direction, but small (line 1 0.97 against 0.88), and 8-bit equals 16-bit, as they report.

## Blocked / needs a decision
- **The E6 design has a confound** (label "2" from the worked example lands on the first line).
  - The pre-registered verdicts stand as computed.
  - A clean test needs a pre-registered amendment: either score on 4+ line requests only, or relabel with the example's labels excluded from the first line.
  - The 4+ line set is small (68 requests from set R). Decide whether to amend and rerun.
- **Prompt ablation** (remove the worked example; remove the "belief (from code)" line) to find which cue the 3B copies.
  - That would be a new pre-registered run.
  - It is the direct test of point 5.
- **m3 prior and MMLU, all of m4's E6–E8, and the 14B (m8)** are still to run on the Mac.

## What I could not verify
- **The host llama.cpp build** in the Mac server logs: they do not print the version at this verbosity. Ask for
  `llama-server --version` on the Mac.
- **Whether m2, m2b and m3 are the same files as in the first replay.** The labels match and R and L were skipped, but
  the first replay's sha256 values are not recorded in `reports/echo_replay.md`.
- **Why calibration moves picks to line 2.** Not tested.
- **Any of this on the NPU.** All are laptop replays; only m1's file is the board file.
- **The letter arm (L) for m5–m7** was run but not scored in this pass.
