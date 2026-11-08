# Benchmark `af_cf_v3_dev`

Architecture **multi**, mode **lockstep**, overlay `configs/v3.yaml,configs/cranfield.yaml`, merge rule `hybrid`, models npu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, cpu: `gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf`. Agent code ran on the laptop and only model calls on the board, so tick times are laptop times. Energy not measured. Plant data: REAL rig data (Cranfield three-phase flow facility, Ruiz-Carcel et al. 2015).

Group top-1 is the share of scored ticks (fault onset onward) whose published rank-1 cause is in the true case's look-alike group; belief group top-1 is the same for the code-only ranking. A held-out true case has no exact top-1. Unusable = a model answer that was not used (wrong format, failed call, rejected note reading). Settings and every run, stopped ones included: `test.json`.

| episode | run | finished | ticks | model calls | unusable | tokens in | group top-1 | belief group top-1 | exact top-1 | faithfulness | actions P / R | lead time min | false alarms /h | tick p95 ms | wall s | chip C | server CPU s npu / cpu / bev | peak RSS MB npu / cpu / bev |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cf_F1_1.2_air_line_blockage | 1 | 2026-11-08 15:45 | 139 | 72 | 0 | 41,895 | 0.54 | 0.42 | 0.54 | 0.95 | – | – | – | 5183 | 181 | 31.0 → 56.2 | 272.9 / 13.2 / – | 539 / 1539 / – |
| cf_F2_2.2_water_line_blockage | 1 | 2026-11-08 15:50 | 107 | 38 | 0 | 18,551 | 0.47 | 0.32 | 0.47 | 1.00 | – | – | – | 4391 | 87 | 36.6 → 52.9 | 121.8 / 14.0 / – | 531 / 1546 / – |
| cf_F3_3.2_top_separator_input_blockage | 1 | 2026-11-08 15:57 | 200 | 115 | 0 | 57,306 | 0.16 | 0.00 | 0.16 | 0.98 | – | – | – | 3229 | 270 | 36.3 → 60.6 | 380.3 / 83.6 / – | 554 / 1562 / – |
| cf_F4_4.2_open_direct_bypass | 1 | 2026-11-08 16:05 | 139 | 71 | 0 | 40,544 | 0.20 | 0.00 | 0.20 | 1.00 | – | – | – | 5019 | 181 | 36.6 → 58.7 | 263.0 / 15.6 / – | 542 / 1579 / – |
| cf_F5_5.1_slugging_conditions | 1 | 2026-11-08 16:14 | 75 | 120 | 0 | 71,946 | 0.33 | 0.34 | 0.33 | 0.91 | – | – | – | 6355 | 322 | 36.6 → 59.8 | 474.6 / 34.0 / – | 546 / 1561 / – |
| cf_F6_6.1_pressurization_of_the_2in_line | 1 | 2026-11-08 16:20 | 84 | 22 | 0 | 10,560 | 0.80 | 0.97 | 0.80 | 1.00 | – | – | – | 2438 | 53 | 36.6 → 50.4 | 74.9 / 0.1 / – | 528 / 1475 / – |

Board resources (on-board sampler, once a second, per episode): CPU seconds and peak memory of each model server. The NPU has no readable usage counter; its work shows as the NPU lane's call time. Supply power, if the board exposes it, is in each summary's `meta.resources`; energy is never estimated.
