# FieldMind: what we have built, how we got here, and what happened on 5 October

*For the FieldMind team (Embedded Systems Workshop, Lab 2, Project 4). Plain language; numbers are from real runs
and say which backend produced them. The detailed records are the reports in `reports/`; this file is the map.*

---

## 1. What FieldMind is, in four lines

FieldMind watches one industrial boiler (a 67 TPH coal-fired fluidised-bed boiler) from 6 sensors, every 30-second
"tick", on a phone-class chip with no internet: the Qualcomm QIDK board (Snapdragon 8 Gen 3, with a CPU, a GPU and an
NPU). It decides whether something is wrong, names the likely cause from a library of 13 real failure reports, and
suggests what an engineer should check. It only advises; it never controls the plant. The plant data is simulated.

The research question is not the agent itself but **how to schedule an agent's model calls across the NPU and CPU**
under a deadline, with no internet and limited power. The headline metric is energy per correct diagnosis.

Two rules hold everywhere: **the model never sees raw numbers** (plain code turns readings into "facts" first), and
**the model never has the last word** (plain code checks every answer and picks actions from a fixed list).

---

## 2. How we got here (the short version)

### 2.1 The single agent (the baseline)
The first working system (`fieldmind/agent/`) runs a fixed chain every tick: checks turn readings into facts, triage
decides whether a model is needed, retrieval finds look-alike library cases, a belief score is updated by code, then
one **diagnostician** model call ranks the causes and one **verifier** call checks it, and a code **gate** approves
actions.

**Its problem:** one big prompt (about 1,900 to 2,150 tokens) and up to two model calls one after the other on one
processor, while the other processor sits idle. On the board, writing an answer is the slow part (about 16 tokens
per second on the NPU), so a long answer costs seconds.

### 2.2 Making the single agent trustworthy (Phase 0, on `main`)
Before any multi-agent work, the single agent was fixed and measured so it could be a fair baseline: the belief
update was corrected (library group score went from 0.028 to 0.574 on the mock), a group-level accuracy metric was
added (9 of 13 cases look alike on 6 sensors), a separate development set of 36 episodes was made so decisions are
never tuned on the 30 reporting episodes, and the baseline was frozen (`results/baselines/single_v3_summary.json`).

### 2.3 Getting models onto the board (Phase 0b, on `main`, the Fedora laptop)
Several ways of running a model on the board were tried first:

| way | result |
|---|---|
| LiteRT-LM on the CPU (Gemma 3 1B) | worked, but 45 to 52 s per call |
| LiteRT-LM on the NPU | context fixed at 1,280 tokens; our prompt did not fit |
| QAIRT compiled graph on the NPU | fastest, but the prompt had to be cut |
| llama.cpp on the NPU, old command-line tool | 7.1 s per call, but it reloaded the 1.79 GB model every call |
| **llama.cpp `llama-server` on the NPU and CPU** | **what we use**: the model stays loaded |

On 3 October the team built llama.cpp for the board (pinned version), built four candidate models the same way
(Llama 3.2 3B, Qwen3 1.7B, Gemma 3 1B, Qwen2.5 0.5B; every weight matrix 4-bit), and pushed them to the board with
checksums. The smoke test on Llama 3.2 3B ran every layer on the NPU: about **899 tokens/s reading** a prompt and
**16.2 tokens/s writing**. An unattended "campaign" was started to pick the model and measure the single agent on
the board; it failed three times that evening because the server kept a copy of every prompt in memory until the
board ran out (fixed with `--cache-ram 0`), and was relaunched.

### 2.4 Why a multi-agent design
The plan (`docs/multi_agent_plan.pdf`) splits the work into small agents that share a **blackboard** (each section
has exactly one writer), so that:
- every model prompt is short (under 1,280 tokens) and every answer is short (60 tokens for a diagnosis);
- the NPU and the CPU can each run a model call **at the same time**;
- plain code publishes an assessment every tick and **the tick never waits for a model**; answers improve it when
  they arrive.

It is built in phases, each changing one thing, so any change in the numbers has one cause:

| phase | what it builds |
|---|---|
| 1. Plumbing | the blackboard, jobs, two lanes, a scheduler, but still the old single prompt; must give exactly the single agent's decisions |
| 2. Shrink the prompt | short prompts, short answers, a text reader for engineer notes |
| 3. Split by plant side | a water-side and a heat-side diagnostician |
| 4. Real time on the board | ticks on the real clock, answers arriving in the background, a drift watcher |
| 5. Scheduling study | compare placement policies, measure energy: the research result |

### 2.5 Where the work stood on the morning of 5 October
- Phase 1 done (tag `multi-phase1`): 0 decision differences against the single agent on 5,850 dev ticks and 5,160
  reporting ticks, with byte-identical prompts.
- Phase 2 commits 0 to 4 done (on the Mac, 3 October): decisions written down before measuring; real token counts
  (1,980 of 1,982 old prompts were over 1,280 tokens); the answer format changed to **line numbers** because the
  planned ID format needed 89 to 111 tokens against a 60-token cap; the text reader built. Commit 4 had **stopped**
  on a question: the note format loses part of two engineer notes.

---

## 3. What we did on 5 October (in order)

### 3.1 Set up the Mac and proved it reproduces
A fresh clone, a new Python environment, episodes regenerated, tokenizers downloaded and checksum-verified. The
223 tests passed, the single and multi-agent versions gave 0 different decisions on the dev set, and the 30-episode
reporting run matched the saved Phase 1 summary exactly. So the Mac reproduces the other machines.

### 3.2 Decided the note-format question: option (c)
The text reader turns a note into a short structured fact. Two dev episodes lose part of a note's meaning (for
example "bfp A suction pressure low" can only be written as "BFP_A LOW"). We chose to **keep the format and record
the loss**, to be measured later with the real model, because on the mock no choice changes any number and the
alternatives were either fitted to the dev notes or costly in answer tokens.

### 3.3 Finished Phase 2's code: shrunk prompts (commits 5 and 6)
Each prompt section got its own on/off switch, so a later accuracy loss can be traced to one section. With every
switch off, the prompts are byte-identical to before.

| prompt (tokens, Llama 3.2 tokenizer, dev) | before | after |
|---|---|---|
| diagnostician, mean / max | ~1,866 / 2,103 | **~750 / 878** |
| verifier, mean / max | ~1,544 / 1,895 | **~428 / 530** |
| prompts over the 1,280 limit (with the answer) | 1,980 of 1,982 | **0** |

All four candidate tokenizers agree within a few percent.

### 3.4 Ran Phase 2's gate (commit 7)
Every check passed except one predicted count: of 3,170 cases whose confidence the code now fills in, 19 were
predicted to keep the same value and **20** did. The other three predicted counts matched exactly (3,170, 580 and
327). We showed the code follows the rule on all 3,170 cases and that the same data reproduces the other option's
committed number; the original calculation was never saved, so the cause is "unexplained". By the rules this is a
stop: **the 30-episode reporting run that closes Phase 2 waits for the team's decision.**

### 3.5 Built Phase 3: two side diagnosticians (on branch `multi-agent-p3`)
The team decided to build Phase 3 before Phase 2's board test, to save board time, on a separate branch.

| commit | what | result (mock, dev) |
|---|---|---|
| 1 | rules for which facts, cases and notes belong to the water side and the heat side | 10 tests |
| 2 | two diagnosticians (water, heat); their answers checked one by one and merged once | the code-only layer unchanged on all 5,850 ticks; side prompts hold only their side |
| 3 | a side is asked again only when its evidence changed; its last checked answer is re-used | diagnosis calls **2,005 to 1,049** (about half) |
| 4 | a tool that feeds the verifier a known-wrong answer and measures whether it objects | ready for the board |
| 5 | final checks and report | everything passes |

**What Phase 3 taught us (all recorded):**
- **Faults that move both sides at once are rare in our data: 23 of 1,982 ticks.** The plan's main example, a tube
  leak that lowers the water level and cools the bed, almost never shows a heat-side change in our simulated
  episodes. So on this data the split mostly gives shorter prompts, not two calls in parallel. This is a question
  for the advisor (A1 in `reports/multi_phase3_split.md`).
- **Mock accuracy rose (group top-1 0.489 to 0.572), but that is not a real gain.** The side filter changes which
  cases the mock is shown; the mock does no reasoning.
- **A verifier that disagrees only lowers a claim's confidence; it never moves it down the ranking.** Even a perfect
  verifier would leave a wrong case at rank 1.

### 3.6 Built the Phase 4 pieces the demonstration needs (on branch `multi-agent-p4`)
The team set three things for the demonstration: **speed first** (not a strict paper comparison), **the heat
diagnostician on the NPU** (the CPU is too slow for it), and **two models**: the 3B model for the diagnosticians, a
1B model for the verifier and text reader in the background on the CPU.

| built | what it does |
|---|---|
| two models, one per lane | NPU lane (port 8080): Llama 3.2 3B for both diagnosticians. CPU lane (port 8081): Gemma 3 1B for the verifier and the text reader. Every call records which model answered |
| `configs/fast.yaml` | the whole demonstration setup in one file: `run_demo.py --overlay configs/fast.yaml` |
| **real-time mode** | `--mode realtime --tick-s 30`: ticks on the wall clock, one worker thread per lane, model calls really in the background, **the tick never waits**. A late answer is used if it is at most one tick old, or later while its side's evidence is unchanged (the plan's rule); otherwise it is dropped and counted |
| `bench/realtime_summary.py` | per episode: calls per lane, how long both lanes worked at once, the slowest answer per agent, stale answers, tick timing |
| live UI hook | `run_episode(..., on_assessment=callback)` hands every tick's assessment to a UI as it is published |
| `HANDOFF_QIDK.md` | step-by-step for the Fedora laptop's Claude: merge `main` and the UI, bring the board up with two models, smoke test, demonstrate |

Checked on the mock: the old "lockstep" mode is unchanged (all four earlier configurations give 0 differences and
byte-identical prompts); with lanes made slower than a tick on purpose, every tick still starts on time and takes
under 200 ms; both lanes work at the same time; nothing is asked twice for the same evidence. 337 tests pass.

### 3.7 What the independent reviews caught
After every commit an independent reviewer (a separate Claude agent that did not write the code) checked it against
the plan's rules. Every review found real problems; they were fixed, tested, and recorded. The important ones:

| found | why it mattered |
|---|---|
| two side answers that each passed the citation check could fail together | would have thrown away good answers on the board |
| my first side rules misread three "pattern" facts, inflating cross-side ticks from 23 to 291 | the first finding I gave the team was wrong; corrected |
| the faithfulness metric scored re-used answers as invented | would have reported a false collapse in faithfulness |
| a re-used answer could name cases retrieval no longer returned | stale answers would have changed actions |
| a verifier that judged nothing counted as agreeing | would have hidden a failing verifier |
| the first real-time version used only half of the plan's stale rule | with slow lanes, no model answer would ever have been used |
| worker threads could write the shared blackboard unchecked | broke the one-writer rule |
| several tests could not fail ("tautologies") | they were proving nothing |

This is why the project insists on an independent check: several of these would have produced convincing, wrong
numbers.

---

## 4. Where everything stands now

### Branches (on this Mac; push with `git push -u origin multi-agent multi-agent-p3 multi-agent-p4`)
| branch | holds |
|---|---|
| `main` | the single agent, the board setup, the campaign (the Fedora laptop has newer commits) |
| `multi-agent` | Phases 1 and 2 (to commit 7) |
| `multi-agent-p3` | plus Phase 3 |
| `multi-agent-p4` | **plus Phase 4 and the handoff: everything** |

### Verified, and what is not
| | on the mock (laptop) | on the board |
|---|---|---|
| Phase 2 shrunk prompts | done | not yet: does a short prompt keep accuracy? |
| Phase 3 split and call-on-change | done | not yet: accuracy, real latency |
| Phase 4 real time, two models | done | **not yet: the demonstration run** |
| the CPU lane's speed with Gemma 1B | — | **never measured: measure first** |
| energy | — | no numbers yet (Phase 5) |

**No number in this file is a model accuracy result.** All accuracy-like numbers come from the mock, which does no
reasoning. Board numbers will come from the demonstration and the campaign.

### A note on episode E01 (slow fouling)
E01 stays QUIET for the whole episode and never calls a model, and its ground truth says NORMAL throughout, so it
scores as correct. That is a known blind spot, not a detection: fouling drifts over hours and no current check sees
it. The plan's fix is the Phase 4 drift watcher, not built yet. Once it is, the ground truth for family E will need a
decision (today, detecting the drift would score as a false alarm). Do not use E01 to E03 for the demonstration;
episodes from families A to D (for example dev_A03, dev_B02, dev_C05) exercise the models.

---

## 5. Decisions the team still owes

| question | options |
|---|---|
| Phase 2 gate G1a (20 against a predicted 19) | accept and run the reporting set; recover the original calculation; or keep investigating |
| advisor question A1: cross-side faults rare; the simulated tube leak barely cools the bed | report it as a property of the data; check the simulator's physics; or add cross-side episodes |
| advisor question A2: fuel-cap cases shown to both sides | keep the inclusive reading or treat steam-flow movement as heat-only |
| is the verifier worth keeping? (it never reorders) | decide after the board's known-wrong-answer test |
| family E and the drift watcher | when to build it; how to label family E's ground truth |

---

## 6. What happens next

1. **Push** the three branches from this Mac.
2. **On the Fedora laptop:** the teammate commits his UI changes and pushes `main`; his Claude follows
   `HANDOFF_QIDK.md`: one `demo` branch with everything merged, tests, the UI connected through `on_assessment`, the
   board up with Llama 3B on the NPU and Gemma 1B on the CPU, a one-episode smoke test, then the demonstration.
3. **After the demonstration:** the real-model test of Phase 2 and Phase 3 against the single agent's board results,
   the known-wrong-answer verifier test, then the rest of Phase 4 (the drift watcher, moving the agent onto the
   board) and Phase 5, the scheduling study.

---

## 7. Words used here

| word | meaning |
|---|---|
| tick | one 30-second step of the monitor |
| fact | a statement plain code makes from the sensor readings, with an id (F1, F2...) |
| mock | a fake model that answers instantly by rule; tests the code, says nothing about accuracy |
| lane | one model server on the board: NPU (port 8080) or CPU (port 8081) |
| lockstep | each tick waits for all its model calls; used for accuracy checks |
| real time | ticks on the clock, model calls in the background, the tick never waits |
| stale | an answer that arrived too late to be used |
| group top-1 | the first-ranked cause is in the right group of look-alike cases |
| dev / reporting set | 36 episodes for decisions / 30 episodes run once per phase, only to report |
| mutation check | breaking the code on purpose to prove a test can fail |
