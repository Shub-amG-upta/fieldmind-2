"""
Published fixes for the diagnostician's position shortcuts (paper B item 2,
PLAN_PAPER_B.md; reports/paperB_item2_prereg.md). Every switch is off by default,
so a run that does not name `multi.debias` is byte for byte what it was.

    multi:
      debias:
        example: on | off            off: drop the prompt's worked "Example:" line
        method: none | calibrate | pride | psc
        psc_k: 3                     psc: orderings per call (identity + k-1 shuffles)
        pride_samples: 5             pride: calls that estimate the prior, per prompt shape
        pride_perms: 4               pride: cyclic orderings per estimating call
        top_logprobs: 20             calibrate / pride: alternatives read per token

  calibrate  contextual calibration (Zhao et al., ICML 2021, arXiv 2102.09690):
             the model's line prior is read once per prompt shape from a content-free
             copy of the prompt (fact and case text replaced by "N/A"); the rank-1 line
             is then re-chosen as argmax(log p(line) - log prior(line)).
  pride      PriDe (Zheng et al., ICLR 2024, arXiv 2309.03882): the prior over
             positions is estimated from the first calls of each prompt shape, each
             asked in cyclic orderings: prior = softmax(mean over orderings of
             log p(position)); later calls are debiased as above.
  psc        permutation self-consistency (Tang et al., arXiv 2310.07712): each call
             is asked in k orderings of the case list and the k rankings are
             combined (Borda count, DESIGN: the paper's central-ranking aggregation
             is replaced by the simpler Borda rule; ties go to the identity
             ordering's ranking).

calibrate and pride re-choose ONLY the rank-1 line (the shortcut the echo test
measures); the rest of the answer is the model's. They need per-token
probabilities, which only llama-server reports (raw, before the grammar); on any
other backend they change nothing and say so ("no_probs").

Standard library only (fieldmind/ rule).
"""

from __future__ import annotations

import math
import random
import re

METHODS = ("none", "calibrate", "pride", "psc")
# DESIGN defaults; every value has a range in reports/paperB_item2_prereg.md.
DEFAULTS = {"example": "on", "method": "none", "psc_k": 3, "pride_samples": 5,
            "pride_perms": 4, "top_logprobs": 20}
_CASES_HEAD = "RETRIEVED CASES:\n"
_FACTS_HEAD = "FACTS:\n"
_FIRST_LINE = re.compile(r'"r"\s*:\s*\[\s*\[?\s*$')


def switches(mcfg: dict | None) -> dict:
    d = dict(DEFAULTS)
    d.update((mcfg or {}).get("debias") or {})
    if d["example"] not in ("on", "off"):
        raise ValueError(f"multi.debias.example must be on or off, not {d['example']!r}")
    if d["method"] not in METHODS:
        raise ValueError(f"multi.debias.method must be one of {METHODS}, not {d['method']!r}")
    for k in ("psc_k", "pride_samples", "pride_perms", "top_logprobs"):
        if not (isinstance(d[k], int) and d[k] >= 1):
            raise ValueError(f"multi.debias.{k} must be a positive integer")
    if d["method"] == "psc" and d["psc_k"] < 2:
        raise ValueError("multi.debias.psc_k must be at least 2 (1 is the plain call)")
    return d


def active(sw: dict) -> bool:
    return sw["example"] == "off" or sw["method"] != "none"


# ---------------------------------------------------------------- prompt text
def drop_example(template: str) -> str:
    """The template without its worked-example line (the line starting "Example: ")."""
    lines = template.split("\n")
    kept = [ln for ln in lines if not ln.startswith("Example: ")]
    if len(kept) == len(lines):
        raise ValueError("template has no 'Example: ' line to drop")
    return "\n".join(kept)


def _block(prompt: str, head: str) -> tuple[str, list[str], list[str]]:
    """(text up to and including the block head, the block's numbered lines, the lines after them)."""
    if head not in prompt:
        raise ValueError(f"prompt has no {head.strip()!r} block")
    before, rest = prompt.split(head, 1)
    lines = rest.split("\n")
    n = 0
    while n < len(lines) and re.match(r"\d+\. ", lines[n]):
        n += 1
    return before + head, lines[:n], lines[n:]


def case_count(prompt: str) -> int:
    return len(_block(prompt, _CASES_HEAD)[1])


def reorder_cases(prompt: str, order: list[int]) -> str:
    """The prompt with its case lines shown in `order` (old 1-based line numbers),
    renumbered 1..k; every other byte kept."""
    head, lines, rest = _block(prompt, _CASES_HEAD)
    if sorted(order) != list(range(1, len(lines) + 1)):
        raise ValueError(f"order {order} is not a permutation of 1..{len(lines)}")
    body = [re.sub(r"^\d+\. ", "", ln) for ln in lines]
    return head + "\n".join([f"{i}. {body[o - 1]}" for i, o in enumerate(order, 1)] + rest)


def content_free(prompt: str) -> str:
    """Zhao et al.'s content-free input: every fact, case, note and record line keeps
    its number and its place, its text becomes "N/A"; so does the world-model line
    (it names cases and their belief). The rules, format and line counts stay."""
    out = prompt
    for head in (_FACTS_HEAD, _CASES_HEAD, "<<<\n"):
        if head not in out:
            continue
        before, lines, rest = _block(out, head)
        out = before + "\n".join([f"{i}. N/A" for i in range(1, len(lines) + 1)] + rest)
    return re.sub(r"(?m)^WORLD MODEL: .*(\nOTHER SIDE \(from code\): .*)?$", "WORLD MODEL: N/A", out)


def orderings(n: int, k: int, seed) -> list[list[int]]:
    """Identity first, then k-1 seeded shuffles, distinct from each other and from the
    identity while that is possible (n! orderings exist)."""
    base = list(range(1, n + 1))
    out = [base]
    rng = random.Random(f"psc:{seed}")
    tries = 0
    while len(out) < min(k, math.factorial(n)) and tries < 1000:
        o = base[:]
        rng.shuffle(o)
        tries += 1
        if o not in out:
            out.append(o)
    return out


def cyclic(n: int, m: int) -> list[list[int]]:
    """The first m cyclic orderings of 1..n (identity first); PriDe's permutations."""
    base = list(range(1, n + 1))
    return [base[s:] + base[:s] for s in range(min(m, n))]


def permuted_hint(hint: dict, order: list[int]) -> dict:
    """The mock hint for a reordered prompt: its shown case lines (and letters) in the
    new order, so the mock (which answers by case id) keeps naming the same cases."""
    h = dict(hint)
    for key in ("case_lines", "letters"):
        if isinstance(h.get(key), list) and len(h[key]) == len(order):
            h[key] = [hint[key][o - 1] for o in order]
    return h


# ---------------------------------------------------------------- answers
def ranked(payload: dict) -> list[int]:
    out = []
    for e in payload.get("r") or []:
        line = e[0] if isinstance(e, list) else e
        if isinstance(line, int) and line not in out:
            out.append(line)
    return out


def to_original(payload: dict, order: list[int], rank_only: bool) -> dict:
    """An answer to a reordered prompt, its case lines mapped back to the original
    numbering (shown line i was original line order[i-1]); lines outside the list
    are kept as they are (the gate counts them as invented)."""
    def back(x):
        return order[x - 1] if isinstance(x, int) and 1 <= x <= len(order) else x
    p = dict(payload)
    if rank_only:
        p["r"] = [back(x) for x in payload.get("r") or []]
    else:
        p["r"] = [[back(e[0]), list(e[1])] for e in payload.get("r") or []]
        if payload.get("sep") is not None:
            p["sep"] = back(payload["sep"])
    return p


def borda(rankings: list[list[int]], n: int) -> list[int]:
    """Lines by Borda score (n - position, 0 when unranked); ties by the first
    ranking's order, then line number. Lines no ranking names are left out."""
    score: dict[int, int] = {}
    for r in rankings:
        for pos, line in enumerate(r):
            score[line] = score.get(line, 0) + (n - pos)
    first = rankings[0] if rankings else []
    tie = {line: (first.index(line) if line in first else len(first)) for line in score}
    return sorted(score, key=lambda line: (-score[line], tie[line], line))


def combine(payloads: list[dict], n: int, rank_only: bool, letters: list | None,
            max_ranked: int) -> dict:
    """PSC: one answer from several (all in original numbering; the first is the
    identity ordering's). Ranking by Borda; each line's fact citations from the first
    answer that ranked it; sep by majority (ties: the first answer's); notes and
    unexplained facts from the first answer; g is the letter of the new rank-1 line."""
    order = borda([ranked(p) for p in payloads], n)[:max_ranked]
    if rank_only:
        return {"r": order}
    facts = {}
    for p in payloads:
        for e in p.get("r") or []:
            facts.setdefault(e[0], list(e[1]))
    first = payloads[0]
    out = {k: v for k, v in first.items() if k not in ("r", "sep", "g")}
    out["r"] = [[line, facts.get(line, [])] for line in order]
    seps = [p.get("sep") for p in payloads if p.get("sep") is not None]
    if seps:
        best = max(seps.count(s) for s in seps)
        out["sep"] = first.get("sep") if seps.count(first.get("sep")) == best else \
            next(s for s in seps if seps.count(s) == best)
    else:
        out["sep"] = first.get("sep")
    if "g" in first:
        out["g"] = (letters[order[0] - 1] if letters and order and 1 <= order[0] <= len(letters)
                    else first.get("g"))
    return out


def move_first(payload: dict, line: int, rank_only: bool, letters: list | None) -> dict:
    """The answer with `line` put at rank 1 (added with no citations if absent); the
    rest keeps the model's order; ranked list still at most its old length + 0
    (when added, the last entry drops if the list was full: caller passes the cap)."""
    p = dict(payload)
    if rank_only:
        p["r"] = [line] + [x for x in payload.get("r") or [] if x != line]
    else:
        old = [list(e) for e in payload.get("r") or []]
        hit = [e for e in old if e[0] == line]
        p["r"] = (hit[:1] or [[line, []]]) + [e for e in old if e[0] != line]
        if "g" in payload and letters and 1 <= line <= len(letters):
            p["g"] = letters[line - 1]
    return p


# ---------------------------------------------------------------- probabilities
def first_line_logprobs(token_probs: list[dict] | None, n: int) -> dict[int, float] | None:
    """{case line: log p} at the token that writes the answer's first case line, read
    from the server's per-token alternatives (raw, before the grammar). Only
    alternatives with the same structural prefix as the chosen token (e.g. "[[" or
    nothing) count; lines outside 1..n are ignored. None if no such token exists."""
    if not token_probs:
        return None
    before = ""
    for t in token_probs:
        tok = t.get("token") or ""
        m = re.match(r"(\D*)(\d+)", tok)
        if m and _FIRST_LINE.search(before + m.group(1)):
            prefix, out = m.group(1), {}
            for alt, lp in [(tok, t.get("logprob"))] + [(a, b) for a, b in t.get("top") or []]:
                m2 = re.match(r"(\D*)(\d+)$", alt or "")
                if m2 and m2.group(1) == prefix and lp is not None:
                    line = int(m2.group(2))
                    if 1 <= line <= n:
                        out[line] = max(out.get(line, -math.inf), float(lp))
            return out or None
        before += tok
    return None


def normalise(lp: dict[int, float], n: int, floor: float | None = None) -> dict[int, float]:
    """Log-probabilities over lines 1..n renormalised over those lines; a line with no
    reading gets `floor` (DESIGN: the lowest reading minus 1 nat when not given)."""
    if not lp:
        return {}
    fl = (min(lp.values()) - 1.0) if floor is None else floor
    full = {j: lp.get(j, fl) for j in range(1, n + 1)}
    z = math.log(sum(math.exp(v) for v in full.values()))
    return {j: v - z for j, v in full.items()}


# DESIGN: content-free probes per prompt shape before calibrate gives up on that shape (a probe whose
# first case line cannot be read: no probabilities, or an empty ranking). Range 1-5. Affects cost only.
CAL_PROBE_ATTEMPTS = 3
# DESIGN: debiased scores within this many nats of the best count as a tie (floating-point noise,
# not evidence). Range 1e-9 to 1e-3. Affects only exact ties.
TIE_NATS = 1e-6


def debiased_first(lp: dict[int, float], prior: dict[int, float], prefer: int | None = None) -> int:
    """argmax over lines the model read of log p(line) - log prior(line). A tie (within
    TIE_NATS) keeps `prefer` (the model's own rank-1) when it is among the best, else the
    lower line: debiasing moves the answer only when the evidence says so."""
    fl = min(prior.values())
    score = {j: lp[j] - prior.get(j, fl) for j in lp}
    best = max(score.values())
    tied = sorted(j for j, v in score.items() if v >= best - TIE_NATS)
    return prefer if prefer in tied else tied[0]


def pride_prior(position_lps: list[dict[int, float]], n: int) -> dict[int, float]:
    """PriDe's prior from one call asked in several orderings: softmax over positions of
    the mean (over orderings) of the renormalised log p(position)."""
    rows = [normalise(lp, n) for lp in position_lps if lp]
    if not rows:
        return {}
    mean = {j: sum(r[j] for r in rows) / len(rows) for j in range(1, n + 1)}
    z = math.log(sum(math.exp(v) for v in mean.values()))
    return {j: v - z for j, v in mean.items()}


def mean_prior(priors: list[dict[int, float]], n: int) -> dict[int, float]:
    """The average of several log-priors over 1..n, renormalised."""
    ps = [p for p in priors if p]
    if not ps:
        return {}
    mean = {j: sum(p[j] for p in ps) / len(ps) for j in range(1, n + 1)}
    z = math.log(sum(math.exp(v) for v in mean.values()))
    return {j: v - z for j, v in mean.items()}
