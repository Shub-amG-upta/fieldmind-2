# Breadth B1, Step 1 — asset-pack refactor — report

## Status
DONE — the boiler is now one asset pack
(`fieldmind/assets/boiler.py`); every other module reads the pack. Boiler behaviour is
byte-identical. Branch `breadth-cranfield` from `bev-ideas` bebed22. Plan:
`~/.claude/plans/refactored-sauteeing-seahorse.md` (approved 2026-11-05).

## Human decisions (2026-11-05)
- Breadth benchmark = Cranfield three-phase flow facility, 2015 dataset first, PRONTO second.
- Cranfield fault signatures DERIVED from rig physics and the published fault descriptions,
  committed before any fault dataset is run (no fitting on fault data).

## What moved
| was (boiler hard-wired) | now |
|---|---|
| `l1_checks._balances`, `_patterns` | `assets/boiler.balances`, `.patterns` (bodies unchanged, `self` → `layer`); `CheckLayer(cfg, asset)` delegates |
| `l1_symbolize.build_signature` balance pseudo-triples | `assets/boiler.balance_triples`; `build_signature(..., asset)` |
| `world_model._fact_ids` water/energy selector | `assets/boiler.balance_fact_sel`; `update_hypotheses(..., asset=)` |
| `l2_triage._trip_predicted` drum level 10 % / bed 940 °C | `AssetPack.trip_lines` (same arithmetic, same order) |
| `multi/sides.py` module constants | `Sides(spec)` class; `assets/boiler.SIDES` spec; module-level names are the boiler's instance (back-compatible) |
| `diagnostician.SIDE_NOTE`, `schemas.TAGS` in agents | `asset.sides.side_note`, `asset.tags` |
| `TAGS` in trust refresh, 10-min slopes, baselines, world summary | the window's / world model's tags |
| prompt templates | `compact.load_prompt(name, asset.prompt_dir)`: an asset folder overrides, else the default |
| `headline` quiet line | `AssetPack.quiet_headline` |

`load_asset(cfg)` reads the top-level key `asset` (default `boiler`). The harness builds the
check layer, window and world model from it; the multi-agent orchestrator takes it from the
check layer and hands it to the sensor, triage, retriever, diagnostician, verifier and gate.

## Verification
| step | result |
|---|---|
| ran the module | mock, all 36 dev episodes, three configurations (single; multi; multi + `configs/v3.yaml`), prompts logged |
| identity vs pre-refactor | `bench/compare_runs.py`: **0 differences** in all three (5,850 assessments each; 2,174 / 2,174 / 1,118 envelopes incl. every prompt). Reference first shown repeatable: a second pre-refactor v3 run vs the first, 0 differences |
| self-tests | `tests/test_assets.py` 8 passed; `bench/test_checks.py` 20/20; `bench/test_orchestrator.py` 22/22; full suite: see below |
| independent re-derivation | n/a for a pure refactor: the identity of every emitted assessment and prompt is the stronger check |
| mutation check | (1) triage passed `None` instead of the asset → `test_triage_extrapolates_to_the_asset_trip_lines` fails; (2) signature built from the boiler's triples instead of the asset's → `test_signature_uses_the_asset_pseudo_triples_not_the_boilers` fails. Both restored, 8/8 |

Full suite (`pytest`, both run at the same time on this laptop):

| code | passed | failed | errors | time |
|---|---|---|---|---|
| original, clean worktree of bebed22 | 607 | 4 | 5 | 22 min |
| this branch | 651 | 1 | 0 | 23 min |

- The original run's 4 failures and 5 errors are all board/benchmark harness tests
  (`test_benchmark`, `test_board_session`, `test_campaign`); every one PASSES on this branch.
  They come from the worktree setup (gitignored files and paths absent there), not from code;
  `test_kill_minus_9...` is the known flaky test. Not investigated further.
- This branch's 1 failure, `test_realtime::test_episode_slow_diagnosis_is_not_asked_again_while_it_runs`,
  is a wall-clock assertion (hard path 378 ms vs < 200 ms) taken while two full suites and the
  identity runs shared the CPU. Rerun alone: 3/3 passed, and `tests/test_realtime.py` 16/16.
  Load, not the refactor.

## Bug found by the new tests (fixed before commit)
`fieldmind/assets/__init__.py` first exposed the default pack as a function `boiler()`. Importing
the submodule `fieldmind.assets.boiler` (which `load_asset` does) replaces that package attribute
with the module, so every "no asset given → boiler" fallback would have raised `TypeError`. The
identity runs did not reach it (the harness always passes the asset); the unit tests did. Renamed
to `default_asset()`.

## Direction checks
None: no physics changed. (Cranfield's balance directions are stated in Step 2.)

## Constants introduced
None. `trip_lines` (10 %, 940 °C) are the existing literals, CITED to `data/kb/asset_model.json`
interlocks T-02 and T-07.

## Numbers that changed
None (identity above).

## Disagreements recorded, not resolved
1. **Tick time convention, evaluator vs harness.** The harness publishes tick *k* at the end of
   its window, (k+1)·30 s (assessment timestamps confirm: tick 9 is 06:05:00 = 300 s). The
   evaluator dates tick *k* at k·30 s (`t2_root_cause` onset filter, `t6_lead_time`,
   `t1_state_f1`). Effect: lead times read 30 s long (e.g. ep_A01 22.2 min by the evaluator,
   21.7 min from the timestamps) and onset filtering admits one tick early. Not changed: it moves
   existing boiler metrics (stop rule 5). The new Cranfield detection metrics will use (k+1)·tick.
2. The boiler's rates_long load normalisation in `l1_checks._rates` still keys on the tag name
   `bed_temp_avg`; it is inert for any asset without that tag, so it was left in place.

## Blocked / needs a decision
- Step 0 needs the 2015 file (IEEE DataPort, free account; doi 10.21227/0b7j-q780).
- Dev/report split of the Cranfield fault datasets (plan default: one dataset per fault with ≥2
  datasets is dev) needs advisor confirmation.

## What I could not verify
- Realtime mode and the bev/decider paths were covered only by the test suite, not by an identity
  run (the identity runs are lockstep with bev and decider off, as in every reported run).
- Board (llamaserver) behaviour: model calls do not depend on the refactored code except through
  the prompt text, which is identical.
