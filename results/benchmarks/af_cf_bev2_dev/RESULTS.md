# Benchmark `af_cf_bev2_dev`

Architecture **multi**, mode **lockstep**, overlay `configs/bev_ideas.yaml,configs/cranfield.yaml`, merge rule `hybrid`, models npu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, cpu: `gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf`, bev: `bev-decider-0.4B-backbone-Q8_0.gguf`. Agent code ran on the laptop and only model calls on the board, so tick times are laptop times. Energy not measured. Plant data: REAL rig data (Cranfield three-phase flow facility, Ruiz-Carcel et al. 2015).

bev ideas switches: `explain=on,clear_skip=on,explain_prompt=v2,empty_skip=on,one_code=on`. bev-decide on npu. bev idea calls: answered by bev-decide (failed = no answer, which makes the run invalid and is not kept; rejected = refused by the gate's check). used = an answer that changed what the agent did; shadow = asked and only logged. Decode tokens per tick: answer tokens written by every model per tick (bev writes none).

Group top-1 is the share of scored ticks (fault onset onward) whose published rank-1 cause is in the true case's look-alike group; belief group top-1 is the same for the code-only ranking. A held-out true case has no exact top-1. Unusable = a model answer that was not used (wrong format, failed call, rejected note reading). Settings and every run, stopped ones included: `test.json`.

| episode | run | finished | ticks | model calls | bev idea calls / failed / rejected | bev used / shadow | decode tokens per tick | unusable | tokens in | group top-1 | belief group top-1 | exact top-1 | faithfulness | actions P / R | lead time min | false alarms /h | tick p95 ms | wall s | chip C | server CPU s npu / cpu / bev | peak RSS MB npu / cpu / bev |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cf_F1_1.2_air_line_blockage | 1 | 2026-11-08 16:22 | 139 | 139 | 67 / 0 / 0 | 91 / 0 | 3.55 | 0 | 75,735 | 0.38 | 0.42 | 0.38 | 0.95 | – | – | – | 4153 | 110 | 45.3 → 54.4 | 53.5 / 41.8 / 18.8 | 534 / 1564 / 483 |
| cf_F2_2.2_water_line_blockage | 1 | 2026-11-08 16:24 | 107 | 69 | 29 / 0 / 0 | 39 / 0 | 2.86 | 0 | 24,723 | 0.35 | 0.32 | 0.35 | 1.00 | – | – | – | 2812 | 52 | 48.4 → 54.0 | 26.8 / 33.5 / 6.2 | 522 / 1558 / 492 |
| cf_F3_3.2_top_separator_input_blockage | 1 | 2026-11-08 16:26 | 200 | 173 | 78 / 0 / 0 | 152 / 0 | 2.17 | 0 | 73,983 | 0.00 | 0.00 | 0.00 | 1.00 | – | – | – | 2324 | 109 | 47.1 → 58.7 | 51.4 / 14.0 / 19.2 | 533 / 1539 / 515 |
| cf_F4_4.2_open_direct_bypass | 1 | 2026-11-08 16:28 | 139 | 125 | 61 / 0 / 0 | 81 / 0 | 3.02 | 0 | 66,314 | 0.08 | 0.00 | 0.08 | 1.00 | – | – | – | 3155 | 101 | 49.4 → 57.7 | 53.6 / 0.1 / 16.8 | 534 / 1476 / 535 |
| cf_F5_5.1_slugging_conditions | 1 | 2026-11-08 16:32 | 75 | 208 | 102 / 0 / 0 | 134 / 0 | 10.85 | 0 | 137,955 | 0.31 | 0.34 | 0.31 | 0.91 | – | – | – | 5021 | 194 | 50.2 → 59.8 | 96.3 / 48.8 / 33.0 | 541 / 1564 / 576 |
| cf_F6_6.1_pressurization_of_the_2in_line | 1 | 2026-11-08 16:34 | 84 | 35 | 17 / 0 / 0 | 31 / 0 | 0.86 | 0 | 10,186 | 0.80 | 0.97 | 0.80 | 1.00 | – | – | – | 1598 | 23 | 49.4 → 52.9 | 9.8 / 0.0 / 3.4 | 517 / 1476 / 580 |

## bev ideas per episode

| episode | run | idea | calls | failed | rejected | used | shadow | other counters |
|---|---|---|---|---|---|---|---|---|
| cf_F1_1.2_air_line_blockage | 1 | clear_skip | 0 | 0 | 0 | 3 | 0 | – |
| cf_F1_1.2_air_line_blockage | 1 | explain | 67 | 0 | 0 | 67 | 0 | over_limit 0 |
| cf_F1_1.2_air_line_blockage | 1 | one_code | 0 | 0 | 0 | 21 | 0 | – |
| cf_F2_2.2_water_line_blockage | 1 | explain | 29 | 0 | 0 | 29 | 0 | over_limit 0 |
| cf_F2_2.2_water_line_blockage | 1 | one_code | 0 | 0 | 0 | 10 | 0 | – |
| cf_F3_3.2_top_separator_input_blockage | 1 | clear_skip | 0 | 0 | 0 | 28 | 0 | – |
| cf_F3_3.2_top_separator_input_blockage | 1 | explain | 78 | 0 | 0 | 78 | 0 | over_limit 0 |
| cf_F3_3.2_top_separator_input_blockage | 1 | one_code | 0 | 0 | 0 | 46 | 0 | – |
| cf_F4_4.2_open_direct_bypass | 1 | clear_skip | 0 | 0 | 0 | 7 | 0 | – |
| cf_F4_4.2_open_direct_bypass | 1 | explain | 61 | 0 | 0 | 61 | 0 | over_limit 0 |
| cf_F4_4.2_open_direct_bypass | 1 | one_code | 0 | 0 | 0 | 13 | 0 | – |
| cf_F5_5.1_slugging_conditions | 1 | clear_skip | 0 | 0 | 0 | 17 | 0 | – |
| cf_F5_5.1_slugging_conditions | 1 | explain | 102 | 0 | 0 | 102 | 0 | over_limit 0 |
| cf_F5_5.1_slugging_conditions | 1 | one_code | 0 | 0 | 0 | 15 | 0 | – |
| cf_F6_6.1_pressurization_of_the_2in_line | 1 | clear_skip | 0 | 0 | 0 | 5 | 0 | – |
| cf_F6_6.1_pressurization_of_the_2in_line | 1 | explain | 17 | 0 | 0 | 17 | 0 | over_limit 0 |
| cf_F6_6.1_pressurization_of_the_2in_line | 1 | one_code | 0 | 0 | 0 | 9 | 0 | – |

Board resources (on-board sampler, once a second, per episode): CPU seconds and peak memory of each model server. The NPU has no readable usage counter; its work shows as the NPU lane's call time. Supply power, if the board exposes it, is in each summary's `meta.resources`; energy is never estimated.
