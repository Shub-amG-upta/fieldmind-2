# 03. Why decision models can make on-device agents more efficient

## 1. The two phases of a language-model call

| phase | what happens | shape of the work | on the Hexagon NPU (measured) |
|---|---|---|---|
| **prefill** | the model reads the whole prompt at once | large matrix-matrix products over all prompt tokens in parallel: the work the NPU's matrix engine is built for | Llama 3.2 3B: 785–843 tok/s in our runs (986 in screening) |
| **decode** | the model writes the answer, **one token at a time** | each token needs the whole model read from memory for one small step, so it is memory-bound and sequential | Llama 3.2 3B: **15.6 tok/s** |

So **answer tokens cost roughly 50× more time than prompt tokens** on this board (785 against 15.6 tok/s). An LLM
agent's time on the NPU is dominated by what it writes.

Measured split of one call (`data/model_call_costs.csv`, mean per call):

| call | prompt | answer | prefill | decode | decode share | whole call |
|---|---|---|---|---|---|---|
| single agent diagnosis, Llama 3B, NPU | 1,874 | 166 | 2.80 s | 12.21 s | **81%** | 15.06 s |
| v3 diagnosis, Llama 3B, NPU | 722 | 34 | 0.92 s | 2.18 s | **70%** | 3.15 s |
| v3 verification, Gemma 1B, CPU | 400 | 25 | 1.18 s | 0.67 s | 36% | 1.89 s |
| **bev-decider decision, 0.4B, NPU** | 398 | **0** | 0.25 s | **0 s** | **0%** | **0.37 s** |

The project already cut decode a lot by moving from the single agent to v3:
- answers as line numbers;
- a 60-token cap;
- a grammar.

Even so, 70% of a v3 diagnosis is still decode.

## 2. What a decision model changes

A System One model like bev-decider answers a **choice** ("which of these causes?") without writing anything:

1. **No decode phase.** The call is prefill plus a small head. That turns a generation job into a prefill-only job,
   the kind of work the NPU does best. bev-decider prefilled at **1,607 tok/s** on HTP0.
2. **About 8× cheaper per decision than a Llama diagnosis** (0.37 s against 3.15 s mean), with a smaller prompt
   (398 against 722 tokens).
3. **Predictable cost.** Median 0.37 s, inter-quartile range 0.34–0.40 s, no answer-length variation. The scheduler
   can predict finish times exactly, which matters for an earliest-finish placement rule.
4. **No format failures by construction.** No text means no JSON, no grammar and no parsing: 0 failed and 0
   rejected answers in 633 calls.
5. **A full probability distribution.** The agent gets a confidence for every option, not just a ranked list.
6. **It shares the NPU cleanly.**
   - It ran on HTP0 in a second process beside Llama's server: 476.6 MiB model, 320 MiB KV, 298.8 MiB compute.
   - Llama's calls didn't slow down (median diagnosis 3.05 s without the decider, 2.98 s with it).
7. **Shared-prompt evaluation.** The prompt is prefilled once and every option continues from its cached state, so
   adding an option costs only that option's tokens.

## 3. What it cost in bev-decider-3, and why

In bev-decider-3 the decider was **added alongside** the Llama diagnosticians, not instead of them:

| 12 episodes | v3 | bev3 |
|---|---|---|
| Llama diagnostician answer tokens | 17,284 | 17,360 (unchanged) |
| decider calls / answer tokens | – | 633 / 0 |
| total model-call time | 1,794 s | 1,981 s (+187 s) |
| wall time | 1,947 s | 2,177 s (+12%) |
| group top-1 (10 fault episodes) | 0.703 | 0.680 |

So in this build it **added** prefill work and **did not remove** any decode. It also didn't improve accuracy:
its picks are right 47% of the time against Llama's 64%. The efficiency benefit is real per call, but the system only
gains it when a decision model **replaces** a generating step.

## 4. Where it would replace decode (direction, not a result)

| generating job today | its answer is really… | decision-model form | measured decode it would remove (12 episodes) |
|---|---|---|---|
| water and heat diagnosticians | a ranked choice among 3–6 candidate cases | `choice` | 17,284 tokens, 1,111 s of decode (v3) |
| verifier | pass / fail per claim | `noul` (yes / no) or `score` | 2,501 tokens, 67 s of decode (v3, CPU) |

**Projection (arithmetic only, label it as such on any slide):**
- 509 diagnosis calls at the decider's measured 0.37 s median ≈ 188 s, against 1,605 s measured for v3's
  diagnosticians.
- This was **not run**. On today's evidence it would also **lower accuracy**, because the decider's picks (0.47) are
  less accurate than Llama's (0.64) and below belief's (0.51) on these faults.

What would need to be true first:
1. a decision model that is accurate on this domain, for example one fine-tuned on boiler fault cases;
2. the board port checked against the original model (conformance);
3. a merge rule that gives the decider its own cap, so it can't cancel the diagnosticians' correct pushes.

## 5. One-line takeaways for the slide

- "On the NPU, writing is the expensive part: 70–81% of a Llama call is decode."
- "A decision model decides without writing: 0 decode tokens, 0.37 s per decision, on HTP0 beside Llama, with no
  slowdown to Llama."
- "The saving is real only when it replaces a generating step. Added on top, as in bev-decider-3, it cost +12% time
  and didn't improve accuracy."
