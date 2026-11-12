#!/usr/bin/env python3
"""
=============================================================================
 ECHO CAUSES  --  why does the model copy line 1?  (PLAN_TWO_BRANCHES.md E6-E8)
 Rules: reports/echo_causes_prereg.md. Laptop replays, NOT NPU results.
=============================================================================

Three tests on top of bench/echo_test.py's replay (same requests, same rebuilt
grammar, temperature 0, seed 0, no prompt cache, the diagnostician cap):

  relabel   E6  label vs position. The case lines get labels that are not
                1..k in display order, so "the first line shown", "the line
                labelled 1" and "the code's top case" come apart:
                  relabel_orig  code's order shown; label 1 is NOT on the first line
                  relabel_shuf  a shuffled order (code's top case not first); label 1
                                not on the first line, and (k >= 3) not on the top case
                The answer is a label; it is mapped back to its case.
  prior     E7  the model's preference before reading (Zhao et al. 2021). Per
                request, two calls with token log-probabilities: the real prompt
                (original order) and its content-free copy (every fact, case, note
                and record line "N/A", fieldmind.multi.debias.content_free). The
                calibrated pick is argmax(log p - log prior) (debias.debiased_first).
  mmlu      E8  control: the same model on public MMLU questions (the
                nondeterminism paper's 300, reports/data/nd_public_requests.json),
                options in the 4 cyclic orders. Does it read when it knows?

    python bench/echo_causes.py run relabel reports/data/echo_requests.json --url URL --model GGUF --label L --out F
    python bench/echo_causes.py run prior   reports/data/echo_requests.json --url URL --model GGUF --label L --out F
    python bench/echo_causes.py run mmlu    reports/data/nd_public_requests.json --url URL --model GGUF --label L --out F
    python bench/echo_causes.py score relabel|prior|mmlu|vote|hint <requests> <rows.jsonl ...> [--bootstrap 2000]
    python bench/echo_causes.py score ceiling reports/data/echo_requests.json [--bootstrap 2000]

On saved data, no model calls (E1-E3): ceiling (is the true case in the list at all?), vote (self-
consistency over the 4 saved orderings of results/echo/R_*.jsonl), hint (shuffled deviations against
a random other line).

Every run resumes: a (label, id, form) already in the output file is not sent
again. Intervals: 95%, resampling EPISODES (relabel, prior) or QUESTIONS (mmlu),
seed 20261111.
=============================================================================
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bench import echo_test as E  # noqa: E402
from bench.evaluator import _groups  # noqa: E402

TOP_LOGPROBS = 20          # DESIGN: llama-server's default number of alternatives (debias.DEFAULTS). Range 5-20.
MMLU_CAP = 4               # CITED: bench/nd_public.py ANSWER_CAP (one letter + end of turn)
MMLU_GRAMMAR = 'root ::= "A" | "B" | "C" | "D"'   # CITED: bench/nd_public.py GRAMMAR
LETTERS = ("A", "B", "C", "D")
BOOT_SEED = 20261111       # CITED: reports/echo_prereg.md (Amendment A1)


# ------------------------------------------------------------------ E6 relabel
def _case_block(prompt: str) -> tuple[str, dict[int, str], str]:
    head, rest = prompt.split("RETRIEVED CASES:\n", 1)
    block, tail = re.split(r"(?=\n\s*\n)", rest, maxsplit=1)
    old = {}
    for ln in block.splitlines():
        m = re.match(r"(\d+)\.\s(.*)", ln)
        if m:
            old[int(m.group(1))] = m.group(2)
    return head, old, tail


def relabel(prompt: str, display: list[int], labels: list[int]) -> tuple[str, dict[int, str], dict[int, int]]:
    """The prompt with its case lines shown in `display` order (old line numbers), the
    i-th shown line labelled labels[i]. Returns the prompt, {label: case id} and
    {label: shown position (1-based)}. Every other byte is kept."""
    head, old, tail = _case_block(prompt)
    k = len(old)
    if sorted(display) != list(range(1, k + 1)) or sorted(labels) != list(range(1, k + 1)):
        raise ValueError(f"display {display} / labels {labels} are not permutations of 1..{k}")
    body = "\n".join(f"{lab}. {old[o]}" for lab, o in zip(labels, display))
    cases = {lab: old[o].split()[0] for lab, o in zip(labels, display)}
    positions = {lab: i for i, lab in enumerate(labels, 1)}
    return f"{head}RETRIEVED CASES:\n{body}{tail}", cases, positions


def relabel_forms(k: int, rid: int, seed: int) -> dict[str, tuple[list[int], list[int]]]:
    """{form: (display order, labels)}; seeded per request. See the module docstring."""
    rng = random.Random(f"relabel:{seed}:{rid}")
    base = list(range(1, k + 1))

    def labels_for(display, avoid_top):
        while True:
            lab = base[:]
            rng.shuffle(lab)
            if lab[0] == 1:
                continue
            if avoid_top and k >= 3 and lab[display.index(1)] == 1:
                continue
            return lab
    out = {"relabel_orig": (base, labels_for(base, False))}
    disp = base[:]
    while disp[0] == 1:
        rng.shuffle(disp)
    out["relabel_shuf"] = (disp, labels_for(disp, True))
    return out


def run_relabel(doc: dict, backend, out_path: str, label: str) -> dict:
    from fieldmind.multi import grammar
    done = _done(out_path)
    counts: dict = {}
    with _append(out_path) as f:
        for req in doc["requests"]:
            gbnf = grammar.to_gbnf(E.rules_for(req["prompt"]))
            k = len(E.case_lines(req["prompt"]))
            top = E.case_lines(req["prompt"])[1]
            for form, (disp, labs) in relabel_forms(k, req["id"], doc["seed"]).items():
                if (label, req["id"], form) in done:
                    continue
                prompt, cases, pos = relabel(req["prompt"], disp, labs)
                reply = backend.generate(prompt, role="diagnostician", max_tokens=E.DIAGNOSTICIAN_CAP, grammar=gbnf)
                counts[reply.status] = counts.get(reply.status, 0) + 1
                _write(f, {"label": label, "id": req["id"], "ordering": form, "display": disp, "labels": labs,
                           "cases": cases, "positions": pos, "top_case": top, "status": reply.status,
                           "reply": reply.text, "model": reply.model, "prefill": reply.prefill_tokens,
                           "decode": reply.decode_tokens, "latency_ms": reply.latency_ms})
    return counts


def relabel_items(doc: dict, rows: list[dict]) -> list[tuple[str, str, str, dict]]:
    """(label, form, episode, indicators) per answered row."""
    reqs = {r["id"]: r for r in doc["requests"]}
    out = []
    for row in rows:
        lines = E.ranked_lines(row["reply"] or "") if row["status"] == "ok" else None
        if not lines:
            continue
        req = reqs[row["id"]]
        cases = {int(a): b for a, b in row["cases"].items()}
        pos = {int(a): b for a, b in row["positions"].items()}
        lab = lines[0]
        pick = cases.get(lab)
        k = len(cases)
        first_lab = next(a for a, p in pos.items() if p == 1)
        distinct = len({cases[first_lab], cases[1], row["top_case"]}) == 3
        ind = {"first_shown": float(pos.get(lab) == 1), "label1": float(lab == 1),
               "top_case": float(pick == row["top_case"]), "chance": 1.0 / k, "distinct": float(distinct)}
        for key in ("first_shown", "label1", "top_case"):
            ind[f"{key}_distinct"] = ind[key] if distinct else None
        ind["chance_distinct"] = 1.0 / k if distinct else None
        right, right_g = _right(req, pick)
        ind["right"], ind["right_group"] = right, right_g
        out.append((row["label"], row["ordering"], req["episode"], ind))
    return out


# ------------------------------------------------------------------ E7 prior
def run_prior(doc: dict, backend, out_path: str, label: str, top_logprobs: int = TOP_LOGPROBS,
              forms: tuple = ("original", "content_free")) -> dict:
    """`forms` limits which of the two calls are sent (bench/echo_4bit.py sends only
    "original" on the board, where the content-free call is not needed)."""
    from fieldmind.multi import debias, grammar
    done = _done(out_path)
    counts: dict = {}
    with _append(out_path) as f:
        for req in doc["requests"]:
            k = len(E.case_lines(req["prompt"]))
            for form, prompt in (("original", req["prompt"]), ("content_free", debias.content_free(req["prompt"]))):
                if form not in forms:
                    continue
                if (label, req["id"], form) in done:
                    continue
                gbnf = grammar.to_gbnf(E.rules_for(prompt))
                reply = backend.generate(prompt, role="diagnostician", max_tokens=E.DIAGNOSTICIAN_CAP,
                                         grammar=gbnf, top_logprobs=top_logprobs)
                counts[reply.status] = counts.get(reply.status, 0) + 1
                lp = debias.first_line_logprobs(reply.token_probs, k)
                _write(f, {"label": label, "id": req["id"], "ordering": form, "status": reply.status,
                           "reply": reply.text, "first_line_logprobs": {str(a): b for a, b in (lp or {}).items()},
                           "model": reply.model, "prefill": reply.prefill_tokens,
                           "decode": reply.decode_tokens, "latency_ms": reply.latency_ms})
    return counts


def prior_items(doc: dict, rows: list[dict]) -> list[tuple[str, str, str, dict]]:
    """(label, "calibrate", episode, indicators) per request with both calls read."""
    import math
    from fieldmind.multi import debias
    reqs = {r["id"]: r for r in doc["requests"]}
    by: dict = {}
    for row in rows:
        by.setdefault((row["label"], row["id"]), {})[row["ordering"]] = row
    out = []
    for (label, rid), forms in sorted(by.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        o, c = forms.get("original"), forms.get("content_free")
        if not o or not c or o["status"] != "ok" or c["status"] != "ok":
            continue
        req = reqs[rid]
        cases = E.case_lines(req["prompt"])
        k = len(cases)
        lp = {int(a): b for a, b in o["first_line_logprobs"].items()}
        pr = {int(a): b for a, b in c["first_line_logprobs"].items()}
        lines = E.ranked_lines(o["reply"] or "")
        if not lp or not pr or not lines:
            continue
        lpn, prn = debias.normalise(lp, k), debias.normalise(pr, k)
        cal = debias.debiased_first(lpn, prn, prefer=lines[0])
        ind = {"prior_line1": math.exp(prn[1]), "prior_argmax_line1": float(max(prn, key=prn.get) == 1),
               "model_line1": float(lines[0] == 1), "cal_line1": float(cal == 1),
               "moved": float(cal != lines[0]), "chance": 1.0 / k}
        for name, line in (("model", lines[0]), ("cal", cal), ("line1", 1)):
            r, g = _right(req, cases.get(line))
            ind[f"{name}_right"], ind[f"{name}_right_group"] = r, g
        for name in ("cal", "model"):              # paired per request, so the interval is of the difference
            for sfx in ("", "_group"):
                x, y = ind[f"{name}_right{sfx}"], ind[f"line1_right{sfx}"]
                ind[f"{name}_minus_line1{sfx}"] = None if x is None else x - y
        out.append((label, "calibrate", req["episode"], ind))
    return out


# ------------------------------------------------------------------ E8 mmlu
_OPT = re.compile(r"(?m)^([ABCD])\. (.*)$")


def mmlu_options(prompt: str) -> dict[str, str]:
    opts = dict(_OPT.findall(prompt))
    if sorted(opts) != list(LETTERS):
        raise ValueError("prompt does not show options A-D")
    return opts


def mmlu_forms(prompt: str, answer: str) -> dict[str, tuple[str, str, dict[str, str]]]:
    """{form: (prompt, correct letter, {shown letter: original letter})} for the 4 cyclic
    orders (cyc0 is the original): each option appears once at each letter."""
    opts = mmlu_options(prompt)
    out = {}
    for s in range(4):
        shown = {LETTERS[i]: LETTERS[(i + s) % 4] for i in range(4)}
        text = _OPT.sub(lambda m: f"{m.group(1)}. {opts[shown[m.group(1)]]}", prompt)
        correct = next(a for a, b in shown.items() if b == answer)
        out[f"cyc{s}"] = (text, correct, shown)
    return out


def run_mmlu(doc: dict, backend, out_path: str, label: str) -> dict:
    done = _done(out_path)
    counts: dict = {}
    with _append(out_path) as f:
        for req in doc["requests"]:
            for form, (prompt, correct, shown) in mmlu_forms(req["prompt"], req["answer"]).items():
                if (label, req["id"], form) in done:
                    continue
                reply = backend.generate(prompt, role="generic", max_tokens=MMLU_CAP, grammar=MMLU_GRAMMAR)
                counts[reply.status] = counts.get(reply.status, 0) + 1
                _write(f, {"label": label, "id": req["id"], "ordering": form, "shown": shown,
                           "correct": correct, "status": reply.status, "reply": reply.text,
                           "model": reply.model, "prefill": reply.prefill_tokens,
                           "decode": reply.decode_tokens, "latency_ms": reply.latency_ms})
    return counts


def mmlu_items(doc: dict, rows: list[dict]) -> list[tuple[str, str, str, dict]]:
    """Per answered row: (label, form, question id, indicators); plus one "all_orders" item
    per question answered in all 4 orders (invariance; invariance among the questions
    the original order got right)."""
    out, picks = [], {}
    for row in rows:
        letter = (row["reply"] or "").strip()[:1]
        if row["status"] != "ok" or letter not in LETTERS:
            continue
        orig = row["shown"][letter]
        picks.setdefault((row["label"], row["id"]), {})[row["ordering"]] = (orig, letter == row["correct"])
        out.append((row["label"], row["ordering"], str(row["id"]),
                    {"right": float(letter == row["correct"]), "letter_A": float(letter == "A"), "chance": 0.25}))
    for (label, qid), v in picks.items():
        if len(v) == 4:
            same = float(len({p for p, _ in v.values()}) == 1)
            known = v.get("cyc0", (None, False))[1]
            out.append((label, "all_orders", str(qid), {"invariance": same,
                                                        "invariance_if_right_orig": same if known else None}))
    return out


# ------------------------------------------------------------------ saved data (E1-E3), no model calls
def _truth(req: dict):
    """(scored, target, target group, case -> group map) by the evaluator's rule."""
    tgt = req["target"]
    if tgt in (None, "NONE") or req["evidence_tick"] * req["tick_s"] < req["onset_s"]:
        return False, None, None, None
    gmap, held, held_ids = _groups(req["asset"])
    return True, tgt, (held.get(tgt) if tgt in held_ids else gmap.get(tgt, tgt)), gmap


def ceiling_items(doc: dict) -> list[tuple[str, str, str, dict]]:
    """E1: on scored requests, is the true case (and its group) among the case lines at
    all, and where? The most any reader of these lines could reach. Grouped by plant
    and pooled; no model output is read."""
    out = []
    for req in doc["requests"]:
        scored, tgt, tg, gmap = _truth(req)
        if not scored:
            continue
        cases = E.case_lines(req["prompt"])
        pos = next((n for n, c in sorted(cases.items()) if c == tgt), None)
        posg = next((n for n, c in sorted(cases.items()) if gmap.get(c) == tg), None)
        ind = {"case_in_list": float(pos is not None), "group_in_list": float(posg is not None),
               "line1_right": float(pos == 1), "line1_right_group": float(posg == 1),
               "lines": float(len(cases))}
        for j in range(1, 5):
            ind[f"case_at_line{j}"] = float(pos == j)
        for form in (req["asset"], "pooled"):
            out.append(("retrieval", form, req["episode"], ind))
    return out


def _answers_by_request(doc: dict, rows: list[dict]) -> dict:
    """{(label, id): {ordering: [case ids in ranked order]}} from echo_test replay rows."""
    out: dict = {}
    for row in rows:
        lines = E.ranked_lines(row["reply"] or "") if row["status"] == "ok" else None
        if not lines:
            continue
        cases = {int(a): b for a, b in row["cases"].items()}
        ranked = [cases[x] for x in lines if x in cases]
        if ranked:
            out.setdefault((row["label"], row["id"]), {})[row["ordering"]] = ranked
    return out


def vote_items(doc: dict, rows: list[dict]) -> list[tuple[str, str, str, dict]]:
    """E2: self-consistency over the 4 saved orderings of each request (no new calls).
    vote: the rank-1 case named most often (a tie keeps the original order's pick);
    borda: fieldmind.multi.debias.borda over the 4 rankings, mapped to the original
    lines (ties keep the original order). Each against line 1 and the original pick,
    paired per request. Only requests answered in all 4 orderings."""
    from fieldmind.multi import debias
    reqs = {r["id"]: r for r in doc["requests"]}
    names = list(E.orderings(2, 0, 0))
    out = []
    for (label, rid), by in sorted(_answers_by_request(doc, rows).items(), key=lambda kv: (kv[0][0], kv[0][1])):
        if any(n not in by for n in names):
            continue
        req = reqs[rid]
        scored, tgt, tg, gmap = _truth(req)
        if not scored:
            continue
        orig = E.case_lines(req["prompt"])
        line_of = {c: n for n, c in orig.items()}
        firsts = [by[n][0] for n in names]
        counts = {c: firsts.count(c) for c in firsts}
        best = max(counts.values())
        vote = by["original"][0] if counts.get(by["original"][0]) == best else \
            next(c for c in firsts if counts[c] == best)
        rankings = [[line_of[c] for c in by[n] if c in line_of] for n in names]
        borda = orig[debias.borda(rankings, len(orig))[0]]
        picks = {"vote": vote, "borda": borda, "orig": by["original"][0], "line1": orig[1]}
        ind = {}
        for name, case in picks.items():
            ind[f"{name}_right"] = float(case == tgt)
            ind[f"{name}_right_group"] = float(gmap.get(case) == tg)
        for name in ("vote", "borda", "orig"):
            for sfx in ("", "_group"):
                ind[f"{name}_minus_line1{sfx}"] = ind[f"{name}_right{sfx}"] - ind[f"line1_right{sfx}"]
        out.append((label, "vote", req["episode"], ind))
    return out


def hint_items(doc: dict, rows: list[dict]) -> list[tuple[str, str, str, dict]]:
    """E3: in the two shuffled orderings, when the model leaves line 1, is its pick
    right more often than a uniform pick among the other lines would be? Per
    deviation: right, the random expectation, and their paired difference."""
    reqs = {r["id"]: r for r in doc["requests"]}
    out = []
    for row in rows:
        if row["ordering"] not in ("shuffle_a", "shuffle_b") or row["status"] != "ok":
            continue
        lines = E.ranked_lines(row["reply"] or "")
        if not lines or lines[0] == 1:
            continue
        req = reqs[row["id"]]
        scored, tgt, tg, gmap = _truth(req)
        if not scored:
            continue
        cases = {int(a): b for a, b in row["cases"].items()}
        pick, others = cases.get(lines[0]), [c for n, c in cases.items() if n != 1]
        ind = {"dev_right": float(pick == tgt), "dev_right_group": float(gmap.get(pick) == tg),
               "dev_random": sum(c == tgt for c in others) / len(others),
               "dev_random_group": sum(gmap.get(c) == tg for c in others) / len(others)}
        ind["dev_minus_random"] = ind["dev_right"] - ind["dev_random"]
        ind["dev_minus_random_group"] = ind["dev_right_group"] - ind["dev_random_group"]
        out.append((row["label"], "shuffled", req["episode"], ind))
    return out


# ------------------------------------------------------------------ shared
def _right(req: dict, pick: str | None) -> tuple[float | None, float | None]:
    """Exact and group credit on scored requests (fault, evidence tick at or after onset;
    the evaluator's T2 rule, as echo_test.score); None elsewhere."""
    tgt = req["target"]
    if tgt in (None, "NONE") or req["evidence_tick"] * req["tick_s"] < req["onset_s"]:
        return None, None
    gmap, held, held_ids = _groups(req["asset"])
    tg = held.get(tgt) if tgt in held_ids else gmap.get(tgt, tgt)
    return float(pick == tgt), float(pick is not None and gmap.get(pick) == tg)


def summarise(items: list[tuple[str, str, str, dict]], boot: int = 0, seed: int = BOOT_SEED) -> dict:
    """{label: {form: {indicator: mean (n)}}}, with 95% intervals over resampled units
    (episodes or questions) when boot > 0. None values are left out of a mean."""
    groups: dict = {}
    for label, form, unit, ind in items:
        groups.setdefault(label, {}).setdefault(form, []).append((unit, ind))

    def means(rows):
        acc: dict = {}
        for _, ind in rows:
            for key, v in ind.items():
                if v is not None:
                    s = acc.setdefault(key, [0.0, 0])
                    s[0] += v
                    s[1] += 1
        return {key: (round(s / n, 4), n) for key, (s, n) in acc.items()}
    res: dict = {}
    for label, forms in groups.items():
        for form, rows in forms.items():
            m = means(rows)
            entry = {key: {"mean": v, "n": n} for key, (v, n) in m.items()}
            if boot:
                by_unit: dict = {}
                for unit, ind in rows:
                    by_unit.setdefault(unit, []).append((unit, ind))
                units = sorted(by_unit)
                rng = random.Random(seed)
                draws: dict = {}
                for _ in range(boot):
                    sample = [r for u in (rng.choice(units) for _ in units) for r in by_unit[u]]
                    for key, (v, _) in means(sample).items():
                        draws.setdefault(key, []).append(v)
                for key, xs in draws.items():
                    xs.sort()
                    entry[key]["ci95"] = [xs[int(0.025 * (len(xs) - 1))], xs[int(0.975 * (len(xs) - 1))]]
            res.setdefault(label, {})[form] = entry
    return res


def _done(out_path: str) -> set:
    done = set()
    if Path(out_path).exists():
        for ln in Path(out_path).read_text().splitlines():
            r = json.loads(ln)
            done.add((r["label"], r["id"], r["ordering"]))
    return done


def _append(out_path: str):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    return open(out_path, "a")


def _write(f, rec: dict) -> None:
    f.write(json.dumps(rec) + "\n")
    f.flush()


RUN = {"relabel": run_relabel, "prior": run_prior, "mmlu": run_mmlu}
ITEMS = {"relabel": relabel_items, "prior": prior_items, "mmlu": mmlu_items,
         "ceiling": lambda doc, rows: ceiling_items(doc), "vote": vote_items, "hint": hint_items}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="what", required=True)
    s = sub.add_parser("run")
    s.add_argument("test", choices=sorted(RUN))
    s.add_argument("requests")
    s.add_argument("--url", required=True)
    s.add_argument("--model", required=True, help="the GGUF file the server loaded (recorded)")
    s.add_argument("--label", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--limit", type=int, default=None, help="first N requests only (pilot)")
    s = sub.add_parser("score")
    s.add_argument("test", choices=sorted(ITEMS))
    s.add_argument("requests")
    s.add_argument("rows", nargs="*", help="replay rows (none for ceiling)")
    s.add_argument("--bootstrap", type=int, default=0)
    s.add_argument("--boot-seed", type=int, default=BOOT_SEED)
    s.add_argument("--plant", default=None, choices=["boiler", "cranfield", "tep"])
    a = ap.parse_args(argv)
    doc = json.loads(Path(a.requests).read_text())
    if a.what == "run":
        if a.limit:
            doc = {**doc, "requests": doc["requests"][:a.limit]}
        from fieldmind.runtime.llm_backend import LlamaServerBackend
        be = LlamaServerBackend(url=a.url, lane="laptop", model_file=a.model, temperature=0.0, seed=0,
                                timeout_s=300.0, cache_prompt=False)
        print(RUN[a.test](doc, be, a.out, a.label))
        return 0
    rows = [json.loads(ln) for p in a.rows for ln in Path(p).read_text().splitlines()]
    if a.plant:
        doc, rows = E.only_plant(doc, rows, a.plant)
    print("Laptop replay of the model, not an NPU result.")
    print(json.dumps(summarise(ITEMS[a.test](doc, rows), a.bootstrap, a.boot_seed), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
