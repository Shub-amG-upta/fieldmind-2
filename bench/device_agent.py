#!/usr/bin/env python3
"""
=============================================================================
 THE AGENT ON THE PHONE  --  bundle, push, run and check the whole agent on
 the QIDK (plan Phase 4; reports/sched_stage_b.md, HANDOFF_SCHED.md)
=============================================================================

    .venv/bin/python -m bench.device_agent launcher      build the launcher (docker)
    .venv/bin/python -m bench.device_agent bundle        assemble results/device_bundle/
    .venv/bin/python -m bench.device_agent push          adb push + sha256 of every file
    .venv/bin/python -m bench.device_agent run -- <run_demo.py args>
    .venv/bin/python -m bench.device_agent identity      mock on the board == mock here
    .venv/bin/python -m bench.device_agent hardpath      hard-path timings on the board

Python on the board is the official CPython Android release (embeddable:
libpython and the standard library, no executable) and a three-line launcher
(device/agent/launcher.c) that calls Py_BytesMain, compiled with the NDK of
the toolchain image the board's llama.cpp was built in. The agent core is
stdlib-only; PyYAML is vendored as its pure-Python files (no libyaml).

Board layout (BOARD_ROOT):
  bin/fieldmind-python       the launcher
  python/lib/                libpython3.14.so and its libraries
  python/lib/python3.14/     the standard library (PYTHONHOME = python/)
  app/                       run_demo.py, fieldmind/, bench/ (the five modules
                             run_demo imports), configs/, data/kb*, the episodes,
                             yaml/ (vendored)
  MANIFEST.json              path -> sha256 of every file above

Every run sets LD_LIBRARY_PATH (python/lib, then the llama.cpp lib folder, as
every adb shell that starts a binary must) and ADSP_LIBRARY_PATH, and
FIELDMIND_ON_DEVICE=1 (chip temperature read locally, bench.board). The board
clock is wrong: times are logged from the laptop around each run.
=============================================================================
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
from pathlib import Path

from bench import board

ROOT = Path(__file__).resolve().parent.parent
BUNDLE = ROOT / "results" / "device_bundle"
STAGE = BUNDLE / "stage"
CACHE = BUNDLE / "cache"
BOARD_ROOT = "/data/local/tmp/fieldmind"

PY_VERSION = "3.14.10"
PY_TARBALL = f"python-{PY_VERSION}-aarch64-linux-android.tar.gz"
PY_URL = f"https://www.python.org/ftp/python/{PY_VERSION}/{PY_TARBALL}"
# Measured on download (2026-11-10). python.org signs the release with sigstore;
# that signature was not checked here (reports/sched_stage_b.md).
PY_SHA256 = "423c80b957330cf0ebb92b9b20f2294c292144a441bdb0ceb8c69d14928e569b"
# The release's minimum Android API level (its android-env.sh default).
ANDROID_API = 24
TOOLCHAIN_IMAGE = "ghcr.io/snapdragon-toolchain/arm64-android:v0.7"

# What run_demo.py imports from bench/ (checked by tests/test_device_agent.py).
BENCH_MODULES = ("__init__.py", "board.py", "case_groups.py", "evaluator.py", "harness.py")
APP_FILES = ("run_demo.py",)
APP_DIRS = ("fieldmind", "configs", "data/kb", "data/kb_cranfield", "data/kb_tep")
# The study's episodes (bench/sched_study.py) and nothing else.
EPISODE_DIRS = ("data/episodes_dev/dev_B01_tube_leak",
                "data/episodes_dev/dev_A02_fcv_seize_fast",
                "data/episodes_cranfield_dev/cf_F5_5.1_slugging_conditions")
# Standard-library folders the agent never imports (size only).
STDLIB_SKIP = ("test", "idlelib", "tkinter", "turtledemo", "ensurepip", "__pycache__",
               "pydoc_data", "config-3.14-aarch64-linux-android")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _skip(rel: Path) -> bool:
    return any(part in ("__pycache__",) or part.endswith(".pyc") for part in rel.parts)


# ---------------------------------------------------------------- python + launcher
def python_tarball() -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    tb = CACHE / PY_TARBALL
    if not tb.exists():
        print(f"downloading {PY_URL}")
        with urllib.request.urlopen(PY_URL, timeout=300) as r, tb.open("wb") as f:
            shutil.copyfileobj(r, f)
    got = sha256(tb)
    if got != PY_SHA256:
        raise SystemExit(f"{tb.name}: sha256 {got} != pinned {PY_SHA256}")
    return tb


def build_launcher() -> Path:
    """Compile device/agent/launcher.c in the toolchain image against the
    release's libpython. Output: results/device_bundle/cache/fieldmind-python."""
    tb = python_tarball()
    prefix = CACHE / "prefix"
    if not (prefix / "lib" / "libpython3.14.so").exists():
        with tarfile.open(tb) as t:
            t.extractall(CACHE, members=[m for m in t.getmembers()
                                         if m.name.startswith("./prefix/lib/libpython")
                                         or m.name.startswith("./prefix/include/python3.14")],
                         filter="data")
    rel = CACHE.relative_to(ROOT)
    cc = (f"$ANDROID_NDK_ROOT/toolchains/llvm/prebuilt/linux-x86_64/bin/"
          f"aarch64-linux-android{ANDROID_API}-clang")
    script = (f"set -e; {cc} -O2 -o {rel}/fieldmind-python device/agent/launcher.c "
              f"-L{rel}/prefix/lib -lpython3.14 && "
              f"$ANDROID_NDK_ROOT/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf -d "
              f"{rel}/fieldmind-python | grep NEEDED")
    cmd = ["docker", "run", "--rm", "--platform", "linux/amd64", "-v", f"{ROOT}:/w", "-w", "/w",
           TOOLCHAIN_IMAGE, "bash", "-c", script]
    p = subprocess.run(cmd, capture_output=True, text=True)
    print(p.stdout + p.stderr)
    if p.returncode != 0:
        raise SystemExit("launcher build failed")
    out = CACHE / "fieldmind-python"
    print(f"{out.relative_to(ROOT)}  sha256 {sha256(out)}")
    return out


# ---------------------------------------------------------------- bundle
def bundle() -> dict:
    """Assemble STAGE from scratch and write its MANIFEST.json."""
    launcher = CACHE / "fieldmind-python"
    if not launcher.exists():
        raise SystemExit("no launcher: run `launcher` first")
    if STAGE.exists():
        shutil.rmtree(STAGE)
    (STAGE / "bin").mkdir(parents=True)
    shutil.copy2(launcher, STAGE / "bin" / "fieldmind-python")
    with tarfile.open(python_tarball()) as t:
        for m in t.getmembers():
            if not m.name.startswith("./prefix/lib/") or m.isdir():
                continue
            rel = Path(m.name[len("./prefix/"):])          # lib/...
            if "pkgconfig" in rel.parts or "engines-3" in rel.parts or "ossl-modules" in rel.parts:
                continue
            if len(rel.parts) > 2 and rel.parts[1] == "python3.14" and rel.parts[2] in STDLIB_SKIP:
                continue
            dst = STAGE / "python" / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            with t.extractfile(m) as src, dst.open("wb") as f:
                shutil.copyfileobj(src, f)
    import yaml
    stage_app(STAGE / "app")
    files = {str(p.relative_to(STAGE)): sha256(p) for p in sorted(STAGE.rglob("*")) if p.is_file()}
    manifest = {"python": PY_VERSION, "python_sha256": PY_SHA256, "pyyaml": yaml.__version__,
                "git": _git(), "built": board.laptop_time(), "files": files}
    (STAGE / "MANIFEST.json").write_text(json.dumps(manifest, indent=1))
    size = sum(p.stat().st_size for p in STAGE.rglob("*") if p.is_file())
    print(f"bundle: {len(files)} files, {size / 1e6:.1f} MB, {STAGE.relative_to(ROOT)}")
    return manifest


def stage_app(app: Path) -> None:
    """The agent's files as they sit on the board (app/): run_demo.py, the bench
    modules it imports, the agent, configs, knowledge bases, the study's episodes
    and the vendored PyYAML (pure-Python files only)."""
    for f in APP_FILES:
        _copy(ROOT / f, app / f)
    for f in BENCH_MODULES:
        _copy(ROOT / "bench" / f, app / "bench" / f)
    for d in APP_DIRS + EPISODE_DIRS:
        src = (ROOT / d).resolve()                 # episode folders may be symlinks
        for p in sorted(src.rglob("*")):
            if p.is_file() and not _skip(p.relative_to(src)):
                _copy(p, app / d / p.relative_to(src))
    import yaml
    for p in sorted(Path(yaml.__file__).parent.glob("*.py")):
        _copy(p, app / "yaml" / p.name)
    (app / "data" / "experience").mkdir(parents=True, exist_ok=True)


def _copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _git() -> str:
    p = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip()
    return p.stdout.strip() + ("+dirty" if dirty else "")


# ---------------------------------------------------------------- board
def push() -> None:
    """Push STAGE to BOARD_ROOT (replacing it) and compare the sha256 of every
    manifest file on the board with the laptop's."""
    manifest = json.loads((STAGE / "MANIFEST.json").read_text())
    board._adb("shell", f"rm -rf {BOARD_ROOT} && mkdir -p {BOARD_ROOT}", timeout=120)
    p = board._adb("push", f"{STAGE}/.", BOARD_ROOT, timeout=1800)
    if p.returncode != 0:
        raise SystemExit(f"adb push failed: {p.stderr[-500:]}")
    board._adb("shell", f"chmod 755 {BOARD_ROOT}/bin/fieldmind-python")
    bad = verify(manifest)
    if bad:
        raise SystemExit(f"{len(bad)} file(s) differ on the board, e.g. {bad[:5]}")
    print(f"pushed {len(manifest['files'])} files; every sha256 matches")


def verify(manifest: dict) -> list[str]:
    out = board._adb("shell", f"cd {BOARD_ROOT} && find . -type f ! -name MANIFEST.json "
                              f"-exec sha256sum {{}} +", timeout=600).stdout
    got = {}
    for ln in out.splitlines():
        parts = ln.split(None, 1)
        if len(parts) == 2:
            got[parts[1].strip().removeprefix("./")] = parts[0]
    return sorted(k for k, v in manifest["files"].items() if got.get(k) != v) + \
        sorted(k for k in got if k not in manifest["files"])


def board_command(run_args: list[str], cpu_mask: str | None = None) -> str:
    """The adb shell line that runs run_demo.py on the board."""
    env = (f"LD_LIBRARY_PATH={BOARD_ROOT}/python/lib:{board.DEVICE_PKG}/lib "
           f"ADSP_LIBRARY_PATH={board.DEVICE_PKG}/lib PYTHONHOME={BOARD_ROOT}/python "
           f"PYTHONDONTWRITEBYTECODE=1 FIELDMIND_ON_DEVICE=1 HOME={BOARD_ROOT}")
    pin = f"taskset {cpu_mask} " if cpu_mask else ""
    return (f"cd {BOARD_ROOT}/app && {env} {pin}{BOARD_ROOT}/bin/fieldmind-python run_demo.py "
            + " ".join(shlex.quote(a) for a in run_args))


def run_on_board(run_args: list[str], out_local: Path, cpu_mask: str | None = None,
                 timeout: float = 7200) -> dict:
    """Run run_demo.py on the board into app/results/device/, pull that folder to
    out_local. Laptop time and chip temperature are logged around the run."""
    run_args = [a for a in run_args if a != "--"]
    if "--out" in run_args:
        raise SystemExit("--out is set by device_agent (app/results/device on the board)")
    board._adb("shell", f"rm -rf {BOARD_ROOT}/app/results/device")
    t0, c0 = board.laptop_time(), board.chip_temperature()
    line = board_command(run_args + ["--out", "results/device"], cpu_mask)
    start = time.monotonic()
    p = board._adb("shell", line, timeout=timeout)
    wall = time.monotonic() - start
    t1, c1 = board.laptop_time(), board.chip_temperature()
    out_local.mkdir(parents=True, exist_ok=True)
    board._adb("pull", f"{BOARD_ROOT}/app/results/device/.", str(out_local), timeout=600)
    rec = {"command": line, "returncode": p.returncode, "laptop_start": t0, "laptop_end": t1,
           "wall_s": round(wall, 1), "chip_c_before": c0, "chip_c_after": c1,
           "cpu_mask": cpu_mask, "stdout_tail": p.stdout[-3000:], "stderr_tail": p.stderr[-3000:]}
    (out_local / "device_run.json").write_text(json.dumps(rec, indent=1))
    if p.returncode != 0:
        raise SystemExit(f"run on the board failed (exit {p.returncode}):\n{p.stdout[-1500:]}\n{p.stderr[-1500:]}")
    return rec


# ---------------------------------------------------------------- identity
# Keys whose values are clock readings (or decided by one): they differ between
# any two runs on the same machine, so identity ignores them and nothing else.
TIMING_KEYS = {"wall_clock_s", "tick_latency_ms", "deadline_miss", "p0_ms", "p0_deadline_miss",
               "hard_ms", "latency_ms", "check_ms", "queue_wait_ms", "start_s", "finish_s",
               "tick_epoch_s", "elapsed_ms", "stage_ms", "resources"}


def strip_timing(x):
    if isinstance(x, dict):
        return {k: strip_timing(v) for k, v in x.items()
                if k not in TIMING_KEYS and not k.endswith("_ms") and not k.endswith("_wall_s")}
    if isinstance(x, list):
        return [strip_timing(v) for v in x]
    return x


def compare_runs(a: list[dict], b: list[dict]) -> dict:
    """Tick-by-tick comparison of two runs files with timing removed."""
    out = {"episodes": 0, "ticks": 0, "ticks_identical": 0, "first_difference": None}
    for ra, rb in zip(a, b):
        out["episodes"] += 1
        for ta, tb in zip(ra["assessments"], rb["assessments"]):
            out["ticks"] += 1
            sa, sb = strip_timing(ta), strip_timing(tb)
            if sa == sb:
                out["ticks_identical"] += 1
            elif out["first_difference"] is None:
                diff = sorted(k for k in set(sa) | set(sb) if sa.get(k) != sb.get(k))
                out["first_difference"] = {"episode": ra["episode_id"], "tick": ta["tick"], "keys": diff}
        if len(ra["assessments"]) != len(rb["assessments"]):
            out["first_difference"] = out["first_difference"] or {
                "episode": ra["episode_id"], "n_ticks": [len(ra["assessments"]), len(rb["assessments"])]}
    out["identical"] = (out["ticks"] > 0 and out["ticks"] == out["ticks_identical"]
                        and len(a) == len(b) and out["first_difference"] is None)
    return out


IDENTITY_RUNS = [  # (episodes dir, episode, overlay): one per plant, the study's systems
    ("data/episodes_dev", "dev_B01_tube_leak", "configs/v3.yaml,configs/sched_study.yaml"),
    ("data/episodes_cranfield_dev", "cf_F5_5.1_slugging_conditions",
     "configs/v3.yaml,configs/cranfield.yaml,configs/sched_study.yaml"),
]


def identity(out_root: Path) -> list[dict]:
    """Mock backend, lockstep: the same command here and on the board."""
    results = []
    for epdir, ep, ov in IDENTITY_RUNS:
        args = ["--backend", "mock", "--arch", "multi", "--episodes-dir", epdir, "--episode", ep,
                "--overlay", ov, "--tag", "ident"]
        lap = out_root / ep / "laptop"
        subprocess.run([sys.executable, "run_demo.py", *args, "--out", str(lap)], cwd=ROOT,
                       check=True, capture_output=True, env=board.clean_env())
        dev = out_root / ep / "board"
        run_on_board(args, dev)
        a = json.loads((lap / "runs_mock_ident.json").read_text())
        b = json.loads((dev / "runs_mock_ident.json").read_text())
        r = {"episode": ep, **compare_runs(a, b)}
        print(json.dumps(r))
        results.append(r)
    (out_root / "identity.json").write_text(json.dumps(results, indent=1))
    return results


def hard_path(runs: list[dict]) -> dict:
    """p50 / p95 / max of the hard path (multi.p0_ms per tick) against the plan's 200 ms."""
    xs = sorted(a["multi"]["p0_ms"] for r in runs for a in r["assessments"]
                if (a.get("multi") or {}).get("p0_ms") is not None)
    if not xs:
        return {"n": 0}

    def q(f):
        return round(xs[min(len(xs) - 1, int(f * len(xs)))], 2)
    return {"n": len(xs), "p50_ms": q(0.5), "p95_ms": q(0.95), "max_ms": round(xs[-1], 2),
            "over_200ms": sum(x > 200.0 for x in xs)}


def main() -> int:
    board.drop_pythonpath()
    ap = argparse.ArgumentParser(description="The FieldMind agent on the QIDK.")
    ap.add_argument("what", choices=["launcher", "bundle", "push", "run", "identity", "hardpath"])
    ap.add_argument("--cpu-mask", default=None, help="run/hardpath: taskset mask, e.g. 80 (cpu7)")
    ap.add_argument("--out", default="results/device", help="local folder for pulled results")
    ap.add_argument("rest", nargs=argparse.REMAINDER, help="run: arguments for run_demo.py")
    a = ap.parse_args()
    out = ROOT / a.out
    if a.what == "launcher":
        build_launcher()
    elif a.what == "bundle":
        bundle()
    elif a.what == "push":
        push()
    elif a.what == "run":
        run_on_board(a.rest, out / time.strftime("%Y%m%d-%H%M%S"), a.cpu_mask)
    elif a.what == "identity":
        res = identity(out / "identity")
        return 0 if all(r["identical"] for r in res) else 1
    elif a.what == "hardpath":
        res = {}
        for epdir, ep, ov in IDENTITY_RUNS:
            d = out / "hardpath" / f"{ep}_{a.cpu_mask or 'any'}"
            run_on_board(["--backend", "mock", "--arch", "multi", "--episodes-dir", epdir,
                          "--episode", ep, "--overlay", ov, "--tag", "hp"], d, a.cpu_mask)
            res[ep] = hard_path(json.loads((d / "runs_mock_hp.json").read_text()))
            print(ep, json.dumps(res[ep]))
        (out / "hardpath" / f"hardpath_{a.cpu_mask or 'any'}.json").write_text(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
