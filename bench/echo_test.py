#!/usr/bin/env python3
"""
=============================================================================
 ECHO TEST  --  does the diagnostician choose a case, or repeat line 1?
 (HANDOFF_ECHO.md step 1; PLAN_LAPTOP_ECHO_SCHED.md stage 1)
=============================================================================

    .venv/bin/python bench/echo_test.py saved results/benchmarks/cranfield_dev_v3 ...
    .venv/bin/python bench/echo_test.py saved <folders> --allow-reporting   (descriptive only)
    .venv/bin/python bench/echo_test.py saved <folders> --json out.json

Reads saved run files (<folder>/*.run.json.gz) and, for every diagnostician
answer that ranks at least one case line, records which prompt lines it put
first. Per run folder, lane and model it reports:

  line1      share of answers whose rank-1 line is line 1 of RETRIEVED CASES
  identity   share whose ranked lines are exactly 1, 2, ..., k
  chance     mean of 1 / (case lines shown): the line-1 share of a uniform pick
  and, on fault episodes from fault onset onward (evidence tick * tick period
  >= fault_onset_t, the evaluator's T2 rule, dated by the answer's evidence tick):
  line1 right     line 1 is the true case (exact) / in the true look-alike group
  deviations      answers whose rank-1 is NOT line 1, and of those
    right         the pick is the true case / in the true group
    line 1 right  line 1 would have been
    random        a uniform pick among the other lines would be (expected value)

Look-alike groups and held-out targets come from bench.evaluator._groups, the
map the evaluator scores with, so the two cannot drift apart.

Dev episodes only by default: an episode counts when its id is a folder of one
of DEV_DIRS (generated locally; gitignored). Reporting episodes are refused
unless --allow-reporting, and those rows are marked REPORTING: descriptive,
never used to decide anything (CLAUDE.md dev set rule).

Saved board runs measure the board's model; nothing here calls a model.
Mock-backend runs measure the mock, which ranks by retrieval score: their
line-1 share is 1 by construction, not a model result.
=============================================================================
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:                   # run as a script from anywhere
    sys.path.insert(0, str(ROOT))

from bench.evaluator import _groups  # noqa: E402

DEV_DIRS = ("data/episodes_dev", "data/episodes_cranfield_dev",
            "data/episodes_tep_dev", "data/episodes_tep_board")

_CASE_LINE = re.compile(r"^(\d+)\.\s+(\S+)")


def dev_ids(root: Path = ROOT) -> set[str]:
    """Episode ids of every dev set present on this machine."""
    out = set()
    for d in DEV_DIRS:
        p = root / d
        if p.is_dir():
            out.update(c.name for c in p.iterdir() if c.is_dir())
    return out


def case_lines(prompt: str) -> dict[int, str]:
    """{line number: case id} from the RETRIEVED CASES block (up to its first blank line)."""
    if "RETRIEVED CASES:" not in prompt:
        return {}
    block = prompt.split("RETRIEVED CASES:", 1)[1].lstrip("\n")
    block = re.split(r"\n\s*\n", block, maxsplit=1)[0]
    out = {}
    for line in block.splitlines():
        m = _CASE_LINE.match(line.strip())
        if m:
            out[int(m.group(1))] = m.group(2)
    return out


def ranked_lines(raw_reply: str) -> list[int] | None:
    """The case lines of a line-number answer, in ranked order; None if unreadable.

    Two formats: the diagnosis answer {"r":[[line,[facts]],...]} and the explain
    (rank-only) answer {"r":[line,...]}."""
    try:
        r = json.loads(raw_reply).get("r")
    except (ValueError, AttributeError, TypeError):
        return None
    if not isinstance(r, list):
        return None
    return [x[0] if isinstance(x, list) else x for x in r
            if (isinstance(x, list) and x and isinstance(x[0], int)) or isinstance(x, int)]


def answers(run: dict):
    """One dict per diagnostician answer that ranks at least one shown case line."""
    gt = run["ground_truth"]
    target = gt.get("root_cause_id")
    fault = target not in (None, "NONE")
    gmap = held = held_ids = None
    tgroup = None
    if fault:
        gmap, held, held_ids = _groups(gt.get("asset", "boiler"))
        # the evaluator's rule (t2_root_cause): a held-out target scores by its group
        tgroup = held.get(target) if target in held_ids else gmap.get(target, target)
    onset = gt.get("fault_onset_t") or 0
    tick_s = float(gt.get("tick_period_s", 30.0))
    for a in run["assessments"]:
        for e in a.get("envelopes") or []:
            if e.get("agent") != "diagnostician" or e.get("status") != "ok":
                continue
            cases = case_lines(e.get("prompt") or "")
            lines = ranked_lines(e.get("raw_reply") or "")
            if not cases or not lines:
                continue
            ev_tick = e.get("tick", a["tick"])
            yield {"lane": e.get("backend"), "model": Path(str(e.get("model"))).name,
                   "lines": lines, "cases": cases,
                   "scored": fault and ev_tick * tick_s >= onset,
                   "target": target, "tgroup": tgroup, "gmap": gmap}


def _new() -> dict:
    keys = ("n", "line1", "identity", "chance", "n_scored", "l1_right", "l1_right_g",
            "dev", "dev_right", "dev_right_g", "dev_l1_right", "dev_l1_right_g",
            "dev_random", "dev_random_g")
    return {k: 0 for k in keys}


def add(c: dict, ans: dict) -> None:
    """Fold one answer into the counters c."""
    lines, cases = ans["lines"], ans["cases"]
    k = len(cases)
    c["n"] += 1
    c["line1"] += lines[0] == 1
    c["identity"] += lines == list(range(1, len(lines) + 1))
    c["chance"] += 1.0 / k
    if not ans["scored"]:
        return
    tgt, tg, gmap = ans["target"], ans["tgroup"], ans["gmap"]
    in_group = lambda case: case is not None and gmap.get(case) == tg  # noqa: E731
    c["n_scored"] += 1
    l1 = cases.get(1)
    c["l1_right"] += l1 == tgt
    c["l1_right_g"] += in_group(l1)
    if lines[0] != 1:
        pick = cases.get(lines[0])
        others = [v for n, v in cases.items() if n != 1]
        c["dev"] += 1
        c["dev_right"] += pick == tgt
        c["dev_right_g"] += in_group(pick)
        c["dev_l1_right"] += l1 == tgt
        c["dev_l1_right_g"] += in_group(l1)
        if others:
            c["dev_random"] += sum(v == tgt for v in others) / len(others)
            c["dev_random_g"] += sum(in_group(v) for v in others) / len(others)


def summarise(c: dict) -> dict:
    """Shares from the counters (None where the denominator is 0)."""
    def r(x, n):
        return round(x / n, 3) if n else None
    n, s, d = c["n"], c["n_scored"], c["dev"]
    return {"n": n, "line1": r(c["line1"], n), "identity": r(c["identity"], n),
            "chance": r(c["chance"], n), "n_scored": s,
            "line1_right": r(c["l1_right"], s), "line1_right_group": r(c["l1_right_g"], s),
            "deviations": d, "deviation_share": r(d, s),
            "dev_right": r(c["dev_right"], d), "dev_right_group": r(c["dev_right_g"], d),
            "dev_line1_right": r(c["dev_l1_right"], d),
            "dev_line1_right_group": r(c["dev_l1_right_g"], d),
            "dev_random": r(c["dev_random"], d), "dev_random_group": r(c["dev_random_g"], d)}


def scan(folders: list[str], dev: set[str] | None = None,
         allow_reporting: bool = False) -> list[dict]:
    """One row per (folder, lane, model). Refuses reporting episodes unless allowed."""
    dev = dev_ids() if dev is None else dev
    rows = []
    for folder in folders:
        groups: dict[tuple, dict] = {}
        reporting = set()
        for f in sorted(Path(folder).glob("*.run.json.gz")):
            run = json.loads(gzip.decompress(f.read_bytes()))
            ep = run["episode_id"]
            if ep not in dev:
                if not allow_reporting:
                    raise SystemExit(f"{f}: episode {ep} is not in a dev set ({', '.join(DEV_DIRS)}); "
                                     "pass --allow-reporting for a descriptive-only row")
                reporting.add(ep)
            for ans in answers(run):
                add(groups.setdefault((ans["lane"], ans["model"]), _new()), ans)
        for (lane, model), c in sorted(groups.items(), key=lambda kv: str(kv[0])):
            rows.append({"folder": Path(folder).name, "lane": lane, "model": model,
                         "reporting_episodes": sorted(reporting), **summarise(c)})
    return rows


def table(rows: list[dict]) -> str:
    def f(x):
        return "–" if x is None else (f"{x:.3f}" if isinstance(x, float) else str(x))
    head = ("| run | lane | set | answers | line1 | identity | chance | scored | line1 right "
            "(exact / group) | deviations | dev right (exact / group) | line1 right on those | "
            "random other line |")
    out = [head, "|" + "---|" * 13]
    for r in rows:
        out.append(f"| {r['folder']} | {r['lane']} | {'REPORTING' if r['reporting_episodes'] else 'dev'} "
                   f"| {r['n']} | {f(r['line1'])} | {f(r['identity'])} | {f(r['chance'])} "
                   f"| {r['n_scored']} | {f(r['line1_right'])} / {f(r['line1_right_group'])} "
                   f"| {r['deviations']} | {f(r['dev_right'])} / {f(r['dev_right_group'])} "
                   f"| {f(r['dev_line1_right'])} / {f(r['dev_line1_right_group'])} "
                   f"| {f(r['dev_random'])} / {f(r['dev_random_group'])} |")
    return "\n".join(out)


# ------------------------------------------------------------------ replay
# Stage 2 (PLAN_LAPTOP_ECHO_SCHED.md steps 8-12): the same saved dev requests sent
# again, with the case lines in other orders, to a running llama-server. The
# request is rebuilt as the system sent it (bench/nd_repeat.py's rule): the
# saved prompt, the diagnostician cap, temperature 0, seed 0, no prompt cache,
# and the grammar for the lines the prompt shows. Only the RETRIEVED CASES block
# is reordered and renumbered; every other byte of the prompt stays.

DIAGNOSTICIAN_CAP = 60     # CITED: configs/base.yaml multi.answer_caps.diagnostician
_SECTIONS = re.compile(r"FACTS:\n(.*?)\n\s*\nRETRIEVED CASES:\n(.*?)\n\s*\n.*?<<<\n(.*?)>>>", re.S)


def line_counts(prompt: str) -> tuple[int, int, int]:
    """(fact lines, case lines, note and record lines) the prompt shows."""
    m = _SECTIONS.search(prompt)
    if not m:
        raise ValueError("prompt has no FACTS / RETRIEVED CASES / notes blocks")
    return tuple(sum(bool(re.match(r"\d+\.\s", ln.strip())) for ln in b.splitlines())
                 for b in m.groups())


def has_letters(prompt: str) -> bool:
    """The v2 answer format: the answer starts with the first case's group letter."""
    return '{"g":' in prompt.split("Answer format", 1)[-1]


def strip_letters(prompt: str) -> str:
    """A letters-on prompt with the letters taken out (the v2 -> v3 difference)."""
    p = re.sub(r" \[group [A-Z]\]", "", prompt)
    return p.replace('{"g":"<group letter of your first case>",', "{").replace('{"g":"A",', "{")


def rules_for(prompt: str, with_group: bool | None = None) -> dict:
    from fieldmind.multi import grammar
    if with_group is None:
        with_group = has_letters(prompt)
    n_facts, n_cases, n_context = line_counts(prompt)
    letters = (re.findall(r"\[group ([A-Z])\]", prompt.split("RETRIEVED CASES:", 1)[1])[:n_cases]
               if with_group else [])
    return grammar.diagnosis(n_facts, n_cases, n_context, letters, with_group=with_group)


def reorder(prompt: str, order: list[int]) -> tuple[str, dict[int, str]]:
    """The prompt with its case lines shown in `order` (old line numbers), renumbered
    1..k, and {new line: case id}."""
    head, rest = prompt.split("RETRIEVED CASES:\n", 1)
    block, tail = re.split(r"(?=\n\s*\n)", rest, maxsplit=1)
    old = {}
    for ln in block.splitlines():
        m = re.match(r"(\d+)\.\s(.*)", ln)
        if m:
            old[int(m.group(1))] = m.group(2)
    if sorted(order) != sorted(old):
        raise ValueError(f"order {order} is not a permutation of lines {sorted(old)}")
    new = "\n".join(f"{i}. {old[o]}" for i, o in enumerate(order, 1))
    cases = {i: old[o].split()[0] for i, o in enumerate(order, 1)}
    return f"{head}RETRIEVED CASES:\n{new}{tail}", cases


def orderings(k: int, rid: int, seed: int) -> dict[str, list[int]]:
    """original; two seeded shuffles that are not the original order (seeded per
    request, not per tick); line 1 moved to the end."""
    import random
    base = list(range(1, k + 1))
    rng = random.Random(f"{seed}:{rid}")
    out = {"original": base}
    for name in ("shuffle_a", "shuffle_b"):
        o = base[:]
        while o == base:
            rng.shuffle(o)
        out[name] = o
    out["line1_last"] = base[1:] + base[:1]
    return out


def _target(run: dict) -> dict:
    gt = run["ground_truth"]
    return {"asset": gt.get("asset", "boiler"), "target": gt.get("root_cause_id"),
            "onset_s": gt.get("fault_onset_t") or 0, "tick_s": float(gt.get("tick_period_s", 30.0))}


def select(folders: list[str], n_per_plant: int, seed: int, dev: set[str] | None = None) -> dict:
    """Diagnosis requests (full-answer format, two or more case lines) from saved
    dev runs, identical prompts once, then a seeded sample per plant. A request
    whose saved reply its rebuilt grammar would not accept is refused, so a wrong
    rebuild cannot pass silently."""
    import random
    from fieldmind.multi import grammar
    dev = dev_ids() if dev is None else dev
    found: dict[str, dict] = {}
    refused = 0
    for folder in folders:
        for f in sorted(Path(folder).glob("*.run.json.gz")):
            run = json.loads(gzip.decompress(f.read_bytes()))
            if run["episode_id"] not in dev:
                raise SystemExit(f"{f}: episode {run['episode_id']} is not in a dev set; "
                                 "reporting episodes are never used to design or run a test")
            tgt = _target(run)
            for a in run["assessments"]:
                for e in a.get("envelopes") or []:
                    p, raw = e.get("prompt") or "", e.get("raw_reply") or ""
                    if (e.get("agent") != "diagnostician" or e.get("status") != "ok"
                            or '"r":[[<case line>' not in p or "---REPAIR REPLY---" in raw):
                        continue
                    if len(case_lines(p)) < 2:
                        continue
                    if p in found:
                        found[p]["saved_replies"].append(raw)
                        continue
                    try:
                        ok = grammar.accepts(rules_for(p), raw)
                    except ValueError:
                        ok = False
                    if not ok:
                        refused += 1
                        continue
                    found[p] = {"prompt": p, "episode": run["episode_id"], "folder": Path(folder).name,
                                "evidence_tick": e.get("tick", a["tick"]), **tgt, "saved_replies": [raw]}
    by_plant: dict[str, list] = {}
    for rec in found.values():
        by_plant.setdefault(rec["asset"], []).append(rec)
    chosen = []
    for plant in sorted(by_plant):
        pool = by_plant[plant]
        chosen += random.Random(f"{seed}:{plant}").sample(pool, min(n_per_plant, len(pool)))
    for i, req in enumerate(chosen):
        req["id"] = i
    return {"seed": seed, "folders": [Path(f).name for f in folders],
            "available": {p: len(v) for p, v in by_plant.items()}, "refused": refused,
            "requests": chosen}


def _ground_truth(episode: str, root: Path = ROOT) -> dict:
    for d in DEV_DIRS:
        f = root / d / episode / "ground_truth.json"
        if f.exists():
            return json.loads(f.read_text())
    raise SystemExit(f"{episode}: no ground truth in a dev set ({', '.join(DEV_DIRS)})")


def pairs(off_log: str, on_log: str, n_per_plant: int, seed: int, dev: set[str] | None = None,
          root: Path = ROOT) -> dict:
    """Letters off / on prompts recorded by the same agent on the same dev episode
    and tick (run_demo.py --record-prompts, mock lockstep: prompts do not depend on
    model answers, f6bd178), kept only when they differ in the letters alone."""
    import random
    dev = dev_ids() if dev is None else dev

    def read(path):
        out: dict[tuple, list] = {}
        for ln in Path(path).read_text().splitlines():
            r = json.loads(ln)
            if "RETRIEVED CASES:" in r["prompt"] and '"r":[[<case line>' in r["prompt"]:
                out.setdefault((r["episode"], r["tick"]), []).append(r["prompt"])
        return out
    off, on = read(off_log), read(on_log)
    found, mismatched = {}, 0
    for key in sorted(set(off) & set(on), key=str):
        ep = key[0]
        if ep not in dev:
            raise SystemExit(f"{ep} is not in a dev set; reporting episodes are never used to design a test")
        if len(off[key]) != len(on[key]):
            mismatched += 1
            continue
        for p_off, p_on in zip(off[key], on[key]):
            if strip_letters(p_on) != p_off or not has_letters(p_on):
                mismatched += 1
                continue
            if len(case_lines(p_off)) < 2 or p_off in found:
                continue
            gt = _ground_truth(ep, root)
            found[p_off] = {"prompt": p_off, "prompt_letters": p_on, "episode": ep,
                            "evidence_tick": key[1], "asset": gt.get("asset", "boiler"),
                            "target": gt.get("root_cause_id"), "onset_s": gt.get("fault_onset_t") or 0,
                            "tick_s": float(gt.get("tick_period_s", 30.0)), "saved_replies": []}
    by_plant: dict[str, list] = {}
    for rec in found.values():
        by_plant.setdefault(rec["asset"], []).append(rec)
    chosen = []
    for plant in sorted(by_plant):
        chosen += random.Random(f"{seed}:{plant}").sample(by_plant[plant], min(n_per_plant, len(by_plant[plant])))
    for i, req in enumerate(chosen):
        req["id"] = i
    return {"seed": seed, "kind": "letter pairs", "available": {p: len(v) for p, v in by_plant.items()},
            "mismatched": mismatched, "requests": chosen}


def run_replay(doc: dict, backend, out_path: str, label: str, names=None,
               field: str = "prompt") -> dict:
    """Every request in every ordering, once; one JSON line per call. Resumes: a
    (label, id, ordering) already in out_path is not sent again."""
    from fieldmind.multi import grammar
    import collections
    done = set()
    if Path(out_path).exists():
        for ln in Path(out_path).read_text().splitlines():
            r = json.loads(ln)
            done.add((r["label"], r["id"], r["ordering"]))
    counts = collections.Counter()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "a") as f:
        for req in doc["requests"]:
            gbnf = grammar.to_gbnf(rules_for(req[field]))
            k = len(case_lines(req[field]))
            for name, order in orderings(k, req["id"], doc["seed"]).items():
                if (names and name not in names) or (label, req["id"], name) in done:
                    continue
                prompt, cases = reorder(req[field], order)
                reply = backend.generate(prompt, role="diagnostician",
                                         max_tokens=DIAGNOSTICIAN_CAP, grammar=gbnf)
                counts[reply.status] += 1
                f.write(json.dumps({"label": label, "id": req["id"], "ordering": name,
                                    "order": order, "cases": cases, "status": reply.status,
                                    "reply": reply.text, "model": reply.model,
                                    "prefill": reply.prefill_tokens, "decode": reply.decode_tokens,
                                    "latency_ms": reply.latency_ms}) + "\n")
                f.flush()
    return dict(counts)


def score(doc: dict, rows: list[dict]) -> dict:
    """Per label and ordering: line-1 share, rank-1 right (exact / group) on scored
    requests, deviations and how often they were right; per label: position
    invariance (the same rank-1 case in every ordering of a request) and, on the
    original order, rank-1 agreement with the saved board reply."""
    reqs = {r["id"]: r for r in doc["requests"]}
    out: dict = {}
    picks: dict = {}
    for row in rows:
        lines = ranked_lines(row["reply"] or "") if row["status"] == "ok" else None
        if not lines:
            continue
        req = reqs[row["id"]]
        cases = {int(k): v for k, v in row["cases"].items()}
        pick = cases.get(lines[0])
        picks.setdefault(row["label"], {}).setdefault(row["id"], {})[row["ordering"]] = pick
        c = out.setdefault(row["label"], {}).setdefault(row["ordering"], _new())
        tgt = req["target"]
        fault = tgt not in (None, "NONE")
        tgroup = gmap = None
        if fault:
            gmap, held, held_ids = _groups(req["asset"])
            tgroup = held.get(tgt) if tgt in held_ids else gmap.get(tgt, tgt)
        add(c, {"lines": lines, "cases": cases, "target": tgt, "tgroup": tgroup, "gmap": gmap,
                "scored": fault and req["evidence_tick"] * req["tick_s"] >= req["onset_s"]})
    res = {}
    for label, by_order in out.items():
        p = picks[label]
        full = [v for v in p.values() if len(v) == len(orderings(2, 0, 0))]
        same = sum(len(set(v.values())) == 1 for v in full)
        agree = n_orig = 0
        for rid, v in p.items():
            if "original" in v and reqs[rid].get("saved_replies"):
                n_orig += 1
                saved = ranked_lines(reqs[rid]["saved_replies"][0])
                agree += bool(saved) and case_lines(reqs[rid]["prompt"]).get(saved[0]) == v["original"]
        res[label] = {"orderings": {o: summarise(c) for o, c in by_order.items()},
                      "requests_all_orderings": len(full),
                      "position_invariance": round(same / len(full), 3) if full else None,
                      "original_agrees_with_saved_rank1": round(agree / n_orig, 3) if n_orig else None}
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="what", required=True)
    s = sub.add_parser("saved", help="echo measures over saved run folders")
    s.add_argument("folders", nargs="+")
    s.add_argument("--allow-reporting", action="store_true",
                   help="include reporting episodes (rows marked REPORTING, descriptive only)")
    s.add_argument("--json", default=None, help="also write the rows to this file")
    s = sub.add_parser("select", help="choose dev requests for the replay")
    s.add_argument("folders", nargs="+")
    s.add_argument("--n", type=int, required=True, help="requests per plant")
    s.add_argument("--seed", type=int, required=True)
    s.add_argument("--out", required=True)
    s = sub.add_parser("pairs", help="letters off / on prompt pairs from two --record-prompts logs")
    s.add_argument("off_log")
    s.add_argument("on_log")
    s.add_argument("--n", type=int, required=True, help="pairs per plant")
    s.add_argument("--seed", type=int, required=True)
    s.add_argument("--out", required=True)
    s = sub.add_parser("run", help="send every request in every ordering to one llama-server")
    s.add_argument("requests")
    s.add_argument("--url", required=True)
    s.add_argument("--model", required=True, help="the GGUF file the server loaded (recorded)")
    s.add_argument("--label", required=True, help="the arm, e.g. q4_0_board_file")
    s.add_argument("--out", required=True)
    s.add_argument("--only", default=None, help="comma-separated orderings (pilot)")
    s.add_argument("--limit", type=int, default=None, help="first N requests only (pilot)")
    s.add_argument("--field", default="prompt", choices=["prompt", "prompt_letters"],
                   help="which prompt of a letter pair to send")
    s = sub.add_parser("score", help="score replay rows")
    s.add_argument("requests")
    s.add_argument("rows", nargs="+")
    args = ap.parse_args(argv)
    if args.what == "saved":
        rows = scan(args.folders, allow_reporting=args.allow_reporting)
        print(table(rows))
        if args.json:
            Path(args.json).write_text(json.dumps(rows, indent=1))
    elif args.what == "select":
        doc = select(args.folders, args.n, args.seed)
        Path(args.out).write_text(json.dumps(doc, indent=1))
        print(f"available {doc['available']}, refused {doc['refused']}, chosen {len(doc['requests'])}")
    elif args.what == "pairs":
        doc = pairs(args.off_log, args.on_log, args.n, args.seed)
        Path(args.out).write_text(json.dumps(doc, indent=1))
        print(f"available {doc['available']}, mismatched {doc['mismatched']}, chosen {len(doc['requests'])}")
    elif args.what == "run":
        from fieldmind.runtime.llm_backend import LlamaServerBackend
        doc = json.loads(Path(args.requests).read_text())
        if args.limit:
            doc = {**doc, "requests": doc["requests"][:args.limit]}
        be = LlamaServerBackend(url=args.url, lane="laptop", model_file=args.model,
                                temperature=0.0, seed=0, timeout_s=300.0, cache_prompt=False)
        print(run_replay(doc, be, args.out, args.label,
                         names=set(args.only.split(",")) if args.only else None, field=args.field))
    else:
        doc = json.loads(Path(args.requests).read_text())
        rows = [json.loads(ln) for p in args.rows for ln in Path(p).read_text().splitlines()]
        print(json.dumps(score(doc, rows), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
