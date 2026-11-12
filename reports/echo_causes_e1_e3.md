# Echo causes E1–E3 (saved data, no model calls) — report

## Status
DONE. E1 (is the true case in the list?), E2 (voting over the 4 saved orders) and E3 (shuffled deviations against a
random other line) were run on set R and the five replay arms. They were run under the agreed pre-registration
(`reports/echo_causes_prereg.md`, A1, committed at `7d86cf4` before these runs).

**What the numbers are:**
- **E1** reads only the requests (the retrieval layer).
- **E2 and E3** read the existing laptop replays of the models (`results/echo/R_*.jsonl`, the five arms of
  `reports/echo_replay.md`). They are **not NPU results.**

Plant data: synthetic (boiler), real (Cranfield), public (TEP). The scores are in `results/echo/scores/e1_ceiling.json`,
`e2_vote.json` and `e3_hint.json`.

95% intervals: 2,000 resamples of episodes, seed 20261111.

## Results

### E1. Is the true case even in the list? (scored requests)
| plant | n | true case in list | true group in list | line 1 is the true case | line 1 in the true group |
|---|---|---|---|---|---|
| pooled | 439 | 0.547 [0.417, 0.681] | **0.611** [0.492, 0.738] | 0.362 | 0.401 |
| boiler | 149 | 0.664 | 0.778 | 0.557 | 0.651 |
| Cranfield | 141 | 0.355 | **0.355** [0.232, 0.549] | 0.184 | 0.184 |
| TEP | 149 | 0.611 | 0.685 | 0.336 | 0.356 |

Where the true case sits (pooled), as the share of requests with it at each line:

| line 1 | line 2 | line 3 | line 4 |
|---|---|---|---|
| 0.362 | 0.107 | 0.061 | 0.016 |

**Verdict by the agreed rule: retrieval-limited.**
- The rule is "group < 0.6 pooled, **or** < 0.5 in any plant". Cranfield (0.355) trips it.
- Pooled (0.611), boiler and TEP are above it.
- On Cranfield the true case is missing from 64.5% of the lists, so no reader can exceed 0.355 there.
- Pooled, the most a perfect reader could add over line 1 is 0.611 − 0.401 = **0.21** (group).

### E2. Voting over the 4 saved orders (group, minus line 1)
| arm | vote − line 1 | Borda − line 1 | the original pick − line 1 |
|---|---|---|---|
| 3B 4-bit | −0.137 [−0.240, −0.046] | −0.184 | 0.000 |
| 3B 8-bit | −0.098 [−0.186, −0.022] | −0.143 | +0.016 |
| 3B 16-bit | −0.100 [−0.189, −0.024] | −0.150 | +0.014 |
| Qwen 7B | +0.002 [−0.076, 0.078] | −0.007 | −0.009 |
| Llama 8B | −0.005 [−0.092, 0.065] | −0.016 | −0.016 |

- **Verdict: voting helps no arm.**
- For the 3B the vote is below line 1. This was predicted before the run (the 4 orders are unbalanced, so a copier's
  vote is near random) and is not evidence that voting harms a reader.

### E3. When the model leaves line 1 in a shuffled order (group)
| arm | deviations | right | a random other line | difference | difference, exact case |
|---|---|---|---|---|---|
| 3B 4-bit | 25 | 0.560 | 0.293 | +0.267 [−0.037, 0.556] | +0.240 [−0.056, 0.556] |
| 3B 8-bit | 110 | 0.418 | 0.294 | **+0.124 [0.051, 0.199]** | +0.085 [0.008, 0.155] |
| 3B 16-bit | 105 | 0.409 | 0.284 | **+0.125 [0.039, 0.204]** | +0.084 [−0.002, 0.159] |
| Qwen 7B | 462 | 0.455 | 0.322 | **+0.132 [0.066, 0.207]** | +0.120 [0.052, 0.190] |
| Llama 8B | 556 | 0.401 | 0.306 | **+0.095 [0.022, 0.170]** | +0.098 [0.028, 0.170] |

**Verdict: "reads a little" for the 8-bit 3B, the 16-bit 3B, Qwen 7B and Llama 8B** (≥ +0.05 and the interval excludes 0).
- The 4-bit 3B is **undetermined**: it leaves line 1 only 25 times, and its interval includes 0.
- The 16-bit 3B's exact-case interval just includes 0. Its group interval does not.

## What this means (stated as tested, nothing beyond)
1. **The models carry some signal from the evidence.** With the order shuffled, their own picks beat a random other line
   by about 0.10–0.13. This holds even for the same 3B at 8 and 16 bits.
2. **That signal is weaker than the retrieval code's ranking.** The agreed first replay found that, in the original
   order, their departures from line 1 are not better than line 1 itself. So the code's order is a better guess than
   the model's departures from it.
3. **On Cranfield, retrieval is the ceiling.** The true case is absent from 64.5% of the lists. Better reading cannot
   fix that; better retrieval could.
4. **For the board's 4-bit file we cannot tell**, because it almost never leaves line 1. Whether 4-bit removes the weak
   signal, or only hides it under copying, is not answered by these data.

## Verification
| step | result |
|---|---|
| ran the module | `echo_causes.py score ceiling | vote | hint --bootstrap 2000`; outputs above |
| self-tests | `tests/test_echo_causes.py` 15 passed |
| independent re-derivation | (1) E1 true case in list, pooled: 0.547 (tool) vs 0.5467, by a separate regex over the raw prompts; difference 0. (2) E3 Qwen 7B, exact difference: 0.120 (tool) vs 0.1201, from the raw replay lines with a separate parser; difference 0 |
| mutation check | 9 of 9 caught (commit `a6f561b`; 2 needed an added test) |

## Direction checks
| claim | expected | measured | |
|---|---|---|---|
| a copier's vote over unbalanced orders is below line 1 | negative (recorded before the run) | 3B −0.10 to −0.14 | OK |
| a model that ignores content matches a random other line | difference ≈ 0 | not applicable: no arm is that model; tested on fakes | – |

## Constants introduced
None. All thresholds are from the agreed pre-registration.

## Numbers that changed
None. This is the first run of E1–E3.

## Disagreements recorded, not resolved
- **"Reads the cases: no" (first replay) against "reads a little: yes" (E3).** These measure different things:
  - the first is position invariance ≥ 0.8 over 4 orders, and departures from line 1 compared with **line 1**;
  - E3 compares departures in **shuffled** orders with a **random other line**.

  Both can hold: a weak signal, much weaker than the code's ranking. Both are reported.
- **The plan's "7B hint" (0.42 vs 0.29)** is now re-measured under a rule: +0.132 [0.066, 0.207]. It holds.

## Blocked / needs a decision
- **The E1 verdict is "retrieval-limited", because of Cranfield alone.** The paper can:
  - (a) report it per plant: Cranfield retrieval-limited, boiler and TEP with room for a reader;
  - (b) treat Cranfield's retrieval as a separate finding.

  Both report the same numbers. Which framing to lead with is a writing decision.
- **Whether to look at why Cranfield's lists miss the true case.** That is a retrieval question in the agent's case
  library, and changing it would touch case data (needs a pre-registered rule and advisor sign-off, CLAUDE.md).

## What I could not verify
- **Whether "group" credit flatters the E3 signal.** The exact-case differences are also positive, with intervals
  excluding 0, for the 8-bit 3B, 7B and 8B. The 16-bit 3B's exact-case interval just includes 0.
- **Whether the same weak signal exists on the NPU.** All of E2 and E3 are laptop replays.
- **Whether the 4-bit file has the signal.** There are too few departures from line 1. E6 (relabel) and E7 (prior) may
  show more, since they read the model's preference directly.
