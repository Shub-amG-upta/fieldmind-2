import json, math, sys, re, random, collections, statistics as st, io, contextlib
S=__import__('os').path.dirname(__import__('os').path.abspath(__file__))
sys.path.insert(0, S); sys.path.insert(0, '.')
with contextlib.redirect_stdout(io.StringIO()):
    import npu_signal as N
import hidden_signal as H
from hidden_signal import auc
def within(rows, key='p1', y='l1_gr'):
    num = den = 0; used = []
    for e in sorted({r['ep'] for r in rows}):
        rs = [r for r in rows if r['ep'] == e]
        pos = [r[key] for r in rs if r[y] == 1]; neg = [r[key] for r in rs if r[y] == 0]
        if pos and neg:
            w = len(pos)*len(neg); num += auc(pos, neg)*w; den += w; used.append(f"{e.replace('dev_','')[:14]}:{auc(pos,neg):.2f}({len(pos)}/{len(neg)})")
    return (num/den if den else float('nan')), used
print("WITHIN-EPISODE AUC (only episodes where line 1 is right at some ticks and wrong at others)")
for nm, lab in [('A0_baseline','NPU 4-bit'), ('A0b_baseline_again','NPU 4-bit again'), ('A3_q8_0','NPU 8-bit')]:
    a, u = within(N.R[nm]); print(f"{lab:18s} {a:.3f}", u)
for a_ in ['m1_q4_0','m2_q8_0','m2b_bf16','m7_qwen3_17b_q4_0','m3_qwen25_7b_q4_0','m4_llama31_8b_q4_0']:
    rows = [r for r in H.load(a_) if r['plant']=='boiler']; a, u = within(rows); print(f"Mac {a_:20s} {a:.3f}", u)
# episode-level picture on the NPU
print("\nNPU per episode: line-1 right share | mean p(line1) 4-bit | 8-bit")
A0 = {r['id']: r for r in N.R['A0_baseline']}; A3 = {r['id']: r for r in N.R['A3_q8_0']}
for e in sorted({r['ep'] for r in A0.values()}):
    ids = [i for i in A0 if A0[i]['ep']==e and i in A3]
    print(f"  {e:26s} n={len(ids):2d} right {st.mean(A0[i]['l1_gr'] for i in ids):.2f} | {st.mean(A0[i]['p1'] for i in ids):.3f} | {st.mean(A3[i]['p1'] for i in ids):.3f}")
ids = sorted(set(A0)&set(A3)); x=[A0[i]['p1'] for i in ids]; y=[A3[i]['p1'] for i in ids]
mx,my=st.mean(x),st.mean(y); cor=sum((a-mx)*(b-my) for a,b in zip(x,y))/math.sqrt(sum((a-mx)**2 for a in x)*sum((b-my)**2 for b in y))
print(f"p(line1) across prompts: 4-bit sd {st.pstdev(x):.3f}, 8-bit sd {st.pstdev(y):.3f}, correlation 4-bit vs 8-bit {cor:.3f}")
for lab, R_ in [('4-bit', A0), ('8-bit', A3)]:
    r1=[R_[i]['p1'] for i in ids if R_[i]['l1_gr']==1]; r0=[R_[i]['p1'] for i in ids if R_[i]['l1_gr']==0]
    print(f"  {lab}: mean p(line1) when line 1 is right {st.mean(r1):.3f}, when wrong {st.mean(r0):.3f}, gap {st.mean(r1)-st.mean(r0):+.3f}")
# MMLU: consistency across the 4 rotations as a confidence proxy (public data, saved replies only)
print("\nMMLU (300 public questions, Mac replays): does 'same option in the other 3 rotations' predict that the original answer is right?")
for arm in ['m1_q4_0','m2_q8_0','m2b_bf16','m5_qwen25_05b_q4_0','m6_gemma3_1b_q4_0','m3_qwen25_7b_q4_0','m4_llama31_8b_q4_0']:
    rows = collections.defaultdict(dict)
    for l in open(f'results/echo/mmlu_{arm}.jsonl'):
        r = json.loads(l); rows[r['id']][r['ordering']] = r
    pos=[];neg=[]
    for d in rows.values():
        o = d['cyc0']; pick = o['shown'].get(o['reply'].strip())
        agree = sum(d[k]['shown'].get(d[k]['reply'].strip()) == pick for k in ('cyc1','cyc2','cyc3'))
        (pos if o['reply'].strip()==o['correct'] else neg).append(agree)
    print(f"  {arm:22s} accuracy {len(pos)/300:.3f} | AUC {auc(pos,neg):.3f}")
