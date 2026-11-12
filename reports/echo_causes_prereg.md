# Echo causes (E5–E8): pre-registration

**Status: DRAFT, 2026-11-12. Written before any of these calls.**
- Items marked PROPOSED must be agreed, dated under "Agreed", before the first full run.
- The 6-request plumbing pilot on this laptop is not scored.

| item | value |
|---|---|
| Code | `bench/echo_causes.py`, `bench/echo_mac_runs.sh`, `bench/echo_mac_score.sh` |
| Requests | set R (`reports/data/echo_requests.json`, 450 dev requests, 150 per plant) and the 300 MMLU questions (`reports/data/nd_public_requests.json`, MIT) |
| Settings | same as `reports/echo_prereg.md`: pinned llama.cpp `99b95488c`, `-c 4096 -np 1 --cache-ram 0 -ngl 99`, temperature 0, seed 0, the system's grammar, diagnostician cap 60 |
| Nature of the numbers | laptop replays, **not NPU results**. Plant data synthetic (boiler), real (Cranfield), public (TEP) |

## E5. Size curve
- **New arms** (PROPOSED):
  - `m5_qwen25_05b_q4_0`, `m6_gemma3_1b_q4_0`, `m7_qwen3_17b_q4_0`: the board's own files, sha256 as in `bench.board.CANDIDATES`;
  - `m8_qwen25_14b_q4_0`: `Qwen/Qwen2.5-14B-Instruct`, built with `bench/build_candidate_gguf.sh`, its revision and sha256 recorded.
- **Measures and outcome rules:** exactly those agreed in `reports/echo_prereg.md` (Amendment A1). Nothing new.
- **Qwen3 caveat (DESIGN, fixed now):** on MMLU, Qwen3-1.7B answered "A" on 299 of 300 questions under a one-letter
  grammar (`reports/nd/m8_public.md`). If its E8 run again puts at least 0.90 of its answers on one letter, its replay
  is reported as "does not use the format". It is not counted as copying.

## E6. Label vs position (`relabel`)
- **Two forms per request,** seeded per request:
  - `relabel_orig`: the code's order, with label 1 not on the first line;
  - `relabel_shuf`: a shuffled order, with the code's top case not first, and label 1 neither first nor (when there are 3 or more lines) on the top case.
- **Measures:** shares of answers picking (a) the first line shown, (b) the line labelled 1, (c) the code's top case,
  with chance = mean 1/k. On `relabel_shuf` they are also reported on requests where the three are distinct (3+ lines).
- **Outcome rules** (PROPOSED), each per model, on `relabel_shuf` distinct requests:

| reading | rule |
|---|---|
| copies the position | first shown ≥ 0.8 and label 1 ≤ 0.3 |
| copies the label | label 1 ≥ 0.8 and first shown ≤ 0.3 |
| follows the code's top case | top case ≥ 0.8 |
| mixed | none of the above |

## E7. Prior (`prior`)
- **Two calls per request** (original order), each with token log-probabilities (top 20):
  - the real prompt;
  - its content-free copy (`fieldmind.multi.debias.content_free`).
- **The calibrated pick** is argmax(log p − log prior). A tie keeps the model's pick.
- **Measures:**
  - mean prior on line 1;
  - share of priors whose argmax is line 1;
  - share moved;
  - right (exact and group, scored requests) for the model's pick, the calibrated pick and line 1;
  - the paired differences calibrated − line 1 and model − line 1.
- **Outcome rules** (PROPOSED):

| reading | rule |
|---|---|
| a prior before reading | mean prior on line 1 ≥ 0.6 (chance is about 0.36 on set R) |
| calibration helps | calibrated − line 1 (group) ≥ +0.05 and its 95% interval excludes 0 |
| calibration hurts | the interval lies wholly below 0 |

## E8. MMLU control (`mmlu`)
- **The 300 questions** in the 4 cyclic orders of their options; each option appears once at each letter.
- **Measures:**
  - accuracy per order;
  - share answering "A";
  - invariance (the same option picked in all 4 orders);
  - invariance among questions the original order got right.
- **Outcome rule** (PROPOSED): **"reads when it knows"** means invariance among questions right in the original order is ≥ 0.8.

## Intervals (fixed now)
95%, 2,000 resamples, seed 20261111:
- E6 and E7 resample **episodes**;
- E8 resamples **questions**.

## Run order
1. **E5 first:** it is the cheapest and decides nothing alone.
2. **Then E6–E8 per arm,** in one pass of `bench/echo_mac_runs.sh`.

## Agreed
(none yet)
