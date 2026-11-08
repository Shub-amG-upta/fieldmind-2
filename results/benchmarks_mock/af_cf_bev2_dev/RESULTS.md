# Benchmark `af_cf_bev2_dev`

**MOCK backend: plumbing only, NOT an agent result.** Architecture **multi**, mode **lockstep**, overlay `configs/bev_ideas.yaml,configs/cranfield.yaml`, merge rule `hybrid`, models npu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, cpu: `gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf`, bev: `bev-decider-0.4B-backbone-Q8_0.gguf`. Agent code ran on the laptop and only model calls on the board, so tick times are laptop times. Energy not measured. Plant data: REAL rig data (Cranfield three-phase flow facility, Ruiz-Carcel et al. 2015).

bev ideas switches: `explain=on,clear_skip=on,explain_prompt=v2,empty_skip=on,one_code=on`. bev-decide on npu. bev idea calls: answered by bev-decide (failed = no answer, which makes the run invalid and is not kept; rejected = refused by the gate's check). used = an answer that changed what the agent did; shadow = asked and only logged. Decode tokens per tick: answer tokens written by every model per tick (bev writes none).

Group top-1 is the share of scored ticks (fault onset onward) whose published rank-1 cause is in the true case's look-alike group; belief group top-1 is the same for the code-only ranking. A held-out true case has no exact top-1. Unusable = a model answer that was not used (wrong format, failed call, rejected note reading). Settings and every run, stopped ones included: `test.json`.

| episode | run | finished | ticks | model calls | bev idea calls / failed / rejected | bev used / shadow | decode tokens per tick | unusable | tokens in | group top-1 | belief group top-1 | exact top-1 | faithfulness | actions P / R | lead time min | false alarms /h | tick p95 ms | wall s | chip C |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cf_F1_1.2_air_line_blockage | 1 | 2026-11-08 15:40 | 139 | 129 | 63 / 0 / 0 | 91 / 0 | 1.24 | 0 | 44,572 | 0.54 | 0.42 | 0.54 | 0.95 | – | – | – | 49 | 3 | – → – |
| cf_F2_2.2_water_line_blockage | 1 | 2026-11-08 15:40 | 107 | 67 | 29 / 0 / 0 | 41 / 0 | 0.95 | 0 | 16,669 | 0.47 | 0.32 | 0.47 | 1.00 | – | – | – | 27 | 2 | – → – |
| cf_F3_3.2_top_separator_input_blockage | 1 | 2026-11-08 15:40 | 200 | 178 | 78 / 0 / 0 | 152 / 0 | 1.16 | 0 | 44,504 | 0.16 | 0.00 | 0.16 | 0.98 | – | – | – | 48 | 6 | – → – |
| cf_F4_4.2_open_direct_bypass | 1 | 2026-11-08 15:41 | 139 | 126 | 61 / 0 / 0 | 81 / 0 | 1.26 | 0 | 42,312 | 0.20 | 0.00 | 0.20 | 1.00 | – | – | – | 35 | 4 | – → – |
| cf_F5_5.1_slugging_conditions | 1 | 2026-11-08 15:41 | 75 | 187 | 92 / 0 / 0 | 138 / 0 | 3.75 | 0 | 72,007 | 0.33 | 0.34 | 0.33 | 0.91 | – | – | – | 62 | 4 | – → – |
| cf_F6_6.1_pressurization_of_the_2in_line | 1 | 2026-11-08 15:41 | 84 | 35 | 17 / 0 / 0 | 30 / 0 | 0.32 | 0 | 6,749 | 0.80 | 0.97 | 0.80 | 1.00 | – | – | – | 22 | 2 | – → – |

## bev ideas per episode

| episode | run | idea | calls | failed | rejected | used | shadow | other counters |
|---|---|---|---|---|---|---|---|---|
| cf_F1_1.2_air_line_blockage | 1 | clear_skip | 0 | 0 | 0 | 7 | 0 | – |
| cf_F1_1.2_air_line_blockage | 1 | explain | 63 | 0 | 0 | 63 | 0 | over_limit 0 |
| cf_F1_1.2_air_line_blockage | 1 | one_code | 0 | 0 | 0 | 21 | 0 | – |
| cf_F2_2.2_water_line_blockage | 1 | clear_skip | 0 | 0 | 0 | 2 | 0 | – |
| cf_F2_2.2_water_line_blockage | 1 | explain | 29 | 0 | 0 | 29 | 0 | over_limit 0 |
| cf_F2_2.2_water_line_blockage | 1 | one_code | 0 | 0 | 0 | 10 | 0 | – |
| cf_F3_3.2_top_separator_input_blockage | 1 | clear_skip | 0 | 0 | 0 | 28 | 0 | – |
| cf_F3_3.2_top_separator_input_blockage | 1 | explain | 78 | 0 | 0 | 78 | 0 | over_limit 0 |
| cf_F3_3.2_top_separator_input_blockage | 1 | one_code | 0 | 0 | 0 | 46 | 0 | – |
| cf_F4_4.2_open_direct_bypass | 1 | clear_skip | 0 | 0 | 0 | 7 | 0 | – |
| cf_F4_4.2_open_direct_bypass | 1 | explain | 61 | 0 | 0 | 61 | 0 | over_limit 0 |
| cf_F4_4.2_open_direct_bypass | 1 | one_code | 0 | 0 | 0 | 13 | 0 | – |
| cf_F5_5.1_slugging_conditions | 1 | clear_skip | 0 | 0 | 0 | 30 | 0 | – |
| cf_F5_5.1_slugging_conditions | 1 | explain | 92 | 0 | 0 | 92 | 0 | over_limit 0 |
| cf_F5_5.1_slugging_conditions | 1 | one_code | 0 | 0 | 0 | 16 | 0 | – |
| cf_F6_6.1_pressurization_of_the_2in_line | 1 | clear_skip | 0 | 0 | 0 | 4 | 0 | – |
| cf_F6_6.1_pressurization_of_the_2in_line | 1 | explain | 17 | 0 | 0 | 17 | 0 | over_limit 0 |
| cf_F6_6.1_pressurization_of_the_2in_line | 1 | one_code | 0 | 0 | 0 | 9 | 0 | – |
