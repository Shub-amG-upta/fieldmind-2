"""Exploratory: rank-aware calibration. score_j = [log p_real(j) - log p_contentfree(j)] + log pi(j),
pi(j) = how often the true group is at rank j, estimated on the OTHER episodes of the same plant
(leave one episode out). No tuned parameter."""
import json, math, sys, re, random, collections, statistics as st
S=__import__('os').path.dirname(__import__('os').path.abspath(__file__))
sys.path.insert(0, S); sys.path.insert(0, '.')
import hidden_signal as H
from bench.echo_causes import _right
def grp(r, j): return _right(r['q'], r['cases'].get(j))[1]
def rank_prior(train, k):
    c = [1.0] * k                                  # add-one smoothing
    for r in train:
        if r['k'] != k: continue
        for j in range(1, k + 1):
            if grp(r, j) == 1.0: c[j - 1] += 1; break
    z = sum(c); return [x / z for x in c]
def run(arm, plants):
    rows = [r for r in H.load(arm) if r['plant'] in plants and r['B']]
    out = {}
    for r in rows:
        tr = [t for t in rows if t['ep'] != r['ep'] and t['plant'] == r['plant']]
        pi = rank_prior(tr, r['k'])
        sc = {j: (r['A'][j] - r['B'][j]) + math.log(pi[j - 1]) for j in range(1, r['k'] + 1)}
        pick = max(sc, key=sc.get)
        model = max(r['A'], key=r['A'].get)
        full = max(r['A'], key=lambda j: r['A'][j] - r['B'][j])
        out[r['id']] = dict(ep=r['ep'], l1=r['l1_gr'], rac=grp(r, pick), model=grp(r, model), full=grp(r, full), moved=float(pick != 1))
    return out
def boot(o, a, b, n=4000, seed=20261111):
    by = collections.defaultdict(list)
    for v in o.values(): by[v['ep']].append(v)
    eps = sorted(by); rng = random.Random(seed); ds = []
    for _ in range(n):
        s = [v for e in (rng.choice(eps) for _ in eps) for v in by[e]]
        ds.append(st.mean(v[a] - v[b] for v in s))
    ds.sort(); return "%+.3f [%+.3f, %+.3f]" % (st.mean(v[a] - v[b] for v in o.values()), ds[int(.025*n)], ds[int(.975*n)])
for label, plants in [('BOILER', ['boiler']), ('ALL THREE PLANTS', ['boiler', 'cranfield', 'tep'])]:
    print(f"\n{label}: group accuracy. line 1 | model's own pick | published calibration (remove the prior) | RANK-AWARE calibration | leaves line 1 | rank-aware minus line 1 [95% CI, episodes]")
    for arm in ['m1_q4_0', 'm2_q8_0', 'm2b_bf16', 'm7_qwen3_17b_q4_0', 'm4_llama31_8b_q4_0', 'm5_qwen25_05b_q4_0', 'm6_gemma3_1b_q4_0']:
        o = run(arm, plants); m = lambda k: st.mean(v[k] for v in o.values())
        print(f"  {arm:22s} n={len(o)} | {m('l1'):.3f} | {m('model'):.3f} | {m('full'):.3f} | {m('rac'):.3f} | {m('moved'):.2f} | {boot(o,'rac','l1')}")
