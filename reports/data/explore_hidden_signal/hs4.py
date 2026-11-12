import sys, random, collections, math, re, json
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__))); sys.path.insert(0, '.')
from hidden_signal import load, auc, ARMS, REQ
D = {a: {r['id']: r for r in load(a)} for a in ARMS}
def A(rows, key, y='l1_gr'):
    rs = [r for r in rows if r.get(key) is not None]
    pos=[r[key] for r in rs if r[y] == 1.0]; neg=[r[key] for r in rs if r[y] == 0.0]
    return auc(pos,neg), len(pos), len(neg)
base = D['m1_q4_0']
print("code-side: belief top-1 == line-1 case, per plant")
for p in ['boiler','cranfield','tep']:
    rows=[r for r in base.values() if r['plant']==p]
    ag=[r for r in rows if r['bel_agree']==1.0]; di=[r for r in rows if r['bel_agree']==0.0]
    f=lambda x: (round(sum(r['l1_gr'] for r in x)/len(x),3) if x else None, len(x))
    print(p, 'AUC %.3f'%A(rows,'bel_agree')[0], '| agree: line1 right, n', f(ag), '| disagree:', f(di))
print("\nBOILER: model p(line1) AUC WITHIN belief-agree strata (does it know more than the belief line says?)")
for a in ARMS:
    rows=[r for r in D[a].values() if r['plant']=='boiler']
    ag=[r for r in rows if r['bel_agree']==1.0]; di=[r for r in rows if r['bel_agree']==0.0]
    mp=lambda x: round(sum(r['p1'] for r in x)/len(x),3)
    print(f"{a:22s} agree: AUC %.3f (%d/%d) mean p1 %s | disagree: AUC %.3f (%d/%d) mean p1 %s | does p1 track agreement? AUC(p1 -> agree) %.3f" % (*A(ag,'p1'), mp(ag), *A(di,'p1'), mp(di), A(rows,'p1','bel_agree')[0]))
