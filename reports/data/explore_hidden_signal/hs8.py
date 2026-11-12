import json, math, sys, re, random, collections, statistics as st, io, contextlib
S=__import__('os').path.dirname(__import__('os').path.abspath(__file__))
sys.path.insert(0, S); sys.path.insert(0, '.')
with contextlib.redirect_stdout(io.StringIO()):
    import npu_signal as N
import hidden_signal as H
from hidden_signal import auc
from bench.echo_causes import _right
from bench import echo_test as E
# 1. shuffled-label check (my analysis must give ~0.5 when labels carry nothing), and a permutation p-value
rng = random.Random(1)
def A(rows, y): return auc([r['p1'] for r, v in zip(rows, y) if v == 1], [r['p1'] for r, v in zip(rows, y) if v == 0])
for nm in ['A0_baseline', 'A3_q8_0']:
    rows = N.R[nm]; y = [r['l1_gr'] for r in rows]; obs = A(rows, y); null = []
    for _ in range(5000):
        z = y[:]; rng.shuffle(z); null.append(A(rows, z))
    print(f"NPU {nm:12s} observed AUC {obs:.3f} | labels shuffled: mean {st.mean(null):.3f}, 95% range [{sorted(null)[125]:.3f}, {sorted(null)[4875]:.3f}] | share of shuffles >= observed {sum(v >= obs for v in null)/5000:.4f}")
# 2. cost of the 8-bit file on the NPU (teammate's m2, same prompts, laptop wall-clock per call)
D = N.D
for nm in ['A0_baseline', 'A0b_baseline_again', 'A3_q8_0']:
    lat = [json.loads(l).get('latency_ms') for l in open(f'{D}/{nm}.jsonl')]; lat = [x for x in lat if x]
    print(f"NPU {nm:20s} latency median {st.median(lat)/1000:.2f} s, p90 {sorted(lat)[int(.9*len(lat))]/1000:.2f} s, n={len(lat)}")
# 3. per plant: the model's own pick minus line 1 (group), saved shuffle runs, original order
doc = json.load(open('reports/data/echo_requests.json')); REQ = {r['id']: r for r in doc['requests']}
def first(reply):
    m = re.search(r'"r"\s*:\s*\[\s*\[\s*(\d+)', reply); return int(m.group(1)) if m else None
print("\nmodel's own pick minus line 1 (group, original order), per plant, [95% CI over episodes]")
for arm in H.ARMS:
    per = collections.defaultdict(list)
    for l in open(f'results/echo/R_{arm}.jsonl'):
        r = json.loads(l)
        if r['ordering'] != 'original': continue
        q = REQ[r['id']]; k = first(r['reply']); g = _right(q, r['cases'].get(str(k)) if k else None)[1]; g1 = _right(q, r['cases'].get('1'))[1]
        if g1 is None: continue
        per[q['asset']].append((q['episode'], g - g1))
    cells = []
    for p in ['boiler', 'cranfield', 'tep']:
        by = collections.defaultdict(list)
        for e, d in per[p]: by[e].append(d)
        eps = sorted(by); rg = random.Random(20261111); ds = []
        for _ in range(3000):
            s = [d for e in (rg.choice(eps) for _ in eps) for d in by[e]]; ds.append(st.mean(s))
        ds.sort(); cells.append(f"{p} {st.mean(d for _, d in per[p]):+.3f} [{ds[75]:+.3f},{ds[2925]:+.3f}]")
    print(f"  {arm:22s} " + ' | '.join(cells))
