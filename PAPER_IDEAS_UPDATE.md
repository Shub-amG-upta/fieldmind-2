# Our paper ideas, after the latest runs

Updated 2026-11-12. Same three ideas as before, with everything learned since: the scheduling sweep on the board, the
echo tool, the no-model test, a first look at the saved board data, the scheduling fix, and the latest nondeterminism
runs (reboot test, second phone, full MMLU). Plant data: the boiler is
synthetic, Cranfield is real rig data, TEP is a public benchmark. **No energy has been measured yet.**

Two kinds of results below:
- **confirmed:** produced by tested tools;
- **first look:** from quick scripts over saved runs, to be checked before anything is quoted.

---

## Idea A: the same question gets different answers on the NPU

**Paper title:** *Same Prompt, Different Answer: Nondeterminism of LLMs on a Mobile NPU*

**The idea in one line:** with randomness switched off, the phone's NPU sometimes gives a different answer to the exact
same question, call after call. The CPU doesn't within one boot of the board.

**What we have (confirmed, measured on the board):**
- Llama 3B on the NPU: **17.8%** of repeated answer pairs differ. On the CPU: **0%** within a boot.
- Restarting the server changes nothing: it happens on every call.
- It depends on the model: Qwen3 1.7B varies (10.7%); Gemma 1B and Qwen2.5 0.5B don't.
- Public benchmarks:
  - **MMLU** (4 models, NPU and CPU, 2 sessions each): only Llama on the NPU ever changes a letter (51 of 13,500
    answers, on 4 of 300 questions).
  - **GSM8K:** 3.5% of final answers change on the NPU, and accuracy moves between **69% and 73%** across repeats. The
    CPU was identical apart from one 8-minute burst in one session (cause unknown); a second CPU session was identical.
- **The CPU and NPU disagree with each other** on 5–12 of 300 MMLU questions, even for models that are stable on both.
- llama.cpp's published fix for a similar bug **doesn't change Llama's variation** and halves Qwen3's (11.3% to 5.3%),
  without removing it.
- **Mechanism:** tiny rounding jitter (about 0.01 nats per token) flips the answer where the top two choices are almost
  tied.
- **In the agent** (saved runs): a changed answer changed the published top cause on 6 of 1,380 ticks. It flipped
  right and wrong on 4 of 809 scored decisions, and the plant state never.

**New since the last version (confirmed, board and phone):**
- **The CPU changes across reboots.** After rebooting the board, 25 of 100 prompts gave a different CPU answer, fixed
  for that whole boot. A third boot went back to the first boot's answers. The CPU's numbers shift by about 0.004 nats
  between boots. So the honest contrast is "the NPU varies call to call; the CPU is fixed within a boot but not across
  boots".
- **A second device, and a silent failure.** On an iQOO phone (Snapdragon 8s Gen 4, older NPU v73):
  - llama.cpp's NPU gives nonsense for all 4 models while reporting that everything runs on the NPU;
  - every version tested fails, including today's upstream;
  - the phone's CPU answers normally.
- **Its cause is found:** llama.cpp's own checker shows the phone NPU's matrix multiply and attention return infinite
  values whenever they process more than one token at once.
  - Reading the prompt one token at a time (`-ub 1 -fa off`) makes the phone answer normally (7 of 10 match the board).
  - This is a *different* problem from the board's jitter.

**New since the last version (first look, from the probe data):**
- **Answer length predicts how often answers differ.** Each token has about a 0.65% chance of being where two runs
  split. That predicts about 0.5% for one-letter answers (MMLU measured 0.4%) and about 19% for the agent's 30-token
  answers (measured 18–20%).
  - **GSM8K doesn't fit:** 62% predicted against 12% measured. Unexplained.
- **The important part never changes.** In 200 differing answer pairs, the first difference was **never the top case**.
  It was in notes, citations or lower ranks. The top case is chosen with a margin about 100× the jitter. That's why
  decisions almost never flip.
- **Heat isn't the cause.** A cold chip (33 °C) and a hot one (62–66 °C) vary about equally (16–19% of answers).

**What it means:** temperature 0 does not mean repeatable on this NPU. Single-run phone NPU benchmarks carry a few points
of hidden noise, and longer answers carry more. On another phone the same software can be silently and completely wrong.
Checking NPU answers against the CPU, within one boot, catches both.

**What it still needs:**
- **The module 2 results.** The tests that change one setting at a time (grammar off, short prompts, 8-bit model, cool
  vs hot chip) are pre-registered and committed. Results not pushed yet.
- **The exact operation** inside the NPU that causes the jitter, if module 2 narrows it.
- **The same jitter on a second runtime or device.** The phone shows a different bug, so "this is one backend's bug" is
  still open. A reviewer could even cite the phone to argue the Hexagon backend is immature.
- **A controlled agent run (m6):** the "6 of 1,380 ticks" figure rests on old saved runs. About several hours of board time.
- **A mitigation and its speed cost.** For the phone, separating `-ub 1` from `-fa off` would give one.
- **A fresh search** that no one has published this for phone NPUs. The GPU version of the problem is well known.
- **The writing:** abstract, sections 1 and 4–8, two figures.

**Honest chances:** still the most complete idea and the only one that could be submitted by **4 December**. The phone
result makes the paper more interesting and more useful, but doesn't remove the main objection, because it is a
different bug. If module 2 narrows the cause and m6 runs, it becomes a real contender. The same jitter shown on a second
runtime would make it a strong one. Nothing here depends on the other two ideas.

---

## Idea B: what the LLM really does inside an on-device agent, and what it costs

**Paper title:** *What Is the LLM Doing in an On-Device Agent? Cost, Shortcuts and Scheduling on a Phone NPU*

**The idea in one line:** on a phone NPU, most of an agent's model time goes into writing answers, and the small model
mostly copies the first option it's given. Its apparent accuracy belongs to the code around it.

**What we have:**

*Cost (confirmed):*
- **Writing is the cost.** The NPU reads prompts 40–56× faster than it writes. About 70% of every call is writing about
  30 tokens.
- **Writing less made the agent 12× faster** (9,916 s to 821 s), with no tick over budget.
- **The NPU only wins at reading.** For Llama 3B the CPU writes as fast as the NPU (19.7 vs 18.2 tokens/s) but reads
  9× slower (100 vs 897).
- **The agent runs on the phone itself** with identical answers to the laptop. Its non-model work takes 33–69 ms
  per tick (p95), well under the 200 ms limit.

*The model copies (confirmed, tested tool, dev data):*
- **It picks line 1 in 98–100% of answers** on all three plants, and **100%** when the list is shuffled.
- **When a prompt format makes it choose, it's no better than random:** right 0.086 against 0.102 for a random pick on
  Cranfield; 0.108 against 0.085 on TEP.
- **The prompt decides which shortcut it takes:**
  - the most common group letter, when letters are shown;
  - line 1, when they aren't;
  - **the worked example in the prompt:** 86% of one format's answers on Cranfield were the example `[2,1]` itself.
- **The agent with no model at all does as well.** Ranking by the retrieval code alone beats the code's belief by
  +0.11 to +0.13 on all three plants: the same gain once credited to the model. On Cranfield the board model scores
  exactly the no-model result (0.524).

*Scheduling (confirmed, board sweep):*
- **How fast a plant the phone keeps up with:** the boiler at one tick per 3 s; at 2 s when the model is called less
  and writes shorter answers. Cranfield: never with full answers; at 4 s with short ones.
- **Calling less beats placing better.** The shorter-answer version gains a full step at the same accuracy.
- **"Smart" placement never helped and hurt on Cranfield.**
- **We found why** (the scheduling fix, built and tested on the laptop):
  - it charged every call a 60-token answer when about 30 (or 8) were written;
  - with real lengths, its timing error fell from 2.3 s to under 0.1 s.
- **A corrected policy** learns real answer lengths and how the chips slow each other. An offline replay predicts it
  then almost never uses the CPU and matches simple fixed placement. On this phone, the slower chip is almost never
  worth it.
- **Two corrections to earlier claims:**
  - short answers meet urgent deadlines only at the slowest load (5 of 34 late at 5 s, 28 of 34 at 4 s);
  - under overload the published cause can freeze on a wrong answer, because model "nudges" never reset (score 0.000
    against 0.344 for the code alone).

*Confirmed since (tested tools, `reports/paperB_prep.md`):*
- **The model changes the published answer on under 1% of moments** compared with the no-model agent: 2 of 500 scored
  ticks (0.40%) on Cranfield, 17 of 2,593 (0.66%) on TEP. Where it does, the no-model answer was right more often (9
  against 3 on TEP). That costs 1.35–2.47 seconds of NPU time per tick.
- **NPU calls aren't free for the CPU:** while the NPU lane runs a call, its server keeps about **1.2–1.4 CPU cores**
  busy, and none while idle. (The first look said about two cores while writing; that came from a fit which turned out
  unreliable. Reading and writing can't be separated.)
- **The chips hurt each other more than measured in isolation:** the CPU drops to 0.43–0.56 of its speed when both
  work (the isolated test said 0.79–0.95).
- **Heat:** the hottest quarter of runs reads prompts 9–22% slower and writes 8–12% slower than the coolest quarter.
  This is an association, not a controlled test.
- **Our own measuring tool uses about 0.75 of a CPU core** during every run (median of 347 runs). It must be off for
  energy measurements.

**What it means:** a phone spends seconds per tick on a model that changes under 1% of answers. A simple shuffle test
and a no-model test expose this, and standard accuracy numbers hide it. The useful scheduling question isn't "which
chip?" but "should we call the model at all?". We now have the mechanism for why the "which chip" answer is "the NPU,
almost always" on this phone.

**What it still needs:**
- **Energy.** Nothing yet; this is the biggest gap, and every competing paper has it.
- **The echo replay** (running now on a teammate's laptop): does a bigger or higher-precision model stop copying? That decides
  between "phone-sized models are too small" and "the prompt invites copying".
- **The scheduling fix on the board:** about 3–4 hours. Until then it's a prediction.
- **The first-look results confirmed** in tested code.
- **More repeats and episodes** (the sweep used 3 episodes), and ideally a second device.

**Honest chances:** this is now the strongest *story*: a reusable test, a clear negative result about the model, and
measured costs with mechanisms. But it is **not ready for 4 December**: energy is missing, the echo cause is pending, and
the fix isn't proven on the board. With those three done, it's a strong contender at the next good deadline. One risk:
if echo turns out to be its own paper (Idea C), B loses its most distinctive part and becomes a cost-measurement paper,
which is a crowded area (borderline at best).

---

## Idea C: does shrinking the model to fit the NPU make it copy?

**Paper title:** *Quantized into Copying: How NPU Quantization Turns Reasoning into Echo*

**The idea in one line:** maybe the full-precision model actually reads the options, and it's the 4-bit version the
NPU needs that makes it copy line 1.

**What we have:**
- The echo finding, now from a tested tool, with one addition: **the model picks line 1 with a confident margin, not
  by a hair** (first look). Echo is a real preference, not a rounding accident.
- **The test is ready but not run.** The 450 questions and 450 letter pairs are fixed, the 8-bit model file is built,
  and the run is handed to a teammate's laptop.

**What it means, if true:** squeezing a model to fit a phone NPU would quietly break its reasoning without changing
its accuracy score. That would be a new, phone-specific problem that ordinary benchmarks can't see.

**What it still needs:**
- **The replay results:** the 4-bit board model against the same model at 8-bit and 16-bit, and one or two bigger
  models. About 1–2 days of laptop time.
- **What each result would mean:**
  - only the higher-precision model reads the options: its own paper;
  - bigger models read them and small ones don't: part of Idea B;
  - every model copies: the prompt's fault, a section of Idea B;
  - bigger models choose but are wrong: our case data needs checking first.
- **A clear difference from known work.** LLMs preferring the first option is already published; the new part would
  be the link to phone NPUs.

**Honest chances:** today, none as a separate paper; it's a hypothesis with one test pending. If the test comes out
"quantization causes it", it becomes the most novel of the three, but would need more models and a second precision
check to stand alone. Most likely outcome, in my view: it folds into Idea B.

---

## In short

| idea | what's done | biggest missing piece | ready for 4 Dec? | honest chances |
|---|---|---|---|---|
| **A**: same question, different answers on the NPU | board measurements, four models, two benchmarks, mechanism, length rule, CPU per-boot result, a diagnosed silent failure on a second phone | module 2 results; the same jitter on a second runtime; the controlled agent run | **yes, borderline** | borderline now; a real contender if module 2 narrows the cause and m6 runs |
| **B**: what the LLM really does in an on-device agent | cost, echo, no-model test, scheduling sweep, scheduling fix (laptop) | energy; echo cause; the fix on the board | **no** | strong at the next deadline if energy, the echo result and the board fix land; weak if echo leaves |
| **C**: does 4-bit compression cause the copying? | the test, fully prepared | the replay results | **no** | depends entirely on one test; most likely becomes part of B |

**Bottom line:** submit **A** for 4 December if module 2 can narrow the cause in time. Build **B** properly (energy,
echo result, fix on the board) for the next good deadline. Let the echo replay decide **C**. MobiSys accepts roughly one
paper in five, so even a strong paper is far from certain.
