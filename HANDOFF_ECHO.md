# Handoff: the "echo" test (does the on-device model read the cases, or copy line 1?)

For: teammates, and the Claude session each of you runs. Part 1 is the idea in plain words. Part 2 is what to
build and run. Part 3 lists the rules that apply. Read all three before starting.

---

## Part 1: the idea

### What we found in our saved board runs

At each tick, the diagnostician gets a short numbered list of possible causes (`RETRIEVED CASES:`), ordered by our
retrieval code, so line 1 is the code's best guess. The model is supposed to weigh the facts and pick the cause that
fits.

Llama 3.2 3B (Q4_0, on the NPU) almost always answers "line 1". We call this **echo**: it repeats the order it was
given instead of choosing.

| what we checked | result |
|---|---|
| v3 prompts: rank-1 is line 1 | boiler 0.988 (503 answers), Cranfield 0.998 (422), TEP 0.997 (4,591) |
| Cranfield v3 with the case list **shuffled** | still line 1 in **1.000** of 423 answers; whole answer is 1, 2, 3... in order 0.998 |
| older v2 prompts (group letters on): model leaves line 1 | 58% of answers (131); those picks right **0.008**, a random other line 0.006, line 1 would have been right 0.802 |
| v2 vs v3 prompt difference | 230 of 230 matched prompts identical **except the group letters**. Line-1 rate 0.43 -> 0.99, boiler group top-1 0.233 -> 0.735 |
| merge rule (nudge, tiebreak) | no effect on the raw reply: line-1 rate 0.43 under v2, nudge and tiebreak alike (merge runs after the reply) |
| cost per diagnostician call (v3, NPU) | prompt 550-720 tokens read in ~0.8 s; answer 28-34 tokens written in ~2.1 s. **About 70% of call time is writing the answer** |

So in v3, the model's apparent accuracy is the retriever's ranking passed through. When the prompt format did make it
choose (v2), its own choices were no better than random. Its choice follows the answer format, not the evidence.

**Status of these numbers:** they come from scratch scripts run over `results/benchmarks/*/*.run.json.gz` (branch
`sched-study`), not from tested code. Exact-case matching, single runs. The boiler v2/v3 rows are from
**reporting** episodes (`ep_*`), so they are descriptive only and must not drive any decision. Step 1 below moves the
counts into a tested tool. Until then, do not quote them.

### The question this handoff answers

Is echo a property of **this small, 4-bit model**, or of **the task and prompt**? We answer it by replaying the same
saved prompts, in the original and in shuffled order, on several models on the laptop. Each outcome gives a
different paper:

| outcome | meaning | paper story |
|---|---|---|
| 1. Bigger models stop copying, and are right when they disagree with line 1 | the task is solvable; phone-sized models are below the size where they help | capability threshold for on-device agents, plus what each side of it costs on the NPU, plus a scheduler that skips calls the model can't improve |
| 2. Every model copies line 1 | the prompt or task causes it, not model size | standard agent accuracy can't tell reasoning from copying; a shuffle test exposes it; hidden time and energy cost |
| 3. Same 3B at F16 does not copy, the Q4_0 board file does | the 4-bit quantization we need for the NPU breaks the reasoning without changing accuracy | strongest mobile-systems story |
| 4. Bigger models leave line 1 but are also wrong | likely a problem in our case data (for example the B-family tube-leak case may not match its own facts) | none yet: fix the data first |

---

## Part 2: what to build and run

### Step 0: get the code and data

- Branch `sched-study` (on origin) has the saved runs, including `results/benchmarks/cranfield_dev_v3_shuffled/`.
- Gagan's replay tool is on `origin/nd-paper`: `bench/nd_repeat.py` and `tests/test_nd_repeat.py`. It already picks
  dev-only diagnostician requests from saved runs, rebuilds the request, including the answer grammar
  (`rules_for(prompt)`), and replays it against a llama-server. **Build on it rather than writing a second replay
  tool.** Bring the two files over with `git checkout origin/nd-paper -- <file>` on a new branch from `sched-study`.
- Work on a new branch, for example `echo-test`. Do not change `fieldmind/` (agent code) or any config thresholds.

### Step 1: a tested echo tool over saved runs (no model calls)

Add `bench/echo_test.py` with a `saved` subcommand that reads run files and reports, per run and per lane:

- **line1**: share of diagnostician answers whose rank-1 line is 1.
- **identity**: share of answers whose ranked lines are exactly 1, 2, ..., k.
- **chance**: mean of 1 / (number of case lines shown).
- **deviation accuracy**: among answers with rank-1 not equal to line 1, the share whose rank-1 case is the true
  case. Compare with (a) the share where line 1 was the true case, and (b) a random other line
  (true case among the other lines / (k-1)).
- All of the above twice: **exact case** (`ground_truth.root_cause_id`) and **look-alike group**. Use the
  evaluator's group map (`bench/evaluator.py`, `_groups(asset)`) so scoring cannot drift from the evaluator.
- Fault episodes only, ticks from fault onset onward: `tick * tick_period_s >= fault_onset_t`.

Parsing: the case lines are the numbered lines after `RETRIEVED CASES:` up to the first blank line
(`<n>. <CASE-ID> ...`). The answer is `json.loads(raw_reply)["r"]`, a list of `[case_line, [fact_lines]]`.
Envelope fields used: `agent == "diagnostician"`, `status == "ok"`, `backend`, `model`, `prompt`, `raw_reply`,
`retrieved_cases`, `calls[].prefill / prefill_ms / decode / decode_ms`.

**Fidelity targets.** The tool must reproduce these scratch-script counts. If it doesn't, find out why before
going on:

| run | n | line1 | identity |
|---|---|---|---|
| `cranfield_dev_v3_shuffled` | 423 | 1.000 | 0.998 |
| `cranfield_dev_v3` | 422 | 0.998 | 0.991 |
| `bevideas_A1` (dev) | 404 | 0.985 | 0.973 |
| `multi_v2_6mark` (exact case, post-onset) | 227, of which 131 deviate | deviations right 0.008 | |

Tests: line-1 and identity counts on a hand-built run file; deviation accuracy on a case where the deviation is right
and one where it is wrong; shuffled order mapped back to case IDs correctly; reporting episodes refused by default.
Mutation-check them (see Part 3).

### Step 2: pre-register before any new model call

Write `reports/echo_prereg.md` and commit it **before** step 3. It must fix:

- **Request set (dev only):**
  - boiler dev from `bevideas_A1` (10 `dev_*` episodes);
  - Cranfield dev from `cranfield_dev_v3`;
  - TEP from `af_tep_v3_board`. **First confirm in `reports/b2_tep_pack.md` whether the 22-episode board subset is
    dev or reporting.** If it is reporting, use TEP dev requests from a mock dev run instead, and say so.
  - Deduplicate identical prompts. Draw a seeded sample, with the seed written down. Suggested: up to 150 per plant
    for a quick pass, then the rest if the quick pass is clear.
- **Orderings per request:**
  - original;
  - 2 seeded shuffles, seeded per request, not per tick. The agent's own `case_order: shuffled` is seeded by the
    tick alone, which correlates episodes; this was recorded as an open item in `reports/multi_phase2_prompt_shrink.md`;
  - one where line 1 moves to the last line.
- **Shuffle mechanics:**
  - permute the case lines and renumber them 1..k;
  - keep the line -> case map and map answers back through it;
  - if `sep` points at a case line, remap it too. Fact lines, note lines and everything else stay byte-identical;
  - the case count, and so the grammar, is unchanged.
- **Format arm:** the same requests with group letters on (v2 format) and off (v3), to test whether the letters alone
  flip behaviour on other models too. Rebuild the v2 form by the reverse of the v3 change, and check it against a
  saved v2 prompt.
- **Models, all at temperature 0, same grammar, same `max_tokens` (diagnostician cap 60):**
  - M1: the exact board file `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf` on the laptop (CPU or Metal);
  - M2: the same Llama 3.2 3B at F16 (and Q8_0 if time allows). **M1 vs M2 isolates quantization**;
  - M3 and M4: larger open models, for example a 7-8B instruct model at Q8_0 or F16, one each from two families;
  - M5 (optional): a cloud model through the existing `gemini` backend. It has no llama.cpp grammar, so record
    that its conditions differ.
  - Pass model files on the command line, never hard-coded. Record each file's sha256 and the llama-server build
    and version. The laptop build is not the pinned board build; say so in the report.
- **Measures:**
  - line1 rate per ordering;
  - **position invariance**: the same case chosen under every ordering of a request;
  - rank-1 accuracy (exact and group) per ordering;
  - deviation accuracy;
  - prompt and answer tokens;
  - laptop latency, labelled laptop time.
- **The outcome rules**, written as numbers before running. These are PROPOSED thresholds: agree them in the team
  first, then fix them in the file.
  - "copies position": shuffled line1 >= 0.8 and position invariance <= 0.5.
  - "reads the cases": invariance >= 0.8, and shuffled accuracy within 0.05 of original.
  - "helps beyond line 1": deviation accuracy above both line 1's and a random other line's, with a 95% interval
    from an episode-level bootstrap (resample episodes, not requests).
  - Which of outcomes 1-4 each combination means, using the table in Part 1.
- **Stop rule:** M1's replies to the *original* order must match the saved board replies for most requests (rank-1
  identical). Saved replies came from the NPU and M1 runs on the laptop, so some differences are expected; Gagan
  measured 29% of requests vary even NPU-vs-NPU. If rank-1 agreement is poor, the replay is not faithful: stop and
  fix it before reading anything else.

### Step 3: run on the laptop

Start one llama-server per model, with the same flags as the lanes where they apply: `-c 4096 -np 1 --cache-ram 0`
and grammar on. Run the quick pass, write the results table, then decide on the full pass under the rules you
pre-registered. Keep every reply: raw text, the ordering used, and the line -> case map.

### Step 4 (optional, needs the board): NPU vs CPU with the same file

Same requests, same `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, board NPU lane vs board CPU lane. This fits into
Gagan's pre-registered day-1 test (`reports/nd_stage1_repeat_tool.md`, arms N and C). Do both in one board session.
Combined with step 3, this separates the NPU, the quantization and the model size.

### Report

`reports/echo_test.md` in the project report format (Status, Verification, Direction checks, Constants, Numbers
that changed, Disagreements, Blocked, What I could not verify). The main table: one row per model, one column group
per measure, original vs shuffled side by side, with the line-1 (retriever) and belief baselines. State which
outcome (1-4) the rules give.

---

## Part 3: project rules that apply here (from CLAUDE.md)

- **Dev only for decisions.** Reporting episodes (`ep_*`, the 30 boiler reporting set and the other plants'
  reporting sets) are never used to choose anything.
- **Pre-register, then run.** Thresholds and outcome rules are committed before the first new model call. If a
  number moves and you can't say why, stop and write that down. Do not adjust things until it looks right.
- **Verification protocol for every new file:**
  - run it and paste the full output;
  - run its tests;
  - re-derive one headline number by a different method;
  - corrupt one constant the tests should catch, confirm a test fails, restore it, and report which test caught it.
- **Mock numbers are not model results.** Laptop timings are not board timings. Energy stays `null` unless measured
  on the device.
- **Board rules if you do step 4:**
  - pinned build `99b95488c`;
  - `LD_LIBRARY_PATH` and `ADSP_LIBRARY_PATH` on every `adb shell`;
  - sha256 check after every push;
  - chip temperature before and after;
  - `-c 4096 -np 1 --cache-ram 0 -fit off -lv 4`.
- **Python:** `.venv/bin/python`, tests with `.venv/bin/python -m pytest`.
- Commit with `echo-test` in the message. Do not push without asking the team.

## Open items to settle as a team

1. The outcome thresholds in step 2. They are proposals, not decided.
2. Which larger models (M3, M4) fit on the laptops we have.
3. Whether the TEP board subset is dev or reporting.
4. Whether the boiler B-family tube-leak case matches its own facts. If the larger models reject it, outcome 4 is
   likely. Check the case line against the facts the L1 layer emits on dev B episodes.
