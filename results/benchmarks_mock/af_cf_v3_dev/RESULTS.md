# Benchmark `af_cf_v3_dev`

**MOCK backend: plumbing only, NOT an agent result.** Architecture **multi**, mode **lockstep**, overlay `configs/v3.yaml,configs/cranfield.yaml`, merge rule `hybrid`, models npu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, cpu: `gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf`. Agent code ran on the laptop and only model calls on the board, so tick times are laptop times. Energy not measured. Plant data: REAL rig data (Cranfield three-phase flow facility, Ruiz-Carcel et al. 2015).

Group top-1 is the share of scored ticks (fault onset onward) whose published rank-1 cause is in the true case's look-alike group; belief group top-1 is the same for the code-only ranking. A held-out true case has no exact top-1. Unusable = a model answer that was not used (wrong format, failed call, rejected note reading). Settings and every run, stopped ones included: `test.json`.

| episode | run | finished | ticks | model calls | unusable | tokens in | group top-1 | belief group top-1 | exact top-1 | faithfulness | actions P / R | lead time min | false alarms /h | tick p95 ms | wall s | chip C |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cf_F1_1.2_air_line_blockage | 1 | 2026-11-08 15:40 | 139 | 72 | 0 | 32,012 | 0.54 | 0.42 | 0.54 | 0.95 | – | – | – | 34 | 2 | – → – |
| cf_F2_2.2_water_line_blockage | 1 | 2026-11-08 15:40 | 107 | 38 | 0 | 14,273 | 0.47 | 0.32 | 0.47 | 1.00 | – | – | – | 22 | 2 | – → – |
| cf_F3_3.2_top_separator_input_blockage | 1 | 2026-11-08 15:40 | 200 | 115 | 0 | 42,211 | 0.16 | 0.00 | 0.16 | 0.98 | – | – | – | 39 | 6 | – → – |
| cf_F4_4.2_open_direct_bypass | 1 | 2026-11-08 15:40 | 139 | 71 | 0 | 30,772 | 0.20 | 0.00 | 0.20 | 1.00 | – | – | – | 29 | 3 | – → – |
| cf_F5_5.1_slugging_conditions | 1 | 2026-11-08 15:40 | 75 | 120 | 0 | 53,928 | 0.33 | 0.34 | 0.33 | 0.91 | – | – | – | 47 | 3 | – → – |
| cf_F6_6.1_pressurization_of_the_2in_line | 1 | 2026-11-08 15:40 | 84 | 22 | 0 | 7,867 | 0.80 | 0.97 | 0.80 | 1.00 | – | – | – | 19 | 1 | – → – |
