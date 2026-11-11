# Echo test, stage 1 steps 1–2: tested tool and echo on every dev run — report

## Status
DONE — `bench/echo_test.py saved` (tested, mutation-checked) measures whether the diagnostician picks line 1 of the
case list, and how often its other picks are right, over saved run files. Run on every dev run folder in git (44
folder/lane rows). Saved board runs only: no model was called. Laptop analysis of board runs (agent code ran on a laptop,
model calls on the QIDK NPU unless the lane says cpu). Plant data: boiler synthetic, Cranfield real rig, TEP simulated.

## Verification
| step | result |
|---|---|
| ran the module | 44 rows over every dev-only folder in `results/benchmarks/`; 13 folders refused as reporting (listed below) |
| self-tests | `tests/test_echo_test.py`: 10 passed |
| independent re-derivation | `bench/board_insights.py` (separate code, reads `multi.compact` case ids, not the prompt): line-1 follow af_cf_v3_dev 1.000 / 1.000, af_tep_v3_board 0.998 / 0.998, af_cf_bev2_dev 0.483 / 0.483, af_tep_bev2_board 0.394 / 0.394 (relative difference 0). Deviations differ by definition: board_insights 138 (0.116 right) and 2,521 (0.105) over **all** answers with two or more cases; this tool 128 (0.086) and 2,397 (0.108) from fault onset onward. Recounted with board_insights' rules through this tool's parser: 138 / 0.116 and 2,521 / 0.105, exact. Explained, verified |
| scratch fidelity | shuffled Cranfield 423 / 1.000 / 0.998; cranfield_dev_v3 422 / 0.998 / 0.991; bevideas_A1 404 / 0.985 / 0.973; multi_v2_6mark (reporting, flag) 227 scored, 131 deviations, right 0.008, random other line 0.006, line 1 right 0.802. All exact |
| mutation check | 11 of 11 caught: line-1 rule (`test_line1_and_identity_shares`), group as exact (`test_deviation_right_exact_and_by_group`), onset `>` for `>=` (`test_answers_before_fault_onset_are_not_scored`), pick ignoring prompt numbering (`test_a_correct_line1_is_counted_when_the_model_leaves_it`), held-out scored as itself (`test_a_held_out_target_scores_by_its_group`), reporting not refused (`test_reporting_episodes_…`), chance 1/(k+1), random including line 1, identity off by one, verifier counted (`test_unusable_and_other_envelopes_are_skipped`), rank-only answers dropped (`test_rank_only_explain_answers_are_read`) |

## Results (dev runs, BOARD)

**Full-answer format (v3 diagnosis):** the model picks line 1 almost always, on every plant.

| plant, runs | answers per run | line 1 | whole answer 1, 2, … | deviations (scored) |
|---|---|---|---|---|
| boiler, `bevideas_*` (10 runs, 10 dev episodes) | 342–406 | 0.980–0.988 | 0.955–0.973 | 5–7 per run |
| boiler, `sched_v3_*` (lockstep and real time, dev_A02 + dev_B01) | 87–192 | 1.000 | 0.949–0.958 | 0 |
| Cranfield, `cranfield_dev_v3`, `_bev`, `_meas`, `_trial`, `sched_v3_*` | 39–423 | 0.984–1.000 | 0.923–1.000 | 0–1 |
| Cranfield, **case order shuffled** | 423 | **1.000** | 0.998 | 0 |
| TEP board subset (dev), `tep_v3_board`, `af_tep_v3_board` | 4,591 / 4,698 | 0.997 / 0.998 | 0.996 | 15 / 8 |

There are too few deviations in this format to judge whether the model's own picks are right.

**Rank-only format, no worked example in the prompt (explain_v2, `af_*_bev2_*`):** the model leaves line 1 often,
and its own picks are about as good as a random other line.

| run | answers | line 1 | scored deviations | right (exact) | random other line | line 1 would have been right |
|---|---|---|---|---|---|---|
| Cranfield dev, `af_cf_bev2_dev` | 267 | 0.483 | 128 | 0.086 | 0.102 | 0.352 |
| TEP dev, `af_tep_bev2_board` | 4,163 | 0.394 | 2,397 | 0.108 | 0.085 | 0.427 |

This is the dev-set, tested counterpart of the reporting-set v2 result. When the model chooses for itself, its pick is
right about as often as chance, and line 1 would have been right three to four times as often.

**Rank-only format with the example `{"r":[2,1]}` (v3x):** a third shortcut, copying the example.

| run | answers with a choice | most common answers | line 1 |
|---|---|---|---|
| Cranfield, `sched_v3x_lockstep_cranfield` | 96 | **`[2,1]` 83 (86%)**, `[3,1]` 6, `[1,3]` 4 | 0.193 |
| boiler, `sched_v3x_lockstep_boiler` | 84 | `[1,3]` 52, `[1,2]` 21, `[2,1]` 7 | 0.875 |

On Cranfield, 86% of v3x answers are the prompt's example verbatim. On the boiler the same prompt template mostly gets
`[1,3]`. Without an example (explain_v2 on TEP), the most common answer is `[3,4]` (1,119 of 4,163). The prompt's surface
form (letters, position, the worked example) predicts the pick better than the evidence does.

## Direction checks
| claim | expected | measured | OK/FAIL |
|---|---|---|---|
| a model that reads the cases moves its pick with a shuffle | line-1 rate falls toward chance (0.639) | 1.000 under shuffle | FAIL for "reads the cases": the finding |
| a model that reasons is right more often than chance when it leaves line 1 | dev right > random other line | 0.086 vs 0.102 (Cranfield), 0.108 vs 0.085 (TEP) | FAIL for "reasons": the finding |
| the mock ranks by retrieval score | line 1 always | not run here (mock rows are 1 by construction) | – |

## Constants introduced
| symbol | value | provenance | range | affects |
|---|---|---|---|---|
| `DEV_DIRS` | 4 folders | CITED: the dev sets of `reports/b1_*`, `reports/b2_tep_pack.md` (TEP board subset = the 22 dev runs cut to 16 h), CLAUDE.md dev set rule | fixed | which episodes count as dev |

No numeric constant. "chance" is the mean of 1 / (case lines shown); the scratch script used 1 / (mean lines), so
chance figures quoted earlier (0.55 for Cranfield) differ from this tool's (0.639). This tool's definition is the
expected line-1 share of a uniform pick.

## Numbers that changed
Chance for Cranfield: 0.55 (scratch, 1 / mean) → 0.639 (mean of 1/k). The definition changed, not the data; nothing
downstream used it.

## Disagreements recorded, not resolved
- The v3x example-copying is plant-dependent (86% on Cranfield, 8% on the boiler) under the same prompt template. No
  cause tested. Candidate differences: case count per prompt, case-line wording. Unexplained.
- v3x Cranfield accuracy equals v3's (lockstep group top-1 0.328 both) although 86% of its answers copy the example. The
  merge and the decision-model follow-up decide what is published; how much the copied ranking reaches the published
  answer is not measured here.

## Blocked / needs a decision
None for steps 1–2.

## What I could not verify
- Whether the shortcuts come from the 4-bit file, the 3B size or the prompt. That is Stage 2 (replay on other files
  and models).
- Deviation accuracy in the full-answer format: 0–15 deviations per run is too few to estimate it.
- The explain_v2 and v3x runs use different follow-up models (bev-decider vs Laya). Their effect on the published
  answer is outside this tool.
- Folders refused as reporting (not used): bev3_armB, bev3_six, bev_armB, cranfield_report_v3, multi_nudge_6.1mark,
  multi_nudge_6mark, multi_tiebreak_6mark, multi_v2_6mark, multi_v3, multi_v3_livedemo, single_6mark, six_episodes,
  v3_new.
