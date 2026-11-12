# 4-bit against 8-bit confirmation: build — report

## Status
DONE (build only). The tool, the two request sets, the run and score scripts, the pre-registration (DRAFT) and the
runbook are built and piloted. **No scored run has been made.** The full run waits for the pre-registration to be
agreed.

| piece | file |
|---|---|
| tool | `bench/echo_4bit.py` (build, squad-build, run, score) |
| tests | `tests/test_echo_4bit.py` |
| run and score scripts | `bench/echo_4bit_runs.sh`, `bench/echo_4bit_score.sh` |
| held-out agent prompts (set H) | `reports/data/echo_4bit_requests.json`: 400 scored boiler requests, 9 new dev episodes |
| public evidence set | `reports/data/echo_4bit_squad.json`: 300 SQuAD v1.1 dev questions, each with a swapped passage |
| rules | `reports/echo_4bit_prereg.md` (DRAFT, every threshold PROPOSED) |
| runbook | `HANDOFF_4BIT.md` |
| small change to existing code | `bench/echo_causes.py` `run_prior` gains `forms` (default unchanged) |

Boiler data is synthetic. SQuAD and MMLU are public. Pilot calls are laptop replays, not NPU results.

## Verification
| step | result |
|---|---|
| ran the module | **Pilot on this laptop,** 3 requests per test, Llama 3B Q4_0 and Q8_0 (`LIMIT=3 bench/echo_4bit_runs.sh`): 48 calls, all `ok`; every case line and every MMLU letter has a probability reading; SQuAD replies are short answers; the scorer reads the rows. Plumbing only, not scored. **`score` on saved set R rows** runs through `bench/echo_4bit_score.sh` |
| self-tests | `tests/test_echo_4bit.py`: 16 passed. With `test_echo_causes.py` and `test_echo_test.py`: 52 passed |
| independent re-derivation | Boiler AUC on the saved set R rows, tool (average-rank formula, `debias.normalise`) against last night's exploratory script (direct count of pairs): 4-bit 0.5902 vs 0.590; 8-bit 0.7809 vs 0.781; 16-bit 0.773 vs 0.773; within-episode 0.4832 / 0.7693 / 0.7616 vs 0.483 / 0.769 / 0.762. Differences 0 at the printed precision. Inside the tests, `auc` is also checked against a direct pair count on random data |
| mutation check | 14 mutations, 14 caught. **Two survived at first** and each got a new test: "a gold answer may survive the swap" (`test_squad_select_drops_a_question_whose_gold_answer_survives_the_swap`) and "a pair uses every row, not the common ones" (`test_a_pair_is_scored_on_the_requests_both_arms_answered`, strengthened). The others: ties counted as wins; pair difference reversed; within-episode AUC replaced by the pooled one; `swap_follows` reading the gold answer; unscored requests kept; content-free rows read as real; answers matched inside words; the `forms` option ignored; letter tokens not stripped; an old episode accepted; the failed-call check dropped; the line-1 share fixed at 1 |

## Direction checks
| claim | expected | measured | |
|---|---|---|---|
| an arm whose probability is high exactly when line 1 is right | AUC 1.0 | 1.0 (test) | OK |
| an arm with a constant probability | AUC 0.5 | 0.5 (test) | OK |
| pair = high − low | reader over blind is +0.5 | +0.5; reversed pair −0.5 (test) | OK |
| a reply that holds the swapped-in answer "follows the passage" | `swap_follows` 1, `swap_memory` 0 | as expected (test) | OK |

## Constants introduced
| symbol | value | provenance | range | affects |
|---|---|---|---|---|
| `SQUAD_CAP` | 24 tokens | DESIGN | 16–48 | how much of a wordy answer is kept; scoring looks for the answer inside the reply |
| `SQUAD_MAX_CONTEXT` | 1,200 characters | DESIGN | 800–2,000 | which paragraphs are eligible; keeps prompts far below 4,096 tokens |
| `SQUAD_MAX_ANSWER_WORDS` | 5 | DESIGN | 3–8 | which questions are eligible |
| seed for set H and SQuAD | 20261113 | DESIGN (the date) | – | which questions are sampled |
| outcome thresholds | 0.10, 0.65, 0.05 | PROPOSED in the pre-registration | given there | the verdicts |

## Numbers that changed
None. `run_prior` behaves as before unless `forms` is passed (test:
`test_run_prior_can_send_the_real_prompt_only`).

## Disagreements recorded, not resolved
- **I first proposed using the 30 reporting episodes as the held-out set.** The request builder refuses reporting
  episodes by design ("never used to design or run a test"). Set H uses 9 **new dev episodes** instead, from the
  teammate's `m6_new_r1` board runs. That is a harder test than new seeds of old scenarios, and it keeps the rule.
- **The public evidence test is not Pandey's own data.** It follows the same idea (the answer is in the passage) on
  SQuAD, and adds a swapped passage. The pre-registration says so.

## Blocked / needs a decision
1. **Agree `reports/echo_4bit_prereg.md`:**
   - the arms;
   - the thresholds (0.10, 0.65, 0.05);
   - the verdict rules;
   - Gemma not counted for "general".
2. **The swapped passages are crude.** The swapped-in answer matches only "number" or "text", so some read oddly (a
   noun where a person stood). Options: keep as is (both precisions see the same passages), or restrict the test to
   numeric answers (72 of the 300). To be decided before the run.
3. **The local Q4_0 file on this laptop is not the board's file** (sha256 `dace5753…` against `5aa3ece5…`). The
   Mac's copy is the board's. Nothing scored may be run here with the local 4-bit file.

## What I could not verify
- **That the five new 8-bit files build cleanly.** The 16-bit sources are on the teammate's Mac, not here. Qwen3 or
  Gemma may need the same extra `llama-quantize` arguments their 4-bit builds used.
- **The board steps in `HANDOFF_4BIT.md`.** No board was attached. They use the existing `bench.board` commands and
  the tested `run prior` path, with only the lane label and `--forms original` new.
- **Run time.** The 10–12 h estimate comes from the earlier runs' log times, not from a timed run.
- **That set H's episodes behave like set R's.** Line 1 is right on 49% of set H against 65% of set R's boiler
  requests, so the mix differs. The AUC does not depend on that mix, but the episodes are different faults.
