# Benchmark `sched_v3_earliest_finish_t2_boiler`

Architecture **multi**, mode **realtime** (tick 2.0 s), overlay `configs/v3.yaml,configs/sched_study.yaml`, merge rule `hybrid`, models npu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, cpu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`. Agent code ran on the laptop and only model calls on the board, so tick times are laptop times. Energy not measured. All plant data is synthetic.

Group top-1 is the share of scored ticks (fault onset onward) whose published rank-1 cause is in the true case's look-alike group; belief group top-1 is the same for the code-only ranking. A held-out true case has no exact top-1. Unusable = a model answer that was not used (wrong format, failed call, rejected note reading). Settings and every run, stopped ones included: `test.json`.

| episode | run | finished | ticks | model calls | unusable | tokens in | group top-1 | belief group top-1 | exact top-1 | faithfulness | actions P / R | lead time min | false alarms /h | tick p95 ms | wall s | chip C | server CPU s npu / cpu / bev | peak RSS MB npu / cpu / bev |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dev_A02_fcv_seize_fast | 1 | 2026-11-11 02:57 | 80 | 37 | 0 | 23,637 | 0.78 | 0.47 | 0.00 | 1.00 | 0.23 / 0.75 | – | – | 52 | 168 | 53.9 → 57.9 | 160.3 / 62.1 / – | 525 / 4417 / – |
| dev_B01_tube_leak | 1 | 2026-11-11 02:54 | 170 | 55 | 0 | 40,883 | 0.80 | 0.47 | 0.80 | 1.00 | 0.44 / 1.00 | – | – | 47 | 347 | 54.4 → 56.7 | 211.7 / 113.7 / – | 530 / 4418 / – |

Board resources (on-board sampler, once a second, per episode): CPU seconds and peak memory of each model server. The NPU has no readable usage counter; its work shows as the NPU lane's call time. Supply power, if the board exposes it, is in each summary's `meta.resources`; energy is never estimated.
