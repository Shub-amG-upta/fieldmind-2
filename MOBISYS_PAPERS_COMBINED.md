# Our paper ideas, explained simply

We have three paper ideas. All of them come from running our fault-diagnosis agent on the Qualcomm board (Snapdragon
8 Gen 3), with the language model on the phone's NPU. Some plant data is synthetic (the boiler), some is real
(Cranfield), and some is a public benchmark (TEP). No energy has been measured yet.

---

## Idea A: the same question gets different answers on the NPU

**Paper title:** *Same Prompt, Different Answer: Nondeterminism of LLMs on a Mobile NPU*

**The idea in one line:** if you ask the model the exact same question twice, with randomness switched off, the phone's
NPU sometimes gives a different answer. The CPU doesn't.

**What we have (measured on the board):**
- Llama 3B on the NPU: **17.8%** of repeated answer pairs differ. On the CPU: **0%**.
- Restarting the server makes no difference: the variation happens on every call.
- It depends on the model. Qwen3 1.7B varies (10.7%); Gemma 1B and Qwen2.5 0.5B don't.
- On public benchmarks it shows up too:
  - **MMLU:** a few letter answers change.
  - **GSM8K:** 3.5% of final answers change, and accuracy moves between **69% and 73%** across repeats of the same run.
- llama.cpp's published fix for a similar bug does not remove it.
- **Why it happens:** tiny rounding differences on the NPU (about 0.01 nats per token) flip the answer when the model's
  top two choices are almost tied.
- **In our agent it rarely changes the final decision:** 4 of 809 scored ticks flipped between right and wrong.

**What it means:** "temperature 0 means the same answer every time" is not true on this NPU. Anyone who benchmarks
models on a phone NPU from a single run has a few points of hidden noise in their results. That makes it useful to
everyone, not just us.

**What it still needs:**
- **A second device** (another phone), to show it isn't just this one board.
- **The exact operation** inside the NPU that causes it.
- **An explanation for one odd result:** the CPU also varies on long GSM8K answers (8.8%). We don't know why yet.
- **A fresh search** to confirm nobody has published this for mobile NPUs.

---

## Idea B: what the LLM really does inside an on-device agent, and what it costs

**Paper title:** *What Is the LLM Doing in an On-Device Agent? Cost, Shortcuts and Scheduling on a Phone NPU*

**The idea in one line:** on the phone, most of the time goes into the model writing its answer. And the model mostly
doesn't reason: it copies the first option it's given.

**What we have:**
- **Writing is the cost.** On the NPU, the model reads the prompt 40-56× faster than it writes its answer, on all four
  models we tried. In our agent, about **70%** of every model call is spent writing about 30 tokens.
- **Writing less fixed the speed.** Answering with short line numbers instead of long text made the agent **12× faster**
  (9,916 s down to 821 s). No tick went over its 30 s budget, and no answer was unusable.
- **The model copies line 1 (we call this "echo").** We give it a numbered list of possible causes, best guess first.
  - It picks line 1 in **98-100%** of answers, on all three plants.
  - When we shuffled the list, it *still* picked line 1, **100%** of the time.
  - A simple piece of code that does no thinking gets the **same accuracy** (Cranfield 0.524 vs 0.524).
- **When it does choose, it's no better than random.** In an older prompt format the model left line 1 about half the
  time. Those choices were right **0.8%** of the time, the same as picking at random.
- **The prompt format decides which shortcut it takes.** With group letters in the prompt, it copied the most common
  letter. Without them, it copies line 1. Those two prompts were identical apart from the letters.
- **Two models can share the NPU** with no slowdown. A small decision model answers in 0.37 s.
- **Practical traps we found on the NPU:**
  - some "Q4_0" model files silently run on the CPU instead;
  - the server's prompt cache fills the phone's memory after about 36 calls.

**What it means:** standard accuracy numbers make the model look useful, but here its accuracy is really the code's
ranking passed through. Meanwhile the model uses most of the time (and, presumably, most of the energy). So the
important scheduling question isn't "which chip runs the model?" but **"should we call the model at all?"**

**What it still needs:**
- **Energy measurements** on the board. This is the biggest gap.
- **The scheduling study, run on the board:**
  - how fast a plant the phone can keep up with;
  - whether placing calls on the NPU vs CPU matters.
- **A "no model" version of the agent,** and one that calls the model only when it might help, both measured on time
  and energy.
- **The agent itself running on the phone** (so far only the model calls ran on the board).
- **The echo test on bigger models,** to see whether they also copy line 1.
- **The echo counts moved into tested code.** Today they come from quick scripts.

---

## Idea C: does shrinking the model to fit the NPU make it copy?

**Paper title:** *Quantized into Copying: How NPU Quantization Turns Reasoning into Echo*

**The idea in one line:** maybe the full-size model actually reads the options, and it's the compressed 4-bit version
the NPU needs that makes it copy line 1.

**What we have:**
- Only the echo finding from Idea B. **The test that decides this idea has not been run yet.**

**What it means, if it turns out true:** squeezing a model to run on a phone NPU would quietly break its reasoning
without changing its accuracy score. That would be a new, phone-specific problem that normal benchmarks can't see.

**What it still needs:**
- **The test itself:** run the same saved questions, in normal and shuffled order, on:
  - the 4-bit board model;
  - the same model at full precision;
  - one or two larger models.

  It takes a few days on a laptop.
- **What each result would mean:**
  - only the full-precision model reads the options: this becomes its own paper;
  - bigger models read them and small ones don't: it becomes part of Idea B, as "how big a model you need";
  - every model copies: it's the prompt's fault, and becomes a section of Idea B;
  - bigger models choose but are wrong: our case data probably needs fixing first.
- **A clear point of difference from known work.** LLMs preferring early options is already published. What would be
  new is the link to phone NPUs.

---

## In short

| idea | what's done | biggest missing piece |
|---|---|---|
| **A**: same question, different answers on the NPU | board measurements, models, public benchmarks, mechanism | a second device; the exact cause |
| **B**: what the LLM really does in an on-device agent | cost findings and the echo finding | energy and the scheduling study on the board |
| **C**: does 4-bit compression cause the copying? | the echo finding it builds on | the full-precision vs 4-bit replay |
