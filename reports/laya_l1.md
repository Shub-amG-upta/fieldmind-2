# Laya L1 — Laya as the System One model (laptop accuracy, NPU port check) — report

## Status
PARTIAL — Laya runs behind bev-decide's protocol, is scored on the decider's exact requests on three plants,
and is shown to load in the pinned llama.cpp with F16 parity 278/278. The pre-registered go rule for the board
run is met formally (2 of 3 dev sets) but the boiler "win" (+0.005) rests on option order; **Track C is not
started: needs a decision (Blocked 1)**. Not finished: TEP shuffled pass (95 of 3,379), the full-agent runs
with Laya in the bev slots (one probe episode only), the two sensitivity checkpoints, the board check (handoff
written). Branch `laya` from `mine/breadth-board-runs` at `ffc4312`; plan
`~/.claude/plans/declarative-seeking-rabin.md` (approved 2026-11-07). `fieldmind/` unchanged.

All boiler data is synthetic; Cranfield is real rig data; TEP is a simulated benchmark. Laya runs on the
laptop CPU (Apple M2) in Track A: its timings are laptop timings, never NPU timings. Energy: null. Decider
requests from mock runs carry mock diagnosticians (retriever order), which Llama matched in 98.5–99.6% of its
board answers; requests from board runs are verbatim.

## Results (decider pick accuracy, post-onset requests; [2.5%, 97.5%] over 2,000 episode resamples)
| set | n (episodes) | Laya | Laya, options shuffled | belief top | retriever top | Laya on the retriever's requests | bev |
|---|---|---|---|---|---|---|---|
| boiler dev (mock requests) | 462 (8) | 0.656 [0.36, 0.85] | 0.385 [0.22, 0.51] | 0.660 | 0.684 (n 399) | 0.689 (n 399) | – |
| Cranfield dev (mock requests) | 331 (6) | 0.360 [0.09, 0.75] | 0.281 [0.13, 0.51] | 0.248 | 0.214 (n 313) | 0.358 (n 313) | – |
| TEP subset (mock requests) | 2,587 (20) | 0.227 [0.13, 0.33] | not run (95 / 3,379) | 0.256 | **0.408** (n 2,452) | 0.235 | – |
| boiler reporting, `bev3_armB` (board requests) | 629 (10) | 0.437 [0.29, 0.61] | 0.304 | 0.514 | 0.647 (n 496) | 0.476 | 0.472 |
| Cranfield dev, `cranfield_dev_v3_bev` (board requests) | 331 (6) | 0.353 | 0.290 | 0.248 | 0.214 (n 313) | 0.351 | 0.347 |

| set | Laya picks the first option | after shuffle, picks the first listed | chance | choice unchanged by the shuffle | options cut at Laya's 48-token cap |
|---|---|---|---|---|---|
| boiler dev | 80.7% | 70.6% | 22.7% | 36.6% | 100% |
| Cranfield dev | 42.6% | 35.3% | 29.3% | 65.0% | 0% |
| TEP subset | 41.0% | (52.4%, n 63) | 22.7% | (39.7%, n 63) | 0% |
| boiler reporting | 72.3% | 70.9% | 24.0% | 33.5% | 100% |

State truncation: 0% everywhere. Per-episode tables: `results/laya_l1/laya_l1_primary.md`; summary JSON
`reports/data/laya_l1_summary.json`.

**Pre-registered rule (Track C):** Laya beats the retriever on the same requests on boiler dev (0.689 vs 0.684)
and Cranfield dev (0.358 vs 0.214), not on TEP (0.235 vs 0.408): 2 of 3, rule met. Read with the order test:
on the boiler Laya follows list position (first option 80.7%, chance 22.7%; with shuffled options it picks
the first listed 70.6% and its accuracy falls 0.656 -> 0.385), so its boiler result is belief's order passed
through. On Cranfield the lead over the retriever survives the shuffle (0.281 vs 0.214) and comes from F1, F2
and F5 (per episode: Laya 0.885 / 0.667 / 0.581 against the retriever 0.340 / 0.241 / 0.049).

**Laya against bev on bev's own board requests:** boiler reporting 0.437 vs 0.472; Cranfield 0.353 vs 0.347.
**Explain requests** (`cranfield_dev_bev_explain_skip`, 331 requests, verbatim): same citation pick as bev
199 / 530 (37.5%), same separating case 187 / 258 (72.5%). No ground truth: descriptive only.

## Track B — Laya on the NPU path (host)
- Pinned `b11371` has native support: `ModernBertDecisionModel` converter (head blocks appended to the encoder,
  temperatures as metadata) and `llama-server` `POST /v1/systemone`. No C++ of ours is needed.
- Converted from revision `7b928d828b7b0e022f929d9bd2e44165aa270148`: F16 844,026,528 B sha256 `32c8144e…`,
  Q8_0 449,396,448 B sha256 `a972d557…` (`bench.board.LAYA_FILES`). Q8_0 types: 123 Q8_0, 78 F32; one matrix
  flagged by `bench.gguf_types`: `token_types.weight` (1024 × 3, F32, the question-type table).
- Parity on 278 unique Cranfield dev requests, Homebrew llama-server 11429 on the laptop CPU (not the pinned
  build), against PyTorch Laya:

| file | top answer identical | max \|Δp\| | median \|Δp\| | input tokens identical | ms per request (laptop) |
|---|---|---|---|---|---|
| F16 | 278 / 278 | 0.0016 | 0.00019 | 278 / 278 | 2,345 (CPU shared with the scorer) |
| Q8_0 | 269 / 278 | 0.0302 | 0.00217 | 278 / 278 | 752 |

  All 9 Q8_0 flips are near-ties (PyTorch top-two margin 0.0002–0.0186); on them PyTorch was right 0 times,
  Q8_0 once. Q8_0 fails the pre-registered rule (identical on every request); F16 passes.
- Board lane added: `bench.board start|stop|log laya` (port 8083, stock llama-server, `-ub`/`-b` = 4096,
  sha256-pinned). Board check: `HANDOFF_LAYA.md`.

## Verification
| step | result |
|---|---|
| ran the module | request collection 5 sets (465 / 347 / 3,379 / 633 / 347 requests); scoring 4,857 unique calls normal pass, shuffled pass for 4 of 5 sets; evaluator; parity F16 + Q8_0; journal pairing 331 requests; one full-agent probe episode (32 decider calls routed to Laya, all ok, 298 ms mean) |
| self-tests | `tests/test_system_one.py` 15 + `tests/test_laya_router.py` 5 + `tests/test_bev_board.py`: 21 passed |
| request faithfulness | Cranfield mock-generated vs board requests at the same 347 ticks: state identical 347/347, prompt identical 314/347 (the 33 differ in options: Llama's top 3 vs the mock's) |
| independent re-derivation | Cranfield dev Laya pick accuracy recounted from `data/episodes_cranfield_dev/*/ground_truth.json` (root cause and onset read directly, no evaluator code): 119 / 331 = 0.3595; evaluator 0.3595 (shown 0.360); relative difference 0 |
| mutation check | 6 / 6 caught: onset at k·tick (`test_onset_dates_tick_k_at_k_plus_one_ticks`); yes/no read as 1−p (`test_reply_passes_the_bev_ideas_gate_check…`); identity shuffle (`test_shuffle_moves_choice_options…`); router sends every role to the mock (`test_router_sends_only_decider_role_calls…`); shuffled first-option read from the unshuffled order (`test_pick_accuracy_join…`); Laya's choice label trusted over its probabilities (`test_reply_choice_is_the_most_probable…`) |

## Direction checks
| claim | expected | measured | |
|---|---|---|---|
| shuffling options moves a position-copier's pick | first-listed rate stays high, accuracy drops | boiler: 70.6% first-listed, 0.656 → 0.385 | OK (Laya copies position on the boiler) |
| an order-free scorer is unchanged by a shuffle | choice unchanged ≈ 100% | 33.5–66.2% | FAIL for Laya: it is not order-free (expected: sequential layout) |
| quantization only moves near-ties | flips only where the margin < max \|Δp\| | 9 flips, margins ≤ 0.0186 < 0.0302 | OK |

## Constants introduced
| symbol | value | provenance | range | affects |
|---|---|---|---|---|
| shuffle / bootstrap seed | 20261107 | DESIGN (pre-registered) | any | which shuffle each request gets; interval edges |
| bootstrap resamples | 2,000 | DESIGN (pre-registered) | 1,000–10,000 | interval precision |
| `OPTION_CAP` | 48 tokens | CITED: laya 0.4.27 `common.build_head` | – | the options-cut count only |
| Laya lane `-ub` / `-b` | 4,096 (= CTX_SIZE) | DESIGN (decision 2) | ≥ longest request | whether a multi-question request fits one micro-batch |
| `LAYA_PORT` | 8083 | DESIGN | free port | board lane only |

No threshold in `configs/base.yaml` was touched; `configs/laya.yaml` changes only the bev lane's url and model name.

## Numbers that changed
None of the agent's: `fieldmind/` is unchanged and every existing test that ran passes.

## Decisions taken (conservative, recorded)
1. Board requests were read verbatim from run files instead of rebuilt (`bev3_armB` and the Cranfield run keep every decider prompt); the planned `DeciderAgent.state_text` rebuild was not needed.
2. Laya lane `-ub 4096 -b 4096`: llama-server evaluates a Laya request in one micro-batch; the human rule fixes `-c` and `-np` only.
3. Q8_0 is the file in the handoff (project rule: Q4_0 / Q8_0 only on HTP), with its parity failure stated; F16 is not to go on the NPU without a decision.
4. Two background jobs reached the 2-hour limit (the TEP shuffled pass; the full-agent decider runs). Neither was restarted automatically.

## Disagreements recorded, not resolved
1. **Go rule met, boiler result order-driven.** The rule counts boiler dev as a win (0.689 vs 0.684) though Laya's boiler picks follow list position. Both recorded; Track C waits for a decision.
2. **Why the boiler order effect is so strong is unexplained.** Tested and not supported: option truncation by count. On the boiler the first-option rate is 0.76–0.88 at every option count (3, 4, 5, 6), including 3 options where every option keeps the full 48-token budget; on Cranfield and TEP it is high at 2–3 options (0.67–0.98) and near chance at 4+. Untested candidates: boiler options all exceed 48 tokens and start with similar long technical text; the first option (belief's top) is also the most common true cause.
3. **Q8_0 fails the strict parity rule on near-ties only.**
4. **Laya on the server reports `confidence` 0.129 where PyTorch Laya reports 0.042 for the same request** (probabilities agree to 0.0012). Different definitions; not used by the agent. Unexplained.
5. Laya warns that the checkpoint ships `temperature_by_options["choice:11+"] = 0.1006`, clamped to 0.5 (no decider request has 11+ options).

## Blocked / needs a decision
1. **Track C.** (a) run the board accuracy run now (rule met); (b) first a pre-registered fix of the order effect on dev (shortened option texts; a parallel-layout checkpoint if one exists; scoring each option separately); (c) stop Laya at L1 and go to L2 (fit on a training split).
2. **NPU file.** (a) Q8_0 with its 9 near-tie flips stated; (b) F16 on HTP, against the Q4_0 / Q8_0 rule; (c) a mixed file (also against the rule).
3. Restart the two stopped jobs (TEP shuffled pass ~3,300 calls; full-agent decider runs on boiler and Cranfield dev), in chunks under the 2-hour limit.
4. `first_threshold` for Laya: the shadow run and `bench/bev_calibrate.py` table are not made yet; the threshold is a human decision in any case.

## What I could not verify
- Why the first full-agent run stalled for 2 hours with no output (the same command on one episode finished in 11 s with all 32 decider calls answered). It ran while the scorer used the CPU; not reproduced.
- Any board number: placement on HTP0, NPU latency, board parity (handoff).
- The two sensitivity checkpoints (`typed-decisions`, `multilingual`): not scored.
- Whether a domain-fitted Laya (`agent.fit`) changes the picture (L2).
- The pinned build on the host: parity used Homebrew llama.cpp 11429, not `b11371`.

## Pre-registration (fixed before any Laya answer)

### Model
- Laya, convaiinnovations, Apache 2.0, `pip install laya` in `.venv-laya/` (versions in
  `bench/requirements-laya.txt`, Hugging Face revision of each checkpoint recorded below once downloaded).
- **Primary checkpoint: `convaiinnovations/laya`** (English root). Sensitivity rows: the `typed-decisions` and
  `multilingual` subfolders. They are reported next to the primary and never selected on results.
- Each checkpoint's own default context length. Truncation is measured and reported, never fixed in L1 (a
  shortened-criteria variant would be its own pre-registered step).

### Requests (never edited for Laya)
- Questions: the existing `multi.bev.questions` sentences in `configs/base.yaml`, unedited. `q_root` is the
  decider's signed sentence; the others are still PROPOSED (reports/bev_ideas.md), so any `on` result from
  them is reported as resting on unsigned questions, exactly as for bev.
- Criteria: the agents' own option texts (`DeciderAgent.offered`, `bev.py` builders), unedited.
- `multi.bev.noul_threshold` stays 0.5 (DESIGN, as bev; range 0.3–0.7).
- `multi.bev.first_threshold` for Laya: the table from `bench/bev_calibrate.py` on boiler dev shadow runs only.
  The tool picks nothing; the threshold is a **human decision**, so `first: on` with Laya is not run until it
  is given (stop rule 1). The tool accepts only boiler `dev_*` episodes; Cranfield and TEP get no threshold.

### Sets
| set | episodes | requests from | compared with |
|---|---|---|---|
| boiler dev quick set | 8 fault + 2 normal (`dev_A01 … dev_N02`) | mock run, `configs/bev3.yaml` | belief, retriever; bev per idea from `bevideas_shadow` |
| Cranfield dev | 6 fault | mock run, `configs/bev3.yaml,configs/cranfield.yaml`; and the board run's journal | belief, retriever, bev (`cranfield_dev_v3_bev`) |
| TEP board subset | 20 fault + 2 normal (dev runs, 16 h) | mock run, `configs/bev3.yaml,configs/tep.yaml` | belief, retriever |
| boiler reporting | 10 fault (`bev3_armB`) | rebuilt from the run file | bev (reported once, never used to decide) |

Requests from mock runs carry the mock diagnosticians' top cases (retriever order), which Llama matched in
98.5–99.6% of its board answers. They are labelled "mock diagnosticians".

### Metrics
- **Decider pick accuracy**: on decider requests whose tick is at or after fault onset (tick k dated at
  (k+1)·tick, as T7), the share where the pick is in the episode's true group (summary `true_group`). Same
  for belief's top (offered[0]), the retriever's top (line 1 of that tick's diagnostician prompt, either
  side), bev where recorded, and chance (mean share of offered cases in the true group).
- First-option rate and chance; **shuffle invariance**: share of requests whose choice is unchanged when the
  options are given in one seeded shuffled order (seed 20261107, derived per request).
- Truncation rate per checkpoint and per request kind.
- Interval: bootstrap over episodes (2,000 resamples, seed 20261107), because consecutive ticks are correlated.
- Per bev idea (shadow): Laya's answer distribution and agreement with bev on the same boiler dev requests.

### Rule for going to Track C (board accuracy run)
Laya's decider pick accuracy is higher than the retriever's top on the same requests on **at least 2 of the 3
dev sets** (boiler dev, Cranfield dev, TEP subset). Otherwise L1 is reported as a negative zero-shot result
and L2 (fit on a training split) is proposed instead. Track B (port feasibility) runs either way.

### Track B pass rule (host parity of the GGUF backbone)
Pinned `b11371` converter; F16 and Q8_0 (every matrix Q8_0). Laya's own head on the GGUF hidden states against
PyTorch end to end: top answer identical on all compared requests (as bev's conformance); max |Δp| reported.

### Clarifications added after scoring started, before any Laya answer was read (2026-11-07)
- Population for pick accuracy: every decider request at or after fault onset in an episode with a true group,
  held-out episodes included (their true cause is never offered, so every model scores 0 there). A
  "library episodes only" row is reported as secondary. "Same requests" for the retriever comparison means the
  requests whose evidence tick also has a diagnostician prompt (the retriever's top exists).
- Request sources: board runs keep every decider prompt verbatim in their run files (`bev3_armB`: 633 of 633;
  `cranfield_dev_v3_bev`: 347 of 347), so nothing is rebuilt; `DeciderAgent.state_text` reconstruction (plan A4)
  was not needed.
- Onset dating: (k+1)·tick as pre-registered (T7). The evaluator's T2 dates ticks at k·tick; the two differ by
  one tick at onset. Recorded, not changed.
