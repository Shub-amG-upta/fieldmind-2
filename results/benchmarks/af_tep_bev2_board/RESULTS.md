# Benchmark `af_tep_bev2_board`

Architecture **multi**, mode **lockstep**, overlay `configs/bev_ideas.yaml,configs/tep.yaml`, merge rule `hybrid`, models npu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, cpu: `gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf`, bev: `bev-decider-0.4B-backbone-Q8_0.gguf`. Agent code ran on the laptop and only model calls on the board, so tick times are laptop times. Energy not measured. Plant data: simulated (Tennessee Eastman Process, Rieth et al. 2017).

bev ideas switches: `explain=on,clear_skip=on,explain_prompt=v2,empty_skip=on,one_code=on`. bev-decide on npu. bev idea calls: answered by bev-decide (failed = no answer, which makes the run invalid and is not kept; rejected = refused by the gate's check). used = an answer that changed what the agent did; shadow = asked and only logged. Decode tokens per tick: answer tokens written by every model per tick (bev writes none).

Group top-1 is the share of scored ticks (fault onset onward) whose published rank-1 cause is in the true case's look-alike group; belief group top-1 is the same for the code-only ranking. A held-out true case has no exact top-1. Unusable = a model answer that was not used (wrong format, failed call, rejected note reading). Settings and every run, stopped ones included: `test.json`.

| episode | run | finished | ticks | model calls | bev idea calls / failed / rejected | bev used / shadow | decode tokens per tick | unusable | tokens in | group top-1 | belief group top-1 | exact top-1 | faithfulness | actions P / R | lead time min | false alarms /h | tick p95 ms | wall s | chip C | server CPU s npu / cpu / bev | peak RSS MB npu / cpu / bev |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tep_board_F01_r1 | 1 | 2026-11-08 16:50 | 319 | 671 | 330 / 0 / 0 | 355 / 0 | 9.53 | 0 | 747,841 | 0.26 | 0.00 | 0.26 | 1.00 | – | – | – | 6020 | 928 | 49.4 → 62.8 | 444.6 / 207.3 / 146.8 | 584 / 1572 / 603 |
| tep_board_F02_r1 | 1 | 2026-11-08 17:03 | 319 | 620 | 304 / 0 / 0 | 342 / 0 | 7.92 | 0 | 598,839 | 0.36 | 0.66 | 0.36 | 1.00 | – | – | – | 5645 | 754 | 53.6 → 62.9 | 363.9 / 71.2 / 120.8 | 572 / 1567 / 738 |
| tep_board_F03_r1 | 1 | 2026-11-08 17:06 | 319 | 150 | 58 / 0 / 0 | 130 / 0 | 2.45 | 0 | 47,078 | 0.00 | 0.00 | 0.00 | 1.00 | – | – | – | 2235 | 106 | 52.1 → 60.5 | 48.1 / 135.9 / 12.6 | 525 / 1555 / 758 |
| tep_board_F04_r1 | 1 | 2026-11-08 17:12 | 319 | 373 | 179 / 0 / 0 | 226 / 0 | 4.62 | 0 | 207,303 | 0.94 | 0.00 | 0.94 | 1.00 | – | – | – | 2971 | 330 | 52.1 → 61.7 | 196.4 / 7.5 / 56.6 | 547 / 1532 / 868 |
| tep_board_F05_r1 | 1 | 2026-11-08 17:28 | 319 | 672 | 330 / 0 / 0 | 359 / 0 | 9.33 | 0 | 746,197 | 0.35 | 0.32 | 0.00 | 1.00 | – | – | – | 6333 | 950 | 53.2 → 63.7 | 433.4 / 280.4 / 140.5 | 577 / 1566 / 1071 |
| tep_board_F06_r1 | 1 | 2026-11-08 17:44 | 319 | 660 | 326 / 0 / 0 | 351 / 0 | 8.73 | 0 | 705,856 | 0.27 | 0.82 | 0.27 | 1.00 | – | – | – | 5933 | 886 | 52.1 → 64.8 | 406.5 / 81.2 / 136.2 | 578 / 1562 / 1294 |
| tep_board_F07_r1 | 1 | 2026-11-08 18:01 | 319 | 682 | 334 / 0 / 0 | 359 / 0 | 9.20 | 0 | 726,788 | 0.00 | 0.00 | 0.00 | 1.00 | – | – | – | 5906 | 955 | 52.1 → 64.1 | 421.6 / 379.4 / 138.0 | 577 / 1567 / 1550 |
| tep_board_F08_r1 | 1 | 2026-11-08 18:16 | 319 | 615 | 302 / 0 / 0 | 329 / 0 | 8.26 | 0 | 649,135 | 0.59 | 0.27 | 0.59 | 1.00 | – | – | – | 6080 | 839 | 52.9 → 64.1 | 380.4 / 230.5 / 123.0 | 570 / 1577 / 1557 |
| tep_board_F09_r1 | 1 | 2026-11-08 18:19 | 319 | 147 | 58 / 0 / 0 | 132 / 0 | 2.25 | 0 | 53,376 | 0.03 | 0.00 | 0.00 | 1.00 | – | – | – | 2315 | 112 | 53.2 → 62.5 | 51.8 / 121.5 / 14.7 | 524 / 1548 / 1609 |
| tep_board_F10_r1 | 1 | 2026-11-08 18:30 | 319 | 465 | 194 / 0 / 0 | 229 / 0 | 10.61 | 0 | 337,777 | 0.10 | 0.07 | 0.00 | 0.99 | – | – | – | 8542 | 623 | 53.6 → 64.1 | 250.8 / 962.4 / 75.0 | 550 / 1571 / 1861 |
| tep_board_F11_r1 | 1 | 2026-11-08 18:37 | 319 | 351 | 163 / 0 / 0 | 250 / 0 | 3.87 | 0 | 303,514 | 0.72 | 0.57 | 0.72 | 0.99 | – | – | – | 3198 | 379 | 52.3 → 63.6 | 183.6 / 7.6 / 63.5 | 542 / 1529 / 1956 |
| tep_board_F12_r1 | 1 | 2026-11-08 18:53 | 319 | 656 | 323 / 0 / 0 | 348 / 0 | 8.96 | 0 | 729,293 | 0.21 | 0.12 | 0.21 | 1.00 | – | – | – | 6005 | 913 | 53.6 → 64.5 | 433.4 / 96.0 / 141.0 | 573 / 1562 / 2472 |
| tep_board_F13_r1 | 1 | 2026-11-08 19:03 | 319 | 415 | 194 / 0 / 0 | 254 / 0 | 5.80 | 0 | 390,740 | 0.55 | 0.46 | 0.55 | 1.00 | – | – | – | 6113 | 538 | 53.2 → 64.1 | 231.8 / 318.1 / 75.6 | 549 / 1571 / 3010 |
| tep_board_F14_r1 | 1 | 2026-11-08 19:13 | 319 | 434 | 199 / 0 / 0 | 272 / 0 | 4.87 | 0 | 420,268 | 0.53 | 0.33 | 0.53 | 1.00 | – | – | – | 3372 | 508 | 53.2 → 64.1 | 233.2 / 7.8 / 82.8 | 549 / 1531 / 3382 |
| tep_board_F15_r1 | 1 | 2026-11-08 19:16 | 319 | 149 | 59 / 0 / 0 | 130 / 0 | 2.39 | 0 | 51,363 | 0.00 | 0.00 | 0.00 | 0.88 | – | – | – | 2309 | 114 | 51.7 → 62.4 | 50.8 / 124.4 / 15.8 | 519 / 1553 / 3228 |
| tep_board_F16_r1 | 1 | 2026-11-09 00:32 | 319 | 376 | 184 / 0 / 0 | 228 / 0 | 5.27 | 0 | 325,649 | 0.97 | 0.96 | 0.97 | 1.00 | – | – | – | 4655 | 441 | 70.5 → 68.6 | 148.4 / 9.3 / 56.6 | 558 / 1543 / 561 |
| tep_board_F17_r1 | 1 | 2026-11-09 00:37 | 319 | 279 | 131 / 0 / 0 | 198 / 0 | 2.82 | 0 | 217,910 | 0.52 | 0.85 | 0.52 | 1.00 | – | – | – | 3242 | 275 | 69.5 → 72.6 | 82.3 / 8.6 / 35.8 | 544 / 1539 / 613 |
| tep_board_F18_r1 | 1 | 2026-11-09 00:47 | 319 | 405 | 197 / 0 / 0 | 235 / 0 | 5.41 | 1 | 413,307 | 0.43 | 0.46 | 0.43 | 1.00 | – | – | – | 5810 | 546 | 70.2 → 70.2 | 167.3 / 132.2 / 65.9 | 561 / 1570 / 706 |
| tep_board_F19_r1 | 1 | 2026-11-09 00:57 | 319 | 517 | 254 / 0 / 0 | 289 / 0 | 6.87 | 0 | 480,981 | 0.46 | 0.43 | 0.46 | 0.99 | – | – | – | 5594 | 628 | 68.7 → 74.9 | 199.1 / 27.9 / 78.3 | 570 / 1570 / 842 |
| tep_board_F20_r1 | 1 | 2026-11-09 01:05 | 319 | 357 | 172 / 0 / 0 | 224 / 0 | 4.68 | 0 | 306,012 | 0.76 | 0.96 | 0.76 | 0.97 | – | – | – | 5143 | 417 | 74.4 → 69.9 | 136.9 / 37.5 / 48.6 | 554 / 1564 / 932 |
| tep_board_N_r1 | 1 | 2026-11-09 01:07 | 319 | 145 | 56 / 0 / 0 | 127 / 0 | 2.28 | 0 | 46,396 | – | – | – | 1.00 | – | – | 2.82 | 2300 | 113 | 68.3 → 70.5 | 32.4 / 165.4 / 8.8 | 530 / 1551 / 953 |
| tep_board_N_r2 | 1 | 2026-11-09 01:08 | 319 | 71 | 21 / 0 / 0 | 95 / 0 | 0.81 | 0 | 10,817 | – | – | – | 1.00 | – | – | 2.45 | 1036 | 36 | 67.8 → 72.9 | 5.7 / 80.6 / 2.0 | 520 / 1551 / 958 |

## bev ideas per episode

| episode | run | idea | calls | failed | rejected | used | shadow | other counters |
|---|---|---|---|---|---|---|---|---|
| tep_board_F01_r1 | 1 | empty_skip | 0 | 0 | 0 | 16 | 0 | – |
| tep_board_F01_r1 | 1 | explain | 330 | 0 | 0 | 330 | 0 | over_limit 0 |
| tep_board_F01_r1 | 1 | one_code | 0 | 0 | 0 | 9 | 0 | – |
| tep_board_F02_r1 | 1 | clear_skip | 0 | 0 | 0 | 3 | 0 | – |
| tep_board_F02_r1 | 1 | empty_skip | 0 | 0 | 0 | 18 | 0 | – |
| tep_board_F02_r1 | 1 | explain | 304 | 0 | 0 | 304 | 0 | over_limit 0 |
| tep_board_F02_r1 | 1 | one_code | 0 | 0 | 0 | 17 | 0 | – |
| tep_board_F03_r1 | 1 | clear_skip | 0 | 0 | 0 | 1 | 0 | – |
| tep_board_F03_r1 | 1 | empty_skip | 0 | 0 | 0 | 40 | 0 | – |
| tep_board_F03_r1 | 1 | explain | 58 | 0 | 0 | 58 | 0 | over_limit 0 |
| tep_board_F03_r1 | 1 | one_code | 0 | 0 | 0 | 31 | 0 | – |
| tep_board_F04_r1 | 1 | clear_skip | 0 | 0 | 0 | 1 | 0 | – |
| tep_board_F04_r1 | 1 | empty_skip | 0 | 0 | 0 | 28 | 0 | – |
| tep_board_F04_r1 | 1 | explain | 179 | 0 | 0 | 179 | 0 | over_limit 0 |
| tep_board_F04_r1 | 1 | one_code | 0 | 0 | 0 | 18 | 0 | – |
| tep_board_F05_r1 | 1 | clear_skip | 0 | 0 | 0 | 4 | 0 | – |
| tep_board_F05_r1 | 1 | empty_skip | 0 | 0 | 0 | 16 | 0 | – |
| tep_board_F05_r1 | 1 | explain | 330 | 0 | 0 | 330 | 0 | over_limit 0 |
| tep_board_F05_r1 | 1 | one_code | 0 | 0 | 0 | 9 | 0 | – |
| tep_board_F06_r1 | 1 | empty_skip | 0 | 0 | 0 | 16 | 0 | – |
| tep_board_F06_r1 | 1 | explain | 326 | 0 | 0 | 326 | 0 | over_limit 0 |
| tep_board_F06_r1 | 1 | one_code | 0 | 0 | 0 | 9 | 0 | – |
| tep_board_F07_r1 | 1 | empty_skip | 0 | 0 | 0 | 16 | 0 | – |
| tep_board_F07_r1 | 1 | explain | 334 | 0 | 0 | 334 | 0 | over_limit 0 |
| tep_board_F07_r1 | 1 | one_code | 0 | 0 | 0 | 9 | 0 | – |
| tep_board_F08_r1 | 1 | empty_skip | 0 | 0 | 0 | 16 | 0 | – |
| tep_board_F08_r1 | 1 | explain | 302 | 0 | 0 | 302 | 0 | over_limit 0 |
| tep_board_F08_r1 | 1 | one_code | 0 | 0 | 0 | 11 | 0 | – |
| tep_board_F09_r1 | 1 | clear_skip | 0 | 0 | 0 | 1 | 0 | – |
| tep_board_F09_r1 | 1 | empty_skip | 0 | 0 | 0 | 42 | 0 | – |
| tep_board_F09_r1 | 1 | explain | 58 | 0 | 0 | 58 | 0 | over_limit 0 |
| tep_board_F09_r1 | 1 | one_code | 0 | 0 | 0 | 31 | 0 | – |
| tep_board_F10_r1 | 1 | clear_skip | 0 | 0 | 0 | 5 | 0 | – |
| tep_board_F10_r1 | 1 | empty_skip | 0 | 0 | 0 | 16 | 0 | – |
| tep_board_F10_r1 | 1 | explain | 194 | 0 | 0 | 194 | 0 | over_limit 0 |
| tep_board_F10_r1 | 1 | one_code | 0 | 0 | 0 | 14 | 0 | – |
| tep_board_F11_r1 | 1 | clear_skip | 0 | 0 | 0 | 17 | 0 | – |
| tep_board_F11_r1 | 1 | empty_skip | 0 | 0 | 0 | 24 | 0 | – |
| tep_board_F11_r1 | 1 | explain | 163 | 0 | 0 | 163 | 0 | over_limit 0 |
| tep_board_F11_r1 | 1 | one_code | 0 | 0 | 0 | 46 | 0 | – |
| tep_board_F12_r1 | 1 | empty_skip | 0 | 0 | 0 | 16 | 0 | – |
| tep_board_F12_r1 | 1 | explain | 323 | 0 | 0 | 323 | 0 | over_limit 0 |
| tep_board_F12_r1 | 1 | one_code | 0 | 0 | 0 | 9 | 0 | – |
| tep_board_F13_r1 | 1 | clear_skip | 0 | 0 | 0 | 14 | 0 | – |
| tep_board_F13_r1 | 1 | empty_skip | 0 | 0 | 0 | 18 | 0 | – |
| tep_board_F13_r1 | 1 | explain | 194 | 0 | 0 | 194 | 0 | over_limit 0 |
| tep_board_F13_r1 | 1 | one_code | 0 | 0 | 0 | 28 | 0 | – |
| tep_board_F14_r1 | 1 | clear_skip | 0 | 0 | 0 | 2 | 0 | – |
| tep_board_F14_r1 | 1 | empty_skip | 0 | 0 | 0 | 16 | 0 | – |
| tep_board_F14_r1 | 1 | explain | 199 | 0 | 0 | 199 | 0 | over_limit 0 |
| tep_board_F14_r1 | 1 | one_code | 0 | 0 | 0 | 55 | 0 | – |
| tep_board_F15_r1 | 1 | clear_skip | 0 | 0 | 0 | 1 | 0 | – |
| tep_board_F15_r1 | 1 | empty_skip | 0 | 0 | 0 | 42 | 0 | – |
| tep_board_F15_r1 | 1 | explain | 59 | 0 | 0 | 59 | 0 | over_limit 0 |
| tep_board_F15_r1 | 1 | one_code | 0 | 0 | 0 | 28 | 0 | – |
| tep_board_F16_r1 | 1 | clear_skip | 0 | 0 | 0 | 18 | 0 | – |
| tep_board_F16_r1 | 1 | empty_skip | 0 | 0 | 0 | 16 | 0 | – |
| tep_board_F16_r1 | 1 | explain | 184 | 0 | 0 | 184 | 0 | over_limit 0 |
| tep_board_F16_r1 | 1 | one_code | 0 | 0 | 0 | 10 | 0 | – |
| tep_board_F17_r1 | 1 | clear_skip | 0 | 0 | 0 | 4 | 0 | – |
| tep_board_F17_r1 | 1 | empty_skip | 0 | 0 | 0 | 17 | 0 | – |
| tep_board_F17_r1 | 1 | explain | 131 | 0 | 0 | 131 | 0 | over_limit 0 |
| tep_board_F17_r1 | 1 | one_code | 0 | 0 | 0 | 46 | 0 | – |
| tep_board_F18_r1 | 1 | clear_skip | 0 | 0 | 0 | 12 | 0 | – |
| tep_board_F18_r1 | 1 | empty_skip | 0 | 0 | 0 | 16 | 0 | – |
| tep_board_F18_r1 | 1 | explain | 197 | 0 | 0 | 197 | 0 | over_limit 0 |
| tep_board_F18_r1 | 1 | one_code | 0 | 0 | 0 | 10 | 0 | – |
| tep_board_F19_r1 | 1 | clear_skip | 0 | 0 | 0 | 5 | 0 | – |
| tep_board_F19_r1 | 1 | empty_skip | 0 | 0 | 0 | 18 | 0 | – |
| tep_board_F19_r1 | 1 | explain | 254 | 0 | 0 | 254 | 0 | over_limit 0 |
| tep_board_F19_r1 | 1 | one_code | 0 | 0 | 0 | 12 | 0 | – |
| tep_board_F20_r1 | 1 | clear_skip | 0 | 0 | 0 | 3 | 0 | – |
| tep_board_F20_r1 | 1 | empty_skip | 0 | 0 | 0 | 35 | 0 | – |
| tep_board_F20_r1 | 1 | explain | 172 | 0 | 0 | 172 | 0 | over_limit 0 |
| tep_board_F20_r1 | 1 | one_code | 0 | 0 | 0 | 14 | 0 | – |
| tep_board_N_r1 | 1 | clear_skip | 0 | 0 | 0 | 1 | 0 | – |
| tep_board_N_r1 | 1 | empty_skip | 0 | 0 | 0 | 39 | 0 | – |
| tep_board_N_r1 | 1 | explain | 56 | 0 | 0 | 56 | 0 | over_limit 0 |
| tep_board_N_r1 | 1 | one_code | 0 | 0 | 0 | 31 | 0 | – |
| tep_board_N_r2 | 1 | empty_skip | 0 | 0 | 0 | 42 | 0 | – |
| tep_board_N_r2 | 1 | explain | 21 | 0 | 0 | 21 | 0 | over_limit 0 |
| tep_board_N_r2 | 1 | one_code | 0 | 0 | 0 | 32 | 0 | – |

Board resources (on-board sampler, once a second, per episode): CPU seconds and peak memory of each model server. The NPU has no readable usage counter; its work shows as the NPU lane's call time. Supply power, if the board exposes it, is in each summary's `meta.resources`; energy is never estimated.
