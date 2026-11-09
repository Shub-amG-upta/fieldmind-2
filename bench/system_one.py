"""
Pure helpers for Laya as the System One model (reports/laya_l1.md). Stdlib only, so
both the project venv (requests, evaluation) and .venv-laya (bench/laya_serve.py)
import the same code.

  shuffle_request    a /v1/systemone request with every choice question's
                     options in a seeded different order (keys unchanged), for
                     the order test: Laya scores all options in one sequence,
                     so it is not order-free by construction
  to_bev_reply       Laya's answers -> bev-decide's reply shape, the one
                     fieldmind.multi.agents.decider.check_answer and
                     fieldmind.multi.agents.bev.check_answers accept, so every
                     bev slot can use Laya by changing the lane URL
  scored_at          the publication time of tick k, (k+1) x tick (as T7)
  pooled_share,
  bootstrap_by_episode   pick accuracy over requests and its interval,
                     resampling whole episodes (consecutive ticks are correlated)
"""

from __future__ import annotations

import hashlib
import json
import random

SEED = 20261107             # DESIGN (pre-registered): one fixed seed for every shuffle and bootstrap
BOOTSTRAP_N = 2000          # DESIGN (pre-registered)


# ----------------------------------------------------------------------
def request_seed(prompt: str, seed: int = SEED) -> int:
    """A per-request seed: the same request always gets the same shuffle."""
    h = hashlib.sha256(f"{seed}:{prompt}".encode()).hexdigest()
    return int(h[:16], 16)


def shuffle_request(req: dict, seed: int) -> dict:
    """A copy of `req` with each choice question's options in a seeded order
    that differs from the original whenever it has two or more options. Keys
    and texts are unchanged; only their order moves. Yes/no questions as is."""
    rng = random.Random(seed)
    qs = {}
    for qid, q in req["questions"].items():
        q = dict(q)
        crit = q.get("criteria")
        if q.get("type") == "choice" and isinstance(crit, dict) and len(crit) >= 2:
            keys = list(crit)
            order = keys[:]
            while order == keys:              # a shuffle that leaves the order is no test
                rng.shuffle(order)
            q["criteria"] = {k: crit[k] for k in order}
        qs[qid] = q
    return {**req, "questions": qs}


# ----------------------------------------------------------------------
class ReplyError(ValueError):
    """Laya's answer cannot be put in bev-decide's shape (a missing question or option)."""


def to_bev_reply(answers: dict, questions: dict, *, model: str, prompt_tokens: int | None,
                 model_ms: float, truncated: bool) -> dict:
    """bev-decide's /v1/systemone reply from Laya's `answers` for `questions`.

    choice: probabilities over exactly the offered keys (Laya's, renormalised
    over them), `choice` the most probable (ties in offered order).
    noul:   P(yes), as `noul`.
    """
    out = {}
    for qid, q in questions.items():
        a = answers.get(qid)
        if not isinstance(a, dict):
            raise ReplyError(f"{qid}: no answer")
        if q["type"] == "noul":
            p = a.get("noul")
            if isinstance(p, bool) or not isinstance(p, (int, float)):
                raise ReplyError(f"{qid}: P(yes) is {p!r}")
            out[qid] = {"type": "noul", "noul": min(1.0, max(0.0, float(p)))}
            continue
        offered = list(q["criteria"])
        probs = a.get("probabilities")
        if not isinstance(probs, dict) or not set(offered) <= set(probs):
            raise ReplyError(f"{qid}: probabilities name {sorted(probs) if isinstance(probs, dict) else probs}, "
                             f"offered {offered}")
        raw = {k: float(probs[k]) for k in offered}
        tot = sum(raw.values())
        if tot <= 0:
            raise ReplyError(f"{qid}: probabilities sum to {tot}")
        p = {k: v / tot for k, v in raw.items()}
        choice = max(offered, key=lambda k: (p[k], -offered.index(k)))
        out[qid] = {"type": "choice", "choice": choice, "probabilities": p}
    return {"model": model, "answers": out,
            "usage": {"prompt_tokens": prompt_tokens},
            "timings": {"decode_ms": float(model_ms)},
            "truncated": bool(truncated)}


# ----------------------------------------------------------------------
def scored_at(tick: int, tick_s: float) -> float:
    """Tick k publishes at (k+1) x tick (the T7 convention)."""
    return (tick + 1) * tick_s


def after_onset(tick: int, tick_s: float, onset_t: float | None) -> bool:
    return onset_t is not None and scored_at(tick, tick_s) >= onset_t


def pooled_share(rows: list[dict], key: str) -> float | None:
    """Share of rows whose `key` is true, over the rows that have it (None = not applicable)."""
    vals = [bool(r[key]) for r in rows if r.get(key) is not None]
    return sum(vals) / len(vals) if vals else None


def bootstrap_by_episode(rows: list[dict], key: str, n: int = BOOTSTRAP_N,
                         seed: int = SEED) -> tuple[float | None, float | None, float | None]:
    """(pooled share, 2.5%, 97.5%) resampling whole episodes with replacement."""
    by_ep: dict[str, list[dict]] = {}
    for r in rows:
        if r.get(key) is not None:
            by_ep.setdefault(r["episode"], []).append(r)
    if not by_ep:
        return None, None, None
    eps = sorted(by_ep)
    point = pooled_share([r for e in eps for r in by_ep[e]], key)
    rng = random.Random(seed)
    stats = []
    for _ in range(n):
        pick = [rng.choice(eps) for _ in eps]
        sample = [r for e in pick for r in by_ep[e]]
        stats.append(pooled_share(sample, key))
    stats.sort()
    return point, stats[int(0.025 * n)], stats[min(n - 1, int(0.975 * n))]


def dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)
