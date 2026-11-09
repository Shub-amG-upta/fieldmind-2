# Benchmark `cranfield_dev_v3`

Architecture **multi**, mode **lockstep**, overlay `configs/v3.yaml,configs/cranfield.yaml`, merge rule `hybrid`, models npu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, cpu: `gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf`. Agent code ran on the laptop and only model calls on the board, so tick times are laptop times. Energy not measured. Data: real Cranfield rig recordings, not synthetic.

Group top-1 is the share of scored ticks (fault onset onward) whose published rank-1 cause is in the true case's look-alike group; belief group top-1 is the same for the code-only ranking. A held-out true case has no exact top-1. Unusable = a model answer that was not used (wrong format, failed call, rejected note reading). Settings and every run, stopped ones included: `test.json`.

| episode | run | finished | ticks | model calls | unusable | tokens in | group top-1 | belief group top-1 | exact top-1 | faithfulness | actions P / R | lead time min | false alarms /h | tick p95 ms | wall s | chip C | server CPU s npu / cpu / bev | peak RSS MB npu / cpu / bev |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cf_F1_1.2_air_line_blockage | 1 | 2026-11-05 23:33 | 139 | 72 | 0 | 41,895 | 0.54 | 0.42 | 0.54 | 0.95 | – | – | – | 5310 | 189 | 34.1 → 57.5 | 270.2 / 13.4 / – | 544 / 1540 / – |
| cf_F2_2.2_water_line_blockage | 1 | 2026-11-05 23:37 | 107 | 38 | 0 | 18,551 | 0.47 | 0.32 | 0.47 | 1.00 | – | – | – | 4432 | 89 | 38.7 → 55.2 | 121.0 / 13.8 / – | 536 / 1551 / – |
| cf_F3_3.2_top_separator_input_blockage | 1 | 2026-11-05 23:45 | 200 | 115 | 0 | 57,306 | 0.16 | 0.00 | 0.16 | 0.98 | – | – | – | 3159 | 280 | 38.2 → 61.6 | 376.9 / 75.0 / – | 544 / 1559 / – |
| cf_F4_4.2_open_direct_bypass | 1 | 2026-11-05 23:51 | 139 | 71 | 0 | 40,544 | 0.20 | 0.00 | 0.20 | 1.00 | – | – | – | 5094 | 189 | 38.7 → 60.1 | 264.6 / 15.6 / – | 540 / 1559 / – |
| cf_F5_5.1_slugging_conditions | 1 | 2026-11-06 00:01 | 75 | 120 | 0 | 71,946 | 0.33 | 0.34 | 0.33 | 0.91 | – | – | – | 6388 | 336 | 38.6 → 62.0 | 481.1 / 34.3 / – | 551 / 1561 / – |
| cf_F6_6.1_pressurization_of_the_2in_line | 1 | 2026-11-06 00:06 | 84 | 22 | 0 | 10,560 | 0.80 | 0.97 | 0.80 | 1.00 | – | – | – | 2440 | 55 | 38.4 → 53.5 | 74.4 / 0.1 / – | 530 / 1475 / – |

Board resources (on-board sampler, once a second, per episode): CPU seconds and peak memory of each model server. The NPU has no readable usage counter; its work shows as the NPU lane's call time. Supply power, if the board exposes it, is in each summary's `meta.resources`; energy is never estimated.
