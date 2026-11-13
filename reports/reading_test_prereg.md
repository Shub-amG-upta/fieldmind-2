# Where does the model's hidden signal come from, and can judging each case alone use it? Pre-registration

**Status: AGREED 2026-11-14 00:48 (laptop time, Gagan's Mac), before any full-run call. Was DRAFT, written 2026-11-14 before any scored call.** Items marked PROPOSED must be agreed, dated under
"Agreed", before the full run. A 2-request plumbing pilot ran on Shubham's laptop (rows not scored, picks not read).

**Why:** the 4-bit test (`reports/echo_4bit_prereg.md`) found that the model's probability on line 1 separates right from
wrong (AUC 0.75–0.88) although its answers stay on line 1. Two explanations: the model reads the evidence, or it reads
the prompt's "belief (from code)" line. And if a signal is there, judging each case alone (no list, so no position to
copy) might turn it into better answers.

| item | value |
|---|---|
| Code | `bench/reading_test.py` (tests `tests/test_reading_test.py`) |
| Requests | set H, `reports/data/echo_4bit_requests.json`: 400 scored boiler requests, 9 dev episodes, 1,354 case lines |
| Settings | as the 4-bit test: pinned llama.cpp `99b95488c`, `-c 4096 -np 1 --cache-ram 0`, temperature 0, seed 0, top-20 probabilities |
| Nature | laptop replays (24 GB Mac), not NPU results. Boiler data synthetic. No energy |
| Intervals | 95%, 2,000 resamples of episodes, seed 20261111 |

## Forms (fixed)
| form | prompt | grammar | readout |
|---|---|---|---|
| `original` | unchanged; **not re-sent**, rows are the 4-bit test's `h_prior_<label>.jsonl` | the system's | p(line 1), line-1 share |
| `no_belief` | the `WORLD MODEL:` line removed | the system's | same |
| `no_example` | the `Example:` line removed | the system's | same |
| `neither` | both removed | the system's | same |
| `per_case` | per case line: the side line, the facts, that one case's line, the notes, and "Does this case explain the facts? Answer yes or no." No list, belief, example or answer format. | `yes` or `no` | p(yes) = p(yes) / (p(yes) + p(no)) |

**Per-case pick:** the case with the highest p(yes). **Ties are broken by case id, never by line**, so position cannot
enter.

## Arms (PROPOSED)
| label | file |
|---|---|
| `m1_q4_0` | Llama 3.2 3B Q4_0, the board's file (`5aa3ece5…`) |
| `m2_q8_0` | the same at Q8_0 (`d91f61ab…`) |
| `m3_qwen25_7b_q8_0` | Qwen2.5 7B Q8_0 (`a9753891…`) |
| `m4_llama31_8b_q8_0` | Llama 3.1 8B Q8_0 (`86ba8355…`) |
| `m7_qwen3_17b_q8_0` | Qwen3 1.7B Q8_0 (`65bb9528…`) |

Order as listed (the 3B first). About 1,200 list calls and 1,354 one-token calls per arm.

## Measures
1. **Signal source:** AUC of p(line 1) for "line 1 is in the true group" in each list form, and the **drop**
   AUC(original) − AUC(form), paired over requests both forms answered. Primary form: `no_belief`.
2. **Code-side comparator (no model):** AUC of the code's own belief in the line-1 case, read from the prompt.
3. **Copying:** line-1 share in each list form.
4. **Fix:** group accuracy of the per-case pick minus line 1's, paired; also against the code's belief top-1.
5. **Also reported:** AUC of p(yes) for the line-1 case; share of per-case picks on line 1; share answered "yes" on line 1;
   calls and tokens per request (Mac, not board).

## Outcome rules (PROPOSED)

**Signal source, per arm (primary `no_belief` drop):**

| reading | rule |
|---|---|
| **from the belief line** | drop ≥ +0.10, interval excluding 0 |
| **from the evidence** | AUC(`no_belief`) ≥ 0.65 with its interval above 0.5, and the whole interval of the drop below +0.10 |
| **undetermined** | anything else |

**Fix, per arm:**

| reading | rule |
|---|---|
| **per-case judging beats line 1** | per-case minus line 1 ≥ +0.05, interval excluding 0 |
| **no gain** | the whole interval below +0.05 |
| **undetermined** | anything else |

**Overall:**
- **"The hidden signal is evidence-reading"** if the 3B (`m1_q4_0` or `m2_q8_0`) reads "from the evidence".
- **"A fix exists"** if any arm reads "beats line 1". If only the 7B or 8B does, it is reported as "a fix for models
  larger than the phone runs today".

| threshold | value | provenance | range | affects |
|---|---|---|---|---|
| drop margin | 0.10 | DESIGN: as the 4-bit test's "loses" margin | 0.05–0.15 | belief vs evidence |
| AUC floor | 0.65 | DESIGN: as the 4-bit test's "reads" floor | 0.60–0.70 | "from the evidence" |
| fix margin | 0.05 | DESIGN: as E3 and the earlier echo rules | – | "beats line 1" |

## Expected, stated before running
| item | expectation | reason |
|---|---|---|
| signal source, 3B | **from the belief line** | the code's own agreement signal was as strong (AUC 0.84) in the exploratory analysis; the belief line names the cases with their scores |
| copying in `no_example` | line-1 share lower than original | the 0.5B and Gemma copy the example; for the 3B, `explain_v2` stopped copying without it |
| per-case, 3B | no gain | `explain_v2`: picks near chance when it did not copy |
| per-case, 7B/8B | no stated direction | they leave line 1 already |

## Run checks (fixed now)
- An arm with more than 5% failed calls in a form is rerun once before scoring.
- A per-case request counts only if every case line has a readable p(yes); the rest are counted and reported.
- **Nothing is rerun, dropped or re-thresholded after the scores are seen.**

## What has already been seen
- Set H's original-form p(line 1) AUCs for every arm (the 4-bit test).
- The pilot: 2 requests, all forms, on Shubham's laptop: calls succeed, probabilities are saved (3 list forms × 2,
  7 per-case calls), per-case answers are one token. No pick read.

## Agreed
**2026-11-14 00:48 (laptop time), before any full-run call.** The human (Gagan) agreed every PROPOSED item in this file as written, unchanged: "the pre-registeratoin mark it as agreed and start the rest of the run". Recorded by the Claude session on Gagan's Mac. Already seen at that time: the 2-request pilot on Shubham's laptop and the same 2-request pilot on Gagan's Mac (2026-11-14 00:48, `/tmp/reading_pilot`: 6 list rows and 7 per-case rows, all `ok`; no pick or score read).

## Interim result: the two Llama 3B arms (scored 2026-11-14 ~02:30; Qwen 7B, Llama 8B, Qwen3 still running)
Laptop replays on Gagan's 24 GB Mac, not NPU results. Set H, 400 requests, 2,000 episode resamples. Scores
`results/echo/scores/reading_source_3b.json`, `reading_fix_3b.json`. No rerun, drop or threshold change.

**Signal source (primary: AUC drop when the belief line is removed):**

| arm | AUC original | AUC no_belief [95%] | drop [95%] | reading |
|---|---|---|---|---|
| `m1_q4_0` | 0.756 | 0.728 [0.459, 0.851] | +0.029 [−0.022, 0.081] | **undetermined** (AUC interval reaches below 0.5) |
| `m2_q8_0` | 0.828 | 0.805 [0.532, 0.921] | +0.023 [−0.012, 0.087] | **from the evidence** |

- **Overall rule: "the hidden signal is evidence-reading" — MET** (by `m2_q8_0`). The stated expectation ("from the
  belief line") was wrong.
- Code-side comparator: the code's own belief in the line-1 case gives AUC 0.789. The 8-bit model with no belief line
  (0.805) is at least as good.

**Fix (per-case judging, top case by p(yes), group accuracy against line 1):**

| arm | line 1 | per-case pick | difference [95%] | reading |
|---|---|---|---|---|
| `m1_q4_0` | 0.490 | 0.440 | −0.050 [−0.154, 0.021] | **no gain** |
| `m2_q8_0` | 0.490 | 0.502 | +0.012 [−0.087, 0.081] | **undetermined** |

- The code's belief top-1 scores 0.517 (against line 1: +0.027 [−0.067, 0.143]).
- p(yes) on the line-1 case, asked alone with no list or belief, separates right from wrong: AUC 0.769 (4-bit), 0.839
  (8-bit). Per-case picks are on line 1 for 57% and 63% of requests. 3.4 one-token calls per request.

**Reported, not used to decide (post hoc, after seeing):**
- **Removing the worked example made copying worse, not better:** line-1 share 0.99–1.00 without it, and the AUC fell
  (drop +0.148 [0.025, 0.277] and +0.168 [0.075, 0.281]). The expectation stated above was the opposite.
- The per-case p(yes) carries the signal but ranking all cases by it does not beat line 1. A rule that keeps line 1
  unless its own p(yes) is low would use the signal differently; it is a new method and needs its own pre-registration.
