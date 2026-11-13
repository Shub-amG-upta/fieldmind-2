#!/usr/bin/env python3
"""
=============================================================================
 EXTERNAL AUDIT: FaultExplainer (Khan et al., arXiv 2412.14492)
 the echo test on someone else's LLM fault-diagnosis system
 (PLAN_PAPER_B.md item 1; reports/ext_faultexplainer_prereg.md)
=============================================================================

    .venv/bin/python bench/ext_faultexplainer.py build <FaultExplainer checkout> --out requests.json
    .venv/bin/python bench/ext_faultexplainer.py run requests.json --url http://127.0.0.1:8080 \
        --model <gguf> --label <arm> --out rows.jsonl [--forms eval,app] [--only original] [--limit N]
    .venv/bin/python bench/ext_faultexplainer.py score requests.json rows.jsonl ...
    .venv/bin/python bench/ext_faultexplainer.py baseline requests.json --out code_rows.jsonl
    .venv/bin/python bench/ext_faultexplainer.py references requests.json [rows.jsonl ...]

`baseline` ranks the 15 causes by code alone (word overlap between the six T2 features and each
cause's line; reports/ext_faultexplainer_baseline_prereg.md) and writes rows that `score` reads like
a model's. It calls no model: it is the "model switched off" comparison, and a weak one.

FaultExplainer detects a TEP fault with PCA (T2), takes the six variables
with the largest T2 contributions, and asks an LLM which of 15 listed root
causes, IDV(1)..IDV(15), explains them ("root causes included" prompt, top 3).

`build` makes the prompts with FaultExplainer's OWN code at the audited commit:
its prompt strings (backend/prompts.py, loaded as a module) and its
generate_feature_comparison (backend/app.py, that one function, compiled from
the file's source), with the selection steps of its evaluation script
backend/test_explain.py (faults 3-15, first window of 6 consecutive T2
anomalies, top-6 T2 contributions). Nothing of FaultExplainer is copied into
this repository.

Three prompt forms:
  eval         byte-for-byte the evaluation script's GPT-4o prompt. Its LaTeX
               instruction says "start your response with
               \\subsubsection{Fault <i> ...}" where <i> is the TRUE fault
               number, and the root-cause list numbers each cause by its IDV
               number: the prompt carries the answer's index.
  eval_noleak  the same with <i> replaced by NOLEAK_LABEL.
  app          what the interactive app sends (backend/app.py /explain):
               system message + prompt + feature comparison, no LaTeX suffix.

Each form is sent in the orderings of bench.echo_test (original, two seeded
shuffles, line 1 last): the 15 root-cause lines are reordered and renumbered
1..15, each keeping its IDV label. A reply's picks are the first three
distinct IDV(k) it names (PARSE rule, fixed before any call).
=============================================================================
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import runpy
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bench.echo_test import orderings  # noqa: E402

# CITED: github.com/li-group/FaultExplainer, the commit audited (cloned 2026-11-12).
EXT_COMMIT = "2fcfee975a687c350f10909eeccd1ecdd60340be"
# CITED: backend/test_explain.py: `for i in range(3, 16)`, `window_size = 6`, `.head(6)`, `seed = 12345`.
EVAL_FAULTS = tuple(range(3, 16))
WINDOW = 6
TOP_K = 6
SEED = 12345
# CITED: arXiv 2412.14492 Table 1, the aliases the paper credits as correct ("treated as correct as long
# as the model classifies the fault or its alias correctly"). Fault 15's printed alias "5, 15" is kept as
# printed (it names itself; PCA does not detect fault 15, so it is never scored).
ALIASES = {1: (8,), 2: (8,), 3: (9,), 4: (11, 14), 5: (12, 15), 8: (1, 2), 9: (3,), 11: (4, 14),
           12: (5, 15), 14: (4, 11), 15: (5, 15)}
# DESIGN: the label that replaces the true fault number in eval_noleak.
NOLEAK_LABEL = "N"
# DESIGN: answer cap (FaultExplainer sets none). The prompts are 2,470-2,641 tokens with the Llama 3.2
# chat template (counted with llama-server /tokenize, pinned build), and every lane runs -c 4096 (human
# rule), which leaves 1,455. Range 1000-1450. Affects how many long answers are cut (finish_reason "length").
MAX_TOKENS = 1400
FORMS = ("eval", "eval_noleak", "app")
_IDV = re.compile(r"IDV\s*\(\s*(\d{1,2})\s*\)")
_LIST_HEAD = "**Available Root Causes**:\n"


def _feature_comparison(repo: Path):
    """FaultExplainer's generate_feature_comparison, compiled from backend/app.py's own source
    (the module itself imports openai/fastapi at top level, which this audit does not need)."""
    import pandas as pd
    path = repo / "backend" / "app.py"
    tree = ast.parse(path.read_text())
    fn = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "generate_feature_comparison"]
    if len(fn) != 1:
        raise SystemExit(f"{path}: generate_feature_comparison not found exactly once")
    ns = {"os": os, "pd": pd, "__file__": str(path)}
    exec(compile(ast.Module(body=fn, type_ignores=[]), str(path), "exec"), ns)  # noqa: S102
    return ns["generate_feature_comparison"]


def _latex_suffix_fn(repo: Path):
    """test_explain.py's `latex_prompt = ...` expression, compiled from the script's own source and
    evaluated with its loop variables (i, prompt_type, gpt_model): byte-identical by construction."""
    path = repo / "backend" / "test_explain.py"
    found = [n.value for n in ast.walk(ast.parse(path.read_text()))
             if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "latex_prompt" for t in n.targets)]
    if len(found) != 1:
        raise SystemExit(f"{path}: latex_prompt assignment not found exactly once")
    code = compile(ast.Expression(body=found[0]), str(path), "eval")
    return lambda i, model="gpt-4o": eval(code, {"i": i, "prompt_type": "prompt=root causes included,",  # noqa: S307
                                                 "gpt_model": model})


def build(repo: Path) -> dict:
    """One request per PCA-detected fault of the evaluation script, with all three forms."""
    import pandas as pd
    head = (repo / ".git" / "HEAD")
    commit = None
    if head.exists():
        ref = head.read_text().strip()
        commit = (repo / ".git" / ref.split(" ", 1)[1]).read_text().strip() if ref.startswith("ref:") else ref
    if commit != EXT_COMMIT:
        raise SystemExit(f"{repo}: checkout is at {commit}, the audit is registered for {EXT_COMMIT}")
    P = runpy.run_path(str(repo / "backend" / "prompts.py"))
    gfc = _feature_comparison(repo)
    _latex_suffix = _latex_suffix_fn(repo)
    reqs, undetected = [], []
    for i in EVAL_FAULTS:
        fd = pd.read_csv(repo / "frontend" / "public" / f"fault{i}.csv")
        fd["anomaly"] = fd["anomaly"].astype(bool)
        run = fd["anomaly"].rolling(window=WINDOW).sum() == WINDOW
        if not run.any():
            undetected.append(i)
            continue
        idx = run.idxmax()
        t2 = [c for c in fd.columns if c.startswith("t2_") and c != "t2_stat"]
        vals = pd.to_numeric(fd.loc[idx, t2], errors="coerce")
        top = [c.split("t2_")[-1] for c in vals.sort_values(ascending=False).head(TOP_K).index]
        upto = fd.iloc[:idx + 1]
        comparison = gfc({f: upto[f].tolist() for f in top if f in upto.columns}, f"fault{i}.csv")
        body = f"{P['EXPLAIN_ROOT']}\n{comparison}"
        reqs.append({"id": len(reqs), "fault": i, "aliases": list(ALIASES.get(i, ())), "top_features": top,
                     "anomaly_index": int(idx),
                     "prompts": {"eval": P["SYSTEM_MESSAGE"] + body + _latex_suffix(i),
                                 "eval_noleak": P["SYSTEM_MESSAGE"] + body + _latex_suffix(NOLEAK_LABEL),
                                 "app": P["SYSTEM_MESSAGE"] + body}})
    return {"source": "github.com/li-group/FaultExplainer", "commit": EXT_COMMIT, "undetected": undetected,
            "requests": reqs}


def root_lines(prompt: str) -> dict[int, int]:
    """{list line: IDV number} of the prompt's root-cause list."""
    block = prompt.split(_LIST_HEAD, 1)[1]
    out = {}
    for ln in block.splitlines():
        m = re.match(r"(\d+)\.\s+IDV\((\d+)\)", ln)
        if m:
            out[int(m.group(1))] = int(m.group(2))
        elif out and ln.strip():
            break
    return out


def reorder(prompt: str, order: list[int]) -> tuple[str, dict[int, int]]:
    """The prompt with its root-cause lines in `order` (old line numbers), renumbered 1..k;
    every other byte kept. Returns the prompt and {new line: IDV}."""
    head, rest = prompt.split(_LIST_HEAD, 1)
    lines = rest.split("\n")
    idx = [n for n, ln in enumerate(lines) if re.match(r"\d+\.\s+IDV\(\d+\)", ln)]
    if idx != list(range(idx[0], idx[0] + len(idx))):
        raise ValueError("root-cause lines are not contiguous")
    old = {int(re.match(r"(\d+)\.", lines[n]).group(1)): re.sub(r"^\d+\.\s+", "", lines[n]) for n in idx}
    if sorted(order) != sorted(old):
        raise ValueError(f"order {order} is not a permutation of lines {sorted(old)}")
    new = [f"{k}. {old[o]}" for k, o in enumerate(order, 1)]
    out = head + _LIST_HEAD + "\n".join(lines[:idx[0]] + new + lines[idx[-1] + 1:])
    return out, root_lines(out)


def picks(reply: str) -> list[int]:
    """PARSE rule: the first three distinct IDV(k), 1 <= k <= 15, named in the reply, in order."""
    out = []
    for m in _IDV.finditer(reply or ""):
        k = int(m.group(1))
        if 1 <= k <= 15 and k not in out:
            out.append(k)
        if len(out) == 3:
            break
    return out


def _post(url: str, text: str, max_tokens: int, timeout: float) -> dict:
    body = json.dumps({"messages": [{"role": "user", "content": text}], "temperature": 0, "seed": SEED,
                       "max_tokens": max_tokens, "cache_prompt": False}).encode()
    req = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())
    d["_latency_ms"] = (time.time() - t0) * 1000
    return d


def run(doc: dict, url: str, model: str, label: str, out_path: str, forms=FORMS, names=None,
        limit: int | None = None, max_tokens: int = MAX_TOKENS, timeout: float = 900.0, post=_post) -> str:
    """Every request x form x ordering, once, appended to out_path (resumes: keys already there are
    skipped). Records the reply, its picks, tokens, server timings and laptop time."""
    done = set()
    p = Path(out_path)
    if p.exists():
        for ln in p.read_text().splitlines():
            r = json.loads(ln)
            done.add((r["label"], r["id"], r["form"], r["ordering"]))
    n_new = 0
    with p.open("a") as f:
        for req in doc["requests"][:limit]:
            for form in forms:
                for oname, order in orderings(15, req["id"], SEED).items():
                    if names and oname not in names:
                        continue
                    key = (label, req["id"], form, oname)
                    if key in done:
                        continue
                    prompt, lines = reorder(req["prompts"][form], order)
                    row = {"label": label, "model": model, "id": req["id"], "fault": req["fault"], "form": form,
                           "ordering": oname, "lines": {str(k): v for k, v in lines.items()},
                           "laptop_time": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
                    try:
                        d = post(url, prompt, max_tokens, timeout)
                        reply = d["choices"][0]["message"]["content"]
                        row.update(status="ok", reply=reply, picks=picks(reply), usage=d.get("usage"),
                                   timings=d.get("timings"), latency_ms=round(d["_latency_ms"], 1),
                                   finish_reason=d["choices"][0].get("finish_reason"))
                    except Exception as e:                 # recorded, never retried silently
                        row.update(status="error", error=f"{type(e).__name__}: {e}")
                    f.write(json.dumps(row) + "\n")
                    f.flush()
                    n_new += 1
    return f"{n_new} new rows -> {out_path}"


def _right(pick: int | None, fault: int, aliases) -> bool:
    return pick is not None and (pick == fault or pick in aliases)


def score(doc: dict, rows: list[dict]) -> dict:
    """Per label and form: per ordering, parse rate, the share whose first pick is line 1, top-1 and
    top-3 right under the paper's alias rule, the share whose first pick is the fault number written
    in the prompt (eval) or would have been (other forms); and, against `original`, where a shuffled
    first pick went: the same IDV (followed the content) or the same line (followed the position)."""
    reqs = {r["id"]: r for r in doc["requests"]}
    by: dict = {}
    for r in rows:
        if r.get("status") == "ok":
            by.setdefault((r["label"], r["form"]), {}).setdefault(r["ordering"], {})[r["id"]] = r
    out = {}
    for (label, form), ords in sorted(by.items()):
        res = {"orderings": {}, "follow": {}}
        for oname, rs in ords.items():
            n = len(rs)
            parsed = [r for r in rs.values() if r["picks"]]
            line_of = lambda r, k: next((int(ln) for ln, v in r["lines"].items() if v == k), None)  # noqa: E731
            res["orderings"][oname] = {
                "n": n, "parsed": len(parsed),
                "first_is_line1": sum(line_of(r, r["picks"][0]) == 1 for r in parsed),
                "top1_right": sum(_right(r["picks"][0], r["fault"], reqs[r["id"]]["aliases"]) for r in parsed),
                "top3_right": sum(any(_right(k, r["fault"], reqs[r["id"]]["aliases"]) for k in r["picks"])
                                  for r in parsed),
                "first_is_fault_number": sum(r["picks"][0] == r["fault"] for r in parsed)}
        base = ords.get("original", {})
        for oname, rs in ords.items():
            if oname == "original":
                continue
            c = {"content": 0, "position": 0, "neither": 0, "uninformative": 0, "n": 0}
            for rid, r in rs.items():
                b = base.get(rid)
                if not (b and b["picks"] and r["picks"]):
                    continue
                c["n"] += 1
                b_line = next(int(ln) for ln, v in b["lines"].items() if v == b["picks"][0])
                if r["lines"].get(str(b_line)) == b["picks"][0]:
                    c["uninformative"] += 1    # the shuffle left that cause on its line: content = position
                elif r["picks"][0] == b["picks"][0]:
                    c["content"] += 1
                elif r["lines"].get(str(b_line)) == r["picks"][0]:
                    c["position"] += 1
                else:
                    c["neither"] += 1
            res["follow"][oname] = c
        out[f"{label} / {form}"] = res
    return out


# ------------------------------------------------------------------ code-only baseline
# reports/ext_faultexplainer_baseline_prereg.md. A ranking of the 15 causes made by code alone, from
# what the request already holds: the six T2 features in order, and the prompt's own cause list.

# CITED: HANDOFF_BUILD_LIST.md B1 ("6 for rank 1 down to 1 for rank 6"): the weight of the feature at
# T2 rank r is TOP_K + 1 - r.
RANK_WEIGHTS = tuple(range(TOP_K, 0, -1))
# CITED: HANDOFF_BUILD_LIST.md B1 ("at least 3 characters").
MIN_WORD = 3
# DESIGN: English function words only; no process word is in it. Range: this list, or empty. Affects
# nothing on the audited cause list, which holds no function word of 3 letters or more (checked on the
# request file's text, not on any score); it only guards against a feature name that contains one.
STOP = frozenset({"the", "and", "for", "with", "from", "into", "that", "this", "are", "was"})
_CAUSE = re.compile(r"(\d+)\.\s+IDV\((\d+)\)\s*(.*)")


def content_words(text: str) -> set[str]:
    """Lower case, letters only, at least MIN_WORD characters, not in STOP."""
    return {w for w in re.split(r"[^a-z]+", text.lower()) if len(w) >= MIN_WORD and w not in STOP}


def cause_texts(prompt: str) -> dict[int, str]:
    """{IDV number: the text after its label} from the prompt's own root-cause list, in any order."""
    out = {}
    for ln in prompt.split(_LIST_HEAD, 1)[1].splitlines():
        m = _CAUSE.match(ln)
        if m:
            out[int(m.group(2))] = m.group(3)
        elif out and ln.strip():
            break
    return out


def overlap_rank(top_features: list[str], prompt: str) -> tuple[list[int], dict[int, int]]:
    """Every cause's score and the causes ranked by it. A cause scores, for each feature that shares a
    content word with its line, that feature's rank weight. Ties go to the lower IDV number, so the
    result does not depend on where a cause sits in the list."""
    if len(top_features) > len(RANK_WEIGHTS):
        raise ValueError(f"{len(top_features)} features, the rank weights cover {len(RANK_WEIGHTS)}")
    feats = [content_words(f) for f in top_features]
    scores = {idv: sum(w for w, fw in zip(RANK_WEIGHTS, feats) if fw & content_words(text))
              for idv, text in cause_texts(prompt).items()}
    return sorted(scores, key=lambda k: (-scores[k], k)), scores


def baseline(doc: dict, out_path: str, label: str = "code_overlap", forms=FORMS, names=None,
             limit: int | None = None) -> str:
    """One row per request x form x ordering, in `run`'s format, so `score` reads them unchanged. The
    reply is the three top-ranked causes, written as IDV(k) and parsed back by the same PARSE rule."""
    done = set()
    p = Path(out_path)
    if p.exists():
        for ln in p.read_text().splitlines():
            r = json.loads(ln)
            done.add((r["label"], r["id"], r["form"], r["ordering"]))
    n_new = 0
    with p.open("a") as f:
        for req in doc["requests"][:limit]:
            for form in forms:
                for oname, order in orderings(15, req["id"], SEED).items():
                    if (names and oname not in names) or (label, req["id"], form, oname) in done:
                        continue
                    prompt, lines = reorder(req["prompts"][form], order)
                    ranked, scores = overlap_rank(req["top_features"], prompt)
                    reply = ", ".join(f"IDV({k})" for k in ranked[:3])
                    f.write(json.dumps({
                        "label": label, "model": "code: word overlap, no model call", "id": req["id"],
                        "fault": req["fault"], "form": form, "ordering": oname,
                        "lines": {str(k): v for k, v in lines.items()},
                        "laptop_time": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "status": "ok", "reply": reply,
                        "picks": picks(reply), "scores": {str(k): v for k, v in scores.items()},
                        "n_scoring": sum(v > 0 for v in scores.values()), "usage": None, "timings": None,
                        "latency_ms": None, "finish_reason": "code"}) + "\n")
                    n_new += 1
    return f"{n_new} new rows -> {out_path}"


def references(doc: dict, rows: list[dict]) -> dict:
    """The three reference answers of the pre-registration, as counts over the requests:
      uniform           a uniform random pick of three distinct causes (expected value, exact)
      first_three_lines whatever sits on lines 1-3 of each ordering
      most_frequent     per arm, form and ordering: its own three most-named causes as a constant answer
    """
    from math import comb
    reqs = doc["requests"]
    ok = lambda r: {r["fault"], *r["aliases"]}                                    # noqa: E731
    out = {"n": len(reqs),
           "uniform": {"top1_right_expected": round(sum(len(ok(r)) / 15 for r in reqs), 3),
                       "top3_right_expected": round(sum(1 - comb(15 - len(ok(r)), 3) / comb(15, 3) for r in reqs), 3)},
           "first_three_lines": {}, "most_frequent": {}}
    for req in reqs:
        for oname, order in orderings(15, req["id"], SEED).items():
            lines = reorder(req["prompts"]["app"], order)[1]
            c = out["first_three_lines"].setdefault(oname, {"top1_right": 0, "top3_right": 0})
            c["top1_right"] += lines[1] in ok(req)
            c["top3_right"] += any(lines[k] in ok(req) for k in (1, 2, 3))
    by: dict = {}
    for r in rows:
        if r.get("status") == "ok":
            by.setdefault((r["label"], r["form"], r["ordering"]), []).append(r)
    byid = {r["id"]: r for r in reqs}
    for (label, form, oname), rs in sorted(by.items()):
        named, first = {}, {}
        for r in rs:
            for k in r["picks"]:
                named[k] = named.get(k, 0) + 1
            if r["picks"]:
                first[r["picks"][0]] = first.get(r["picks"][0], 0) + 1
        top3 = sorted(named, key=lambda k: (-named[k], k))[:3]
        top1 = sorted(first, key=lambda k: (-first[k], k))[:1]
        out["most_frequent"].setdefault(f"{label} / {form}", {})[oname] = {
            "answer": top3, "first": top1, "n": len(rs),
            "top1_right": sum(bool(top1) and top1[0] in ok(byid[r["id"]]) for r in rs),
            "top3_right": sum(any(k in ok(byid[r["id"]]) for k in top3) for r in rs)}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="what", required=True)
    s = sub.add_parser("baseline", help="code-only ranking of the causes, written as rows `score` reads")
    s.add_argument("requests")
    s.add_argument("--out", required=True)
    s.add_argument("--label", default="code_overlap")
    s.add_argument("--limit", type=int, default=None)
    s = sub.add_parser("references", help="uniform, first-three-lines and most-frequent reference answers")
    s.add_argument("requests")
    s.add_argument("rows", nargs="*")
    s = sub.add_parser("build")
    s.add_argument("repo")
    s.add_argument("--out", required=True)
    s = sub.add_parser("run")
    s.add_argument("requests")
    s.add_argument("--url", required=True)
    s.add_argument("--model", required=True, help="the model file the server loaded (recorded)")
    s.add_argument("--label", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--forms", default=",".join(FORMS))
    s.add_argument("--only", default=None, help="comma-separated orderings")
    s.add_argument("--limit", type=int, default=None)
    s.add_argument("--max-tokens", type=int, default=MAX_TOKENS)
    s = sub.add_parser("score")
    s.add_argument("requests")
    s.add_argument("rows", nargs="+")
    a = ap.parse_args(argv)
    if a.what == "build":
        doc = build(Path(a.repo))
        Path(a.out).write_text(json.dumps(doc, indent=1))
        print(f"{len(doc['requests'])} requests (faults {[r['fault'] for r in doc['requests']]}); "
              f"not detected by PCA: {doc['undetected']}")
    elif a.what == "baseline":
        print("Code only: no model is called. Not an agent result and not FaultExplainer's own method.")
        print(baseline(json.loads(Path(a.requests).read_text()), a.out, label=a.label, limit=a.limit))
    elif a.what == "references":
        doc = json.loads(Path(a.requests).read_text())
        rows = [json.loads(ln) for p in a.rows for ln in Path(p).read_text().splitlines()]
        print(json.dumps(references(doc, rows), indent=1))
    elif a.what == "run":
        doc = json.loads(Path(a.requests).read_text())
        print(run(doc, a.url, a.model, a.label, a.out, forms=a.forms.split(","),
                  names=set(a.only.split(",")) if a.only else None, limit=a.limit, max_tokens=a.max_tokens))
    else:
        doc = json.loads(Path(a.requests).read_text())
        rows = [json.loads(ln) for p in a.rows for ln in Path(p).read_text().splitlines()]
        print(json.dumps(score(doc, rows), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
