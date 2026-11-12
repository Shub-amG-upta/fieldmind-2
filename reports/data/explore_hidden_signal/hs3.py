import sys, random, collections, math, re, json
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__))); sys.path.insert(0, '.')
from hidden_signal import load, auc, ARMS, REQ
D = {a: {r['id']: r for r in load(a)} for a in ARMS}
# what is in the prompts, per plant
c = collections.defaultdict(collections.Counter)
for r in REQ.values():
    p = r['prompt']; m = re.search(r'NOTES AND RECORDS.*?<<<\n(.*?)>>>', p, re.S)
    body = m.group(1) if m else ''
    c[r['asset']]['has notes block'] += bool(m)
    c[r['asset']]['has a [note' ] += '[note' in body
    c[r['asset']]['n'] += 1
print({k: dict(v) for k, v in c.items()})
def A(rows, key, y='l1_gr'):
    rs = [r for r in rows if r.get(key) is not None]
    return auc([r[key] for r in rs if r[y] == 1.0], [r[key] for r in rs if r[y] == 0.0])
print("\nBOILER ONLY. AUC for 'line 1 is right (group)'. Controls first (code-side or content-free), then the model.")
rows = [r for r in D['m1_q4_0'].values() if r['plant'] == 'boiler']
for r in rows: r['kneg'] = -r['k']
print('controls: number of lines (fewer=higher)', round(A(rows,'kneg'),3), '| code belief top', round(A(rows,'bel_top'),3), '| belief margin', round(A(rows,'bel_margin'),3), '| belief agrees with line 1', round(A(rows,'bel_agree'),3))
for a in ARMS:
    rows = [r for r in D[a].values() if r['plant'] == 'boiler']
    for r in rows:
        r['prior1'] = math.exp(r['B'][1]) if r['B'] else None
        r['note'] = '[note' in r['q']['prompt']
    byk = []
    for k in (2, 3, 4):
        rk = [r for r in rows if r['k'] == k]
        byk.append(f"k={k}: {A(rk,'p1'):.2f} (n={len(rk)})")
    wn = [r for r in rows if r['note']]; nn = [r for r in rows if not r['note']]
    print(f"{a:22s} content-free prior {A(rows,'prior1'):.3f} | real p(line1) {A(rows,'p1'):.3f} | shift {A(rows,'shift'):.3f} | exact-case: p1 {A(rows,'p1','l1_ex'):.3f} | {' '.join(byk)} | with a note {A(wn,'p1'):.2f} (n={len(wn)}), no note {A(nn,'p1'):.2f} (n={len(nn)})")
