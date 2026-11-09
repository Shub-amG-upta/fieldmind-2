"""Does Llama read the cases or copy the order? Shuffled run against the normal run, answer by answer."""
import collections
import glob
import gzip
import json
import os
import re

N = os.path.expanduser("~/fieldmind-2/results/benchmarks/cranfield_dev_v3/")
S = os.path.expanduser("~/fieldmind-tep/results/benchmarks/cranfield_dev_v3_shuffled/")


def calls(path):
    out = {}
    for l in gzip.open(path, "rt", encoding="utf-8"):
        r = json.loads(l)
        if r.get("event") != "done" or r.get("role") != "diagnostician" or "RETRIEVED CASES:" not in r["prompt"]:
            continue
        cases = re.findall(r"(?m)^\d+\. (CF-\d)", r["prompt"].split("RETRIEVED CASES:")[1].split("NOTES AND")[0])
        try:
            rk = json.loads(r["reply"]["text"]).get("r") or []
        except ValueError:
            continue
        out[(r["agent"], r["tick"])] = (cases, rk[0][0] if rk else None)
    return out


pos = collections.Counter(); chance = 0.0; n = 0; same = moved_follow = moved_copy = moved_other = moved = 0; solo = 0
per = []
for f in sorted(glob.glob(S + "*.summary.json")):
    ep = os.path.basename(f)[:-len("_multi.summary.json")]
    s = json.load(open(f)); t = s["evaluation"]["T2_root_cause"]
    ns = json.load(open(N + ep + "_multi.summary.json"))["evaluation"]["T2_root_cause"]
    a, b = calls(N + ep + "_multi.calls.jsonl.gz"), calls(S + ep + "_multi.calls.jsonl.gz")
    p1 = tot = 0
    for k, (cases, pick) in b.items():
        if len(cases) < 2 or pick is None:
            solo += len(cases) < 2
            continue
        n += 1; tot += 1; pos[pick] += 1; chance += 1 / len(cases); p1 += pick == 1
        if k in a and a[k][1] and pick <= len(cases) and a[k][1] <= len(a[k][0]):
            na, nb = a[k][0][a[k][1] - 1], cases[pick - 1]
            if set(a[k][0]) == set(cases) and a[k][0] != cases and a[k][0][0] != cases[0]:
                moved += 1
                if nb == na:
                    moved_follow += 1      # chose the same case the normal run chose, though it moved
                elif pick == 1:
                    moved_copy += 1        # took whatever was now first
                else:
                    moved_other += 1
    per.append((ep[3:22], t.get("top1"), ns.get("top1"), t.get("top3"), ns.get("top3"), t.get("belief_top1"), s["calls"]["calls"], s["calls"]["unusable"], f"{p1}/{tot}"))
print("ep | shuffled top1 | normal | shuffled top3 | normal | belief | calls | unusable | picked pos 1")
for w in per:
    print(" | ".join(map(str, w)))
print("answers with 2+ cases:", n, "position picked:", dict(sorted(pos.items(), key=lambda x: str(x[0]))))
print("share position 1:", round(pos[1] / n, 3), "| by chance would be:", round(chance / n, 3))
print("first case changed by the shuffle:", moved, "| picked what is now first:", moved_copy, "| picked the same case as the normal run:", moved_follow, "| other:", moved_other)
print("answers with one case only:", solo)
