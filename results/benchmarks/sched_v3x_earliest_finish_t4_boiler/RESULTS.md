# Benchmark `sched_v3x_earliest_finish_t4_boiler`

Architecture **multi**, mode **realtime** (tick 4.0 s), overlay `configs/v3.yaml,configs/bev_ideas.yaml,configs/laya_board.yaml,configs/sched_study.yaml`, merge rule `hybrid`, models npu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, cpu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, bev: `laya-7b928d8-Q8_0.gguf`. Agent code ran on the laptop and only model calls on the board, so tick times are laptop times. Energy not measured. All plant data is synthetic.

bev ideas switches: `explain=on,clear_skip=on`. Laya on llama-server on npu. bev idea calls: answered by Laya on llama-server (failed = no answer, which makes the run invalid and is not kept; rejected = refused by the gate's check). used = an answer that changed what the agent did; shadow = asked and only logged. Decode tokens per tick: answer tokens written by every model per tick (bev writes none).

Group top-1 is the share of scored ticks (fault onset onward) whose published rank-1 cause is in the true case's look-alike group; belief group top-1 is the same for the code-only ranking. A held-out true case has no exact top-1. Unusable = a model answer that was not used (wrong format, failed call, rejected note reading). Settings and every run, stopped ones included: `test.json`.

| episode | run | finished | ticks | model calls | bev idea calls / failed / rejected | bev used / shadow | decode tokens per tick | unusable | tokens in | group top-1 | belief group top-1 | exact top-1 | faithfulness | actions P / R | lead time min | false alarms /h | tick p95 ms | wall s | chip C | server CPU s npu / cpu / bev | peak RSS MB npu / cpu / bev |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dev_A02_fcv_seize_fast | 1 | 2026-11-11 01:18 | 80 | 80 | 37 / 0 / 0 | 39 / 0 | 5.85 | 0 | 24,805 | 0.67 | 0.47 | 0.02 | 1.00 | 0.23 / 0.75 | -9.8 | – | 55 | 324 | 40.3 → 43.6 | 57.4 / 25.7 / 14.0 | 521 / 4399 / 188 |
| dev_B01_tube_leak | 1 | 2026-11-11 01:12 | 170 | 111 | 55 / 0 / 0 | 58 / 0 | 2.96 | 0 | 38,471 | 0.92 | 0.47 | 0.92 | 1.00 | 0.50 / 1.00 | – | – | 52 | 684 | 50.5 → 41.8 | 64.4 / 54.9 / 15.1 | 521 / 4402 / 157 |

## bev ideas per episode

| episode | run | idea | calls | failed | rejected | used | shadow | other counters |
|---|---|---|---|---|---|---|---|---|
| dev_A02_fcv_seize_fast | 1 | clear_skip | 0 | 0 | 0 | 3 | 0 | – |
| dev_A02_fcv_seize_fast | 1 | explain | 37 | 0 | 0 | 36 | 0 | over_limit 0 |
| dev_B01_tube_leak | 1 | clear_skip | 0 | 0 | 0 | 4 | 0 | – |
| dev_B01_tube_leak | 1 | explain | 55 | 0 | 0 | 54 | 0 | over_limit 0 |

Board resources (on-board sampler, once a second, per episode): CPU seconds and peak memory of each model server. The NPU has no readable usage counter; its work shows as the NPU lane's call time. Supply power, if the board exposes it, is in each summary's `meta.resources`; energy is never estimated.
