import sys, random, collections, math
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__))); sys.path.insert(0, '.')
from hidden_signal import load, auc, ARMS
D = {a: {r['id']: r for r in load(a)} for a in ARMS}
PL = ['boiler', 'cranfield', 'tep']
def strat(rows, key, y='l1_gr'):
    """within-plant AUC, pooled over plants by number of (pos,neg) pairs"""
    num = den = 0
    for p in PL:
        rs = [r for r in rows if r['plant'] == p and r[key] is not None]
        pos = [r[key] for r in rs if r[y] == 1.0]; neg = [r[key] for r in rs if r[y] == 0.0]
        if pos and neg:
            w = len(pos) * len(neg); num += auc(pos, neg) * w; den += w
    return num / den if den else float('nan')
print("WITHIN-PLANT AUC (line 1 right, group) per plant and stratified")
print("arm | key | boiler | cranfield | tep | stratified")
for a in ARMS:
    rows = list(D[a].values())
    for key in ('p1', 'shift'):
        per = []
        for p in PL:
            rs = [r for r in rows if r['plant'] == p and r[key] is not None]
            pos = [r[key] for r in rs if r['l1_gr'] == 1.0]; neg = [r[key] for r in rs if r['l1_gr'] == 0.0]
            per.append(f"{auc(pos,neg):.3f} ({len(pos)}/{len(neg)})")
        print(a, key, *per, f"{strat(rows,key):.3f}")
print()
for key in ('bel_top', 'bel_margin', 'bel_agree'):
    rows = list(D['m1_q4_0'].values())
    print('code', key, f"stratified {strat(rows,key):.3f}")
# paired bootstrap by episode: 8-bit minus 4-bit, 16-bit minus 4-bit, stratified AUC
def paired(a, b, key, n=2000, seed=20261111):
    ids = sorted(set(D[a]) & set(D[b]))
    by = collections.defaultdict(list)
    for i in ids: by[D[a][i]['ep']].append(i)
    eps = sorted(by); rng = random.Random(seed); ds = []
    pt = strat([D[a][i] for i in ids], key) - strat([D[b][i] for i in ids], key)
    for _ in range(n):
        s = [i for e in (rng.choice(eps) for _ in eps) for i in by[e]]
        v = strat([D[a][i] for i in s], key) - strat([D[b][i] for i in s], key)
        if v == v: ds.append(v)
    ds.sort()
    return pt, ds[int(.025*len(ds))], ds[int(.975*len(ds))], sum(d <= 0 for d in ds)/len(ds)
print("\nPAIRED DIFFERENCE in stratified AUC (episode bootstrap, 2000): point [95% CI], share of resamples <= 0")
for a, b in [('m2_q8_0','m1_q4_0'), ('m2b_bf16','m1_q4_0'), ('m2b_bf16','m2_q8_0'), ('m7_qwen3_17b_q4_0','m1_q4_0'), ('m4_llama31_8b_q4_0','m1_q4_0')]:
    for key in ('p1', 'shift'):
        print(a, '-', b, key, "%.3f [%.3f, %.3f] p<=0: %.3f" % paired(a, b, key))
