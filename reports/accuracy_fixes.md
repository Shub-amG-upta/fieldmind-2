# Accuracy fixes (steps 1–5) — report

## Status
PARTIAL — of five pre-registered steps, three are kept (1 in-fault scoring, 2a alarm persistence on Cranfield
and TEP, 5 two new TEP patterns) and three reverted (2b corrected limits, 3 score smoothing, 4 cosine
matching; code kept, switched off). The boiler is unchanged. **Mock only: these numbers measure the
deterministic and retrieval layers, NOT agent results.** Step 5 changes case data and needs advisor sign-off.
Branch `accuracy-fixes` from `breadth-tep` (1f7b422).

## Reporting sets, run once (mock, multi v3) — NOT agent results
Before = commit 807768a (breadth-tep code + the step-1 scoring), run from a separate worktree; after = the
kept state. Paired bootstrap over episodes (4,000 resamples, seed 0).
| plant | accuracy (group top-1, in-fault) | case top-1 | belief group | detection | false alarms before fault | fault-free FP/h |
|---|---|---|---|---|---|---|
| boiler (30 ep., 13 scored) | 0.721 → 0.721 | 0.610 → 0.610 | 0.574 → 0.574 | — | — | 0.91 → 0.91 |
| Cranfield (10) | 0.327 → 0.327 | 0.317 → 0.317 | 0.154 → 0.154 | 0.884 → 0.839 | 0.645 → 0.522 (−19 %) | — |
| TEP (110, 100 scored) | **0.416 → 0.575** (+0.159 [+0.117, +0.204], 83 up / 12 down) | 0.416 → **0.512** (+0.096) | 0.126 → 0.499 | 0.837 → 0.796 | 0.273 → 0.127 (−53 %) | 5.29 → 2.43 (−54 %) |

The before row equals reports/b2_tep_pack.md (TEP 0.416 / 0.837 / 0.273 / 5.29): the pre-fix code is
reproduced. On TEP, 0.063 of the +0.159 is group-only credit (Disagreements 2): **quote case top-1
(+0.096) as the conservative gain.** Cranfield's persistence gain is much smaller on the reporting set
(−19 %) than on dev (−58 %): the dev set has 6 episodes and one of them carried most of its false alarms.

## Pre-registered rules (committed BEFORE the step's first dev run)

Every keep/revert decision uses the **dev sets** on the **mock** backend, multi-agent v3 arm
(`bench/accuracy_table.py`): boiler `data/episodes_dev`, Cranfield `data/episodes_cranfield_dev`,
TEP `data/episodes_tep_dev`. On mock, the published order is the retrieval order (the "line-1 rule";
the board's Llama v3 picked line 1 on 88–100 % of calls), so these numbers measure the deterministic and
retrieval layers. **They are not agent results.** Reporting sets are run once at the end, never to decide.

"Accuracy" below = line-1 group top-1, scored inside the fault windows where the episode has them
(`Q2_group_top1_in_fault`, step 1), else from onset (`Q2_library.group_top1`, the boiler).
Each step is judged against the last KEPT state, per plant; a step can be kept on one plant and not another.

**Step 2a — state persistence.** A DEVIATION/ALARM is published only after it holds for N = 3
consecutive ticks (`agent.state_persistence_ticks`; DESIGN, range 2–4; costs (N−1) ticks of detection
delay: +1 min Cranfield, +6 min TEP). Facts are unchanged. Cranfield and TEP only; boiler stays 1 (off).
Kept on a plant if all hold: false alarms before the fault (`Q7_far_before_fault`) drop by ≥ 50 %
relative (TEP also fault-free `Q5_fp_per_hour` by ≥ 50 %); detection rate drops by ≤ 0.05 absolute;
accuracy drops by ≤ 0.01.

**Step 2b — multiple-testing-corrected limits.** Per plant, the probability that ANY state-raising
check fires on a healthy tick is held at α_F = 0.01 (DESIGN, the conventional 99 % control limit;
range 0.005–0.05). Šidák over m = tags × state-raising check kinds (TEP 52 × 3: limit, rate,
variability; Cranfield tags × 2: limit, rate): per-check α = 1 − (1 − α_F)^(1/m); limits at the
α/2 and 1 − α/2 healthy quantiles, rate and variability at the 1 − α quantile, from the same healthy
data as before (TEP fault-free training runs; Cranfield T1–T3). Where the healthy data hold fewer than
1/α windows the healthy maximum is used and recorded. Bands are not changed. Because TEP's level
(HIGH/LOW) and NOISY signature triples come from these facts, the TEP case library is re-fitted with the
unchanged `data/tep/fit_signatures.py` on the training split only (no test run read): thresholds and
library are one unit. Same pass rule as 2a, against the kept 2a state.

**Step 3 — temporal smoothing of the match score.** Each case's retrieval score is an EWMA over ticks,
half-life 2 ticks (DESIGN; 1 and 4 run and reported as sensitivity, not chosen between). Kept if accuracy
rises by ≥ 0.02 on at least 2 of the 3 plants and falls by > 0.01 on none.

**Step 4 — size-fair matching (written 2026-11-08, after steps 2–3 ran, before step 4's first run).**
Diagnosis on the baseline dev runs (in-fault ticks where line 1 is wrong and the true case IS shown):
the winner is a LARGER case than the true one on Cranfield 50 of 65 ticks and TEP 1,427 of 1,682; on the
boiler it is the same size (109) or smaller (65), larger on 5. Weighted Jaccard divides by the union, so
when the tick shows many triples a large case pays little for the predictions it does not see. Change:
`retrieval.match_measure: cosine`: weighted cosine (Ochiai) Σ a·b / (‖a‖‖b‖) over the same
triples and weights, which normalises by each case's own size; contradiction factor 0.15, provenance and
weight, the 0.01 floor, wildcards: unchanged. Default `jaccard` (identity). Applied to all three plants.
Expected direction, stated before the run: Cranfield and TEP up, boiler down or flat.
Kept on a plant if its accuracy rises by ≥ 0.02 with a paired-bootstrap 95 % interval (episodes, 4,000
resamples, seed 0) above −0.01, and kept for the agent as a whole only if no plant falls by > 0.01.
If the plants disagree, the step is recorded as plant-dependent and NOT kept (conservative), and the
per-plant result is reported. Case groups (the scoring definition) are not changed.

**Step 5 — two more pre-registered TEP patterns (written 2026-11-08, before step 5's first run;
TEP only; touches case data, so advisor sign-off is still needed before it is reported as final).**
Diagnosis on the TRAINING runs only (no test or dev run read): faults 3, 9, 15 show nothing on any
existing kind (as the TEP literature reports); fault 5 moves the condenser cooling-water valve 18.1 → 20.8
%, inside the healthy envelope (13.6–22.6) that hours of healthy wander make wide; faults 10 and 13 widen a
tag's swing with little change of mean (fault 13 stripper pressure p10/p90 3,000/3,216 against healthy
limits 3,082/3,123), which the step-sd variability check does not measure.
New PATTERN facts, severity **INFO** (they never raise the plant state, so detection and false alarms
cannot move), and signature triples:
  * SHIFT: |mean of the last 60 min − mean of the episode's first 60 min| above the healthy p99.7 of the
    same statistic → (tag, SHIFT_UP | SHIFT_DOWN, "-"). Assumes the episode starts healthy (true of every
    TEP episode: training faults start at 1 h, test faults at 8 h; on a live plant the baseline would be
    the last NORMAL hour).
  * WIDE: sd of the values over 60 min above the healthy p99.7 of the same statistic → (tag, WIDE, "-").
Thresholds from the fault-free training runs (as every other TEP threshold); windows 60 min (DESIGN, as
the variability check). The library is re-fitted with the unchanged vote rule (a run shows a triple when
it holds on most post-onset windows; ≥ 70 % of 100 training runs), the two kinds added. Scoring groups
stay the B2 file. Kept if TEP accuracy rises by ≥ 0.02 with a paired-bootstrap 95 % interval above 0,
TEP detection and false alarms move by ≤ 0.005 (expected 0), boiler and Cranfield identical.
Expected before the run: faults 5, 10, 13 gain triples; 3, 9, 15 stay empty. Strict case top-1 is
reported beside group top-1 (the B2 groups put 3, 5, 9, 10, 11, 13, 15 in one group).

## Step 1 — score only while the fault is present (DONE, 807768a)
`t2_root_cause` gains `group_top1_in_fault` / `belief_group_in_fault`: ticks published, (k+1)·tick as in
T7, inside a fault window. Cranfield episodes end with the fault removed; TEP faults last to the end
(in-fault = from-onset); the boiler has no windows (None).

## Baseline (mock, dev, multi v3; breadth-tep code)
| plant | accuracy (in-fault) | from onset | belief group | detection | false alarms before fault | fault-free FP/h |
|---|---|---|---|---|---|---|
| boiler | — | 0.637 | 0.502 | — | — | 0.98 |
| Cranfield | 0.524 | 0.417 | 0.343 | 0.760 | 0.376 | — |
| TEP | 0.435 | 0.435 | 0.193 | 0.853 | 0.239 | 5.53 |

Where the false alarms come from (healthy ticks, before the first window):
- TEP 1,290 of 5,098 ticks alarm; 884 of those carry exactly one tag-fact, mostly RATE (1,183 ticks
  carry a RATE fact, 397 LIMIT, 290 PATTERN). Alarm runs: 213 of 1 tick, 244 of 2, 94 of 3+. Many
  tags each tested at a per-tag level: a multiple-testing problem.
- Cranfield 21 of 100 ticks: 13 are the whole pre-fault segment of set 5.1 (slugging, ALARM on every
  tick, ≥ 4 LIMIT facts at once), 2 of set 3.2, 4 start-up ticks of set 4.2. Not multiple testing: set
  5.1 starts outside the T1–T3 healthy envelope. Neither step 2a nor 2b is expected to fix it.

## Results per step (mock, dev, multi v3) — NOT agent results
Accuracy = line-1 group top-1 (in-fault where windows exist). Each row against the last kept state.

| step | boiler | Cranfield | TEP | other effects | decision |
|---|---|---|---|---|---|
| kept state before step 2 | 0.637 | 0.524 | 0.435 | | |
| 2a persistence N=3 | (off) | 0.524 = | 0.435 = | Cranfield false alarms before fault 0.376 → 0.159 (−58 %), detection 0.760 → 0.732; TEP 0.239 → 0.050 (−79 %), fault-free FP/h 5.53 → 2.51 (−55 %), detection 0.853 → 0.807 (−0.046) | **KEPT** (Cranfield, TEP) |
| 2b Šidák limits (+ TEP re-fit) | (off) | 0.529 | 0.422 | Cranfield false alarms 0.159 → 0.159 (no drop); TEP 0.050 → 0.000, FP/h 2.51 → 0.00, detection 0.807 → **0.730** | **REVERTED** (both fail) |
| 3 EWMA h=2 | **0.605** (−0.032) | 0.570 (+0.046) | 0.453 (+0.018) | belief group up on all three | **REVERTED** (1 plant ≥ +0.02, boiler falls) |
| 3 sensitivity h=1 | 0.667 (+0.030) | 0.574 (+0.050) | 0.458 (+0.023) | | reported, not chosen (pre-registered) |
| 3 sensitivity h=4 | 0.575 (−0.062) | 0.588 (+0.064) | 0.455 (+0.019) | | reported |
| 4 cosine matching | 0.663 (+0.026) | **0.452** (−0.072) | 0.445 (+0.010) | prediction (Cranfield, TEP up; boiler down) wrong on 2 of 3 plants | **REVERTED** |
| 5 TEP SHIFT + WIDE | 0.637 = | 0.524 = | **0.539** (+0.104) | TEP case top-1 0.435 → 0.521, belief group 0.193 → 0.422; detection, false alarms unchanged | **KEPT** (TEP) |

Paired bootstrap over episodes (4,000 resamples, seed 0), accuracy difference vs the kept state:
| step | boiler (13 ep.) | Cranfield (6 ep.) | TEP (20 ep.) |
|---|---|---|---|
| 3 h=1 | +0.030 [−0.013, +0.071] | +0.050 [−0.018, +0.166] | +0.023 [+0.002, +0.054] |
| 3 h=2 | −0.032 [−0.096, +0.035] | +0.046 [+0.000, +0.137] | +0.018 [+0.003, +0.036] |
| 3 h=4 | −0.062 [−0.105, −0.019] | +0.064 [−0.008, +0.149] | +0.019 [+0.001, +0.040] |
| 4 cosine | +0.026 [−0.002, +0.055] | −0.072 [−0.203, +0.000] | +0.009 [+0.001, +0.018] |
| 5 | 0 | 0 | **+0.104 [+0.033, +0.189]** (15 episodes up, 4 down) |

Step 5 per fault (TEP dev, group / case top-1 in fault): gains on PF-05 0.00 → 0.62 / 0.31, PF-16
0.54 → 0.96, PF-17 0.54 → 0.76, PF-20 0.37 → 0.78, PF-08 0.05 → 0.23, PF-11 0.00 → 0.15, PF-13
0.00 → 0.07, PF-12 0.90 → 0.96; losses on PF-01 0.85 → 0.79, PF-07 0.71 → 0.66, PF-18 0.16 → 0.08.
PF-03, 09, 10, 15 stay at ~0. PF-05's group credit (0.62) is twice its case credit (0.31): half of it is
picking another member of the B2 "empty" group (see Disagreements 2).

## Verification
| step | result |
|---|---|
| ran the modules | every row above is a full dev run of all three plants (`bench/accuracy_table.py`, ~3 min each) |
| self-tests | new: `test_in_fault_scoring` 4, `test_state_persistence` 5, `test_score_smoothing` 2, `test_match_measure` 3, `test_tep_shift_spread` 3; `test_tep_pack` updated (2 tests: vocabulary list; variability test narrowed to "fluctuating" facts and now also asserts the ramp's WIDE fact). Plant/asset suites 46 passed. Full suite at step 1: passed except the known flaky `test_real_time_answers_get_the_tokens_of_their_own_envelope` (fails on main too) |
| identity (switches off) | after the step-2/3/4 code: boiler, Cranfield, TEP equal the kept state on every table number; step 5: boiler and Cranfield equal |
| independent re-derivation | (1) Cranfield in-fault top-1 from timeseries row timestamps and `root_cause_id` (not the evaluator): 0.5242 vs 0.524. (2) step 2a: persistence applied OFFLINE to the baseline state strings: Cranfield false alarms 0.1586 vs agent 0.159, detection 0.732 = 0.732; TEP 0.0503 vs 0.050, detection 0.8069 vs 0.807 (a first offline version used list position for the tick and disagreed on Cranfield, whose ticks start at 9 after warm-up; the bug was mine). (3) step 5: TEP in-fault accuracy from the run file and `case_groups.json` directly: 0.5388 vs 0.539. (4) cosine by hand: 2/√10 = 0.632, 3/√35 = 0.507 = the test's values. (5) bootstrap mean differences equal the table differences |
| mutation checks | tick dated k·tick instead of (k+1)·tick → 2 in-fault tests fail; persistence `>=` → `>` → 3 fail; EWMA bias correction removed → 1 fails; gap decay removed → 1 fails; cosine norm not square-rooted → 2 fail; SHIFT sign flipped → direction test fails; WIDE on changes instead of values → fit-equals-agent test fails |
| fit = agent (step 5) | `shift_and_spread` facts equal `fit_signatures.window_shift` / `window_value_sd` tick by tick on a synthetic step-then-widen series |

## Direction checks
| claim | expected | measured | |
|---|---|---|---|
| persistence can only remove alarms | false alarms and detection both fall or stay | Cranfield 0.376 → 0.159, 0.760 → 0.732; TEP 0.239 → 0.050, 0.853 → 0.807 | OK |
| INFO facts do not move the state | detection, false alarms unchanged at step 5 | 0.807 / 0.050 / 2.51 before and after | OK |
| stricter limits trade detection for false alarms | both fall at 2b | TEP 0.050 → 0.000, 0.807 → 0.730 | OK |
| cosine helps where larger cases win (step 4 prediction) | Cranfield, TEP up; boiler down | boiler +0.026, Cranfield −0.072, TEP +0.010 | **FAIL** (prediction; recorded, explanation not confirmed) |
| step 5 gives faults 5, 10, 13 a signature | 5, 10, 13 gain | 5, 11, 13 gain; 10 stays empty | **partly FAIL** (recorded) |
| fault 5 shifts the condenser cooling-water valve UP | SHIFT_UP | fitted `condenser_cw_valve|SHIFT_UP` (training) | OK |

## Constants introduced
| symbol | value | provenance | range | affects |
|---|---|---|---|---|
| `agent.state_persistence_ticks` | 3 (Cranfield, TEP); 1 = off (boiler) | DESIGN, pre-registered | 2–4 | false alarms, detection, delay +(N−1) ticks |
| α_F (2b, code kept, off) | 0.01 | DESIGN, 99 % control-limit convention | 0.005–0.05 | 2b thresholds (reverted) |
| EWMA half-life (3, code kept, off) | 2 ticks | DESIGN, pre-registered | 1–4 | retrieval order (reverted) |
| `retrieval.match_measure` (4, code kept) | jaccard | unchanged default | jaccard, cosine | retrieval order |
| TEP `checks.shift` thresholds | healthy p99.7 of \|60-min mean − first-hour mean\| | FITTED, fault-free training runs | p99.7 by the B2 convention | SHIFT facts, TEP signatures |
| TEP `checks.spread` thresholds | healthy p99.7 of the 60-min sd of values | FITTED, fault-free training runs | as above | WIDE facts, TEP signatures |
| shift/spread windows | 60 min (20 samples) | DESIGN, as the variability check | 30–120 min | as above |

## Numbers that changed
| quantity (dev, mock) | old | new | ratio | downstream |
|---|---|---|---|---|
| Cranfield false alarms before fault | 0.376 | 0.159 | 0.42 | board runs, paper detection table |
| Cranfield detection | 0.760 | 0.732 | 0.96 | as above |
| TEP false alarms before fault | 0.239 | 0.050 | 0.21 | as above |
| TEP fault-free FP/h | 5.53 | 2.51 | 0.45 | as above |
| TEP detection | 0.853 | 0.807 | 0.95 | as above |
| TEP accuracy (group top-1) | 0.435 | 0.539 | 1.24 | headline accuracy; energy per correct diagnosis |
| TEP belief group | 0.193 | 0.422 | 2.19 | hybrid merge (belief leads where strong) |
| TEP library | 13 cases with a signature, 7 empty | 16 with, 4 empty (3, 9, 10, 15); sizes up (PF-06 27 → 58, PF-12 12 → 33, PF-02 13 → 30) | | prompts, case groups |
| TEP prompt tokens (multi v3) | diag median 596/650, verifier over 1,280: 13 calls, max 1,737 | diag median 768/843 (max 1,179); verifier calls 375 → 641, over 1,280: **50**, max **2,650** | | board prefill time, the 1,280 budget |
| TEP AI invocation rate | 0.684 | 0.688 | | cost |

## Decisions taken
1. **2b judged against the kept 2a state, and reverted on both plants**; α_F was not loosened to make it
   pass (that would be choosing an input to reproduce a target). Code kept (`JOINT = False`), fingerprints
   carry the corrected quantiles.
2. **The 2b and step-5 re-fits keep the B2 `case_groups.json` for scoring.** Regenerating the groups from a
   re-fitted library merges cases (2b: PF-16 into the empty group, PF-07 + PF-08), which would make group
   top-1 easier without a better diagnosis: a change of what the benchmark measures. Strict case top-1 is
   reported beside it.
3. **Step 3: the step-specific rule (≥ 2 of 3 plants) governs over the general "per plant" sentence**,
   which conflict; the step-specific one changes less. Cranfield alone would have passed a per-plant reading.
4. **Step 3 half-life 1 not adopted** although it passes the rule on all three plants: it was
   pre-registered as sensitivity, "not chosen between". Needs a human decision (below).
5. **Step 5 facts are INFO**, so detection and false alarms cannot move and the step is judged on
   diagnosis alone.

## Disagreements recorded, not resolved
1. **The step-4 explanation is not confirmed.** "Larger cases win on Cranfield/TEP" was measured, but
   the fix that follows from it hurt Cranfield (−0.072, 2 of 6 episodes) and helped the boiler. Why is
   unexplained; the larger-winner count may not be the cause of the misses.
2. **Group credit on TEP is partly structural.** The B2 groups put the seven originally empty faults in
   one group; after step 5, PF-05, PF-11 and PF-13 have signatures but still share that group, so picking
   PF-11 on a fault-5 tick scores as right (PF-05 group 0.62 vs case 0.31). Overall the gap is small
   (group 0.539 vs case 0.521).
3. **Cranfield's remaining false alarms are an operating-point gap, not noise**: set 5.1 runs outside the
   T1–T3 envelope for its whole pre-fault segment. No threshold rule fixes it.
4. **SHIFT thresholds are fitted on 25-h training runs; test episodes are 48 h.** Healthy drift over 47 h
   is wider than over 24 h, so late fault-free ticks may carry spurious SHIFT facts (INFO: no alarm, but
   they enter the signature). Not measured.

## Blocked / needs a decision
1. **Step 3 at half-life 1?** Passes on all three plants on dev (+0.030 / +0.050 / +0.023, only TEP's
   interval excludes 0). Options: (a) leave off (current); (b) pre-register h = 1 now and accept it on the
   reporting sets alone; (c) build a second dev set and test h = 1 there.
2. **Advisor sign-off for step 5** (it changes case data: the TEP library's vocabulary and signatures).
3. **Verifier prompt size** (open since B2): step 5 raised over-budget verifier calls from 13 to 50,
   max 2,650 tokens. Options: show the verifier only cited + the most severe facts (behaviour change for
   every plant), or exclude INFO facts from the verifier, or leave flagged.
4. **Board re-run** for the kept state (Cranfield and TEP): mock numbers are not agent results.

## What I could not verify
- Any LLM result: all mock. The line-1 rule (Llama follows line 1 88–100 %) was measured on the old
  libraries; whether it holds with step 5's larger TEP cases is a board question.
- Whether TEP's literature-undetectable faults (3, 9, 15) are truly undetectable with these windows, or
  only with these statistics.
- `derive_state` compares `len(wm.trusted_tags)` with the BOILER tag count (`TAGS`, 6): on Cranfield and
  TEP a lost instrument can never show DEGRADED (51 trusted of 52 > 6). Found while writing the
  persistence test; not fixed (behaviour change, outside this stage).
