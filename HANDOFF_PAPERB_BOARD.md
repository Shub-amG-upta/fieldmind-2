# Paper B: what to run on the board, and in what order

Written 2026-11-12. Every command comes from one place:

    .venv/bin/python bench/paperB_board.py check        # every overlay, episode and request file exists
    .venv/bin/python bench/paperB_board.py plan         # all commands; --item 1|2|6|7|8 for one item

**Before anything:**
- agree the PROPOSED items in each pre-registration and date them under "Agreed";
- lanes up with `/board-up`, using the sweep's file (`Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`);
- chip temperature before and after every run, with cooling gaps;
- laptop time only.

| order | item | what | pre-registration | board time (estimate) |
|---|---|---|---|---|
| 1 | 8 | NPU reading speed with arXiv 2605.27435's settings (`-b 128 -ub 128 -fa off`), then restore the lane | `reports/paperB_prep.md` | 30 min |
| 2 | 6 | `calibrated_finish` on the sweep's cells (sched fix part D) | `reports/sched_fix.md` (pass rule PROPOSED) | 3–4 h |
| 3 | 1 | FaultExplainer, arm F1, on the NPU lane (108 calls; answers up to 1,400 tokens) | `reports/ext_faultexplainer_prereg.md` | 1.5–2.6 h |
| 4 | 2 | the published fixes: no example, no letters, calibrate, PriDe, PSC (lockstep) | `reports/paperB_item2_prereg.md` | about 2 nights |
| 5 | 7 | the capacity-setting cells on more episodes, 3 repeats | `bench/paperB_board.py` (PROPOSED) | about 2–3 nights |
| any | 4 | energy: needs a logging meter on the board's DC input; then `bench/energy.py idle` and `bench/energy.py runs` | `PLAN_PAPER_B.md` item 4 | 2 min idle + the runs above |

**New since the sweep:**
- `bench/benchmark.py` records each run's process window (`child_t0_unix`, `child_t1_unix`) for the meter;
- the sampler records its laptop start time;
- the runner accepts `--placement calibrated_finish`. Before this it did not, and item 6 would have failed at start-up.

**After each item:** score it with the tools named in its pre-registration:
- `bench/echo_test.py saved` and `changed`;
- `bench/ext_faultexplainer.py score`;
- `bench/sched_study.py table`;
- `bench/sched_replay.py`.

Commit the results with the item name. Do not push.
