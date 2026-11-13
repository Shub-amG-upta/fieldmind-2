# External audit 1: FaultExplainer, pre-registration (PLAN_PAPER_B.md item 1)

**Status: AGREED 2026-11-13 (A1 below; the F1 run had started before agreement, see A1). Was DRAFT, 2026-11-12,
written before any model call.** Every item marked PROPOSED must be agreed by the team
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

**A1, 2026-11-13.** The human agreed every PROPOSED item in this file as written, unchanged ("agreed"):
- the arms (F1 board NPU; pilot);
- the stop rule (pilot parse 0 of 2; more than 20% of F1 unparsed);
- the four outcome rules and their thresholds (50% / 50%; 8 of 9; 70%; 3 of 9).

**F0 (GPT-4o) is agreed as a design only.** It is not run until the separate decision on an API key and its cost.

**Recorded honestly: the F1 board run had already started before this agreement.**
- On 2026-11-13 the human reported that FaultExplainer was running on the QIDK. That is the first scored call, before
  "agreed".
- This laptop has seen no F1 row: `results/ext/` here holds only the pilot file.
- Whether anyone looked at F1 output before this agreement is not known here. **To be confirmed by whoever ran it.**
  If someone did, F1 is reported as exploratory.
- Nothing in this file was changed after the run started. The text above A1 is as committed on 2026-11-12.

**A code-only baseline is being added** (`HANDOFF_BUILD_LIST.md` B1) under its own pre-registration. It does not change
anything here. The limit "No model-free diagnosis arm" stays true for this file.

## F1 on the board: result (2026-11-13, SM8750 `1d9c8f40`, 01:56–04:42 laptop time)
`results/ext/faultexplainer_F1.jsonl` (108 / 108 calls `ok`), score `results/ext/faultexplainer_F1_score.txt`, NPU server log
`results/ext/f3_lane_npu.log`.

**The stop rule is hit, but not for the reason it anticipates.**
- **Calls 1–4 are normal:** fault 5, form `eval`, four orderings, finish `stop`, 527–773 tokens.
- **From call 5 on, every reply degenerates into one repeated token, "@" (id 31):** 104 / 108 replies are mostly "@",
  and all of them run to the 1,400-token cap. Some start normally and turn into "@" partway (for example the `app` form of
  fault 5, after about 356 characters).
- **So almost nothing parses:** `app` 0 / 36, `eval` and `eval_noleak` about 1 per ordering.

**This is a failure of the NPU computation on this board, not the model not following FaultExplainer's format.**
**F1's numbers must not be read as FaultExplainer's model behaviour.**

**Facts from the server log:**
- One server ran for all 108 calls.
- `cache_prompt` is false, and every call recomputed its prompt from 0 (`cached n_tokens = 0`), so the prompt cache is
  not involved.
- Prompts are 2,471–2,642 tokens, processed in two chunks (2,048 and the rest).
- No error or warning lines were logged. The chip ended at 91 °C.

**Related:** the same "@" token made 7 calls fail in the two attention arms of the nondeterminism study's SM8750 run on
the same night (`reports/nd/m9_cause_sm8750.md` in the nd-paper branch).

**Not tested:**
- whether a server restart before every call avoids it;
- whether the CPU lane, or the SM8650, gives normal F1 replies.

Each is a short board run, but a rerun changes the protocol, so the team decides (not run).

## Amendment A2 (PROPOSED, drafted 2026-11-13 on Shubham's laptop; not agreed, nothing in it has run)
**Why an amendment:** the F1 run above is invalid, and a rerun changes the protocol. Everything not named here stays
as written: the 108 fixed requests, the parse rule, the measures, the four outcome rules and their thresholds.

**Order of events, for the record:**
- 00:35: Gagan agreed the PROPOSED items on the team's behalf.
- 01:56–04:42: F1 ran.
- about 03:15: Shubham's "agreed" (A1), after F1 had started.
- 04:49: Gagan scored F1 and found the "@" failure. So F1's output has been looked at.

### 1. The F1 run of 2026-11-13
- It is **excluded from every outcome rule** and from the comparison with the code baseline.
- Its rows stay in the repository as a record of the board failure.
- Its four normal replies (fault 5, `eval` form) have been seen. Fault 5's `eval` rows in a rerun are therefore not
  blind; this is stated wherever they are reported.

### 2. What counts as a garbage reply (fixed before any rerun call)
- **A reply is garbage if it holds a run of 20 or more consecutive "@" characters.**
- A garbage reply is a failed call. It is never parsed, and it is counted and reported.
- **An arm with more than 5% garbage replies (6 or more of 108) is invalid as a whole** and is not scored.

| threshold | value | provenance | range | affects |
|---|---|---|---|---|
| "@" run | 20 | FITTED to F1's 108 rows: the 104 failed replies each hold a run of 100 or more, the 4 normal replies hold no "@" at all, so any value from 1 to 100 separates them | 5–100 | which replies are dropped |
| arm invalid above | 5% | CITED: the run check of `reports/echo_4bit_prereg.md` | – | whether an arm is scored |

### 3. Board and NPU setting
- **Board:** the SM8750 (`1d9c8f40`, Hexagon v79). The SM8650 this file assumed has been exchanged.
- **NPU threads:** the lane is started with `NHVX=2`, and is otherwise the standard lane.
  - Reason: on this board the default 6 threads gave "@" failures on 42 of 1,000 agent calls, and 1 or 2 threads gave
    0 of 1,000 with bit-identical replies, at about 1.26× the time per call (`reports/nd/m9_cause_sm8750.md` and the
    M9-3 run, branch `nd-paper`).
  - **Not known:** whether this holds on FaultExplainer's prompts. Those results are on prompts of about 750 tokens;
    these are 2,471–2,642.
- **Fallback order, fixed now.** Each setting first gets a check of 8 calls (requests 0 and 1, `app` form, four
  orderings). The check is read only for garbage replies, finish reason and token counts. Its picks are not read and it
  is not scored.
  1. `NHVX=2`. No garbage reply in 8: run the arms at this setting.
  2. Otherwise `NHVX=1` (about 2.1× the time per call). The same check.
  3. Otherwise the CPU lane with the same file. The arm is then labelled CPU, and the paper says that the NPU of this
     board could not run FaultExplainer's prompts.
- The first setting that passes is used for **both** arms below.

### 4. Arms
| arm | model file | where |
|---|---|---|
| **F1r** | Llama 3.2 3B Q4_0, the board's file (`5aa3ece5…`) | NPU lane, the setting from section 3 |
| **F2** | the same weights at Q8_0, `Llama-3.2-3B-Instruct-Q8_0-pure.gguf` (`d91f61ab…`) | the same lane and setting |

- **Order:** F1r, then F2.
- **Before F2:** the 8-bit file must be on the SM8750 with its sha256 checked on the board, and listed in
  `bench.board.CANDIDATES` (the entry exists on branch `nd-paper`).
- **The outcome rules apply to each arm separately.**
- **4-bit against 8-bit:** the two arms' counts are shown side by side. With 9 faults there is no rule and no claim of a
  difference.
- **The code-only baseline** has its own file, `reports/ext_faultexplainer_baseline_prereg.md`.

### 5. Heat
- Chip temperature is logged before and after every form (36 calls). F1 ended at 91 °C.
- Before each form the chip is cooled to idle + 5 °C, for at most 900 s. CITED: the rule of
  `results/run_s3_sm8750.sh`.

### 6. Time (estimate, not measured at this setting)
- F1's four normal calls took 33–46 s each at 6 threads (decode about 18 tokens/s, replies of 527–773 tokens).
- At 1.26× that is about 45–60 s per call, so **about 1.4–1.8 hours per arm plus cooling**. The 8-bit arm's speed on
  this board is not known.

### Agreed
**A2 agreed 2026-11-13 11:47 (laptop time) by Shubham ("i agree on decision 2"), as written above, unchanged, before any rerun
call.** What was put to him as "decision 2": 2 NPU threads first, then 1 thread, then the CPU lane; the 8-bit arm F2;
the garbage-reply rule (a run of 20 "@", an arm invalid above 5%).

**Implemented after the agreement, before any rerun call:** `bench/ext_faultexplainer.py` `is_garbage`, `health` (reads
no pick) and the garbage rule inside `score` (a garbage reply is a failed call, never parsed, counted under `failed`).
Checked on the invalid F1 rows: 104 of 108 garbage, the count Gagan reported independently; the arm is refused.
