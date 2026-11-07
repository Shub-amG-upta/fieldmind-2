# Benchmark `tep_bev_explain_skip_board`

Architecture **multi**, mode **lockstep**, overlay `configs/bev_ideas.yaml,configs/tep.yaml`, merge rule `hybrid`, models npu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, cpu: `gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf`, bev: `bev-decider-0.4B-backbone-Q8_0.gguf`. Agent code ran on the laptop and only model calls on the board, so tick times are laptop times. Energy not measured. Plant data: simulated (Tennessee Eastman Process, Rieth et al. 2017).

bev ideas switches: `explain=on,clear_skip=on`. bev-decide on npu. bev idea calls: answered by bev-decide (failed = no answer, which makes the run invalid and is not kept; rejected = refused by the gate's check). used = an answer that changed what the agent did; shadow = asked and only logged. Decode tokens per tick: answer tokens written by every model per tick (bev writes none).

Group top-1 is the share of scored ticks (fault onset onward) whose published rank-1 cause is in the true case's look-alike group; belief group top-1 is the same for the code-only ranking. A held-out true case has no exact top-1. Unusable = a model answer that was not used (wrong format, failed call, rejected note reading). Settings and every run, stopped ones included: `test.json`.

| episode | run | finished | ticks | model calls | bev idea calls / failed / rejected | bev used / shadow | decode tokens per tick | unusable | tokens in | group top-1 | belief group top-1 | exact top-1 | faithfulness | actions P / R | lead time min | false alarms /h | tick p95 ms | wall s | chip C | server CPU s npu / cpu / bev | peak RSS MB npu / cpu / bev |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tep_board_F01_r1 | 1 | 2026-11-06 14:46 | 319 | 677 | 319 / 0 / 0 | 323 / 0 | 9.70 | 3 | 710,349 | 0.22 | 0.00 | 0.22 | 0.98 | – | – | – | 4722 | 128 | 39.0 → 55.6 | 44.9 / 135.7 / 16.6 | 525 / 1568 / 586 |
| tep_board_F02_r1 | 1 | 2026-11-06 15:01 | 319 | 630 | 296 / 0 / 0 | 300 / 0 | 8.57 | 0 | 533,720 | 0.16 | 0.59 | 0.16 | 0.98 | – | – | – | 5263 | 746 | 39.0 → 62.5 | 361.7 / 82.5 / 112.5 | 582 / 1568 / 714 |
| tep_board_F03_r1 | 1 | 2026-11-06 15:08 | 319 | 145 | 38 / 0 / 0 | 48 / 0 | 2.43 | 0 | 47,847 | 0.00 | 0.00 | 0.00 | 1.00 | – | – | – | 1636 | 116 | 39.0 → 56.0 | 97.2 / 25.0 / 6.4 | 538 / 1549 / 723 |
| tep_board_F04_r1 | 1 | 2026-11-06 15:16 | 319 | 297 | 110 / 0 / 0 | 149 / 0 | 4.36 | 0 | 111,058 | 0.79 | 0.67 | 0.79 | 0.95 | – | – | – | 2432 | 234 | 39.0 → 58.3 | 171.9 / 24.9 / 23.9 | 551 / 1535 / 760 |
| tep_board_F05_r1 | 1 | 2026-11-06 18:59 | 319 | 683 | 321 / 0 / 0 | 330 / 0 | 10.05 | 1 | 662,710 | 0.00 | 0.00 | 0.00 | 0.96 | – | – | – | 4945 | 258 | 35.9 → 57.9 | 111.7 / 89.8 / 41.0 | 536 / 1586 / 952 |
| tep_board_F06_r1 | 1 | 2026-11-06 19:32 | 319 | 668 | 316 / 0 / 0 | 320 / 0 | 9.42 | 2 | 704,756 | 0.42 | 0.82 | 0.42 | 1.00 | – | – | – | 6266 | 800 | 38.6 → 64.7 | 328.7 / 181.3 / 129.2 | 571 / 1572 / 1150 |
| tep_board_F07_r1 | 1 | 2026-11-06 19:56 | 319 | 696 | 326 / 0 / 0 | 331 / 0 | 10.58 | 0 | 770,216 | 0.09 | 0.00 | 0.09 | 0.94 | – | – | – | 6887 | 1074 | 39.3 → 64.5 | 438.4 / 561.1 / 150.8 | 587 / 1581 / 1388 |
| tep_board_F08_r1 | 1 | 2026-11-06 20:19 | 319 | 634 | 295 / 0 / 0 | 299 / 0 | 9.53 | 0 | 634,777 | 0.01 | 0.38 | 0.01 | 0.97 | – | – | – | 6915 | 910 | 39.3 → 65.2 | 378.5 / 504.1 / 126.2 | 584 / 1585 / 1619 |
| tep_board_F09_r1 | 1 | 2026-11-06 20:27 | 319 | 149 | 39 / 0 / 0 | 48 / 0 | 2.50 | 0 | 50,919 | 0.00 | 0.00 | 0.00 | 1.00 | – | – | – | 1828 | 126 | 39.1 → 56.7 | 95.7 / 25.1 / 7.4 | 541 / 1540 / 1638 |
| tep_board_F10_r1 | 1 | 2026-11-06 20:38 | 319 | 405 | 176 / 0 / 0 | 181 / 0 | 6.01 | 0 | 200,370 | 0.00 | 0.00 | 0.00 | 0.82 | – | – | – | 4559 | 380 | 39.3 → 62.1 | 231.6 / 86.7 / 49.0 | 556 / 1561 / 1768 |
| tep_board_F11_r1 | 1 | 2026-11-06 20:58 | 319 | 389 | 154 / 0 / 0 | 163 / 0 | 6.34 | 1 | 217,170 | 0.00 | 0.00 | 0.00 | 0.91 | – | – | – | 3175 | 227 | 39.3 → 60.2 | 117.1 / 90.1 / 33.5 | 544 / 1559 / 1909 |
| tep_board_F12_r1 | 1 | 2026-11-06 21:27 | 319 | 653 | 309 / 0 / 0 | 319 / 0 | 9.04 | 1 | 653,872 | 0.59 | 0.15 | 0.59 | 1.00 | – | – | – | 5814 | 628 | 39.5 → 63.3 | 270.8 / 73.1 / 101.0 | 562 / 1580 / 2287 |
| tep_board_F13_r1 | 1 | 2026-11-06 21:53 | 319 | 417 | 175 / 0 / 0 | 185 / 0 | 6.50 | 1 | 338,285 | 0.00 | 0.00 | 0.00 | 0.98 | – | – | – | 32 | 66 | 39.1 → 50.2 | 26.0 / 0.1 / 10.0 | 513 / 1469 / 2512 |
| tep_board_F14_r1 | 1 | 2026-11-06 22:03 | 319 | 464 | 209 / 0 / 0 | 213 / 0 | 6.39 | 0 | 372,175 | 0.55 | 0.08 | 0.55 | 0.98 | – | – | – | 4279 | 526 | 39.3 → 61.7 | 273.4 / 53.2 / 79.0 | 560 / 1560 / 2820 |
| tep_board_F15_r1 | 1 | 2026-11-06 22:11 | 319 | 152 | 40 / 0 / 0 | 47 / 0 | 2.55 | 0 | 51,580 | 0.00 | 0.00 | 0.00 | 1.00 | – | – | – | 1671 | 121 | 39.3 → 57.0 | 98.8 / 28.6 / 7.5 | 534 / 1537 / 2859 |
| tep_board_F16_r1 | 1 | 2026-11-06 22:22 | 319 | 391 | 176 / 0 / 0 | 190 / 0 | 5.50 | 0 | 241,213 | 0.69 | 0.38 | 0.69 | 0.96 | – | – | – | 3838 | 381 | 39.0 → 62.1 | 229.4 / 25.7 / 58.0 | 553 / 1531 / 3182 |
| tep_board_F17_r1 | 1 | 2026-11-06 22:32 | 319 | 281 | 114 / 0 / 0 | 124 / 0 | 4.43 | 0 | 155,301 | 0.58 | 0.89 | 0.58 | 0.97 | – | – | – | 3492 | 266 | 39.0 → 59.4 | 162.5 / 79.4 / 38.6 | 541 / 1549 / 1439 |
| tep_board_F18_r1 | 1 | 2026-11-06 22:47 | 319 | 437 | 198 / 0 / 0 | 206 / 0 | 6.65 | 0 | 401,042 | 0.17 | 0.33 | 0.17 | 1.00 | – | – | – | 5838 | 574 | 39.3 → 62.9 | 260.4 / 287.4 / 83.2 | 557 / 1566 / 2867 |
| tep_board_F19_r1 | 1 | 2026-11-07 03:52 | 319 | 487 | 215 / 0 / 0 | 230 / 0 | 7.00 | 0 | 363,635 | 0.56 | 0.17 | 0.56 | 0.97 | – | – | – | 4298 | 334 | 36.4 → 59.8 | 182.1 / 0.3 / 59.0 | 552 / 1471 / 523 |
| tep_board_F20_r1 | 1 | 2026-11-07 04:02 | 319 | 357 | 140 / 0 / 0 | 151 / 0 | 5.44 | 0 | 245,852 | 0.38 | 0.44 | 0.38 | 0.95 | – | – | – | 4231 | 362 | 39.0 → 62.1 | 210.0 / 76.5 / 48.4 | 565 / 1567 / 583 |
| tep_board_N_r1 | 1 | 2026-11-07 04:09 | 319 | 141 | 36 / 0 / 0 | 46 / 0 | 2.39 | 0 | 47,283 | – | – | – | 1.00 | – | – | 6.27 | 1544 | 107 | 39.0 → 56.0 | 86.1 / 24.7 / 6.0 | 536 / 1537 / 591 |
| tep_board_N_r2 | 1 | 2026-11-07 04:13 | 319 | 98 | 11 / 0 / 0 | 11 / 0 | 2.30 | 0 | 30,257 | – | – | – | 0.79 | – | – | 5.33 | 1398 | 83 | 39.3 → 55.2 | 67.8 / 74.1 / 1.8 | 526 / 1546 / 593 |

## bev ideas per episode

| episode | run | idea | calls | failed | rejected | used | shadow | other counters |
|---|---|---|---|---|---|---|---|---|
| tep_board_F01_r1 | 1 | clear_skip | 0 | 0 | 0 | 4 | 0 | – |
| tep_board_F01_r1 | 1 | explain | 319 | 0 | 0 | 319 | 0 | over_limit 0 |
| tep_board_F02_r1 | 1 | clear_skip | 0 | 0 | 0 | 4 | 0 | – |
| tep_board_F02_r1 | 1 | explain | 296 | 0 | 0 | 296 | 0 | over_limit 0 |
| tep_board_F03_r1 | 1 | clear_skip | 0 | 0 | 0 | 10 | 0 | – |
| tep_board_F03_r1 | 1 | explain | 38 | 0 | 0 | 38 | 0 | over_limit 0 |
| tep_board_F04_r1 | 1 | clear_skip | 0 | 0 | 0 | 39 | 0 | – |
| tep_board_F04_r1 | 1 | explain | 110 | 0 | 0 | 110 | 0 | over_limit 0 |
| tep_board_F05_r1 | 1 | clear_skip | 0 | 0 | 0 | 9 | 0 | – |
| tep_board_F05_r1 | 1 | explain | 321 | 0 | 0 | 321 | 0 | over_limit 0 |
| tep_board_F06_r1 | 1 | clear_skip | 0 | 0 | 0 | 4 | 0 | – |
| tep_board_F06_r1 | 1 | explain | 316 | 0 | 0 | 316 | 0 | over_limit 0 |
| tep_board_F07_r1 | 1 | clear_skip | 0 | 0 | 0 | 5 | 0 | – |
| tep_board_F07_r1 | 1 | explain | 326 | 0 | 0 | 326 | 0 | over_limit 0 |
| tep_board_F08_r1 | 1 | clear_skip | 0 | 0 | 0 | 4 | 0 | – |
| tep_board_F08_r1 | 1 | explain | 295 | 0 | 0 | 295 | 0 | over_limit 0 |
| tep_board_F09_r1 | 1 | clear_skip | 0 | 0 | 0 | 9 | 0 | – |
| tep_board_F09_r1 | 1 | explain | 39 | 0 | 0 | 39 | 0 | over_limit 0 |
| tep_board_F10_r1 | 1 | clear_skip | 0 | 0 | 0 | 5 | 0 | – |
| tep_board_F10_r1 | 1 | explain | 176 | 0 | 0 | 176 | 0 | over_limit 0 |
| tep_board_F11_r1 | 1 | clear_skip | 0 | 0 | 0 | 9 | 0 | – |
| tep_board_F11_r1 | 1 | explain | 154 | 0 | 0 | 154 | 0 | over_limit 0 |
| tep_board_F12_r1 | 1 | clear_skip | 0 | 0 | 0 | 10 | 0 | – |
| tep_board_F12_r1 | 1 | explain | 309 | 0 | 0 | 309 | 0 | over_limit 0 |
| tep_board_F13_r1 | 1 | clear_skip | 0 | 0 | 0 | 10 | 0 | – |
| tep_board_F13_r1 | 1 | explain | 175 | 0 | 0 | 175 | 0 | over_limit 0 |
| tep_board_F14_r1 | 1 | clear_skip | 0 | 0 | 0 | 4 | 0 | – |
| tep_board_F14_r1 | 1 | explain | 209 | 0 | 0 | 209 | 0 | over_limit 0 |
| tep_board_F15_r1 | 1 | clear_skip | 0 | 0 | 0 | 7 | 0 | – |
| tep_board_F15_r1 | 1 | explain | 40 | 0 | 0 | 40 | 0 | over_limit 0 |
| tep_board_F16_r1 | 1 | clear_skip | 0 | 0 | 0 | 14 | 0 | – |
| tep_board_F16_r1 | 1 | explain | 176 | 0 | 0 | 176 | 0 | over_limit 0 |
| tep_board_F17_r1 | 1 | clear_skip | 0 | 0 | 0 | 10 | 0 | – |
| tep_board_F17_r1 | 1 | explain | 114 | 0 | 0 | 114 | 0 | over_limit 0 |
| tep_board_F18_r1 | 1 | clear_skip | 0 | 0 | 0 | 8 | 0 | – |
| tep_board_F18_r1 | 1 | explain | 198 | 0 | 0 | 198 | 0 | over_limit 0 |
| tep_board_F19_r1 | 1 | clear_skip | 0 | 0 | 0 | 15 | 0 | – |
| tep_board_F19_r1 | 1 | explain | 215 | 0 | 0 | 215 | 0 | over_limit 0 |
| tep_board_F20_r1 | 1 | clear_skip | 0 | 0 | 0 | 11 | 0 | – |
| tep_board_F20_r1 | 1 | explain | 140 | 0 | 0 | 140 | 0 | over_limit 0 |
| tep_board_N_r1 | 1 | clear_skip | 0 | 0 | 0 | 10 | 0 | – |
| tep_board_N_r1 | 1 | explain | 36 | 0 | 0 | 36 | 0 | over_limit 0 |
| tep_board_N_r2 | 1 | explain | 11 | 0 | 0 | 11 | 0 | over_limit 0 |

Board resources (on-board sampler, once a second, per episode): CPU seconds and peak memory of each model server. The NPU has no readable usage counter; its work shows as the NPU lane's call time. Supply power, if the board exposes it, is in each summary's `meta.resources`; energy is never estimated.
