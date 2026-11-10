# Benchmark `sched_v3_lockstep_boiler`

Architecture **multi**, mode **lockstep**, overlay `configs/v3.yaml,configs/sched_study.yaml`, merge rule `hybrid`, models npu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, cpu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`. Agent code ran on the laptop and only model calls on the board, so tick times are laptop times. Energy not measured. All plant data is synthetic.

Group top-1 is the share of scored ticks (fault onset onward) whose published rank-1 cause is in the true case's look-alike group; belief group top-1 is the same for the code-only ranking. A held-out true case has no exact top-1. Unusable = a model answer that was not used (wrong format, failed call, rejected note reading). Settings and every run, stopped ones included: `test.json`.

| episode | run | finished | ticks | model calls | unusable | tokens in | group top-1 | belief group top-1 | exact top-1 | faithfulness | actions P / R | lead time min | false alarms /h | tick p95 ms | wall s | chip C | server CPU s npu / cpu / bev | peak RSS MB npu / cpu / bev |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dev_A02_fcv_seize_fast | 1 | 2026-11-10 21:35 | 80 | 51 | 0 | 30,889 | 0.62 | 0.47 | 0.02 | 1.00 | 0.29 / 1.00 | -9.3 | – | 8819 | 186 | 51.7 → 62.1 | 169.2 / 384.6 / – | 535 / 4419 / – |
| dev_B01_tube_leak | 1 | 2026-11-10 21:31 | 170 | 65 | 0 | 46,429 | 0.95 | 0.47 | 0.95 | 1.00 | 0.57 / 1.00 | – | – | 3200 | 208 | 46.7 → 60.6 | 229.4 / 207.2 / – | 541 / 4408 / – |

Board resources (on-board sampler, once a second, per episode): CPU seconds and peak memory of each model server. The NPU has no readable usage counter; its work shows as the NPU lane's call time. Supply power, if the board exposes it, is in each summary's `meta.resources`; energy is never estimated.
