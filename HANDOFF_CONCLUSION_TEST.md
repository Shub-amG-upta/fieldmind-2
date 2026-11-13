# Handoff: the "description vs conclusion" test (for a new Claude session on Shubham's laptop)

Written 2026-11-14. Work in `.worktrees/fe-baseline` (branch `fe-baseline`) or a new branch `conclusion-test` from it.
Python: `env -u PYTHONPATH .venv/bin/python`. Read `CLAUDE.md` first; its rules apply (no invented numbers, pre-register
before results, run / test / re-derive / mutation-check, report in the CLAUDE.md format).

**Build only. No model call on new data, no score, no push.** The run waits for (a) tonight's TEP result and (b) Shubham's
"agreed" on the pre-registration you write.

## Why
Post hoc on set H (`reports/reading_test_prereg.md`, Amendment A3): the Llama 3B's one-word check (p(yes) for line 1)
separates right from wrong almost perfectly on prompts whose facts **state a conclusion** (BALANCE / VALIDITY, e.g. "water is
being lost between the feed meter and the drum": AUC 1.00, code 0.39) and **worse than chance** on prompts with only
**trend descriptions** (RATE, e.g. "bed temp −2.1 °C/min sustained 30 min": AUC 0.11–0.21, code 0.88). Fact type and fault
episode are mixed together in set H, so it is unproven. Prior work to build on, not to claim against: ExpliCa (ACL 2025
Findings), "Decodable but Not Faithful" (ICML 2026), SensorLLM (arXiv 2410.10624), S2S-FDD, TSQueryBench (arXiv
2604.02118).

**The test:** the same prompts, with each RATE fact shown either as now (description) or as a code-written statement of
what it means (conclusion). Everything else identical. Does the model's signal rise with the conclusion form?

## Pieces to build
1. **Rewrite rules** (`fieldmind/` is stdlib-only and must not change; put this in `bench/conclusion_rules.py`):
   - for each boiler tag and direction that a RATE fact can carry (bed_temp_avg, drum_pressure, ms_temperature,
     steam_flow, feed_water_flow, drum_level; UP / DOWN), one short sentence stating **what the trend means physically,
     listing every plausible cause**;
   - every sentence CITED to `docs/Boiler_Failure_Case_Studies_RCA.pdf` (section) or `data/kb/asset_model`;
   - **never a case id, never a single cause when the PDF or the asset model gives several**. Fair: "bed losing heat:
     consistent with water entering the furnace, wet coal, or reduced fuel". Not fair: "bed falling: tube leak";
   - use the CLAUDE.md sign list (tube leak → bed cools; load up → swell; …) as a check on every direction.
2. **New boiler episodes**: fresh dev episodes from `dev_catalogue()` in `data/generator/episode_build.py` with new seeds,
   covering families A–E, written to a new folder (never `data/episodes`, the reporting set). Record diagnostician prompts
   with a mock-backend run at set H's settings (`configs/v3.yaml`, multi, lockstep), the way
   `reports/reading_cranfield_tep_build.md` did for TEP. Build a request set with `bench/echo_4bit.py` `held_out`
   (refuse anything in set R or set H), scored requests only, seed 20261115:
   `reports/data/conclusion_requests_boiler.json`. Report requests, episodes, families, and how many prompts hold RATE
   facts.
3. **Tool**: a new form `conclusion` in `bench/reading_test.py` for the `per_case` test (one-word check of every case
   line, as now), where each RATE fact line is replaced by its rule sentence; the original `per_case` form is the
   comparison. Tests:
   - only RATE lines change; every other byte is identical;
   - no rewritten line contains a case id (`RCA-…`) or the word of any single case's title;
   - a fake model that reads only conclusion sentences scores higher on the `conclusion` form (the scorer works);
   - mutation-check at least 3 rules (one must be "a case id leaks").
4. **Pre-registration** `reports/conclusion_test_prereg.md`, marked DRAFT:
   - arms `m1_q4_0`, `m2_q8_0` (the same files as the reading test);
   - primary measure: AUC of p(yes) for line 1, `conclusion` minus `per_case`, on prompts that hold at least one RATE
     fact, paired, 2,000 episode resamples, seed 20261111;
   - **"conclusion form raises the signal"**: difference ≥ +0.10 with interval excluding 0; **"no effect"**: whole interval
     inside ±0.05; else undetermined. Per arm; confirmed if both;
   - also reported: the same on prompts without RATE facts (should not move), the code's belief AUC, top-pick accuracy;
   - expectations stated before running, what has been seen, limits;
   - an empty "Agreed" section. **Never fill it yourself.**
5. **Mac handoff** section added to `HANDOFF_READING_TEST.md`: the run command (one-word checks only, both forms, two 3B
   arms, about 1 h).
6. **Build report** `reports/conclusion_test_build.md` (CLAUDE.md format). Commit each piece separately. **Do not push.**

## When a question comes up: decide it yourself, with these defaults
Record every decision under "Decisions taken" in the build report, with the reason.

| question | choose |
|---|---|
| a tag/direction has no source in the PDF or asset model | leave that tag's RATE facts unchanged (description in both forms) and list it under "Blocked / needs a decision" |
| the PDF lists one cause but physics allows others | state all physically plausible causes, cite each; if a cause has no source, leave it out |
| which families / how many episodes | all of A–E, the same count per family as `dev_catalogue()`, one new seed each |
| mock replies fail `select`'s grammar check | add a prompts-only path that keeps every other rule of `select`; test it |
| too few RATE-holding prompts (< 100) | build anyway, report the count, and flag it in the pre-registration's limits |
| a threshold or range needs choosing | the conservative one: the larger margin, the stricter rule |
| anything that would touch `configs/base.yaml`, the reporting episodes, the agent's code in `fieldmind/`, or existing results | do not do it; write the question under "Blocked / needs a decision" and carry on with the rest |
| marking a pre-registration agreed, pushing, deleting files | never; these are Shubham's |

## Done when
`reports/data/conclusion_requests_boiler.json`, `bench/conclusion_rules.py`, the `conclusion` form, its tests (passing,
mutations caught), `reports/conclusion_test_prereg.md` (DRAFT), the Mac section, and the build report are committed.
