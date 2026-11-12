import json, math, sys, re, random, collections, statistics as st, io, contextlib
S=__import__('os').path.dirname(__import__('os').path.abspath(__file__))
sys.path.insert(0, S); sys.path.insert(0, '.')
with contextlib.redirect_stdout(io.StringIO()):
    import npu_signal as N
from bench.echo_causes import _right
from bench import echo_test as E
print("NPU: the model's own answer vs line 1 (group), per call, 99 scored boiler prompts x 5 repeats")
for nm in ['A0_baseline', 'A0b_baseline_again', 'A3_q8_0']:
    by = collections.defaultdict(list); dep = n = 0
    for l in open(f'{N.D}/{nm}.jsonl'):
        r = json.loads(l)
        if r['status'] != 'ok': continue
        q = N.nd[r['id']]; m = N.meta[q['episode']]; cases = E.case_lines(q['prompt'])
        req = dict(target=m['target'], evidence_tick=q['tick'], tick_s=m['tick_s'], onset_s=m['onset_s'], asset=m['asset'])
        g1 = _right(req, cases.get(1))[1]
        if g1 is None: continue
        mm = re.match(r'\{"r":\[\[(\d)', r['reply']); k = int(mm.group(1)) if mm else None
        g = _right(req, cases.get(k) if k else None)[1]
        by[q['episode']].append(g - g1); n += 1; dep += (k != 1)
    eps = sorted(by); rg = random.Random(20261111); ds = []
    allv = [d for e in eps for d in by[e]]
    for _ in range(4000):
        ds.append(st.mean([d for e in (rg.choice(eps) for _ in eps) for d in by[e]]))
    ds.sort()
    print(f"  {nm:20s} calls {n} | leaves line 1 on {dep/n:.3f} | own answer minus line 1: {st.mean(allv):+.4f} [{ds[100]:+.4f}, {ds[3900]:+.4f}]")
