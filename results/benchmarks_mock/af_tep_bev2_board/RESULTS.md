# Benchmark `af_tep_bev2_board`

**MOCK backend: plumbing only, NOT an agent result.** Architecture **multi**, mode **lockstep**, overlay `configs/bev_ideas.yaml,configs/tep.yaml`, merge rule `hybrid`, models npu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, cpu: `gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf`, bev: `bev-decider-0.4B-backbone-Q8_0.gguf`. Agent code ran on the laptop and only model calls on the board, so tick times are laptop times. Energy not measured. Plant data: simulated (Tennessee Eastman Process, Rieth et al. 2017).

bev ideas switches: `explain=on,clear_skip=on,explain_prompt=v2,empty_skip=on,one_code=on`. bev-decide on npu. bev idea calls: answered by bev-decide (failed = no answer, which makes the run invalid and is not kept; rejected = refused by the gate's check). used = an answer that changed what the agent did; shadow = asked and only logged. Decode tokens per tick: answer tokens written by every model per tick (bev writes none).

Group top-1 is the share of scored ticks (fault onset onward) whose published rank-1 cause is in the true case's look-alike group; belief group top-1 is the same for the code-only ranking. A held-out true case has no exact top-1. Unusable = a model answer that was not used (wrong format, failed call, rejected note reading). Settings and every run, stopped ones included: `test.json`.

| episode | run | finished | ticks | model calls | bev idea calls / failed / rejected | bev used / shadow | decode tokens per tick | unusable | tokens in | group top-1 | belief group top-1 | exact top-1 | faithfulness | actions P / R | lead time min | false alarms /h | tick p95 ms | wall s | chip C |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tep_board_F01_r1 | 1 | 2026-11-08 15:41 | 319 | 663 | 326 / 0 / 0 | 355 / 0 | 4.22 | 0 | 443,573 | 0.09 | 0.00 | 0.09 | 1.00 | – | – | – | 4 | 2 | – → – |
| tep_board_F02_r1 | 1 | 2026-11-08 15:41 | 319 | 554 | 272 / 0 / 0 | 343 / 0 | 3.11 | 0 | 326,205 | 0.66 | 0.66 | 0.66 | 1.00 | – | – | – | 7 | 2 | – → – |
| tep_board_F03_r1 | 1 | 2026-11-08 15:41 | 319 | 147 | 56 / 0 / 0 | 130 / 0 | 1.12 | 0 | 35,359 | 0.00 | 0.00 | 0.00 | 1.00 | – | – | – | 3 | 1 | – → – |
| tep_board_F04_r1 | 1 | 2026-11-08 15:41 | 319 | 372 | 178 / 0 / 0 | 226 / 0 | 2.03 | 0 | 154,767 | 0.88 | 0.00 | 0.88 | 1.00 | – | – | – | 4 | 2 | – → – |
| tep_board_F05_r1 | 1 | 2026-11-08 15:41 | 319 | 677 | 332 / 0 / 0 | 359 / 0 | 4.32 | 0 | 477,199 | 0.30 | 0.32 | 0.00 | 1.00 | – | – | – | 4 | 2 | – → – |
| tep_board_F06_r1 | 1 | 2026-11-08 15:41 | 319 | 658 | 324 / 0 / 0 | 351 / 0 | 4.07 | 0 | 444,081 | 0.85 | 0.82 | 0.85 | 1.00 | – | – | – | 4 | 2 | – → – |
| tep_board_F07_r1 | 1 | 2026-11-08 15:41 | 319 | 683 | 334 / 0 / 0 | 361 / 0 | 4.47 | 0 | 462,858 | 0.00 | 0.00 | 0.00 | 0.99 | – | – | – | 5 | 2 | – → – |
| tep_board_F08_r1 | 1 | 2026-11-08 15:41 | 319 | 614 | 300 / 0 / 0 | 329 / 0 | 3.98 | 0 | 417,089 | 0.18 | 0.27 | 0.18 | 1.00 | – | – | – | 5 | 2 | – → – |
| tep_board_F09_r1 | 1 | 2026-11-08 15:41 | 319 | 144 | 56 / 0 / 0 | 132 / 0 | 1.02 | 0 | 39,144 | 0.03 | 0.00 | 0.00 | 1.00 | – | – | – | 3 | 1 | – → – |
| tep_board_F10_r1 | 1 | 2026-11-08 15:41 | 319 | 468 | 195 / 0 / 0 | 229 / 0 | 4.85 | 0 | 242,260 | 0.10 | 0.07 | 0.00 | 0.99 | – | – | – | 3 | 1 | – → – |
| tep_board_F11_r1 | 1 | 2026-11-08 15:41 | 319 | 374 | 174 / 0 / 0 | 250 / 0 | 1.96 | 0 | 229,196 | 0.43 | 0.57 | 0.43 | 1.00 | – | – | – | 3 | 1 | – → – |
| tep_board_F12_r1 | 1 | 2026-11-08 15:41 | 319 | 653 | 322 / 0 / 0 | 349 / 0 | 4.04 | 0 | 464,608 | 0.92 | 0.12 | 0.92 | 1.00 | – | – | – | 5 | 2 | – → – |
| tep_board_F13_r1 | 1 | 2026-11-08 15:41 | 319 | 395 | 186 / 0 / 0 | 255 / 0 | 2.48 | 0 | 242,780 | 0.49 | 0.46 | 0.49 | 1.00 | – | – | – | 4 | 1 | – → – |
| tep_board_F14_r1 | 1 | 2026-11-08 15:41 | 319 | 435 | 199 / 0 / 0 | 272 / 0 | 2.28 | 0 | 285,590 | 0.96 | 0.33 | 0.96 | 1.00 | – | – | – | 3 | 1 | – → – |
| tep_board_F15_r1 | 1 | 2026-11-08 15:41 | 319 | 146 | 57 / 0 / 0 | 130 / 0 | 1.08 | 0 | 37,653 | 0.00 | 0.00 | 0.00 | 0.87 | – | – | – | 3 | 1 | – → – |
| tep_board_F16_r1 | 1 | 2026-11-08 15:41 | 319 | 317 | 154 / 0 / 0 | 228 / 0 | 1.89 | 0 | 178,213 | 0.97 | 0.96 | 0.97 | 1.00 | – | – | – | 3 | 1 | – → – |
| tep_board_F17_r1 | 1 | 2026-11-08 15:41 | 319 | 272 | 127 / 0 / 0 | 198 / 0 | 1.26 | 0 | 144,852 | 0.67 | 0.85 | 0.67 | 1.00 | – | – | – | 3 | 1 | – → – |
| tep_board_F18_r1 | 1 | 2026-11-08 15:41 | 319 | 399 | 193 / 0 / 0 | 237 / 0 | 2.59 | 0 | 261,563 | 0.44 | 0.46 | 0.44 | 1.00 | – | – | – | 5 | 2 | – → – |
| tep_board_F19_r1 | 1 | 2026-11-08 15:41 | 319 | 488 | 240 / 0 / 0 | 290 / 0 | 2.74 | 0 | 307,660 | 0.71 | 0.43 | 0.71 | 0.99 | – | – | – | 3 | 1 | – → – |
| tep_board_F20_r1 | 1 | 2026-11-08 15:41 | 319 | 326 | 156 / 0 / 0 | 225 / 0 | 1.87 | 0 | 194,642 | 0.84 | 0.96 | 0.84 | 0.97 | – | – | – | 3 | 1 | – → – |
| tep_board_N_r1 | 1 | 2026-11-08 15:41 | 319 | 142 | 54 / 0 / 0 | 127 / 0 | 1.03 | 0 | 34,521 | – | – | – | 1.00 | – | – | 2.82 | 3 | 1 | – → – |
| tep_board_N_r2 | 1 | 2026-11-08 15:41 | 319 | 71 | 21 / 0 / 0 | 95 / 0 | 0.37 | 0 | 8,754 | – | – | – | 1.00 | – | – | 2.45 | 3 | 1 | – → – |

## bev ideas per episode

| episode | run | idea | calls | failed | rejected | used | shadow | other counters |
|---|---|---|---|---|---|---|---|---|
| tep_board_F01_r1 | 1 | clear_skip | 0 | 0 | 0 | 4 | 0 | – |
| tep_board_F01_r1 | 1 | empty_skip | 0 | 0 | 0 | 16 | 0 | – |
| tep_board_F01_r1 | 1 | explain | 326 | 0 | 0 | 326 | 0 | over_limit 0 |
| tep_board_F01_r1 | 1 | one_code | 0 | 0 | 0 | 9 | 0 | – |
| tep_board_F02_r1 | 1 | clear_skip | 0 | 0 | 0 | 36 | 0 | – |
| tep_board_F02_r1 | 1 | empty_skip | 0 | 0 | 0 | 18 | 0 | – |
| tep_board_F02_r1 | 1 | explain | 272 | 0 | 0 | 272 | 0 | over_limit 0 |
| tep_board_F02_r1 | 1 | one_code | 0 | 0 | 0 | 17 | 0 | – |
| tep_board_F03_r1 | 1 | clear_skip | 0 | 0 | 0 | 3 | 0 | – |
| tep_board_F03_r1 | 1 | empty_skip | 0 | 0 | 0 | 40 | 0 | – |
| tep_board_F03_r1 | 1 | explain | 56 | 0 | 0 | 56 | 0 | over_limit 0 |
| tep_board_F03_r1 | 1 | one_code | 0 | 0 | 0 | 31 | 0 | – |
| tep_board_F04_r1 | 1 | clear_skip | 0 | 0 | 0 | 2 | 0 | – |
| tep_board_F04_r1 | 1 | empty_skip | 0 | 0 | 0 | 28 | 0 | – |
| tep_board_F04_r1 | 1 | explain | 178 | 0 | 0 | 178 | 0 | over_limit 0 |
| tep_board_F04_r1 | 1 | one_code | 0 | 0 | 0 | 18 | 0 | – |
| tep_board_F05_r1 | 1 | clear_skip | 0 | 0 | 0 | 2 | 0 | – |
| tep_board_F05_r1 | 1 | empty_skip | 0 | 0 | 0 | 16 | 0 | – |
| tep_board_F05_r1 | 1 | explain | 332 | 0 | 0 | 332 | 0 | over_limit 0 |
| tep_board_F05_r1 | 1 | one_code | 0 | 0 | 0 | 9 | 0 | – |
| tep_board_F06_r1 | 1 | clear_skip | 0 | 0 | 0 | 2 | 0 | – |
| tep_board_F06_r1 | 1 | empty_skip | 0 | 0 | 0 | 16 | 0 | – |
| tep_board_F06_r1 | 1 | explain | 324 | 0 | 0 | 324 | 0 | over_limit 0 |
| tep_board_F06_r1 | 1 | one_code | 0 | 0 | 0 | 9 | 0 | – |
| tep_board_F07_r1 | 1 | clear_skip | 0 | 0 | 0 | 2 | 0 | – |
| tep_board_F07_r1 | 1 | empty_skip | 0 | 0 | 0 | 16 | 0 | – |
| tep_board_F07_r1 | 1 | explain | 334 | 0 | 0 | 334 | 0 | over_limit 0 |
| tep_board_F07_r1 | 1 | one_code | 0 | 0 | 0 | 9 | 0 | – |
| tep_board_F08_r1 | 1 | clear_skip | 0 | 0 | 0 | 2 | 0 | – |
| tep_board_F08_r1 | 1 | empty_skip | 0 | 0 | 0 | 16 | 0 | – |
| tep_board_F08_r1 | 1 | explain | 300 | 0 | 0 | 300 | 0 | over_limit 0 |
| tep_board_F08_r1 | 1 | one_code | 0 | 0 | 0 | 11 | 0 | – |
| tep_board_F09_r1 | 1 | clear_skip | 0 | 0 | 0 | 3 | 0 | – |
| tep_board_F09_r1 | 1 | empty_skip | 0 | 0 | 0 | 42 | 0 | – |
| tep_board_F09_r1 | 1 | explain | 56 | 0 | 0 | 56 | 0 | over_limit 0 |
| tep_board_F09_r1 | 1 | one_code | 0 | 0 | 0 | 31 | 0 | – |
| tep_board_F10_r1 | 1 | clear_skip | 0 | 0 | 0 | 4 | 0 | – |
| tep_board_F10_r1 | 1 | empty_skip | 0 | 0 | 0 | 16 | 0 | – |
| tep_board_F10_r1 | 1 | explain | 195 | 0 | 0 | 195 | 0 | over_limit 0 |
| tep_board_F10_r1 | 1 | one_code | 0 | 0 | 0 | 14 | 0 | – |
| tep_board_F11_r1 | 1 | clear_skip | 0 | 0 | 0 | 6 | 0 | – |
| tep_board_F11_r1 | 1 | empty_skip | 0 | 0 | 0 | 24 | 0 | – |
| tep_board_F11_r1 | 1 | explain | 174 | 0 | 0 | 174 | 0 | over_limit 0 |
| tep_board_F11_r1 | 1 | one_code | 0 | 0 | 0 | 46 | 0 | – |
| tep_board_F12_r1 | 1 | clear_skip | 0 | 0 | 0 | 2 | 0 | – |
| tep_board_F12_r1 | 1 | empty_skip | 0 | 0 | 0 | 16 | 0 | – |
| tep_board_F12_r1 | 1 | explain | 322 | 0 | 0 | 322 | 0 | over_limit 0 |
| tep_board_F12_r1 | 1 | one_code | 0 | 0 | 0 | 9 | 0 | – |
| tep_board_F13_r1 | 1 | clear_skip | 0 | 0 | 0 | 23 | 0 | – |
| tep_board_F13_r1 | 1 | empty_skip | 0 | 0 | 0 | 18 | 0 | – |
| tep_board_F13_r1 | 1 | explain | 186 | 0 | 0 | 186 | 0 | over_limit 0 |
| tep_board_F13_r1 | 1 | one_code | 0 | 0 | 0 | 28 | 0 | – |
| tep_board_F14_r1 | 1 | clear_skip | 0 | 0 | 0 | 2 | 0 | – |
| tep_board_F14_r1 | 1 | empty_skip | 0 | 0 | 0 | 16 | 0 | – |
| tep_board_F14_r1 | 1 | explain | 199 | 0 | 0 | 199 | 0 | over_limit 0 |
| tep_board_F14_r1 | 1 | one_code | 0 | 0 | 0 | 55 | 0 | – |
| tep_board_F15_r1 | 1 | clear_skip | 0 | 0 | 0 | 3 | 0 | – |
| tep_board_F15_r1 | 1 | empty_skip | 0 | 0 | 0 | 42 | 0 | – |
| tep_board_F15_r1 | 1 | explain | 57 | 0 | 0 | 57 | 0 | over_limit 0 |
| tep_board_F15_r1 | 1 | one_code | 0 | 0 | 0 | 28 | 0 | – |
| tep_board_F16_r1 | 1 | clear_skip | 0 | 0 | 0 | 48 | 0 | – |
| tep_board_F16_r1 | 1 | empty_skip | 0 | 0 | 0 | 16 | 0 | – |
| tep_board_F16_r1 | 1 | explain | 154 | 0 | 0 | 154 | 0 | over_limit 0 |
| tep_board_F16_r1 | 1 | one_code | 0 | 0 | 0 | 10 | 0 | – |
| tep_board_F17_r1 | 1 | clear_skip | 0 | 0 | 0 | 8 | 0 | – |
| tep_board_F17_r1 | 1 | empty_skip | 0 | 0 | 0 | 17 | 0 | – |
| tep_board_F17_r1 | 1 | explain | 127 | 0 | 0 | 127 | 0 | over_limit 0 |
| tep_board_F17_r1 | 1 | one_code | 0 | 0 | 0 | 46 | 0 | – |
| tep_board_F18_r1 | 1 | clear_skip | 0 | 0 | 0 | 18 | 0 | – |
| tep_board_F18_r1 | 1 | empty_skip | 0 | 0 | 0 | 16 | 0 | – |
| tep_board_F18_r1 | 1 | explain | 193 | 0 | 0 | 193 | 0 | over_limit 0 |
| tep_board_F18_r1 | 1 | one_code | 0 | 0 | 0 | 10 | 0 | – |
| tep_board_F19_r1 | 1 | clear_skip | 0 | 0 | 0 | 20 | 0 | – |
| tep_board_F19_r1 | 1 | empty_skip | 0 | 0 | 0 | 18 | 0 | – |
| tep_board_F19_r1 | 1 | explain | 240 | 0 | 0 | 240 | 0 | over_limit 0 |
| tep_board_F19_r1 | 1 | one_code | 0 | 0 | 0 | 12 | 0 | – |
| tep_board_F20_r1 | 1 | clear_skip | 0 | 0 | 0 | 20 | 0 | – |
| tep_board_F20_r1 | 1 | empty_skip | 0 | 0 | 0 | 35 | 0 | – |
| tep_board_F20_r1 | 1 | explain | 156 | 0 | 0 | 156 | 0 | over_limit 0 |
| tep_board_F20_r1 | 1 | one_code | 0 | 0 | 0 | 14 | 0 | – |
| tep_board_N_r1 | 1 | clear_skip | 0 | 0 | 0 | 3 | 0 | – |
| tep_board_N_r1 | 1 | empty_skip | 0 | 0 | 0 | 39 | 0 | – |
| tep_board_N_r1 | 1 | explain | 54 | 0 | 0 | 54 | 0 | over_limit 0 |
| tep_board_N_r1 | 1 | one_code | 0 | 0 | 0 | 31 | 0 | – |
| tep_board_N_r2 | 1 | empty_skip | 0 | 0 | 0 | 42 | 0 | – |
| tep_board_N_r2 | 1 | explain | 21 | 0 | 0 | 21 | 0 | over_limit 0 |
| tep_board_N_r2 | 1 | one_code | 0 | 0 | 0 | 32 | 0 | – |
