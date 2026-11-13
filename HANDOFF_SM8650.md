# SM8650 runs (for the Claude session on Gagan's Mac)

Written 2026-11-13 on Shubham's laptop. Branch `fe-baseline`. Order agreed by Shubham: **6, then 1, then 2.**
Item 3 (2 threads on this chip) is already done.

| # | run | rules | time |
|---|---|---|---|
| 6 | Speed check at our settings: 4-bit Llama 3B, NPU, 2 threads | measurement only | 10 min |
| 1 | 4-bit confirmation, NPU arms: 4-bit then 8-bit Llama 3B, 400 calls each | `reports/echo_4bit_prereg.md` **A3** (agreed) | ~1.5 h |
| 2 | FaultExplainer: 4-bit (F1r) then 8-bit (F2), 108 calls each | `reports/ext_faultexplainer_prereg.md` **A3** (agreed) | ~6 h |

All at `GGML_HEXAGON_NHVX=2`, cooled to the SM8650's idle + 5 °C before every arm and block. One driver runs all of it:
`results/run_sm8650_6_1_2.sh`. It reads no reply and no pick, and nothing is scored on your side.

## 1. Get the code
```
cd ~/projects/fieldmind-bc
git fetch mine fe-baseline && git merge FETCH_HEAD
env -u PYTHONPATH .venv/bin/python -m pytest -q tests/test_echo_4bit.py tests/test_ext_faultexplainer.py \
    tests/test_ext_faultexplainer_baseline.py tests/test_nd_board_knobs.py tests/test_board_env.py   # expect all pass
```

## 2. Start it
Only the SM8650 should be attached, and nothing else should be using it.
```
adb devices                                   # note the SM8650 serial
BOARD_SERIAL=<serial> nohup caffeinate -dimsu zsh results/run_sm8650_6_1_2.sh > results/sm8650_6_1_2.out 2>&1 < /dev/null &
```
The driver, in order:
1. checks `ro.soc.model` is SM8650, stops any lane, pushes the 8-bit 3B if missing (sha256 must be `d91f61ab…`);
2. waits 2 minutes, reads the idle temperature and sets the cooling target to idle + 5 °C;
3. item 6, then item 1 (with A2's rerun rule: more than 20 failed of 400 → file moved aside, one rerun), then item 2;
4. stops on any failed check: not an SM8650, wrong sha256, a lane log without `threads 2`, two failed tries.

Progress: `results/sm8650_runlog.txt`. Keep the Mac on its charger.

## 3. Hand back
```
git add -f results/sm8650_runlog.txt results/sm8650_6_1_2.out results/sm8650_lane_*.txt results/sm8650_speed_q4.json \
           results/echo/h_prior_npu8650_*.jsonl results/ext/faultexplainer_F1r_sm8650.jsonl results/ext/faultexplainer_F2_sm8650.jsonl
git commit -m "SM8650 runs 6, 1, 2 at NHVX=2 (speed, 4-bit confirmation NPU arms, FaultExplainer F1r and F2); not scored"
```
Push `bc-runs` and tell Shubham. Do not run `score`, and do not rerun or drop anything after looking at results. If
the driver stopped, say where and paste the last lines of the run log.
