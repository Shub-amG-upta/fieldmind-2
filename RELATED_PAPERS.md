# Published work close to our three paper ideas

Collected 2026-11-12. The full papers are in `related_papers_by_idea.pdf`, grouped the same way, with a page list
at the start of each idea. Each summary below comes from the paper's abstract plus spot checks of its text, not a full
reading. Where a venue is marked "listed as", it comes from a search listing, not from the PDF itself.

Each paper is placed under the idea it bears on most; papers relevant to two ideas are noted.

---

## Idea A: same prompt, different answer (nondeterminism on a phone NPU)

**In short:** run-to-run variation at temperature 0 is well studied on **GPUs and cloud APIs**. None of the phone-NPU
papers under Idea B checks whether outputs repeat. That includes one on our exact stack (llama.cpp, Snapdragon 8 Gen 3,
Hexagon v75), which measures speed only. That is the gap A fills.

### Non-Determinism of "Deterministic" LLM Settings
*Atil et al., arXiv 2408.04667 (preprint, v5 2025)*
- **What they did:** ran 5 LLMs, through cloud APIs at temperature 0, 10 times each on 8 tasks.
- **What they found:** accuracy varies up to 15% between runs, and no model repeats its outputs exactly. The cause is
  left open.
- **For us:** same question, but cloud only and no cause. Our version adds a phone NPU, a measured mechanism (jitter
  plus near-ties) and a CPU comparison.

### Understanding and Mitigating Numerical Sources of Nondeterminism in LLM Inference
*Yuan et al., arXiv 2506.09501 (listed as NeurIPS 2025)*
- **What they did:** changed batch size, GPU count and GPU model with greedy decoding.
- **What they found:** in 16-bit (bfloat16), outputs and accuracy change (up to 9% for a reasoning model). The cause is
  the order of floating-point additions. Their fix, LayerCast, computes in 32-bit.
- **For us:** **the main paper to compare against.**
  - Our module 2's 8-bit arm is the phone version of their "more precision" fix.
  - Their causes are configuration changes between runs. Ours varies with nothing changed.

### Introducing Background Temperature to Characterise Hidden Randomness in LLMs
*Messina and Scotta, arXiv 2604.22411 (short note, 2026)*
- **What they did:** defined a "background temperature": the randomness an inference setup adds even at temperature 0.
  Pilot runs on cloud providers.
- **For us:** a ready-made way to express our NPU result as one number. Cite it, and maybe report it.

### Thinking Machines Lab, "Defeating Nondeterminism in LLM Inference" (blog, September 2025; not in the PDF)
- **What it says** (seen second-hand only): GPU kernels give slightly different results at different batch sizes,
  which makes cloud answers vary.
- **For us:** **a useful point of difference.** Our board runs one request at a time (`-np 1`), so batching cannot be the
  cause. Our jitter has to be something in the NPU path itself.

**Also relevant to A:** *Accuracy is Not All You Need* (under Idea C). Accuracy can stay the same while individual
answers change, which matches our "GSM8K accuracy moves between 69% and 73%" observation.

---

## Idea B: what the LLM really does inside an on-device agent, and what it costs

**In short:**
- "Remove the LLM and nothing is lost" has a strong precedent.
- LLM fault-diagnosis systems like ours exist.
- **The cost results overlap two 2026 papers on our chip.**

### Are Language Models Actually Useful for Time Series Forecasting?
*Tan et al., NeurIPS 2024, arXiv 2406.16964*
- **What they did:** removed the LLM from three published LLM forecasting methods, or replaced it with a simple attention
  layer.
- **What they found:** accuracy stayed the same or improved. Pretrained LLMs did no better than models trained from
  scratch.
- **For us:** **the template for B's argument,** and proof that a top venue accepts it. Important difference: they
  tested **other people's** systems. We test our own, so a reviewer can say our prompts were poor.

### FaultExplainer: Leveraging LLMs for Interpretable Fault Detection and Diagnosis
*Khan et al., arXiv 2412.14492 (2024)*
- **What they did:** classical statistics (PCA and T2) detect faults on the Tennessee Eastman process (TEP); an LLM
  explains likely causes to operators.
- **For us:** the kind of system B questions, on one of our plants. **A candidate for running our audit on someone
  else's system.**

### A Large Language Model Enhanced Fault Diagnosis Framework for Chemical Processes
*Liang and Sin, ESCAPE 36 (2026)*
- **What they did:** an LLM calls neural-network diagnosis tools over MCP on TEP and writes operator reports. They
  compared several LLMs.
- **What they found:** reliable tool calling matters more than model size.
- **For us:** a second outside TEP system for the audit.

### When NPUs Are Not Always Faster: A Stage-Level Analysis of Mobile LLM Inference
*Li, Qi and Chen, arXiv 2605.27435 (2026)*
- **What they did:** **llama.cpp on Snapdragon 8 Gen 3 with the Hexagon v75 NPU, our exact stack.** They timed each
  stage and each operation.
- **What they found:**
  - the CPU beats the NPU at reading the prompt by up to 1.6×;
  - the NPU writes only 1.05–1.2× faster;
  - there is a per-call scheduling overhead;
  - more NPU offload means up to 51% more energy.
- **For us:** **overlaps B's cost section.** It agrees that writing is the bottleneck, so we can't claim that as new.
  - Our board measured the NPU reading about 8–9× *faster* than the CPU, the opposite of their prefill result.
  - **Their setup differs from ours in three testable ways:**
    - llama.cpp **b7588** against our **b11371**;
    - attention (`FLASH_ATTN_EXT`) **not supported on their NPU**, so it falls back to the CPU, while our build runs it
      on the NPU;
    - batch size 128 against our default (2048 / 512).
  - Both use 6 CPU threads. Which difference explains it is **untested**; a short board run with `-b 128 -ub 128` and
    attention off would tell.
  - They don't check outputs, which supports Idea A's gap.

### Is Your NPU Ready for LLMs? Dissecting the Hidden Efficiency Bottlenecks in Mobile LLM Inference
*Cai et al., arXiv 2607.05475 (v2, 2026)*
- **What they did:** four phones (including SM8650, our chip) and five frameworks (including llama.cpp), with energy
  measured per backend by their tool PowerBench.
- **What they found:**
  - the NPU wins at reading the prompt; **the CPU wins at writing**;
  - up to about 40% of energy is wasted by thread settings, NPU sleep timing and CPU polling;
  - mobile LLM efficiency is "a scheduling problem".
- **For us:** **it has the energy B lacks.** Their CPU-polling finding matches ours that the NPU lane's server keeps
  about 1.2–1.4 CPU cores busy while it runs a call.

### Characterizing Mobile SoC for Accelerating Heterogeneous LLM Inference (HeteroLLM, engine HeteroInfer)
*Chen et al., arXiv 2501.14794 (v2, 2025); cited as SOSP 2025 by 2605.27435*
- **What they did:** built an engine on Snapdragon 8 Gen 3 that splits *one model's layers* across the GPU and NPU.
- **What they found:** 1.34–6.02× faster end to end. Version 1 reported different numbers against other baselines.
- **For us:** the placement literature. Our "the slower chip is almost never worth it" is about whole agent calls,
  a different level.

### Fast On-device LLM Inference with NPUs (llm.npu)
*Xu et al., ASPLOS 2025, arXiv 2407.05858*
- **What they found:** offloading prompt reading to the NPU gives 22.4× faster prefill and 30.7× energy savings.
- **For us:** the standard citation for "the NPU is for reading".

### MELTing point: Mobile Evaluation of Language Transformers
*Laskaridis et al., MobiCom 2024, arXiv 2403.12844*
- **What they found:** on-device LLMs are limited by memory speed; compression costs accuracy; heat and energy make
  continuous use hard.
- **For us:** the measurement baseline every mobile-LLM paper cites.

### Phase Matters: Characterizing Heterogeneous Vision-Language Inference on a Mobile SoC
*Murthy et al., MobiSys '26 workshop, arXiv 2606.27906*
- **What they found:** on SM8750 with a vision-language model, the NPU is 1.64× faster at reading, 1.18× at writing and
  20–45× on vision encoders. It also runs 10.47 °C cooler with 2.52× less energy.
- **For us:** a third result agreeing that the NPU barely helps writing, on a different chip and software stack.

---

## Idea C and the echo finding: copying the first option, the common label or the worked example

**In short:**
- Every shortcut we found (first option, most common label, the example's answer) is a documented bias.
- **One 2026 preprint already links 4-bit compression to position bias**, on GPUs.

### Calibrate Before Use: Improving Few-Shot Performance of Language Models
*Zhao et al., ICML 2021, arXiv 2102.09690*
- **What they found:** models favour answers that are frequent in the prompt, near its end, or common in training. In
  4-shot LAMA, **50.2% of GPT-3 2.7B's predictions repeat an example answer** (the correct rate would be 24.7%).
  Their fix is to calibrate against a content-free input such as "N/A".
- **For us:** **the same effect as our copied worked example** (86% of one format's Cranfield answers were `[2,1]`).

### Large Language Models Sensitivity to The Order of Options in Multiple-Choice Questions
*Pezeshkpour and Hruschka, arXiv 2308.11483 (2023)*
- **What they found:** reordering options moves accuracy by 13–75%. It happens when the model is unsure between its top
  two or three choices.
- **For us:** order sensitivity, measured on public benchmarks.

### Large Language Models Are Not Robust Multiple Choice Selectors
*Zheng et al., ICLR 2024, arXiv 2309.03882*
- **What they found:** across 20 LLMs, models prefer particular option labels such as "A". This comes mostly from the
  label token itself, not the position. Their fix, PriDe, estimates the preference by shuffling options.
- **For us:** **closest to our "most common group letter" shortcut, and their shuffling is close to our shuffle
  test.** We must cite it and not claim the shuffle test as new.

### Found in the Middle: Permutation Self-Consistency Improves Listwise Ranking in LLMs
*Tang et al., arXiv 2310.07712 (2023, v2 2024)*
- **What they found:** LLMs that rank a list are biased by its order. Shuffling the list several times and combining
  the rankings fixes much of it.
- **For us:** our agent's task *is* ranking a list of cases, so this is a known fix we could test.

### LLM-based Listwise Reranking under the Effect of Positional Bias
*Qiao et al., arXiv 2604.03642 (2026)*
- **What they found:** items late in the list are rarely moved to the top. Part of the cause is training data where the
  relevant item usually comes first.
- **For us:** line-1 echo is the extreme form of this.

### Do RAG Systems Really Suffer From Positional Bias?
*Cuconasu et al., arXiv 2505.15561 (listed as EMNLP 2025)*
- **What they found:** in real retrieval pipelines, position bias matters little, and rearranging passages does no
  better than random shuffling.
- **For us:** a counterpoint to expect from reviewers. Our case is different: the model copies line 1 almost always.

### Accuracy is Not All You Need
*Dutta et al., NeurIPS 2024, arXiv 2407.09141*
- **What they found:** compressed models keep accuracy within about 1%, while up to 13.6% of individual answers flip.
- **For us:** supports C's "compression changes behaviour that accuracy hides", and A's similar point.

### Beyond Accuracy: How 8-bit and 4-bit Quantization Change Position Bias and Answer Consistency in Multiple-Choice LLM Evaluation
*Kolakaluri, 2026 preprint; code and results on GitHub, paper not yet posted; not in the PDF*
- **What they did:** 7 small models at 16-bit, 8-bit and 4-bit (bitsandbytes NF4) on GPUs; about 330,000 prompts.
- **What they found:**
  - 4-bit changes position bias depending on the model, more often increasing it;
  - 8-bit barely changes it;
  - a simple prior correction removes much of the extra bias.
- **For us:** **the direct competitor to Idea C.** What's left for us:
  - the phone NPU's Q4_0 format;
  - inside a real agent;
  - an extreme effect (98–100% copying, not a shift of a few points).
- It is unreviewed and GPU-only.

---

## What this means for each idea

- **A:** the clearest gap. The published work covers GPUs and clouds; the phone-NPU papers never check outputs. The
  paper must explain why the GPU causes (batching, configuration changes) don't apply to us.
- **B:**
  - The cost half is no longer new: the "writing is the bottleneck" result is published on our chip.
  - The "does the model matter" half is where B's novelty lies, with Tan et al. as the precedent.
  - Its weak point is that we audit only our own agent. Running the shuffle test and no-model arm on an outside system
    (FaultExplainer, the TEP MCP framework, or a published on-device agent) is what would make it general.
- **C:** weak as its own paper, because the biases are known and compression-versus-position-bias has a preprint.
  Better folded into B: the echo replay tells B whether to blame model size, compression or the prompt.
