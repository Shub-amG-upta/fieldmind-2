# 01. bev-decider-3: architecture

bev-decider-3 = **multi-agent v3, unchanged, plus one new model agent: the decider.** With the decider switched off,
the code publishes exactly what v3 publishes (checked by the teammate on 20 mock runs, 3,440 ticks, 0 differences).
So the measured difference between the two is the decider.

---

## 1. The model: bev-decider-0.4B ("System One")

| | |
|---|---|
| source | huggingface.co/avbiswas/bev-decider-0.4B (licence CC-BY-NC) |
| structure | the **first 20 transformer layers of Qwen3-0.6B** (the "backbone") plus a small **decision head** |
| parameters | backbone 470,202,368 (including the 155,582,464-parameter token embedding); head 7,364,608 |
| what it returns | **one probability per option**, from one forward pass. It generates no text |
| question types it supports | `choice` (pick one of N options; used here), `noul` (yes / no), `score` |
| training domain | general decision tasks such as support routing and policy questions. **Not boilers:** it is used zero-shot here |

"System One" vs "System Two": a language model like Llama writes its answer token by token (deliberate,
generative). A System One model maps the input straight to a decision (fast, no generation).

## 2. On the board: `bev-decide`

| | |
|---|---|
| program | `bev-decide`, a small C++ HTTP server written by the team: bev-decider's token layout and decision head, with the transformer run by llama.cpp |
| llama.cpp | the **same pinned build as the Llama lanes** (b11371, commit 99b95488), linked against the libraries already on the board: no new libraries were installed |
| build | Android NDK r29, Clang 21.0.0, in the same Snapdragon toolchain container as llama.cpp's board build |
| weights | backbone GGUF quantized to **Q8_0** for every matrix (505,674,304 bytes; 141 Q8_0 matrices, 81 small F32 norm tensors); head as fp32 (29,458,432 bytes) |
| placement | `--device HTP0 -ngl 99`: startup log shows **`offloaded 21/21 layers`** (20 layers + output) |
| HTP0 buffers | model **476.58 MiB**, KV cache **320.00 MiB**, compute **298.75 MiB** |
| context | `n_ctx 4096`, up to 18 sequences per request (16 options + prompt + answer) |
| endpoint | port **8082**, `POST /v1/systemone`, `GET /health`, forwarded to the laptop over adb like the Llama lanes |
| integrity | the binary and the three model files are sha256-checked on laptop and board before the server may start (same rule as the Llama models) |

The KV buffer is consistent with the model's shape:
2 (K and V) × 20 layers × 8 KV heads × 128 dims × 4,096 context × 2 bytes = 335,544,320 B = 320.00 MiB.

**How one decision is computed** (from the server's design):
1. The **state and question** are prefilled once, in sequence 0.
2. **Each option** is prefilled in its own sequence, continuing from the prompt's cached positions. The prompt's KV
   cache is shared, not recomputed per option.
3. An **answer sequence** follows the prompt and all options.
4. The server reads **hidden states**, not logits. The decision head turns them into one probability per option.
5. **No token is generated.** The whole call is prefill plus the head.

The model card says option order can't change the answer. That was not tested on the board (the conformance check,
which includes a shuffle test, was not run).

## 3. In the agent

```
 sensors → sensor agent (facts) → triage → retriever + belief ─┬→ scheduler → NPU lane :8080  Llama 3B: water + heat diagnosticians
                                                              │             CPU lane :8081  Gemma 1B: verifier
                                                              └→ scheduler → decider lane :8082  bev-decider (HTP0)   ← NEW
                                     all answers → gate (checks) → merge rule hybrid → published assessment
```

| aspect | how it works | measured |
|---|---|---|
| when it is called | only when its evidence changes: the offered cases, the signature, the open findings | **633 calls on 1,053 non-quiet ticks** (60%), 12 episodes |
| the state it sees | the tick's facts as short lines (at most 9), e.g. `[RATE/WATCH] drum_level -0.50 %/min sustained 3 min`. Facts only, no raw sensor readings | mean prompt 398 tokens |
| the question | fixed: "Which root cause best explains the plant facts?" | – |
| the options | belief's top 3 causes, then the Llama diagnosticians' top 3 of the same tick that belief's list doesn't hold; each option is "case ID: root cause text" | 2 options: 3 calls; 3: 106; 4: 261; 5: 192; 6: 71 |
| checking | the gate accepts the answer only if every offered case has a probability in [0, 1] and nothing else is named | **0 rejected, 0 failed** of 633 |
| effect on the ranking | its top pick gets +0.35 and its second +0.175 (log-odds), **added to the Llama diagnosticians' bonus; the sum is capped at 1.2 per case per episode** | – |
| inside `hybrid` | belief **weak or tied**: the Llama picks lead the ranking, and the decider can't change the top cause. Belief **clear**: belief + bonuses decides, so the decider can move it | – |
| guards | never pushes the three "filler" cases (flat on every sensor: RCA-09, RCA-10, RCA-15); never writes belief; plant state and alarms are always computed by code | flat-case picks 18% of calls, all blocked by the guard |
| priority | P3 (background) in the scheduler | – |

## 4. What runs where (bev-decider-3 runs)

| process | port | model | compute unit |
|---|---|---|---|
| `llama-server` | 8080 | Llama 3.2 3B, Q4_0 + Q8_0 embedding | Hexagon NPU (HTP0) |
| `llama-server` | 8081 | Gemma 3 1B, Q4_0 | Kryo CPU, 6 threads |
| **`bev-decide`** | **8082** | **bev-decider 0.4B, Q8_0** | **Hexagon NPU (HTP0), shared with :8080** |
| FieldMind agent | – | – | laptop (Python), calls the board over USB |

**Two processes on HTP0 at once worked:** no errors, and the Llama diagnostician's median call didn't get slower
(3.05 s in v3, 2.98 s in bev3).

## 5. What was not verified

- **Conformance:** that the board's answers match the original PyTorch model's (token ids, top choice,
  probabilities, option-shuffle drift) was not run. The board runs show it works; they don't show it matches the
  original.
- **The model's domain:** it was trained on non-industrial decision tasks; it was not fine-tuned for boilers.
- **Real-time mode:** all runs were lockstep (each tick waits for its model calls), like every accuracy benchmark in
  the deck.
