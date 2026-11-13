"""Does the 4-bit file lose what the 8-bit file knows? The confirmation of
reports/echo_hidden_signal_exploratory.md, under reports/echo_4bit_prereg.md.

Three tests, each run once per arm (one model file) and scored for pairs of arms that
hold the same weights at two precisions:

  signal    agent prompts: does the probability on line 1 say whether line 1 is right?
            (rows from `run prior`; AUC, pooled and within episode)
  mmluprob  public recall control: does the probability on the chosen letter say whether
            the answer is right? (300 MMLU questions, original order)
  squad     public evidence test (SQuAD v1.1 dev): the question alone, with its passage,
            and with a passage whose answer was swapped for another one. Does the model
            follow the passage?

    build        held-out requests (scored only) from saved dev runs, none shared with set R
    squad-build  the public evidence set from SQuAD's dev-v1.1.json
    run          prior | mmluprob | squad   against one llama-server
    score        signal | mmluprob | squad  with --pair LOW:HIGH for each precision pair

Rows are laptop replays of the model unless the arm ran on the board's NPU lane (labels
starting "npu_"). Mock numbers are not agent results. No energy is measured here.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import re
import string
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench import echo_causes as C  # noqa: E402
from bench import echo_test as E  # noqa: E402

BOOT_SEED = C.BOOT_SEED             # CITED: reports/echo_prereg.md (Amendment A1)
LETTERS = C.LETTERS
# DESIGN: answer cap for a short extracted answer. Range 16-48. Affects only how much of a
# wordy answer is kept; the scoring looks for the answer inside the reply.
SQUAD_CAP = 24
# DESIGN: longest passage kept, in characters. Range 800-2000. Affects which paragraphs are
# eligible; keeps every prompt far below the lanes' 4096-token context.
SQUAD_MAX_CONTEXT = 1200
# DESIGN: longest gold answer kept, in words. Range 3-8. Affects which questions are eligible;
# short answers keep "the reply contains the answer" a fair score.
SQUAD_MAX_ANSWER_WORDS = 5
SQUAD_NONE = "Answer the question with a short phrase.\nQuestion: {q}\nAnswer:"
SQUAD_PASSAGE = ("Answer the question with a short phrase, using the passage.\n"
                 "Passage: {c}\nQuestion: {q}\nAnswer:")


# ------------------------------------------------------------------ AUC
def auc(pos: list[float], neg: list[float]) -> float | None:
    """P(score of a positive > score of a negative), ties counted half (Mann-Whitney),
    from average ranks. None when a class is empty."""
    if not pos or not neg:
        return None
    xs = sorted([(v, 1) for v in pos] + [(v, 0) for v in neg])
    rank_sum, i, n = 0.0, 0, len(xs)
    while i < n:
        j = i
        while j < n and xs[j][0] == xs[i][0]:
            j += 1
        rank_sum += (i + 1 + j) / 2.0 * sum(t[1] for t in xs[i:j])     # ranks i+1 .. j share their mean
        i = j
    return (rank_sum - len(pos) * (len(pos) + 1) / 2.0) / (len(pos) * len(neg))


def _pooled(recs: list[dict]) -> float | None:
    return auc([r["score"] for r in recs if r["y"] == 1.0], [r["score"] for r in recs if r["y"] == 0.0])


def _per_unit(recs: list[dict]) -> dict:
    """{unit: (AUC inside the unit, number of positive-negative pairs)} for units holding both classes."""
    by: dict = {}
    for r in recs:
        by.setdefault(r["unit"], []).append(r)
    out = {}
    for u, rs in by.items():
        pos = [r["score"] for r in rs if r["y"] == 1.0]
        neg = [r["score"] for r in rs if r["y"] == 0.0]
        if pos and neg:
            out[u] = (auc(pos, neg), len(pos) * len(neg))
    return out


def _within(per_unit: dict, units: list) -> float | None:
    """AUC inside units, each unit weighted by its number of pairs; `units` may repeat (a resample)."""
    num = den = 0.0
    for u in units:
        if u in per_unit:
            a, w = per_unit[u]
            num += a * w
            den += w
    return num / den if den else None


def _ci(xs: list[float]) -> list[float] | None:
    if not xs:
        return None
    xs = sorted(xs)
    return [round(xs[int(0.025 * (len(xs) - 1))], 4), round(xs[int(0.975 * (len(xs) - 1))], 4)]


def summarise_auc(recs: list[dict], pairs: list[tuple[str, str]] = (), boot: int = 0,
                  seed: int = BOOT_SEED) -> dict:
    """Per arm: AUC of `score` for `y`, pooled and within unit. Per (low, high) pair, on the
    requests both arms answered: AUC(high) - AUC(low). Intervals resample units (episodes or
    questions) with replacement, the same resample for both arms of a pair."""
    by_label: dict = {}
    for r in recs:
        by_label.setdefault(r["label"], []).append(r)
    res: dict = {"arms": {}, "pairs": {}}

    def stats(rs):
        units = sorted({r["unit"] for r in rs})
        picks = [r["picks_line1"] for r in rs if "picks_line1" in r]
        return {"n": len(rs), "positive": sum(r["y"] == 1.0 for r in rs),
                "negative": sum(r["y"] == 0.0 for r in rs), "units": len(units),
                "line1_share": sum(picks) / len(picks) if picks else None,
                "auc": _pooled(rs), "auc_within_unit": _within(_per_unit(rs), units)}

    def resamples(rs_list):
        """Yields, per draw, the resampled record lists (one per arm) and the drawn units."""
        units = sorted({r["unit"] for rs in rs_list for r in rs})
        bys = []
        for rs in rs_list:
            by: dict = {}
            for r in rs:
                by.setdefault(r["unit"], []).append(r)
            bys.append(by)
        rng = random.Random(seed)
        for _ in range(boot):
            drawn = [rng.choice(units) for _ in units]
            yield [[r for u in drawn for r in by.get(u, [])] for by in bys], drawn

    for label, rs in sorted(by_label.items()):
        entry = stats(rs)
        if boot:
            pu = _per_unit(rs)
            a_draws, w_draws = [], []
            for (sample,), drawn in resamples([rs]):
                a = _pooled(sample)
                if a is not None:
                    a_draws.append(a)
                w = _within(pu, drawn)
                if w is not None:
                    w_draws.append(w)
            entry["auc_ci95"], entry["auc_within_unit_ci95"] = _ci(a_draws), _ci(w_draws)
        res["arms"][label] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in entry.items()}

    for low, high in pairs:
        lo = {r["id"]: r for r in by_label.get(low, [])}
        hi = {r["id"]: r for r in by_label.get(high, [])}
        ids = sorted(set(lo) & set(hi))
        rl, rh = [lo[i] for i in ids], [hi[i] for i in ids]
        entry = {"n_common": len(ids), "auc_low": _pooled(rl), "auc_high": _pooled(rh)}
        entry["diff"] = (None if entry["auc_low"] is None or entry["auc_high"] is None
                         else entry["auc_high"] - entry["auc_low"])
        units = sorted({r["unit"] for r in rl})
        wl, wh = _within(_per_unit(rl), units), _within(_per_unit(rh), units)
        entry["diff_within_unit"] = None if wl is None or wh is None else wh - wl
        if boot and ids:
            pul, puh = _per_unit(rl), _per_unit(rh)
            d_draws, dw_draws = [], []
            for (sl, sh), drawn in resamples([rl, rh]):
                a, b = _pooled(sl), _pooled(sh)
                if a is not None and b is not None:
                    d_draws.append(b - a)
                a, b = _within(pul, drawn), _within(puh, drawn)
                if a is not None and b is not None:
                    dw_draws.append(b - a)
            entry["diff_ci95"], entry["diff_within_unit_ci95"] = _ci(d_draws), _ci(dw_draws)
            entry["share_of_resamples_at_or_below_0"] = (round(sum(d <= 0 for d in d_draws) / len(d_draws), 4)
                                                         if d_draws else None)
        res["pairs"][f"{low}:{high}"] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in entry.items()}
    return res


# ------------------------------------------------------------------ signal (agent prompts)
def signal_rows(doc: dict, rows: list[dict]) -> tuple[list[dict], dict]:
    """One record per scored request with a readable first case line, from `run prior` rows
    (original order): score = the probability on line 1 (over the lines shown), y = line 1
    is in the true group. Also returns {reason: count} of the rows left out."""
    from fieldmind.multi import debias
    reqs = {r["id"]: r for r in doc["requests"]}
    out, skipped = [], {}

    def skip(why):
        skipped[why] = skipped.get(why, 0) + 1
    for row in rows:
        if row["ordering"] != "original":
            continue
        req = reqs.get(row["id"])
        if req is None:
            skip("not in the request file")
            continue
        cases = E.case_lines(req["prompt"])
        exact, group = C._right(req, cases.get(1))
        if group is None:
            skip("not scored")
            continue
        if row["status"] != "ok":
            skip("call failed")
            continue
        lp = {int(a): b for a, b in (row.get("first_line_logprobs") or {}).items()}
        if not lp:
            skip("no first case line")
            continue
        lines = E.ranked_lines(row["reply"] or "")
        out.append({"label": row["label"], "id": row["id"], "unit": req["episode"], "plant": req["asset"],
                    "score": math.exp(debias.normalise(lp, len(cases))[1]), "y": group, "y_exact": exact,
                    "picks_line1": float(bool(lines) and lines[0] == 1)})
    return out, skipped


def held_out(doc: dict, exclude: list[dict], max_per_plant: int = 10 ** 9, seed: int = 0) -> dict:
    """The scored requests of `doc` (a fault, evidence tick at or after its onset), renumbered.
    Refuses the set if any of its episodes or prompts is in an `exclude` request file: a
    confirmation set must be new. max_per_plant: a seeded sample of the scored requests per
    plant, drawn after scoring is decided (default: all, as set H)."""
    old_eps = {r["episode"] for d in exclude for r in d["requests"]}
    old_prompts = {r["prompt"] for d in exclude for r in d["requests"]}
    keep = []
    for r in doc["requests"]:
        if r["episode"] in old_eps or r["prompt"] in old_prompts:
            raise SystemExit(f"episode {r['episode']} (or its prompt) is already in an earlier request set; "
                             "a confirmation set must be new")
        if C._right(r, None)[1] is None:
            continue
        keep.append(dict(r))
    n_scored = len(keep)
    by_plant: dict[str, list] = {}
    for r in keep:
        by_plant.setdefault(r["asset"], []).append(r)
    if any(len(v) > max_per_plant for v in by_plant.values()):
        import random
        keep = []
        for plant in sorted(by_plant):
            pool = by_plant[plant]
            keep += random.Random(f"{seed}:{plant}:held_out").sample(pool, min(max_per_plant, len(pool)))
    for i, r in enumerate(keep):
        r["id"] = i
    return {**doc, "requests": keep, "scored_only": True, "dropped_unscored": len(doc["requests"]) - n_scored,
            "scored_available": n_scored}


def not_held_out(doc: dict, plant: str) -> dict:
    """One plant's scored requests of an EARLIER request set, renumbered, for a test that has no held-out data
    for that plant. Labelled held_out False. Saved model replies are removed: only the code-made prompts are
    reused, and no earlier model row is carried into the new file."""
    keep = [dict(r, saved_replies=[]) for r in doc["requests"]
            if r["asset"] == plant and C._right(r, None)[1] is not None]
    for i, r in enumerate(keep):
        r["id"] = i
    return {"held_out": False, "source_set": doc.get("folders"), "source_seed": doc.get("seed"), "plant": plant,
            "requests": keep, "scored_only": True}


# ------------------------------------------------------------------ mmluprob (public recall control)
def letter_logprobs(token_probs: list | None) -> dict[str, float] | None:
    """{letter: log p} at the token that writes the answer letter, from the server's
    alternatives (raw, before the grammar). None if no such token."""
    for t in token_probs or []:
        if (t.get("token") or "").strip() in LETTERS:
            out: dict = {}
            for alt, lp in [(t.get("token"), t.get("logprob"))] + list(t.get("top") or []):
                a = (alt or "").strip()
                if a in LETTERS and lp is not None:
                    out[a] = max(out.get(a, -math.inf), float(lp))
            return out or None
    return None


def run_mmluprob(doc: dict, backend, out_path: str, label: str, top_logprobs: int = C.TOP_LOGPROBS) -> dict:
    """Each MMLU question once, in its original order, with the letter probabilities saved."""
    done = C._done(out_path)
    counts: dict = {}
    with C._append(out_path) as f:
        for req in doc["requests"]:
            if (label, req["id"], "cyc0") in done:
                continue
            reply = backend.generate(req["prompt"], role="generic", max_tokens=C.MMLU_CAP,
                                     grammar=C.MMLU_GRAMMAR, top_logprobs=top_logprobs)
            counts[reply.status] = counts.get(reply.status, 0) + 1
            C._write(f, {"label": label, "id": req["id"], "ordering": "cyc0", "correct": req["answer"],
                         "status": reply.status, "reply": reply.text,
                         "letter_logprobs": letter_logprobs(reply.token_probs) or {},
                         "model": reply.model, "prefill": reply.prefill_tokens,
                         "decode": reply.decode_tokens, "latency_ms": reply.latency_ms})
    return counts


def mmluprob_rows(doc: dict, rows: list[dict]) -> tuple[list[dict], dict]:
    """One record per answered question: score = the probability on the chosen letter (over
    A-D), y = the letter is right. Each question is its own unit."""
    from fieldmind.multi import debias
    out, skipped = [], {}
    for row in rows:
        letter = (row["reply"] or "").strip()[:1]
        lp = row.get("letter_logprobs") or {}
        why = ("call failed" if row["status"] != "ok" else "no letter" if letter not in LETTERS
               else "no probabilities" if not lp else None)
        if why:
            skipped[why] = skipped.get(why, 0) + 1
            continue
        norm = debias.normalise({LETTERS.index(a) + 1: v for a, v in lp.items()}, len(LETTERS))
        out.append({"label": row["label"], "id": row["id"], "unit": str(row["id"]),
                    "score": math.exp(norm[LETTERS.index(letter) + 1]), "y": float(letter == row["correct"])})
    return out, skipped


# ------------------------------------------------------------------ squad (public evidence test)
_ARTICLES = re.compile(r"\b(a|an|the)\b")


def squad_tokens(s: str) -> list[str]:
    """SQuAD's own answer normalisation (lower case, no punctuation, no articles), as words."""
    s = "".join(ch for ch in s.lower() if ch not in set(string.punctuation))
    return _ARTICLES.sub(" ", s).split()


def contains(reply: str, answers: list[str]) -> bool:
    """True if any answer's words appear in the reply as a run of whole words."""
    r = squad_tokens(reply)
    for a in answers:
        t = squad_tokens(a)
        if t and any(r[i:i + len(t)] == t for i in range(len(r) - len(t) + 1)):
            return True
    return False


def _swap(context: str, golds: list[str], sub: str) -> str:
    for g in sorted(golds, key=len, reverse=True):
        context = context.replace(g, sub)
    return context


def squad_select(raw: dict, n: int, seed: int) -> dict:
    """`n` questions from SQuAD's dev file: the first eligible question of a paragraph (short
    passage, short answer), a seeded sample, each with a `swapped` passage in which every gold
    answer is replaced by another question's answer of the same kind (number or text). A
    question is kept only if no gold answer survives in its swapped passage."""
    pool = []
    for art in raw["data"]:
        for par in art["paragraphs"]:
            ctx = par["context"]
            if len(ctx) > SQUAD_MAX_CONTEXT:
                continue
            for qa in par["qas"]:
                golds = sorted({a["text"].strip() for a in qa.get("answers", []) if a["text"].strip()}, key=len)
                if golds and len(golds[0].split()) <= SQUAD_MAX_ANSWER_WORDS and squad_tokens(golds[0]):
                    pool.append({"qid": qa["id"], "question": qa["question"].strip(), "context": ctx,
                                 "answers": golds})
                    break
    rng = random.Random(seed)
    rng.shuffle(pool)
    kind = lambda s: "num" if any(ch.isdigit() for ch in s) else "text"  # noqa: E731
    chosen, failed = [], 0
    for item in pool:
        if len(chosen) == n:
            break
        g0 = item["answers"][0]
        cands = [o["answers"][0] for o in pool if o is not item and kind(o["answers"][0]) == kind(g0)]
        random.Random(f"{seed}:{item['qid']}").shuffle(cands)
        sub = next((c for c in cands
                    if not contains(c, item["answers"]) and not contains(item["context"], [c])
                    and not any(contains(g, [c]) for g in item["answers"])), None)
        swapped = _swap(item["context"], item["answers"], sub) if sub else ""
        if not sub or contains(swapped, item["answers"]) or not contains(swapped, [sub]):
            failed += 1
            continue
        chosen.append({**item, "id": len(chosen), "substitute": sub, "swapped": swapped})
    return {"seed": seed, "source": "SQuAD v1.1 dev (CC BY-SA 4.0)", "eligible": len(pool),
            "swap_failed": failed, "requests": chosen}


def squad_forms(req: dict) -> dict[str, str]:
    return {"none": SQUAD_NONE.format(q=req["question"]),
            "oracle": SQUAD_PASSAGE.format(c=req["context"], q=req["question"]),
            "swap": SQUAD_PASSAGE.format(c=req["swapped"], q=req["question"])}


def run_squad(doc: dict, backend, out_path: str, label: str) -> dict:
    done = C._done(out_path)
    counts: dict = {}
    with C._append(out_path) as f:
        for req in doc["requests"]:
            for form, prompt in squad_forms(req).items():
                if (label, req["id"], form) in done:
                    continue
                reply = backend.generate(prompt, role="generic", max_tokens=SQUAD_CAP)
                counts[reply.status] = counts.get(reply.status, 0) + 1
                C._write(f, {"label": label, "id": req["id"], "ordering": form, "status": reply.status,
                             "reply": reply.text, "model": reply.model, "prefill": reply.prefill_tokens,
                             "decode": reply.decode_tokens, "latency_ms": reply.latency_ms})
    return counts


def squad_items(doc: dict, rows: list[dict]) -> list[tuple[str, str, str, dict]]:
    """Per question answered in all three forms: (label, "squad", question id, indicators).
    `known` = right with no passage. `swap_follows` = the reply holds the swapped-in answer."""
    reqs = {r["id"]: r for r in doc["requests"]}
    by: dict = {}
    for row in rows:
        if row["status"] == "ok" and row["id"] in reqs:
            by.setdefault((row["label"], row["id"]), {})[row["ordering"]] = row["reply"] or ""
    out = []
    for (label, rid), f in sorted(by.items()):
        if set(f) != {"none", "oracle", "swap"}:
            continue
        req = reqs[rid]
        known = contains(f["none"], req["answers"])
        oracle = float(contains(f["oracle"], req["answers"]))
        follows = float(contains(f["swap"], [req["substitute"]]))
        memory = float(contains(f["swap"], req["answers"]))
        out.append((label, "squad", str(rid), {
            "none_right": float(known), "oracle_right": oracle,
            "use_unknown": None if known else oracle, "keep_known": oracle if known else None,
            "swap_follows": follows, "swap_memory": memory,
            "swap_follows_known": follows if known else None,
            "swap_memory_known": memory if known else None}))
    return out


def paired_means(items: list[tuple[str, str, str, dict]], pairs: list[tuple[str, str]], boot: int = 0,
                 seed: int = BOOT_SEED) -> dict:
    """Per (low, high) pair and indicator: mean(high) - mean(low) over the units where both
    arms have a value, with a 95% interval over resampled units."""
    by: dict = {}
    for label, _, unit, ind in items:
        by.setdefault(label, {})[unit] = ind
    res: dict = {}
    for low, high in pairs:
        lo, hi = by.get(low, {}), by.get(high, {})
        entry: dict = {}
        for key in sorted({k for d in list(lo.values()) + list(hi.values()) for k in d}):
            units = sorted(u for u in set(lo) & set(hi)
                           if lo[u].get(key) is not None and hi[u].get(key) is not None)
            if not units:
                continue
            d = {u: hi[u][key] - lo[u][key] for u in units}
            e = {"diff": round(sum(d.values()) / len(units), 4), "n": len(units)}
            if boot:
                rng = random.Random(seed)
                e["ci95"] = _ci([sum(d[rng.choice(units)] for _ in units) / len(units) for _ in range(boot)])
            entry[key] = e
        res[f"{low}:{high}"] = entry
    return res


# ------------------------------------------------------------------ CLI
def _pairs(spec: list[str]) -> list[tuple[str, str]]:
    out = []
    for s in spec or []:
        low, _, high = s.partition(":")
        if not low or not high:
            raise SystemExit(f"--pair wants LOW:HIGH, got {s!r}")
        out.append((low, high))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="what", required=True)
    s = sub.add_parser("build", help="held-out requests from saved dev run folders")
    s.add_argument("folders", nargs="+")
    s.add_argument("--exclude", nargs="+", required=True, help="earlier request files the set must not share with")
    s.add_argument("--seed", type=int, required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--mock-prompts", action="store_true",
                   help="folders are mock-backend runs, read for their prompts only (echo_test.select)")
    s.add_argument("--max-per-plant", type=int, default=10 ** 9,
                   help="seeded sample size per plant (default: every scored request)")
    s = sub.add_parser("not-held-out", help="one plant's scored requests of an earlier set, labelled not held out")
    s.add_argument("requests")
    s.add_argument("--plant", required=True, choices=["boiler", "cranfield", "tep"])
    s.add_argument("--out", required=True)
    s = sub.add_parser("squad-build", help="the public evidence set from SQuAD's dev-v1.1.json")
    s.add_argument("squad_json")
    s.add_argument("--n", type=int, required=True)
    s.add_argument("--seed", type=int, required=True)
    s.add_argument("--out", required=True)
    s = sub.add_parser("run")
    s.add_argument("test", choices=["prior", "mmluprob", "squad"])
    s.add_argument("requests")
    s.add_argument("--url", required=True)
    s.add_argument("--model", required=True, help="the GGUF file the server loaded (recorded)")
    s.add_argument("--label", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--limit", type=int, default=None, help="first N requests only (pilot)")
    s.add_argument("--lane", default="laptop", help="recorded lane: laptop, or npu for the board's NPU lane")
    s.add_argument("--forms", default="original,content_free", help="prior only: which calls to send")
    s = sub.add_parser("score")
    s.add_argument("test", choices=["signal", "mmluprob", "squad"])
    s.add_argument("requests")
    s.add_argument("rows", nargs="+")
    s.add_argument("--pair", action="append", default=[], help="LOW:HIGH arm labels, e.g. m1_q4_0:m2_q8_0")
    s.add_argument("--bootstrap", type=int, default=0)
    s.add_argument("--boot-seed", type=int, default=BOOT_SEED)
    s.add_argument("--plant", default=None, choices=["boiler", "cranfield", "tep"])
    a = ap.parse_args(argv)

    if a.what == "build":
        doc = held_out(E.select(a.folders, 10 ** 9, a.seed, mock_prompts=a.mock_prompts),
                       [json.loads(Path(p).read_text()) for p in a.exclude], a.max_per_plant, a.seed)
        doc["held_out"] = True
        if a.mock_prompts:
            doc["prompt_source"] = "mock-backend runs (prompts only; no model reply kept)"
        Path(a.out).write_text(json.dumps(doc))
        print(f"{len(doc['requests'])} scored requests from {len({r['episode'] for r in doc['requests']})} "
              f"episodes; {doc['dropped_unscored']} unscored dropped -> {a.out}")
        return 0
    if a.what == "not-held-out":
        doc = not_held_out(json.loads(Path(a.requests).read_text()), a.plant)
        Path(a.out).write_text(json.dumps(doc))
        print(f"{len(doc['requests'])} scored {a.plant} requests from "
              f"{len({r['episode'] for r in doc['requests']})} episodes, NOT held out -> {a.out}")
        return 0
    if a.what == "squad-build":
        doc = squad_select(json.loads(Path(a.squad_json).read_text()), a.n, a.seed)
        Path(a.out).write_text(json.dumps(doc))
        print(f"{len(doc['requests'])} questions (eligible {doc['eligible']}, swap failed {doc['swap_failed']}) -> {a.out}")
        return 0
    doc = json.loads(Path(a.requests).read_text())
    if a.what == "run":
        if a.limit:
            doc = {**doc, "requests": doc["requests"][:a.limit]}
        from fieldmind.runtime.llm_backend import LlamaServerBackend
        be = LlamaServerBackend(url=a.url, lane=a.lane, model_file=a.model, temperature=0.0, seed=0,
                                timeout_s=300.0, cache_prompt=False)
        if a.test == "prior":
            print(C.run_prior(doc, be, a.out, a.label, forms=tuple(a.forms.split(","))))
        else:
            print({"mmluprob": run_mmluprob, "squad": run_squad}[a.test](doc, be, a.out, a.label))
        return 0
    rows = [json.loads(ln) for p in a.rows for ln in Path(p).read_text().splitlines()]
    print("Laptop replays of the model, not NPU results, except arms whose label starts with npu_.")
    if a.test == "squad":
        items = squad_items(doc, rows)
        print(json.dumps({"arms": C.summarise(items, a.bootstrap, a.boot_seed),
                          "pairs": paired_means(items, _pairs(a.pair), a.bootstrap, a.boot_seed)}, indent=1))
        return 0
    recs, skipped = (signal_rows if a.test == "signal" else mmluprob_rows)(doc, rows)
    if a.plant:
        recs = [r for r in recs if r.get("plant") == a.plant]
    out = summarise_auc(recs, _pairs(a.pair), a.bootstrap, a.boot_seed)
    out["rows_left_out"] = skipped
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
