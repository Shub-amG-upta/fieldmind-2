# What we did after the Cranfield and TEP runs (6–12 November 2026)

A short summary in plain words, covering:
- where we started;
- the two paper ideas that came out of it;
- what is finished;
- what is still running or missing.

---

## How to read the numbers

| label | meaning |
|---|---|
| **Board** | measured on the Qualcomm board (Snapdragon 8 Gen 3), with the model on its NPU. Our agent code ran on a laptop; only the model calls ran on the board |
| **Laptop replay** | the same saved questions sent again to a model on a laptop. **Not an NPU result** |
| **No-model** | the agent with the model switched off (only our code ranks the causes). It is a baseline, **not** a model result |

- The boiler data is **synthetic**. Cranfield is **real** test-rig data. TEP is a **public** benchmark.
- **No energy has been measured yet.** The board has no power sensor, so we need an external meter.
- Every decision is made on **development episodes**, never on the episodes we report.
- **Every rule is written down before the run it judges.**

---

## Where we started (6 November)

We added two plants besides our synthetic boiler:
- **Cranfield:** real data from a multiphase flow rig, 6 faults;
- **TEP:** the Tennessee Eastman chemical process, 20 faults, a standard public benchmark.

We ran the full agent on both, on the board.

**What we did with those runs:**
1. **Fixed accuracy on TEP.** Some rules were written down in advance and then run once on the reporting set:
   - the true cause was being cut from the candidate list; that is fixed (1,689 times → 0);
   - two new TEP signal patterns were added.

   TEP accuracy rose from **0.416 to 0.575**, and false alarms fell by about **half**. Boiler and Cranfield were
   unchanged.
2. **Compared with a standard method (PCA).** Our agent detects more faults:
   - on TEP: 0.81 against 0.65;
   - on Cranfield: 0.88 against 0.85.

   But on TEP it raises about **12× more false alarms per hour**, so we make no detection claim there.
3. **A surprise: we shuffled the list of candidate causes before giving it to the model.** The model still picked
   whatever was on line 1. This one test started both paper ideas below.

---

## Idea 1: the same question gets different answers on the phone's NPU

**In one line:** ask the model the exact same question twice, with all randomness switched off, and the NPU sometimes
gives a different answer. The CPU never does.

**What we found (board):**
- **Llama 3B:** 17.8% of repeated answer pairs differ on the NPU, and 0% on the CPU.
- **It depends on the model.** Qwen3 1.7B varies (10.7%); Gemma 1B and Qwen2.5 0.5B don't.
- **It also happens on public benchmarks.**
  - MMLU: a few answers change.
  - GSM8K: 3.5% of final answers change, and accuracy moves between 69% and 73% across repeats of the same run.
- **Why:** tiny rounding differences on the NPU (about 0.01 per token, in log-probability) flip the answer when the
  model's top two choices are almost tied.
- **The published llama.cpp fix for a similar bug does not remove it.**
- **In our agent it rarely changes the final decision:** 4 of 809 scored ticks flipped between right and wrong.
- **A second device (a phone with an older NPU) was tried.** It gives wrong answers for every model, with every
  llama.cpp version. We traced this to two NPU operations; with them switched off it works, but more slowly.

**What it means:** anyone who measures models on a phone NPU from a single run has a few points of hidden noise.

**Still to do:**
- find the exact operation that causes the variation (planned and written down, not yet run);
- repeat the test on the second device;
- explain why the CPU also varies on long GSM8K answers.

---

## Idea 2: what the language model really does inside the agent, and what it costs

**In one line:** on the phone, most of the time goes into the model writing its answer, and the model mostly copies
the first option it is given instead of weighing the evidence.

### What it costs (board)
- **Writing is the expensive part.** The NPU reads the prompt 40–56× faster than it writes the answer.
- **Writing less made the agent 12× faster** (9,916 s → 821 s), with no missed deadlines.
- **The NPU and the CPU slow each other down** when both run a model at the same time.
- **The NPU still keeps 1.2–1.4 of the phone's CPU cores busy** while it works.
- **The phone gets slower when it gets hot.**
- **Scheduling (52 board runs):** we measured how fast a plant the phone can keep up with. Sending work to "whichever
  chip will finish first" did worse than always using the NPU. We found why, and built a corrected rule. It is not
  yet tested on the board.

### What the model does: it copies line 1 (we call this "echo")
We give the model a numbered list of possible causes, with our code's best guess first.
- **It picks line 1 in 97–99% of answers, even after the list is shuffled** (board, all three plants).
- **It changes the agent's final answer on less than 1% of ticks** compared with the no-model agent. When it did
  change it on TEP, the code alone was right more often (9 against 3).
- So the agent's accuracy is really our code's ranking passed through.

### Why does it copy? (laptop replays of the same 450 saved questions)
**Five models were tested:** the board's 3B at 4-bit, 8-bit and 16-bit, plus Qwen 7B and Llama 8B.

| question | answer |
|---|---|
| Is it the 4-bit compression the NPU needs? | **No.** The full-precision model copies almost as much |
| Is it just model size? | **Partly.** Bigger models leave line 1 more often, but are not more often right |
| Is the right answer even in the list? | **Often not.** It is there 61% of the time overall, but only 36% on Cranfield, where no model could do better |
| Do the models read the evidence at all? | **A little.** When the list is shuffled, their own picks beat a random guess by about 10–13 points. That holds for every model except the board's 4-bit file, which leaves line 1 too rarely to judge |
| Do they read better than our code ranks? | **No.** When they leave the code's first choice, they are less often right than the code |

**What it means:** standard accuracy makes the model look useful, but here it adds almost nothing on top of our code,
while using most of the time. The important question is not "which chip should run the model?" but **"should we call
the model at all?"**

**Running now (on a 24 GB Mac):**
- a **size curve** from 0.5B to 14B;
- whether the model copies the **position** or the **label** "1";
- what it **prefers before reading** anything;
- the same test on **public MMLU questions**, to see if the model reads when it knows the answer.

**Still to do:**
- **Energy:** the biggest gap; we need a power meter.
- **Someone else's system.** We will run the same test on FaultExplainer (a published LLM fault-diagnosis tool), so the
  finding is not "your agent was badly built". The harness is built.
- **A much stronger cloud model** on the same questions, to check whether the answer is even findable from our prompt.
- **On the board:** the corrected scheduling rule, the known published fixes for this kind of copying, and repeat runs.

---

## How the two ideas relate
- **Idea 1** is about the hardware: the NPU is not repeatable.
- **Idea 2** is about the agent: the model copies, and costs a lot for little gain.

They use the same board and agent, but no result is claimed in both. Idea 2 cites Idea 1 to explain why its numbers
need repeat runs.

## Questions for you
1. **A power meter.** Is there one we can borrow, or should we buy one?
2. **A cloud model.** Can we send our synthetic and public test questions to one, to get an upper bound?
3. **Which conference.** Idea 1 looks closest to ready. Idea 2 needs energy and the outside-system test first, so it
   likely needs a later deadline.
4. **Cranfield's candidate lists often miss the true cause.** Should we look into the case library? That would change
   case data, so we would write a rule first and need your sign-off.
