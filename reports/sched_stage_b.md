# Scheduling study, Stage B: the agent on the phone — report

## Status
PARTIAL — the bundle (CPython 3.14.10 for Android, a 3-line launcher built with NDK r29, the agent,
vendored PyYAML, the study's episodes) is built and checked on the laptop; nothing has run on the board
yet (no board attached to this laptop). Board steps: HANDOFF_SCHED.md step 1.

## What was built
| piece | file |
|---|---|
| launcher (`Py_BytesMain`) | `device/agent/launcher.c` |
| launcher build, bundle, push + sha256, run, identity, hard path | `bench/device_agent.py` |
| chip temperature without adb (on the board) | `bench/board.py` `chip_temperature` (`FIELDMIND_ON_DEVICE`) |
| tests | `tests/test_device_agent.py` |

Python: `python-3.14.10-aarch64-linux-android.tar.gz` from python.org, sha256
`423c80b9…e569b` (pinned in `bench/device_agent.py`), minimum Android API 24 (the release's
`android-env.sh`). The release has no executable; the launcher was compiled in
`ghcr.io/snapdragon-toolchain/arm64-android:v0.7` (the image of the board's llama.cpp build; NDK r29,
`aarch64-linux-android24-clang`): ELF aarch64 PIE, interpreter `/system/bin/linker64`, NEEDED
`libpython3.14.so`, `libdl.so`, `libc.so`; sha256 `3197115a…76e6be`.

Bundle: 777 files, 40.4 MB (python 38 MB, app 2.1 MB). The agent needs nothing outside the stdlib but
PyYAML (checked: importing `run_demo`, `bench.harness`, `bench.evaluator` loads 46 project files and one
third-party package, `yaml`); PyYAML 6.0.3 is vendored as its 17 `.py` files (no libyaml, so the pure-Python
parser runs on the board).

## Verification
| step | result |
|---|---|
| ran the module | `launcher` built the binary (output above); `bundle` built 777 files / 40.4 MB |
| self-tests | `tests/test_device_agent.py` 4 passed |
| independent re-derivation | the agent's app folder run alone with `python -S -E` (no site-packages, no PYTHON* variables: stdlib + app/ only) against the normal laptop run on dev_B01, v3 + sched_study, mock: 170 of 170 ticks identical (timing removed). Second route: two normal laptop runs, 170 / 170 identical, so the identity check is not passing because it strips everything |
| mutation check | PyYAML not vendored → fixture fails (agent cannot start); `case_groups.py` left out of the bundle → fixture fails; identity strips `hypotheses` → `test_identity_sees_a_changed_answer…` fails; llama.cpp lib dropped from LD_LIBRARY_PATH → `test_the_board_command_carries_both_library_paths…` fails |

Laptop hard path (dev_B01, v3, mock, lockstep; **laptop timing, not board**): p50 18.2 ms, p95 23.5 ms,
max 30.6 ms, 0 of 170 ticks over 200 ms.

## Direction checks
None (no physical response involved).

## Constants introduced
| symbol | value | provenance | range | affects |
|---|---|---|---|---|
| PY_VERSION / PY_SHA256 | 3.14.10 / 423c80b9… | measured on download 2026-11-10 | — | which Python runs on the board |
| ANDROID_API | 24 | CITED: the release's `android-env.sh` default | — | launcher link target |
| TIMING_KEYS (identity) | clock fields: `*_ms`, `wall_clock_s`, `deadline_miss`, `p0_deadline_miss`, `start_s`, `finish_s`, `tick_epoch_s`, `resources` | DESIGN: every field whose value is a clock reading or decided by one | — | what identity ignores |

## Numbers that changed
None (new stage).

## Decisions taken
1. **The study runs the agent on the laptop**, as every earlier board run (lanes over `adb forward`); the agent
   on the phone is validated separately (identity, hard path). Driving the benchmark runner from the board
   (its own lane restarts, temperature logging and result files) is not built. Conservative: changes less;
   the plan's "agent on the device" for the study is a later step.
2. **No CPU pinning by default.** `--cpu-mask` exists (`taskset`); which core to reserve needs the board's
   core layout (HANDOFF step 1 reads it) and the CPU lane's thread count (`bench.board` starts it with 6
   threads). Both hard-path runs (unpinned, cpu7) are in the handoff.
3. **Launcher built in the snapdragon toolchain image**, as planned. Docker Desktop was started on this Mac to
   do it.
4. **Stdlib folders left out of the bundle**: `test`, `idlelib`, `tkinter`, `turtledemo`, `ensurepip`,
   `pydoc_data` (size only; the agent imports none of them — the `-S -E` run proves the app needs nothing
   else, but on the laptop's own stdlib, see "could not verify").

## Disagreements recorded, not resolved
None.

## Blocked / needs a decision
- Board steps not run: no board attached here. HANDOFF_SCHED.md step 1.

## What I could not verify
- That the launcher starts on the board, and that the Android standard library has every module the agent
  imports (the `-S -E` test used the laptop's CPython 3.13 stdlib, not the Android 3.14 one). First board
  check: `identity`.
- python.org's sigstore signature of the tarball (only its sha256 is pinned, as measured).
- Whether the launcher build is reproducible (built once).
- Hard-path time on the board, pinned or not.
