# Who does what: two branches

Written 2026-11-12. The full reasoning is in `PLAN_PAPER_BC.md`; this file is just the split.

## The two branches

Both start from `sched-study` at the merge of the echo replay.

| branch | who | what |
|---|---|---|
| **`bc-runs`** | the 24 GB Mac, which also drives the board | runs things: models, the board, the meter |
| **`bc-build`** | this laptop | builds tools, analyses saved data, writes the pre-registrations |

**How they meet:**
- When a tool is ready on `bc-build`, it is merged into `bc-runs`.
- When runs finish on `bc-runs`, their results are merged back into `bc-build` for scoring.

**Labels in the "when" column:**

| label | meaning |
|---|---|
| NOW | can start today |
| AFTER BUILD | waits for a tool from `bc-build` |
| AFTER AGREE | waits for you to agree its rules |
| AFTER METER | waits for the power meter |

---

## ECHO: why does the model copy line 1?

| # | job | branch | when | time |
|---|---|---|---|---|
| E1 | Is the true case even in the list? (from saved data) | build | NOW | hours |
| E2 | Vote over the 4 orders already run, for each model (no new calls) | build | NOW | hours |
| E3 | Re-check the "7B is a bit better after shuffling" hint under a written rule | build | NOW | hours |
| E4 | Write the rules for E5–E9 (one pre-registration) | build | NOW | 1 day |
| E5 | **Size curve:** run 0.5B, 1B, 1.7B and 14B through the same replay (`results/echo/run_arms.sh`) | runs | AFTER AGREE | 1 night |
| E6 | **Label vs position:** the code's top case first but labelled "3", letters instead of numbers, top case last but labelled "1" | build the forms, then runs | AFTER BUILD | build 1 day, run 1 night |
| E7 | **The model's prior:** what each model picks on an empty prompt, and whether removing that preference helps | build the replay option, then runs | AFTER BUILD | build 1 day, run a few hours |
| E8 | **Control:** the same 3B on shuffled MMLU questions. Does it read when it knows the answer? | build the request file, then runs | AFTER BUILD | build half a day, run 1 h |
| E9 | **Frontier model** on the same 450 requests: is the answer even in the prompt? | build | AFTER AGREE (needs your OK to use an API) | 1 day |

E5 needs the 0.5B, 1B and 1.7B files copied from the board (sha256 checked). The 14B is built with `bench/build_candidate_gguf.sh`.

**After this part we know whether the cause is the model (too small), the prompt (not enough evidence) or retrieval (the right case is missing).**

---

## OUTSIDE CHECK: does someone else's system echo too? (FaultExplainer)

| # | job | branch | when | time |
|---|---|---|---|---|
| F1 | Code-only ranking for FaultExplainer (its no-model baseline) | build | NOW | 1 day |
| F2 | Look for a second published system with runnable code (give up after 2 days) | build | NOW | 2 days |
| F3 | FaultExplainer with our 3B on the NPU, causes in original and shuffled order | runs (board) | AFTER AGREE | 2–3 h |
| F4 | FaultExplainer with GPT-4o, its own model | build | AFTER AGREE (needs money) | half a day |
| F5 | Score F3 and F4 | build | after F3, F4 | hours |

---

## SCHED: scheduling on the phone

| # | job | branch | when | time |
|---|---|---|---|---|
| S1 | Reading-speed check against the 2605.27435 paper (`bench/paperB_board.py plan --item 8`) | runs (board) | NOW | 30 min |
| S2 | `calibrated_finish` on the sweep's cells (`--item 6`) | runs (board) | AFTER AGREE | 3–4 h |
| S3 | More episodes, 3 repeats (`--item 7`) | runs (board) | AFTER AGREE | 2–3 nights |
| S4 | Score S1–S3 (`bench/sched_study.py`, `bench/sched_replay.py`) | build | after the runs | hours |

---

## FIXES: do the published fixes stop the copying?

| # | job | branch | when | time |
|---|---|---|---|---|
| X1 | Decide which fixes go to the board, from E2 and E7 (only the ones that help on the Mac) | build | after E2, E7 | hours |
| X2 | Those fixes on the board (`--item 2`, cut down) | runs (board) | AFTER AGREE | 1 night |
| X3 | Score X2 (`bench/paperB_score.py`) | build | after X2 | hours |

---

## ENERGY: what it costs in joules

| # | job | branch | when | time |
|---|---|---|---|---|
| P1 | Get the meter | you | NOW | – |
| P2 | Idle reading, then energy on the runs above (`bench/energy.py`) | runs (board) | AFTER METER | adds to the runs |
| P3 | A bigger model (the one ECHO says reads best) on the NPU: does it fit, and what does it cost? | runs (board) | after ECHO | 1–2 h |
| P4 | Score energy: J per call, per tick and per correct answer | build | after P2 | 1 day |

---

## GATE: only if some model reads (ECHO says yes)

| # | job | branch | when |
|---|---|---|---|
| G1 | Build a gate that accepts the model's pick only when it is the same in 2 orders | build | after ECHO |
| G2 | Run it on the board, with energy | runs | after G1 |

If no model reads, this part is skipped.

---

## WRITING

| # | job | branch | when |
|---|---|---|---|
| W1 | Figures and tables from every scored part | build | as parts finish |
| W2 | Paper draft | build | weeks 5–7 |
| W3 | Release the audit tool and the board logs | build | with the draft |

---

## What you need to decide now
1. **Agree the rules.** The rules for E5–E9 come first; I draft them. Then FaultExplainer, scheduling part D and the fixes.
2. **API use for E9.** Can the 450 replay prompts go to a frontier model API? They hold synthetic boiler data and public Cranfield and TEP data. Which API?
3. **GPT-4o for F4.** Pay for it?
4. **Meter.** Which one, and when it gets ordered?

## Order at a glance
| week | `bc-build` (here) | `bc-runs` (24 GB Mac and board) |
|---|---|---|
| 1 | E1–E4, F1, F2, then the E6–E8 tools | S1; E5 once its rules are agreed |
| 2 | E9, F4, X1 | E6–E8, F3, S2 |
| 3–4 | scoring, energy method | S3, X2, P2–P3 (with the meter) |
| 5–7 | writing (G1 if needed) | G2 if needed |
