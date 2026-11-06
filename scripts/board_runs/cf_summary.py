"""Cranfield board results against the branch's mock report, with the measurements."""
import collections
import glob
import gzip
import json
import os
import statistics as st

base = "/home/harsha/fieldmind-2/results/benchmarks/"
MOCK = {"cranfield_dev_v3": "/mnt/c/Users/Admin/Desktop/fieldmind-2/results/cranfield_dev/summary_mock_dev.json",
        "cranfield_report_v3": "/mnt/c/Users/Admin/Desktop/fieldmind-2/results/cranfield_report/summary_mock_report.json"}
for T in ("cranfield_dev_v3", "cranfield_report_v3"):
    mock = {e.get("episode_id") or e.get("episode"): e for e in json.load(open(MOCK[T]))["per_episode"]}
    rows, pre, post, delays, det, npul, cpul, pfill, dec = [], [], [], [], [], [], [], [], []
    picks = collections.Counter(); fix = worse = both = neither = same = total = 0
    ver = collections.Counter(); unusable = calls = tin = tout = wall = cool = resumed = 0
    npuT, cpuT, rssN, rssC, dma, avail = [], [], [], [], [], []
    for f in sorted(glob.glob(base + T + "/*.summary.json")):
        s = json.load(open(f)); m = s["meta"]; e = s["evaluation"]; t2 = e["T2_root_cause"]; t7 = e.get("T7_detection") or {}
        stem = f[:-len(".summary.json")]
        r = json.load(gzip.open(stem + ".run.json.gz", "rt"))
        gt = r["ground_truth"]; tgt = gt["root_cause_id"]; on = gt["fault_onset_t"]
        ep = r["episode_id"]; me = mock.get(ep, {}).get("T2_root_cause", {})
        rows.append((ep[3:24], r["n_ticks"], s["calls"]["calls"], round(m["wall_s"]), t2.get("top1"), me.get("top1"), t2.get("top3"), t2.get("belief_top1"), t7.get("detection_rate"), t7.get("far_before_fault"), t7.get("detection_delay_s"), (m.get("resources") or {}).get("temps", {}).get("npu_max_c")))
        det.append(t7.get("detection_rate")); pre.append(t7.get("far_before_fault")); post.append(t7.get("far_after_fault")); delays.append(t7.get("detection_delay_s"))
        calls += s["calls"]["calls"]; unusable += s["calls"]["unusable"]; tin += s["calls"]["tokens_in"]; tout += s["calls"]["tokens_out"]; wall += m["wall_s"]; cool += m.get("cool_wait_s") or 0
        resumed += bool((m.get("resume") or {}).get("resumed"))
        res = m.get("resources") or {}; tm = res.get("temps") or {}
        npuT.append(tm.get("npu_max_c")); cpuT.append(tm.get("cpu_max_c"))
        p = res.get("processes") or {}
        rssN.append((p.get("npu") or {}).get("peak_rss_mb")); rssC.append((p.get("cpu") or {}).get("peak_rss_mb"))
        mem = (m.get("memory") or {}).get("after_run") or {}
        dma.append(((mem.get("processes") or {}).get("npu") or {}).get("dmabuf_kb")); avail.append(mem.get("mem_available_kb"))
        for a in r["assessments"]:
            hy = a.get("hypotheses") or []
            top = hy[0].get("case_ref") if hy else None
            bk = a.get("belief_ranking") or []
            bel = bk[0].get("case_ref") if bk else None
            if hy and a["tick"] * 30 >= on:
                x, y = top == tgt, bel == tgt
                both += x and y; fix += x and not y; worse += y and not x; neither += not x and not y
            for en in a.get("envelopes") or []:
                raw = (en.get("raw_reply") or "").split("\n---REPAIR")[0]
                for c in en.get("calls") or []:
                    if c.get("latency_ms"):
                        (cpul if en.get("agent") == "verifier" else npul).append(c["latency_ms"] / 1000)
                    if c.get("prefill") and c.get("prefill_ms") and en.get("agent") != "verifier":
                        pfill.append(c["prefill"] / c["prefill_ms"] * 1000)
                    if c.get("decode") and c.get("decode_ms") and en.get("agent") != "verifier":
                        dec.append(c["decode"] / c["decode_ms"] * 1000)
                try:
                    j = json.loads(raw)
                except ValueError:
                    continue
                if j.get("r"):
                    picks[j["r"][0][0]] += 1
                for v in j.get("v") or []:
                    ver[v[1]] += 1
    print(f"=== {T}: {len(rows)} episodes")
    print("ep | ticks | calls | s | top1 | mock | top3 | belief | detect | FA-pre | delay | npuC")
    for w in rows:
        print(" | ".join(str(x) for x in w))
    nn = lambda v: [x for x in v if x is not None]
    print("mean detect", round(st.mean(nn(det)), 3), "FA pre", round(st.mean(nn(pre)), 3), "FA post", round(st.mean(nn(post)), 3), "delay", round(st.mean(nn(delays)), 1))
    print("ticks both right", both, "pub only", fix, "belief only", worse, "neither", neither)
    print("calls", calls, "unusable", unusable, "tokens", tin, tout, "wall_s", round(wall), "cool_s", round(cool), "resumed eps", resumed)
    print("first-case picks", dict(picks.most_common()), "verifier verdicts", dict(ver))
    print("NPU s median", round(st.median(npul), 2), "p95", round(sorted(npul)[int(len(npul) * .95)], 2), "CPU s median", round(st.median(cpul), 2) if cpul else None, "n", len(npul), len(cpul))
    print("NPU prefill tok/s", round(st.median(pfill)), "decode tok/s", round(st.median(dec), 1))
    print("NPU max C", max(nn(npuT)), "CPU max C", max(nn(cpuT)), "RSS npu", max(nn(rssN)), "cpu", max(nn(rssC)), "dma kB", max(nn(dma)), "min avail kB", min(nn(avail)))
