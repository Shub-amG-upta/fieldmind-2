# Scheduling study, Stage A: the real-time engine — report

## Status
DONE (laptop, mock backend) — real time runs the best system (v3, merge rule `hybrid`, with or without
explain + clear_skip) under four placement policies, with priority queues, deadlines in ticks, per-call
telemetry and a study runner. No board run yet; every number below is **mock backend on the laptop:
plumbing only, not an agent result** (the mock model does no reasoning; its timings are laptop timings).

## What was built (commits `sched A1-A3/A5` 315fef7, `sched A4`, `sched A6`)
| item | where |
|---|---|
| A1 per-lane queues ordered (priority, submit order); one waiting job per (agent, side) | `fieldmind/multi/realtime.py` |
| A2 policies `fixed`, `earliest_finish` (lane free time incl. queued work + prompt/prefill + cap/decode), `tick_alternation`, `priority_reserved`; decision-model jobs keep their lane | `realtime.py`, `scheduler.py` |
| measured-rate EWMA (0.3), only with `multi.adapt_rates` | `realtime.py`, `configs/base.yaml` |
| A3 every merge rule in real time (`apply_rule` after the side fold) | `orchestrator.py` |
| A4 explain as a two-stage job: the runner submits the decision-model follow-up the moment a side ranking finishes and releases both together | `realtime.py` (`followup`, `chained`), `orchestrator.py` (`_explain_followup`, `_explain_rt`), `gate.py` (`fold_bev(check_stale=)`), `agents/bev.py` (`REALTIME_OK`) |
| runner `idle()` covers the hand-on window (fix, below) | `realtime.py` (`settling`) |
| A5 deadlines in ticks (`multi.rt_deadline_ticks`), spans per call, per-run summary | `realtime.py`, `bench/harness.py` |
| A6 study runner: registered matrix, `plan` / `run` / `table` / `rates`; `--placement` through the benchmark runner; refusal to run real time on the board with unmeasured lane rates | `bench/sched_study.py`, `bench/benchmark.py`, `run_demo.py`, `configs/sched_study.yaml` |

## Verification
| step | result |
|---|---|
| ran the module | dry matrix on mock, 36 tests (4 lockstep + 32 real time at a 0.05 s wall tick), all exit 0; table printed (excerpt below) |
| self-tests | `test_sched_policies` 12, `test_rt_explain` 3, `test_sched_study` 6, `test_realtime` 16: all pass. Full suite on the final code: 752 passed, 4 skipped, 1 failed — the failure is an inherited flaky test (decision 8), fixed in the test; it then passed 6 of 6 runs |
| independent re-derivation | (1) deadline misses recounted from raw spans (end - evidence wall tick > deadline) vs the runner's own count (age at finish, unrounded): 47 of 48 dry runs identical; the 48th differs by one P3 call whose rounded age equals its deadline exactly (0.1000 s vs 0.1 s), a 0.1 ms rounding boundary. (2) Lane overlap by an event sweep vs the runner's pairwise interval sum: max difference 0.0 s over 48 runs |
| mutation check | 17 mutations, all caught — see below |

Mutations (each restored after): six in commit 315fef7 (among them FIFO instead of priority, wrong
alternation parity, rates not updated); fold_bev stale check back on → `test_a_late_follow_up_still_cites…`
(0 of 40 late answers cited); follow-up not chained → 3 tests; replaced follow-up keeps its parent →
`test_a_replaced_follow_up_drops_its_parent…`; `idle()` ignores the hand-on window →
`test_the_runner_is_not_idle_while…`; always adapt rates → `test_without_adapt_rates…`; merge rule skipped in
real time → `test_hybrid_runs_in_real_time…`; `--placement` not passed to the child run →
`test_the_policy_named_on_the_command_line…`; overlap counts one lane → `test_the_sweep_overlap…`; deadline
judged at call start → `test_deadline_misses_are_recounted…`; board refusal of unmeasured rates off →
`test_the_board_runner_refuses…`; lane-rate test running "together" calls one after
the other → `test_lane_rates_reports_each_lane…`.

### Consistency with lockstep (instant mock)
The plan asked for identity "real time == lockstep, tick for tick". That cannot hold: in real time an answer
folds one tick after its evidence at the earliest (the tick never waits), so assessments differ by design.
Checked instead, per evidence tick and side, on what both modes produced:

| check | episode | result |
|---|---|---|
| side answers (cases shown + answer), v3 | dev_B01 | 57 / 57 identical (only the last tick differs: real time ends before its answer folds) |
| explain composed answers (Llama ranking + decision-model citations) | dev_B01 | 45 / 45 identical (lockstep 53, real time 54) |
| same | Cranfield F5 | 85 / 85 identical (lockstep 92, real time 91) |
| same | dev_B02 | 4 / 4 identical, but only 4 of 18 overlap: which ticks call the model differs between modes |
| hybrid rule records | dev_A02 | rule published on the same 64 ticks; regime identical on 64 / 64 |

### Mock dry-matrix excerpt (plumbing only)
| config | policy | s / tick | plant | P2 missed | calls npu / cpu / bev | group top-1 | lockstep |
|---|---|---|---|---|---|---|---|
| v3 | fixed | 10 | boiler | 2/61 | 98 / 9 / 0 | 0.797 | 0.789 |
| v3 | tick_alternation | 10 | boiler | 0/61 | 53 / 54 / 0 | 0.797 | 0.789 |
| v3 | earliest_finish | 10 | cranfield | 91/117 | 2 / 118 / 0 | 0.344 | 0.328 |
| v3x | fixed | 10 | boiler | 0/58 | 91 / 9 / 91 | 0.797 | 0.789 |

Not results: at the dry 0.05 s wall tick, Cranfield's hard path (laptop p50 85 ms, p95 104 ms) is longer than the
tick, so jobs are submitted ~74 ms after their tick and most P2 calls "miss"; P1's 1/3-tick deadline (17 ms)
is always missed. Measured, not assumed (spans: submit − tick p50 0.074 s, run 0.0 s, wait 0.002 s).

## Direction checks
| claim | expected | measured | |
|---|---|---|---|
| P1 job overtakes a waiting P3 on its lane | P1 first | order ["P1", "P3"] | OK |
| earliest_finish moves off a busy lane | CPU when NPU busy | CPU | OK |
| a late follow-up is used with its accepted side answer | cited | 40 late answers, ≥ 80 % cited | OK |
| mock rates feed back into lane choice when adapt_rates is on | winner lane attracts all | boiler earliest_finish 107/0, Cranfield 2/118 | OK (see decisions) |

## Constants introduced
| symbol | value | provenance | range | affects |
|---|---|---|---|---|
| RATE_EWMA | 0.3 | DESIGN | 0.1–0.5 | how fast predicted lane rates follow measured calls (real time, `adapt_rates` only) |
| rt_deadline_ticks | P1 1/3, P2 1, P3 2, P4 none | DERIVED: plan deadlines 10 / 30 / 60 s ÷ the plan's 30 s tick | — | real-time deadline accounting only |
| study loads | 10 s, 5 s per 30 s tick | CITED: approved plan (2026-11-09) | open decision, prereg | the study only |

## Numbers that changed
None outside real time. Lockstep is untouched (its `fixed` / `earliest_finish` paths unchanged;
`tick_alternation` added; `priority_reserved` equals `earliest_finish` in lockstep, where nothing waits).

## Decisions taken
1. **Identity replaced by per-evidence consistency** (above): identity is impossible by design.
2. **Explain follow-up staleness is judged with its side answer** (`fold_bev(check_stale=False)` for chained
   replies): fold_sides accepts a late answer while that side's evidence is unchanged; dropping its follow-up by
   the stricter one-tick rule would publish the ranking uncited (the mutation shows 0 of 40 late answers cited).
3. **`adapt_rates` off by default, on in `configs/sched_study.yaml`.** Off keeps mock runs deterministic (mock
   timings are noise and pull every job onto whichever lane measured fastest); on the board measured rates are
   the point.
4. **Runner `idle()` fix**: between a call ending and its result reaching the done queue (or its follow-up being
   queued) nothing was running or waiting, so `wait_idle()` could return and a final `drain()` lose that result.
   A `settling` count now covers the window (test holds the window open and checks `idle()` is False).
5. **Episodes**: Cranfield F1 replaced by boiler dev_A02 (reasons in `reports/sched_prereg.md`).
6. **Accuracy bar**: each policy against real-time `fixed` at the same load, not lockstep (prereg).
7. **The study's agent runs on the laptop** (Stage B report, decision 1).
8. **Flaky test fixed, not the code.** `test_real_time_answers_get_the_tokens_of_their_own_envelope` failed 3 of
   4 runs on this branch, 3 of 4 at commit 315fef7 and 5 of 5 at the merge commit 1896fc4 (before any of this
   work). Cause, verified: it left stale-dropped jobs out of the token sum while their envelopes (real calls)
   stayed in; at a 0.02 s tick whether an answer goes stale is timing. With every finished call counted the sums
   match exactly (19,595 = 19,595 on the failing run).

## Disagreements recorded, not resolved
- Plan "real time == lockstep tick for tick" vs the design rule "the tick never waits": both cannot hold; the
  design rule wins, consistency is checked per evidence instead.
- Plan's study scope (10 s and 5 s) vs measured board call times: predicted to contend for a lane only on Cranfield
  at 5 s (prereg "Predictions"); recorded, not changed.

## Blocked / needs a decision
- **Load levels** (prereg "Open decision", options A / B / C) — before HANDOFF_SCHED.md step 4.
- Llama 3B CPU-lane rates: unmeasured; the board runner refuses real time until HANDOFF step 3 fills them.

## What I could not verify
- Any board behaviour: real lane contention, the shared-memory slowdown, Llama's CPU speed, Laya follow-up
  latency under load, chip temperature effects. All in HANDOFF_SCHED.md.
- Cranfield split-diagnostician call times on the board (no such run here); prediction 3 assumes boiler-like calls.
- Run-to-run spread of real-time results (registered repeat cells measure it).
