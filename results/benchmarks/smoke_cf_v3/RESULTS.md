# Benchmark `smoke_cf_v3`

Architecture **multi**, mode **lockstep**, overlay `configs/v3.yaml,configs/cranfield.yaml`, merge rule `hybrid`, models npu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, cpu: `gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf`. Agent code ran on the laptop and only model calls on the board, so tick times are laptop times. Energy not measured. Plant data: REAL rig data (Cranfield three-phase flow facility, Ruiz-Carcel et al. 2015).

Group top-1 is the share of scored ticks (fault onset onward) whose published rank-1 cause is in the true case's look-alike group; belief group top-1 is the same for the code-only ranking. A held-out true case has no exact top-1. Unusable = a model answer that was not used (wrong format, failed call, rejected note reading). Settings and every run, stopped ones included: `test.json`.

| episode | run | finished | ticks | model calls | unusable | tokens in | group top-1 | belief group top-1 | exact top-1 | faithfulness | actions P / R | lead time min | false alarms /h | tick p95 ms | wall s | chip C | server CPU s npu / cpu / bev | peak RSS MB npu / cpu / bev | °C cpu start → peak | °C npu start → peak | board memory MB peak / total | RSS growth MB npu / cpu / bev | ticks with own sample | sample period s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cf_F5_5.1_slugging_conditions | 1 | 2026-11-07 15:27 | 75 | 120 | 0 | 71,946 | 0.33 | 0.34 | 0.33 | 0.91 | – | – | – | 5850 | 308 | 33.2 → 56.0 | 518.9 / 32.6 / – | 552 / 1565 / – | 92.3 → 95.8 | 75.7 → 96.1 | 6012 / 11361 | +27 / -7 / – | 74 / 75 | 1.20 |

Board resources (on-board sampler, per episode): CPU seconds and peak memory of each model server. The NPU has no readable usage counter; its work shows as the NPU lane's call time. Supply power, if the board exposes it, is in each summary's `meta.resources`; energy is never estimated.

Per tick (`<stem>.tick_resources.jsonl`, bench/board_resources.py): the hottest CPU and NPU zone in each tick's window, board memory in use (MemTotal - MemAvailable, board-wide, so it should also count the NPU lane's DMA buffers, which its RSS misses; not yet checked against dmabuf_dump) and each lane's RSS. °C columns: first tick → hottest tick. RSS growth: last tick - first tick. A tick shorter than the sample period has no sample of its own and shows the last earlier one. – = not recorded (runs before per-tick resources, or no board).
