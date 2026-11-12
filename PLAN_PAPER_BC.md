# The combined paper (B + echo): what to run to make it strong

Written 2026-11-12, after the echo replay (`reports/echo_replay.md` on `origin/sched-study`, outcome 4). This plan
supersedes the order of work in `PLAN_PAPER_B.md`. Its item numbers (items 1–10) are kept where they still apply.

**No plan guarantees acceptance.** This one targets the four things a main systems-conference reviewer will look for:
1. a finding that holds beyond our own agent;
2. an explanation of *why*, tested, not guessed;
3. energy, not only time;
4. a lesson or mechanism that others can use.

---

## 1. The paper we are aiming for

**Claim:** in an always-on monitoring agent on a phone NPU, the LLM costs time and energy every tick but barely changes
the agent's decisions, because it copies the order the retrieval code gave it. We show:
- **why** it copies: prior, label, position, uncertainty, compression and size, each tested;
- **that** it happens beyond our agent;
- **what** the phone spends on it;
- **what** it would cost to have a model that actually reads the evidence.

We also give a cheap audit, a shuffle test plus a no-model run, that anyone can run before paying for an on-device LLM.

**What is already measured** (sources in `PLAN_PAPER_B.md` "Already done" and `reports/echo_replay.md`):

| | result | label |
|---|---|---|
| copying | 3B picks line 1 in 99% of answers, 97% after shuffling; same pick across 4 orderings 0.000 | laptop replay, pre-registered |
| compression ruled out | 8-bit 0.88, 16-bit 0.88 after shuffling | laptop replay |
| size, partly | 7B and 8B leave line 1 (0.48, 0.38 after shuffling), but their other picks are no better than line 1 or a random line | laptop replay |
| room to improve | line 1 is right only 0.362 (case) / 0.401 (group) on the replay set | laptop replay |
| decisions | the model changes the published top cause on 0.40% (Cranfield) / 0.66% (TEP) of ticks against no-model | board vs mock |
| cost | decode 40–56× slower than prefill; writing 70–81% of a call; 12× from writing less; host CPU load; contention; heat | board |
| scheduling | capacity per tick period, 52 runs | board |

---

## 2. Reviewer objections and the run that answers each

| # | objection | answered by | today |
|---|---|---|---|
| R1 | "You built a task where the LLM is redundant" | **P1** (why it copies), **P2** (other systems) | open: the biggest risk |
| R2 | "Position bias is known (Zheng 2024, Zhao 2021, Tang)" | P1 separates the known causes on a real agent; P3 gives the phone cost | half: the novelty must be argued |
| R3 | "No energy" | **P3.1** | open: needs a meter |
| R4 | "Cost results are already published (2605.27435, *Is Your NPU Ready*)" | P3.4 (resolve the contradiction), the agent workload framing | open |
| R5 | "One model, few episodes, single runs on a varying NPU" | P1.6 (size curve), P3.6 (repeats), Paper A's rates | partial |
| R6 | "Only a negative result" | P1 gives a design lesson whichever way it comes out; P4 (gate) if a model reads | open |
| R7 | "Synthetic data" | lead with Cranfield (real rig) and TEP (public) | done; say it |

---

## 3. The runs

Every run is on **dev data**. Every threshold is **pre-registered before the run**. No-model numbers are mock (retrieval
order, **not an agent result**). Replay numbers are laptop replays of the board's own prompts, **not NPU runs**.

**Set R:** the 450 dev requests of the echo replay (150 per plant), in the same four orderings:
- the original order;
- shuffles a and b;
- line 1 moved to last.

### P1. Why the model copies (decides the paper's story)

| run | what | how | where | cost |
|---|---|---|---|---|
| **P1.1** Ceiling | how often the true case, and the true group, is in the list at all; where it sits | from the saved set-R requests and the episode truth | laptop | hours |
| **P1.2** Frontier bound | one frontier model on set R, 4 orderings | API, temperature 0, same prompt and answer format | API | 1,800 calls, about 1.3 M prompt tokens; needs your OK |
| **P1.3** Label vs position | separate "first line" from "the line labelled 1" | set R, 3 new forms: (a) the code's top case first but labelled 3, 1, 2…; (b) labels A, B, C instead of numbers; (c) the code's top case last and labelled 1 | Mac: 3B Q4_0, 7B, 8B | 1,350 calls per model, about 1 h each on the 24 GB Mac |
| **P1.4** Prior | the content-free prior of each model, and whether removing it (calibrate) beats line 1 | `fieldmind/multi/debias.py` `content_free` and `debiased_first` on set R | Mac, 5 models | 450 + a few calls per model |
| **P1.5** Self-consistency | majority vote and Borda over the 4 saved orderings | **from saved answers, no new calls** | laptop | minutes |
| **P1.6** Size curve | add Qwen2.5 0.5B, Gemma 3 1B, Qwen3 1.7B (already timed on the board), and Qwen2.5 14B if it fits | the same replay | Mac | about 1 night |
| **P1.7** The 7B hint | is the shuffled-order result (7B's other picks right 0.42 vs 0.29 random) real? | pre-registered rule, intervals over episodes, every model | from saved data, then new runs | minutes |
| **P1.8** Control: the 3B can read when it knows | the shuffle test on a public multiple-choice set (MMLU), same 3B, same NPU file | Paper A's MMLU requests, shuffled options | Mac | about 1 h |
| **P1.9** Richer evidence | only if P1.1 shows a high ceiling **and** P1.2 shows the frontier model also fails | give the prompt more information (full case signatures, fact magnitudes) and re-run P1.2 and 7B | Mac + API | 2 days |

**What P1 decides:**

| result | what the model's failure is | paper's line |
|---|---|---|
| frontier reads and beats line 1; small models don't; bigger ones start to | **capability** | "a model that reads needs about N B parameters; on this phone that costs X s and Y J per tick" (strongest) |
| frontier also fails, ceiling high | **information** | "the facts-only prompt that fits the NPU strips what a reader needs": a design trade-off, tested by P1.9 |
| ceiling low (true case often missing) | **retrieval** | "no reader can fix a missing case; fix retrieval": weakest; aim at a workshop |

P1.3, P1.4 and P1.8 give the mechanism section whichever way P1.2 goes:
- P1.3 asks whether it is the label or the position (Zheng et al.'s distinction);
- P1.4 asks whether it is the prior (Zhao et al.);
- P1.8 asks whether the 3B copies only when it doesn't know (Pezeshkpour; Shi et al.).

### P2. Beyond our agent (answers R1)

| run | what | where | cost |
|---|---|---|---|
| **P2.1** FaultExplainer, arm F1 | our 3B on the NPU through its own prompt code, with its 15 causes in order and shuffled, plus the no-leak form | board | 1.5–2.6 h (`reports/ext_faultexplainer_prereg.md`) |
| **P2.2** FaultExplainer, arm F0 | GPT-4o, its own model: shuffled vs original | API | needs your OK and money |
| **P2.3** No-model for FaultExplainer | rank the 15 causes by code alone from the same top-6 variables | laptop | 1 day to build, pre-registered |
| **P2.4** A second outside system | find one with code: the TEP LLM framework in `RELATED_PAPERS.md`, or a published on-device agent. Give it 2 days; if none has runnable code, drop it and say so | laptop / Mac | 2 days search, then about 2 days |

**FaultExplainer's eval prompt contains the true fault number.** Report it carefully: show the line, run with and
without it, and do not claim more than the runs show.

### P3. The cost on the phone (answers R3, R4, R5)

| run | what | where | cost |
|---|---|---|---|
| **P3.1** Energy | meter on the board's DC input: idle, then the cells below. Split each call into prefill and decode by regressing on token counts; report J per call, per tick, per correct diagnosis, and against no-model | board | the meter, then re-runs (`bench/energy.py`) |
| **P3.2** A model that reads, on the phone | the largest model P1 finds useful, at Q4_0 on the NPU: does it fit, every layer on HTP0, s and J per call | board | 1–2 h, plus checking board memory first |
| **P3.3** Size–cost curve | the 4 timed models (0.5–3B) plus P3.2, with energy | board | 1 night |
| **P3.4** Reading-speed check against 2605.27435 | item 8: `-b 128 -ub 128 -fa off` | board | 30 min |
| **P3.5** Scheduling fix | item 6: `calibrated_finish` on the sweep's cells | board | 3–4 h |
| **P3.6** Repeats | item 7: key cells, at least 10 dev episodes per plant, 3 repeats, intervals | board | 2–3 nights |
| **P3.7** Published fixes on the board | item 2, **cut to the fixes P1.4 and P1.5 show help on the Mac**. If none help, run only PSC once to give its cost | board | 1 night at most (was 2) |

### P4. Only if some model reads (P1.2, P1.6 or P1.7 positive)

| run | what |
|---|---|
| **P4.1** Order-checked gate | ask the model in 2 orderings and accept its pick only if both agree, otherwise keep the code's order. Measure accuracy against J per tick, against "always call" and "never call". Pre-registered on dev |
| **P4.2** Call only when it can matter | item 10: skip the call when the code's ranking is clear. Threshold registered on dev after P1 |

**If nothing reads, P4 is not built.** The constructive part is then the audit tool and the design lesson from P1.

### P5. Packaging

| item | what |
|---|---|
| P5.1 | release `bench/echo_test.py`, the no-model arm and the replay tool as one audit tool, with a README; board logs as the artifact |
| P5.2 | figures: (1) size against cost against "reads the evidence"; (2) label vs position vs prior; (3) J per tick against share of decisions changed; (4) capacity against tick period; (5) FaultExplainer original vs shuffled |
| P5.3 | related work from `RELATED_PAPERS.md`: claim what is new (a 97–99% effect inside a deployed agent, invisible to accuracy, its causes separated, its phone cost), not position bias itself |
| P5.4 | threats: one board; synthetic boiler; replay on a laptop; one model family unless P1.6 widens it |

---

## 4. Order and time

| week (from 2026-11-13) | runs | where | gate before the next step |
|---|---|---|---|
| 0 (1–2 days) | merge the replay branch; write and agree one pre-registration for P1; order the meter | laptop | thresholds dated under "Agreed" |
| 1 | P1.1, P1.5, P1.7 (saved data); P1.3, P1.4, P1.8 (Mac); P1.2 (API, if agreed) | laptop, Mac, API | **read P1: capability, information or retrieval** |
| 2 | P1.6; P1.9 if needed; P2.3; P2.4 search | Mac, laptop | – |
| 2–3 | P2.1 (board), P2.2 (API); P3.4, P3.5 | board, API | outside system: echoes or not |
| 3–4 | P3.2, P3.3, P3.6, P3.7; P3.1 as soon as the meter arrives | board | energy method reviewed before reading numbers |
| 4–5 | P4 only if P1 found a reader | laptop, board | – |
| 5–7 | writing, figures, artifact | laptop | internal review against section 2 |

**About 6–7 weeks.** This paper does not make 4 December. Paper A is the team's candidate for that deadline; this one
targets the next suitable systems deadline (check the calls for papers).

**Minimum for a main conference:** P1 resolved, P2.1 + P2.3, P3.1. Without energy, or with P1 coming out "retrieval",
aim at a workshop or short paper instead and say so early.

---

## 5. Decisions needed

1. **P1.2:** may the set-R prompts go to a frontier API, and which one? They contain synthetic boiler data and the
   public Cranfield and TEP data, and no personal data.
2. **P2.2:** pay for the GPT-4o arm of FaultExplainer?
3. **P3.1:** which meter, ordered when?
4. **Pre-registrations:** agree P1's rules (to be drafted next), and the PROPOSED items in
   `reports/ext_faultexplainer_prereg.md`, `reports/paperB_item2_prereg.md` and `reports/sched_fix.md` part D.
5. **Mac time:** who runs P1.3, P1.4, P1.6 and P1.8. They need about 3 nights on the 24 GB Mac.

## 6. Rules that still hold
- Dev data only for decisions; reporting episodes are run once, to report.
- Every exploratory number (like the 7B hint) is re-measured under a registered rule before it is quoted.
- No energy number without the meter.
- A difference smaller than the NPU's run-to-run spread is not a finding.
- Chip temperature logged before and after every board run, with cooling gaps.
