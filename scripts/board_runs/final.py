"""TEP board results against mock; failed calls; speed against temperature; the measuring pass."""
import collections
import glob
import gzip
import json
import os
import statistics as st

T = "/home/harsha/fieldmind-tep/results/benchmarks/tep_v3_board/"
mock = {e.get("episode_id") or e.get("episode"): e for e in
        json.load(open("/tmp/tep_mock/summary_mock_board.json"))["per_episode"]}
rows = []
agg = collections.Counter(); picks = collections.Counter(); ver = collections.Counter()
npu, cpu, pre, dec, temps, rssn, rssc, dma, avail, fp = [], [], [], [], [], [], [], [], [], []
failed = []; mock_same = mock_ticks = 0
for f in sorted(glob.glob(T + "*.summary.json")):
    s = json.load(open(f)); m = s["meta"]; e = s["evaluation"]; t2 = e["T2_root_cause"]; t7 = e.get("T7_detection") or {}
    stem = f[:-len(".summary.json")]
    r = json.load(gzip.open(stem + ".run.json.gz", "rt"))
    gt = r["ground_truth"]; tgt = gt.get("root_cause_id"); on = gt.get("fault_onset_t") or 0
    ep = r["episode_id"]; me = mock.get(ep, {}); mt2 = me.get("T2_root_cause", {})
    res = m.get("resources") or {}; tm = res.get("temps") or {}; p = res.get("processes") or {}
    temps.append(tm.get("npu_max_c")); rssn.append((p.get("npu") or {}).get("peak_rss_mb")); rssc.append((p.get("cpu") or {}).get("peak_rss_mb"))
    mem = (m.get("memory") or {}).get("after_run") or {}
    dma.append(((mem.get("processes") or {}).get("npu") or {}).get("dmabuf_kb")); avail.append(mem.get("mem_available_kb"))
    rs = m.get("resume") or {}
    rows.append((ep[10:], r["n_ticks"], s["calls"]["calls"], s["calls"]["unusable"], t2.get("group_top1"), t2.get("top1"), mt2.get("top1"), t2.get("top3"), t2.get("belief_top1"), t7.get("detection_rate"), t7.get("far_before_fault"), t7.get("detection_delay_s"), rs.get("sessions"), rs.get("calls_recorded_failed_after_server_death"), tm.get("npu_max_c")))
    fp.append((ep, (e.get("T5_false_positives") or {}).get("fp_per_hour")))
    agg["calls"] += s["calls"]["calls"]; agg["unusable"] += s["calls"]["unusable"]; agg["tin"] += s["calls"]["tokens_in"]; agg["tout"] += s["calls"]["tokens_out"]
    agg["failed"] += rs.get("calls_recorded_failed_after_server_death") or 0
    for g in glob.glob(stem + ".calls.jsonl*"):
        op = gzip.open if g.endswith(".gz") else open
        for l in op(g, "rt", encoding="utf-8"):
            c = json.loads(l)
            if c.get("crash_recorded"):
                failed.append((ep, c["agent"], c["tick"]))
    for a in r["assessments"]:
        hy = a.get("hypotheses") or []; top = hy[0].get("case_ref") if hy else None
        bk = a.get("belief_ranking") or []; bel = bk[0].get("case_ref") if bk else None
        if hy and tgt not in (None, "NONE") and a["tick"] * 180 >= on:
            x, y = top == tgt, bel == tgt
            agg["both"] += x and y; agg["pub"] += x and not y; agg["bel"] += y and not x; agg["neither"] += not x and not y
        for en in a.get("envelopes") or []:
            raw = (en.get("raw_reply") or "").split("\n---REPAIR")[0]
            is_v = en.get("agent") == "verifier"
            for c in en.get("calls") or []:
                if c.get("latency_ms"):
                    (cpu if is_v else npu).append(c["latency_ms"] / 1000)
                if not is_v and c.get("prefill") and c.get("prefill_ms"):
                    pre.append(c["prefill"] / c["prefill_ms"] * 1000)
                if not is_v and c.get("decode") and c.get("decode_ms"):
                    dec.append(c["decode"] / c["decode_ms"] * 1000)
            try:
                j = json.loads(raw)
            except ValueError:
                continue
            if j.get("r"):
                picks[j["r"][0][0]] += 1
            for v in j.get("v") or []:
                ver[v[1]] += 1
print("episodes", len(rows))
print("ep|ticks|calls|unus|group|top1|mock|top3|belief|detect|FApre|delay|sess|failed|npuC")
for w in rows:
    print("|".join(str(x) for x in w))
sc = [w for w in rows if w[5] is not None]
print("mean top1", round(st.mean(w[5] for w in sc), 3), "mean mock", round(st.mean(w[6] for w in sc if w[6] is not None), 3), "mean belief", round(st.mean(w[8] for w in sc if w[8] is not None), 3), "mean top3", round(st.mean(w[7] for w in sc if w[7] is not None), 3), "n", len(sc))
print("episodes with top1 equal mock:", sum(w[5] == w[6] for w in sc), "of", len(sc), "| different:", [(w[0], w[5], w[6]) for w in sc if w[5] != w[6]])
print(dict(agg)); print("first-case picks", dict(picks.most_common())); print("verdicts", dict(ver))
print("failed calls", failed)
print("NPU s med", round(st.median(npu), 2), "p95", round(sorted(npu)[int(len(npu) * .95)], 2), "CPU s med", round(st.median(cpu), 2), "n", len(npu), len(cpu))
print("prefill", round(st.median(pre)), "decode", round(st.median(dec), 1))
nn = lambda v: [x for x in v if x is not None]
print("npu max", max(nn(temps)), "rss npu", max(nn(rssn)), "cpu", max(nn(rssc)), "dma", max(nn(dma)), "min avail", min(nn(avail)))
print("false positives per hour, fault-free:", [x for x in fp if "normal" in x[0].lower() or "N0" in x[0] or "FF" in x[0]])

# speed against temperature: earlier and later calls of Cranfield report episodes
base = "/home/harsha/fieldmind-2/results/benchmarks/cranfield_report_v3/"
first, last = [], []
for g in glob.glob(base + "*.run.json.gz"):
    r = json.load(gzip.open(g, "rt")); v = []
    for a in r["assessments"]:
        for en in a.get("envelopes") or []:
            if en.get("agent") == "verifier":
                continue
            for c in en.get("calls") or []:
                if c.get("decode") and c.get("decode_ms"):
                    v.append(c["decode"] / c["decode_ms"] * 1000)
    if len(v) >= 40:
        first += v[:15]; last += v[-15:]
print("Cranfield decode tok/s, first 15 vs last 15 calls per episode:", round(st.median(first), 1), round(st.median(last), 1), "n", len(first), len(last))

# measuring pass
M = "/home/harsha/fieldmind-2/results/benchmarks/cranfield_meas/measure/"
if os.path.isdir(M):
    print("measure files", len(os.listdir(M)), sorted(set(x.split("_")[0] for x in os.listdir(M))))
    idle = json.load(open(M + "idle_resources.json"))
    print("idle:", {k: idle.get(k) for k in ("cpu_busy_pct", "sampler_cpu_s", "duration_s", "supply_power")}, "temps", idle.get("temps"))
    print("idle procs", {k: (v.get("cpu_s"), v.get("peak_rss_mb")) for k, v in (idle.get("processes") or {}).items()})
    for n in sorted(glob.glob(M + "memory_*.json"))[:12]:
        d = json.load(open(n)); print(os.path.basename(n)[7:-5], d.get("mem_available_kb"), {k: (v.get("rss_kb"), v.get("pss_kb"), v.get("dmabuf_kb")) for k, v in (d.get("processes") or {}).items()}, d.get("error"))
    print("pftrace", [(x, os.path.getsize(M + x)) for x in os.listdir(M) if x.endswith(".pftrace")])
    sp = sorted(glob.glob(M + "simpleperf_*.txt"))
    print("simpleperf files", len(sp))
    for x in sp[:2]:
        print(os.path.basename(x)); print("\n".join(l[:95] for l in open(x).read().splitlines()[-9:]))
    print(open(M + "perfetto.log").read()[-200:] if os.path.exists(M + "perfetto.log") else "")
