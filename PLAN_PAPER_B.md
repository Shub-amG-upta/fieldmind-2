# Making Paper B strong: what to do, and what is left

Written 2026-11-12, after checking the related work (`RELATED_PAPERS.md`). Plant data: the boiler is synthetic,
Cranfield is real rig data, TEP is a public benchmark. **No energy has been measured.** Time estimates are rough guesses,
not measurements.

---

## Where B stands, honestly

**The paper we want:** *on a phone NPU, an agent's LLM costs seconds and energy per tick but barely changes its
decisions. A cheap audit (a shuffle test plus a no-model run) exposes this, and standard accuracy hides it. Here is what
the model costs, why scheduling it cleverly doesn't help, and when calling it is worth it.*

**Today it is borderline-to-weak for the main conference.** Four reviewer objections, in order of danger:

| # | objection | how bad today |
|---|---|---|
| 1 | "You audited only **your own** agent. Your prompts were poor, so of course the model added nothing." | **fatal**: no answer yet |
| 2 | "The cost results are already published." The NPU barely helps writing on our chip: *When NPUs Are Not Always Faster* (llama.cpp, Hexagon v75) and *Is Your NPU Ready for LLMs?* (includes SM8650). | serious |
| 3 | "No energy." Every competing paper has it, and the board has no power sensor. | serious |
| 4 | "One 3B model, three episodes per cell, a scheduling fix shown only in a replay." | moderate |

Each item below says which objection it answers.

---

## Tier 1: without these, B is a workshop paper

### 1. Run the audit on other people's systems (answers objection 1)
**Why:** this is what made *Are Language Models Actually Useful for Time Series Forecasting?* (Tan et al., NeurIPS
2024) work: they removed the LLM from **three published systems built by others**. One outside system turns
"our design was bad" into "this happens in practice".

**Candidates:**
- **FaultExplainer** (Khan et al. 2024): MIT licence, code at `github.com/li-group/FaultExplainer`.
  - PCA and T2 statistics flag the variables; an LLM explains the cause.
  - It runs on **TEP, which we already have** (`reports/b2_tep_pack.md`).
  - Its "root causes included" prompt gives the model a list of known faults to choose from, which is exactly where our
    shuffle test applies.
- **Liang and Sin (ESCAPE 2026):** an LLM calls neural-network diagnosis tools over MCP on TEP. Check whether its code
  is public.
- **A published on-device agent benchmark** where the model picks from a list (an action or a UI element). To be found;
  `llm.npu` used one called DroidTask.

**Steps:**
1. Get FaultExplainer running unchanged with its own cloud model, and reproduce one of its published numbers.
2. Point it at `llama-server` (which speaks the same OpenAI-style API) with our Llama 3B, on the laptop first, then on
   the board's NPU.
3. Pre-register, before any run:
   - **the arms:**
     - the original model;
     - Llama 3B;
     - **no model**: PCA's top variables mapped to the fault list, the "no-model arm" equivalent;
   - **the shuffle test:** shuffle the fault list and check whether the answer follows the position;
   - **the scoring rule.**
4. Report:
   - line-1 rate;
   - shuffle-follow rate;
   - model accuracy against no-model accuracy;
   - cost per call on the board.

**Status 2026-11-12:** FaultExplainer's harness is built and tested (`bench/ext_faultexplainer.py`, 8 tests). The
pre-registration is DRAFT (`reports/ext_faultexplainer_prereg.md`); no model call has been made. Found before running:
- its published evaluation prompt names the true fault number;
- GPT-4o's published picks include IDV(6) for all 11 faults.
**Left:**
- agree the PROPOSED items;
- the laptop pilot;
- arm F1 on the board (about 1.5–2.6 h);
- arm F0 (GPT-4o) only if the team pays for it;
- a second outside system.

**Needs:** laptop, then the board. Using the original cloud model needs an API key and money (the team's decision).
TEP is public data, so nothing private leaves the laptop.
**Effort:** about 1 week for FaultExplainer; another 1–2 weeks for a second system.
**Done when:** at least **two** outside systems are audited with the same tools. Ideally one is a phone or edge agent.

**Outcomes:**
- **Their small models also echo or add nothing:** B becomes general. This is the strongest version.
- **Their models do add value:** B honestly narrows to "it depends on the design". Then the audit itself, and *what made
  the difference*, is the contribution. That is weaker, but still a paper.

### 2. Show it isn't our prompt: try the published fixes (answers objection 1)
**Status 2026-11-12: BUILT, not run on the board.**
- `fieldmind/multi/debias.py` and the overlays `configs/debias_{noexample,noletters,calibrate,pride,psc}.yaml`; every
  switch is off by default.
- 18 tests, 16/16 mutations caught.
- Pre-registration DRAFT: `reports/paperB_item2_prereg.md`.
- Laptop smoke test, laptop model, plumbing only: calibrate moved the rank-1 line off line 1 on 4 of 4 answers (the
  content-free prior puts 0.88 on line 1).
- Commands: `bench/paperB_board.py plan --item 2`.

**Why:** reviewers will say echo is a prompting mistake. The literature has ready fixes, so test them:
- **no worked example in the prompt:** our `explain_v2` exists on `accuracy-fixes`, untested on the board. The example
  `[2,1]` was copied in 86% of one format's answers;
- **no group letters;**
- **contextual calibration** (Zhao et al. 2021): subtract the model's answer to a content-free input;
- **PriDe** (Zheng et al. 2024): estimate the position prior by permuting a few lists;
- **permutation self-consistency** (Tang et al.): shuffle the case list *k* times and combine the answers.

**Why this is good for us whatever happens:**
- **The fixes still don't beat no-model:** the strongest evidence that the model adds nothing.
- **A fix makes the model beat no-model:** a new, useful finding. For example, permutation self-consistency costs *k*×
  the NPU time, so **"accuracy gained per joule"** becomes a real phone trade-off, which is MobiSys material.

**Steps:**
1. Implement each fix behind a config switch.
2. Pre-register on the dev set (never the 30 reporting episodes).
3. Run on the board for all three plants.
4. Report each fix's accuracy against no-model, its NPU time per tick and its echo rate.

**Needs:** laptop code, then board runs. **Effort:** about 1 week of code and tests, plus about 2 nights of board time.
**Done when:** each fix has accuracy, echo rate and cost on all three plants, next to no-model.

### 3. Finish the echo replay (answers objections 1 and 4)
**Why:** it says whether echo comes from model **size**, **compression** (4-bit) or the **prompt**, which decides how
B explains the result.

**Status:**
- Tools, 450 questions and 450 letter pairs are ready.
- The arms:
  - M1: the 4-bit board file;
  - M2: Q8_0;
  - M2b: BF16;
  - M3 and M4: 7–8B models.
- The run is handed off to a teammate's laptop.
- **The thresholds in `reports/echo_prereg.md` are still PROPOSED. They must be agreed before results are read.**

**Steps:**
1. Agree the thresholds.
2. Finish the runs.
3. Score them with bootstrap intervals and per-plant results.
4. If a 7–8B model reads the options, check whether it fits on the board's NPU and what it costs per tick. That gives
   "a model that reads costs X".

**Effort:** 1–2 days of laptop time, plus a few hours of board time if a bigger model is tested there.

### 4. Measure energy (answers objection 3)
**Status 2026-11-12: the software side is BUILT.**
- `bench/energy.py`: meter CSV, then joules per run, per tick, above idle, and per changed decision. 5 tests, 6/6
  mutations caught.
- The runner now records each run's process window.
- **Still needs the meter.**

**Why:** the project's headline metric is energy per correct diagnosis, and every competing paper reports energy.

**Problem:** the board can't measure it (`reports/bev_measurement.md`):
- no power rails;
- battery readings denied;
- the board is fed from a DC supply outside its battery gauge.

**Options:**
1. **An external logging power meter** on the board's DC supply line (recommended). Measure idle first, then subtract it.
2. The iQOO phone's battery gauge. Its NPU only works with prompts read one token at a time (`-ub 1 -fa off`), which
   changes the cost, so it can't stand in for the board's NPU. It is usable for CPU numbers only.

**What to report:**
- joules per tick, with and without the model;
- **joules per changed decision** (the model changes under 1% of ticks);
- joules per correct diagnosis, model against no-model;
- NPU against CPU lane.

**Rules:**
- the sampler must be off or at its light setting (it costs about 0.75 of a core);
- log chip temperature before and after;
- leave cooling gaps between runs.

**Needs:** a meter (to buy or borrow), and the team's decision on which. **Effort:** a few days to get the meter, about
1 day of runs.
**Done when:** every cost table has an energy column from real measurements. Energy stays null until then.

---

## Tier 2: makes it solid

### 5. Confirm the first-look results in tested code (objection 4)
**DONE 2026-11-12** (`reports/paperB_prep.md`; tools `echo_test changed`, `sched_study hostload`, `sched_study heat`):
- the model changes the published top cause on **0.40% (Cranfield) / 0.66% (TEP)** of ticks compared with no-model
  (9 against 3 right on TEP);
- **corrected:** the NPU lane's server keeps **1.2–1.4 CPU cores** busy per second of call, and none while idle. The
  first look's "1.9 cores while writing" came from an unreliable fit;
- heat: the hottest quarter of runs reads 9–22% slower and writes 8–12% slower (an association);
- the sampler costs **0.75 of a core**.

(The in-situ contention figures, CPU 0.43–0.56 of its speed when both chips work, are already from a tested tool.)

### 6. Prove the scheduling fix on the board (objection 4)
**Status 2026-11-12:** the commands are ready (`bench/paperB_board.py plan --item 6`).
- The runner and `run_demo.py` now accept `--placement calibrated_finish`. They did not before; found by the planner's
  test.
- A mock dry run completes.

- Run part D of `reports/sched_fix.md`: `calibrated_finish` on v3x Cranfield (5, 4, 3, 2 s) and v3 boiler (4, 3 s).
- **Agree the pass rule first.**
- Record honestly that the replay doesn't reproduce `earliest_finish`.

**Effort:** 3–4 hours of board time.

**Expected result:** it matches `fixed`, which gives B its mechanism: *a correct cost model concludes the slower chip is
almost never worth it on this phone*.

### 7. More episodes and repeats (objection 4)
**Status 2026-11-12:** the commands are ready (`bench/paperB_board.py plan --item 7`). The cells and episodes are
PROPOSED.

- The sweep used 3 episodes per cell. Rerun the key cells with at least 10 dev episodes per plant and 3 repeats each,
  and report bootstrap intervals.
- Because of the NPU's run-to-run variation (Paper A), single runs carry hidden noise. Cite A for this.

**Effort:** about 2–3 nights of board time.

### 8. Explain the reading-speed disagreement with *When NPUs Are Not Always Faster* (objection 2)
- On the same chip and software, they report the **CPU reading prompts up to 1.6× faster** than the NPU. We measured
  the **NPU about 9× faster** (897 against 100 tokens/s for Llama 3B).
- **Laptop part DONE 2026-11-12** (`reports/paperB_prep.md`). Same model and thread count, so neither explains it.
  Three setup differences remain:
  - their llama.cpp **b7588** against our **b11371**;
  - attention **falls back to the CPU** in theirs and runs on the NPU in ours;
  - batch size **128** against our default.
- **Left:** a 30-minute board check with `-b 128 -ub 128` and attention off. Until then it is unexplained.

### 9. Make the cost section about agents, not single model calls (objection 2)
The published papers measure **one model call**. Our new angle is the **agent's workload**:
- many short calls per tick, with deadlines;
- the share of each call spent writing (about 70%);
- the 12× gain from writing less;
- the chips slowing each other inside real runs (not in isolation);
- the CPU load caused by NPU writing;
- the capacity curve (how fast a plant the phone keeps up with).

Rewrite the cost section around these, and cite the single-call papers as agreeing on the basics.
**Effort:** writing only, once items 4–7 are in.

---

## Tier 3: turns a negative result into a system

### 10. A gate that calls the model only when it can matter
**Status 2026-11-12: NOT BUILT, on purpose.** Its skip rule needs a threshold, and choosing one before items 1–2
report would be tuning on a guess. Build it after them, with the threshold pre-registered on dev.

- The natural constructive answer to "should we call the model at all?". Skip the call when the evidence shows it won't
  change the decision. Possible signals:
  - a clear winner in the retrieval ranking;
  - an unchanged case list since the last call;
  - the model having just copied line 1 on a similar input.
- Measure capacity, energy and accuracy against "always call" and "never call".
- Pre-register on dev, and never tune on the reporting episodes.
- This gives B a *system* contribution, which MobiSys reviewers expect, not only a measurement.

**Effort:** about 1 week of code, plus board nights.

### 11. A second device (optional)
- The phone's NPU is broken for normal prompts (Paper A's finding), so it can't give a fair second NPU.
- A newer Snapdragon board or phone (NPU v79 or v81) would answer "one device".
- At minimum, run the echo audit on the phone's CPU. Echo should not depend on the chip.

---

## Writing and packaging

12. **Related work** from `RELATED_PAPERS.md`:
    - position against Tan et al. (same argument, other domain);
    - Zheng, Zhao and Tang (known biases; our test is cheap, theirs are fixes);
    - the two 2026 cost papers (agree on basics, single-call scope);
    - the compression and position-bias preprint (concurrent).
13. **The audit as a released tool:** `bench/echo_test.py` plus the no-model arm. Package it so anyone can run it on
    their agent. MobiSys has artifact evaluation, so release the tools and the board logs.
14. **Threats to validity:**
    - one board;
    - one synthetic plant;
    - the agent ran on the laptop for the sweep (the on-phone run gave identical answers, with the non-model work at
      33–69 ms p95);
    - one model family unless item 3 adds others.
15. **Figures:**
    - capacity against tick period, per placement;
    - joules per tick against the share of decisions changed;
    - the echo test result (line-1 rate, original against shuffled);
    - accuracy with model, without model, and with each fix.

---

## Order of work

| step | items | where | rough time |
|---|---|---|---|
| now | 3 (agree thresholds, finish replay), 5 (confirm first looks), 8 (read and compare) | laptop | about 1 week |
| next | 1 (FaultExplainer audit), 2 (prompt fixes) | laptop, then board | 2–3 weeks |
| in parallel | 4 (get a meter) | purchase or borrow | depends on the meter |
| board block | 2, 6, 7, then 4 with the meter | board | about 1 week of nights |
| then | 10 (gate), second outside system | laptop and board | 2 weeks |
| last | 9, 12–15 (writing) | laptop | 2 weeks |

**About 6–8 weeks of work in total.** That means B cannot make 4 December, and should target the next good deadline.

---

## Decision points

- **After item 1:**
  - outside systems also echo or add nothing → go for the main conference;
  - they don't → narrow B to "when the model helps, and how to tell", and consider a workshop.
- **After item 2:** a fix makes the model useful → the accuracy-per-joule trade-off becomes a headline.
- **After item 3:**
  - the 8-bit or 16-bit model stops copying → the compression finding (Idea C) becomes a section of B, or its own short
    paper;
  - every model copies → the prompt is to blame, and item 2 carries the story.
- **If no meter can be found:** B is not a main-conference paper. Say so early rather than late.

---

## Already done (for reference)

- **Cost:**
  - writing is about 70% of each call;
  - 12× faster with shorter answers;
  - the NPU wins only at reading for Llama 3B (on our board);
  - the agent runs on the phone itself, with identical answers.
- **Echo** (dev data, tested tool):
  - the model picks line 1 in 98–100% of answers, and 100% when shuffled;
  - where a prompt forces a choice, it is no better than random;
  - the shuffle tool is built, with 19 tests.
- **No-model arm:** ranking by the retrieval code alone beats belief by +0.11 to +0.13 on all three plants. On
  Cranfield, the board model scores exactly the no-model result.
- **Scheduling:**
  - the board sweep (52 runs, capacity per placement);
  - why `earliest_finish` failed (the 60-token cap);
  - the `calibrated_finish` policy and the offline replay (laptop only).
- **Two earlier claims corrected:**
  - urgent deadlines are met only at the slowest load;
  - the overload freeze comes from the nudge rule, not from a bug.
