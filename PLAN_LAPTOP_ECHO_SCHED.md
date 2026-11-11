# Laptop plan: echo and scheduling work for Paper B

Written 2026-11-11. This is everything for Paper B's echo and scheduling parts that can be done **without the QIDK
board**. Board-only work (energy, more scheduling repeats, cool lane speeds) is listed at the end, for later.

**Facts this plan is built on (checked 2026-11-11):**
- **This laptop:** Apple M2, 8 GB memory, 83 GB free disk. Homebrew llama.cpp build 11429 (`d81235049`), which is
  **not** the pinned board build `99b95488c`.
- **No Llama model file is on this laptop,** only Laya's.
- **Saved runs are in git** on `sched-study`, with prompts and replies:
  - `bevideas_A1`–`A_soak` (10 dev boiler episodes each);
  - `cranfield_dev_v3` and `cranfield_dev_v3_shuffled` (6 Cranfield dev episodes);
  - the `sched_*` runs (dev_A02, dev_B01, cf_F5).
- **All 36 dev episodes exist locally** (`data/episodes_dev`).
- **Gagan's replay tool** (`bench/nd_repeat.py`, on `origin/nd-paper`) replays a saved request with its grammar,
  at temperature 0, seed 0, with no prompt cache. It builds only the no-letters grammar (`with_group=False`).

**Rules that apply:**
- **Dev episodes only** for any decision; reporting episodes (`ep_*`) are descriptive only.
- **Labels on every number:** mock numbers are not model results, and laptop replays test the model, not the NPU.
- **No change to agent behaviour** (`fieldmind/`) without a pre-registered rule.
- **Every new file:** run it, test it, re-derive one number another way, and mutation-check the tests.

---

## Stage 1: analysis of saved runs (no model calls, can start now)

### Step 1: a tested echo tool
- **Build** `bench/echo_test.py`, subcommand `saved`. For each run and lane it reports:
  - **line-1 rate:** the share of diagnostician answers whose rank-1 line is 1;
  - **whole-answer order:** the share whose ranked lines are exactly 1, 2, ..., k;
  - **chance:** the mean of 1 / (number of case lines shown);
  - **deviation accuracy:** among answers that leave line 1, the share whose pick is the true case. Compare it with
    how often line 1 was right, and with a random other line;
  - each of these by **exact case** and by **look-alike group** (the evaluator's `_groups(asset)`);
  - fault episodes only, ticks from fault onset onward (`tick * tick_period_s >= fault_onset_t`).
- **Dev episodes by default;** reporting episodes only with an explicit flag, and labelled.
- **Done when it reproduces the scratch counts:**

  | run | answers | line-1 rate | whole-answer order |
  |---|---|---|---|
  | `cranfield_dev_v3_shuffled` | 423 | 1.000 | 0.998 |
  | `cranfield_dev_v3` | 422 | 0.998 | 0.991 |
  | `bevideas_A1` | 404 | 0.985 | 0.973 |
  | `multi_v2_6mark` (reporting, flag on) | 227 post-onset, 131 leave line 1 | deviations right 0.008 | |

- **Tests:**
  - counts on a hand-built run file;
  - a deviation that is right and one that is wrong;
  - a shuffled order mapped back to case IDs correctly;
  - reporting episodes refused by default.

  Mutation-check them.

### Step 2: echo on every dev run
- **Run step 1's tool** on every dev run in git, including the board `sched_*` dev runs (lockstep and real time).
- **Output:** one table per plant (boiler, Cranfield, TEP if a dev run exists), each number labelled BOARD.
- **Report:** `reports/echo_saved.md`, in the project report format.

### Step 3: urgent (P1) deadlines counted at release time
- **The problem:** `bench/sched_study.py` counts a P1 deadline at the end of the Llama call. In v3x the answer is
  released only after the decision model's follow-up, so the table shows 0/34 missed where the release time gives
  about 5/34 (v3x boiler, 5 s, hand count).
- **Change:** for a call with a follow-up, the deadline is judged at the follow-up's end.
  - Saved runs don't record which follow-up belongs to which call. Match by evidence tick + side + "starts after
    the parent ends", and **test that the match is one to one** (34 of 34 matched by hand).
  - For new runs, add a parent-job field to each span in `fieldmind/multi/realtime.py` (stdlib only; recording
    only, no behaviour change).
- **Output:** the 32-cell table re-scored, with P1 shown both ways (call end and release).
- **Done when** v3x boiler 5 s reads about 5/34 at release time, matching the hand count.

### Step 4: trace the overload freeze
- **The observation:** in three overloaded Cranfield cells (v3 earliest_finish 3 s, v3x fixed 2 s, v3x
  earliest_finish 2 s), the published cause is CF-4 (wrong) on all 61 post-onset ticks.
  - Those cells drop 67–69 answers as stale (3 at 5 s).
  - Belief alone would score 0.344 group top-1; the agent scores 0.000.
- **Do:**
  1. read the stale-drop, gate and merge path;
  2. find why the published ranking stays on CF-4;
  3. reproduce it on the laptop with a mock backend slowed to board-like call times (through the harness's
     `wrap_backend`).
- **Output:** a short report: a bug, or the intended behaviour of the merge rule under stale answers.
- **No fix in this step.** A fix changes what the benchmark measures, so it needs a pre-registered rule and a
  decision.

### Step 5: the two small bugs from the board run
- **`bench/sched_study.py rates`** fails when run as a script: `bench` is imported inside the `rates` branch only,
  so `--help` works but `rates` doesn't. Make it run as a script, the same way the other `bench` scripts do.
- **`tests/test_sched_study.py::test_the_board_runner_refuses_real_time_with_unmeasured_lane_rates`** reads the live
  `configs/sched_study.yaml`, so it fails now that the lane rates are measured (1 failed, 6 passed). Give the test its
  own temporary config.
- **Done when** `rates` starts as a script and the test file passes.

### Step 6: the two no-model arms
- **Retriever-order arm:** the mock backend in lockstep. The mock ranks the retrieved cases by retrieval score and
  passes them through the same merge rule, so it is the agent with the retriever standing in for the model.
- **Belief-only arm:** `merge_rule: belief_only`. The code's belief ranking alone.
- **Run both** on the dev episodes of boiler, Cranfield and TEP.
- **Output:** an accuracy table next to v3's board accuracy on the same episodes. Label it MOCK: these measure the
  deterministic layers, which is exactly what a no-model agent is.
- Time and energy for these arms need the board (see the end).

---

## Stage 2: the echo replay (needs model files and decisions)

### Step 7: get the board's model file
- **Copy** `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf` from Gagan (about 2 GB).
- **Check** its sha256 against `bench.board.CANDIDATES` before any use.

### Step 8: pre-register the replay
Write `reports/echo_prereg.md` and commit it **before** step 9. Contents (detail in `HANDOFF_ECHO.md` step 2):
- **Request set:**
  - dev only, from `bevideas_A1`, `cranfield_dev_v3`, and TEP dev;
  - first confirm whether `af_tep_v3_board` is dev or reporting (`reports/b2_tep_pack.md`);
  - identical prompts deduplicated;
  - a seeded sample.
- **Orderings:** original, 2 seeded shuffles (seeded per request), and line 1 moved to the last line.
- **Shuffle mechanics:** renumber the case lines and keep a line-to-case map. Facts, notes and everything else stay
  byte-identical, and the grammar is unchanged.
- **Measures:**
  - line-1 rate per ordering;
  - **position invariance**, the same case chosen under every ordering;
  - rank-1 accuracy (exact and group);
  - deviation accuracy, with a bootstrap over episodes, not requests.
- **Outcome thresholds,** agreed by the team first. Proposed: "copies position" = shuffled line-1 rate >= 0.8 and
  invariance <= 0.5; "reads the cases" = invariance >= 0.8, and shuffled accuracy within 0.05 of original.
- **Stop rule:** if the laptop's replies to the original order rarely match the saved board replies at rank 1, the
  replay is not faithful. Stop and fix it before reading anything else.

### Step 9: pilot
- **Run** 20 calls with the board file on the laptop.
- **Measure** the call time, to size the full run.
- **Check fidelity** against the saved board replies. Some difference is expected, because the build and the
  hardware differ.

### Step 10: replay with the 4-bit board file
- **Run** all orderings from step 8.
- **Output:** the main echo table for the 4-bit model.

### Step 11: precision arm (Q8_0)
- **Build** the same Llama 3.2 3B at Q8_0 (about 3.4 GB, fits in 8 GB).
- **Needs:**
  - the Hugging Face weights. Meta's Llama is gated, so accept the licence first;
  - a `llama-quantize` build at the pinned commit (`bench/build_candidate_gguf.sh`).
- **Run** the same orderings.
- **Q4_0 against Q8_0** is the first test of "does 4-bit compression cause the copying".

### Step 12: the group-letter arm on dev
- **Record** v2 and v3 prompts on the dev episodes with `run_demo.py --record-prompts`, in mock lockstep, with
  `multi.compact.group_letters` on and off. Prompts don't depend on model answers (`f6bd178`), so these are the
  prompts a board run would send.
- **Extend** the replay tool's grammar to the letter format (`with_group=True`).
- **Replay** both formats with the 4-bit file.
- **Done when** the dev result can be put beside the reporting-set result (230 of 230 prompts identical except the
  letters; line-1 rate 0.43 against 0.99).

---

## What can't be done well on this laptop

| task | why | options |
|---|---|---|
| Llama 3B at full precision (F16, about 6.4 GB) | 8 GB total memory: it will swap heavily or fail | run it on Gagan's M5, or use Q8_0 (step 11) as the precision step |
| 7–8B models | a Q4 file (about 4.5 GB) just fits but runs slowly; Q8_0 and F16 don't fit | run on Gagan's M5, or a cloud model through the existing `GeminiBackend`. The cloud route has no grammar, so its conditions differ, and **it sends the prompts to Google**. The data is synthetic, but it needs an explicit OK |

## Decisions needed before Stage 2
1. **Model file:** copy the board file from Gagan (recommended), or build it here.
2. **Bigger models:** Gagan's M5, or the cloud route.
3. **The freeze (step 4):** if it is a bug, pre-register a fix, or report it only.
4. **Thresholds (step 8):** agreed by the team before the first replay call.

---

## Later, on the board (not part of this plan)
- **Energy:** an external power meter. Energy per call, per tick and per correct diagnosis for v3, v3x and the
  no-model arms, with an idle baseline subtracted and the energy split between reading and writing.
- **Scheduling:**
  - more repeats and episodes for the sweep;
  - lane speeds re-measured with the chip cool;
  - the no-model and gated arms timed in real time;
  - optionally, the sweep with the agent on the phone.
- **Optional:** the echo replay on the board's NPU with the 4-bit file, to show the laptop result holds on the chip.
  It can share a session with the nondeterminism runs.
- **A second device,** if one is available.
