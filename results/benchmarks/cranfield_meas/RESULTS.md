# Benchmark `cranfield_meas`

Architecture **multi**, mode **lockstep**, overlay `configs/v3.yaml,configs/cranfield.yaml`, merge rule `hybrid`, models npu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, cpu: `gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf`. Agent code ran on the laptop and only model calls on the board, so tick times are laptop times. Energy not measured. Data: real Cranfield rig recordings, not synthetic.

Group top-1 is the share of scored ticks (fault onset onward) whose published rank-1 cause is in the true case's look-alike group; belief group top-1 is the same for the code-only ranking. A held-out true case has no exact top-1. Unusable = a model answer that was not used (wrong format, failed call, rejected note reading). Settings and every run, stopped ones included: `test.json`.

| episode | run | finished | ticks | model calls | unusable | tokens in | group top-1 | belief group top-1 | exact top-1 | faithfulness | actions P / R | lead time min | false alarms /h | tick p95 ms | wall s | chip C | server CPU s npu / cpu / bev | peak RSS MB npu / cpu / bev |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cf_F5_5.1_slugging_conditions | 1 | 2026-11-06 01:48 | 75 | 120 | 0 | 71,946 | 0.33 | 0.34 | 0.33 | 0.91 | – | – | – | 6826 | 332 | 34.5 → 62.1 | 473.1 / 33.1 / – | 546 / 1561 / – |
| cf_F6_6.1_pressurization_of_the_2in_line | 1 | 2026-11-06 01:53 | 84 | 22 | 0 | 10,560 | 0.80 | 0.97 | 0.80 | 1.00 | – | – | – | 2464 | 56 | 39.1 → 52.5 | 74.7 / 0.1 / – | 525 / 1475 / – |

Board resources (on-board sampler, once a second, per episode): CPU seconds and peak memory of each model server. The NPU has no readable usage counter; its work shows as the NPU lane's call time. Supply power, if the board exposes it, is in each summary's `meta.resources`; energy is never estimated.
