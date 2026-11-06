# Benchmark `cranfield_dev_v3_shuffled`

Architecture **multi**, mode **lockstep**, overlay `configs/v3.yaml,configs/cranfield.yaml,configs/case_shuffled.yaml`, merge rule `hybrid`, models npu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, cpu: `gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf`. Agent code ran on the laptop and only model calls on the board, so tick times are laptop times. Energy not measured. Plant data: REAL rig data (Cranfield three-phase flow facility, Ruiz-Carcel et al. 2015).

Group top-1 is the share of scored ticks (fault onset onward) whose published rank-1 cause is in the true case's look-alike group; belief group top-1 is the same for the code-only ranking. A held-out true case has no exact top-1. Unusable = a model answer that was not used (wrong format, failed call, rejected note reading). Settings and every run, stopped ones included: `test.json`.

| episode | run | finished | ticks | model calls | unusable | tokens in | group top-1 | belief group top-1 | exact top-1 | faithfulness | actions P / R | lead time min | false alarms /h | tick p95 ms | wall s | chip C | server CPU s npu / cpu / bev | peak RSS MB npu / cpu / bev |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cf_F1_1.2_air_line_blockage | 1 | 2026-11-06 10:11 | 139 | 73 | 0 | 42,703 | 0.51 | 0.42 | 0.51 | 0.95 | – | – | – | 5757 | 199 | 36.6 → 59.0 | 274.6 / 28.9 / – | 544 / 1568 / – |
| cf_F2_2.2_water_line_blockage | 1 | 2026-11-06 10:16 | 107 | 40 | 0 | 19,475 | 0.41 | 0.32 | 0.41 | 1.00 | – | – | – | 4618 | 97 | 40.5 → 57.9 | 125.5 / 33.1 / – | 532 / 1558 / – |
| cf_F3_3.2_top_separator_input_blockage | 1 | 2026-11-06 10:23 | 200 | 119 | 0 | 58,567 | 0.14 | 0.00 | 0.14 | 0.98 | – | – | – | 4416 | 297 | 40.3 → 62.5 | 381.9 / 107.4 / – | 552 / 1563 / – |
| cf_F4_4.2_open_direct_bypass | 1 | 2026-11-06 10:31 | 139 | 71 | 0 | 40,543 | 0.15 | 0.00 | 0.15 | 1.00 | – | – | – | 5409 | 196 | 40.5 → 62.4 | 278.2 / 15.8 / – | 540 / 1564 / – |
| cf_F5_5.1_slugging_conditions | 1 | 2026-11-06 10:40 | 75 | 120 | 0 | 71,941 | 0.31 | 0.34 | 0.31 | 0.91 | – | – | – | 6996 | 353 | 40.9 → 64.8 | 477.0 / 34.9 / – | 546 / 1562 / – |
| cf_F6_6.1_pressurization_of_the_2in_line | 1 | 2026-11-06 10:47 | 84 | 22 | 0 | 10,560 | 0.86 | 0.97 | 0.86 | 1.00 | – | – | – | 2668 | 62 | 40.5 → 54.8 | 73.1 / 0.1 / – | 526 / 1475 / – |

Board resources (on-board sampler, once a second, per episode): CPU seconds and peak memory of each model server. The NPU has no readable usage counter; its work shows as the NPU lane's call time. Supply power, if the board exposes it, is in each summary's `meta.resources`; energy is never estimated.
