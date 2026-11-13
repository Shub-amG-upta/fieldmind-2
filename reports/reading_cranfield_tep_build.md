# Reading test on TEP and Cranfield: request sets — build report

## Status
DONE (build only), following `HANDOFF_READING_CRANFIELD_TEP.md`. **No model call, no score of any model output, and no
set R or set H model row read.** Two request files, a PROPOSED amendment, Mac run steps.

| piece | file |
|---|---|
| TEP set, held out | `reports/data/reading_requests_tep.json`: 400 scored requests, 18 episodes of the new dev run 13 (sha256 `9737fa434b0a7a593f899e451e0af07de3d2a6d39ad54b308777da63b3c46ef7`) |
| Cranfield set, **not held out** | `reports/data/reading_requests_cranfield.json`: set R's 141 scored Cranfield requests, 6 episodes (sha256 `9f8feea769fce65d84aefae039f7637baf4caf85622c0a61c7ab76ff53e04fcb`) |
| new TEP dev run | `data/tep/convert.py --new-dev` writes `data/episodes_tep_dev_r13` (20 episodes, gitignored), registered in `bench/echo_test.DEV_DIRS` and `bench/stage_monitor_multi.OTHER_EPISODE_DIRS` |
| builder | `bench/echo_4bit.py build --mock-prompts --max-per-plant`, `not-held-out`; `bench/echo_test.select(mock_prompts=True)` |
| rules | `reports/reading_test_prereg.md`, Amendment A1 (PROPOSED) |
| Mac steps | `HANDOFF_READING_TEST.md` §5; `bench/reading_test_runs.sh` takes `REQ` and `SUFFIX` |
| tests | `tests/test_reading_test.py` (+13) |

## Decisions taken (all by the human, asked before acting)
| question | options put | chosen |
|---|---|---|
| TEP has no unused dev data (the 22 `tep_dev` runs are the same simulations as set R's `tep_board` episodes: all 320 rows of F01 identical) | new dev runs / tep_dev tails labelled / reporting runs once / set R not held out | **new dev runs** |
| Cranfield has no unused dev data (16 fault sets: 6 dev, all in set R; 10 reporting) | set R not held out / reporting sets once / skip | **set R, not held out** |
| fault run 7 equals the **reporting** fault-free run 7 for its first 8 h (checked: first differing sample 160 = the onset) | run 13 (its fault-free twin is in no split) / run 7 with the overlap recorded | **run 13** |
| TEP pool: 3,649 scored requests | 400 / all / 150 | **400** |
| sampling | uniform over requests (as set R and set H) / equal per episode | **uniform** |

**Not asked (taken as the option that changes least, recorded here):**
- **The episode length is the board length (16 h).** That is the form set R's TEP requests came from, and it keeps
  the TEP prompts comparable.
- **The ground truth's `split` field reads "dev"** (set R's board episodes read "board"). No agent or scoring code
  reads it.

## Verification
| step | result |
|---|---|
| ran the module | **Converter:** `python -m data.tep.convert --new-dev`: "checks: PASS", 20 episodes. **Mock prompts:** `bench/benchmark.py rcf_tep_r13_prompts <20 episodes> --backend mock --overlay configs/v3.yaml,configs/tep.yaml --merge-rule hybrid` (set R's TEP settings, from `results/benchmarks/af_tep_v3_board/test.json`): 20 runs, 0 unusable. **Builder:** 3,653 candidates, 2 refused, 4 unscored, 3,649 scored → 400 drawn; Cranfield 141 |
| self-tests | `tests/test_reading_test.py` 20 passed (7 before). With the echo, benchmark, stage-monitor, paperB, TEP and FaultExplainer suites: **141 passed, 1 skipped**. This needed the main checkout's gitignored episode folders linked into the worktree; without them, 4 tests that need `data/episodes*` fail for that reason alone |
| independent re-derivation | (1) **Prompts from a mock run equal the board's.** Mock replay of set R's `tep_board_F01_r1` against the board run `af_tep_v3_board` (prompts only): 352 of 352 diagnostician prompts identical at 194 of 194 ticks, and all 11 set R requests from that episode found byte for byte. The model-call count is also the same, 357 and 357. The verifier differs at 1 of 5 ticks, its documented exception. (2) **TEP line-1 credit.** From the episodes' `ground_truth.json`, the raw `data/kb_tep/case_groups.json` and an own regex, without `_right`, `_target` or `_groups`: 194 of 400, against the tool's 194 (difference 0). (3) **Episode data.** `tep_board_F01_r13` equals `read_block(Faulty_Testing, run 13, fault 1)` on all 320 rows, and first differs from fault-free run 13 at sample 160, the onset |
| mutation check | 3 of 3 caught: the `"g"` removal for letterless prompts disabled (`test_mock_prompts_accepts_the_mocks_spaced_reply…`); the fault-free twin runs dropped from the split check (`test_new_dev_runs_refuse_any_run_in_the_split_or_twinned_with_one[7]` and `[12]`); the prompt check dropped from `held_out` (`test_held_out_refuses_a_set_sharing_an_episode_or_a_prompt_with_an_earlier_set`) |

**Set H's counts reproduce its pre-registration** (196 of 400 line 1 right, both outcomes in 7 episodes), which
checks the counting code.

## Direction checks
| claim | expected | measured | |
|---|---|---|---|
| a fault run equals its fault-free twin until the onset | first difference at sample 160 | 160 (runs 7 and 13) | OK |
| a held-out set shares nothing with set R or set H | 0 shared episodes, 0 shared prompts | 0 and 0 (test) | OK |
| removing the belief and example lines leaves every prompt distinct | 400 and 141 distinct | 400 and 141 | OK |

## Constants introduced
| symbol | value | provenance | range | affects |
|---|---|---|---|---|
| `NEW_DEV_RUNS` | (13,) | human decision 2026-11-14 | any run in 13–500 whose fault-free twin is unused | which TEP simulations make the held-out set |
| TEP set size | 400 | human decision 2026-11-14 (as set H) | 150–3,649 | interval width, Mac time |
| sample seed | 20261114 | DESIGN (the date, as the handoff says) | – | which 400 |

## Numbers that changed
None. No agent code, config, threshold, case library or existing episode was changed.
- `select` and `held_out` behave as before unless the new options are passed. Set H's numbers reproduce.
- `reading_test_runs.sh` with no `REQ` runs set H exactly as before.

## Disagreements recorded, not resolved
1. **The handoff assumed TEP had unused dev episodes; it had none in substance.** `tep_dev` run 1 and set R's
   `tep_board` run 1 are the same simulation (`data/tep/convert.py` cuts one from the other). Resolved by the human's
   choice of a new run, not by reinterpreting "held out".
2. **The existing pre-registered TEP split already has a twin overlap:** reporting fault run 2 equals dev fault-free
   run 2 before the onset (and runs 3–6 likewise with reporting fault-free runs). That is outside this build;
   recorded, not changed.
3. **The mock's replies are not in grammar form**: spaces, a `"g"` key on letterless prompts, and once each in F12 and
   F19, fact lines in descending order. The builder reads them in the form a grammar-constrained server would write.
   Two replies the grammar still rejects (the descending fact lists) were refused, not repaired.

## Blocked / needs a decision
1. **Agree Amendment A1** in `reports/reading_test_prereg.md` before any call on either set.
2. **`data/episodes_tep_dev_r7/`** (20 episodes of the superseded run 7, gitignored at first, now untracked) is still
   on disk. My `rm -rf` was blocked. Delete it by hand: `rm -rf data/episodes_tep_dev_r7`. It is not in `DEV_DIRS`, so no
   tool reads it.

## What I could not verify
- **That run 13's own prompts match what the board would send.** The identity is shown on one set R episode
  (F01, run 1) and argued from the prompt-identity tests. No board run of run 13 exists, and making one would be a
  model call.
- **The Mac run time** (TEP 10–12 h, Cranfield 3 h). It is scaled from set H's night by call counts, not timed.
- **That the full Mac command works end to end.** Without a model, the guards were run (another `REQ` without
  `SUFFIX` is refused, and a missing file is logged as FAILED), and the Python path was run with fake models in
  `test_the_whole_run_and_score_path_works_on_both_new_sets`. The `llama-server` part was not run.
- **The worktree links** (`data/episodes*`, `data/reference/tep/*.RData` → the main checkout) are local only and
  excluded from git. On another machine, `python -m data.tep.convert --new-dev` regenerates run 13 from the
  sha256-checked raw files.
