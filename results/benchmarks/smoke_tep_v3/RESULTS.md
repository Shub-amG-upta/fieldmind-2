# Benchmark `smoke_tep_v3`

Architecture **multi**, mode **lockstep**, overlay `configs/v3.yaml,configs/tep.yaml`, merge rule `hybrid`, models npu: `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, cpu: `gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf`. Agent code ran on the laptop and only model calls on the board, so tick times are laptop times. Energy not measured. Plant data: simulated (Tennessee Eastman Process, Rieth et al. 2017).

Group top-1 is the share of scored ticks (fault onset onward) whose published rank-1 cause is in the true case's look-alike group; belief group top-1 is the same for the code-only ranking. A held-out true case has no exact top-1. Unusable = a model answer that was not used (wrong format, failed call, rejected note reading). Settings and every run, stopped ones included: `test.json`.

| episode | run | finished | ticks | model calls | unusable | tokens in | group top-1 | belief group top-1 | exact top-1 | faithfulness | actions P / R | lead time min | false alarms /h | tick p95 ms | wall s | chip C | server CPU s npu / cpu / bev | peak RSS MB npu / cpu / bev | °C cpu start → peak | °C npu start → peak | board memory MB peak / total | RSS growth MB npu / cpu / bev | ticks with own sample | sample period s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tep_board_F08_r1 | 1 | 2026-11-07 16:20 | 319 | 341 | 0 | 284,245 | 0.17 | 0.38 | 0.17 | 0.97 | – | – | – | 8032 | 1106 | 34.7 → 57.9 | 1702.8 / 376.2 / – | 591 / 1579 / – | 38.6 → 96.9 | 37.4 → 97.3 | 6098 / 11361 | +97 / +87 / – | 181 / 319 | 1.20 |
| tep_board_N_r1 | 1 | 2026-11-07 16:27 | 319 | 115 | 0 | 49,930 | – | – | – | 1.00 | – | – | 6.27 | 2662 | 216 | 38.6 → 56.7 | 357.3 / 25.6 / – | 547 / 1546 / – | 41.3 → 95.0 | 40.5 → 96.5 | 6007 / 11361 | +49 / +53 / – | 99 / 319 | 1.19 |

Board resources (on-board sampler, per episode): CPU seconds and peak memory of each model server. The NPU has no readable usage counter; its work shows as the NPU lane's call time. Supply power, if the board exposes it, is in each summary's `meta.resources`; energy is never estimated.

Per tick (`<stem>.tick_resources.jsonl`, bench/board_resources.py): the hottest CPU and NPU zone in each tick's window, board memory in use (MemTotal - MemAvailable, board-wide, so it should also count the NPU lane's DMA buffers, which its RSS misses; not yet checked against dmabuf_dump) and each lane's RSS. °C columns: first tick → hottest tick. RSS growth: last tick - first tick. A tick shorter than the sample period has no sample of its own and shows the last earlier one. – = not recorded (runs before per-tick resources, or no board).
