# FaultExplainer code-only baseline (build list B1) — build report

## Status
DONE for the baseline: built, tested, agreed (2026-11-13) and run on the nine requests. **Result: 3 of 9 top-1 and 4 of 9
top-3 right, in every form and ordering** (uniform expectation 1.27 and 3.38); details in the "Result" section of
`reports/ext_faultexplainer_baseline_prereg.md`. The model rerun (A2) has not run: it waits for the board. Built 2026-11-13 on Shubham's
laptop, branch `fe-baseline` (from `bc-build`, with `origin/bc-runs` merged in).

| piece | file |
|---|---|
| ranker, row writer, reference answers | `bench/ext_faultexplainer.py`: `content_words`, `cause_texts`, `overlap_rank`, `baseline`, `references`; two new subcommands |
| tests | `tests/test_ext_faultexplainer_baseline.py` (14 tests: 10 for the baseline, 4 for the garbage rule) |
| rules and result | `reports/ext_faultexplainer_baseline_prereg.md` (agreed 2026-11-13; result appended) |
| rerun rules for the model arms | Amendment A2 in `reports/ext_faultexplainer_prereg.md` (**agreed 2026-11-13**) |
| A2's garbage rule in code | `is_garbage`, `health` (reads no pick), and `score` now treats a garbage reply as a failed call |
| board steps for the rerun | `HANDOFF_FE_RERUN.md` |

`run` is unchanged. `score` changed in one way, required by A2: a reply holding a run of 20 or more "@" is a failed
call, and each arm and form gains a `failed` count. A row without such a run scores exactly as before. The baseline calls no model: its numbers are not agent results and not FaultExplainer's
own method. TEP is a public benchmark. No energy figure.

## Verification
| step | result |
|---|---|
| ran the module | **pilot only:** `baseline … --limit 2 --label pilot` wrote 24 rows (2 requests × 3 forms × 4 orderings) with the 15 fields of a `run` row plus `scores` and `n_scoring`; every row holds three picks. The picks were not printed. `references` on the real request file with no rows: uniform 1.267 / 3.382 of 9; first three lines 1/1, 1/4, 3/3, 1/3 (top-1 / top-3 for `original`, `shuffle_a`, `shuffle_b`, `line1_last`) |
| self-tests | 14 passed / 0 failed. With the existing suites (`test_ext_faultexplainer`, `test_echo_test`, `test_echo_causes`, `test_echo_4bit`): 73 passed, 1 skipped (needs the FaultExplainer checkout, not on this laptop) |
| independent re-derivation | (1) **uniform top-3 expectation, 9 requests:** the tool's closed form gives 3.382; a count over all 455 triples of causes gives 3.382418; 0.01% apart (rounding). (2) **against the values already in the main pre-registration** for Table 1's 11 detected faults: the tool gives 4.125 against the stated "4.1 / 11", and 3 against the stated "(1, 2, 3) score 3 / 11" |
| ran the garbage rule on real rows | `health` on the invalid F1 file: 108 calls, 0 errors, **104 garbage** (share 0.963), `may_be_scored` false. Gagan's report counted 104 by reading the replies: the same number by a different route. `score` on that file now scores 4 rows (fault 5, `eval`, one per ordering) and marks 104 as failed |
| mutation check | 15 of 15 caught: 10 for the baseline (table below) and 5 for the garbage rule (run length 2000, run length 19, garbage replies scored, arm limit 50%, errors counted as garbage). The first pass caught 9: "substring match instead of whole words" survived, so `test_a_shortened_word_does_not_match_its_long_form` was added and the mutation rerun |

| mutation | caught by |
|---|---|
| rank weights reversed | `…top_feature_is_ranked_first`, `…rank_weights_decide…`, and two more |
| ties to the higher IDV | `test_ties_go_to_the_lower_idv…`, and two more |
| ties by list position | `test_the_code_picks_do_not_move_when_the_list_is_shuffled` |
| shortest word 2 letters | `test_content_words…` |
| stop list emptied | `test_content_words…` |
| substring match instead of whole words | `test_a_shortened_word_does_not_match_its_long_form` |
| uniform expectation over pairs, not triples | `test_references_uniform_matches_a_count_over_every_triple` |
| aliases ignored in the references | the same |
| most-frequent answer: ties to the higher IDV | `test_references_first_three_lines_and_the_arms_most_frequent_answer` |
| the reply holds two picks | `test_baseline_rows_are_read_by_score…` |

The mutation script is kept outside the repository (session scratchpad); it restores the file after each run, and
`git diff` showed the file unchanged afterwards.

## Direction checks
| claim | expected | measured | OK/FAIL |
|---|---|---|---|
| a cause sharing a word with the top feature | ranked first | first, score 6 (hand-built request) | OK |
| the same match at a lower T2 rank | scores less | 5 against 6 | OK |
| shuffling the list | picks do not move | identical in 4 orderings; 0 position-follows (hand-built request) | OK |
| on the real requests | the same | identical picks in all 12 rows of each of the 9 requests; 0 position-follows | OK |

## Constants introduced
| symbol | value | provenance | range | affects |
|---|---|---|---|---|
| `RANK_WEIGHTS` | 6…1 | CITED: `HANDOFF_BUILD_LIST.md` B1 | – | which matched cause wins |
| `MIN_WORD` | 3 | CITED: the same | – | which words count |
| tie rule | lower IDV | CITED: the same | – | ties, and places filled at score zero |
| `STOP` | 10 English function words | DESIGN | this list, or empty | nothing on the audited cause list |
| "adds" margin (pre-registration) | 2 of 9 | DESIGN, PROPOSED | 1–3 | how easily a model is said to add |
| "no information" bound (pre-registration) | 3 of 9 | DERIVED from the uniform expectation 3.38 | 3–4 | whether the baseline comparison may be used |
| garbage reply (A2) | a run of 20 "@" | FITTED to F1's rows (failed replies ≥ 100, normal replies 0) | 5–100 | which replies are dropped in a rerun |

## Numbers that changed
None. No existing result, rule or file content was changed, except that `reports/ext_faultexplainer_prereg.md` gained
A2 (PROPOSED) and its two earlier agreement records now sit in time order after the merge.

## Decisions taken
1. **Built here, on a new branch `fe-baseline`,** not on `bc-build-2` as the build list names for the second laptop.
   No baseline branch existed on the remote, and a separate name avoids a clash if the second laptop starts one.
2. **A separate `references` subcommand** instead of adding the reference answers to `score`'s output. The build list
   asks for `score` to stay unchanged, and Gagan's saved F1 score file has that format.
3. **The stop list is function words only.** The build list left the list open. Adding process words would be a choice
   about this benchmark made after seeing its cause list.
4. **The merge conflict in the main pre-registration** was resolved by keeping both agreement records, Gagan's (00:35)
   first and A1 after it. No text of either was changed.

## Disagreements recorded, not resolved
- **The baseline is expected to be weak, and may carry no information.** One outcome is already known by hand: it
  misses fault 5 (top three 1, 3, 6). The word "feed" is in six cause lines and in two of fault 5's features, and the
  tie rule then prefers the low numbers. This is left as built. The pre-registration proposes a rule for the case where
  the baseline is at or below chance.
- **The build list's design is a word match;** a trained classifier on TEP would be a stronger "model off" arm. Not
  built: it is a larger piece of work and a different comparison.

## Blocked / needs a decision
1. ~~Agree the baseline pre-registration~~ **agreed 2026-11-13 and run.** (the ranker as fixed, the "adds" margin of 2, the "no
   information" bound of 3). Then the baseline runs in seconds.
2. ~~Agree Amendment A2~~ **agreed 2026-11-13.** The rerun now waits for the board and for this branch to reach
   Gagan's Mac (it is not pushed).
3. **Who looks at the 8-call check.** It uses two scored requests. A2 says its picks are not read; that depends on
   whoever runs it.

## What I could not verify
- **Anything on the board.** No call was made. Whether `NHVX=2` avoids the "@" failure on 2,600-token prompts is
  untested.
- **Whether the 8-bit Llama 3B is on the SM8750,** and whether the board has room for it (3.4 GB).
- **The real build path** (`build` against FaultExplainer's checkout): the checkout is not on this laptop, so that test
  is skipped here. The request file is used as committed.
- **How much of the baseline's 4 of 9 is the tie rule:** `n_scoring` is 3 to 10 on every request, so no answer is the tie
  rule alone, but ties inside the "feed" and "reactor" groups decide most top-threes (one hit, fault 6, rests on it).
