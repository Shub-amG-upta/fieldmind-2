# Power probe (does the fuel gauge see the board's draw?) — report

## Status
DONE (tool). `bench/power_probe.py` runs the TA's fuel-gauge method (*Phase Matters*, MobiSys Workshop '26, §2.3:
"fuel-gauge I×V at 100 ms granularity") through a known load step and prints one verdict. **Run on the old SM8650
only** (the board attached to this laptop): **FAIL**. **Not yet run on the SM8750**, the board every new run uses.
No energy number exists or is implied.

| piece | file |
|---|---|
| tool | `bench/power_probe.py` (`python -m bench.power_probe [--root]`, `analyse <dir>`) |
| tests | `tests/test_power_probe.py` (13) |
| real runs, SM8650 `ab8f6592` | `results/power_probe/20261114_003022` (no root), `…_003033` (root, script bug), `…_003550` (root, valid) |

**What it does:** 30 s idle → 30 s with every CPU core spinning → 30 s idle.
- It reads `current_now` and `voltage_now` every 100 ms (the TA's loop), with `/proc/uptime` as the clock.
- It checks from `/proc/stat` that the load really ran.
- It records the chip temperature before and after.
- With `--root` it runs `adb root` for the probe only and `adb unroot` afterwards, even on failure.

## Verification
| step | result |
|---|---|
| ran the module | **SM8650, no root:** `DENIED` ("cat: /sys/class/power_supply/battery/current_now: Permission denied"), as `reports/bev_measurement.md` found. **SM8650, `--root`, valid run (`…_003550`):** 495 samples, 0 malformed; CPU busy 0.9996 during the load, 0.044 before; gauge idle −5,127 → load −4,760 → idle −6,225 (raw µA) at 9.05 V; step **+0.0085 W**, idle noise 0.0098 W; gauge updates about every 2 s; verdict **FAIL**. Root undone (`id -u` 2000), no probe process left. Chip 32.8 → 38.7 °C |
| self-tests | 13 passed. The two local end-to-end tests run the real board script under `sh` against a fake sysfs; 20 consecutive passes after the fix below |
| independent re-derivation | step on `…_003550` from the raw CSVs with `awk`, **phase means** (the tool uses phase medians): +0.00807 W against the tool's +0.00847 W, a 5% difference, both about 60× below the 0.5 W floor |
| mutation check | 4 of 4 caught: µA·µV→W factor 1e-12 → 1e-9 (`test_the_old_sm8650_flat_reading_fails` and 2 more); the "comes back" check removed (`test_a_reading_that_does_not_come_back_is_unclear`); the readable check forced true (`test_unreadable_nodes_stop_before_anything_is_pushed_or_run`); `MIN_BUSY` 0.90 → 0 (`test_a_load_that_did_not_run_is_invalid_even_if_the_reading_steps`) |

## Direction checks
| claim | expected | measured | |
|---|---|---|---|
| a gauge that sees the draw rises under load (discharging) | step up, PASS | synthetic +3.0 W PASS; local script +2.0 W PASS | OK |
| a charging gauge's current falls under load | step down, still PASS | synthetic PASS, direction "down" | OK |
| the load raises CPU busy | up | SM8650 0.044 → 0.9996 | OK |
| the SM8650 gauge follows the load | – (no direction stated; the question) | +0.0085 W against 0.5 W floor | FAIL (the finding) |

## Constants introduced
| symbol | value | provenance | range | affects |
|---|---|---|---|---|
| `UA_UV_TO_W` | 1e-12 | CITED: Linux `Documentation/ABI/testing/sysfs-class-power` (current_now µA, voltage_now µV) | – | watts |
| `IDLE_S`, `LOAD_S` | 30 s, 30 s | DESIGN | 15–60 | samples per phase |
| `SETTLE_S` | 2 s | DESIGN | 1–5 | samples dropped after each phase change |
| `MIN_SAMPLES` | 20 per phase | DESIGN | 10–50 | INVALID |
| `MIN_BUSY` | 0.90 | DESIGN | 0.80–0.95 | INVALID |
| `FLOOR_W` | 0.5 W | DESIGN. Basis: an expectation, **not a citation**, that all cores spinning on a phone SoC draw well over 1 W above idle; and the one known flat case (about 2 mW, SM8650) | 0.2–1.0 W | PASS / FAIL. The raw step is always printed |
| `K_NOISE` | 5 | DESIGN | 3–10 | UNCLEAR |
| `RETURN_SHARE` | 0.5 | DESIGN | 0.3–0.7 | UNCLEAR |
| `VOLT_RANGE` | 2.5–15 V | DESIGN | – | UNCLEAR when units look wrong |

## Numbers that changed
None. No agent code, config, threshold or episode was touched.

## Disagreements recorded, not resolved
1. **The TA reports a load-dependent fuel-gauge energy on a QIDK SM8750; on the SM8650 QIDK the same reading does not
   follow load.**
   - TA: 2.52× NPU against CPU energy, while his time ratio is 1.64× (warm, Table 4).
   - Ours: +0.0085 W for a full 8-core step, root, sysfs.
   - Different chip and board, so this does not contradict him. **Unexplained** until the SM8750 is probed.
2. **The SM8650 gauge reports discharge (about −5 mA) at 100% charge, 9.05 V, with "AC powered: false, USB powered:
   false".** It looks like a board fed outside the battery path. That is a reading of `dumpsys battery`, **not
   tested**.

## Bugs found and fixed while building
1. **On the board, `kill $PIDS` took down the whole probe** (first rooted run, `…_003033`: the logger and the script
   stopped at `load_end`, with "Terminated" and no "probe-done").
   - On the board's `/system/bin/sh`, a redirected `( … ) &` is two nested processes, and `$!` names the outer one.
   - Seen directly: `$!` = 11538, a `sh` whose child 11540 ran the loop. After `kill 11538`, both were still alive.
   - **The full-script kill itself is unexplained.**
   - The script now uses no `kill`: the loops stop on stop files, then `wait`. Valid run `…_003550` followed.
   - The local `sh` does not reproduce this, so the end-to-end tests could not have caught it. Only the board run did.
2. **The fake board in the tests failed about 1 run in 7** with INVALID: it rewrote its fake `/proc/stat` in place,
   and the script sometimes read a half-written file. Fake writes are now atomic: 20 of 20 passes after. This was a
   test-harness artefact; the real runs had 0 malformed lines.

## Blocked / needs a decision
1. **Run it on the SM8750** (`HANDOFF_4BIT.md`, step Q0). Until then the TA's method is untested on our board, and
   energy stays `null`.
2. **`adb root` on the SM8750** restarts adbd and drops the lane port forwards. Run it only with no lane up (Q0 says
   so). Whether the SM8750 build allows `adb root` is unknown.

## What I could not verify
- **That a PASS on the SM8750 means usable energy numbers.** It would show only that the gauge follows a CPU step.
  Still open: whether it covers the NPU's rail, its 2 s update period against calls of 3–4 s, and idle subtraction.
  Those need their own rules before any energy run.
- **Why the TA's QIDK differs, if it does.** That needs his board's `dumpsys battery` and probe output.
- **The 0.5 W floor's basis is an expectation,** not a measured or cited SoC power. The raw step is printed for that
  reason.
