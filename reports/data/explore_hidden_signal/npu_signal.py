"""Exploratory: the hidden-signal test on NPU runs (teammate's m2: A0, A0b = Q4_0; A3 = Q8_0)."""
import json, math, sys, re, random, collections, statistics as st
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__))); sys.path.insert(0, '.')
from hidden_signal import auc
from bench.echo_causes import _right
from bench import echo_test as E
D = __import__('os').environ.get('ND_M2_DIR', 'results/nd/m2_settings')
nd = {r['id']: r for r in json.load(open(f'{D}/nd_requests.json'))['requests']}
eq = json.load(open('reports/data/echo_requests.json'))['requests']
meta = {r['episode']: r for r in eq}
DIG = {str(15 + d): d for d in range(0, 10)}      # hypothesis: token id of digit d is 15+d; checked below
def first_line(row, k):
    """{line: logprob} at the first digit token of a reply that starts with a ranked case; None otherwise."""
    m = re.match(r'\{"r":\[\[(\d)', row['reply'])
    if not m: return None, None
    for t in row['tokens']:
        if str(t['id']) in DIG:
            if DIG[str(t['id'])] != int(m.group(1)): return 'MISMATCH', None
            lp = {DIG[i]: v for i, v in t['top'].items() if i in DIG and 1 <= DIG[i] <= k}
            return int(m.group(1)), lp
    return None, None
def norm(lp, k):
    fl = min(lp.values()) - 1.0
    full = {j: lp.get(j, fl) for j in range(1, k + 1)}
    z = math.log(sum(math.exp(v) for v in full.values()))
    return {j: v - z for j, v in full.items()}
def load(name):
    per = collections.defaultdict(list); mism = empty = n = 0
    for l in open(f'{D}/{name}.jsonl'):
        r = json.loads(l)
        if r['status'] != 'ok': continue
        q = nd[r['id']]; cases = E.case_lines(q['prompt']); k = len(cases); n += 1
        pick, lp = first_line(r, k)
        if pick == 'MISMATCH': mism += 1; continue
        if pick is None or not lp or 1 not in lp and len(lp) == 0: empty += 1; continue
        per[r['id']].append((pick, math.exp(norm(lp, k)[1])))
    rows = []
    for rid, v in per.items():
        q = nd[rid]; m = meta[q['episode']]; cases = E.case_lines(q['prompt'])
        req = dict(target=m['target'], evidence_tick=q['tick'], tick_s=m['tick_s'], onset_s=m['onset_s'], asset=m['asset'])
        ex, gr = _right(req, cases.get(1))
        if gr is None: continue
        b = re.search(r'belief \(from code\): (.*)', q['prompt']); pairs = re.findall(r'([A-Z]+-\d+) (\d\.\d+)', b.group(1)) if b else []
        rows.append(dict(id=rid, ep=q['episode'], k=len(cases), l1_gr=gr, l1_ex=ex, p1=st.mean(p for _, p in v),
                         line1_share=st.mean(float(pk == 1) for pk, _ in v), reps=len(v),
                         bel_agree=float(bool(pairs) and pairs[0][0] == cases.get(1))))
    return rows, dict(calls=n, digit_mismatch=mism, no_first_line=empty)
def A(rows, key, y='l1_gr'):
    return auc([r[key] for r in rows if r[y] == 1.0], [r[key] for r in rows if r[y] == 0.0])
R = {}
for name in ['A0_baseline', 'A0b_baseline_again', 'A3_q8_0']:
    R[name], info = load(name)
    rows = R[name]; pos = sum(r['l1_gr'] for r in rows)
    ag = [r for r in rows if r['bel_agree'] == 1]; di = [r for r in rows if r['bel_agree'] == 0]
    print(f"{name:20s} {info} | scored prompts {len(rows)} (line 1 right {int(pos)}, wrong {len(rows)-int(pos)}) | picks line 1 {st.mean(r['line1_share'] for r in rows):.3f} | mean p(line1) {st.mean(r['p1'] for r in rows):.3f}")
    print(f"{'':20s} AUC p(line1)->line 1 right: {A(rows,'p1'):.3f} | exact {A(rows,'p1','l1_ex'):.3f} | within belief-agree {A(ag,'p1'):.3f} (n={len(ag)}) | within disagree {A(di,'p1'):.3f} (n={len(di)}) | control: belief agrees {A(rows,'bel_agree'):.3f} | control: k {A([dict(r, kk=-r['k']) for r in rows],'kk'):.3f}")
def paired(a, b, n=4000, seed=20261111, unit='id'):
    A_ = {r['id']: r for r in R[a]}; B_ = {r['id']: r for r in R[b]}; ids = sorted(set(A_) & set(B_))
    by = collections.defaultdict(list)
    for i in ids: by[A_[i][unit] if unit != 'id' else i].append(i)
    us = sorted(by); rng = random.Random(seed); ds = []
    pt = A([A_[i] for i in ids], 'p1') - A([B_[i] for i in ids], 'p1')
    for _ in range(n):
        s = [i for u in (rng.choice(us) for _ in us) for i in by[u]]
        v = A([A_[i] for i in s], 'p1') - A([B_[i] for i in s], 'p1')
        if v == v: ds.append(v)
    ds.sort(); return "%.3f [%.3f, %.3f], share<=0 %.3f (n=%d %ss)" % (pt, ds[int(.025*len(ds))], ds[int(.975*len(ds))], sum(d <= 0 for d in ds)/len(ds), len(us), unit)
print("\nPAIRED AUC difference on the NPU:")
print(" 8-bit - 4-bit (A3 - A0), resampling prompts :", paired('A3_q8_0', 'A0_baseline'))
print(" 8-bit - 4-bit (A3 - A0b), resampling prompts:", paired('A3_q8_0', 'A0b_baseline_again'))
print(" 8-bit - 4-bit (A3 - A0), resampling episodes:", paired('A3_q8_0', 'A0_baseline', unit='ep'))
print(" noise floor: 4-bit vs 4-bit again (A0b - A0) :", paired('A0b_baseline_again', 'A0_baseline'))
