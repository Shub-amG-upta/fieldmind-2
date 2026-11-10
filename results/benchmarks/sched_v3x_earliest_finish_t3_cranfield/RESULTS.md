# Benchmark `sched_v3x_earliest_finish_t3_cranfield`

Architecture **multi**, mode **realtime** (tick 3.0 s), overlay `configs/v3.yaml,configs/cranfield.yaml,configs/bev_ideas.yaml,configs/laya_board.yaml,configs/sched_study.yaml`, merge rule `hybrid`, models npu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, cpu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, bev: `laya-7b928d8-Q8_0.gguf`. Agent code ran on the laptop and only model calls on the board, so tick times are laptop times. Energy not measured. Plant data: REAL rig data (Cranfield three-phase flow facility, Ruiz-Carcel et al. 2015).

bev ideas switches: `explain=on,clear_skip=on`. Laya on llama-server on npu. bev idea calls: answered by Laya on llama-server (failed = no answer, which makes the run invalid and is not kept; rejected = refused by the gate's check). used = an answer that changed what the agent did; shadow = asked and only logged. Decode tokens per tick: answer tokens written by every model per tick (bev writes none).

Group top-1 is the share of scored ticks (fault onset onward) whose published rank-1 cause is in the true case's look-alike group; belief group top-1 is the same for the code-only ranking. A held-out true case has no exact top-1. Unusable = a model answer that was not used (wrong format, failed call, rejected note reading). Settings and every run, stopped ones included: `test.json`.

| episode | run | finished | ticks | model calls | bev idea calls / failed / rejected | bev used / shadow | decode tokens per tick | unusable | tokens in | group top-1 | belief group top-1 | exact top-1 | faithfulness | actions P / R | lead time min | false alarms /h | tick p95 ms | wall s | chip C | server CPU s npu / cpu / bev | peak RSS MB npu / cpu / bev |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cf_F5_5.1_slugging_conditions | 1 | 2026-11-11 02:35 | 75 | 221 | 112 / 0 / 0 | 111 / 0 | 12.08 | 0 | 60,022 | 0.34 | 0.34 | 0.34 | 0.91 | – | – | – | 97 | 231 | 43.2 → 63.7 | 107.2 / 638.8 / 38.7 | 532 / 4418 / 223 |

## bev ideas per episode

| episode | run | idea | calls | failed | rejected | used | shadow | other counters |
|---|---|---|---|---|---|---|---|---|
| cf_F5_5.1_slugging_conditions | 1 | clear_skip | 0 | 0 | 0 | 2 | 0 | – |
| cf_F5_5.1_slugging_conditions | 1 | explain | 112 | 0 | 0 | 109 | 0 | over_limit 0 |

Board resources (on-board sampler, once a second, per episode): CPU seconds and peak memory of each model server. The NPU has no readable usage counter; its work shows as the NPU lane's call time. Supply power, if the board exposes it, is in each summary's `meta.resources`; energy is never estimated.
