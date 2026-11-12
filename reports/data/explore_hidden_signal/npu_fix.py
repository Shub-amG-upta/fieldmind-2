"""Exploratory: can the 1-token confidence be turned into better decisions? NPU runs (m2) and Mac boiler replays."""
import json, math, sys, re, random, collections, statistics as st
S=__import__('os').path.dirname(__import__('os').path.abspath(__file__))
sys.path.insert(0, S); sys.path.insert(0, '.')
from bench.echo_causes import _right
from bench import echo_test as E
import npu_signal as N      # prints its own table first
import hidden_signal as H
print("\n================ FIX TEST ================")
def enrich_npu(rows):
    out = []
    for r in rows:
        q = N.nd[r['id']]; m = N.meta[q['episode']]; cases = E.case_lines(q['prompt'])
        req = dict(target=m['target'], evidence_tick=q['tick'], tick_s=m['tick_s'], onset_s=m['onset_s'], asset=m['asset'])
        b = re.search(r'belief \(from code\): (.*)', q['prompt']); pairs = re.findall(r'([A-Z]+-\d+) (\d\.\d+)', b.group(1)) if b else []
        bt = pairs[0][0] if pairs else None
        out.append(dict(r, bel_gr=_right(req, bt)[1] if bt else 0.0, bel_in_list=float(bt in cases.values()) if bt else 0.0))
    return out
def enrich_mac(rows):
    out = []
    for r in rows:
        b = re.search(r'belief \(from code\): (.*)', r['q']['prompt']); pairs = re.findall(r'([A-Z]+-\d+) (\d\.\d+)', b.group(1)) if b else []
        bt = pairs[0][0] if pairs else None
        out.append(dict(r, bel_gr=_right(r['q'], bt)[1] if bt else 0.0, bel_in_list=float(bt in r['cases'].values()) if bt else 0.0))
    return out
def acc(rows, f): return st.mean(f(r) for r in rows)
def loeo(rows, score='p1'):
    """Policy: where the code's two rankings disagree, keep line 1 if score >= tau, else take the belief's top case.
    tau is chosen on the other episodes (leave one episode out), never on the episode it is applied to."""
    eps = sorted({r['ep'] for r in rows}); got = {}
    for e in eps:
        tr = [r for r in rows if r['ep'] != e and r['bel_agree'] == 0]
        cands = sorted({r[score] for r in tr}) + [9.0]
        best = max(cands, key=lambda t: sum((r['l1_gr'] if r[score] >= t else r['bel_gr']) for r in tr)) if tr else 9.0
        for r in rows:
            if r['ep'] == e:
                got[r['id']] = r['l1_gr'] if (r['bel_agree'] == 1 or r[score] >= best) else r['bel_gr']
    return got
def boot(rows, got, base='l1_gr', n=4000, seed=20261111):
    by = collections.defaultdict(list)
    for r in rows: by[r['ep']].append(r)
    eps = sorted(by); rng = random.Random(seed); ds = []
    pt = st.mean(got[r['id']] - r[base] for r in rows)
    for _ in range(n):
        s = [r for e in (rng.choice(eps) for _ in eps) for r in by[e]]
        ds.append(st.mean(got[r['id']] - r[base] for r in s))
    ds.sort(); return "%+.3f [%+.3f, %+.3f]" % (pt, ds[int(.025*n)], ds[int(.975*n)])
def report(name, rows):
    ag = [r for r in rows if r['bel_agree'] == 1]; di = [r for r in rows if r['bel_agree'] == 0]
    g = loeo(rows)
    print(f"{name:34s} n={len(rows)} eps={len({r['ep'] for r in rows})} | line 1: {acc(rows, lambda r: r['l1_gr']):.3f} | belief top: {acc(rows, lambda r: r['bel_gr']):.3f} | best of the two (oracle): {acc(rows, lambda r: max(r['l1_gr'], r['bel_gr'])):.3f} | GATE: {st.mean(g.values()):.3f}  vs line 1 {boot(rows, g)}  vs belief {boot(rows, g, 'bel_gr')}")
    print(f"{'':34s} disagree stratum n={len(di)}: line 1 {acc(di, lambda r: r['l1_gr']):.3f}, belief {acc(di, lambda r: r['bel_gr']):.3f}, gate {st.mean(g[r['id']] for r in di):.3f} | agree n={len(ag)}: {acc(ag, lambda r: r['l1_gr']):.3f}")
print("NPU runs (boiler dev prompts):")
for nm in ['A0_baseline', 'A0b_baseline_again', 'A3_q8_0']:
    report({'A0_baseline': 'NPU 4-bit', 'A0b_baseline_again': 'NPU 4-bit (again)', 'A3_q8_0': 'NPU 8-bit'}[nm], enrich_npu(N.R[nm]))
print("Mac replays, boiler requests only:")
for a in H.ARMS:
    rows = enrich_mac([r for r in H.load(a) if r['plant'] == 'boiler'])
    report('Mac ' + a, rows)
