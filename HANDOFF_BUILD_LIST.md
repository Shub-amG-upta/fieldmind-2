# Build list for the second laptop (paper B: echo + 4-bit + measurement)

Written 2026-11-13. These are the pieces of paper B that are **not built yet**. The run pieces are in
`HANDOFF_4BIT.md` (the 4-bit confirmation) and `HANDOFF_MAC_RUNS.md` (FaultExplainer on the board).

**The order matters:** B1 is needed whatever the 4-bit confirmation shows. B2 is next. B3 waits for an API decision.

| # | piece | why | time | blocked on |
|---|---|---|---|---|
| **B1** | FaultExplainer code-only baseline | Without it, the outside check shows whether FaultExplainer's LLM copies, but not whether it adds anything over the code | about 1 day | nothing |
| **B2** | Prompt ablation for our agent | Shows which prompt cue the 3B copies | half a day to build, one Mac night to run | nothing |
| **B3** | Strong cloud model on our prompts | Shows whether the right answer can be found from our prompt at all | about 1 day | the human's OK to send prompts to an API |

---

## Rules for every piece (from `CLAUDE.md`)
- **Branch:** build on a new branch from `bc-build` (commands at the end). Never on `main`.
- **Python:** always `env -u PYTHONPATH .venv/bin/python` (this laptop exports a QAIRT path that breaks imports).
- **Rules before results:**
  - every piece that produces a number gets a short pre-registration, `reports/<name>_prereg.md`, marked DRAFT;
  - the human agrees it, dated, under "Agreed", **before the first scored call**;
  - a pilot of 2–3 requests may run before that. It is labelled `pilot` and not scored.
- **No invented numbers:** every constant is CITED (file and line, or paper and section), FITTED (method stated) or
  DESIGN (with a range and what it affects).
- **Never use the 30 reporting episodes.** `bench.echo_test.select` refuses them already.
- **Before you hand anything back:**
  1. run it, and keep the output;
  2. run its tests;
  3. re-derive one headline number by a different route;
  4. break one thing a test should catch, see the test fail, put it back.

  Report all four in `reports/<name>_build.md` (format in `CLAUDE.md`, "Report").
- **Tests check outcomes, not formulas:** fake models with a known behaviour (a copier, a reader) on the real request
  files, as in `tests/test_echo_causes.py` and `tests/test_echo_4bit.py`.

---

## B1. FaultExplainer code-only baseline

**What FaultExplainer does:** PCA (T2) detects a TEP fault and picks the 6 variables with the largest T2
contributions. Its LLM is then asked which of 15 listed root causes, IDV(1)–IDV(15), explains them.
`bench/ext_faultexplainer.py` already rebuilds its prompts (`reports/data/ext_faultexplainer_requests.json`, 9 detected
faults: 5, 6, 7, 8, 10, 11, 12, 13, 14) and scores replies.

**What is missing:** a ranking of the 15 causes **made by code only**, from the same 6 variables. Our agent was judged
against "the agent with the model switched off"; FaultExplainer needs the same comparison.

**Build:**
1. **A new subcommand `baseline` in `bench/ext_faultexplainer.py`**, which writes rows in the same format as `run`, so
   the existing `score` reads them unchanged. Label `code_overlap`.
2. **The ranker uses only what is in the request:** the 6 `top_features` in T2 order, and the 15 cause lines of the
   prompt's own list (`root_lines` and the text after `_LIST_HEAD`).
   - **Score per cause:** for each of the 6 features that shares a content word with the cause's line, add a weight
     for its T2 rank (6 for rank 1 down to 1 for rank 6).
   - **Content word:** lower case, letters only, at least 3 characters, not in a short stop list.
   - **Ties** go to the lower IDV number.
   - **Top 3** = the reply's three picks.
   - The weights, the stop list and the word rule are DESIGN choices. Write them in the pre-registration **before
     looking at any score**.
3. **Also report the existing baselines** next to it: uniform random top-3, the first three lines, and the arm's most
   frequent answer.
4. **Pre-registration `reports/ext_faultexplainer_baseline_prereg.md`:**
   - the ranker above;
   - the outcome rule as counts out of 9, no significance claims (the existing FaultExplainer pre-registration's style);
   - one sentence stating that this is a weak, simple baseline, so a model that does not beat it adds little, and a
     model that beats it has not yet been shown to beat a good baseline.

**Tests** (`tests/test_ext_faultexplainer_baseline.py`):
- a hand-built request where one cause shares words with the top feature: that cause is ranked first;
- the rank weights change the order when two causes share words with different features;
- ties go to the lower IDV;
- rows written by `baseline` are read by `score` with the expected top-1 and top-3;
- the shuffled orderings give the **same** code picks (the ranker reads content, not position).

**Done when:**
- `baseline` writes `results/ext/faultexplainer_code_overlap.jsonl`;
- `score` prints its top-1 and top-3 beside the board arm;
- the build report is written.

**Watch out:** FaultExplainer's cause names and the TEP variable names use different words (for example "Reactor
Cooling Water Inlet Temperature" against "Reactor Coolant Temp"). The overlap may be weak. **That is a result, not a
reason to tune the rule after seeing the scores.**

---

## B2. Prompt ablation for our agent

**Question:** the 3B picks line 1 about 97% of the time. Is it copying the worked example, the code's "belief" line,
or line 1 itself?

**The three cues**, each present in all 450 prompts of set R (`reports/data/echo_requests.json`):
- `Example: {"r":[[2,[1,3]],[1,[1]]],...}`, the worked example. The 0.5B and Gemma 1B copy its "2";
- `WORLD MODEL: belief (from code): ...`, the code's ranking in words;
- the order of the case lines itself.

**Build:**
1. **A new file `bench/echo_ablate.py`** (or a new test in `bench/echo_causes.py`) with four forms per request:
   - `full`;
   - `no_example`: the `Example:` line removed;
   - `no_belief`: the `WORLD MODEL: belief (from code):` line removed;
   - `no_both`.

   Each form is sent in two orderings, `original` and `shuffle_a`, from `bench.echo_test.orderings`, so 8 calls per
   request.
2. **Remove only those lines.** Every other byte stays, and the grammar is rebuilt with `echo_test.rules_for`, as in
   `relabel`.
3. **Run function, resumable,** in the style of `run_relabel` (`_done`, `_append`, `_write`). Add a step to
   `bench/echo_mac_runs.sh` or a new script.
4. **Measures per form:**
   - share of answers on line 1 (both orderings);
   - share answering label "2";
   - right, group credit, original order;
   - departures right against a random other line (as E3).
5. **Arms:** Llama 3B 4-bit (`m1_q4_0`) and 8-bit (`m2_q8_0`), Gemma 1B, Llama 8B. About 4 × 450 × 8 = 14,400 calls,
   one Mac night.
6. **Pre-registration `reports/echo_ablate_prereg.md`,** with rules in the style of `reports/echo_causes_prereg.md`, for example:
   - **"the example drives it":** shuffled line-1 share falls by ≥ 0.20 from `full` to `no_example`, interval excluding 0;
   - the same for `no_belief`.

   Expected directions, stated before running:
   - `no_example` lowers the "2" answers for the small models;
   - no stated direction for the 3B.

**Tests:**
- each form removes exactly its line and nothing else (compare with the original after putting the line back);
- the grammar still accepts every case label shown;
- a fake model that copies the example's first number answers "2" in `full` and something else in `no_example`;
- a fake line-1 copier gives the same line-1 share in all forms;
- resuming sends nothing twice.

---

## B3. Strong cloud model on our prompts (only after the human says yes)

**Question:** if a much stronger model also cannot beat the code's line 1 on set R, the limit is the evidence in the
prompt, not the small model.

**Build only after the human's OK** to send set R's prompts to an API. They hold synthetic boiler data and public
Cranfield and TEP data. Then:
- **Reuse the existing cloud backend** in `fieldmind/runtime/llm_backend.py` if it fits. Otherwise add one class with
  one method and `register_backend()`.
- **Fill `LLMReply`'s latency, model and token fields** from the API's own numbers. No energy.
- **Original order and `shuffle_a` only,** 450 × 2 calls. Score with `bench/echo_test.py score`.
- **Pre-registration first:** the model name and version, the date, and the rule ("beats line 1" = group difference
  ≥ +0.05, interval excluding 0, as E2/E3).
- **The model name lives in the config or the label, never in the code.**

---

## Commands

**1. Get the code** (the 4-bit tools and this file are on `bc-build`):
```
git fetch mine
git switch -c bc-build-2 mine/bc-build
env -u PYTHONPATH .venv/bin/python -m pytest -q tests/test_echo_4bit.py tests/test_echo_causes.py tests/test_echo_test.py
```
Expect all to pass (52 at the time of writing).

**2. Commit as you go,** one piece per commit:
```
git add bench/ext_faultexplainer.py tests/test_ext_faultexplainer_baseline.py reports/ext_faultexplainer_baseline_prereg.md
git commit -m "B1: FaultExplainer code-only baseline (DRAFT pre-registration; tests; build report)"
```

**3. Push to the same remote you pushed the earlier runs to:**
```
git push origin bc-build-2
```

**Do not push to `main`, and do not merge into `bc-runs` until the build report is written.**
