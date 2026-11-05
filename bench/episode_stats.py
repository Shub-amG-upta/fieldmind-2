#!/usr/bin/env python3
"""Every statistic of ONE episode run on the board, read from its saved files.

    .venv/bin/python -m bench.episode_stats                          # newest run of the newest test
    .venv/bin/python -m bench.episode_stats <test>                   # that test's newest run
    .venv/bin/python -m bench.episode_stats <test> <episode> [--run N]
    .venv/bin/python -m bench.episode_stats --list                   # tests and their episodes

Reads results/benchmarks/<test>/<episode>_<arch>[_rN].{summary.json, run.json.gz,
resources.json}. Changes nothing. Uses bench.bev_report.metrics for the per-stage,
per-agent, lane and board numbers, so they match the COMPARE reports.
Laptop times: the agent code runs on the laptop; model call times are board times."""
from __future__ import annotations

import argparse
import gzip
import json
import re
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from bench import bev_report as br  # noqa: E402

BENCH = ROOT / "results/benchmarks"


def _f(x, nd=2):
    if x is None:
        return "–"
    if isinstance(x, float):
        return f"{x:,.{nd}f}"
    return f"{x:,}" if isinstance(x, int) else str(x)


def table(head, rows):
    w = [max(len(str(h)), *(len(str(r[i])) for r in rows)) if rows else len(str(h)) for i, h in enumerate(head)]
    num = [bool(rows) and all(re.fullmatch(r"[-–\d.,%]+( s| ms)?", str(r[i]).strip() or "–") for r in rows)
           for i in range(len(head))]
    line = lambda r: "  " + "  ".join(str(c).rjust(w[i]) if num[i] else str(c).ljust(w[i]) for i, c in enumerate(r))
    print(line(head))
    print("  " + "  ".join("-" * x for x in w))
    for r in rows:
        print(line(r))


def section(t):
    print(f"\n== {t} " + "=" * max(0, 78 - len(t)))


def runs_of(test_dir: Path) -> list[Path]:
    return sorted(test_dir.glob("*.summary.json"), key=lambda p: p.stat().st_mtime)


def pick(test: str | None, episode: str | None, run: int | None) -> Path:
    if test is None:
        tests = [d for d in BENCH.iterdir() if d.is_dir() and runs_of(d)]
        if not tests:
            raise SystemExit("no benchmark runs in results/benchmarks/")
        test_dir = max(tests, key=lambda d: runs_of(d)[-1].stat().st_mtime)
    else:
        test_dir = br.find(test)
    cands = runs_of(test_dir)
    if episode:
        cands = [p for p in cands if json.loads(p.read_text())["meta"]["episode"] == episode]
        if run:
            cands = [p for p in cands if json.loads(p.read_text())["meta"]["run"] == run]
    if not cands:
        raise SystemExit(f"no saved run of {episode or 'any episode'} in {test_dir}")
    return cands[-1]


def main() -> int:
    ap = argparse.ArgumentParser(description="Statistics of one episode run (board or mock).")
    ap.add_argument("test", nargs="?", help="test name (folder in results/benchmarks); default: newest")
    ap.add_argument("episode", nargs="?", help="episode id; default: the test's newest run")
    ap.add_argument("--run", type=int, default=None, help="run number (1, 2 for _r2, ...)")
    ap.add_argument("--list", action="store_true", help="list tests and their saved episodes")
    a = ap.parse_args()
    if a.list:
        for d in sorted(BENCH.iterdir()):
            rs = runs_of(d) if d.is_dir() else []
            if rs:
                eps = sorted({json.loads(p.read_text())["meta"]["episode"] for p in rs})
                print(f"{d.name:32} {len(rs):3} runs  {' '.join(eps)}")
        return 0

    sp = pick(a.test, a.episode, a.run)
    stem = sp.name[:-len(".summary.json")]
    d = sp.parent
    summ = json.loads(sp.read_text())
    run = json.load(gzip.open(d / f"{stem}.run.json.gz"))
    run = run[0] if isinstance(run, list) else run
    rp = d / f"{stem}.resources.json"
    res = json.loads(rp.read_text()) if rp.exists() else summ["meta"].get("resources")
    m, ev, calls = summ["meta"], summ["evaluation"], summ["calls"]
    p = m.get("params", {})
    ep = m["episode"]
    t = {"name": d.name, "dir": d, "params": p,
         "episodes": {ep: {"summary": summ, "run": run, "resources": res}}}
    M = br.metrics(t, [ep])

    mock = run.get("backend") == "mock"
    print(f"{'MOCK BACKEND: plumbing only, NOT an agent result. ' if mock else ''}"
          f"{ep}  ·  test {d.name}  ·  run {m['run']}  ·  {stem}")

    section("Run")
    table(("field", "value"), [
        ("architecture / mode", f"{p.get('arch')} / {p.get('mode')}"),
        ("overlay / merge rule", f"{p.get('overlay')} / {p.get('merge_rule')}"),
        ("models", ", ".join(f"{k}: {v}" for k, v in (p.get("models") or {}).items())),
        ("bev ideas / bev device", f"{p.get('bev') or '–'} / {p.get('bev_device') or '–'}"),
        ("started → finished (laptop)", f"{m.get('started', '')[:19]} → {m.get('finished', '')[:19]}"),
        ("wall time", f"{_f(m.get('wall_s'), 1)} s"),
        ("chip °C before → after", f"{_f(m.get('chip_c_before'), 1)} → {_f(m.get('chip_c_after'), 1)}"),
        ("cooling wait", f"{_f(m.get('cool_wait_s'))} s"),
        ("git", f"{(m.get('git') or {}).get('branch')} {(m.get('git') or {}).get('commit')}"
                + (" (uncommitted changes)" if (m.get('git') or {}).get('uncommitted_changes') else "")),
        ("where", m.get("where", "")),
        ("energy", "not measured" if m.get("energy_mwh") is None else m["energy_mwh"]),
    ])

    section("Accuracy (scored from fault onset)")
    t2, t3, t4, t5, t6 = (ev.get(k) or {} for k in ("T2_root_cause", "T3_faithfulness", "T4_actions",
                                                   "T5_false_positives", "T6_lead_time"))
    rows = [("true cause", f"{t2.get('target')} (group {t2.get('true_group')})"
             + (" · held-out" if t2.get("heldout") else ""))] if t2.get("applicable") else []
    rows += [("scored ticks", _f(t2.get("n_scored"))),
             ("published group top-1 (headline)", _f(t2.get("group_top1"), 3)),
             ("belief alone group top-1 (code only)", _f(t2.get("belief_group"), 3)),
             ("exact top-1", _f(t2.get("top1_strict") if not t2.get("heldout") else None, 3)),
             ("true case in top 3", _f(t2.get("top3"), 3))] if t2.get("applicable") else \
            [("root cause", "not scored (no library cause for this episode)")]
    rows += [("plant state macro-F1 (code)", _f((ev.get("T1_state") or {}).get("macro_f1"), 3)),
             ("faithfulness (cited facts exist)", _f(t3.get("faithfulness"), 3)),
             ("actions precision / recall", f"{_f(t4.get('precision'), 3)} / {_f(t4.get('recall'), 3)}"
              if t4.get("applicable") else "–"),
             ("lead time, exact case before trip", f"{_f(t6.get('lead_time_min'), 1)} min"
              if t6.get("applicable") else "–"),
             ("false alarms (no-fault episodes)", f"{_f(t5.get('fp_per_hour'))} /h" if t5.get("applicable") else "–")]
    table(("metric", "value"), rows)

    section("Ticks (LAPTOP times)")
    A = run["assessments"]
    nq = [a for a in A if a.get("triage") != "QUIET"]
    tl = [a["tick_latency_ms"] for a in nq if a.get("tick_latency_ms") is not None]
    p0 = [a["multi"]["p0_ms"] for a in A if (a.get("multi") or {}).get("p0_ms") is not None]
    triage = {}
    for a in A:
        triage[a.get("triage")] = triage.get(a.get("triage"), 0) + 1
    table(("metric", "value"), [
        ("ticks / non-quiet", f"{len(A)} / {len(nq)}"),
        ("triage levels", ", ".join(f"{k} {v}" for k, v in sorted(triage.items()))),
        ("ticks with a model call (invocation rate)", _f(ev.get("S4_llm_invocation_rate"), 3)),
        ("non-quiet tick time median / p95 / max", " / ".join(_f(x / 1000, 2) for x in
                                                             (st.median(tl), br._q(tl, .95), max(tl))) + " s"
         if tl else "–"),
        ("ticks over the 30 s budget", sum(x > 30000 for x in tl)),
        ("hard path (code only) median / p95 / max", " / ".join(_f(x, 1) for x in
                                                              (st.median(p0), br._q(p0, .95), max(p0))) + " ms"
         if p0 else "–"),
        ("hard path over 200 ms", sum(x > 200 for x in p0)),
    ])

    if M["stages"]:
        section("Time per stage, ms per tick it ran (LAPTOP)")
        table(("stage", "ticks", "mean", "p95", "max", "total s"),
              [(k + (" (hard path)" if k in br.HARD else ""), v["ticks"], _f(v["mean"], 2), _f(v["p95"], 2),
                _f(v["max"], 2), _f(v["total_s"], 2)) for k, v in M["stages"].items()])

    section("Model calls per agent @ lane (board timings)")
    rows = []
    lat = {}
    for a in A:
        envs = list(a.get("envelopes") or []) + [x["envelope"] for x in (a.get("multi") or {}).get("text", [])]
        for e in envs:
            lat.setdefault(f"{e['agent']}@{e.get('backend', '?')}", []).append((e.get("latency_ms") or 0) / 1000)
    for k, c in M["calls"].items():
        n = c.get("calls", 0)
        rd, dc = c.get("server_read_s", 0), c.get("server_decode_s", 0)
        rows.append((k, c.get("answers", 0), n, _f(c.get("read_tokens", 0)), _f(c.get("decode_tokens", 0)),
                     _f(st.median(lat[k]), 2) if lat.get(k) else "–",
                     _f(c.get("call_s", 0), 1), _f(rd, 1), _f(dc, 1),
                     f"{dc / (rd + dc):.0%}" if rd + dc else "–",
                     _f(c.get("read_tokens", 0) / rd, 0) if rd else "–",
                     _f(c.get("decode_tokens", 0) / dc, 1) if dc else "–"))
    table(("agent@lane", "answers", "calls", "prompt tok", "answer tok", "median s", "total s",
           "prefill s", "decode s", "decode %", "prefill tok/s", "decode tok/s"), rows)
    print(f"  unusable answers {calls.get('unusable', 0)} · answer tokens per tick {_f(M['decode_per_tick'])}")

    if calls.get("decider") or calls.get("bev_ideas"):
        section("bev-decider")
        if calls.get("decider"):
            dd = calls["decider"]
            print(f"  decider: calls {dd.get('calls')} · failed {dd.get('failed')} · rejected {dd.get('rejected')}"
                  f" · replay reproduces published: {m.get('replay_reproduces_published', '–')}")
        if calls.get("bev_ideas"):
            table(("idea", "calls", "failed", "rejected", "used", "shadow", "other"),
                  [(k, v.get("calls", 0), v.get("failed", 0), v.get("rejected", 0), v.get("used", 0),
                    v.get("shadow", 0), ", ".join(f"{a} {b}" for a, b in v.items()
                                                 if a not in ("calls", "failed", "rejected", "used", "shadow")) or "–")
                   for k, v in sorted(calls["bev_ideas"].items())])
            for k, v in M["bev"]["agreement"].items():
                print(f"  {k}: mean {v['mean']} over {v['n']} answers")

    if M["lanes"]:
        section("Lanes: measured call time / wall time")
        if not any(v["busy_s"] for v in M["lanes"].values()):
            print("  not recorded for this run (lane busy time is logged from the bev-ideas runner on)")
        else:
          table(("lane", "busy s", "share of wall"),
              [(k, _f(v["busy_s"], 1), f"{v['share_of_wall']:.0%}" if v["share_of_wall"] is not None else "–")
               for k, v in M["lanes"].items()])

    section("Board resources (on-board sampler, once a second)")
    if not res or "error" in (res or {}):
        print("  " + (f"sampler error: {res['error']}" if res else "no sampler data for this run "
                      "(runs before the bev-ideas runner, or a mock run)"))
    else:
        b = M["board"]
        table(("server", "process", "CPU s", "cores busy", "peak RSS MB"),
              [(k, v["process"], _f(v["cpu_s"], 1), _f(v["cores_busy_mean"], 2), _f(v["peak_rss_mb"], 1))
               for k, v in b["processes"].items()])
        print(f"  board CPU busy {_f(b['board_cpu_busy_pct_mean'], 1)} % · max CPU / NPU {_f(b['cpu_max_c'], 1)}"
              f" / {_f(b['npu_max_c'], 1)} °C · sampler's own CPU {_f(b['sampler_cpu_s'])} s · supply energy "
              f"{_f(b['supply_energy_j'])} (null: not readable on this board)")
        print("  RSS misses the NPU's DMA buffers (Llama NPU lane ~2.5 GB, bev-decide ~1.1 GB; "
              "reports/bev_measurement.md 2A).")
    print(f"\nfiles: {d.relative_to(ROOT)}/{stem}.*")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
