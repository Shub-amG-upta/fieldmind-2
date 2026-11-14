# Handoff: test the TA's energy method on the SM8750 (for whichever laptop has the board)

Written 2026-11-14. Branch `fe-baseline` (it now contains `bc-build`'s `bench/power_probe.py`, 13 tests passing).

## What is tested
The TA's method (Phase Matters, MobiSys Workshop '26, §2.3): read the board's fuel gauge,
`/sys/class/power_supply/battery/current_now × voltage_now`, every 100 ms, and integrate. The question is only whether
that reading **follows the board's load** on this SM8750 (`1d9c8f40`). If it does not, it cannot give energy.

`bench/power_probe.py` runs **30 s idle → 30 s with every CPU core spinning → 30 s idle**, logs the gauge every 100 ms on
the board, and prints a verdict by rules fixed in the file before any SM8750 run:

| verdict | meaning |
|---|---|
| PASS | the reading rises by ≥ 0.5 W under load, ≥ 5 robust SDs above idle noise, and comes back |
| FAIL | the load ran and the step is below 0.5 W: the gauge does not see the board's draw |
| UNCLEAR | a large step but noisy, not coming back, or the units look wrong |
| INVALID | the load did not run (CPU busy < 0.90) or too few samples |
| DENIED | the gauge files cannot be read (rerun with `--root`) |

**Prior evidence, stated before running:**
- the old SM8650: FAIL with root (+0.0085 W step under all cores; the gauge updates about every 2 s);
- the SM8750 on 2026-11-13, sampled at 1 Hz during an NPU run and after it: battery current mean −2,394 under load and
  −2,506 idle (4,803 samples), no difference; the board reports its battery as `Debug_Board`.
So **FAIL is expected.** A PASS would contradict both and should be repeated once before anyone uses it.

## Steps
```
cd <repo>/.worktrees/fe-baseline            # or: git fetch mine fe-baseline && git merge FETCH_HEAD
export ANDROID_SERIAL=1d9c8f40
adb shell getprop ro.soc.model               # must print SM8750P
adb shell pidof llama-server                 # must print nothing (no lane running)
env -u PYTHONPATH .venv/bin/python -m pytest -q tests/test_power_probe.py      # expect 13 passed
env -u PYTHONPATH .venv/bin/python -m bench.power_probe --root
```
- About 2 minutes. It writes `results/power_probe/<time>/` (samples, markers, `probe.json`) and prints the verdict and
  the raw step in watts.
- If it prints **DENIED** without `--root`, use `--root` (it unroots afterwards).
- If **PASS**: run it a second time, after 5 minutes of idle, before anyone treats the gauge as usable.
- Log the chip temperature before and after (`python -m bench.board temp`).

## Hand back
```
git add -f results/power_probe/
git commit -m "power probe on the SM8750 (TA's fuel-gauge method): <verdict>, step <x> W"
```
Push and tell Shubham. **No energy number comes from this probe**, whatever the verdict: a PASS only means a separate,
pre-registered energy rule can be written for this gauge.
