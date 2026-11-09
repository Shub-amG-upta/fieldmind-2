#!/usr/bin/env python3
"""
=============================================================================
 SCHEDULING STUDY  --  the pre-registered matrix, run through the benchmark
 runner, and its tables (plan Phase 5; reports/sched_prereg.md)
=============================================================================

    .venv/bin/python bench/sched_study.py plan   [--backend mock]
    .venv/bin/python bench/sched_study.py run    [--only TEXT] [--backend mock]
    .venv/bin/python bench/sched_study.py table  [--backend mock]
    .venv/bin/python bench/sched_study.py run --backend mock --dry-tick-s 0.05   (plumbing)
    .venv/bin/python bench/sched_study.py rates [--n 6]   lanes up, after the lockstep refs

The matrix is fixed here and in reports/sched_prereg.md (committed before any
study run): POLICIES x CONFIGS x LOADS, each cell on every episode of
EPISODES, plus one lockstep reference per config and plant (fixed placement,
the answer every real-time cell is compared against). One benchmark test per
cell (scripts/benchmark.sh <name> ...), so a cell resumes where it stopped and
is never mixed with another cell's settings.

`table` reads results/benchmarks[_mock]/sched_*/ and prints, per cell: the
deadline-miss rate per priority, answer age in ticks (p50 / p95), the share of
time both model lanes ran together, calls per lane, answers dropped as stale,
and accuracy next to the lockstep reference. Deadline misses are recounted
from the per-call spans of the run file, not taken from the stored summary.
Mock-backend tables are plumbing only: the mock model does no reasoning and
its timings are not the board's.
=============================================================================
"""

from __future__ import annotations

import argparse
import gzip
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

POLICIES = ("fixed", "earliest_finish", "tick_alternation", "priority_reserved")
# Overlays stack in order; the plant overlay goes right after the system's.
CONFIGS = {
    "v3": {"overlays": ["configs/v3.yaml", "{asset}", "configs/sched_study.yaml"], "bev": None},
    "v3x": {"overlays": ["configs/v3.yaml", "{asset}", "configs/bev_ideas.yaml",
                         "configs/laya_board.yaml", "configs/sched_study.yaml"],
            "bev": "explain=on,clear_skip=on"},
}
# Wall seconds per 30 s plant tick (compressed time: 3x and 6x real time).
LOADS_S = (10.0, 5.0)
# dev_A02 has URGENT ticks (P1 work); dev_B01 and every Cranfield dev episode have
# none (reports/sched_prereg.md, "Episodes").
EPISODES = {"boiler": ["dev_B01_tube_leak", "dev_A02_fcv_seize_fast"],
            "cranfield": ["cf_F5_5.1_slugging_conditions"]}
ASSET_OVERLAY = {"boiler": None, "cranfield": "configs/cranfield.yaml"}
PRIORITIES = ("P1", "P2", "P3")


def overlay(config: str, asset: str) -> str:
    out = []
    for o in CONFIGS[config]["overlays"]:
        if o == "{asset}":
            if ASSET_OVERLAY[asset]:
                out.append(ASSET_OVERLAY[asset])
        else:
            out.append(o)
    return ",".join(out)


def cells(dry_tick_s: float | None = None) -> list[dict]:
    """Every test of the study: the lockstep references first, then the real-time
    cells, light load before heavy. dry_tick_s (mock only): every real-time cell
    at that wall tick instead, named *_dry, so a plumbing run is never read as a cell."""
    out = []
    for config in CONFIGS:
        for asset in EPISODES:
            out.append({"name": f"sched_{config}_lockstep_{asset}", "config": config, "asset": asset,
                        "policy": "fixed", "mode": "lockstep", "tick_s": None})
    for tick_s in LOADS_S:
        for config in CONFIGS:
            for policy in POLICIES:
                for asset in EPISODES:
                    out.append({"name": f"sched_{config}_{policy}_t{tick_s:g}_{asset}"
                                        + ("_dry" if dry_tick_s else ""),
                                "config": config, "asset": asset, "policy": policy,
                                "mode": "realtime", "tick_s": tick_s,
                                "run_tick_s": dry_tick_s or tick_s})
    return out


def command(cell: dict, backend: str) -> list[str]:
    cmd = ["scripts/benchmark.sh", cell["name"], *EPISODES[cell["asset"]],
           "--overlay", overlay(cell["config"], cell["asset"]),
           "--placement", cell["policy"], "--mode", cell["mode"], "--plain"]
    if cell["mode"] == "realtime":
        cmd += ["--tick-s", f"{cell['run_tick_s']:g}"]
    if CONFIGS[cell["config"]]["bev"]:
        cmd += ["--bev", CONFIGS[cell["config"]]["bev"]]
    if backend == "mock":
        cmd += ["--backend", "mock"]
    return cmd


# ---------------------------------------------------------------- analysis
def _pct(xs: list, q: float):
    if not xs:
        return None
    s = sorted(xs)
    return s[min(len(s) - 1, int(q * len(s)))]


def _overlap_s(spans: list[dict], a: str, b: str) -> float:
    """Seconds during which lanes a and b both ran a call (sweep over start/end
    events; an independent route from realtime.summarize's interval pairs)."""
    ev = sorted([(s["start_s"], 1, s["lane"]) for s in spans if s["lane"] in (a, b)]
                + [(s["end_s"], -1, s["lane"]) for s in spans if s["lane"] in (a, b)])
    busy = {a: 0, b: 0}
    t_prev, both = None, 0.0
    for t, d, lane in ev:
        if t_prev is not None and busy[a] > 0 and busy[b] > 0:
            both += t - t_prev
        busy[lane] += d
        t_prev = t
    return both


def run_metrics(run: dict, ev: dict) -> dict:
    """One episode run: scheduling numbers from its spans, accuracy from its evaluation."""
    rt = ((run.get("multi") or {}).get("realtime")) or {}
    spans = rt.get("spans") or []
    wall_tick = rt.get("wall_tick_s")
    m = {"calls": {}, "busy_s": {}, "deadline": {p: {"n": 0, "missed": 0} for p in PRIORITIES},
         "ages": [], "spans": len(spans)}
    for s in spans:
        m["calls"][s["lane"]] = m["calls"].get(s["lane"], 0) + 1
        m["busy_s"][s["lane"]] = m["busy_s"].get(s["lane"], 0.0) + (s["end_s"] - s["start_s"])
        p = f"P{s['priority']}"
        if s.get("deadline_s") is not None and p in m["deadline"]:
            m["deadline"][p]["n"] += 1
            # recounted: finish time against the wall tick the job's evidence belongs to
            m["deadline"][p]["missed"] += (s["end_s"] - s["tick_s"]) > s["deadline_s"]
        if wall_tick:
            m["ages"].append((s["end_s"] - s["tick_s"]) / wall_tick)
    m["both_busy_s"] = _overlap_s(spans, "npu", "cpu")
    m["stale_dropped"] = len(((run.get("multi") or {}).get("stale_dropped")) or [])
    m["n_ticks"] = run.get("n_ticks")
    t2, t5 = ev.get("T2_root_cause") or {}, ev.get("T5_false_positives") or {}
    m["group_top1"] = t2.get("group_top1")
    m["fp_per_hour"] = t5.get("fp_per_hour") if t5.get("applicable") else None
    m["recorded_deadline"] = rt.get("deadline")
    # jobs superseded by newer evidence before they ran: no span, so no deadline
    # entry; counted here so a policy cannot look punctual by never running work
    m["replaced"] = rt.get("replaced_waiting_jobs") or 0
    return m


def load_cell(folder: Path) -> list[dict]:
    out = []
    for sp in sorted(folder.glob("*.summary.json")):
        s = json.loads(sp.read_text())
        rp = sp.with_name(sp.name.replace(".summary.json", ".run.json.gz"))
        with gzip.open(rp, "rt") as f:
            run = json.load(f)
        out.append({"episode": s["meta"]["episode"], "run": s["meta"].get("run", 1), "meta": s["meta"],
                    **run_metrics(run, s["evaluation"])})
    return out


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def _f(x, nd=3):
    return "–" if x is None else f"{x:.{nd}f}"


def table(root: Path, dry_tick_s: float | None = None, per_run: bool = False) -> str:
    """One row per cell (episodes pooled), or with per_run one row per episode run
    (run-to-run spread: the registered repeat cells, reports/sched_prereg.md)."""
    ref = {}
    rows = []
    for cell in cells(dry_tick_s):
        folder = root / cell["name"]
        found = load_cell(folder) if folder.exists() else []
        if cell["mode"] == "lockstep":
            ref[(cell["config"], cell["asset"])] = found
            continue
        if not found:
            rows.append(f"| {cell['config']} | {cell['policy']} | {cell['tick_s']:g} | {cell['asset']} "
                        f"| not run |" + " |" * 10)
            continue
        for runs in ([[r] for r in found] if per_run else [found]):
            rows.append(_row(cell, runs, ref, per_run))
    head = ("| config | policy | wall s / tick | plant | runs | P1 missed | P2 missed | P3 missed "
            "| age ticks p50 / p95 | both lanes busy / less-busy lane | calls npu / cpu / bev "
            "| replaced before running | stale dropped | group top-1 | lockstep group top-1 |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    return head + "\n" + "\n".join(rows)


def _row(cell: dict, runs: list[dict], ref: dict, per_run: bool) -> str:
    miss = []
    for p in PRIORITIES:
        n = sum(r["deadline"][p]["n"] for r in runs)
        k = sum(r["deadline"][p]["missed"] for r in runs)
        miss.append(f"{k}/{n}" if n else "–")
    ages = [a for r in runs for a in r["ages"]]
    busy = {ln: sum(r["busy_s"].get(ln, 0.0) for r in runs) for ln in ("npu", "cpu")}
    both = sum(r["both_busy_s"] for r in runs)
    calls = {ln: sum(r["calls"].get(ln, 0) for r in runs) for ln in ("npu", "cpu", "bev")}
    acc = _mean([r["group_top1"] for r in runs])
    base = ref.get((cell["config"], cell["asset"])) or []
    acc0 = _mean([r["group_top1"] for r in base if r["episode"] in {x["episode"] for x in runs}])
    n = f"{runs[0]['episode']} r{runs[0]['run']}" if per_run else str(len(runs))
    return (
        f"| {cell['config']} | {cell['policy']} | {cell['tick_s']:g} | {cell['asset']} | {n} "
        f"| {' | '.join(miss)} | {_f(_pct(ages, 0.5), 2)} / {_f(_pct(ages, 0.95), 2)} "
        f"| {_f(both / max(1e-9, min(busy['npu'], busy['cpu'])) if min(busy.values()) else None, 2)} "
        f"| {calls['npu']} / {calls['cpu']} / {calls['bev']} | {sum(r['replaced'] for r in runs)} "
        f"| {sum(r['stale_dropped'] for r in runs)} | {_f(acc)} | {_f(acc0)} |")


# ---------------------------------------------------------------- lane rates
def study_prompts(n: int, root: Path) -> list[str]:
    """n diagnostician prompts the agent really sent, evenly spaced through the
    v3 boiler lockstep reference run (its run file keeps every prompt)."""
    ps = []
    for f in sorted((root / "sched_v3_lockstep_boiler").glob("*.run.json.gz")):
        with gzip.open(f, "rt") as fh:
            run = json.load(fh)
        ps += [e["prompt"] for a in run["assessments"] for e in a.get("envelopes", [])
               if e.get("agent", "").startswith("diag") and e.get("prompt")]
    if len(ps) < n:
        raise SystemExit(f"{len(ps)} saved diagnostician prompts in {root}/sched_v3_lockstep_boiler; "
                         f"run the lockstep reference first (prompts saved)")
    return [ps[round(i * (len(ps) - 1) / max(1, n - 1))] for i in range(n)]


def lane_rates(urls: dict, prompts: list[str], max_tokens: int = 60) -> dict:
    """Each lane alone (one call at a time), then both lanes at once on the same
    prompt (plan risk: shared LPDDR5). Rates are the server's own timings."""
    import threading
    from bench import board
    out = {"alone": {}, "together": {}, "samples": {"alone": {}, "together": {}}}
    for lane, url in urls.items():
        s = [board.lane_speed(url, p, max_tokens) for p in prompts]
        out["samples"]["alone"][lane] = s
        out["alone"][lane] = board.mean_rates(s)
    tog = {lane: [] for lane in urls}
    for p in prompts:
        res, threads = {}, []
        for lane, url in urls.items():
            t = threading.Thread(target=lambda ln=lane, u=url: res.__setitem__(ln, board.lane_speed(u, p, max_tokens)))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        for lane in urls:
            tog[lane].append(res[lane])
    out["samples"]["together"] = tog
    out["together"] = {lane: board.mean_rates(s) for lane, s in tog.items()}
    out["together_over_alone"] = {
        lane: {k: (round(out["together"][lane][k] / out["alone"][lane][k], 3)
                   if out["together"][lane][k] and out["alone"][lane][k] else None)
               for k in ("prefill_tok_s", "decode_tok_s")} for lane in urls}
    out["models"] = {lane: sorted({x.get("model") for x in out["samples"]["alone"][lane]}, key=str)
                     for lane in urls}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("what", choices=["plan", "run", "table", "rates"])
    ap.add_argument("--n", type=int, default=6, help="rates: prompts per lane and condition")
    ap.add_argument("--backend", choices=["llamaserver", "mock"], default="llamaserver")
    ap.add_argument("--only", default=None, help="run: only cells whose name contains this")
    ap.add_argument("--dry-tick-s", type=float, default=None,
                    help="mock only: run every real-time cell at this wall tick (plumbing check)")
    ap.add_argument("--per-run", action="store_true", help="table: one row per episode run")
    args = ap.parse_args()
    if args.dry_tick_s and args.backend != "mock":
        ap.error("--dry-tick-s is for --backend mock only")
    todo = cells(args.dry_tick_s)
    if args.what == "plan":
        for c in todo:
            print(" ".join(command(c, args.backend)))
        return 0
    if args.what == "run":
        for c in todo:
            if args.only and args.only not in c["name"]:
                continue
            print(f"== {c['name']}", flush=True)
            r = subprocess.run(command(c, args.backend), cwd=ROOT)
            if r.returncode != 0:
                print(f"stopped: {c['name']} exited {r.returncode}", file=sys.stderr)
                return r.returncode
        return 0
    root = ROOT / ("results/benchmarks_mock" if args.backend == "mock" else "results/benchmarks")
    if args.what == "rates":
        from bench import board
        from run_demo import load_config
        cfg = load_config(str(ROOT / "configs/base.yaml"), "llamaserver",
                          ",".join(str(ROOT / o) for o in ("configs/v3.yaml", "configs/sched_study.yaml")))
        urls = {ln: cfg["multi"]["lanes"][ln]["url"] for ln in ("npu", "cpu")}
        down = [ln for ln, u in urls.items() if not board.lane_health(u)]
        if down:
            raise SystemExit(f"lane(s) not up: {down} (HANDOFF_SCHED.md step 2 starts them)")
        t0, c0 = board.laptop_time(), board.chip_temperature()
        res = lane_rates(urls, study_prompts(args.n, root))
        res.update({"laptop_start": t0, "laptop_end": board.laptop_time(), "chip_c_before": c0,
                    "chip_c_after": board.chip_temperature(), "n": args.n,
                    "lane_files": {ln: cfg["multi"]["lanes"][ln]["model_file"] for ln in urls}})
        d = ROOT / "results" / "sched_rates"
        d.mkdir(parents=True, exist_ok=True)
        f = d / f"rates_{time.strftime('%Y%m%d-%H%M%S')}.json"
        f.write_text(json.dumps(res, indent=1))
        print(json.dumps({k: res[k] for k in ("alone", "together", "together_over_alone", "models")}, indent=1))
        print(f"saved {f.relative_to(ROOT)}")
        return 0
    if args.backend == "mock":
        print("MOCK backend: plumbing only. The mock model does no reasoning and its timings are "
              "laptop timings, not the board's; none of these numbers is a study result.\n")
    print(table(root, args.dry_tick_s, args.per_run))
    return 0


if __name__ == "__main__":
    sys.exit(main())
