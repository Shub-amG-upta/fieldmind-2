# Handoff: held-out Cranfield and TEP sets for the reading test (for a new Claude session on Shubham's laptop)

Written 2026-11-14. Work in the worktree `.worktrees/fe-baseline` (branch `fe-baseline`), or a new branch from it.
Run Python as `env -u PYTHONPATH .venv/bin/python` (the worktree's `.venv` links to the main checkout's).

## Goal
The reading test (`reports/reading_test_prereg.md`, tool `bench/reading_test.py`) ran on 400 held-out **boiler**
prompts (set H). Interim result: the Llama 3B's hidden signal comes from the evidence (8-bit, by the agreed rule).
The boiler is synthetic. **Build fresh, held-out Cranfield (real rig) and TEP (public) request sets** so the same test
can run on them, plus a dated amendment to the rule file. **Build only: no model call, no scoring.**

## What is known (checked 2026-11-14)
- `reports/data/echo_requests.json` (set R) already used **all 6 Cranfield dev episodes**
  (`data/episodes_cranfield_dev`: cf_F1 … cf_F6) and **21 of the 22 TEP dev episodes** (`tep_board_F01_r1` …
  `F20_r1`, `N_r1`). Set R has been looked at, so it cannot be the held-out set.
- `data/episodes_cranfield` (10) and `data/episodes_tep` (110) exist in the main checkout. Which of them are dev
  and which are **reporting** episodes is not checked: read `bench/echo_test.py` (`DEV_DIRS`, `dev_ids`) and
  `CLAUDE.md` ("Dev set rule": reporting episodes are run once to report, never to decide).
- Set H was built with `bench/echo_4bit.py build` (`held_out` refuses any episode or prompt already in set R) from saved
  **board runs** that hold diagnostician prompts and replies. `bench/echo_test.select` also refuses a request whose saved
  reply its grammar would not accept.
- Diagnostician prompts are built by the agent's code before any model call, so a **mock-backend run** can produce
  them without a model. Whether mock replies pass `select`'s grammar check is **not checked**; if not, the builder may
  need a prompts-only path (keep `select`'s other rules).

## Steps
1. **Find usable episodes.** List Cranfield and TEP episodes that are dev (per `DEV_DIRS`) and not in set R. Report the
   counts before building anything.
2. **Stop and ask Shubham if either plant has none.** Cranfield likely has none (all 6 dev episodes are in set R).
   The options to put to him, without choosing one:
   - generate new dev episodes (TEP has a simulator path in `data/`; Cranfield is real data and may have no more runs);
   - use reporting episodes once, as a report-only confirmation (a rule decision: CLAUDE.md treats this strictly);
   - use set R's Cranfield prompts for the new forms only, labelled "not held out".
3. **Record prompts** for the usable episodes: run the agent on them with the mock backend so every diagnostician prompt
   is saved (find the harness flag used for earlier `--record-prompts` logs, or save run files as the board runs do).
4. **Build the request sets** with `echo_4bit.held_out` (excluding set R and set H), scored requests only, seed
   20261114: `reports/data/reading_requests_cranfield.json`, `reading_requests_tep.json`. Report requests and episodes
   per plant, and how often line 1 is in the true group (code only, no model).
5. **Tests**: extend `tests/test_reading_test.py` (or the builder's tests) so a set that shares an episode or prompt with
   set R or set H is refused, and both new files load in `reading_test.py`. Run them; mutation-check one rule.
6. **Amendment A1** in `reports/reading_test_prereg.md`, marked PROPOSED: the two sets, the same forms, arms, rules and
   thresholds, per plant, never pooled with the boiler. State the retrieval ceiling per plant as a stated limit.
7. **Mac handoff**: add the two sets to `HANDOFF_READING_TEST.md` (same script, `REQ=` the new files; labels unchanged,
   output files suffixed `_cranfield` / `_tep`; the run script takes `REQ` and `OUT` from the environment or needs a
   small change to do so).
8. Build report `reports/reading_cranfield_tep_build.md` in the CLAUDE.md format. Commit; do not push.

## Rules
- No model call. No score of any model output. No look at set R or set H model rows.
- Reporting episodes are never used to design anything.
- Stop and ask on any decision that changes what the benchmark measures (CLAUDE.md stop rule 4).
