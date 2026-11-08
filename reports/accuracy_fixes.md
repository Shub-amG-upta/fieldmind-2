# Accuracy fixes (steps 1–5) — report

## Status
IN PROGRESS. Branch `accuracy-fixes` from `breadth-tep` (1f7b422).

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
`retrieval.match_measure: cosine`: weighted cosine (Ochiai) Σ min-free product a·b / (‖a‖‖b‖) over the same
triples and weights, which normalises by each case's own size; contradiction factor 0.15, provenance and
weight, the 0.01 floor, wildcards: unchanged. Default `jaccard` (identity). Applied to all three plants.
Expected direction, stated before the run: Cranfield and TEP up, boiler down or flat.
Kept on a plant if its accuracy rises by ≥ 0.02 with a paired-bootstrap 95 % interval (episodes, 4,000
resamples, seed 0) above −0.01, and kept for the agent as a whole only if no plant falls by > 0.01.
If the plants disagree, the step is recorded as plant-dependent and NOT kept (conservative), and the
per-plant result is reported. Case groups (the scoring definition) are not changed.

Step 5: rule written here, and committed, before its first run.

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
