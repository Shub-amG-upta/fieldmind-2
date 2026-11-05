# Systems papers to read for the MobiSys 2027 paper

**Request:** "give some systems papers that we can read to get inspiration and some idea on how to format and present
our project"

Short reading list, picked for **how these papers are structured and presented** as much as for their content. Venue
and year confirmed for each. Read the four marked ⭐ first; four weeks doesn't leave room for more.

## 1. Papers closest to ours: copy their structure

| Paper | Venue | What to learn from how it's presented |
|---|---|---|
| ⭐ [**llm.npu: Fast On-device LLM Inference with NPUs**](https://arxiv.org/abs/2407.05858) | ASPLOS 2025 | **The model for our paper.** Measured motivation first (prefill is 88–99% of latency), then the obstacles, then one technique per obstacle, then evaluation and an ablation (naive → +1 → +2 → +3). Same Snapdragon 8 Gen 3 chip as ours |
| ⭐ [**MELT: Mobile Evaluation of Language Transformers**](https://arxiv.org/pdf/2403.12844) | MobiCom 2024 | How to present **energy, heat and accuracy together** on real phones, and how to write measurement findings as numbered, quotable takeaways |
| [**Mobile Foundation Model as Firmware (M4)**](https://arxiv.org/abs/2308.14363) | MobiCom 2024 | Presenting a **new system design plus its own benchmark** (eAIBench: 38 tasks, 50 datasets) in one paper. Useful once the plant benchmark grows |
| [**Band: Multi-DNN Inference on Heterogeneous Mobile Processors**](https://github.com/mrsnu/band) | MobiSys 2022 | A MobiSys **scheduling** paper: several models on CPU, GPU and NPU. How they define jobs and show placement decisions, the closest match to our lanes |
| [**CORE: Rethinking DVFS for Mobile LLMs**](https://proceedings.mlsys.org/paper_files/paper/2026/hash/136b9a13861308c8948cd308ccd02658-Abstract-Conference.html) | MLSys 2026 | A short, clean structure: a measurement reveals an inefficiency, a governor fixes it, evaluated across several models with time-to-first-token, time-per-token and energy |

## 2. Recent MobiSys papers to calibrate the bar

| Paper | Venue | Why read it |
|---|---|---|
| **EdgeLoRA: An Efficient Multi-Tenant LLM Serving System on Edge Devices** | MobiSys 2025 ([accepted papers](https://www.sigmobile.org/mobisys/2025/accepted_papers/)) | An LLM serving system on edge devices accepted at MobiSys: compare its evaluation breadth to ours |
| **ARIA: Optimizing Vision Foundation Model Inference on Heterogeneous Mobile Processors for AR** | MobiSys 2025, best paper | Heterogeneous-processor scheduling for a continuous, real-time workload, close in spirit to our tick loop |

Read the evaluation sections of these two to see **how many devices, models and baselines** MobiSys accepted last
year. That's the bar to match.

## 3. Measuring cost, especially energy

| Paper | Venue | What to take |
|---|---|---|
| ⭐ [**Where is the energy spent inside my app? (eprof)**](https://www.cs.columbia.edu/~nieh/teaching/e6998_s13/papers/eprof_eurosys2012.pdf) | EuroSys 2012, Test of Time award 2022 | How to **attribute energy** to parts of a program when hardware gives only whole-device power. That's exactly our case: the board has no per-process power, so we'll split metered power by CPU and NPU activity |
| [**DistServe**](https://www.usenix.org/conference/osdi24/presentation/zhong-yinmin) | OSDI 2024 | Reporting reading and writing separately (time to first token, time per output token) |
| [**Is Your NPU Ready for LLMs?**](https://arxiv.org/abs/2607.05475) | SIGMETRICS 2027 | A measurement paper on mobile NPUs: how to organise many findings |

## 4. Continuous sensing and monitoring (the "always-on" angle)

| Paper | Venue | Why |
|---|---|---|
| [**LightLLM: A Versatile LLM for Predictive Light Sensing**](https://dl.acm.org/doi/10.1145/3715014.3722067) | SenSys 2025 | How a sensing venue presents an LLM working on sensor data |
| [**Evaluating the Practicality of Language Models on Edge Devices for Sensor Data Analysis**](https://link.springer.com/chapter/10.1007/978-3-032-03072-6_6) | Springer book chapter | Related: language models on edge devices for sensor analysis. Check overlap for related work |
| [**FaultExplainer**](https://arxiv.org/abs/2412.14492) | preprint | The industrial LLM diagnosis comparison point (Tennessee Eastman) |

## 5. Guides on reporting and reviewing (short, high value)

| Guide | What it gives you |
|---|---|
| ⭐ [**Hoefler & Belli, "Scientific Benchmarking of Parallel Computing Systems: Twelve ways to tell the masses when reporting performance results"**](https://www.unixer.de/publications/index.php?pub=222) (SC15) | Rules for reporting measurements: repeats, confidence intervals, medians and spread, stating the setup. Directly fixes our "one run" weakness |
| [**Timothy Roscoe, "Writing reviews for systems conferences"**](https://www.sigcommedu.web.illinois.edu/advice/review-writing.pdf) | How systems reviewers think: what they look for in contributions, evaluation and claims. Read it before writing, then review your own draft with it |

## How to use them for our paper

A section plan for MobiSys's 12 pages, modelled mainly on llm.npu and MELT:

| Section | Pages | Model it on |
|---|---|---|
| 1. Introduction: always-on asset monitoring on a phone NPU; writing is the cost; our 4 contributions, with headline numbers | 1.25 | llm.npu §1 |
| 2. Background and measured motivation: read vs write speed (849 vs 16.1 tokens/s), writing is 70% of each call, CPU cost of NPU work | 1.25 | llm.npu §2, MELT |
| 3. Design: facts, belief over past cases, tick loop and hard path, lanes, gate, decision model, choose-don't-write | 2.5 | llm.npu §3 |
| 4. Implementation: QIDK, pinned llama.cpp Hexagon build, bev-decide, sampler | 0.75 | llm.npu §4 |
| 5. Evaluation: setup; accuracy and cost; ablation (baseline → +Explain → +Clear skip → +Verifier); monitoring metrics; energy; placement; second LLM; repeats with spread | 4 | llm.npu §4, CORE, Hoefler rules |
| 6. Lessons: where decision models fail; measurement pitfalls (RSS, non-determinism, heat) | 1 | MELT's numbered findings |
| 7. Related work and limitations | 1 | — |
| 8. Conclusion | 0.25 | — |

**Two presentation habits from these papers worth copying now:**

- **Lead with one measured motivation figure.** For us: read vs write speed, and decode's share of each call.
- **End the introduction with a numbered contribution list that includes headline numbers.**
