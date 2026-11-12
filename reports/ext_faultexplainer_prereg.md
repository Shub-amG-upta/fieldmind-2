# External audit 1: FaultExplainer, pre-registration (PLAN_PAPER_B.md item 1)

**Status: DRAFT, 2026-11-12. Written before any model call.** Every item marked PROPOSED must be agreed by the team
(dated, under "Agreed" at the end) before the first call. The tool is `bench/ext_faultexplainer.py`; its requests are
fixed in `reports/data/ext_faultexplainer_requests.json`. TEP is a public simulation benchmark; FaultExplainer's data
files come from its repository. No energy figures.

## What is audited
**The system:** FaultExplainer (Khan et al., arXiv 2412.14492), `github.com/li-group/FaultExplainer` at commit
`2fcfee975a687c350f10909eeccd1ecdd60340be`, MIT licence. How it works:
- PCA (T2) detects a TEP fault and takes the six variables with the largest T2 contributions;
- an LLM is asked which of **15 listed root causes, IDV(1)–IDV(15), always in that order**, explains them (the
  "root causes included" prompt, top three).

The paper reports GPT-4o right on 7 of 11 PCA-detected faults and o1-preview on 9 of 11 (Table 1, top three, aliases
credited).

**How the prompts are built:** with FaultExplainer's own code, not a copy:
- the prompt strings, from `backend/prompts.py`;
- `generate_feature_comparison`, from `backend/app.py`;
- the LaTeX instruction, from `backend/test_explain.py`;
- the selection steps of its evaluation script (faults 3–15, the first window of 6 consecutive T2 anomalies, the top 6
  T2 contributions).

**Fidelity checks, passed:**
1. **PCA detects the same faults.** Faults 3, 4, 9 and 15 are not detected, as Table 1 marks them. Faults 1 and 2 are
   in Table 1 but outside the script's `range(3, 16)`, so the paper's results for them come from another run;
   they are not audited here.
2. **Fault 7's evidence is the paper's.** Ours: Stripper Pressure −3.00%, A and C Feed −8.90%, Reactor Pressure
   −3.49%, Product Sep Pressure −3.69%. The paper's text: "Stripper Pressure decreased by 3.00%, the A and C Feed flow
   rate decreased by 8.90%, the Reactor Pressure decreased by 3.49%…".
3. **The alias rule reproduces the paper's own counts** (7/11 and 9/11), recomputed from Table 1.

## Found before any call (from FaultExplainer's code and its published Table 1)
1. **The evaluation prompt carries the answer's index.**
   - `test_explain.py` ends the prompt with "you can start your response with `\subsubsection{Fault <i> prompt=root
     causes included, model=gpt-4o}`", where `<i>` is the **true fault number**.
   - The root-cause list numbers each cause by its IDV number, so "Fault 6" maps to "6. IDV(6)".
   - The interactive app (`app.py` `/explain`) does not add this text; only the published evaluation does.
   - In Table 1, the first pick equals the fault number on 2 of 11 faults for GPT-4o (faults 6, 7) and 3 of 11 for
     o1-preview (2, 6, 7).
2. **GPT-4o's picks cluster on a few options:**
   - IDV(6) is in its top three for **all 11** faults, and IDV(4) for 9;
   - it uses 8 distinct options in 33 picks.
   - A constant answer (4, 5, 8), chosen after seeing the table, scores the same 7/11. Uniform random is expected to
     score 4.1/11; the first three lines, (1, 2, 3), score 3/11.
   - These are 11 faults with one trajectory each, read from a published table: **descriptive, not a test**. They can't
     separate a position preference from a content preference; the shuffle test below can.

## Requests (fixed)
- The 9 faults that the evaluation script reaches and PCA detects: **5, 6, 7, 8, 10, 11, 12, 13 and 14**.
- **Three prompt forms per fault:**
  - `eval`: the published evaluation prompt, byte for byte, with the leak;
  - `eval_noleak`: the same, with the fault number replaced by `N`;
  - `app`: what the interactive app sends.
- **Four orderings per form** (from `bench.echo_test.orderings`, seed 12345, the evaluation script's seed): `original`,
  `shuffle_a`, `shuffle_b` and `line1_last`. The 15 root-cause lines are reordered and renumbered 1–15, each keeping
  its IDV label; every other byte is kept.
- So **108 calls per arm.**
- **Prompt size:** 2,470–2,641 tokens with the Llama 3.2 chat template (counted with the pinned build's
  `/tokenize`).
- **Answer cap:** 1,400 tokens (`MAX_TOKENS`, DESIGN), because lanes run `-c 4096`. FaultExplainer itself sets no cap.
- **Sampling:** temperature 0, seed 12345, `cache_prompt` false; the chat endpoint, with the prompt as the user message
  (as FaultExplainer sends it).

## Arms (PROPOSED)
| arm | model | where | why |
|---|---|---|---|
| **F1** | Llama 3.2 3B Q4_0, **the board's file** (`5aa3ece5…`) | board NPU lane (port 8080, pinned build, standard flags) | the on-device audit: FaultExplainer run on the phone |
| F0 | GPT-4o, as the paper used | OpenAI API | reproduce Table 1 with our harness; **needs the team's decision on an API key and its cost** (about 108 calls) |
| pilot | Llama 3.2 3B Q4_0, the laptop rebuild (`dace5753…`, not the board file) | laptop | call time and parse rate only |

## Parse rule (fixed)
- A reply's picks are the **first three distinct `IDV(k)`, 1 ≤ k ≤ 15, it names**, in order.
- "Fault k" and bare numbers never count: "Fault k" also appears in the leaked header.
- A reply with no `IDV(k)` is unparsed. It is counted and reported, never guessed.

## Measures (per arm and form, for each ordering)
- **Parse rate.**
- **First pick on line 1.**
- **Right, top-1 and top-3,** under the paper's alias rule (Table 1's aliases, `ALIASES`).
- **First pick equals the true fault number.**
- **Shuffle follow:** for each shuffled ordering against `original`, whether the first pick stayed with the **content**
  (the same IDV), moved with the **position** (whatever is now on the original pick's line), went to **neither**, or
  was **uninformative** (the shuffle left that cause on its line).
- **Leak effect:** "first pick equals the fault number" in `eval` minus the same in `eval_noleak`.
- **Baselines:** uniform random top-3 (expected value), the first three lines, and the arm's own most frequent answer.
- **Cost:** prompt and answer tokens, the server's prefill and decode timings, and call latency.

**n = 9 faults.** Every measure is reported as counts (k of 9), with no significance claims.

## Pilot (fixed)
- The first 2 requests, `app` form, `original` ordering, on the laptop rebuild.
- Labelled `pilot`, kept, and not scored.

## Stop rule (PROPOSED)
- **If the pilot's parse rate is 0 of 2:** stop and amend the parse rule (dated, written here) before any scored call.
- **If more than 20% of F1's replies are unparsed:** report that as a finding (the model doesn't follow the format) and
  do not re-parse by hand.

## Outcome rules (PROPOSED: thresholds to be agreed)
| outcome | rule (per arm, `app` form, pooled over the three shuffled orderings) | meaning for Paper B |
|---|---|---|
| position echo | position-follow ≥ 50% of informative pairs **and** first pick on line 1 ≥ 50% in every ordering | the outside system's small model echoes as ours does: B generalises |
| favourite option | one IDV in the top three for ≥ 8 of 9 faults in every ordering, wherever it sits | a content shortcut, not a position one: B's "the model adds little" holds, its mechanism differs |
| reads the evidence | content-follow ≥ 70% of informative pairs **and** top-3 right above the uniform-random expectation | the outside system's model does use the evidence: B narrows (see PLAN_PAPER_B.md decision points) |
| leak used | leak effect ≥ 3 of 9 faults | the published evaluation's prompt helped its answers; a methodological finding about that evaluation |

## Board time (estimate)
- **Per call:** prefill about 3 s; decode up to 1,400 tokens at about 17 tokens/s, about 80 s. Up to about 85 s per
  call.
- **F1:** 108 calls, **about 1.5–2.6 hours**, plus cooling between forms.
- Chip temperature is logged before and after; the sampler stays at its light setting.

## Not changed
No agent code, config, threshold or episode. Nothing of FaultExplainer is copied into this repository.

## Limits, stated now
- **Nine faults, one trajectory each:** this is FaultExplainer's own evaluation set.
- **No model-free diagnosis arm.** FaultExplainer has no step that maps the six variables to a cause without the LLM, so
  "no model" here means chance and constant answers, not a trained classifier.
- **The audit uses FaultExplainer's prompt as published.** Its length (about 2,600 tokens) and free-text answers
  are its design, not ours.

## Pilot result (2026-11-12, laptop rebuild, not scored)
2 of 2 replies parsed; the picks are the model's numbered selections. One answer stopped at the 1,400-token cap, the
other at 1,061 tokens. About 68 s per call on the laptop. The stop rule is not hit; nothing is amended.
Rows: `results/ext/faultexplainer_pilot.jsonl`.

## Agreed
**Agreed 2026-11-13 00:35 (laptop time) by Gagan (human instruction: "s2, s3, f3 just agree"), on behalf of the team. Shubham was not consulted before this agreement.** Every item marked PROPOSED above is agreed exactly as written: the arms, the stop rule and the outcome-rule thresholds. Nothing is changed. Board: the SM8750 (`1d9c8f40`, v79), not the SM8650 the plan assumed, because the SM8650 has been exchanged. Laya and bev files restored from the SM8650 backup (sha256 equal to its manifest).
