# Benchmark `cranfield_report_v3`

Architecture **multi**, mode **lockstep**, overlay `configs/v3.yaml,configs/cranfield.yaml`, merge rule `hybrid`, models npu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, cpu: `gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf`. Agent code ran on the laptop and only model calls on the board, so tick times are laptop times. Energy not measured. Data: real Cranfield rig recordings, not synthetic.

Group top-1 is the share of scored ticks (fault onset onward) whose published rank-1 cause is in the true case's look-alike group; belief group top-1 is the same for the code-only ranking. A held-out true case has no exact top-1. Unusable = a model answer that was not used (wrong format, failed call, rejected note reading). Settings and every run, stopped ones included: `test.json`.

| episode | run | finished | ticks | model calls | unusable | tokens in | group top-1 | belief group top-1 | exact top-1 | faithfulness | actions P / R | lead time min | false alarms /h | tick p95 ms | wall s | chip C | server CPU s npu / cpu / bev | peak RSS MB npu / cpu / bev |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cf_F1_1.1_air_line_blockage | 1 | 2026-11-06 00:11 | 184 | 96 | 0 | 51,093 | 0.51 | 0.22 | 0.51 | 0.98 | – | – | – | 5455 | 254 | 46.3 → 60.1 | 339.4 / 48.6 / – | 542 / 1557 / – |
| cf_F1_1.3_air_line_blockage | 1 | 2026-11-06 00:14 | 135 | 55 | 0 | 33,383 | 0.67 | 0.39 | 0.67 | 1.00 | – | – | – | 5786 | 164 | 51.3 → 62.8 | 217.6 / 22.2 / – | 548 / 1544 / – |
| cf_F2_2.1_water_line_blockage | 1 | 2026-11-06 00:18 | 297 | 93 | 0 | 44,109 | 0.09 | 0.00 | 0.09 | 1.00 | – | – | – | 2790 | 232 | 51.2 → 61.4 | 305.9 / 13.1 / – | 539 / 1562 / – |
| cf_F2_2.3_water_line_blockage | 1 | 2026-11-06 00:22 | 105 | 66 | 0 | 32,072 | 0.30 | 0.00 | 0.30 | 1.00 | – | – | – | 5210 | 166 | 52.5 → 61.7 | 224.7 / 17.6 / – | 535 / 1549 / – |
| cf_F3_3.1_top_separator_input_blockage | 1 | 2026-11-06 00:34 | 293 | 242 | 0 | 137,398 | 0.37 | 0.00 | 0.37 | 1.00 | – | – | – | 6281 | 702 | 51.5 → 63.7 | 937.6 / 74.5 / – | 570 / 1562 / – |
| cf_F3_3.3_top_separator_input_blockage | 1 | 2026-11-06 00:48 | 349 | 261 | 0 | 153,591 | 0.30 | 0.00 | 0.30 | 1.00 | – | – | – | 6381 | 789 | 52.3 → 63.3 | 1053.2 / 33.2 / – | 573 / 1560 / – |
| cf_F4_4.1_open_direct_bypass | 1 | 2026-11-06 00:58 | 231 | 181 | 0 | 97,609 | 0.12 | 0.00 | 0.12 | 1.00 | – | – | – | 5525 | 503 | 52.3 → 64.1 | 665.5 / 58.3 / – | 560 / 1561 / – |
| cf_F4_4.3_open_direct_bypass | 1 | 2026-11-06 01:03 | 113 | 93 | 0 | 54,423 | 0.21 | 0.08 | 0.21 | 1.00 | – | – | – | 6194 | 276 | 51.9 → 64.5 | 363.4 / 54.2 / – | 543 / 1570 / – |
| cf_F5_5.2_slugging_conditions | 1 | 2026-11-06 01:25 | 344 | 434 | 0 | 235,175 | 0.11 | 0.18 | 0.11 | 0.98 | – | – | – | 6565 | 1245 | 52.1 → 64.5 | 1666.6 / 88.9 / – | 600 / 1564 / – |
| cf_F6_6.2_pressurization_of_the_2in_line | 1 | 2026-11-06 01:30 | 151 | 93 | 0 | 43,642 | 0.49 | 0.66 | 0.49 | 1.00 | – | – | – | 4479 | 237 | 51.5 → 64.5 | 312.8 / 63.9 / – | 538 / 1552 / – |

Board resources (on-board sampler, once a second, per episode): CPU seconds and peak memory of each model server. The NPU has no readable usage counter; its work shows as the NPU lane's call time. Supply power, if the board exposes it, is in each summary's `meta.resources`; energy is never estimated.
