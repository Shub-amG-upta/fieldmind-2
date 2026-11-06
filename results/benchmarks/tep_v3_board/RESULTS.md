# Benchmark `tep_v3_board`

Architecture **multi**, mode **lockstep**, overlay `configs/v3.yaml,configs/tep.yaml`, merge rule `hybrid`, models npu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, cpu: `gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf`. Agent code ran on the laptop and only model calls on the board, so tick times are laptop times. Energy not measured. Plant data: simulated (Tennessee Eastman Process, Rieth et al. 2017).

Group top-1 is the share of scored ticks (fault onset onward) whose published rank-1 cause is in the true case's look-alike group; belief group top-1 is the same for the code-only ranking. A held-out true case has no exact top-1. Unusable = a model answer that was not used (wrong format, failed call, rejected note reading). Settings and every run, stopped ones included: `test.json`.

| episode | run | finished | ticks | model calls | unusable | tokens in | group top-1 | belief group top-1 | exact top-1 | faithfulness | actions P / R | lead time min | false alarms /h | tick p95 ms | wall s | chip C | server CPU s npu / cpu / bev | peak RSS MB npu / cpu / bev |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tep_board_F01_r1 | 1 | 2026-11-06 03:16 | 319 | 363 | 0 | 310,266 | 0.29 | 0.00 | 0.29 | 0.96 | – | – | – | 8750 | 1322 | 31.6 → 65.6 | 1679.7 / 300.5 / – | 590 / 1573 / – |
| tep_board_F02_r1 | 1 | 2026-11-06 03:40 | 319 | 335 | 0 | 251,740 | 0.62 | 0.59 | 0.62 | 0.98 | – | – | – | 8126 | 1093 | 37.2 → 65.9 | 1470.2 / 27.1 / – | 583 / 1540 / – |
| tep_board_F03_r1 | 1 | 2026-11-06 03:50 | 319 | 117 | 0 | 50,715 | 0.00 | 0.00 | 0.00 | 1.00 | – | – | – | 2841 | 229 | 37.2 → 61.0 | 330.9 / 26.3 / – | 540 / 1536 / – |
| tep_board_F04_r1 | 1 | 2026-11-06 04:52 | 319 | 221 | 2 | 100,148 | 0.81 | 0.67 | 0.81 | 0.95 | – | – | – | 35 | 14 | 41.8 → 41.3 | 0.0 / 0.0 / – | 490 / 1475 / – |
| tep_board_F05_r1 | 1 | 2026-11-06 05:14 | 319 | 368 | 0 | 293,610 | 0.00 | 0.00 | 0.00 | 0.94 | – | – | – | 8635 | 1310 | 40.1 → 64.8 | 1643.3 / 247.4 / – | 589 / 1577 / – |
| tep_board_F06_r1 | 1 | 2026-11-06 05:42 | 319 | 351 | 1 | 297,047 | 0.82 | 0.82 | 0.82 | 1.00 | – | – | – | 8460 | 544 | 51.9 → 64.5 | 674.0 / 0.6 / – | 555 / 1475 / – |
| tep_board_F07_r1 | 1 | 2026-11-06 06:08 | 319 | 379 | 0 | 346,860 | 0.01 | 0.00 | 0.01 | 0.94 | – | – | – | 14120 | 1547 | 54.4 → 64.7 | 1778.5 / 755.6 / – | 593 / 1578 / – |
| tep_board_F08_r1 | 1 | 2026-11-06 06:38 | 319 | 341 | 3 | 281,774 | 0.17 | 0.38 | 0.17 | 0.97 | – | – | – | 8301 | 294 | 50.5 → 71.4 | 204.7 / 161.5 / – | 538 / 1582 / – |
| tep_board_F09_r1 | 1 | 2026-11-06 06:44 | 319 | 119 | 0 | 52,225 | 0.00 | 0.00 | 0.00 | 1.00 | – | – | – | 3597 | 264 | 51.3 → 74.5 | 215.0 / 34.0 / – | 550 / 1535 / – |
| tep_board_F10_r1 | 1 | 2026-11-06 06:58 | 319 | 235 | 0 | 132,064 | 0.00 | 0.00 | 0.00 | 0.83 | – | – | – | 7383 | 682 | 50.0 → 74.1 | 522.6 / 138.4 / – | 562 / 1559 / – |
| tep_board_F11_r1 | 1 | 2026-11-06 07:12 | 319 | 242 | 0 | 127,328 | 0.00 | 0.00 | 0.00 | 0.91 | – | – | – | 6358 | 682 | 50.9 → 72.5 | 528.0 / 193.7 / – | 562 / 1559 / – |
| tep_board_F12_r1 | 1 | 2026-11-06 07:40 | 319 | 352 | 0 | 282,891 | 0.95 | 0.15 | 0.95 | 1.00 | – | – | – | 9667 | 1401 | 48.4 → 76.8 | 1044.7 / 77.9 / – | 589 / 1565 / – |
| tep_board_F13_r1 | 1 | 2026-11-06 07:57 | 319 | 252 | 0 | 175,599 | 0.00 | 0.00 | 0.00 | 0.98 | – | – | – | 9049 | 850 | 50.2 → 75.3 | 617.8 / 256.4 / – | 570 / 1569 / – |
| tep_board_F14_r1 | 1 | 2026-11-06 08:14 | 319 | 257 | 0 | 173,088 | 0.96 | 0.08 | 0.96 | 0.98 | – | – | – | 7194 | 842 | 47.7 → 77.2 | 672.8 / 37.2 / – | 568 / 1545 / – |
| tep_board_F15_r1 | 1 | 2026-11-06 08:22 | 319 | 119 | 0 | 51,949 | 0.00 | 0.00 | 0.00 | 1.00 | – | – | – | 3542 | 264 | 50.9 → 75.3 | 222.3 / 31.3 / – | 541 / 1557 / – |
| tep_board_F16_r1 | 1 | 2026-11-06 08:36 | 319 | 229 | 0 | 134,015 | 0.79 | 0.38 | 0.79 | 0.96 | – | – | – | 6610 | 689 | 49.6 → 74.4 | 558.4 / 31.6 / – | 567 / 1537 / – |
| tep_board_F17_r1 | 1 | 2026-11-06 08:47 | 319 | 172 | 0 | 92,763 | 0.69 | 0.89 | 0.69 | 0.99 | – | – | – | 6343 | 492 | 50.0 → 76.0 | 392.3 / 49.5 / – | 555 / 1557 / – |
| tep_board_F18_r1 | 1 | 2026-11-06 09:06 | 319 | 248 | 0 | 199,109 | 0.17 | 0.33 | 0.17 | 1.00 | – | – | – | 9920 | 977 | 50.9 → 73.7 | 686.7 / 427.4 / – | 567 / 1578 / – |
| tep_board_F19_r1 | 1 | 2026-11-06 09:24 | 319 | 287 | 0 | 174,314 | 0.79 | 0.17 | 0.79 | 0.97 | – | – | – | 7628 | 920 | 50.9 → 73.6 | 708.7 / 38.7 / – | 574 / 1542 / – |
| tep_board_F20_r1 | 1 | 2026-11-06 09:39 | 319 | 226 | 0 | 134,569 | 0.53 | 0.44 | 0.53 | 0.95 | – | – | – | 7190 | 673 | 47.7 → 74.5 | 525.8 / 72.0 / – | 565 / 1562 / – |
| tep_board_N_r1 | 1 | 2026-11-06 09:47 | 319 | 115 | 0 | 49,930 | – | – | – | 1.00 | – | – | 6.27 | 3398 | 253 | 50.9 → 76.0 | 209.2 / 32.3 / – | 540 / 1537 / – |
| tep_board_N_r2 | 1 | 2026-11-06 09:52 | 319 | 87 | 0 | 32,282 | – | – | – | 0.79 | – | – | 5.33 | 2865 | 171 | 51.5 → 73.7 | 131.4 / 108.8 / – | 536 / 1547 / – |

Board resources (on-board sampler, once a second, per episode): CPU seconds and peak memory of each model server. The NPU has no readable usage counter; its work shows as the NPU lane's call time. Supply power, if the board exposes it, is in each summary's `meta.resources`; energy is never estimated.
