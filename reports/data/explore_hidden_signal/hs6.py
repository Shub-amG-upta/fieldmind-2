import json, math, sys, re, collections, statistics as st, io, contextlib
S=__import__('os').path.dirname(__import__('os').path.abspath(__file__))
sys.path.insert(0, S); sys.path.insert(0, '.')
import hidden_signal as H
from bench import echo_test as E
M1 = {r['id']: r for r in H.load('m1_q4_0')}; M2 = {r['id']: r for r in H.load('m2_q8_0')}
ids = sorted(i for i in M1 if M1[i]['ep'] == 'dev_D01_high_cv_coal')
print("D01_high_cv_coal (true case RCA-07). tick | side | line-1 case | right? | p1 4-bit | p1 8-bit | facts (short)")
for i in ids:
    q = M1[i]['q']; p = q['prompt']
    facts = re.search(r'FACTS:\n(.*?)\n\nRETRIEVED', p, re.S).group(1).split('\n')
    side = p.split('\n')[0][:40]
    l1 = re.search(r'RETRIEVED CASES:\n1\. (\S+) (.*?);', p)
    print(f"{q['evidence_tick']:4d} | {side[19:34]:15s} | {l1.group(1)} | {int(M1[i]['l1_gr'])} | {M1[i]['p1']:.2f} | {M2[i]['p1']:.2f} | " + ' // '.join(f[3:70] for f in facts[:3]))
