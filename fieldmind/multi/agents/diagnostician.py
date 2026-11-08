"""
Diagnostician (model agent, a Job).

`multi.compact.schema` off: the single agent's L4, unchanged (Phase 1). The
job's work is Diagnostician.run on THIS tick's evidence; the Diagnostician
object was constructed on the LaneBackend facade, so its call goes to whichever
lane the scheduler picks.

`schema` on (Phase 2 commit 5): the compact prompt (compact.build_diagnosis),
answer format B' capped at multi.answer_caps.diagnostician, one repair call.
The line map built with the prompt travels with the job; the gate expands the
answer through it. The counters (calls, parse failures) stay on the single
agent's Diagnostician, so the run file's diag_calls / parse_failure_rate keep
their meaning.

Reads the board (facts, retrieval, findings, belief, trust, notefacts,
recordfacts) and writes nothing: its envelope returns as a Result, and only the
gate puts it on the board.
"""

from __future__ import annotations

from types import SimpleNamespace

from ...agent.l1_symbolize import evidence_packet
from ...agent.orchestrator import evidence_max_facts, wm_summary
from ...schemas import TAGS
from .. import compact, grammar, merge_rules, sides
from ._call import call_model, code_answer
from .bev import explain_prompt, routed_note_sides, switches as bev_switches

# one_code (explain_v2): the code answer for a side shown exactly one case
ONE_CASE_ANSWER = '{"r":[1]}'

NAME = "diagnostician"
# Phase 3: a side's job is placed by `diag_<side>` (multi.fixed_placement);
# its envelope keeps agent "diagnostician", so the bench tools read it as one.
SIDE_FACT_LINES = 8     # CITED: plan p.15 token budget, "this side's facts (up to 8 lines)"
SIDE_NOTE = {           # one line naming the side; plan p.5 agent table
    "water": "This prompt covers the WATER side only: drum level, feed water flow, steam flow.",
    "heat": "This prompt covers the HEAT side only: bed temperature, drum pressure, main "
            "steam temperature, with steam flow as the load.",
}


def priority_for(level: str) -> int:
    """P1 urgent diagnosis (trip predicted / CRITICAL fact, i.e. triage URGENT),
    else P2 (plan p.10)."""
    return 1 if level == "URGENT" else 2


class DiagnosticianAgent:
    def __init__(self, diag, cfg: dict, mcfg: dict | None = None,
                 letters: dict | None = None, asset=None):
        self.diag = diag
        # The plant (fieldmind/assets): its tags, side split and prompt wording.
        # None = the boiler (the module-level side functions and SIDE_NOTE).
        self.asset = asset
        self.tags = tuple(TAGS) if asset is None else asset.tags
        self.sides = sides if asset is None or asset.sides is None else sides.for_asset(asset)
        self.side_note = SIDE_NOTE if asset is None or asset.sides is None else asset.sides.side_note
        sub = None if asset is None else asset.prompt_dir
        self.cfg = cfg
        mcfg = mcfg or {}
        self.sw = compact.compact_switches(mcfg.get("compact"))
        self.letters = letters or {}
        self.cap = (mcfg.get("answer_caps") or {}).get("diagnostician", 60)
        self.guard_cpt = mcfg.get("compact_guard_cpt")
        self.split = bool(mcfg.get("split", False))
        self.raw_notes = self.sw["notes"] and self.sw["note_source"] == "raw"
        self.on_change = bool(mcfg.get("split_on_change", False))
        self.grammar = bool(mcfg.get("grammar", False))
        if self.grammar and not self.sw["schema"]:
            raise ValueError("multi.grammar needs multi.compact.schema on: the grammar "
                             "is the compact (B') answer format")
        if self.on_change and not self.split:
            raise ValueError("multi.split_on_change needs multi.split on")
        if self.split and not self.sw["schema"]:
            raise ValueError("multi.split needs multi.compact.schema on: the side "
                             "prompts are the compact (B') prompts")
        # bev ideas (reports/bev_ideas.md): clear_skip (code only) and the
        # telemetry of the skips it made or (shadow) would have made
        self.bev_sw = bev_switches(mcfg)
        if self.bev_sw["clear_skip"] != "off" and not (self.split and self.on_change):
            raise ValueError("multi.bev.clear_skip needs multi.split and multi.split_on_change "
                             "(it skips a side whose evidence changed)")
        if self.bev_sw["empty_skip"] != "off" and not self.split:
            raise ValueError("multi.bev.empty_skip needs multi.split (it skips one side's call)")
        if self.bev_sw["one_code"] != "off" and not (self.split and self.bev_sw["explain"] == "on"):
            raise ValueError("multi.bev.one_code needs multi.split and multi.bev.explain on "
                             "(only the ranking-only answer {\"r\":[1]} is complete)")
        self.skip_log: list[dict] = []
        self.bev_notes = self.bev_sw["notes"] == "on"
        if self.bev_sw["notes"] != "off" and not (self.raw_notes and self.split):
            raise ValueError("multi.bev.notes needs raw notes (compact.note_source: raw) and "
                             "multi.split (it routes each note to a side)")
        if self.sw["schema"]:
            # group_letters off: the same body without the leading "g" in the
            # answer format and example
            body = ("diag_compact.txt" if self.sw["group_letters"]
                    else "diag_compact_nogroup.txt")
            self.templates = {"body": compact.load_prompt(body, sub),
                              "rules_full": compact.load_prompt("diag_rules_full.txt", sub),
                              "rules_compact": compact.load_prompt("diag_rules_compact.txt", sub)}
            self.repair = compact.load_prompt("repair_lines.txt", sub)
        # bev ideas, explain on (reports/bev_ideas.md): Llama ranks the cases
        # only; bev supplies citations, sep and notes (orchestrator._explain).
        # shadow keeps the full prompt (bev is asked beside it, for agreement).
        self.rank_only = self.bev_sw["explain"] == "on"
        if self.rank_only:
            if not self.sw["schema"] or self.sw["group_letters"]:
                raise ValueError("multi.bev.explain on needs compact.schema on and "
                                 "group_letters off (the ranking-only answer has no letter)")
            if not self.split:
                raise ValueError("multi.bev.explain needs multi.split (side prompts)")
            rules = compact.load_prompt("diag_rules_rank_only.txt", sub)
            body = ("diag_rank_only_v2.txt" if explain_prompt(mcfg) == "v2"
                    else "diag_rank_only.txt")
            self.templates = {"body": compact.load_prompt(body, sub),
                              "rules_full": rules, "rules_compact": rules}

    def make_job(self, bb, scheduler, tick: int, level: str, rung: int,
                 submit_s: float):
        if self.sw["schema"]:
            return self._compact_job(bb, scheduler, tick, level, rung, submit_s)
        facts = bb.read("facts").facts_of(tick)
        retrieved = bb.read("retrieval")
        summary_view = SimpleNamespace(open_findings=bb.read("findings"),
                                       hypotheses=bb.read("belief"),
                                       trusted_tags=bb.read("trust"))

        def work():
            with bb.step(NAME):
                evidence = evidence_packet(
                    facts, max_facts=evidence_max_facts(level, rung))
                return self.diag.run(tick, evidence, dict(retrieved), facts,
                                     wm_summary(summary_view, self.tags))

        return scheduler.new_job(NAME, evidence_tick=tick,
                                 priority=priority_for(level),
                                 max_answer_tokens=self.cfg["max_tokens"],
                                 submit_s=submit_s, work=work)

    def sides_to_run(self, bb, tick: int) -> list[str]:
        """The active sides (non-INFO fact or open finding); both when neither
        side has evidence (Phase 3 decision 5)."""
        return self.sides.sides_to_run(bb.read("facts").facts_of(tick), bb.read("findings"))

    @staticmethod
    def fingerprint(bb, side: str, raw_notes: bool = False, bev_notes: bool = False,
                    sd=None) -> tuple:
        """The evidence a side's diagnosis depends on, as on the board now.
        `raw_notes` (note_source raw): the side's selected raw notes count as
        evidence, so a newly arrived note makes the side be asked again (with
        the text reader on, its note-facts do that). `sd`: the asset's side
        functions (None = the boiler's)."""
        sd = sides if sd is None else sd
        retrieved = bb.read("retrieval")
        shown = ([c.get("case_id") for c in
                  sd.cases_for_side(retrieved.get("cases", []), side)]
                 + [e.get("case_id") for e in retrieved.get("experience", [])])
        if raw_notes:
            shown += ["note:" + str(n.get("id")) for n in retrieved.get("notes", [])
                      if side in routed_note_sides(bb, n, bev_notes)]
        return sd.side_fingerprint(bb.read("signature").get("signature", {}),
                                      bb.read("findings"),
                                      list(bb.read("notefacts").values()), side,
                                      case_ids=shown)

    def make_jobs(self, bb, scheduler, tick: int, level: str, rung: int,
                  submit_s: float) -> list:
        """Phase 3: one job per side to run (`multi.split` on); else one job.
        With `multi.split_on_change`, no job for a side whose evidence is
        unchanged since its cached answer (plan: "a side's diagnosis is
        requested only if its signature, its open findings or its note-facts
        changed"); the gate re-uses that answer."""
        if not self.split:
            return [self.make_job(bb, scheduler, tick, level, rung, submit_s)]
        cached = bb.read("side_answers")
        jobs = []
        for s in self.sides_to_run(bb, tick):
            fp = self.fingerprint(bb, s, self.raw_notes, self.bev_notes, self.sides)
            if self.on_change and s in cached and cached[s]["fingerprint"] == fp:
                continue
            if self.bev_sw["clear_skip"] != "off" and self._clear_skip(bb, cached, s, tick):
                if self.bev_sw["clear_skip"] == "on":
                    continue                    # no call; the gate re-uses nothing (evidence changed)
            if self.bev_sw["empty_skip"] != "off" and self._empty_skip(fp, s, tick):
                if self.bev_sw["empty_skip"] == "on":
                    continue                    # no case to rank: the answer could only be "r":[]
            one = self.bev_sw["one_code"] != "off" and self._one_case(fp, s, tick)
            job = self._compact_job(bb, scheduler, tick, level, rung, submit_s, side=s,
                                    code_text=ONE_CASE_ANSWER if one and self.bev_sw["one_code"] == "on"
                                    else None)
            if one:
                job.line_map["info"]["one_code"] = self.bev_sw["one_code"]
            job.line_map["fingerprint"] = fp
            # telemetry: the cache this job was made against ("same" is only
            # possible with split_on_change off)
            job.line_map["info"]["cache"] = ("none" if s not in cached else
                                             "same" if cached[s]["fingerprint"] == fp
                                             else "changed")
            jobs.append(job)
        return jobs

    def _clear_skip(self, bb, cached: dict, side: str, tick: int) -> bool:
        """clear_skip (code only, reports/bev_ideas.md): belief has a clear
        leader (merge_rules.regime, belief alone) and this side's last checked
        answer already put that leader first. Under hybrid the model does not
        lead on a clear tick, so the call can only add a capped nudge. The only
        evidence so far is an offline replay of the v3 board answers on the
        REPORTING episodes (no published change; 77 calls, 2,596 decode tokens):
        it motivated the idea and decides nothing; keep / revert is decided on
        the dev set by the pass rule (reports/bev_ideas.md). Logged either way."""
        if side not in cached:
            return False
        hyps = (cached[side].get("payload") or {}).get("hypotheses") or []
        last_top = hyps[0].get("case_ref") if hyps else None
        live = [h for h in bb.read("belief") if not h.retired]
        order = merge_rules._belief_order(live)
        leader = order[0].case_ref if order else None
        hit = (last_top is not None and last_top == leader
               and merge_rules.regime(live) == "clear")
        if hit:
            self.skip_log.append({"agent": "bev", "idea": "clear_skip",
                                  "mode": self.bev_sw["clear_skip"], "evidence_tick": tick,
                                  "side": side, "leader": leader, "skipped": True})
        return hit

    def _empty_skip(self, fp: tuple, side: str, tick: int) -> bool:
        """empty_skip (explain_v2, reports/accuracy_fixes.md): this side's prompt would
        show no case (own past episodes included), so the only possible answer is an
        empty ranking. A side that made no call drops out of the tick's merge, which is
        what an empty ranking does too. Logged either way."""
        shown = [c for c in fp[3] if not str(c).startswith("note:")]
        if shown:
            return False
        self.skip_log.append({"agent": "bev", "idea": "empty_skip",
                              "mode": self.bev_sw["empty_skip"], "evidence_tick": tick,
                              "side": side, "skipped": True})
        return True

    def _one_case(self, fp: tuple, side: str, tick: int) -> bool:
        """one_code (explain_v2): this side's prompt shows exactly one case, so the
        ranking-only answer is {"r":[1]} or an empty ranking; the board chose
        {"r":[1]} on 1,427 of 1,436 such calls. Logged either way."""
        shown = [c for c in fp[3] if not str(c).startswith("note:")]
        if len(shown) != 1:
            return False
        self.skip_log.append({"agent": "bev", "idea": "one_code",
                              "mode": self.bev_sw["one_code"], "evidence_tick": tick,
                              "side": side, "case": shown[0], "skipped": self.bev_sw["one_code"] == "on"})
        return True

    # ------------------------------------------------------------------
    def _compact_job(self, bb, scheduler, tick, level, rung, submit_s, side=None,
                     code_text: str | None = None):
        all_facts = bb.read("facts").facts_of(tick)
        retrieved = dict(bb.read("retrieval"))
        notefacts = dict(bb.read("notefacts"))
        belief = bb.read("belief")
        trust = bb.read("trust")
        summary_view = SimpleNamespace(open_findings=bb.read("findings"),
                                       hypotheses=belief, trusted_tags=trust)
        facts, extra = all_facts, {}
        if side is not None:
            # the side's view: its facts, its cases, its notes; retrieval and
            # belief themselves are not split (decision 4)
            facts = self.sides.facts_for_side(all_facts, side)
            retrieved["cases"] = self.sides.cases_for_side(retrieved.get("cases", []), side)
            if self.sw["notes"] and self.sw["note_source"] == "raw":
                # raw notes: by the note's own tags (a note with none goes to both);
                # bev notes on: by bev's reading (reports/bev_ideas.md, idea 6)
                retrieved["notes"] = [n for n in retrieved.get("notes", [])
                                      if side in routed_note_sides(bb, n, self.bev_notes)]
            elif self.sw["notes"]:
                # note-facts: by the note-fact's own subjects (commit 0 design)
                notefacts = {k: v for k, v in notefacts.items()
                             if v.get("status") != "ok" or side in self.sides.notefact_sides(v)}
            else:
                # raw notes (the notes-section ablation): by the note's tags
                retrieved["notes"] = [n for n in retrieved.get("notes", [])
                                      if side in self.sides.note_sides(n)]
            extra = {"max_fact_lines": SIDE_FACT_LINES, "side_note": self.side_note[side],
                     "other_line": self.sides.other_side_line(all_facts, side)}
        prompt, line_map, hint, info = compact.build_diagnosis(
            self.sw, self.templates, facts=facts,
            level_cap=evidence_max_facts(level, rung), retrieved=retrieved,
            notefacts=notefacts,
            recordfacts=list(bb.read("recordfacts")), belief=list(belief),
            untrusted=sorted(set(self.tags) - set(trust)),
            wm_text=wm_summary(summary_view, self.tags), now_s=submit_s,
            evidence_tick=tick, letters=self.letters, cap=self.cap,
            guard_cpt=self.guard_cpt,
            tick_signature=bb.read("signature").get("signature", {}), **extra)
        line_map["side"] = side
        if self.rank_only:
            hint["rank_only"] = True
            line_map["rank_only"] = True
        info.update(side=side, fact_ids=list(line_map["facts"]),
                    case_ids=[c["case_id"] for c in line_map["cases"]])
        line_map["info"] = info
        diag = self.diag

        def work():
            if code_text is not None:           # one_code: no model call
                with bb.step(NAME):
                    env = code_answer(code_text, NAME, tick, compact.check_rank_only_shape)
                    env.retrieved_cases = list(line_map["retrieved_cases"])
                    return env
            with bb.step(NAME):
                diag.calls += 1
                env, failed = call_model(
                    diag.backend, prompt, NAME, self.cap, hint, NAME, tick,
                    compact.check_rank_only_shape if self.rank_only
                    else compact.check_diag_answer_shape, repair_template=self.repair,
                    log_prompts=diag.log_prompts)
                diag.parse_failures += failed
                diag.retries += env.retries
                env.retrieved_cases = list(line_map["retrieved_cases"])
                return env

        job = scheduler.new_job(NAME if side is None else f"diag_{side}",
                                evidence_tick=tick, priority=priority_for(level),
                                max_answer_tokens=self.cap,
                                submit_s=submit_s, work=work,
                                side="all" if side is None else side)
        job.line_map = line_map
        if self.grammar and self.rank_only:
            job.grammar = grammar.to_gbnf(grammar.rank_only(len(line_map["cases"])))
        elif self.grammar:
            # exactly the lines THIS prompt showed
            job.grammar = grammar.to_gbnf(grammar.diagnosis(
                len(line_map["facts"]), len(line_map["cases"]),
                len(line_map["context"]), line_map["letters"],
                with_group=self.sw["group_letters"]))
        return job
