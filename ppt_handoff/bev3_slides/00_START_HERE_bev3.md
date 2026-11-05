# Three new slides: bev-decider-3 (a System One decision model on the NPU)

**Who this is for:** the Claude chat that already holds the FieldMind deck. This pack adds **three slides** about the
latest variant, **bev-decider-3**: multi-agent v3 plus a small "System One" decision model running on the Hexagon
NPU next to the Llama lane. The audience is unchanged: **Qualcomm engineers**, who care most about how the NPU is
used, measured speed, scheduling and memory.

Read this file first, then `01_bev3_architecture.md`, `02_bev3_data_guide.md` and
`03_decision_model_efficiency.md`. Every number below comes from the board runs in `data/`.

---

## Where the three slides go

Put them **after the v3 results slide** (in the existing outline that is after "v3 results on ten episodes"; before
"NPU utilisation and headroom"). They continue the story: v3 is the best multi-agent version, and the next question
was whether a different kind of model, one that decides instead of writing, can use the NPU better.

Use the deck's existing colours: v3 is blue, bev-decider-3 is teal (#17a589), belief (code only) is grey.

---

## Slide A: Architecture

**Title (suggested):** "Adding a System One decider on the NPU"

**Key message:** a third model agent joins v3. It doesn't write text. It reads the facts and the candidate causes,
and returns one probability per cause in a single forward pass, served by its own small server on the Hexagon NPU,
beside the Llama lane.

**Content:**
- What bev-decider-0.4B is:
  - the first 20 layers of Qwen3-0.6B plus a small decision head;
  - Q8_0 GGUF of 505.7 MB plus a 29.5 MB head;
  - returns probabilities, no generated tokens.
- How it is served:
  - `bev-decide`, a C++ server built on the **same llama.cpp build** as the Llama lanes (b11371);
  - port 8082;
  - **21/21 layers on HTP0** (HTP0 buffers: model 476.6 MiB, KV 320 MiB, compute 298.8 MiB).
- How it fits in the agent:
  - called only when its evidence changes (633 calls on 1,053 non-quiet ticks);
  - offered belief's top 3 and the Llama diagnosticians' top 3 (2–6 options);
  - the gate checks its answer;
  - its pick becomes a small capped bonus in v3's `hybrid` merge rule;
  - it never writes belief, and never pushes the three "filler" cases.
- On the board: **three model servers, two of them sharing the Hexagon NPU** (Llama 3B on :8080, bev-decide on :8082),
  plus Gemma 1B on the CPU (:8081).

**Visual:** `figures/05_flow_bev_decider_3.png` (or the `.svg`), the full flow with the new decider lane in teal.
Optionally `figures/06_board_deployment.png` as an inset (what runs where on the board).

**Speaker notes:** "The Llama diagnosticians generate a short JSON answer token by token. bev-decider answers the same
kind of question with probabilities from one forward pass. It runs as a third server on the same NPU. We built the
server against the exact llama.cpp build already on the board, so no new libraries went onto the board."

Details: `01_bev3_architecture.md`.

---

## Slide B: Results against v3

**Title (suggested):** "bev-decider-3 against v3: same speed class, no accuracy gain"

**Key message:** it ran cleanly on the board. There were 633 decider calls with 0 failures, no tick over budget, and
no slowdown of the Llama NPU lane. But it **did not improve accuracy**: group top-1 was 0.680 against v3's 0.703.
Replaying the same run without the decider gives 0.707. So the drop is the decider's doing, not noise.

**Table (from `data/bev3_vs_v3_summary.csv`, 10 fault episodes unless marked):**

| | v3 | bev-decider-3 | belief alone |
|---|---|---|---|
| group top-1 (mean of episodes) | **0.703** | 0.680 | 0.575 |
| exact top-1 | **0.600** | 0.571 | – |
| right group in top 3 | **0.908** | 0.890 | – |
| right before the trip | **0.757** | 0.752 | – |
| first right after fault onset | 9.6 min | **9.5 min** | – |
| ticks over the 30 s budget (12 episodes) | 0 | 0 | – |
| wall time, 12 episodes | **1,947 s** | 2,177 s (+12%) | – |
| decider calls (failed / rejected) | – | 633 (0 / 0) | – |

**One sentence on why:** on these boiler faults, bev-decider's pick is right less often than Llama's (0.47 against
0.64). It is good on feed-water and fuel faults, but poor on tube leaks and high-CV coal, where it often picks
wrong causes or filler cases. Because its bonus shares a cap with Llama's, its wrong picks can outweigh Llama's right
ones. Mechanism details: `02_bev3_data_guide.md` section 5.

**Visual:** `figures/40_bev3_vs_v3_accuracy.png` (per-episode bars plus means, including the "decider removed" replay).
Backup: `figures/30_decider_effect.png` (use the top panel only: bev-decider-3) or
`figures/31_decider_picks_by_family.png` (left panel).

**Speaker notes:** "Accuracy is close to v3, but not better: the decider fixed 1 tick and broke 33. We measured that
inside the same run by replaying its saved answers without the decider, so model run-to-run noise is excluded. The
model was trained on customer-support routing, not boilers, and it shows on two of the four fault families."

---

## Slide C: Why decision models help efficiency

**Title (suggested):** "Deciding instead of generating: a prefill-only workload for the NPU"

**Key message:** a language model spends most of its NPU time **writing** (decode), one token at a time. A decision
model only **reads** (prefill), which is the batched matrix work the NPU is fastest at. One decision took 0.37 s
against 3.15 s for one Llama diagnosis. The saving only becomes real when a decision model **replaces** a generating
step. In bev-decider-3 it was added alongside, so total model time went up.

**Content (measured, `data/model_call_costs.csv`):**

| one model call | prompt | answer | time spent decoding | mean call |
|---|---|---|---|---|
| single agent diagnosis, Llama 3B, NPU | 1,874 tokens | 166 tokens | 81% | 15.06 s |
| v3 diagnosis, Llama 3B, NPU | 722 tokens | 34 tokens | 70% | 3.15 s |
| **bev-decider decision, 0.4B, NPU** | 398 tokens | **0** | **0%** | **0.37 s** |

- Prefill speed on the NPU: 785–843 tok/s for Llama 3B, **1,607 tok/s** for bev-decider. Decode: 15.6 tok/s for Llama.
- Other benefits, all measured:
  - **No format failures:** it returns numbers, not text; 0 failed and 0 rejected answers.
  - **A probability for every option:** a graded confidence signal, where Llama returns a ranked list.
  - **Shares HTP0 without slowing Llama:** median diagnosis 3.05 s without the decider, 2.98 s with it.
  - **Predictable cost:** median 0.37 s, inter-quartile range 0.34–0.40 s. That suits the scheduler's predicted-finish rule.
- Honest cost in this build: total model time was 1,794 s for v3 and 1,981 s for bev3 (+187 s). Llama's answer tokens
  were unchanged (17,284 and 17,360).
- Where it would cut decode: by replacing a job whose answer is really a choice.
  - The diagnosticians: a ranked list of case IDs.
  - The verifier: pass or fail.
  - Shown as a direction, **not a measured result** (see `03` for the arithmetic and why accuracy blocks it today).

**Visual:** `figures/41_call_time_split.png`: per-call prefill/decode split on the left, total model time for v3
and bev3 on the right. Alternative: `figures/26_call_latency.png`.

**Speaker notes:** "For an NPU, the expensive part of an LLM agent is decode. A decision model turns a generation job
into a prefill-only job, about 8× cheaper per call here. In this version we only added it, so we paid for it. The next
step is to let it replace a generating job, once its accuracy on our task is good enough."

Details: `03_decision_model_efficiency.md`.

---

## Rules for these slides (same as the rest of the deck)

1. **Only measured numbers.** Every number is in `data/` or these markdown files. Section C's "what if it replaced
   the diagnosticians" is arithmetic, and must be labelled as a projection, not a result.
2. **Energy was not measured.** Don't state power or energy, and don't infer them from time.
3. **Say "on the episodes measured".** Ten fault episodes from the reporting set, one run each. v3's design was chosen
   on these same episodes.
4. **The board port of bev-decider was not checked against the original model** (the planned "conformance" check
   was not run). Don't claim the board answers equal the original PyTorch model's. You may say it runs on the board.
5. **Tick and wall times are laptop plus board times;** model call times are board times.
6. All plant data is simulated; the system is advisory only.

---

## Files in this pack

| file | what |
|---|---|
| `00_START_HERE_bev3.md` | this brief: slide specs, numbers, rules |
| `01_bev3_architecture.md` | the model, the server, how it fits into v3, what runs where on the board |
| `02_bev3_data_guide.md` | every data file and figure, every metric, how to read them, pitfalls |
| `03_decision_model_efficiency.md` | decode against prefill, what System One saves and what it cost here |
| `data/bev3_vs_v3_summary.csv` | headline comparison (10 fault episodes, first 4, all 12) |
| `data/bev3_vs_v3_per_episode.csv` | every metric per episode for v3 and bev3, with the decider's own stats |
| `data/model_call_costs.csv` | per agent: calls, tokens, prefill / decode seconds, tok/s |
| `data/decider_picks_by_family.csv` | how often the decider, Llama and belief pick the right cause, by fault family |
| `data/decider_options_per_call.csv` | how many options each decider call had |
| `data/decider_trigger.json` | decider calls against non-quiet ticks |
| `figures/05_flow_bev_decider_3.png` / `.svg` | architecture flow (slide A) |
| `figures/06_board_deployment.png` | what runs where on the board (slide A inset) |
| `figures/03_flow_multi_v3.png` | v3 without the decider, for a side-by-side if wanted |
| `figures/40_bev3_vs_v3_accuracy.png` | slide B main chart |
| `figures/30_decider_effect.png`, `31_decider_picks_by_family.png` | slide B backups (top / left panel = bev-decider-3) |
| `figures/14_bench_v3.png`, `16_bench_bev3.png` | per-benchmark summaries (backup slides) |
| `figures/33_timeline_A01.png`, `34_timeline_B01.png` | tick-by-tick strips (backup) |
| `figures/41_call_time_split.png` | slide C main chart |
| `figures/26_call_latency.png` | slide C alternative: call time by agent and model |

Some backup figures also show **bev-decider-2**, an earlier variant (v2 prompts, `nudge`, Llama on both lanes) that
scored 0.592. These slides are about bev-decider-3; mention bev-decider-2 only if asked.

**Upload order if limited:** the four markdown files, then `data/bev3_vs_v3_summary.csv` and
`data/model_call_costs.csv`, then the figures `05_flow_bev_decider_3.png`, `40_bev3_vs_v3_accuracy.png`,
`41_call_time_split.png`, then everything else.
