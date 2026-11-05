# FieldMind multi-agent accuracy fix — what changed and how to benchmark it

Branch: `multi-agent-fix` (made from `demo`)
Status as of 7 Oct 2026: Steps 0 and 1 are built and tested on the mock backend. **No accuracy has been measured with the real model yet.** Step 2 has not started.

---

## 1. The problem

The multi-agent system (Llama 3B diagnostician plus Gemma 1B verifier and text reader) was much faster than the single agent, but much less accurate on some episodes.

Share of scored ticks where the published first-ranked cause is in the right group (four reporting-set episodes, one board run each, so treat these as indicative):

| Episode | Single agent (Llama 3B) | Multi-agent (Llama 3B + Gemma 1B) | Deterministic belief alone |
|---|---|---|---|
| A01 valve seizure | 0.56 | 0.59 | 0.55 |
| B01 tube leak | 0.66 | **0.12** | 0.55 |
| C01 wet coal (held-out) | 0.67 | 0.79 | 0.98 |
| D01 high-CV coal | 0.79 | **0.03** | 0.82 |

The speed side worked. A diagnosis call took about 3 s instead of 14–18 s, there were half as many calls and no deadline misses, and total wall time was about a tenth.

The accuracy loss was not the model failing where belief also failed. The model was **overriding a correct deterministic answer**. On D01, belief was right on 182 of 223 ticks, but the published answer was right on only 7. On B01 it was 71 against 16.

## 2. Why accuracy fell (diagnosis)

1. **The answer format forced a group letter first.** The grammar made the model write `{"g":"<letter>"` before choosing a case. It wrote "A" when an A case was shown and "B" otherwise, then picked a case to match. It chose the true group's letter on 0 of 48 answers in B01 and 1 of 77 in D01. A01 and C01 only looked fine because their true groups are A and C.
2. **The model's order was always published above belief, whatever the confidences.** The gate used the single agent's merge rule, where the model wins on order. On D01, a model pick with confidence 0.22 was published first while belief held the right case at 0.98 in third place. The plan's rule (a checked answer nudges belief by a capped amount) was never built.
3. **The compact case lines removed what identifies a case.** Titles and cause text were gone, leaving only an ID, signature jargon and a "check" sentence. The model could not link a coal-CV record to RCA-07.
4. **The right case was sometimes not shown at all.** It was missing from 18 of 57 prompts on A01 and 19 of 96 on D01. All-FLAT "filler" cases took up to three of the four slots.
5. **Old answers were reused while belief moved on.** 21–34% of merged answers were more than one tick old, up to 14 ticks.
6. **The verifier gave the same answer every time.** Gemma 1B returned `[[1,"p"],[2,"f"],[3,"p"]]` on 85 of 86 calls, echoing the prompt's example.
7. **The text reader produced false evidence.** All 27 notes were coded OTHER with invented subject/state pairs (for example, "fire ext refill due" became FEED_VALVE DOWN).
8. **Answers echoed the prompt example in other fields too.** About 90% listed facts as both cited and "unexplained".
9. **Weaknesses inherited from the deterministic layer.** Belief is right first only 0.55 of the time on A01 and B01; E01 fouling is never detected.
10. **Process gaps.** No real-model accuracy gate was ever run, the two lanes ran different models, and board runs did not save prompts.

## 3. Fix plan (in order)

1. Make belief the default order; the model may move a case only by a capped amount, or only when belief is tied or uncertain. **← Step 1, built**
2. Remove `g` from the answer, or move it after the ranking and derive it in code.
3. Remove or randomise worked examples in all three prompts.
4. Put a short case name back in each case line; replace the "check" sentence with something comparable to the facts.
5. Stop all-FLAT filler cases taking prompt slots; always show belief's top cases.
6. Add belief's top case to the answer-reuse test; cap how old a reused answer can be.
7. Turn the verifier off until it passes a known-wrong-answer test, or run it on the 3B model.
8. Turn the text reader off or move it to 3B, and reject pairs whose subject is not in the note.
9. Drop or check the `x` and `n` answer fields.
10. Fix belief itself (signature band calibration, tie handling, retire-then-default inversion).
11. Build the drift watcher for family E.
12. Use one model for both lanes, and run the real-model gate on dev before trusting anything.

Steps 2 onwards change what the model is shown, so each one needs a new board run to measure.

---

## 4. What has been done

### Commits on `multi-agent-fix`

| Commit | What it contains |
|---|---|
| `e1269a1` | Pre-registration: answers a–c, decisions, quick and full episode sets, metric definitions. Committed **before any measurement**. |
| `34ba9f7` | Step 0: baselines, prompt saving, `configs/accuracy.yaml`, replay tool. |
| `354cd05` | Amendment recording the merge-rule decision and A-vs-B adoption rule, committed **before any merge-rule replay**. |
| `3c79bc7` | Step 1: the merge rules and `bench/board_session.sh`. |
| `06038e6` | Wording fix in the report. |
| `f6bd178` | Closed three risks: replay exactness, session resume, board preflight. |
| latest | Verifier-cannot-reorder test; memory logging in the preflight made non-fatal. |

### Step 0 — baselines and measurement tooling

**Baselines**

| Baseline | Result |
|---|---|
| Belief alone, full dev, 13 library episodes | 0.502 group top-1 (0.477 with ties shared) |
| Belief alone, full dev, 4 held-out episodes | 0.709 |
| Current multi-agent, quick set, Llama 3B on the board | **Not run yet: needs the QIDK** |

The 0.502 equals the Phase 1 dev value, so the deterministic layer has not moved. Belief takes no model input, so this number holds for any backend.

**Important finding:** on dev, belief is almost never right on family A (A01 0.018, A05 0.0, A06 0.034). A merge rule that keeps belief's order as the default cannot rescue those episodes. Only the model, or a fix to belief itself (fix 10), can.

**Tooling built**

- **The board runner saves every prompt and raw reply**, so runs can be replayed and inspected offline. It takes the overlay, CPU-lane model and episode folder from the environment.
- **`configs/accuracy.yaml`** is `fast.yaml` with Llama 3B on both lanes (decision 4). This differs from the old runs in `outputs/`, where the verifier and text reader were Gemma 1B.
- **`bench/replay_multi.py`** re-applies a merge rule to a saved run's answers without the board. It reproduces the published ranking with 0 differences on a 5,850-tick mock dev run, and it reproduces the diagnosis figures (0.12 against 0.55 on B01, 0.03 against 0.82 on D01). Every run file now carries a `belief_order` key so confidence ties replay exactly.

### Step 1 — merge rules

`multi.merge_rule` decides how the model's answer and belief's ranking are combined for publication:

| Rule | Behaviour |
|---|---|
| `model` | Old behaviour: the model's order wins. Still the default in `base.yaml`. |
| `belief_only` | Publish belief's order; ignore the model. Reproduces the belief baseline tick for tick. |
| `tiebreak` (**option B, primary**) | The model may only reorder cases within 0.35 log-odds of belief's leader, recomputed every tick. Nothing is written to belief, so it cannot drift, but it has no effect when belief is confidently wrong. Used by `configs/accuracy.yaml`. |
| `nudge` (**option A, secondary**) | The model's rank 1 gets +0.35 log-odds and rank 2 +0.175, capped at ±1.2 per case over the episode. Offsets are added only when ranking for publication; belief itself is never changed (a test checks this). A reused (cached) answer gives no new nudge. |

**Overrides:** `--merge-rule` on `run_demo.py`, or the `MERGE_RULE` environment variable for the runner.

**Logging:** every non-quiet tick records the rule, whether the published top 3 differs from belief's top 3, and why. For `tiebreak` it lists belief's leaders and which model cases fell inside or outside the band; for `nudge` it lists the offsets.

**Pre-registered adoption rule (commit `354cd05`):** adopt A (`nudge`) over B (`tiebreak`) only if, on the dev quick set replayed from baseline 3, A beats B on group top-1 by at least 0.03 **and** loses to B by no more than 0.05 on any single episode. Otherwise B stays.

**Why B is primary:** with the model's answers currently close to noise, the first job of the merge rule is to stop it destroying correct belief answers. B can't move far from belief-alone; A can drift belief the wrong way with a consistently wrong model.

### Risks closed before using the board

1. **The A-vs-B replay is exact for group top-1.** The diagnostician prompt, the text reader and the call-or-reuse decision never read the published ranking. The verifier's prompt does, but the verifier only caps confidences at 0.35, never removes or reorders hypotheses, and its verdict is never read by a later tick. Tests run several dev episodes under all four rules and assert identical diagnostician and text-reader prompts and reuse records tick for tick, and an unchanged published order with the verifier forced to fail claims. **Confidence-based numbers from a cross-rule replay are not exact and will not be reported.**
2. **The session resumes safely.** An episode counts as done only when its summary (the last file written) exists; an interrupted episode is rerun from tick 0. This does not share code with the intermittently failing `test_campaign.py` kill-and-resume test.
3. **Board preflight.** Before measuring, the script starts both 3B servers, checks each answers a trivial prompt with the correct model file and lane label, and checks placement (NPU lane fully offloaded with an HTP0 buffer; CPU lane with neither). Memory and RSS logging is best-effort: if `pidof` or `/proc` fails on Android, it records `null` and continues. The model, lane and placement checks are fatal.

### Tests

453 passing. Mutation tests confirm the new tests catch deliberate bugs. One pre-existing, intermittent failure remains open: `test_campaign.py`'s kill-and-resume test, unrelated to this work.

---

## 5. What to expect (honestly)

- **Accuracy has not been shown to improve yet.** Everything above is groundwork and correctness checks on the mock.
- `tiebreak` should mostly **remove the collapses** (B01 0.12, D01 0.03), bringing the multi-agent system back to about belief's level. On the old board runs, belief alone would have scored 0.55 / 0.55 / 0.98 / 0.82.
- Getting **above** belief needs the prompt fixes (Steps 2+: dropping the forced group letter, case names back, filler cases out) and fixes to belief itself, especially for family A on dev.

---

## 6. How to run the new benchmark on the QIDK

### What you need

- The board laptop (Fedora) with the repo and its `.venv`.
- The QIDK connected over USB.
- The Llama 3B GGUF on the board at `/data/local/tmp/llm/Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`.

### Steps

**1. Get the branch** (from the Mac, push first: `git push -u origin multi-agent-fix`):

```bash
git fetch origin && git switch multi-agent-fix && git pull
source .venv/bin/activate
```

**2. Check the board and model file:**

```bash
adb devices
# must list the QIDK

adb shell sha256sum /data/local/tmp/llm/Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf
# expect 5aa3ece50ab33d09a7181888a75f8755f924c662dc99626e7f45440adfeadcdb

ls data/episodes_dev | wc -l
# expect 36
```

**3. Run the board tests on the mock first:**

```bash
.venv/bin/python -m pytest -q tests/test_board_preflight.py tests/test_board_session.py
```

**4. Run the session:**

```bash
mkdir -p logs
bench/board_session.sh 2>&1 | tee logs/board_session_$(date +%Y%m%dT%H%M%S).log
```

### What the session does

| Part | What it runs | Notes |
|---|---|---|
| Preflight | Starts both 3B servers, checks model, lane and placement, logs memory | Exits **3** on failure; nothing is measured |
| (a) Baseline 3 | Unchanged gate (`model` rule), Llama 3B on both lanes, dev quick set (10 episodes) | Every prompt and reply saved; cooldowns and temperature logged |
| (b) Check | Every quick-set run exists, holds all prompts and replies, and replays with 0 differences | Session stops here if anything is wrong |
| (c) Single-agent reference | Llama 3B on the NPU lane, all 36 dev episodes | About 7–9 hours |

**Exit codes:** 0 = done; 3 = preflight failed, nothing measured; 1 = baseline 3, its check, or a single-agent episode failed (the message says which). Running the same command again resumes; finished episodes are skipped and a half-finished one is redone from tick 0.

**Results:** `results/accuracy_fix/board_session/`, plus the log in `logs/`.

### Running only baseline 3 (recommended for now)

The single agent's code has not changed (0 decision differences against Phase 1), so part (c) is only needed if no real-model single-agent run on dev exists yet. To run only baseline 3, start the session as above and **press Ctrl-C as soon as part (c) begins**. Resume handles a half-finished episode safely. Expect roughly 40–70 minutes including cooldowns; the first episode's timestamps give the real figure.

Running a custom list of episodes (for example, a 6-episode subset) is **not supported yet**. It needs an episode-list option in `board_session.sh` and a pre-registration amendment naming the episodes, committed before the run. Those episodes must come from **dev**, never from the reporting set, because the merge rule is being chosen on them.

### After the run

Bring back `results/accuracy_fix/board_session/` and the log, then:

1. Replay baseline 3 under `belief_only`, `tiebreak` and `nudge` with `bench/replay_multi.py` (exact command in `reports/multi_accuracy_fix.md`).
2. Apply the pre-registered A-vs-B adoption rule to group top-1, per episode.
3. For each rule, report how often the published top case differed from belief's, and whether that was right or wrong.
4. Run Step 1 on the board with the adopted rule (`MERGE_RULE=<rule>` or `--merge-rule`).

### Rules for reading the results

- Report **group top-1** from replays; never confidence-based metrics from a cross-rule replay.
- Never choose a rule, prompt or threshold using reporting-set episodes.
- With 10 or fewer episodes, differences of a few points are within noise; treat results as indicative.

---

## 7. Open items

- Baseline 3 on the board (needs the QIDK).
- Confirm whether an existing real-model single-agent run on dev can serve as the reference, or run part (c).
- Episode-list option for `board_session.sh`, if a subset is used.
- Steps 2 onwards (prompt and format fixes) — each needs a board run.
- Fix belief itself for family A on dev; build the family-E drift watcher.
- Intermittent `test_campaign.py` kill-and-resume failure.

---

## Glossary

- **Belief**: the deterministic ranking of candidate causes from facts and signature matching, with no model input.
- **Group top-1**: share of scored ticks where the published first-ranked cause is in the correct root-cause group.
- **Quick set / full dev**: the pre-registered 10-episode and 36-episode development sets.
- **Reporting set**: episodes held back for final numbers; never used for tuning.
- **Baseline 3**: the current multi-agent system with Llama 3B on both lanes, run on the dev quick set with prompts saved.
- **Replay**: re-applying a merge rule to a saved run's answers offline, without the board.
