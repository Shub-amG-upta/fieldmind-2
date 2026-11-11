# Laptop plan, stage 1 steps 3–6: deadlines at release, the overload freeze, two bugs, no-model arms — report

## Status
DONE — Steps 3–6 of `PLAN_LAPTOP_ECHO_SCHED.md` stage 1, all on the laptop, with no board:
- **Step 3:** deadlines are also judged when an answer is released;
- **Step 4:** the Cranfield overload freeze is traced to the nudge rule;
- **Step 5:** two runner bugs fixed;
- **Step 6:** the two no-model arms measured on the dev sets.

Steps 1–2 are in `reports/echo_saved.md`. Board numbers are from Gagan's 2026-11-10/11 sweep (agent on a laptop, model calls
on the QIDK). Mock numbers measure the deterministic layers only. Plant data: boiler synthetic, Cranfield real rig,
TEP simulated.

## Verification
| step | result |
|---|---|
| ran the module | `bench.sched_study table` on the 32 sweep cells, exit 0 (`results/sched_handoff_log/table_release.txt`); `bench/sched_study.py rates` as a script reaches "lane(s) not up" (no board); `bench/accuracy_table.py` both arms, exit 0 |
| self-tests | `tests/test_sched_study.py` 13 passed (was 1 failed: the live-config test); with the realtime suites, 29 passed |
| independent re-derivation | (a) Step 3 matching rule against the recorded parent links: a fresh v3x mock real-time run records `parent`; matching with the field removed gives the same pairs (`test_realtime_records_each_follow_ups_call_and_matching_agrees`). (b) Step 4 freeze: published rank-1 recomputed as argmax(belief log-odds + recorded offsets) on non-model-led post-onset ticks: 61/61, 62/62, 62/62 and 61/61 in four cells; 44/62 in `sched_v3x_earliest_finish_t2_cranfield` (unexplained, below). (c) Step 6: the belief-only arm's published group top-1 against the belief column of the retriever arm: 0.508 / 0.502 (boiler), 0.343 / 0.343, 0.421 / 0.422 |
| mutation check | Step 3: 6 of 6 caught (follow-up ignored; follow-ups counted twice; 10 s window; side ignored; matching over the record; parent never recorded). Step 5: removing the `sys.path` line brings `ModuleNotFoundError` back |

## Step 3: deadlines at release
- **What changed.** A call followed by a decision-model follow-up (`bev_explain`) hands its answer on only when the
  follow-up ends (`fieldmind/multi/realtime.py`, chained results). The table judged it at the call's end, and it counted
  the follow-up as a separate P3 job.
  - **New column:** "P1 / P2 missed at release". Every existing column is unchanged: 0 of 47 lines differ once the new
    column is removed.
  - **New runs:** spans record `parent` (recording only).
  - **Older runs:** follow-ups are matched to their call. All 1,611 follow-ups in the sweep matched exactly one call,
    submitted at most 0.6 ms after it ended.

| v3x boiler, P1 (urgent) | 5 s | 4 s | 3 s | 2 s |
|---|---|---|---|---|
| missed at call end (as before) | 0/34 | 0/34 | 30/34 | 34/34 |
| missed at release | **5/34** | **28/34** | 33/34 | 34/34 |

| v3x Cranfield, P2 (`fixed` / `earliest_finish`) | 5 s | 4 s | 3 s | 2 s |
|---|---|---|---|---|
| at call end | 0 / 9 of 115 | 0 / 6 | 6 / 28 | 55 / 65 of 95 / 93 |
| at release | 0 / 11 | 0 / 6 | 27 / 47 | 74 / 74 |

**Capacity is unchanged under the pre-registered rule.** It uses P2 at call end, and at release every cell's verdict is
the same: v3x boiler 2 s; v3x Cranfield `fixed` 4 s, `earliest_finish` none. The claim "short answers meet urgent
deadlines" holds only at 5 s per tick once the follow-up is counted.

## Step 4: the overload freeze is the nudge rule, not a bug
- **Observation.** In three overloaded Cranfield cells, the published cause is CF-4 (wrong) on every post-onset tick,
  and group top-1 is 0.000:
  - `sched_v3_earliest_finish_t3`;
  - `sched_v3x_fixed_t2`;
  - `sched_v3x_earliest_finish_t2`.
- **Mechanism, verified on the run files:**
  1. **The model is not leading.** `hybrid` records `model_led: false` on 61–62 of 62 post-onset ticks; belief is in
     its "clear" regime almost throughout.
  2. **What is published instead.** In that regime `hybrid` publishes belief log-odds plus the model's nudge offsets.
     The argmax of that sum reproduces the published rank-1 on 61/61, 62/62 and 62/62 non-model-led post-onset ticks in
     the three cells checked.
  3. **Nudges only grow.** `merge_rules.add_nudges`: each fresh answer adds 0.35 to its rank-1 case and 0.175 to its
     rank-2, capped at 1.2 per case for the whole episode, with no decay. Answers given before the fault still count:
     CF-4 holds 0.35–0.7 at onset in the three frozen cells (1.2 in the 5 s cells).
  4. **Overload decides which cases reach the cap.** Most fresh answers are dropped as stale (65–69 in the frozen cells,
     3 at 5 s), so the true case gains little:
     - **`sched_v3x_fixed_t2` at tick 62:** CF-5 holds 0.35 against CF-4's 1.2.
     - **At 5 s:** every case reaches 1.2 by tick 62, the offsets cancel, belief decides, and CF-5 is published on
       21 ticks.
- **Reading.** This follows from the registered `hybrid`/`nudge` design (monotone, capped, never reset), not from a
  coding error. Under overload, accuracy falls below belief alone (0.000 against 0.344 group top-1 for CF-5).
  - A decay or a per-fault reset would change what the benchmark measures, so **nothing was changed**.
  - **Open decision:** whether a pre-registered variant should be tested.

## Step 5: two bugs
- `bench/sched_study.py rates` imported `bench` only inside the `rates` branch, so it failed when run as a script. The
  repo root now goes on `sys.path`, as in `bench/benchmark.py`.
- `test_the_board_runner_refuses_real_time_with_unmeasured_lane_rates` read the live `configs/sched_study.yaml`, which
  has had measured rates since 2026-11-10. It now stacks its own `lane_rates_measured: false` overlay.

## Step 6: the two no-model arms (MOCK, dev sets, lockstep)
Retriever order = the mock backend with v3's `hybrid` (the agent with the retriever standing in for the model).
Belief only = `merge_rule: belief_only`. Tables: `reports/data/echo_noarm_retriever.txt`, `echo_noarm_belief.txt`.

| dev set | retriever order: group top-1 (in fault) | belief only: group top-1 (in fault) | difference |
|---|---|---|---|
| boiler (36 episodes) | 0.637 (–) | 0.508 (–) | +0.129 |
| Cranfield (6) | 0.417 (0.524) | 0.343 (0.416) | +0.074 (+0.108) |
| TEP (22) | 0.541 (0.541) | 0.421 (0.421) | +0.120 |

- **The gain over belief needs no model.** The gain the dossier credited to the model on reporting episodes ("hybrid
  +0.128 over belief") appears here on dev with no model at all: retriever order beats belief order by 0.07–0.13 group
  top-1.
- **On Cranfield dev, the board's v3 run scores the same as this no-model arm:** 0.524 in fault for both (`af_insights.md`).
  - TEP's board figure (0.475) is on the 16 h board subset, so it is not comparable with the full dev episodes here.
  - On that subset, the mock gave 0.477.

## Direction checks
| claim | expected | measured | OK/FAIL |
|---|---|---|---|
| a follow-up can only make an answer later | missed at release >= missed at call end | 0 violations over all 52 sweep run files (P1, P2) | OK |
| nudges never fall within an episode | each case's offset non-decreasing tick to tick | 0 decreases over all 52 sweep run files | OK |
| more overload, fewer answers land | stale drops rise with load | 3 (v3x fixed 5 s) to 65–69 (the frozen cells) | OK |

## Constants introduced
| symbol | value | provenance | range | affects |
|---|---|---|---|---|
| `FOLLOWUP_AGENTS` | `("bev_explain",)` | CITED: `orchestrator._explain_followup`, the only job chained | fixed | which spans count as follow-ups |
| `FOLLOWUP_GAP_S` | 0.05 s | DESIGN: largest observed gap 0.0006 s over 1,611 follow-ups, no second candidate; a decision call takes ~0.3 s | 0.001 s and 0.25 s give the same pairs on all 52 sweep run files (checked) | matching in runs without `parent` |

## Numbers that changed
None of the existing table's numbers. New: P1/P2 at release, as above.

## Disagreements recorded, not resolved
1. **"Urgent deadlines are met with short answers"** (said in conversation 2026-11-11) holds only at 5 s per tick. At
   4 s, 28 of 34 urgent answers are late at release. Corrected here.
2. **`sched_v3x_earliest_finish_t2_cranfield`:** argmax(belief + recorded offsets) reproduces the published rank-1 on
   44 of 62 ticks, not all. Possibly the decision model's offsets (`total_offsets`) are logged separately from the ones
   recomputed here, but that is untested. Unexplained.
3. **Belief-only arm vs the belief column on the boiler:** 0.508 against 0.502. Possibly tie-breaking order, but that
   is untested. Unexplained, and small.

## Blocked / needs a decision
- Whether to pre-register and test a variant of the nudge rule: decay, a reset at a state change, or a cap below the
  "clear" margin. It would change the benchmark, so it is not done.

## What I could not verify
- Why CF-4 in particular collects early nudges (which answers named it before onset). That is not needed for the
  mechanism, but it would show whether the pre-fault answers were the model's or the decision model's.
- Time and energy of the no-model arms. These need the board.
