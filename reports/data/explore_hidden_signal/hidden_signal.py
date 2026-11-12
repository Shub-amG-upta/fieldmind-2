"""Exploratory (NOT pre-registered): does the model's first-line probability carry
information the argmax throws away? Uses only saved E7 rows (original order + content-free).
Laptop replays, not NPU results."""
import json, math, random, re, sys, collections
sys.path.insert(0, '.')
from bench.echo_causes import _right, _truth
from bench import echo_test as E
from fieldmind.multi.debias import normalise

doc = json.load(open('reports/data/echo_requests.json'))
REQ = {r['id']: r for r in doc['requests']}
ARMS = ['m5_qwen25_05b_q4_0', 'm6_gemma3_1b_q4_0', 'm7_qwen3_17b_q4_0', 'm1_q4_0', 'm2_q8_0', 'm2b_bf16',
        'm3_qwen25_7b_q4_0', 'm4_llama31_8b_q4_0']
BELIEF = re.compile(r'belief \(from code\): (.*)')


def auc(pos, neg):
    if not pos or not neg:
        return float('nan')
    w = 0.0
    for p in pos:
        for n in neg:
            w += 1.0 if p > n else 0.5 if p == n else 0.0
    return w / (len(pos) * len(neg))


def load(arm):
    rows = {}
    for l in open(f'results/echo/prior_{arm}.jsonl'):
        r = json.loads(l)
        rows.setdefault(r['id'], {})[r['ordering']] = r
    out = []
    for rid, d in rows.items():
        q = REQ[rid]
        cases = E.case_lines(q['prompt'])
        k = len(cases)
        a = d['original'].get('first_line_logprobs') or {}
        b = d.get('content_free', {}).get('first_line_logprobs') or {}
        if not a:
            continue
        A = normalise({int(x): v for x, v in a.items()}, k)
        B = normalise({int(x): v for x, v in b.items()}, k) if b else None
        ex, gr = _right(q, cases.get(1))
        if gr is None:
            continue
        m = BELIEF.search(q['prompt'])
        pairs = re.findall(r'([A-Z]+-\d+) (\d\.\d+)', m.group(1)) if m else []
        bel = [float(v) for _, v in pairs]
        belcase = [c for c, _ in pairs]
        s = sorted(A.values(), reverse=True)
        out.append(dict(id=rid, ep=q['episode'], plant=q['asset'], k=k, A=A, B=B, cases=cases, q=q,
                        l1_ex=ex, l1_gr=gr, p1=math.exp(A[1]),
                        shift=(A[1] - B[1]) if B else None,
                        margin=(s[0] - s[1]) if k > 1 else 9.0,
                        bel_top=bel[0] if bel else None,
                        bel_margin=(bel[0] - bel[1]) if len(bel) > 1 else (bel[0] if bel else None),
                        bel_agree=float(bool(belcase) and belcase[0] == cases.get(1))))
    return out


def boot_auc(rows, key, y, n=1000, seed=20261111):
    eps = sorted({r['ep'] for r in rows})
    by = collections.defaultdict(list)
    for r in rows:
        by[r['ep']].append(r)
    rng = random.Random(seed)
    def one(rs):
        rs = [r for r in rs if r[key] is not None]
        return auc([r[key] for r in rs if r[y] == 1.0], [r[key] for r in rs if r[y] == 0.0])
    pt = one(rows)
    bs = []
    for _ in range(n):
        samp = [r for e in (rng.choice(eps) for _ in eps) for r in by[e]]
        v = one(samp)
        if v == v:
            bs.append(v)
    bs.sort()
    return pt, bs[int(0.025 * len(bs))], bs[int(0.975 * len(bs))]


if __name__ == '__main__':
    print("AUC: does the score predict that the code's line 1 is right (group)?  0.5 = no information")
    print("arm | n | model p(line1) | evidence shift (real - content-free) | code belief top | code belief margin | belief agrees with line 1")
    for arm in ARMS:
        rows = load(arm)
        f = lambda t: f"{t[0]:.3f} [{t[1]:.2f},{t[2]:.2f}]"
        cells = [f(boot_auc(rows, k, 'l1_gr')) for k in ('p1', 'shift', 'bel_top', 'bel_margin', 'bel_agree')
                 if any(r[k] is not None for r in rows)]
        print(arm, len(rows), ' | '.join(cells))
