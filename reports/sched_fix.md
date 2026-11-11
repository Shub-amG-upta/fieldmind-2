# Scheduling fix: why earliest_finish failed, a calibrated policy, and an offline replay — report

## Status
PARTIAL. Built and tested on the laptop:
- **A:** `bench.sched_study insitu`, the in-situ lane measurement;
- **B:** the `calibrated_finish` placement policy;
- **C:** `bench/sched_replay.py`, the offline replay.

The board test (D) is proposed, not run.

The replay predicts `calibrated_finish` ≈ `fixed` and removes `earliest_finish`'s losses. That is a prediction of a
model that reproduces `fixed` on the board but **not** `earliest_finish`.

Inputs are the 2026-11-10/11 board sweep (52 real-time runs; agent on the laptop, model calls on the QIDK). Plant
data: boiler synthetic, Cranfield real rig. No energy figures.

## Why earliest_finish mispredicted (step 1)
`earliest_finish` predicts a call as `prompt_tokens / prefill rate + max_answer_tokens / decode rate`, with:
- `prompt_tokens` = chars/4 (`est_tokens`);
- `max_answer_tokens` = the cap (60).

On 937 calls that started at once, so that no queue was involved:

| prediction | npu median error | cpu median error |
|---|---|---|
| as the scheduler predicted | +2.28 s (too slow) | +0.38 s (abs 0.99 s) |
| real answer length instead of the cap | −0.01 s (abs 0.07 s) | −1.47 s (too fast) |
| + contention scaled by the overlap that happened (oracle) | +0.02 s (abs 0.08 s) | −0.02 s (abs 0.85 s) |
| running answer length (knowable when deciding), real prompt | +0.00 s (abs 0.06 s) | −1.39 s |

**Three causes:**
1. **The cap: the main cause on the NPU.** v3 answers are about half the cap; v3x answers about an eighth (8 tokens).
2. **Contention ignored:** the CPU lane runs at well under half speed while the NPU works.
3. **The chars/4 estimate undercounts real tokens by 1.227×.** This matters on the CPU, which reads about 9× slower.

These rows come from a scratch analysis. The inputs the fix uses (part A) come from the tested tool.

## A. In-situ lane measurement (`bench.sched_study insitu`, `reports/data/sched_insitu.json`)

| lane | alone prefill / decode tok/s | together prefill / decode tok/s | together / alone | n alone / together |
|---|---|---|---|---|
| npu | 971.9 / 17.52 | 698.6 / 12.74 | 0.719 / 0.727 | 2,604 / 487 |
| cpu | 124.4 / 22.68 | 69.4 / 9.73 | 0.558 / 0.429 | **26** / 85 |

- **Real prompt tokens / the chars/4 estimate:** 1.227 (n = 3,398).
- **The isolated two-lane measurement (step 3 of the sweep) gave the CPU 0.79 / 0.95.** Inside real runs the CPU
  slows far more. The CPU's alone figure rests on 26 calls.

## B. `calibrated_finish` (`fieldmind/multi/realtime.py`)
`earliest_finish` with three corrections, all learned or measured, none tuned against a target:
1. **Answer length:** a running mean of the tokens each agent wrote (`LEARN_EWMA` = 0.3, starting at the cap).
2. **Prompt length:** the estimate × a running mean of real/estimate.
3. **Contention:** a lane's rates slowed by `multi.contention`, for the share of the call expected to overlap the other
   model lane's queued and running work.

`multi.contention` is in `configs/sched_study.yaml`, FITTED from part A. The policy refuses to run without it. In
lockstep it behaves as `earliest_finish` (no queues there). The run telemetry records what it learned.

## C. Offline replay (`bench/sched_replay.py`)
**How it works:**
- The sweep's recorded job streams are placed by the **real runner code**, with its threads stopped and a simulated
  clock.
- **The world:** each run's own alone speeds (`MIN_OWN_CALLS` = 10, else the sweep median), the sweep's contention
  ratios applied while both lanes work (a fluid model), recorded follow-up times, and replacement of waiting jobs.
- **Validity rule** (fixed before reading any calibrated result): a run is valid when the board replaced ≤ 5% of its
  jobs. A replaced job is missing from the stream, so an invalid run's replay has less work than the board had.

**Validation: the replay of the policy each cell actually ran, against the board (P2 miss rate, valid cells):**

| | board | replay | |
|---|---|---|---|
| `fixed`, v3 boiler 5 / 4 / 3 s | 0.00 / 0.00 / 0.01 | 0.00 / 0.00 / 0.07 | reproduced; pessimistic at 3 s |
| `fixed`, v3 Cranfield 5 s | 0.34 | 0.31 | reproduced |
| `fixed`, v3x Cranfield 5 / 4 / 3 s | 0.00 / 0.00 / 0.05 | 0.00 / 0.00 / 0.03 | reproduced |
| `earliest_finish`, v3 Cranfield 5 s | **0.50** | **0.32** | **not reproduced** |
| `earliest_finish`, v3x Cranfield 5 / 4 / 3 s | 0.08 / 0.05 / **0.25** | 0.03 / 0.05 / **0.04** | **not reproduced at 3 s** |

**Why `earliest_finish` is not reproduced:** the replay's `earliest_finish` sends fewer calls to the CPU than the
board's did. On Cranfield the board sent 13–16 diagnosis calls per cell to the CPU; the replay sent 3–11 calls of any
kind. Cause not established. The candidates are untested: the timing of submissions within a tick, and how the board
run's learned rates evolved.

**Prediction for `calibrated_finish`:**
- It almost never uses the CPU (0–2 calls per cell), so it behaves like `fixed`, the policy the replay does reproduce.
- **Capacity in the replay:** v3x boiler 2 s for all three policies. v3x Cranfield: `fixed` 3 s, `earliest_finish`
  5 s, `calibrated_finish` 3 s. v3 Cranfield: none for all three.
- On the v3 boiler the replay gives `calibrated_finish` 3 s against `fixed` 4 s. That is inside the replay's error:
  the board itself reached 3 s with `fixed`. **Not claimed.**

**Reading.** With a correct cost model, the policy concludes that on this phone, for Llama 3.2 3B, the CPU lane is
almost never worth using. It reads prompts about 8× slower and runs at under half speed beside the NPU. The fix
recovers `fixed`'s capacity and removes `earliest_finish`'s losses. It does not show heterogeneous placement
*gaining* capacity here. That answers the project's scheduling question with a mechanism, rather than a bare negative
result. It is a prediction until part D runs.

## D. Board test (PROPOSED, needs agreement before running)
- **Arms:** `calibrated_finish` on the sweep's cells for v3x Cranfield (5, 4, 3, 2 s) and v3 boiler (4, 3 s), next to
  the existing `fixed` and `earliest_finish` results.
- **Rule** (proposed): it passes if its capacity is at least `fixed`'s on each plant, and its group top-1 at that load
  is within 0.02 of `fixed` at 5 s, as in Amendment 1.
- **Board time:** about 2.5 h of running, 3–4 h with restarts and cooling. The sampler should be at its light setting
  (it costs about 0.75 of a core).

## Verification
| step | result |
|---|---|
| ran the modules | `insitu` over 52 runs; `sched_replay` over all 52 runs in about 4 s, exit 0 |
| self-tests | `tests/test_sched_study.py` 16, `tests/test_sched_policies.py` 19 (7 new), `tests/test_sched_replay.py` 5; with the realtime and fixed-placement suites, 66 passed before the replay was added |
| independent re-derivation | the tool's ratios against an earlier scratch analysis with different matching code: npu 0.719 / 0.727 against 0.723 / 0.730 (0.6% and 0.4% apart, unexplained, small), cpu 0.558 / 0.429 against 0.558 / 0.429 (equal). The scratch prompt figure (median estimate/real 0.835) is a different statistic from the tool's median real/estimate (1.227), so they are not compared |
| mutation check | A: 3/3 (partial overlap counted as alone, a 0.5 s match window, the inverted ratio). B: 6/6 (never learns, answer = cap, prompt ratio unused, contention ignored, other lane never busy, no refusal). C: 4/4 (no contention, replacement ignored, follow-up ignored, decode not timed) |

## Direction checks
| claim | expected | measured | OK/FAIL |
|---|---|---|---|
| contention slows a lane | together < alone | npu 0.72, cpu 0.43–0.56 | OK |
| charging the cap overpredicts | error falls with real lengths | npu 2.28 → 0.07 s | OK |
| replay of `fixed` matches the board | within ~0.05 on valid cells | yes, except boiler 3 s (+0.06) | OK, with that exception |
| replay of `earliest_finish` matches the board | within ~0.05 | Cranfield 5 s −0.18, v3x 3 s −0.21 | **FAIL** (recorded above) |

## Constants introduced
| symbol | value | provenance | range | affects |
|---|---|---|---|---|
| `multi.contention` | npu 0.7188 / 0.7273, cpu 0.5577 / 0.429 | FITTED: `insitu`, 52 sweep runs | npu 0.6–0.85, cpu 0.35–0.8 | calibrated_finish's predictions |
| `LEARN_EWMA` | 0.3 | DESIGN (same as `RATE_EWMA`) | 0.1–0.5 | how fast it learns answer length and prompt ratio |
| `MATCH_S` | 0.005 s | DESIGN: span run time and call latency measure the same call | 0.001–0.02 | which calls `insitu` and the replay use |
| `OVERLAP_TOGETHER` | 0.8 | DESIGN | 0.6–0.95 | the "together" sample |
| `MIN_OWN_CALLS` | 10 | DESIGN | 5–30 | when a run's own speed replaces the sweep's |
| `MAX_REPLACED_SHARE` | 0.05 | DESIGN, fixed before reading calibrated results | 0.02–0.10 | which replayed runs are valid |

## Numbers that changed
None of the existing policies, tables or results.

## Disagreements recorded, not resolved
1. **The replay does not reproduce `earliest_finish`'s CPU placements** (board 13–16 per Cranfield cell, replay
   fewer). Unexplained. Any replay number for a policy that uses the CPU is unreliable.
2. **The replay is pessimistic for v3 boiler at 3 s** (0.07 against 0.01–0.02). Unexplained.
3. **The isolated CPU-lane contention measurement (0.79 / 0.95) and the in-situ one (0.56 / 0.43) disagree by about
   2×.** Not resolved. A possible cause is that the isolated run was short with uniform prompts, but that is untested.

## Blocked / needs a decision
- Run part D on the board, and agree its pass rule first.
- Whether the sampler stays at full rate during D.

## What I could not verify
- Anything on the board: every result here is a laptop analysis of saved board runs, or a model's prediction.
- Accuracy under `calibrated_finish`: the replay models time only, not stale drops or answers.
- The CPU's alone speed beyond 26 calls.
