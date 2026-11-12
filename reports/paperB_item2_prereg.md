# Paper B item 2: published fixes for the diagnostician's shortcuts, pre-registration

**Status: DRAFT, 2026-11-12. Written before any board run.** Items marked PROPOSED must be agreed (dated, under
"Agreed") before the first scored run. Code: `fieldmind/multi/debias.py`, wired in
`fieldmind/multi/agents/diagnostician.py`. Every switch is off by default; a run that does not name `multi.debias`
is unchanged (tested: `test_switches_off_leave_the_run_unchanged`). Plant data: boiler synthetic, Cranfield real rig,
TEP public benchmark. No energy figures.

## Why
Reviewers will say echo (line 1 in 98–100% of answers, the worked example copied in 86% of one format's Cranfield
answers) is a prompting mistake. These arms try the published fixes on the same agent:
- **If none beats no-model:** that is the strongest evidence the model adds nothing.
- **If one does:** its extra cost on the phone gives an accuracy-per-second (later, per-joule) trade-off.

## Arms (overlays stacked last on a system's usual overlays)
| arm | overlay | what changes | extra model calls |
|---|---|---|---|
| base | – | the system as run in the sweep | – |
| no example | `configs/debias_noexample.yaml` | the diagnosis prompt loses its `Example:` line (v3; under explain v2 there is none, so a no-op) | 0 |
| no letters | the system's `compact.group_letters: false` (existing switch) | no `[group X]` tags, no `"g"` | 0 |
| calibrate | `configs/debias_calibrate.yaml` | Zhao et al. 2021: the rank-1 line is re-chosen as argmax(log p − log prior), with the prior read from a content-free copy of the prompt (all fact, case, note and record text and the world line set to `N/A`) | 1 per prompt shape (side × number of case lines × format), once per run |
| PriDe | `configs/debias_pride.yaml` | Zheng et al. 2024: the position prior from the first 5 calls of each prompt shape, each asked in 4 cyclic orderings; then the rank-1 line is debiased as above | 3 extra on each of the first 5 calls per shape |
| PSC | `configs/debias_psc.yaml` | Tang et al.: every diagnosis asked in 3 orderings (identity + 2 seeded shuffles), rankings combined by Borda count (ties go to the identity ordering) | 2 per diagnosis |
| no model | the mock backend, same overlays | retrieval order only (**not an agent result**) | – |

calibrate and PriDe re-choose **only the rank-1 line**; the rest of the answer is the model's. They read raw
(pre-grammar) token log-probabilities, which only llama-server reports. On any other backend they record
`unchanged_because: no_probs` and change nothing (tested).

**Systems (PROPOSED):** v3 (full answers) on all three plants, and v3x (rank-only answers, explain v2) on Cranfield and
TEP, in lockstep.
- Real time is not used: these arms change the work per tick, and capacity is a separate question (item 6).

## Constants (DESIGN; values fixed now)
| symbol | value | range | affects |
|---|---|---|---|
| `psc_k` | 3 | 2–5 | PSC's orderings per diagnosis and its cost |
| `pride_samples` | 5 | 3–10 | calls that estimate PriDe's prior per prompt shape |
| `pride_perms` | 4 | 2–n | cyclic orderings per estimating call |
| `top_logprobs` | 20 | 5–20 | how many alternatives per token are read (20 is the server's default) |
| missing-line floor | lowest reading − 1 nat | 0.5–3 nats | the prior or reading of a line not among the alternatives |
| `TIE_NATS` | 1e-6 | 1e-9 to 1e-3 | ties keep the model's own rank-1 |
| Borda points | n − position | – | PSC's combination (DESIGN: replaces the paper's central ranking) |

## Measures (dev set only; reporting episodes are never used to decide)
1. **Accuracy against no-model:** group top-1 in fault (`Q2_group_top1_in_fault`) and case top-1; each arm minus the
   no-model run of the same episodes; bootstrap 95% intervals over episodes (2,000 resamples, seed 20261111).
2. **Echo:** `bench/echo_test.py saved` on each arm's run folder. Line-1 share, and right on deviations against the
   random-other-line expectation.
3. **What the arm changed:** `bench/echo_test.py changed <arm> <base>`. Ticks whose published top cause differs from
   base, and who was right.
4. **Cost:** model calls per tick, NPU seconds per tick (`changed` reports it), and prompt and answer tokens.
5. **What calibrate / PriDe did:** from each answer's `debias` record. Share moved, share with no reading
   (`unchanged_because`), and the priors read (logged for the paper's figure).

**Scoring tool:** `bench/paperB_score.py <arm folder> <no-model folder> --base <base folder>` gives measures 1–4 in
one table.
- **The headline accuracy is the mean over episodes,** the convention of the earlier tables: for example, the Cranfield
  v3 board run is 0.524. Pooled over ticks it is 0.327, because one long episode dominates; the pooled figure is
  printed beside it.

**No-model folders (mock: retrieval order, not an agent result):**

| system | plant | folder |
|---|---|---|
| v3 | Cranfield | `results/benchmarks_mock/af_cf_v3_dev` |
| v3 | TEP | `results/benchmarks_mock/af_tep_v3_board` |
| v3 | boiler | `results/benchmarks_mock/sched_v3_lockstep_boiler` |
| v3x | Cranfield | `results/benchmarks_mock/paperB_nomodel_v3x_cranfield` (made 2026-11-12) |
| v3x | TEP | `results/benchmarks_mock/paperB_nomodel_v3x_tep` (made 2026-11-12) |

**Base folders (the board, without the fix):** `results/benchmarks/af_cf_v3_dev`, `af_tep_v3_board` and the sweep's
lockstep cells. They were run earlier, so heat and date differ from the arms; this is stated as a limit.

## Decision rule (PROPOSED)
| outcome | rule (per plant) | meaning |
|---|---|---|
| fix helps | arm − no-model accuracy ≥ +0.05 and its 95% interval excludes 0 | report the gain and its cost per tick |
| fix does not help | otherwise | report as "the published fix does not make the model add value here" |
| fix removes echo | line-1 share drops by ≥ 0.20 (absolute) against base | echo is a shortcut the prompt invites (supports Idea C's "prompt" branch) |

**No arm is "kept" into the agent on this evidence.** This is a measurement for Paper B, not a keep/revert step.

## Board time (estimate)
- One dev pass per plant per arm in lockstep: the sweep's lockstep reference took about 7 min per boiler episode.
- PSC triples the diagnosis calls.
- About **two nights** for all arms × systems × plants, cooled between runs.

## Laptop checks done before registration (plumbing only, laptop model, not results)
See "Smoke test" in `reports/paperB_prep.md` once run. It checks that each arm completes with a real model, that the
first-line token is found in llama-server's log-probabilities, and that the call counts are as stated.

## Agreed
(none yet)
