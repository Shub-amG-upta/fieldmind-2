# Resume brief: FieldMind multi-agent build

*Written 5 October 2026 from the team handoff of 3 October (about 23:15 IST). This file is for Claude Code. The person running you is continuing this build on a different laptop.*

**The repo is the source of truth, not this file.** Everything below describes the state on 3 October. Work may have continued after that. Where the repo disagrees with this file, trust the repo and say what differs.

---

## Part 1: Check the machine and the state (do this first, change nothing)

Run these and report the results before doing anything else. Do not edit, commit or fix anything in Part 1.

1. `git status` and `git branch --show-current`. The branch must be `multi-agent` and the tree clean.
2. `git log --oneline -15` and `git tag --list`. Confirm the tag `multi-phase1` exists and find which Phase 2 commits are present (see Part 4).
3. Read `CLAUDE.md`, `reports/multi_phase2_prompt_shrink.md` and `reports/multi_phase2_progress.md`. The progress file says exactly which step was last finished.
4. Confirm a virtual environment exists at `.venv` and run `.venv/bin/python -m pytest`. At Phase 2 commit 3 the count was 197 passing. A later commit will have more. Fewer than 197, or any failure, is a stop.
5. Check the episodes exist: `data/episodes` (30 reporting episodes) and `data/episodes_dev` (36 dev episodes). They are not in git. If they are missing, find the generator command in `CLAUDE.md` or the README, regenerate them, and verify them against any committed checksum manifest. The generator is meant to give byte-identical files on every machine.
6. Check `data/experience/store.json` is empty. If it is not, stop and report; a non-empty store changes the prompts.
7. Fetch the tokenizer files if they are missing: `.venv/bin/python bench/token_count.py --fetch`. A committed manifest checks their sha256.
8. Re-run the Phase 1 identity check with the mock backend: single and multi architectures must give 0 differing decisions on the dev set, and the summary must match `results/baselines/multi_p1_summary.json`. The flags are `run_demo.py --all --backend mock --arch single` and `--arch multi --mode lockstep`; check `CLAUDE.md` for the exact form.

**Stop and report if** any of these is true: the branch is wrong, tests fail, the identity check shows any difference, the episodes do not verify, or there are uncommitted changes you did not make.

Report format for Part 1: one table with a row per check (result, and the evidence), then one line saying which Phase 2 commit is the next to build.

---

## Part 2: The project in brief

- FieldMind watches one industrial boiler from 6 sensor tags, every 30-second tick, on a phone-class chip with no internet. It names the likely cause of a fault and suggests what to check. It only advises.
- Tags: `drum_level`, `feed_water_flow`, `steam_flow`, `drum_pressure`, `bed_temp_avg`, `ms_temperature`.
- Data is simulated: 30 reporting episodes and 36 dev episodes. 13 failure cases are in the case library and 5 are held out.
- The single agent in `fieldmind/agent/` is the working baseline: checks produce facts, then triage, retrieval, belief, a diagnostician model call, a verifier model call, a gate and memory.
- The multi-agent system in `fieldmind/multi/` splits that work into small agents that share a blackboard, so model calls can be short and can run on the NPU and CPU at the same time. The design is `docs/multi_agent_plan.pdf`.
- Real models run only on the QIDK board, attached to a different laptop. **This machine has no board. All work here uses the mock backend.** Mock results prove prompt sizes, parsing and unchanged decisions. They say nothing about model accuracy.

---

## Part 3: Rules (these do not bend)

1. One change per commit, measured after each, so every number that moves has one cause.
2. Write the keep-or-revert rule and any predicted counts **before** running the measurement, and commit them first.
3. Decide on the dev set only. The 30 reporting episodes are run once per phase, to report.
4. A human overruling a rule is recorded as a HUMAN DECISION with its reason. You never waive a rule yourself.
5. Every number that moves has a stated cause, or is marked "unexplained".
6. Do not change case data, thresholds or band edges to improve a number.
7. Every new test gets a mutation check, run with `PYTHONDONTWRITEBYTECODE=1`.
8. **Do not edit `fieldmind/agent/` or `bench/model_choice.py` on this branch.** A board campaign on `main` depends on them. If something there blocks you, stop and report it.
9. Always use `.venv/bin/python`. Never `git push`; the person pushes.
10. If a measured count differs from a prediction you committed, stop. Do not adjust the prediction.

---

## Part 4: Where the build stood on 3 October

| Phase | State |
|---|---|
| 0. Fix the single agent | Done on `main`. Baseline `results/baselines/single_v3_summary.json`, tag `single-agent-v3`. |
| 1. Plumbing | Done, tag `multi-phase1`. Multi-agent gave 0 differing decisions against the single agent on 5,850 dev ticks and 5,160 reporting ticks, with byte-identical prompts. Report: `reports/multi_phase1_plumbing.md`. |
| 2. Prompt shrink | **In progress: commits 0 to 3 of 8 were in.** |
| 3. Split by plant side | Not started. |
| 4. Real time on the board | Not started. |
| 5. Scheduling study | Not started. |

Phase 2 commits that existed:

| Commit | Hash | What it holds |
|---|---|---|
| 0 | `595180b` | The decisions and the gate G1 to G6, written before any measurement. |
| 1 | `c7ddcc0` | `bench/time_single_hard.py`, timing for the single agent's code path. |
| 2 | `a36e4a8` | Fixed placement in the scheduler, now the default: diagnostician on the NPU lane, verifier and text reader on the CPU lane. |
| 3 | `0d3254f` | `bench/token_count.py`, counting tokens with the real tokenizers of all 4 candidate models. Phase 1 prompts average about 1,870 to 1,890 tokens, up to 2,150; 1,980 of 1,982 are over the 1,280 limit. |

Phase 2 commits still to build, as of that date:

| Commit | What it should hold |
|---|---|
| 4 | The text reader agent: one engineer note in, one checked note-fact out. |
| 5 | The shrunk diagnostician prompt, with a separate on/off switch for each shrunk section, so a later accuracy loss can be traced to one section. |
| 6 | The shrunk verifier prompt. |
| 7 | The dev gate G1 to G6, then one reporting run, then the report. |

It is not known whether any of commits 4 to 7 were built after 3 October. Part 1 step 2 and step 3 answer that.

---

## Part 5: Phase 2 decisions already taken

These were given as HUMAN DECISIONS. Confirm each is written in `reports/multi_phase2_prompt_shrink.md`. If one is missing there, report it; do not re-decide it.

- **Token limit.** Prompt tokens plus that agent's answer limit must be under 1,280 on all four tokenizers. Answer limits: diagnostician 60, verifier 30, text reader 50.
- **Answer format: line numbers.** The planned ID-only answer measured 89 to 135 tokens and did not fit in 60. The model answers with the line numbers of the cases, facts and notes shown in the prompt, with no confidence numbers (worst case 49 tokens). Code maps line numbers back to real IDs using a map saved when the prompt was built.
- **At most 9 fact lines** per diagnosis prompt, most severe first. Dropped facts are logged.
- **Verifier** answers pass or fail for every case shown. A case with no verdict counts as "not judged", never as a pass.
- **The verifier loses three things** (a design change): the check that a distinguishing sign is observable, the rewrite of the top confidence, and claims beyond rank 3.
- **Faithfulness is measured as Q3_rel.** A citation counts only if that fact really supports that case according to the plain-code layer. The Phase 2 gate uses Q3_rel.
- **Confidence** for a case outside belief's top 3 comes from belief, capped at 0.5 (0.3 if belief has no entry). Predicted effect on dev: verifier calls go from 192 to 327.
- **Plant records become facts by code**, with no model call. The text reader handles engineer notes only.
- **Gate G1 is split.** G1a changes only the answer format and allows differences only in confidence-related fields, with counts predicted in advance. G1b turns on all the prompt shrinking and must show 0 differences against G1a.
- **Allowed accuracy drop, for the later real-model test on dev:** group top-1 by at most 0.05, faithfulness by at most 0.02, and group top-1 must stay above the plain-code floor of 0.501. This cannot be checked on this machine.

The full gate G1 to G6 is defined in commit `595180b` and the Phase 2 report. Read it there. Do not redefine it.

---

## Part 6: What to do next

After Part 1 passes, continue with the **next unfinished Phase 2 commit**, one at a time.

For each commit:

1. Start in plan mode. State what the commit will contain, the tests and mutation checks, any counts you predict, and what must stay unchanged. Wait for approval.
2. If the step has predicted counts or a keep-or-revert rule, commit those first, before measuring.
3. Build it. Run the full test suite.
4. Measure on the dev set with the mock backend. Compare against the previous commit.
5. Update `reports/multi_phase2_progress.md` and the Phase 2 report.
6. Commit with the Phase 2 commit number in the message. **Stop and report.** Do not start the next commit until told to.

Notes for the remaining commits:

- **Commit 4, text reader.** One note in, one note-fact out: tags, equipment, the claim, time, reliability, and a link to the raw note. Diagnosis prompts get note-facts, never raw note text. A note that contains an instruction must produce a note-fact that carries no instruction; test this with the injection episodes. On the mock, note-facts come from code-built hints, so text-reader quality stays unmeasured; say so in the report.
- **Commit 5, diagnostician prompt.** Each shrunk section has its own switch. With every switch off, prompts must be byte-identical to the previous commit. Report prompt tokens (max and p95) per tokenizer.
- **Commit 6, verifier prompt.** Same approach. Keep the verifier's narrow view: claims and facts only, no cases text beyond what the decisions above allow, no notes.
- **Commit 7, the gate.** Run G1a, then G1b, then the rest of G1 to G6 on dev. Only if the dev gate passes, run the 30 reporting episodes once, then write the report. If any gate fails, stop and report; do not adjust the gate.

One open question to look into along the way, **look only, do not fix**: why 1,154 of 3,170 retrieved cases have no belief entry. If the cause is in `fieldmind/agent/`, record it for `main`.

When all of Phase 2's mock work is committed and the dev gate passes, stop. Do **not** start Phase 3. The real-model test of Phase 2 needs the board and the real-model baseline from the campaign on `main`, and it needs `main` merged into this branch first (a conflict in `run_demo.py` is expected). That merge is the person's call.

---

## Part 7: What you must not do on this machine

- No real-model runs, no `adb`, no `/board-up`. There is no board here.
- Do not merge `main`, rebase, or touch tags unless asked.
- Do not edit anything under `results/board/` or `results/board_aborted_20261003/`.
- Do not commit episodes, model files, tokenizer files, or anything under `npu/maven/`.
- Do not report mock numbers as model accuracy, or laptop timings as board timings.

---

## Part 8: How to report at each stop

Keep it short and checkable:

1. What was built, in one or two lines, with the commit hash.
2. Test count before and after, and the mutation checks with their outcomes.
3. The measurement table against the previous commit, on dev.
4. Every number that moved, with its cause, or "unexplained".
5. Anything that differs from this brief or from a committed prediction.
6. Decisions you need from the person, each as a question with options.

The person pastes your plans and reports into a separate Claude chat for checking before telling you to continue. Make them easy to check: exact numbers, file paths, and commit hashes.
