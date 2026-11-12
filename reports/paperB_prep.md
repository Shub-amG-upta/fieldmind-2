# Paper B preparation, items 5 and 8 (PLAN_PAPER_B.md) — report

## Status
PARTIAL. Two items, laptop only:
- **Item 5:** the first-look results are rebuilt as tested tools:
  - `bench/echo_test.py changed`;
  - `bench/sched_study.py hostload`;
  - `bench/sched_study.py heat`.
  Two first-look numbers changed (below).
- **Item 8:** the disagreement with *When NPUs Are Not Always Faster* is narrowed to three testable setup differences.
  The board check is not run.

Every input is a saved board run (agent on the laptop, model calls on the QIDK) or its mock twin. Plant data: boiler
synthetic, Cranfield real rig, TEP public benchmark. No energy figures. **Mock runs measure the deterministic and
retrieval layers only; they are the no-model baseline, not agent results.**

## Results

### 5a. What the model changed (`echo_test changed`; dev episodes only)
The published top cause of the board run against the mock run of the same episode, tick by tick:

| | Cranfield (`af_cf_v3_dev`, 6 episodes) | TEP (`af_tep_v3_board`, 22 episodes) |
|---|---|---|
| scored ticks where the top cause differs | **2 of 500 (0.40%)** | **17 of 2,593 (0.66%)** |
| of those, board right / no-model right (exact) | 0 / 0 | **3 / 9** (same by group) |
| top-1 right, board / no-model | 155 / 155 of 500 | 1,277 / 1,283 of 2,593 |
| NPU call time per tick | 1.35 s | 2.47 s |
| CPU-lane call time per tick | 0.04 s | 0.10 s |

### 5b. Host CPU used by each model lane (`sched_study hostload`; all saved board runs)
Server CPU seconds (board sampler, `/proc`) per second the lane spent in calls:

| lane, model | mode | runs | cores per busy second (median, range) |
|---|---|---|---|
| NPU, Llama 3.2 3B | lockstep | 254 | **1.38** (0.52–2.23) |
| NPU, Llama 3.2 3B | real time | 52 | **1.24** (0.68–1.69) |
| CPU, Llama 3.2 3B | lockstep / real time | 2 / 7 | 5.97 / 5.97 (the lane runs `-t 6`) |
| CPU, gemma 3 1B | lockstep | 50 | 5.37 |

- **The sampler's own cost:** 0.747 core (median of 347 runs; range 0.09–0.82).
- **Five records were skipped:** each sampler covered less time than its lane spent in calls (for example
  `tep_v3_board/tep_board_F04_r1`: 215 calls, 10.6 s sampled). Seventeen records whose NPU server made no calls were
  dropped by the minimum of 10 calls.

### 5c. Speed against chip temperature (`sched_study heat`; lockstep NPU runs, within each plant)

| plant | runs | coolest / hottest quarter, °C | reading, hot / cool | writing, hot / cool |
|---|---|---|---|---|
| boiler | 197 | 53.2 / 64.7 | 752 / 920 tok/s = **0.817** | 15.1 / 16.5 = **0.916** |
| Cranfield | 52 | 51.5 / 62.9 | 745 / 954 = **0.781** | 15.1 / 17.1 = **0.884** |
| TEP | 67 | 60.8 / 70.2 | 685 / 754 = **0.908** | 14.2 / 15.9 = **0.892** |

This is an association across runs, not a controlled test: hotter runs also come later in a session.

### 8. Reading speed against *When NPUs Are Not Always Faster* (Li, Qi and Chen, arXiv 2605.27435)
- **The disagreement:** the paper reports the CPU reading prompts 1.27–1.62× faster than the NPU (Llama 3.2 3B and
  others, Snapdragon 8 Gen 3, Hexagon v75, llama.cpp). Our board's NPU reads about 8× faster than its CPU lane
  (in-situ, alone: 972 against 124 tok/s, `reports/sched_fix.md`).
- **Setup differences found in their text:**

| | the paper | our board |
|---|---|---|
| llama.cpp | tag b7588 | b11371 (commit 99b95488c) |
| attention (`FLASH_ATTN_EXT`) | not supported on the NPU; falls back to the CPU (1–1.5× penalty) | has an HTP0 implementation: 722 of its cases pass `test-backend-ops` on the phone (`nd-paper`, `results/nd/m1c_phone/`) |
| batch size | 128 | default (`-b 2048 -ub 512`) |
| CPU threads | 6 | 6 |
| prompt | about 1,281 tokens | median about 750 |

- **The proposed board check:** our build with `-b 128 -ub 128` and attention off, NPU against CPU, on one prompt set.
  If NPU reading falls toward the CPU's speed, the difference is setup. Until it runs, the cause is **unexplained**.

## Verification
| step | result |
|---|---|
| ran the modules | `changed` on both board folders; `hostload` and `heat` over every saved board run; outputs above |
| self-tests | 2 new in `tests/test_echo_test.py` (21 total) and 5 new in `tests/test_sched_study.py` (21 total); with the policy and replay suites, 66 passed |
| independent re-derivation | (1) **Top-1 right**, from the evaluator's stored `T2_root_cause.top1 × n_scored` against the tool's own rule on the model run alone: Cranfield 155/500 and 155/500, TEP 1,277/2,593 and 1,277/2,593 (0% apart). (2) **NPU server cores while busy**, time-resolved: the raw sampler intervals (3,713 intervals, 52 real-time runs), with server CPU per interval regressed on the NPU lane's busy share from the spans (clock offset chosen per run by correlation, 2.5–3.5 s, a DESIGN choice of this check only). Result: 1.32 cores fully busy and −0.01 idle, against the tool's 1.24; **6% apart**. (3) **Heat**, within a run: the last third of calls against the first third, in 204 lockstep runs that warmed by 15 °C or more. Reading 0.890, writing 0.946, against the between-run 0.78–0.91 and 0.88–0.92: same direction, smaller size (different quantities; see Disagreements) |
| mutation check | `changed` 5/5 (no onset rule, the model's empty tick counted, group credit = exact, episode mismatch accepted, time over paired ticks); `hostload` and `heat` 8/8 (busy = decode only, divide by wall time, no call minimum, no sampler-coverage guard, real-time runs kept, plants pooled, short answers in decode, halves instead of quarters). All rerun with bytecode caching off: a stale `.pyc` had made one restored file test as its last mutant |

## Direction checks
| claim | expected | measured | OK/FAIL |
|---|---|---|---|
| hot runs are slower | hot / cool < 1 | reading 0.78–0.91, writing 0.88–0.92 | OK |
| an idle NPU server costs ~0 CPU | intercept ≈ 0 | −0.01 cores | OK |
| the CPU lane uses its thread count | ≈ 6 cores | 5.97 | OK |
| the model rarely changes the published cause | small share | 0.40% / 0.66% | OK (descriptive) |

## Constants introduced
| symbol | value | provenance | range | affects |
|---|---|---|---|---|
| `MIN_LANE_CALLS` | 10 | DESIGN | 5–30 | which runs enter `hostload` and `heat` |
| `MIN_DECODE_TOKENS` | 15 | DESIGN | 8–30 | which calls give `heat`'s writing speed |

## Numbers that changed
| claim | old (first look) | new (tested tool) | why |
|---|---|---|---|
| CPU cores busy while the NPU writes | about 1.9 | **1.24–1.38 cores per second of NPU call (reading and writing together), none while idle** | the 1.9 was a regression coefficient on decode time over 52 real-time runs. The same regression over 259 lockstep runs gives a negative prefill coefficient and 1.1 cores idle, both physically wrong. The fit cannot separate reading from writing, so only the combined ratio is kept |
| reading slowdown when hot | 17–21% | **9–22%** (boiler 18%, Cranfield 22%, TEP 9%) | TEP added; its cool quarter was already at 61 °C |
| writing slowdown when hot | about 10% | **8–12%** | same tool, all three plants |

Downstream: `PAPER_IDEAS_UPDATE.md` and `PLAN_PAPER_B.md` are updated to the new figures. Nothing in the agent or the
configs depends on them.

## Disagreements recorded, not resolved
1. **Reading speed against arXiv 2605.27435** (above): CPU 1.27–1.62× faster there, NPU about 8× faster here. Three
   candidate setup differences, none tested.
2. **Heat between runs against within a run:**
   - reading 0.78–0.91 between runs against 0.89 within a run;
   - writing 0.88–0.92 against 0.95.
   They are different quantities. Both are confounded: between runs with session order, within a run with prompts
   growing over an episode. The cause of the gap is not tested.
3. **Lockstep against real-time host load** (1.38 against 1.24 cores). Unexplained; small.

## Blocked / needs a decision
- **The item 8 board check** (about 30 minutes of board time) needs a board session.

## What I could not verify
- **Host CPU is credited entirely to call time.** The time-resolved check supports this (idle about 0), but it relies on
  a fitted clock offset, because the sampler's laptop start time is not saved with the results. Saving it would remove
  the fit.
- **The split of host CPU between reading and writing** is not determined.
- **Heat is an association across uncontrolled runs.** A controlled hot/cool test on one server (as in `nd-paper`
  module 2, arm A4) would settle it.
- **The changed-cause numbers** come from 6 Cranfield and 22 TEP episodes of one configuration (v3), and the board
  run's own variation (Paper A) is not separated from the model's effect.

---

# Item 2 (published fixes): built, laptop smoke test (2026-11-12)

## Status
PARTIAL: the code for every arm in `reports/paperB_item2_prereg.md` (DRAFT) is built and tested
(`fieldmind/multi/debias.py`, diagnostician wiring, llama-server token probabilities, overlays
`configs/debias_*.yaml`). No board run. The smoke test below used the **laptop's** model file and is **plumbing only,
not a result**.

## Laptop smoke test (laptop llama-server, Metal, Llama 3.2 3B Q4_0 laptop rebuild `dace5753…`, not the board file)
`dev_A01_fcv_seize`, cut at fault onset + 25 ticks (35 ticks, 5 diagnosis answers), v3, lockstep:

| arm | model calls | wall s | what it did |
|---|---|---|---|
| none | 5 | 14.7 | – |
| no example | 5 | 13.8 | `Example:` in 0 of 5 prompts (5 of 5 in none); same published causes |
| calibrate | 7 | 18.2 | first-line probabilities found in 4 of 4 replies; 2 probes (one per prompt shape); rank-1 moved off line 1 on 4 of 4 |
| PriDe | 16 | 56.2 | readings found; no prior yet (5 estimating calls per shape needed, 4 happened); nothing moved |
| PSC | 13 | 62.5 | 3 of 3 orderings valid on each of 4 answers; changed 1 of 4 |

- **What calibrate read** (two answers, n = 4 lines): the content-free prompt puts 0.88 on line 1 (log −0.125). The real
  prompts put 0.61 and 0.54. Line 1 therefore loses after calibration.
- **One move went to line 4** (read 3%, prior 0.8%). This is the known behaviour of contextual calibration: it lifts
  unlikely options whose prior is lower still. Recorded, not changed.
- **Two code fixes came from this checking:**
  - ties keep the model's own rank-1 (`TIE_NATS`), so floating-point noise can no longer move an answer;
  - an unreadable calibration probe is retried at most `CAL_PROBE_ATTEMPTS` = 3 times per prompt shape. Before the
    fix, a mock run probed on every call (76 extra calls in 92 answers).

## Verification (item 2)
| step | result |
|---|---|
| ran it | mock: two arms through `scripts/benchmark.sh` (PSC: 17 answers × 3 calls, 59 × 2 on 2-case sides, 16 skipped with < 2 cases; calibrate: `no_probs` on all 76). Laptop model: the table above |
| self-tests | `tests/test_debias.py` 18 passed |
| independent re-derivation | (1) PSC on the mock, a position-invariant ranker, publishes exactly the base run's causes on every tick: the reorder → answer → map-back path loses nothing. (2) The laptop model's first-line probabilities from llama-server agree with its own answers: the read argmax was the line it wrote first on the 2 answers the smoke test logged in full (the other 2 were not kept, so not checked) |
| mutation check | 16 of 16 caught (`debias.py` 11, diagnostician 5, probe cap 1; one mutation matched no code and is not counted). Four survived at first (Borda counted mentions only, prefix unchecked, PriDe used one ordering, probabilities never requested); tests were added until each failed |

---

# Item 1 pilot (FaultExplainer, laptop, registered pilot)
- 2 requests, `app` form, `original` ordering, the laptop rebuild. Labelled `pilot`; **not scored**.
- **Parse fidelity:** in both replies the parser's picks are the model's own numbered selections ("1. IDV(13) … 2.
  IDV(14) … 3. …"). The stop rule is not hit.
- **Size and time:**
  - prompts are 2,475 tokens;
  - answers are 1,061 tokens and **1,400 (stopped at the cap)**;
  - each call takes about 68 s on the laptop.
- One of 2 answers reaching the cap means the board arm will cut some answers; their picks come early, so parsing is
  unaffected in this pilot.
