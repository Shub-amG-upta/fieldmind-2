# QIDK handoff: accuracy fixes + explain_v2 on Cranfield and TEP

For whoever runs the board (and that laptop's Claude). Branch **`accuracy-fixes`**. Everything here was
run end to end in **mock** mode on 2026-11-08; nothing has run on the board yet. Background and every
number: `reports/accuracy_fixes.md`.

This is a **separate track from `HANDOFF_LAYA.md`** (branch `laya`). Do not mix the branches in one run:
run the Laya handoff from `laya`, this one from `accuracy-fixes`.

## What changed, in four lines
- **Cranfield, TEP:** an alarm is published only after it holds for 3 ticks (false alarms about −50 %).
- **TEP:** two new patterns (a sensor moved from its first-hour level; a sensor's swing widened) and a
  re-fitted case library; case lines show at most 8 signature triples (long lines were cutting the true case).
- **bev explain arm ("explain_v2"):** the rank-only prompt loses its example `{"r":[2,1]}` (Llama copied it on
  85 % of Cranfield answers that had a choice); no Llama call for a side showing no case; a side showing one
  case gets the answer `{"r":[1]}` from code (the board's Llama gave exactly that on 1,427 of 1,436 such calls).
- **Boiler:** agent behaviour unchanged (only the bev arm's prompt and skips, if run).

## What the run must answer
1. Does Llama still follow line 1 with the new TEP library? (v3 arm)
2. Does explain_v2 stop the copying and win back the accuracy bev v1 lost (Cranfield 0.417 → 0.364,
   TEP 0.380 → 0.261), while keeping its speed-up? Rule written before the run: explain_v2 is kept if, on
   Cranfield dev AND the TEP board subset, its board accuracy is at least the v3 arm's − 0.02 and its Llama
   decode tokens are below the v3 arm's.
3. Where Llama leaves line 1 (TEP close calls): is it right?

## 1. Get the code
```bash
cd ~/field-mind
git fetch https://github.com/Shub-amG-upta/fieldmind-2 accuracy-fixes
git switch -c accuracy-fixes FETCH_HEAD        # or: git switch accuracy-fixes && git merge --ff-only FETCH_HEAD
env -u PYTHONPATH .venv/bin/python -m pytest tests/test_explain_v2.py tests/test_board_insights.py \
    tests/test_state_persistence.py tests/test_tep_shift_spread.py tests/test_tep_pack.py tests/test_cranfield_pack.py -q
```
All must pass. Episodes: the ones you already have (`data/episodes_cranfield_dev`, `data/episodes_cranfield`,
`data/episodes_tep_board`; `HANDOFF_QIDK_BREADTH.md` made them). Nothing to regenerate: the fixes are code and config.

## 2. Board up
`/board-up` as for the breadth runs: Llama 3.2 3B (Q4_0 pure, embq8) on the NPU lane :8080, Gemma 3 1B on
the CPU lane :8081, bev-decide on :8082 (as in the earlier bev explain runs); `-c 4096 -np 1 --cache-ram 0
-fit off -lv 4`. Nothing new on the board side.

## 3. Mock dry runs first (2 min; they are also the line-1 comparison the analysis needs)
Same test names with `--backend mock`; results go to `results/benchmarks_mock/<name>/`.
```bash
A="--overlay configs/v3.yaml,configs/cranfield.yaml"
B="--overlay configs/bev_ideas.yaml,configs/cranfield.yaml --bev explain=on,clear_skip=on,explain_prompt=v2,empty_skip=on,one_code=on"
scripts/benchmark.sh af_cf_v3_dev   $(ls data/episodes_cranfield_dev) ${=A} --backend mock
scripts/benchmark.sh af_cf_bev2_dev $(ls data/episodes_cranfield_dev) ${=B} --backend mock
A="--overlay configs/v3.yaml,configs/tep.yaml"
B="--overlay configs/bev_ideas.yaml,configs/tep.yaml --bev explain=on,clear_skip=on,explain_prompt=v2,empty_skip=on,one_code=on"
scripts/benchmark.sh af_tep_bev2_board $(ls data/episodes_tep_board) ${=B} --backend mock
scripts/benchmark.sh af_tep_v3_board   $(ls data/episodes_tep_board) ${=A} --backend mock
```
(zsh: `${=A}` splits the variable into words; in bash write `$A`.)

## 4. Board runs, in this order (the runner logs chip temperature and cools between episodes)
| step | test name | episodes | about |
|---|---|---|---|
| 4a | `af_cf_v3_dev` | Cranfield dev, 6 | 45 min |
| 4b | `af_cf_bev2_dev` | Cranfield dev, 6 | 35 min |
| 4c | `af_tep_bev2_board` | TEP board subset, 22 | 3–4 h |
| 4d | `af_tep_v3_board` | TEP board subset, 22 | 5–7 h |

The same four commands as in step 3, **without** `--backend mock`. A stopped run resumes with the same
command (finished episodes are skipped); TEP can be split over days.
Each `RESULTS.md` bev table must show `failed 0` for explain and `one_code` / `empty_skip` under "used".

## 5. Analysis (laptop, 1 min)
```bash
env -u PYTHONPATH .venv/bin/python -m bench.board_insights \
    results/benchmarks/af_cf_v3_dev results/benchmarks/af_cf_bev2_dev \
    results/benchmarks/af_tep_bev2_board results/benchmarks/af_tep_v3_board \
    --out results/benchmarks/af_insights.json | tee results/benchmarks/af_insights.md
```
It prints, per run: accuracy on the board and on mock (the line-1 rule, same episodes), agreement with
mock, line-1 follow, copies of `[2,1]`, how often a deviation from line 1 was right, how often the true
case was in the prompt (and whether the token guard cut it), 1-case answers, Llama calls, decode tokens,
seconds per tick. For comparison the earlier runs gave (same tool):
| run | accuracy | line-1 follow | copy [2,1] | deviations right |
|---|---|---|---|---|
| Cranfield dev v3 | 0.524 in fault (0.417 from onset) | 0.996 | 0.004 | – |
| Cranfield dev bev v1 | 0.435 in fault (0.364) | 0.060 | 0.851 | 0.155 |
| TEP board v3 | 0.380 | 0.996 | 0.003 | 0.125 |
| TEP board bev v1 | 0.261 | 0.637 | 0.133 | 0.060 |
Old and new TEP accuracies are NOT directly comparable (new library, persistence): compare each new board
arm with its own mock run and with the other new arm.

## Optional, only after step 5
- Cranfield reporting set, both arms (10 episodes each, ~1 h each): `af_cf_v3_report`, `af_cf_bev2_report`
  with `$(ls data/episodes_cranfield)`. Run once, for the paper table; decide nothing on it.
- Energy: if the USB meter is in, log its reading per test with the laptop time.

## Things to know
- Verifier prompts on TEP can reach ~2,650 tokens (over the 1,280 budget, inside the 4,096 context). They
  are flagged `over_limit`, never cut (Phase 1 rule); an open decision for Shubham, not something to change.
- `test_real_time_answers_get_the_tokens_of_their_own_envelope` is flaky on `main` too (timing).
- Do not edit thresholds, `configs/base.yaml` or the case libraries. If a number looks wrong, send it, do
  not adjust.

## Send back
`results/benchmarks/af_*` and `results/benchmarks_mock/af_*` (RESULTS.md, test.json, per-episode summaries,
gzipped runs and call journals, temperatures) and `af_insights.md/json`. Commit them on a branch of your own
(e.g. `accuracy-board-runs`) and push it to Shubham's repo.
