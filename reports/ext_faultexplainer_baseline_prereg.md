# External audit 1b: a code-only baseline for FaultExplainer. Pre-registration

**Status: AGREED 2026-11-13 11:51 (see "Agreed"). Written 2026-11-13 before the baseline was run on any real request.** Items marked PROPOSED must be
agreed, and dated under "Agreed", before the baseline is run on the nine requests and scored. Until then only the
plumbing pilot below has touched the real request file, and its picks were not printed or read.

**What it adds to** `reports/ext_faultexplainer_prereg.md`: that audit can show whether FaultExplainer's LLM copies a
position. It cannot show whether the LLM adds anything over code, because FaultExplainer has no step that names a cause
without the LLM. Our own agent was judged against "the agent with the model switched off". This gives FaultExplainer
the same comparison. Nothing in that file changes.

**This is a weak, simple baseline.** A model that does not beat it adds little. A model that beats it has not yet
been shown to beat a good baseline.

| item | value |
|---|---|
| Code | `bench/ext_faultexplainer.py` (`baseline`, `references`; `score` is unchanged), tests `tests/test_ext_faultexplainer_baseline.py` |
| Requests | `reports/data/ext_faultexplainer_requests.json` (unchanged): 9 PCA-detected faults (5, 6, 7, 8, 10, 11, 12, 13, 14), 3 prompt forms, 4 orderings |
| Rows | 108, label `code_overlap`, in `results/ext/faultexplainer_code_overlap.jsonl` |
| Model calls | none. No board, no energy figure |
| Data | TEP is a public simulation benchmark; the files are FaultExplainer's own |

## The ranker (fixed)
It uses only what each request already holds: the six `top_features` in T2 order, and the 15 cause lines of the prompt's
own list.

1. **Content words** of a text: lower case, split on anything that is not a letter, keep words of 3 letters or more that
   are not in the stop list. Whole words only: "Temp" does not match "Temperature".
2. **Score of a cause:** for each of the six features that shares at least one content word with the cause's line, add
   that feature's rank weight: 6 for the feature with the largest T2 contribution, down to 1 for the sixth.
3. **Ranking:** by score, highest first. **Ties go to the lower IDV number.** So the ranking does not depend on where a
   cause sits in the list.
4. **The answer** is the top three. When fewer than three causes score above zero, the remaining places are filled by
   the tie rule, so they are the lowest IDV numbers. The number of causes scoring above zero is recorded per request
   (`n_scoring`) and reported.

| constant | value | provenance | range | affects |
|---|---|---|---|---|
| rank weights | 6, 5, 4, 3, 2, 1 | CITED: `HANDOFF_BUILD_LIST.md` B1, committed 2026-11-13 03:12 (`f1096ef`) | – | which cause wins when two are matched by different features |
| shortest word | 3 letters | CITED: the same | – | drops the single-letter component names (A, B, C, D, E) |
| tie rule | lower IDV | CITED: the same | – | every tie, and every place filled at score zero |
| stop list | the, and, for, with, from, into, that, this, are, was | DESIGN (mine, 2026-11-13) | this list, or empty | nothing on the audited cause list, which holds no such word of 3 letters or more; it guards a feature name that might |

**The stop list holds English function words only.** Process words that many causes share ("feed", "stream", "step",
"temperature") are deliberately left in. Removing them would be a choice about this benchmark, and I have seen the
cause list.

## What is run
`bench/ext_faultexplainer.py baseline reports/data/ext_faultexplainer_requests.json --out results/ext/faultexplainer_code_overlap.jsonl`,
then `score` and `references` on the result, beside every valid model arm.

## Measures
All are counts out of 9, per form and ordering, with no significance claims (the style of the main audit).

- **Top-1 right and top-3 right** under the paper's alias rule, from the unchanged `score`.
- **`n_scoring`:** how many of the 15 causes any feature matched, per request. Requests where it is 0 are answered
  "1, 2, 3" by the tie rule and are listed.
- **Shuffle check:** the picks must be identical in all four orderings. This is a property of the ranker, checked on
  the real rows.
- **Reference answers** (`references`):

| reference | top-1 right of 9 | top-3 right of 9 | how it is known |
|---|---|---|---|
| uniform random three causes (expected) | 1.27 | 3.38 | from the fault numbers and aliases alone |
| the first three lines, `original` | 1 | 1 | from the fault numbers and the ordering alone |
| the first three lines, `shuffle_a` | 1 | 4 | the same |
| the first three lines, `shuffle_b` | 3 | 3 | the same |
| the first three lines, `line1_last` | 1 | 3 | the same |
| an arm's own three most-named causes, as a constant answer | per arm | per arm | from that arm's rows, after it runs |

  These values need no model output and no baseline output, so they are stated now.

## Outcome rules (PROPOSED)
**Which model arms:** every valid model arm of the main audit (the F1 rerun, its 8-bit arm, F0 if it is run). The F1 run
of 2026-11-13 is invalid ("@" replies) and is not compared.

**Compared on:** top-3 right, `app` form, each of the four orderings. `M` is the model arm's count, `C` the code
baseline's (the same in every ordering).

| reading | rule |
|---|---|
| **the baseline carries no information** | `C` ≤ 3 (at or below the uniform expectation of 3.38) |
| **the model adds over the code baseline** | `M` − `C` ≥ 2 in all four orderings |
| **the model does not add over the code baseline** | `M` − `C` ≤ 0 in all four orderings |
| **undetermined** | anything else; reported ordering by ordering |

- **If the baseline carries no information,** the model-against-baseline readings are still reported, but the paper
  may only say what the comparison with chance says. A model "not beating" an empty baseline is not evidence that it
  adds nothing.
- Top-1 counts are reported beside these. They do not decide a reading.

| threshold | value | provenance | range | affects |
|---|---|---|---|---|
| "adds" margin | 2 of 9 | DESIGN: one fault is the smallest possible difference and each fault has one trajectory | 1–3 | how easily a model is said to add |
| "no information" bound | 3 of 9 | DERIVED: the uniform expectation 3.38, rounded down | 3–4 | whether the baseline comparison may be used in the paper |

## Expected, stated before running
| item | expectation | reason |
|---|---|---|
| picks across orderings | identical | the ranker reads content and breaks ties by IDV number |
| fault 5 | wrong (top three 1, 3, 6) | worked out by hand from request 0, see below |
| the other eight faults | **no stated expectation** | their features were not looked at |
| overall | likely weak | the feature names and the cause names use different words ("Reactor Coolant Temp" against "Reactor Cooling Water Inlet Temperature"); the build list says so too |

A weak result is a result. **The ranker is not changed after its scores are seen.**

## What has already been seen
- **The 15 cause lines,** while reading the request file's format.
- **Request 0 (fault 5): its six features.** From them and the cause list the baseline's answer can be worked out by
  hand: "D Feed" and "E feed load" share "feed" with causes 1, 3, 6, 8, 9 and 10 (score 7 each), and "Component C to
  Reactor" shares "reactor" with causes 4, 11 and 14 (score 1 each). The top three are 1, 3, 6. Fault 5's accepted
  answers are 5, 12 and 15, so the baseline misses fault 5. **This one outcome of nine was known before this file was
  written.**
- **The weights, the word rule and the tie rule** were fixed in `HANDOFF_BUILD_LIST.md` before I saw either of the above.
  **The stop list was chosen after.** It changes nothing on this cause list.
- **The other eight requests' features:** not looked at.
- **Pilot:** the first 2 requests through `baseline`, written to a scratch file. Checked: row count and field names
  only. The picks were not printed.
- **GPT-4o's and o1-preview's picks** in the paper's Table 1 are public and were read for the main audit.

## Limits, stated now
- **Nine faults, one trajectory each.**
- **Word overlap is not diagnosis.** It knows nothing about the process, and a strong code baseline (a classifier
  trained on TEP) would be a different and larger piece of work. The paper must describe this as the weakest
  reasonable "model switched off" comparison.
- **The tie rule favours low IDV numbers.** With many ties the baseline drifts toward "1, 2, 3", which is also the first
  three lines of the `original` ordering. `n_scoring` is reported so this can be seen.

## Agreed
**A1, 2026-11-13 11:51 (laptop time), by Shubham ("yeah i agree it with"), before the baseline was run on the nine requests.**
Every PROPOSED item is agreed as written, unchanged: the ranker, the "adds" margin of 2 of 9 and the "no information"
bound of 3 of 9.

**The human's stated view at agreement, recorded:** the baseline is to be treated as a minor row beside chance, the
first three lines and the arm's constant answer, not as the basis of a claim. A stronger "model off" comparison (a
classifier trained on TEP data) is to be decided after the model rerun.
