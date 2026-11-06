# Benchmark `cranfield_dev_v3_bev`

Architecture **bev**, mode **lockstep**, overlay `configs/bev3.yaml,configs/cranfield.yaml`, merge rule `hybrid`, models npu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, cpu: `gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf`, bev: `bev-decider-0.4B-backbone-Q8_0.gguf`. Agent code ran on the laptop and only model calls on the board, so tick times are laptop times. Energy not measured. Plant data: REAL rig data (Cranfield three-phase flow facility, Ruiz-Carcel et al. 2015).

Group top-1 is the share of scored ticks (fault onset onward) whose published rank-1 cause is in the true case's look-alike group; belief group top-1 is the same for the code-only ranking. A held-out true case has no exact top-1. Unusable = a model answer that was not used (wrong format, failed call, rejected note reading). Settings and every run, stopped ones included: `test.json`. Model calls include the decider's. Decider calls: answered by bev-decide (failed = no answer; rejected = refused by the gate's check). Replay ok: bench/replay_multi rebuilds every published ranking from the saved answers, decider included.

| episode | run | finished | ticks | model calls | decider calls / failed / rejected | unusable | tokens in | group top-1 | belief group top-1 | exact top-1 | faithfulness | actions P / R | lead time min | false alarms /h | tick p95 ms | wall s | chip C | replay ok | server CPU s npu / cpu / bev | peak RSS MB npu / cpu / bev |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cf_F1_1.2_air_line_blockage | 1 | 2026-11-06 10:58 | 139 | 124 | 52 / 0 / 0 | 0 | 60,394 | 0.53 | 0.42 | 0.53 | 0.95 | – | – | – | 6433 | 234 | 38.7 → 61.4 | yes | 274.0 / 13.9 / 8.5 | 542 / 1544 / 462 |
| cf_F2_2.2_water_line_blockage | 1 | 2026-11-06 11:06 | 107 | 67 | 30 / 0 / 0 | 0 | 25,150 | 0.47 | 0.32 | 0.47 | 1.00 | – | – | – | 4575 | 109 | 41.3 → 56.0 | yes | 121.2 / 6.6 / 4.6 | 530 / 1544 / 466 |
| cf_F3_3.2_top_separator_input_blockage | 1 | 2026-11-06 11:17 | 200 | 219 | 105 / 0 / 0 | 0 | 81,850 | 0.16 | 0.00 | 0.16 | 1.00 | – | – | – | 3993 | 367 | 41.3 → 60.6 | yes | 378.8 / 67.4 / 14.9 | 544 / 1562 / 482 |
| cf_F4_4.2_open_direct_bypass | 1 | 2026-11-06 11:25 | 139 | 133 | 62 / 0 / 0 | 0 | 59,433 | 0.20 | 0.00 | 0.20 | 1.00 | – | – | – | 5732 | 234 | 41.3 → 58.3 | yes | 266.0 / 15.2 / 9.4 | 540 / 1560 / 491 |
| cf_F5_5.1_slugging_conditions | 1 | 2026-11-06 11:35 | 75 | 195 | 75 / 0 / 0 | 0 | 102,349 | 0.33 | 0.34 | 0.33 | 0.91 | – | – | – | 7097 | 385 | 41.3 → 63.2 | yes | 465.7 / 34.6 / 12.9 | 546 / 1559 / 502 |
| cf_F6_6.1_pressurization_of_the_2in_line | 1 | 2026-11-06 11:41 | 84 | 45 | 23 / 0 / 0 | 0 | 15,124 | 0.80 | 0.97 | 0.80 | 1.00 | – | – | – | 3049 | 71 | 40.5 → 51.7 | yes | 73.7 / 0.1 / 3.1 | 527 / 1476 / 505 |

Board resources (on-board sampler, once a second, per episode): CPU seconds and peak memory of each model server. The NPU has no readable usage counter; its work shows as the NPU lane's call time. Supply power, if the board exposes it, is in each summary's `meta.resources`; energy is never estimated.
