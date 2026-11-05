# FieldMind on the QIDK: what we measured, what we found, and the road to a paper

Analysis of every board result on branch `bev-ideas-results` (runs by Pranav, 8 to 19 October 2026), written
20 October 2026. Board: Qualcomm QIDK (SM8650). Llama 3.2 3B Q4_0 on the NPU, Gemma 3 1B Q4_0 on the CPU,
bev-decider-0.4B Q8_0 on the NPU. Agent code ran on the laptop; only model calls ran on the board. **All plant data is
synthetic.** No number below comes from the mock backend. Every number was recomputed from the saved run files.

---

## 1. The short version

1. **The multi-agent design already cuts decoding about 10× against the single agent, and is more accurate.** On the
   same episode (`ep_A01`): 194.7 → 18.3 decode tokens per tick, 2,103 → 196 s of model time, group top-1
   0.557 → 0.887.
2. **Letting bev-decider write the citations (`explain`) cuts Llama's decoding another 71% on the dev set.**
   - Decode tokens per tick fall 10.68 → 3.06; wall time falls 32% (1,350 → 913 s); CPU time across the model
     servers falls 57%.
   - Group accuracy holds: 0.759 → 0.772, within noise.
   - The cost: exact top-1 falls 0.646 → 0.605, almost all of it on one episode (C02).
3. **`clear_skip` (no bev at all) cuts 15% of Llama calls for free.** 406 → 343 calls, no measurable accuracy change.
   This matches the saving predicted before the run.
4. **bev-decider is fast, but its judgement on our questions is poor.**
   - It reads about 1,430 tokens/s on the NPU, against Llama's 849, and answers in 0.3-0.7 s.
   - It says "yes, needed" to 836 of 837 actions.
   - It says "none of these causes" on 97% of questions, including obvious library faults.
   - It labels every engineer note "not about this boiler", including the notes that name the root cause.
   - Picking the cause on hard ticks, it is right 38% of the time, against Llama's 56%.
   - Its best use is the narrow one: choosing the supporting fact for a cause Llama already chose.
5. **The board is less repeatable than the pass rule assumed.**
   - Llama gave a different reply to the identical prompt in **16%** of calls (61 of 381) between two baseline runs.
   - The chip reached **about 97 °C** in every arm.
   - Accuracy differences under about 0.02 are noise, and the pass rule's noise estimate (|A1 − A2| = 0) is too small.
6. **For a paper:** the strongest claim we can already support is about *where the cost goes* on an edge NPU
   (decode, not prefill) and *how much of it can be moved to code or to a decision model* without losing group
   accuracy. Energy, repeated runs and the reporting set are the missing pieces (section 8).

---

## 2. What was run

| test folder | what | config | episodes | date |
|---|---|---|---|---|
| `single_6mark` | single agent baseline | single agent, Llama on NPU | 2 reporting (A01, N01) | 7 Oct |
| `multi_v3` | multi-agent v3 (the baseline design) | `v3.yaml`, merge `hybrid` | 12 reporting | 8 Oct |
| `multi_v3_livedemo` | v3 again, demo set | `v3.yaml` | 5 reporting | 8 Oct |
| `bev3_armB` | v3 + bev decider | `bev3.yaml` | 12 reporting | 8 Oct |
| `bev_armB` | nudge rule + bev decider (Llama on both lanes) | `bev.yaml` | 12 reporting | 8 Oct |
| `multi_nudge_6mark`, `multi_tiebreak_6mark`, `multi_v2_6mark`, `multi_nudge_6.1mark` | earlier merge-rule variants | various | 6 reporting | 7 Oct |
| `six_episodes` | fast config (merge `model`) | `fast.yaml` | 6 reporting | 12 Oct |
| `bevideas_shadow` | every bev idea asked, nothing used | `bev_ideas.yaml` + shadow | 10 dev | 19 Oct |
| `bevideas_A1`, `bevideas_A2` | baseline, twice | `bev_ideas.yaml` (= v3 + bev lane, all off) | 10 dev | 19 Oct |
| `bevideas_B_explain`, `_actions`, `_unknown`, `_verifier`, `_notes`, `_skip` | one bev idea on per arm | `bev_ideas.yaml` + `--bev` | 10 dev | 19 Oct |
| `v3_new`, `bev3_six`, `bev3_new`, `live_demo` | single episodes / demos / empty folders | – | – | – |

The `first` arm was not run: it needed a threshold choice, and the shadow data argue against running it (5.3).
**Dev quick set:** A01, A02, B01, B02, C01, C02, D01, D03 (faults) + N01, N02 (normal); C01 is the only held-out
case. **Reporting set:** `ep_*`; the project rule is to report on it, never to decide on it.

---

## 3. What we measured, and how far each number can be trusted

| quantity | how | status | trust |
|---|---|---|---|
| Root-cause accuracy (group top-1, exact top-1, held-out, belief alone) | evaluator on every tick from fault onset | **measured** | single runs; Llama's own run-to-run noise is about ±0.01-0.02 pooled and up to 0.06 on C01 (section 6) |
| Faithfulness, citation relevance, action precision / recall | evaluator | **measured** | as above. Under `explain` faithfulness scores bev's citations, so it is near 1 by construction |
| Decode and read (prefill) tokens per call, per agent | server-reported counts on every call | **measured** | exact |
| Model call time; server-side read and decode time | client wall clock; llama-server / bev-decide timings | **measured** | good; the chip ran hot (about 97 °C), so absolute times include throttling |
| bev's tokenize / transformer / head time | bev-decide's own timings | **measured** | good |
| Lane busy share | sum of call times / episode wall time | **measured** | good |
| CPU seconds and peak memory per model server | on-board sampler, 1 Hz | **measured** | good per process; the board-wide CPU load includes the sampler itself (about 0.76 core) |
| Chip temperatures | thermal zones, every second and before / after each episode | **measured** | good |
| Time per agent stage, per tick | blackboard step timer | **measured on the LAPTOP** | not board times: agent code runs on the laptop |
| Run-to-run repeatability | A1 vs A2, identical prompts | **measured** | only two baseline runs |
| bev's agreement with Llama / Gemma (shadow) | logged per answer | **measured** | agreement, not correctness, except where ground truth exists (5.3) |
| **Energy** | – | **NOT measured** | the board exposes no readable power supply to adb, so supply energy is empty. No estimate is made |
| **NPU utilisation (hardware counter)** | – | **NOT measured** | no counter readable without root / vendor tools; NPU work is shown as NPU-lane call time |
| Hard-path time on the board | – | **not measured** | needs the agent code on the board (Phase 4) |
| `first` on, `text_reader`, `rt_fallback` | – | **not run** | see 5.3 and 8 |
| bev ideas on the reporting set | – | **not run** | by design (decide on dev first) |

---

## 4. The architecture result (same episode, `ep_A01`)

| design | decode tokens / tick | read tokens | model calls | model time | group top-1 | exact top-1 |
|---|---|---|---|---|---|---|
| single agent (`single_6mark`) | **194.7** | 233,599 | 157 | **2,103 s** | 0.557 | 0.170 |
| multi-agent v3 (`multi_v3`) | **18.3** | 46,958 | 74 | **196 s** | **0.887** | **0.887** |
| v3 + bev decider (`bev3_armB`) | 18.3 | 76,701 | 146 | 231 s | 0.877 | 0.877 |

The multi-agent design (short JSON answers made of line numbers, side-split prompts, a call only when evidence
changes, code-first belief with a hybrid merge rule) is about **10.7× cheaper in decoding and model time** and more
accurate on this episode. This is one episode with one run each; the full 12-episode v3 set gives group top-1 0.752.
The single agent was only run on 2 episodes, so a full same-set comparison is still missing (section 8).

---

## 5. The bev ideas (dev quick set, 10 episodes, 1,380 ticks, 0 failed bev calls in every arm)

### 5.1 Headline per idea

| idea | decode / tick (A1 10.68) | wall s (A1 1,350, A2 1,498) | library group top-1 (A1 = A2 = 0.759) | exact top-1 (0.646) | pass rule as written | verdict |
|---|---|---|---|---|---|---|
| **`explain`** | **3.06 (−71%)** | **913 (−32%)** | 0.772 | **0.605** | pass | **keep; report the exact-top-1 cost** |
| **`clear_skip`** | **9.13 (−14.5%)** | 1,249 | 0.766 | 0.654 | pass | **keep** |
| `verifier` | 9.96 (Gemma removed) | 1,405 | 0.759 | 0.651 | pass | keep only as a cost saving; its judgement is unvalidated (5.3) |
| `actions` | 10.68 | 1,609 | 0.759 | 0.646 | formally passes (precision +0.008 vs a spread of 0) | **drop**: no real effect (5.3) |
| `unknown` | 10.72 | 1,708 | 0.770 | 0.654 | – | **drop**: not discriminative |
| `notes` | 10.53 | 1,444 | 0.759 | 0.646 | – | **drop**: removes the key notes |
| `first` | not run | – | – | – | – | **drop as built** (shadow: 38% vs Llama 56%) |

Held-out group top-1 (C01 only) moved between 0.451 and 0.549 across arms and between the two baselines
(0.451 / 0.510), so no held-out claim can be made from these runs.

### 5.2 Where the time and the CPU go

| arm | Llama (NPU) call time | Gemma (CPU) call time | bev call time | server CPU seconds, NPU / CPU / bev | total server CPU s |
|---|---|---|---|---|---|
| A1 | 1,211.7 s (lane busy 90% of wall) | 79.1 s | 0 | 1,839.7 / 419.5 / 0.4 | 2,259.6 |
| `explain` | **493.2 s** (54%) | 74.4 s | 279.0 s (31%) | **444.9** / 395.3 / 130.0 | **970.2 (−57%)** |
| `verifier` | 1,313.5 s | **0** | 32.2 s | 1,905.1 / **1.6** / 16.1 | 1,922.8 (−15%) |
| `clear_skip` | 1,105.8 s | 85.7 s | 0 | 1,608.1 / 454.0 / 0.4 | 2,062.5 (−9%) |
| `actions` | 1,259.6 s | 82.8 s | 197.1 s | 1,849.8 / 439.3 / 96.5 | 2,385.6 (+6%) |
| `unknown` | 1,297.1 s | 84.4 s | 246.5 s | 1,898.4 / 446.3 / 120.6 | 2,465.3 (+9%) |

- **Decode dominates Llama's cost on the NPU.**
  - In A1, decode was 849 of 1,212 s of Llama call time (70%).
  - Llama reads at 849 tokens/s but generates at 16.1 tokens/s (62 ms per token).
  - One generated token costs about 53 read tokens.
- **Decoding "on the NPU" still burns the CPU.** The NPU llama-server used 1.32 CPU cores on average over the
  episode, about 1.5 cores while it was busy. `explain` cut that process's CPU time by 76%. For an edge-scheduling
  paper this is a real, measured finding: NPU offload does not free the CPU during decode in this llama.cpp build.
- **Per diagnosis, `explain` takes about 1.9 s instead of 3.0 s** (Llama step 3.01 s → 1.22 s, plus bev 0.69 s; laptop
  step timer).

### 5.3 bev-decider as a model: speed and judgement

**Speed (measured):**

| request type | calls | read tokens / call | time / call | bev read rate | share of time in bev's decision head |
|---|---|---|---|---|---|
| `explain` (citations, separating case, notes) | 405 | 691 | 0.69 s | 1,431 tok/s | 27% |
| `actions` (yes/no per action) | 455 | 379 | 0.43 s | 1,284 tok/s | 28% |
| `unknown` (top 3 + none) | 812 | 292 | 0.30 s | 1,441 tok/s | 27% |
| `verifier` (yes/no per claim + contradiction) | 67 | 380 | 0.48 s | 1,172 tok/s | 29% |

bev reads about 1.7× faster than Llama on the same NPU and decodes nothing. Its small decision head (7.4M parameters)
takes over a quarter of every call: the obvious thing to optimise.

**Judgement (shadow run and on-arms):**

| question | what bev said | what that means |
|---|---|---|
| citation for a cause Llama chose (`explain`) | its fact was among Llama's own citations **77%** of the time | usable: a narrow, well-posed choice |
| which cause, on weak / tied ticks (`first`) | in the true group **38%**, against Llama's **56%** on the same 162 ticks; agrees with Llama 41%; higher confidence was not more often right (≥ 0.70: 27%) | not usable; no threshold fixes it |
| is this action needed (`actions`) | "yes" to 836 of 837 (P(yes) median 0.86, min 0.49) | strong yes-bias; no filtering power |
| none of these causes (`unknown`) | flagged on 97% of questions; 82-100% on library faults (median P(none) 0.64-0.97) | not discriminative |
| does the claim hold (`verifier`) | agreed with Gemma's verdict on **47%** of claims | coin-flip agreement; which is right is unknown |
| which side is the note about (`notes`) | "none" for every note, including "fcv on feed line not responding" (A01), "makeup consumption high" (B01), "new coal ... CV higher" (D01) | wrong; it removed the root-cause hints from every prompt |

**Pattern:** bev does well when the options are short, concrete and come from the prompt itself (pick a fact line).
It does badly when the question asks for domain judgement (is this action needed, does this note concern the water
side, is none of these right). That fits its model card: strongest on routing and policy questions, weakest on answer
verification (54.1%). The question wordings are ours and were never tuned. Rewording could change this, but it must
be designed on the dev set, signed off and pre-registered, not fitted to these results.

### 5.4 The bev decider (reporting set, one run each, 8 October)

| | v3 | v3 + decider (`bev3_armB`) |
|---|---|---|
| library group top-1 (12 episodes) | 0.752 | 0.718 |
| library exact top-1 | 0.600 | 0.571 |
| held-out group top-1 | 0.505 | 0.528 |
| decode tokens / tick | 9.42 | 9.43 |
| wall time | 1,841 s | 2,070 s |
| decider calls | – | 633, 0 failed, 0 rejected |

No benefit shows, and the decider adds 12% wall time. These are reporting-set single runs, so this is reported, not
decided; the pre-registered dev measurement of the decider was not done (`bev3_new` is empty). With Llama's 16%
reply variation, a −0.034 difference from one run is not conclusive either way.

---

## 6. What we found about the measurement itself

1. **Llama on the board is not deterministic.**
   - Between A1 and A2, 61 of 381 identical prompts (16%) got a different reply.
   - Every arm that sends Llama the same prompts shows the same rate (53-64 differing replies), so this is the
     board / runtime, not bev.
   - Pooled group top-1 happened to match between A1 and A2 (spread 0), but the `unknown` arm, which cannot change
     the ranking, moved it by +0.011. Real noise is at least that.
   - C01 alone moved 0.451 ↔ 0.510 between baselines.
2. **The chip ran at about 97 °C** (CPU and NPU zones) in every arm, so throttling is likely. Wall time differed by
   148 s (11%) between the two identical baselines. Only differences well beyond that (`explain` −32%) are clear.
3. **Our sampler was too expensive**: about 1,000 CPU seconds per arm (about 0.76 core). Per-process figures are
   unaffected, but board-wide load includes it. The next runs should sample every 5 s.
4. **Energy cannot be read from this board through adb.** A paper needs an external measurement (USB / bench power
   meter) or Qualcomm's profiling tools.
5. **The stage times are laptop times.** Hard-path timing on the board needs Phase 4.

---

## 7. What is good, what is weak

**Good (measured, solid enough to build on):**
- The single → multi-agent architecture result: an order of magnitude less decoding and model time, with better
  accuracy, on the same episode.
- The decode-vs-prefill cost structure on the NPU (16 vs 849 tokens/s, 70% of call time decoding), and the CPU cost of
  NPU decoding (about 1.5 cores busy).
- `explain`: −71% decode, −32% wall, −57% server CPU, group accuracy held. A clean, explainable mechanism ("generate
  the decision, select the evidence").
- `clear_skip`: −15% Llama calls from a code rule, no accuracy cost.
- Engineering quality: zero failed bev calls over thousands; switches-off identity is test-enforced; every claim
  traceable to run files.

**Weak or not yet shown:**
- bev's judgement on domain questions (`actions`, `unknown`, `notes`, `first`, and `verifier` agreement).
- Accuracy differences are within noise; only two baseline runs.
- Exact top-1 cost of `explain` (C02).
- No energy, no NPU counter, no board-side hard path, a single held-out case, synthetic data only.
- The single agent has only 2 episodes on the board.

---

## 8. How to move towards a paper

### 8.1 A framing the data supports

> *Decode is the cost on an edge NPU. How much of an industrial diagnostic agent's decoding can be removed, by
> architecture (short structured answers, code-first belief, call-on-change), by rules (skip calls that cannot change
> the result), and by delegating selection to a single-pass decision model, without losing diagnostic accuracy?*

This matches the project's research question (scheduling heterogeneous agentic LLM work across NPU / CPU / DSP under
offline, latency and power limits). The agent is the vehicle; the cost study is the contribution.

### 8.2 Claims available now, and what each still needs

| claim | evidence now | still needed for a paper |
|---|---|---|
| C1. The multi-agent architecture cuts decode and model time by about an order of magnitude against a single agent, with no accuracy loss | `ep_A01`: 194.7 → 18.3 decode/tick, 2,103 → 196 s, 0.557 → 0.887 | single agent on the same full episode set; 3+ runs each |
| C2. On the NPU, decode dominates (62 ms/token vs 1.2 ms/token read) and still occupies CPU cores | measured on every call and per process | energy per call (external meter); a second model size |
| C3. Selecting evidence with a decision model instead of generating it removes 71% of decode and 32% of wall time with group accuracy held | dev set, one run | 3+ runs per arm; reporting set run once; exact-top-1 cost explained (C02) |
| C4. A code rule removes 15% of calls at no cost | dev set, one run; matches the offline replay | repeats; reporting set |
| C5. Decision models are reliable for narrow, prompt-grounded selection but not for domain judgement | shadow agreement and ground-truth rates per question type | more question types, reworded and pre-registered; a second decision model (e.g. the 2B ones) |
| C6. Edge LLM runs are not repeatable (16% reply variation) and run hot: benchmark protocols must repeat | measured | report as a methodological finding |

### 8.3 Experiments to run next (in this order)

1. **Fix the sampler period** (1 s → 5 s) and buy or borrow a **USB power meter** for the QIDK supply. The headline
   metric of the project is energy per correct diagnosis, and it is still missing.
2. **Combined arm:** `explain` + `clear_skip` + `verifier`, plus the A baseline, **3 runs each**, on the dev quick set.
   This gives a real noise estimate and the stacked saving.
3. **Reporting set, once** (30 episodes): single agent, v3, and v3 + the combined arm. This is the table for the paper.
4. **Energy per correct diagnosis** for those three, from the power meter.
5. **The C02 exact-top-1 loss under `explain`**: inspect what Llama ranks first with the ranking-only prompt.
6. Optional: **reworded bev questions** for `notes` and `actions`, designed and pre-registered on the dev set, with
   human sign-off. If they still fail, that negative result is itself part of claim C5.
7. Optional, for generality (the advisor's suggestion): the same facts-to-decision pipeline on a public industrial
   dataset (Tennessee Eastman, PRONTO). This makes C5 a cross-domain claim.

### 8.4 Figures and tables the paper would need (all can be produced from saved runs)

- Cost breakdown per tick: prefill vs decode time, per lane, for single / v3 / v3 + bev.
- Pareto plot: decode tokens per tick (or energy) against group top-1, one point per arm, with run-to-run error bars.
- Per-question-type reliability of the decision model (the table in 5.3, with ground truth where it exists).
- Repeatability: reply variation for identical prompts; temperature traces.
- Board resource table (CPU seconds and memory per server process).

### 8.5 Threats to validity to state up front

Synthetic plant data; one board; one held-out case; laptop-side agent timing; thermal throttling; Llama
non-determinism; bev question wordings never tuned or validated by a domain expert; the decision model's own
published accuracy is the author's, not independently checked.

---

## 9. Files

- Board runs: `results/benchmarks/*` on branch `bev-ideas-results` (run files, summaries, resources, `RUN_LOG.md`).
- The comparison the runner made: `results/benchmarks/bevideas_B_skip/COMPARE_bevideas_A1.md` / `.html`.
- What was built and pre-registered: `reports/bev_ideas.md`; earlier designs: `reports/multi_v3_results.md`,
  `reports/bev_decider.md`.
