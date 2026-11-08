# Benchmark `af_tep_v3_board`

**MOCK backend: plumbing only, NOT an agent result.** Architecture **multi**, mode **lockstep**, overlay `configs/v3.yaml,configs/tep.yaml`, merge rule `hybrid`, models npu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, cpu: `gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf`. Agent code ran on the laptop and only model calls on the board, so tick times are laptop times. Energy not measured. Plant data: simulated (Tennessee Eastman Process, Rieth et al. 2017).

Group top-1 is the share of scored ticks (fault onset onward) whose published rank-1 cause is in the true case's look-alike group; belief group top-1 is the same for the code-only ranking. A held-out true case has no exact top-1. Unusable = a model answer that was not used (wrong format, failed call, rejected note reading). Settings and every run, stopped ones included: `test.json`.

| episode | run | finished | ticks | model calls | unusable | tokens in | group top-1 | belief group top-1 | exact top-1 | faithfulness | actions P / R | lead time min | false alarms /h | tick p95 ms | wall s | chip C |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tep_board_F01_r1 | 1 | 2026-11-08 15:41 | 319 | 357 | 0 | 249,219 | 0.09 | 0.00 | 0.09 | 1.00 | – | – | – | 5 | 2 | – → – |
| tep_board_F02_r1 | 1 | 2026-11-08 15:41 | 319 | 335 | 0 | 200,958 | 0.66 | 0.66 | 0.66 | 1.00 | – | – | – | 4 | 2 | – → – |
| tep_board_F03_r1 | 1 | 2026-11-08 15:41 | 319 | 132 | 0 | 47,744 | 0.00 | 0.00 | 0.00 | 1.00 | – | – | – | 3 | 1 | – → – |
| tep_board_F04_r1 | 1 | 2026-11-08 15:41 | 319 | 224 | 0 | 105,476 | 0.88 | 0.00 | 0.88 | 1.00 | – | – | – | 3 | 1 | – → – |
| tep_board_F05_r1 | 1 | 2026-11-08 15:41 | 319 | 363 | 0 | 256,862 | 0.30 | 0.32 | 0.00 | 1.00 | – | – | – | 5 | 2 | – → – |
| tep_board_F06_r1 | 1 | 2026-11-08 15:41 | 319 | 352 | 0 | 243,557 | 0.85 | 0.82 | 0.85 | 1.00 | – | – | – | 5 | 2 | – → – |
| tep_board_F07_r1 | 1 | 2026-11-08 15:41 | 319 | 367 | 0 | 262,634 | 0.00 | 0.00 | 0.00 | 0.99 | – | – | – | 5 | 2 | – → – |
| tep_board_F08_r1 | 1 | 2026-11-08 15:41 | 319 | 332 | 0 | 232,163 | 0.18 | 0.27 | 0.18 | 1.00 | – | – | – | 5 | 2 | – → – |
| tep_board_F09_r1 | 1 | 2026-11-08 15:41 | 319 | 130 | 0 | 49,035 | 0.03 | 0.00 | 0.00 | 1.00 | – | – | – | 3 | 1 | – → – |
| tep_board_F10_r1 | 1 | 2026-11-08 15:41 | 319 | 293 | 0 | 157,097 | 0.10 | 0.07 | 0.00 | 0.99 | – | – | – | 4 | 1 | – → – |
| tep_board_F11_r1 | 1 | 2026-11-08 15:41 | 319 | 230 | 0 | 136,137 | 0.43 | 0.57 | 0.43 | 1.00 | – | – | – | 3 | 1 | – → – |
| tep_board_F12_r1 | 1 | 2026-11-08 15:41 | 319 | 349 | 0 | 241,825 | 0.92 | 0.12 | 0.92 | 1.00 | – | – | – | 5 | 2 | – → – |
| tep_board_F13_r1 | 1 | 2026-11-08 15:41 | 319 | 249 | 0 | 156,030 | 0.49 | 0.46 | 0.49 | 1.00 | – | – | – | 4 | 1 | – → – |
| tep_board_F14_r1 | 1 | 2026-11-08 15:42 | 319 | 254 | 0 | 158,493 | 0.96 | 0.33 | 0.96 | 1.00 | – | – | – | 3 | 1 | – → – |
| tep_board_F15_r1 | 1 | 2026-11-08 15:42 | 319 | 131 | 0 | 47,970 | 0.00 | 0.00 | 0.00 | 0.87 | – | – | – | 3 | 1 | – → – |
| tep_board_F16_r1 | 1 | 2026-11-08 15:42 | 319 | 227 | 0 | 132,895 | 0.97 | 0.96 | 0.97 | 1.00 | – | – | – | 3 | 1 | – → – |
| tep_board_F17_r1 | 1 | 2026-11-08 15:42 | 319 | 170 | 0 | 97,064 | 0.67 | 0.85 | 0.67 | 1.00 | – | – | – | 3 | 1 | – → – |
| tep_board_F18_r1 | 1 | 2026-11-08 15:42 | 319 | 239 | 0 | 160,734 | 0.44 | 0.46 | 0.44 | 1.00 | – | – | – | 5 | 2 | – → – |
| tep_board_F19_r1 | 1 | 2026-11-08 15:42 | 319 | 286 | 0 | 175,157 | 0.71 | 0.43 | 0.71 | 0.99 | – | – | – | 3 | 1 | – → – |
| tep_board_F20_r1 | 1 | 2026-11-08 15:42 | 319 | 224 | 0 | 130,020 | 0.84 | 0.96 | 0.84 | 0.97 | – | – | – | 4 | 1 | – → – |
| tep_board_N_r1 | 1 | 2026-11-08 15:42 | 319 | 128 | 0 | 46,533 | – | – | – | 1.00 | – | – | 2.82 | 3 | 1 | – → – |
| tep_board_N_r2 | 1 | 2026-11-08 15:42 | 319 | 86 | 0 | 27,016 | – | – | – | 1.00 | – | – | 2.45 | 3 | 1 | – → – |
