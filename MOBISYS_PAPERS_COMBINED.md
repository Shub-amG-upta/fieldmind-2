# Our paper ideas, explained simply

**Updated 2026-11-12.**

We have three paper ideas. All of them come from running our fault-diagnosis agent on the Qualcomm board (Snapdragon
8 Gen 3), with the language model on the phone's NPU. The plant data comes from three places:
- the boiler is synthetic;
- Cranfield is real;
- TEP is a public benchmark.

No energy has been measured yet.

**What changed since the last version:**
- **The echo test on bigger and full-precision models has been run.** Compression is not the cause, so Idea C is no
  longer its own paper. B and C are now **one paper**.
- **For Idea A,** the second device (a phone) turned out to be broken for normal prompts. The test that finds the
  exact operation has been planned, but not run.

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
  - **MMLU:** a few letter answers change (Llama NPU 51 of 13,500 pairs; CPU 0).
  - **GSM8K:** 3.5% of final answers change, and accuracy moves between **69% and 73%** across repeats of the same run.
- llama.cpp's published fix for a similar bug does not remove it.
- **Why it happens:** tiny rounding differences on the NPU (about 0.01 nats per token) flip the answer when the model's
  top two choices are almost tied.
- **In our agent it rarely changes the final decision:** 4 of 809 scored ticks flipped between right and wrong.

**New since last time:**
- **The second device (a phone with the older v73 NPU) gives wrong answers for every model**, with every llama.cpp
  version tried, including the newest.
  - The cause was found: two NPU operations used for normal prompts return "infinity".
  - With those switched off, the phone answers normally.
  - So it can be used as a second device, but only in that slower setting.
- **The test that finds the exact operation (module 2) is pre-registered,** but not yet run.

**What it means:** "temperature 0 means the same answer every time" is not true on this NPU. Anyone who benchmarks
models on a phone NPU from a single run has a few points of hidden noise in their results. That makes it useful to
everyone, not just us.

**What it still needs:**
- **The exact operation:** run module 2.
- **The second device in its working setting:** does the variation appear there too?
- **An explanation for one odd result:** the CPU also varies on long GSM8K answers (8.8%). We don't know why yet.
- **A fresh search** to confirm nobody has published this for mobile NPUs.

---

## Ideas B and C (now one paper): what the LLM really does inside an on-device agent, and what it costs

**Paper title:** *What Is the LLM Doing in an On-Device Agent? Cost, Shortcuts and Scheduling on a Phone NPU*

**The idea in one line:** on the phone, most of the time goes into the model writing its answer. And the model mostly
doesn't reason: it copies the first option it's given. Shrinking it to 4-bit is not the reason.

### Cost (measured on the board)
- **Writing is the cost.** On the NPU, the model reads the prompt 40-56× faster than it writes its answer, on all four
  models we tried. In our agent, about **70%** of every model call is spent writing about 30 tokens.
- **Writing less fixed the speed.** Answering with short line numbers instead of long text made the agent **12× faster**
  (9,916 s down to 821 s). No tick went over its 30 s budget, and no answer was unusable.
- **New: the two chips get in each other's way.** When the NPU and the CPU both run a model, the CPU's model runs at
  only 43–56% of its normal speed.
- **New: the NPU still keeps the phone's CPU busy.** While the NPU model works, the server keeps about **1.2–1.4 CPU
  cores** busy.
- **New: heat slows it down.** The hottest quarter of runs read prompts 9–22% slower and write 8–12% slower. That is a
  link we saw, not a proven cause.
- **Two models can share the NPU** with no slowdown. A small decision model answers in 0.37 s.
- **Practical traps we found on the NPU:**
  - some "Q4_0" model files silently run on the CPU instead;
  - the server's prompt cache fills the phone's memory after about 36 calls.
- **New: one disagreement with a 2026 paper on the same chip.** They found the CPU reads prompts faster than the NPU;
  we find the NPU about 9× faster. We have narrowed it to three setup differences. A 30-minute board check will settle
  it.

### Scheduling (new: run on the board)
- **52 board runs**: how fast a plant the phone keeps up with, at 5, 4, 3 and 2 seconds per plant tick.
- **The "send it to whichever chip finishes first" rule did worse than simply always using the NPU.** We found why: it
  guessed answer lengths wrong.
- **A corrected rule is built.** On the laptop's replay of the board runs, it does as well as "always the NPU". It
  has not been tested on the board yet.
- The lesson so far: **the slower chip is almost never worth using on this phone.**

### Echo: the model copies line 1
We give the model a numbered list of possible causes, best guess first.
- It picks line 1 in **98-100%** of answers, on all three plants.
- When we shuffled the list, it *still* picked line 1, **97-100%** of the time.
- A simple piece of code that does no thinking gets the **same accuracy** (Cranfield 0.524 vs 0.524).
- **New: the model changes the agent's final answer on less than 1% of ticks** (Cranfield 0.40%, TEP 0.66%). When it
  did change it on TEP, the code alone was right more often (9 against 3).
- **The prompt format decides which shortcut it takes.** With group letters in the prompt, it copied the most common
  letter. Without them, it copies line 1. Those two prompts were identical apart from the letters.
- **New: the echo counts are now in tested code,** no longer quick scripts.

### New: the echo test on other models (this was Idea C)
Same 450 saved questions, in normal and shuffled order, replayed on a laptop (not the NPU):

| model | picks line 1 after shuffling | same pick in every order |
|---|---|---|
| Llama 3B, 4-bit (the board's file) | 97% | 0% |
| Llama 3B, 8-bit | 88% | 8% |
| Llama 3B, 16-bit (full precision) | 88% | 7% |
| Qwen 7B, 4-bit | 48% | 34% |
| Llama 8B, 4-bit | 38% | 48% |

- **4-bit compression is not the cause.** The full-precision model copies almost as much.
- **Bigger models stop copying, but they don't choose better.** When they leave line 1, they are right no more often
  than line 1 or a random line would be.
- **The group letters move the 3B off line 1, onto worse answers:** right 5% of the time, where line 1 would have been
  right 39%.
- **This is outcome 4 of the plan:** "bigger models choose but are wrong". So the next step is to check whether our case
  data even makes the right answer findable.

**What it means:** standard accuracy numbers make the model look useful, but here its accuracy is really the code's
ranking passed through. Meanwhile the model uses most of the time (and, presumably, most of the energy). So the
important scheduling question isn't "which chip runs the model?" but **"should we call the model at all?"**

### Built, waiting to run
- **Known fixes from published papers** for this kind of copying: no worked example, no group letters, calibration,
  PriDe, and shuffle-and-vote.
- **The same test on someone else's system** (FaultExplainer, a published LLM fault-diagnosis tool).
- **Energy measurement**, waiting for a power meter.

### What it still needs
- **Why it copies.** Each cause gets its own test:
  - Is the right answer even in the list?
  - Can a much stronger model (a frontier model) find it?
  - Does it copy the first *position* or the *label* "1"?
  - What does it prefer before reading anything?
  - Does the 3B read when it actually knows the answer (MMLU)?
- **Someone else's system.** FaultExplainer, so it isn't "you built a bad agent".
- **Energy measurements** on the board. Still the biggest gap.
- **The corrected scheduling rule, the known fixes, and more repeats** on the board.

---

## In short

| idea | what's done | biggest missing piece |
|---|---|---|
| **A**: same question, different answers on the NPU | board measurements, models, public benchmarks, mechanism; second device tried (works only in a slower setting) | the exact operation (module 2); the variation on the second device |
| **B + C**: what the LLM really does in an on-device agent | cost findings, the scheduling sweep on the board, the echo finding, the echo test on 5 models (compression ruled out), tools for fixes, FaultExplainer and energy | why it copies; someone else's system; energy |
