# Benchmark `af_tep_v3_board`

Architecture **multi**, mode **lockstep**, overlay `configs/v3.yaml,configs/tep.yaml`, merge rule `hybrid`, models npu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, cpu: `gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf`. Agent code ran on the laptop and only model calls on the board, so tick times are laptop times. Energy not measured. Plant data: simulated (Tennessee Eastman Process, Rieth et al. 2017).

Group top-1 is the share of scored ticks (fault onset onward) whose published rank-1 cause is in the true case's look-alike group; belief group top-1 is the same for the code-only ranking. A held-out true case has no exact top-1. Unusable = a model answer that was not used (wrong format, failed call, rejected note reading). Settings and every run, stopped ones included: `test.json`.

| episode | run | finished | ticks | model calls | unusable | tokens in | group top-1 | belief group top-1 | exact top-1 | faithfulness | actions P / R | lead time min | false alarms /h | tick p95 ms | wall s | chip C | server CPU s npu / cpu / bev | peak RSS MB npu / cpu / bev |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tep_board_F01_r1 | 1 | 2026-11-08 20:33 | 319 | 357 | 0 | 294,142 | 0.09 | 0.00 | 0.09 | 1.00 | – | – | – | 9277 | 1478 | 62.0 → 71.3 | 1598.4 / 212.4 / 0.0 | 598 / 1596 / 472 |
| tep_board_F02_r1 | 1 | 2026-11-08 20:55 | 319 | 335 | 0 | 245,911 | 0.66 | 0.66 | 0.66 | 1.00 | – | – | – | 9028 | 1304 | 69.9 → 66.0 | 1434.1 / 22.5 / 0.0 | 588 / 1558 / 472 |
| tep_board_F03_r1 | 1 | 2026-11-08 21:00 | 319 | 132 | 0 | 57,318 | 0.00 | 0.00 | 0.00 | 1.00 | – | – | – | 4101 | 288 | 65.1 → 68.2 | 300.1 / 159.7 / 0.0 | 544 / 1566 / 472 |
| tep_board_F04_r1 | 1 | 2026-11-08 21:11 | 319 | 224 | 0 | 124,464 | 0.88 | 0.00 | 0.88 | 1.00 | – | – | – | 5449 | 624 | 65.1 → 65.6 | 732.9 / 18.7 / 0.0 | 568 / 1550 / 472 |
| tep_board_F05_r1 | 1 | 2026-11-08 21:34 | 319 | 363 | 0 | 303,853 | 0.30 | 0.32 | 0.00 | 1.00 | – | – | – | 8256 | 1367 | 64.5 → 66.7 | 1553.0 / 279.5 / 0.0 | 596 / 1588 / 472 |
| tep_board_F06_r1 | 1 | 2026-11-08 21:56 | 319 | 352 | 0 | 290,150 | 0.85 | 0.82 | 0.85 | 1.00 | – | – | – | 8174 | 1309 | 63.7 → 64.8 | 1552.4 / 112.0 / 0.0 | 591 / 1567 / 472 |
| tep_board_F07_r1 | 1 | 2026-11-08 22:20 | 319 | 367 | 0 | 317,189 | 0.00 | 0.00 | 0.00 | 0.99 | – | – | – | 8277 | 1432 | 63.3 → 65.2 | 1592.3 / 610.1 / 0.0 | 602 / 1579 / 472 |
| tep_board_F08_r1 | 1 | 2026-11-08 22:42 | 319 | 332 | 0 | 275,186 | 0.18 | 0.27 | 0.18 | 1.00 | – | – | – | 8189 | 1256 | 63.7 → 65.2 | 1421.7 / 337.3 / 0.0 | 584 / 1576 / 472 |
| tep_board_F09_r1 | 1 | 2026-11-08 22:47 | 319 | 130 | 0 | 58,631 | 0.03 | 0.00 | 0.00 | 1.00 | – | – | – | 4416 | 285 | 62.8 → 67.2 | 305.7 / 140.6 / 0.0 | 549 / 1553 / 472 |
| tep_board_F10_r1 | 1 | 2026-11-08 23:02 | 319 | 293 | 0 | 184,706 | 0.10 | 0.07 | 0.00 | 0.99 | – | – | – | 9953 | 876 | 64.8 → 65.1 | 792.0 / 1039.2 / 0.0 | 572 / 1579 / 472 |
| tep_board_F11_r1 | 1 | 2026-11-08 23:13 | 319 | 230 | 0 | 157,761 | 0.43 | 0.57 | 0.43 | 1.00 | – | – | – | 5778 | 671 | 62.8 → 62.1 | 821.4 / 18.5 / 0.0 | 572 / 1551 / 472 |
| tep_board_F12_r1 | 1 | 2026-11-08 23:33 | 319 | 349 | 0 | 278,928 | 0.90 | 0.12 | 0.90 | 1.00 | – | – | – | 7530 | 1175 | 59.3 → 62.0 | 1421.0 / 47.8 / 0.0 | 594 / 1567 / 472 |
| tep_board_F13_r1 | 1 | 2026-11-08 23:46 | 319 | 249 | 0 | 181,610 | 0.49 | 0.46 | 0.49 | 1.00 | – | – | – | 7594 | 777 | 59.7 → 64.0 | 911.7 / 104.8 / 0.0 | 575 / 1559 / 472 |
| tep_board_F14_r1 | 1 | 2026-11-09 00:00 | 319 | 254 | 0 | 184,789 | 0.93 | 0.33 | 0.93 | 1.00 | – | – | – | 6250 | 808 | 62.5 → 64.0 | 952.6 / 18.9 / 0.0 | 568 / 1546 / 472 |
| tep_board_F15_r1 | 1 | 2026-11-09 00:05 | 319 | 131 | 0 | 57,743 | 0.00 | 0.00 | 0.00 | 0.87 | – | – | – | 4067 | 286 | 61.6 → 66.7 | 315.9 / 141.3 / 0.0 | 551 / 1563 / 472 |
| tep_board_F16_r1 | 1 | 2026-11-09 00:17 | 319 | 227 | 0 | 150,062 | 0.97 | 0.96 | 0.97 | 1.00 | – | – | – | 6239 | 672 | 62.9 → 64.1 | 801.5 / 18.4 / 0.0 | 571 / 1563 / 472 |
| tep_board_F17_r1 | 1 | 2026-11-09 01:17 | 319 | 170 | 0 | 113,288 | 0.68 | 0.85 | 0.68 | 1.00 | – | – | – | 6903 | 543 | 64.1 → 71.4 | 460.5 / 20.6 / 0.0 | 559 / 1547 / 958 |
| tep_board_F18_r1 | 1 | 2026-11-09 01:32 | 319 | 239 | 2 | 184,924 | 0.45 | 0.46 | 0.45 | 1.00 | – | – | – | 8639 | 894 | 68.3 → 72.6 | 706.8 / 144.6 / 0.0 | 569 / 1574 / 958 |
| tep_board_F19_r1 | 1 | 2026-11-09 01:49 | 319 | 286 | 0 | 198,234 | 0.70 | 0.43 | 0.70 | 0.99 | – | – | – | 7620 | 969 | 63.6 → 74.5 | 774.9 / 22.0 / 0.0 | 585 / 1558 / 958 |
| tep_board_F20_r1 | 1 | 2026-11-09 02:02 | 319 | 224 | 0 | 146,682 | 0.85 | 0.96 | 0.85 | 0.97 | – | – | – | 7290 | 714 | 67.5 → 69.8 | 574.0 / 77.9 / 0.0 | 572 / 1592 / 958 |
| tep_board_N_r1 | 1 | 2026-11-09 02:07 | 319 | 128 | 0 | 55,853 | – | – | – | 1.00 | – | – | 2.82 | 4226 | 293 | 67.5 → 69.9 | 217.5 / 177.7 / 0.0 | 543 / 1568 / 958 |
| tep_board_N_r2 | 1 | 2026-11-09 02:10 | 319 | 86 | 0 | 32,986 | – | – | – | 1.00 | – | – | 2.45 | 2871 | 177 | 66.8 → 71.4 | 138.0 / 95.3 / 0.0 | 538 / 1545 / 958 |

Board resources (on-board sampler, once a second, per episode): CPU seconds and peak memory of each model server. The NPU has no readable usage counter; its work shows as the NPU lane's call time. Supply power, if the board exposes it, is in each summary's `meta.resources`; energy is never estimated.
