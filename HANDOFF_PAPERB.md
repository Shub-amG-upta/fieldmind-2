# Paper B: handoff (2026-11-12)

**Branch `sched-study`. Full suite on the last code commit (`a799fb0`): 831 passed, 5 skipped.**

**Where things stand:**
- everything for Paper B that could be built or run on a laptop is done;
- nothing has been run on the board since the sweep;
- no scored run has been made for any new item.

The work now waits on three decisions (below), then on board time.

- What to do and why: `PLAN_PAPER_B.md`.
- The board commands, in run order: `HANDOFF_PAPERB_BOARD.md`.
- Every command comes from `bench/paperB_board.py plan` (`check` confirms every file it names exists).

## 1. Decisions needed before any board or scored run

| decision | where | what is PROPOSED |
|---|---|---|
| Thresholds and pass rules | `reports/ext_faultexplainer_prereg.md`, `reports/paperB_item2_prereg.md`, `reports/sched_fix.md` part D, `reports/echo_prereg.md` | each file's PROPOSED rows. Date them under "Agreed" before the first scored run |
| Pay for GPT-4o calls? | `reports/ext_faultexplainer_prereg.md`, arm F0 | reproduces FaultExplainer's own result with its own model; costs API money. Arm F1 (our 3B on the NPU) runs without it |
| Which power meter | `PLAN_PAPER_B.md` item 4 | a logging meter on the board's DC input. Without one there are no energy numbers, and B is not a main-conference paper |

## 2. What was built this session

| item | what | state | code | tests |
|---|---|---|---|---|
| 5 | First-look results redone in tested code | **DONE** | `bench/echo_test.py changed`, `bench/sched_study.py hostload`, `heat` | +7 |
| 8 | Reading-speed gap with arXiv 2605.27435 | laptop part done; 30 min of board left | `bench/paperB_board.py plan --item 8` | – |
| 1 | External audit: FaultExplainer, through its own prompt code | harness built; 2-call pilot (plumbing) | `bench/ext_faultexplainer.py` | 8 |
| 2 | Published echo fixes: no example, no letters, calibrate (Zhao 2021), PriDe (Zheng 2024), PSC (Tang) | built, off by default; laptop smoke test | `fieldmind/multi/debias.py`, `configs/debias_*.yaml`, `bench/paperB_score.py` | 18 + 6 |
| 4 | Energy from an external meter | software built; needs the meter | `bench/energy.py` | 5 |
| 6 | `calibrated_finish` on the board | commands ready; mock dry run done | `bench/paperB_board.py plan --item 6` | 3 |
| 7 | More episodes, 3 repeats | commands ready; cells PROPOSED | `bench/paperB_board.py plan --item 7` | (in the 3 above) |
| 10 | Gate that calls the model only when it can matter | **not built, on purpose** | – | – |
| 3 | Echo replay on another laptop | thresholds still PROPOSED | `HANDOFF_ECHO_REPLAY.md` | – |

**Why item 10 is not built:** its skip rule needs a threshold, and that should be chosen after items 1 and 2.

**Small changes to existing code:**
- `bench/benchmark.py` records each run's process window (`child_t0_unix`, `child_t1_unix`) for the meter;
- `bench/board_sampler.py` records its laptop start time;
- the runner and `run_demo.py` accept `--placement calibrated_finish`. Before this they did not, so item 6 would have failed at start-up;
- `LlamaServerBackend` can return token log-probabilities (`LLMReply.token_probs`). It does so only when a debias
  switch asks for them. With every switch off, the run is unchanged (tested).

## 3. Results so far

| label | meaning |
|---|---|
| BOARD | the saved sweep runs |
| LAPTOP | plumbing only, not results |
| MOCK | no-model, not an agent result |

| finding | value | label | source |
|---|---|---|---|
| The model changes the published top cause vs no-model | Cranfield 2 of 500 scored ticks (0.40%); TEP 17 of 2,593 (0.66%), board right 3 vs no-model right 9 | BOARD vs MOCK | `reports/paperB_prep.md` |
| NPU lane's host CPU load | 1.24 cores per busy second (real time, 52 runs), 1.38 (lockstep, 254 runs); none while idle | BOARD | same |
| CPU lane's host CPU load | about 5.97 cores | BOARD | same |
| Sampler cost | 0.75 of a core | BOARD | same |
| Heat: speed of hot runs relative to cool runs, reading | boiler 0.82, Cranfield 0.78, TEP 0.91 (an association, not a cause) | BOARD | same |
| Heat: speed of hot runs relative to cool runs, writing | 0.88–0.92 (an association, not a cause) | BOARD | same |
| Reading-speed gap with 2605.27435 | narrowed to 3 setup differences: build b7588 vs b11371, attention on the CPU, batch 128. **Unexplained** until the board check | – | same |
| Calibrate smoke test | probabilities read 4 of 4 times; the content-free prior puts 0.88 on line 1; the rank-1 line moved off line 1 on 4 of 4 | LAPTOP | same |
| PSC smoke test | 3 of 3 orderings valid each time; changed the answer 1 of 4 times | LAPTOP | same |
| FaultExplainer pilot | 2 of 2 answers parsed; about 68 s per call; one answer hit the 1,400-token cap. **Not scored** | LAPTOP | `reports/ext_faultexplainer_prereg.md` |

**Accuracy convention, so tables agree.** The headline is the mean over episodes of group top-1 in the fault windows.
For example, the Cranfield v3 board run is 0.524. Pooled over ticks it is 0.327, because one long episode dominates.
`bench/paperB_score.py` prints both; its test pins both.

**Correction to an earlier note:** GPT-4o names IDV(6) in 11 of 11 of its top-3 lists, not 10.

## 4. Board run order (after the decisions)

1. **Item 8**, 30 min: restore the lane afterwards.
2. **Item 6**, 3–4 h.
3. **Item 1**, arm F1: 1.5–2.6 h. It makes 108 calls, with answers up to 1,400 tokens.
4. **Item 2**, about two nights.
5. **Item 7**, about two to three nights.
6. **Item 4**, once a meter exists: `bench/energy.py idle` first, then score the runs above with `bench/energy.py runs`.

**Board rules (CLAUDE.md):**
- `/board-up` with the sweep's file;
- check the sha256 after every push;
- log chip temperature before and after each run, with cooling gaps between runs;
- use laptop time only;
- dev episodes only, never the reporting episodes for decisions.

## 5. Known limits to state in the paper

- **Item 2 base runs are older.** The base runs it compares against (`af_cf_v3_dev`, `af_tep_v3_board`, the sweep's
  lockstep cells) were made earlier, so heat and date differ from the new arms.
- **calibrate and PriDe re-choose only the rank-1 line.** They need raw token log-probabilities, which only llama-server
  gives. On other backends they record `unchanged_because: no_probs`.
- **The FaultExplainer eval prompt leaks the true fault number.** `eval_noleak` is the arm without the leak. Faults 3,
  4, 9 and 15 are not detected by its PCA, so 9 faults are used.
- **The `sched_replay` model does not reproduce `earliest_finish`** (cause unknown, `reports/sched_fix.md`). It is
  recorded, not fixed.
- **Agent code runs on the laptop.** Its hard-path timings are not board timings.

## 6. Files outside git

These are gitignored and live on this laptop only:
- `results/ext/faultexplainer_pilot.jsonl`;
- `results/benchmarks_mock/paperB_nomodel_v3x_cranfield` and `paperB_nomodel_v3x_tep`, the no-model folders for item 2;
- plumbing runs under `results/benchmarks*/paperB_psc/` and `sched_v3x_calibrated_finish_t5_cranfield_dry`.

**Rebuilding the no-model side:** `bench/paperB_board.py plan --item 2 --backend mock` prints every item-2 run on the
mock backend (same episodes and overlays).

## 7. Paused

Shortening `CLAUDE.md` is paused. Each change is to be shown before it is made.
