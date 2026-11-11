# Echo replay — pre-registration (DRAFT)

**Status: DRAFT, 2026-11-11.** Written before any replay call. Every number marked PROPOSED must be agreed by the team
and this file committed again, with the agreement recorded under "Amendments", **before the first replay call**. Until
then no replay result may be read.

The question: is the diagnostician's position echo (it picks line 1 of the case list, also when the list is shuffled;
`reports/echo_saved.md`) a property of the 4-bit board file, of the 3B model, or of the prompt? Laptop replays test the
model, not the NPU. All plant data behind the prompts is synthetic (boiler) or recorded (Cranfield rig, TEP simulator).

## Request sets (fixed now)

| set | source | selection | size |
|---|---|---|---|
| **R: replay requests** | saved board dev runs `bevideas_A1` (boiler), `cranfield_dev_v3`, `af_tep_v3_board` (the TEP board subset is the dev runs cut to 16 h, `reports/b2_tep_pack.md`) | `bench/echo_test.py select --n 150 --seed 0`. Full-answer format, two or more case lines, identical prompts once, the rebuilt grammar must accept every saved reply (0 refused) | 450 (150 per plant, from 397 / 277 / 3,927 available) |
| **L: letter pairs** | mock lockstep dev runs with `multi.compact.group_letters` off and on, every prompt recorded (`run_demo.py --record-prompts`). Prompts do not depend on model answers (`f6bd178`) | `bench/echo_test.py pairs --n 150 --seed 0`; a pair is kept only when the two prompts differ in the letters alone. Available 989 boiler, 277 Cranfield, 18,274 TEP; 10 TEP pairs excluded because the letters made the prompt long enough for the size guard to cut the fourth case line (`tep_F17_r1`), so they differ by a whole case | 450 (150 per plant), `reports/data/echo_letter_pairs.json` |

Both selections are made without looking at any replay reply.

## Orderings (fixed now)
For each request in R: `original`; `shuffle_a` and `shuffle_b`, two seeded permutations that are never the original
order (seed `"0:<request id>"`, so per request, not per tick); `line1_last`, line 1 moved to the end. Only the
RETRIEVED CASES block is reordered and renumbered. Every other byte stays, and the grammar is unchanged. L is sent in
the original order only, once with letters (`--field prompt_letters`) and once without.

## Arms

| arm | file | where | status |
|---|---|---|---|
| **M1** | `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, the board file, sha256 checked against `bench.board.CANDIDATES` | this laptop (Apple M2, 8 GB), Homebrew llama.cpp 11429 `d81235049`, not the pinned board build | needs the file from Gagan |
| **M2** | the same Llama 3.2 3B Instruct at Q8_0, built with `bench/build_candidate_gguf.sh` at the pinned commit | this laptop | needs the Hugging Face licence and weights |
| **M3, M4** | two larger instruct models from different families | NEEDS A DECISION: Gagan's M5, or a cloud model through `GeminiBackend` (no grammar, prompts sent outside) | open |

Same settings for every arm: temperature 0, seed 0, no prompt cache, the diagnostician cap (60 tokens), the
grammar the system sends. `llama-server` with `-c 4096 -np 1 --cache-ram 0`.

## Measures (fixed now; `bench/echo_test.py score`)
- **line-1 share per ordering,** against chance (the mean of 1 / case lines);
- **position invariance:** the share of requests whose rank-1 case is the same in all four orderings;
- **rank-1 right** (exact case, look-alike group) per ordering, on fault ticks from onset onward;
- **deviation accuracy:** among answers that leave line 1, the share that are right. Compare it with line 1 and with a
  random other line;
- **original-order agreement** with the saved board reply's rank-1 (fidelity; R only);
- **intervals:** 95% from 2,000 bootstrap resamples **over episodes, not requests**, with seed 20261111 (PROPOSED).

## Pilot (fixed now)
M1, the first 20 requests of R, `original` only: call time on this laptop (to size the full run) and fidelity. Pilot
replies are kept, labelled `pilot`, and not scored.

## Stop rule (PROPOSED)
If M1's original-order rank-1 agrees with the saved board rank-1 on **fewer than 80%** of the requests, the replay is
not reproducing what the system did. Stop and find why before reading any other number. Some disagreement is
expected: a different build, different hardware, and Gagan's measured NPU run-to-run variation.

## Outcome rules (PROPOSED: thresholds to be agreed)

| reading | rule |
|---|---|
| **copies position** | shuffled line-1 share >= 0.8 **and** position invariance <= 0.5 |
| **reads the cases** | position invariance >= 0.8 **and** shuffled rank-1 right within 0.05 of original |
| **helps beyond line 1** | deviation accuracy above both line 1's and a random other line's, the 95% intervals not overlapping |

| outcome | combination | where it goes (`MOBISYS_PAPERS_COMBINED.md`) |
|---|---|---|
| 1 | M3/M4 read the cases and help beyond line 1; M1 copies | Paper B: a capability threshold |
| 2 | every arm copies position | Paper B: a prompt or task effect |
| 3 | M2 reads the cases, M1 copies | Paper C, standalone: quantization causes the copying |
| 4 | M3/M4 leave line 1 but do not help beyond it | none until the case data is checked |

Any other combination is reported as found, with no outcome label.

**Letter arm (L), reported:** line-1 share and deviation accuracy, letters on against off, per arm. This tests on dev
whether the letters alone flip the behaviour, as they did on the reporting set (0.43 against 0.99).

## Not changed by this test
No agent code, config, threshold or episode. Reporting episodes are not used (`select` and `pairs` refuse them).

## Amendments
(none yet: the team's agreement on the PROPOSED items goes here, dated, before the first call)
