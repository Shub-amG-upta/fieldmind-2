# Benchmark `cranfield_dev_bev_explain_skip`

Architecture **multi**, mode **lockstep**, overlay `configs/bev_ideas.yaml,configs/cranfield.yaml`, merge rule `hybrid`, models npu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, cpu: `gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf`, bev: `bev-decider-0.4B-backbone-Q8_0.gguf`. Agent code ran on the laptop and only model calls on the board, so tick times are laptop times. Energy not measured. Plant data: REAL rig data (Cranfield three-phase flow facility, Ruiz-Carcel et al. 2015).

bev ideas switches: `explain=on,clear_skip=on`. bev-decide on npu. bev idea calls: answered by bev-decide (failed = no answer, which makes the run invalid and is not kept; rejected = refused by the gate's check). used = an answer that changed what the agent did; shadow = asked and only logged. Decode tokens per tick: answer tokens written by every model per tick (bev writes none).

Group top-1 is the share of scored ticks (fault onset onward) whose published rank-1 cause is in the true case's look-alike group; belief group top-1 is the same for the code-only ranking. A held-out true case has no exact top-1. Unusable = a model answer that was not used (wrong format, failed call, rejected note reading). Settings and every run, stopped ones included: `test.json`.

| episode | run | finished | ticks | model calls | bev idea calls / failed / rejected | bev used / shadow | decode tokens per tick | unusable | tokens in | group top-1 | belief group top-1 | exact top-1 | faithfulness | actions P / R | lead time min | false alarms /h | tick p95 ms | wall s | chip C | server CPU s npu / cpu / bev | peak RSS MB npu / cpu / bev |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cf_F1_1.2_air_line_blockage | 1 | 2026-11-06 13:09 | 139 | 139 | 65 / 0 / 0 | 68 / 0 | 4.38 | 3 | 81,578 | 0.50 | 0.42 | 0.50 | 0.95 | – | – | – | 308 | 24 | 65.1 → 69.0 | 1.0 / 0.0 / 0.2 | 503 / 1475 / 481 |
| cf_F2_2.2_water_line_blockage | 1 | 2026-11-06 13:28 | 107 | 69 | 29 / 0 / 0 | 29 / 0 | 3.44 | 0 | 28,610 | 0.32 | 0.32 | 0.32 | 1.00 | – | – | – | 3282 | 73 | 52.5 → 75.2 | 18.7 / 64.3 / 3.6 | 527 / 1555 / 489 |
| cf_F3_3.2_top_separator_input_blockage | 1 | 2026-11-06 13:49 | 200 | 182 | 78 / 0 / 0 | 106 / 0 | 4.58 | 0 | 94,395 | 0.04 | 0.00 | 0.04 | 0.96 | – | – | – | 4104 | 228 | 50.2 → 58.3 | 66.2 / 186.8 / 16.1 | 548 / 1557 / 512 |
| cf_F4_4.2_open_direct_bypass | 1 | 2026-11-06 13:56 | 139 | 146 | 65 / 0 / 0 | 67 / 0 | 5.93 | 0 | 86,491 | 0.05 | 0.00 | 0.05 | 1.00 | – | – | – | 3557 | 152 | 39.7 → 57.1 | 72.1 / 124.2 / 18.5 | 536 / 1556 / 534 |
| cf_F5_5.1_slugging_conditions | 1 | 2026-11-06 14:04 | 75 | 233 | 115 / 0 / 0 | 117 / 0 | 12.81 | 0 | 163,603 | 0.33 | 0.34 | 0.33 | 0.91 | – | – | – | 5081 | 234 | 39.3 → 58.3 | 122.4 / 33.3 / 37.2 | 540 / 1564 / 579 |
| cf_F6_6.1_pressurization_of_the_2in_line | 1 | 2026-11-06 14:09 | 84 | 37 | 18 / 0 / 0 | 22 / 0 | 1.60 | 0 | 14,862 | 0.94 | 0.97 | 0.94 | 1.00 | – | – | – | 1666 | 34 | 39.7 → 47.5 | 17.6 / 0.0 / 3.9 | 516 / 1475 / 584 |

## bev ideas per episode

| episode | run | idea | calls | failed | rejected | used | shadow | other counters |
|---|---|---|---|---|---|---|---|---|
| cf_F1_1.2_air_line_blockage | 1 | clear_skip | 0 | 0 | 0 | 3 | 0 | – |
| cf_F1_1.2_air_line_blockage | 1 | explain | 65 | 0 | 0 | 65 | 0 | over_limit 0 |
| cf_F2_2.2_water_line_blockage | 1 | explain | 29 | 0 | 0 | 29 | 0 | over_limit 0 |
| cf_F3_3.2_top_separator_input_blockage | 1 | clear_skip | 0 | 0 | 0 | 28 | 0 | – |
| cf_F3_3.2_top_separator_input_blockage | 1 | explain | 78 | 0 | 0 | 78 | 0 | over_limit 0 |
| cf_F4_4.2_open_direct_bypass | 1 | clear_skip | 0 | 0 | 0 | 2 | 0 | – |
| cf_F4_4.2_open_direct_bypass | 1 | explain | 65 | 0 | 0 | 65 | 0 | over_limit 0 |
| cf_F5_5.1_slugging_conditions | 1 | clear_skip | 0 | 0 | 0 | 2 | 0 | – |
| cf_F5_5.1_slugging_conditions | 1 | explain | 115 | 0 | 0 | 115 | 0 | over_limit 0 |
| cf_F6_6.1_pressurization_of_the_2in_line | 1 | clear_skip | 0 | 0 | 0 | 4 | 0 | – |
| cf_F6_6.1_pressurization_of_the_2in_line | 1 | explain | 18 | 0 | 0 | 18 | 0 | over_limit 0 |

Board resources (on-board sampler, once a second, per episode): CPU seconds and peak memory of each model server. The NPU has no readable usage counter; its work shows as the NPU lane's call time. Supply power, if the board exposes it, is in each summary's `meta.resources`; energy is never estimated.
