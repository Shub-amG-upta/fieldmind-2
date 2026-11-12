# Echo: what the model knows but does not say (4-bit vs 8-bit) — exploratory report

## Status
PARTIAL. **Exploratory analysis of saved runs, not pre-registered.** No new model call was made. It finds one effect
that replicates on the NPU, and it records two attempted fixes that failed. Nothing here is a paper result until a
pre-registered run confirms it (see "Blocked / needs a decision").

**Data used:**
- **Mac:** the E7 rows of `results/echo/prior_*.jsonl` (first-case-line token probabilities, original order and
  content-free), 8 arms. **Laptop replays, not NPU results.**
- **NPU:** the teammate's module-2 runs on branch `nd-paper` (`results/nd/m2_settings/A0_baseline`,
  `A0b_baseline_again`: Llama 3.2 3B Q4_0; `A3_q8_0`: the same weights at Q8_0). 100 boiler dev prompts × 5 calls,
  top-20 token probabilities, QIDK SM8650. These were collected for the nondeterminism study, not for this question.
- **Plant data:** synthetic (boiler), real (Cranfield), public (TEP). The effect below is on the **synthetic boiler
  only**.

**Code:** `reports/data/explore_hidden_signal/` (analysis scripts kept as a record; not a tested tool).

## The question
The model answers "line 1" almost always. Does its **probability** on line 1 still say whether line 1 is right?

**Measure:** AUC of p(line 1), read at the token that writes the first case line, against "the code's line 1 is in the
true group". 0.5 means the probability carries no information.

## Results

### 1. Same answers, different knowledge (Llama 3.2 3B, same weights)
| run | picks line 1 | AUC, all prompts | AUC, within episode | mean p(line 1) when line 1 is right / wrong |
|---|---|---|---|---|
| **NPU, 4-bit (Q4_0)** | 0.990 | **0.555** | 0.346 | 0.685 / 0.655 (gap +0.03) |
| NPU, 4-bit, second session | 0.990 | 0.558 | 0.340 | – |
| **NPU, 8-bit (Q8_0)** | 0.976 | **0.780** | 0.683 | 0.782 / 0.610 (gap +0.17) |
| Mac, 4-bit, boiler | 0.99 | 0.590 | 0.483 | – |
| Mac, 8-bit, boiler | 0.91 | 0.781 | 0.769 | – |
| Mac, 16-bit, boiler | 0.92 | 0.773 | 0.762 | – |

- **NPU, 8-bit minus 4-bit:** +0.225 [0.160, 0.298] resampling prompts; [0.067, 0.366] resampling the 8 episodes.
- **Noise floor** (4-bit against 4-bit again): +0.003 [−0.007, 0.014].
- **Shuffled labels:** 0 of 5,000 shuffles reach the 8-bit AUC. The 4-bit AUC is inside the shuffled range (share 0.19).
- **Mac, pooled over the three plants** (within-plant AUC, paired, 36 episodes): 8-bit minus 4-bit +0.119
  [0.023, 0.228]; 16-bit minus 8-bit −0.008.

**What it looks like in the prompts** (episode `dev_D01_high_cv_coal`, true case RCA-07, bed heating up):
- When line 1 is RCA-07 (signature: bed up), the 8-bit model puts 0.66–0.91 on line 1.
- When line 1 is a case whose signature contradicts the facts (RCA-11, tube leak, bed down), the 8-bit model's
  probability falls to 0.35–0.57 on most ticks.
- The 4-bit model stays at 0.54–0.84 in both situations.

### 2. Controls
| control | result |
|---|---|
| number of case lines | AUC 0.48 (no information) |
| content-free prior on line 1 | AUC 0.46–0.54 for every arm (no information) |
| within lists of 2, 3 and 4 lines (8-bit, Mac) | 0.83 / 0.75 / 0.87 |
| requests with an engineer's note / without (8-bit, Mac) | 0.74 / 0.84: **not driven by the notes** |
| **code-side: does the code's belief top-1 equal line 1?** | **AUC 0.842 (Mac boiler), 0.848 (NPU prompts)** |
| within "belief disagrees with line 1" (NPU, n = 50) | 4-bit 0.52, 8-bit 0.75 |

- **A code-side signal is as strong as the best model.** On the boiler, when the code's belief and its retrieval agree,
  line 1 is right on 0.96 of requests (n = 75); when they disagree, on 0.34 (n = 74).
- **The 8-bit model still knows more than that line.** Inside the disagreement cases its AUC is 0.75 on the NPU. The
  4-bit file is at chance there.

### 3. Where it does not hold
- **Cranfield and TEP:** every arm, at every precision, is near 0.5 (0.43–0.63). There is no signal to lose. On those
  plants the true case is often missing from the list (E1).
- **MMLU** (300 public questions, proxy = agreement of the other 3 rotations with the original answer): 4-bit 0.724,
  8-bit 0.730, 16-bit 0.713. **No 4-bit loss.** The proxy is not a probability, so it is a weaker test.
- **Other 4-bit models keep the signal:** Qwen3 1.7B Q4_0 0.725, Qwen 7B Q4_0 0.825, Llama 8B Q4_0 0.816 (Mac boiler).
  So "Q4_0 erases it" is shown for Llama 3.2 3B only. Their 8-bit versions were not run.

### 4. Does any model beat line 1 on the boiler alone? (own answer minus line 1, group, original order)
| arm | boiler | Cranfield | TEP |
|---|---|---|---|
| Llama 3B **4-bit** (Mac) | **+0.000 [0.000, 0.000]** | +0.000 | +0.000 |
| Llama 3B 8-bit (Mac) | +0.027 [0.009, 0.049] | +0.028 [0.005, 0.095] | −0.007 |
| Llama 3B 16-bit (Mac) | +0.034 [0.010, 0.068] | +0.014 | −0.007 |
| Qwen3 1.7B 4-bit | +0.047 [0.018, 0.095] | 0.000 | +0.007 |
| Qwen 7B 4-bit | +0.047 [−0.014, 0.120] | 0.000 | −0.074 |
| Llama 8B 4-bit | **+0.081 [0.062, 0.111]** | −0.028 | −0.101 [−0.277, 0.069] |
| Llama 3B 4-bit, **NPU** | −0.012 [−0.043, 0.000] | – | – |
| Llama 3B 8-bit, **NPU** | +0.010 [0.000, 0.040] | – | – |

- The pooled "no model beats line 1" hid a split by plant. On the boiler, the reading models gain a little.
- The gains are small, from 8 episodes, and exploratory.

### 5. Cost of 8-bit on the NPU (teammate's runs, laptop wall-clock per call)
| file | median | p90 |
|---|---|---|
| Q4_0 | 3.25 s, 3.21 s | 4.11 s |
| Q8_0 | 4.27 s (1.31×) | 4.97 s |

### 6. Attempted fixes that did NOT work
| fix | result |
|---|---|
| **Gate:** where belief and retrieval disagree, keep line 1 if p(line 1) ≥ a threshold, else take the belief's top case (threshold from the other episodes) | NPU: +0.081 [−0.016, 0.213] for 8-bit and the **same** +0.081 for 4-bit. The interval includes 0 and the gain does not depend on the model. **Not supported.** |
| **Rank-aware calibration:** replace the model's own prior with the measured rank prior (no tuned parameter) | Boiler: 8-bit +0.020 [−0.008, 0.047]; 4-bit −0.282. All plants: every arm ≤ +0.011. **Not supported.** |

No accuracy fix was found in the saved data.

## What this means (as tested, nothing beyond)
1. **For Llama 3.2 3B, the echo has two parts:** a preference for line 1 held before reading (0.80 at 8-bit, 0.88 at
   4-bit), and a response to the evidence. At 8 and 16 bits the response is real but too weak to overturn the
   preference. At 4 bits it is not distinguishable from zero.
2. **Accuracy cannot see this.** The answers are the same line (0.990 against 0.976 on the NPU) and the accuracy is
   the same.
3. **This revises `reports/echo_causes_e5_e8.md`,** which said compression "adds to" the copying. By the agreed rules
   that still stands. On this finer measure, for this model, 4-bit is the difference between a weak reader and none.

## Verification
| step | result |
|---|---|
| ran the module | every script in `reports/data/explore_hidden_signal/`; outputs quoted above |
| self-tests | none: these are analysis scripts, not a tool. `tests/test_echo_causes.py` and `tests/test_echo_test.py` (unchanged code): 36 passed |
| independent re-derivation | the effect was measured by two separate routes: (a) Mac rows through `debias.first_line_logprobs` (token strings); (b) NPU rows through token ids, with digit `d` = id 15 + d, checked against the reply text on 1,500 calls (0 mismatches). 8-bit boiler AUC 0.781 (Mac) vs 0.780 (NPU); 4-bit 0.590 vs 0.555 |
| mutation check | labels shuffled 5,000 times: mean AUC 0.501, range [0.38, 0.62], so the analysis returns chance when the labels carry nothing |

## Direction checks
| claim | expected | measured | |
|---|---|---|---|
| a prior read with no content carries no information | AUC ≈ 0.5 | 0.46–0.54 | OK |
| two sessions of the same file agree | difference ≈ 0 | +0.003 | OK |
| engineer's notes drive the signal | higher with a note | 0.74 with, 0.84 without | **FAIL: my hypothesis was wrong** |

## Constants introduced
None.

## Numbers that changed
| quantity | before | now |
|---|---|---|
| "no model beats line 1" (pooled) | best +0.02, within noise | unchanged pooled; **on the boiler** 8B +0.081, Qwen3 +0.047, 3B 8-bit +0.027, 3B 4-bit 0.000 |
| role of 4-bit | "not the cause, adds to it" | by the agreed rules, unchanged; on the probability measure, 0.78 → 0.56 for Llama 3B |

## Disagreements recorded, not resolved
- **Agent prompts against MMLU.** The 4-bit loss appears on boiler agent prompts and not on the MMLU proxy.
  - Possible reasons: long evidence-matching prompts against short recall questions; a probability against a consistency proxy.
  - Not tested.
- **Llama 3B against other models.** Qwen3 1.7B, Qwen 7B and Llama 8B keep the signal at Q4_0. Whether Q4_0 costs them
  anything is unknown, because their 8-bit files were not run.
- **Prior work:**
  - Proskurina et al. (Findings of NAACL 2024) report that 4-bit GPTQ lowers confidence on true labels, model by model.
  - A 2026 preprint, *Can Small Language Models Use What They Retrieve?*, reports that small models fail to use context and that an FP16 run shows the same pattern.

  Neither was read in full for this report.

## Blocked / needs a decision
1. **Confirm or kill the effect with a pre-registered run** (one Mac night plus about 2 h of board time):
   - Q4_0 against Q8_0 for five models (Qwen 0.5B, Gemma 1B, Qwen3 1.7B, Llama 3B, and Qwen 7B or Llama 8B);
   - on requests from the **30 reporting boiler episodes**, never used for a decision;
   - plus a public task with probabilities saved (MMLU with token probabilities, and one evidence-matching task);
   - Llama 3B at both precisions on the NPU;
   - rule written first: the 8-bit minus 4-bit AUC difference and its interval.
2. **Whether the paper may lean on the synthetic boiler.** The effect exists only where the list contains the answer.
   Cranfield and TEP cannot show it until retrieval there is better.
3. **The code-side agreement signal** (0.96 against 0.34) suggests a retrieval and belief change in the agent. That
   touches agent behaviour and needs its own pre-registered rule.

## What I could not verify
- **That the effect is caused by quantization as such,** and not by this file's recipe (every matrix Q4_0, as the NPU
  requires). K-quant 4-bit files were not tested, and cannot run on the NPU.
- **Generality:** one model family, 8 synthetic episodes, two hardware paths.
- **Novelty:** two searches, no full reading of the nearest papers.
- **The NPU latency** is laptop wall-clock from the teammate's logs, one boot.
