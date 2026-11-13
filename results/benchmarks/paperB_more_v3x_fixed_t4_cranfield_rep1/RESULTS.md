# Benchmark `paperB_more_v3x_fixed_t4_cranfield_rep1`

Architecture **multi**, mode **realtime** (tick 4.0 s), overlay `configs/v3.yaml,configs/cranfield.yaml,configs/bev_ideas.yaml,configs/laya_board.yaml,configs/sched_study.yaml`, merge rule `hybrid`, models npu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, cpu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, bev: `laya-7b928d8-Q8_0.gguf`. Agent code ran on the laptop and only model calls on the board, so tick times are laptop times. Energy not measured. Plant data: REAL rig data (Cranfield three-phase flow facility, Ruiz-Carcel et al. 2015).

bev ideas switches: `explain=on,clear_skip=on`. Laya on llama-server on npu. bev idea calls: answered by Laya on llama-server (failed = no answer, which makes the run invalid and is not kept; rejected = refused by the gate's check). used = an answer that changed what the agent did; shadow = asked and only logged. Decode tokens per tick: answer tokens written by every model per tick (bev writes none).

Group top-1 is the share of scored ticks (fault onset onward) whose published rank-1 cause is in the true case's look-alike group; belief group top-1 is the same for the code-only ranking. A held-out true case has no exact top-1. Unusable = a model answer that was not used (wrong format, failed call, rejected note reading). Settings and every run, stopped ones included: `test.json`.

| episode | run | finished | ticks | model calls | bev idea calls / failed / rejected | bev used / shadow | decode tokens per tick | unusable | tokens in | group top-1 | belief group top-1 | exact top-1 | faithfulness | actions P / R | lead time min | false alarms /h | tick p95 ms | wall s | chip C | server CPU s npu / cpu / bev | peak RSS MB npu / cpu / bev |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cf_F1_1.2_air_line_blockage | 1 | 2026-11-13 10:26 | 139 | 137 | 68 / 0 / 0 | 69 / 0 | 3.96 | 0 | 36,852 | 0.51 | 0.42 | 0.51 | 0.95 | – | – | – | 86 | 555 | 39.9 → 52.3 | 48.4 / 327.8 / 13.7 | 539 / 4432 / 230 |
| cf_F2_2.2_water_line_blockage | 1 | 2026-11-13 10:34 | 107 | 67 | 29 / 0 / 0 | 29 / 0 | 3.12 | 0 | 16,551 | 0.29 | 0.32 | 0.29 | 1.00 | – | – | – | 53 | 426 | 43.8 → 43.4 | 25.8 / 72.2 / 5.5 | 533 / 4422 / 186 |
| cf_F3_3.2_top_separator_input_blockage | 1 | 2026-11-13 10:48 | 200 | 178 | 81 / 0 / 0 | 95 / 0 | 3.63 | 1 | 43,330 | 0.03 | 0.00 | 0.03 | 0.97 | – | – | – | 88 | 800 | 43.8 → 48.8 | 65.9 / 530.6 / 15.2 | 543 / 4407 / 223 |
| cf_F4_4.2_open_direct_bypass | 1 | 2026-11-13 10:58 | 139 | 137 | 65 / 0 / 0 | 65 / 0 | 4.71 | 0 | 36,599 | 0.06 | 0.00 | 0.06 | 1.00 | – | – | – | 72 | 555 | 44.2 → 44.2 | 53.5 / 142.2 / 14.6 | 540 / 4430 / 225 |
| cf_F5_5.1_slugging_conditions | 1 | 2026-11-13 11:03 | 75 | 231 | 115 / 0 / 0 | 116 / 0 | 12.64 | 0 | 62,944 | 0.34 | 0.34 | 0.34 | 0.91 | – | – | – | 99 | 300 | 43.8 → 58.0 | 89.9 / 93.0 / 28.9 | 545 / 4430 / 237 |
| cf_F6_6.1_pressurization_of_the_2in_line | 1 | 2026-11-13 11:10 | 84 | 39 | 19 / 0 / 0 | 23 / 0 | 1.64 | 0 | 8,284 | 0.97 | 0.97 | 0.97 | 1.00 | – | – | – | 48 | 334 | 43.8 → 41.9 | 13.5 / 0.2 / 3.3 | 528 / 4358 / 190 |

## bev ideas per episode

| episode | run | idea | calls | failed | rejected | used | shadow | other counters |
|---|---|---|---|---|---|---|---|---|
| cf_F1_1.2_air_line_blockage | 1 | clear_skip | 0 | 0 | 0 | 2 | 0 | – |
| cf_F1_1.2_air_line_blockage | 1 | explain | 68 | 0 | 0 | 67 | 0 | over_limit 0 |
| cf_F2_2.2_water_line_blockage | 1 | explain | 29 | 0 | 0 | 29 | 0 | over_limit 0 |
| cf_F3_3.2_top_separator_input_blockage | 1 | clear_skip | 0 | 0 | 0 | 15 | 0 | – |
| cf_F3_3.2_top_separator_input_blockage | 1 | explain | 81 | 0 | 0 | 80 | 0 | over_limit 0 |
| cf_F4_4.2_open_direct_bypass | 1 | clear_skip | 0 | 0 | 0 | 1 | 0 | – |
| cf_F4_4.2_open_direct_bypass | 1 | explain | 65 | 0 | 0 | 64 | 0 | over_limit 0 |
| cf_F5_5.1_slugging_conditions | 1 | clear_skip | 0 | 0 | 0 | 2 | 0 | – |
| cf_F5_5.1_slugging_conditions | 1 | explain | 115 | 0 | 0 | 114 | 0 | over_limit 0 |
| cf_F6_6.1_pressurization_of_the_2in_line | 1 | clear_skip | 0 | 0 | 0 | 4 | 0 | – |
| cf_F6_6.1_pressurization_of_the_2in_line | 1 | explain | 19 | 0 | 0 | 19 | 0 | over_limit 0 |

Board resources (on-board sampler, once a second, per episode): CPU seconds and peak memory of each model server. The NPU has no readable usage counter; its work shows as the NPU lane's call time. Supply power, if the board exposes it, is in each summary's `meta.resources`; energy is never estimated.
