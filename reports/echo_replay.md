# Echo replay on Gagan's Mac (HANDOFF_ECHO_REPLAY.md): report

## Status
DONE — all five arms, sets R (1,800 calls each) and L (900 calls each), run 2026-11-11 21:20 to 2026-11-12 05:05 (laptop
time) on Gagan's Mac (Apple M5, 24 GB, Metal), under the agreed pre-registration (`reports/echo_prereg.md`, Amendment A1,
committed before any replay call). **Every number is a laptop replay of the model, not an NPU result.** Plant data is
synthetic. Data: `results/echo/` (arm files, `RUNLOG.txt`, server logs, `scores/`).

**By the agreed rules the outcome is 4: the larger models leave line 1 but do not help beyond it ("none until the case data is
checked").**

## Setup
- **llama.cpp:** pinned `99b95488c` built for macOS (`llama-server --version`: build 11371, commit 99b95488c);
  `--list-devices` shows MTL0 Apple M5.
- **Server, every arm:** `-c 4096 -np 1 --cache-ram 0 -ngl 99`, one server at a time.
- **Pilot (20 requests, M1, original order):** `original_agrees_with_saved_rank1` = 1.0 (stop rule ≥ 0.80: passed);
  1.2 s per call.

| arm | file | bytes | sha256 | source |
|---|---|---|---|---|
| M1 `m1_q4_0` | the board's own file | 2,012,612,832 | `5aa3ece5…` | copied from the board 2026-11-11 |
| M2 `m2_q8_0` | Q8_0, `--pure` | 3,421,899,488 | `d91f61ab…` | `unsloth/Llama-3.2-3B-Instruct` @ `006f5dcd` |
| M2b `m2b_bf16` | the 16-bit conversion | 6,433,688,288 | `f9e8a86e…` | same |
| M3 `m3_qwen25_7b_q4_0` | recipe Q4_0 + emb Q8_0 | 4,835,881,568 | `723c8cf9…` | `Qwen/Qwen2.5-7B-Instruct` @ `a09a3545` (Apache-2.0) |
| M4 `m4_llama31_8b_q4_0` | recipe Q4_0 + emb Q8_0 | 5,051,115,200 | `cc8f3ba7…` | `unsloth/Meta-Llama-3.1-8B-Instruct` @ `a2856192` (llama3.1; Meta's repo is gated) |

- **Both machines produced identical files.** M2, M2b and the recipe Q4_0 rebuild (`dace5753…`) have the same sha256 on
  Gagan's Mac as on Shubham's.
- **M1 vs the rebuild:** identical weight data (sha256 `644749ed…`), headers differ by 512 bytes. Only descriptive
  metadata differs: `general.name`, `finetune`, `basename`, `license`, `base_model.*`, `tags`, `languages`. No architecture,
  tokenizer or tensor field differs, so M1 against M2 isolates the quantization.

## Results, set R (450 requests, 150 per plant), pooled
95% intervals from 2,000 bootstrap resamples over episodes, seed 20261111 (`scores/R_pooled.json`; per plant in
`scores/R_<plant>.json`; the rule table in `scores/verdicts.txt`).

| arm | line 1 picked, original | shuffled (a, b) | line 1 last | position invariance | copies position | reads the cases | helps beyond line 1 |
|---|---|---|---|---|---|---|---|
| M1 3B Q4_0 | 0.991 | 0.971, 0.973 | 0.978 | 0.000 | yes | no | no |
| M2 3B Q8_0 | 0.913 | 0.887, 0.864 | 0.880 | 0.080 | yes | no | no |
| M2b 3B 16-bit | 0.922 | 0.891, 0.871 | 0.887 | 0.071 | yes | no | no |
| M3 Qwen2.5 7B | 0.629 | 0.482, 0.482 | 0.473 | 0.338 | no | no | no |
| M4 Llama 3.1 8B | 0.580 | 0.356, 0.400 | 0.416 | 0.478 | no | no | no |

**When the model leaves line 1** (original order, pooled):

| arm | times | right [95% CI] | line 1 would have been right [CI] | a random other line [CI] |
|---|---|---|---|---|
| M3 | 163 | 0.160 [0.087, 0.252] | 0.190 [0.082, 0.336] | 0.116 [0.071, 0.168] |
| M4 | 185 | 0.141 [0.073, 0.233] | 0.238 [0.116, 0.383] | 0.120 [0.072, 0.184] |

Per plant the reading is the same:
- M3 and M4 leave line 1 in every plant and help beyond it in none;
- no arm reads the cases;
- M1 copies everywhere; M2 and M2b copy everywhere except the boiler, where the shuffled line-1 share is 0.777 and 0.780,
  just under 0.8.

## Outcome by the agreed rules
- **Outcome 1:** no. M3 and M4 do not "read the cases" (invariance 0.34 and 0.48, against ≥ 0.8) and do not "help beyond
  line 1".
- **Outcome 2:** no. M3 and M4 do not copy position.
- **Outcome 3:** no. M2 does not read the cases. The 16-bit and 8-bit 3B copy almost as much as the 4-bit file.
- **Outcome 4: yes.** M3 and M4 leave line 1 (shuffled line-1 share 0.48 and 0.38) but their picks are no better than line 1
  or a random line. Per the pre-registration: **no paper outcome until the case data is checked** (open item 4 in
  `HANDOFF_ECHO.md`: does each case line match the facts the L1 layer emits).

## Letter set L (450 pairs, original order), letters off against on
| arm | line 1, letters off | letters on | picks off line 1 right, off / on | line 1 would be right |
|---|---|---|---|---|
| M1 | 0.993 | 0.667 | 0.000 / 0.051 | 0.392 |
| M2 | 0.904 | 0.656 | 0.150 / 0.086 | 0.392 |
| M2b | 0.918 | 0.660 | 0.114 / 0.087 | 0.392 |
| M3 | 0.662 | 0.647 | 0.148 / 0.107 | 0.392 |
| M4 | 0.613 | 0.480 | 0.135 / 0.117 | 0.392 |

On dev data, the group letters alone move the 3B off line 1 (0.99 → 0.67), as the reporting-set observation suggested, and
those picks are worse than line 1. The larger models change less.

## Verification
| step | result |
|---|---|
| ran the module | 5 arms × 2,700 calls, every status ok; `RUNLOG.txt` has each server command and start/end |
| self-tests | `tests/test_echo_test.py`, `test_sched_study.py`, `test_sched_policies.py`, `test_sched_replay.py`: 59 passed |
| independent re-derivation | M1's line-1 share was first read from an inline count of the raw files (0.991 original), equal to the tool's |
| stop rule | pilot 20 / 20 and full original order 0.987 (M1) agree with the saved board rank-1 (≥ 0.80) |

## Disagreements recorded, not resolved
- **M3 and M4 agree with the board's saved rank-1 on only 0.63 and 0.58 of requests.** Expected for different models; the
  stop rule is defined for M1's fidelity and M1 passes it.
- **"Reads the cases" needs invariance ≥ 0.8; the best arm reaches 0.48.** No arm is close, so the accuracy half of that
  rule never came into play.

## What I could not verify
- **Whether the case data is the cause** (outcome 4's open question): not checked here.
- **The NPU side:** this is a laptop replay. The optional board check (M1 on the NPU, original and shuffled) was not run.

**Not pushed.** The handoff says to tell Shubham before pushing.
