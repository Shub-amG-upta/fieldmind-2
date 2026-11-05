# Breadth B2 — Tennessee Eastman Process (TEP) asset pack (mock) — report

## Status
DONE on the mock backend: FieldMind runs on TEP (52 variables, 3-min samples) in all three
configurations; 22 dev + 110 report episodes scored; a 22-episode board subset and a QIDK handoff
(`HANDOFF_QIDK_BREADTH.md`) are ready. Branch `breadth-tep`. **Mock numbers measure the deterministic
and retrieval layers only; they are NOT agent results.** Energy: null. TEP data is SIMULATED.

## Human decisions (2026-11-07)
1. Signatures FITTED on the official faulty TRAINING runs (1–100 of 500 per fault); frozen in commit
   `b8970d7` (2026-11-06 04:30:25 +0530) before any test run went through the agent.
2. Episodes: test run 1 of each fault = dev, runs 2–6 = report; fault-free test runs 1–2 dev, 3–12 report.
3. Signature vocabulary for TEP: movement + level + variability (after the movement-only fit failed, below).
4. Board: option A, the 22 dev runs cut to 16 h (8 h normal + 8 h fault).

## Decisions taken (by me, recorded)
1. **Plain tag names, neutral case ids, no benchmark words in prompts** (`reactor_pressure`, `PF-06`;
   tests assert no "tennessee", "eastman", "idv", "xmeas", "xmv", "stream 4" in prompts or case text):
   Llama has read TEP papers; numbering would let it recognise the benchmark.
2. **Windows in samples** (one per 3 min): rate 30 min (10), signature 60 min (20), frozen and
   variability 60 min (20; analysers hold their value 6–15 min). DESIGN; range 30–120 min.
3. **Write audit off for TEP only** (`multi.audit_writes: false`). Profiled: the audit fingerprinted
   the ever-growing event timeline after every step, 98 % of run time on 960-tick episodes
   (4.6 min → 5.8 s for two episodes, results identical: 0 differences). The single-writer API check
   stays on; the audit stays on for the boiler, Cranfield and the tests (same agent code).
4. **Board runner** (`bench/benchmark.py`, `bench/stage_monitor_multi.episode_dir`): finds `cf_*`/`tep_*`
   episodes, takes comma-separated overlays, and states the data's nature per plant (the header said
   "all plant data is synthetic" for every run, false for Cranfield). Boiler paths unchanged; its tests pass.

## Verification
| step | result |
|---|---|
| data | four .RData files, sizes equal the Dataverse listing; sha256 recorded and checked; row order (run, fault, sample) asserted on every block; a fault run equals its fault-free twin until sample ~160 (the 8 h onset) |
| column order, re-derived | fault-free training means equal the published base case: reactor pressure 2705 kPa, reactor level 75 %, reactor temperature 120.4 °C, separator/stripper levels 50 %, compressor work 341.4 kW. **PROVISIONAL**: base values quoted from memory of Downs & Vogel Table 4; the paper (user download via IIITH) has not been read yet |
| fit = agent | the fitting code's slope, direction and variability equal the agent's own functions: 25,012 window×tag pairs, max slope difference 4.4e-16, 0 direction mismatches (and a test on 80 samples) |
| Step 1 identity | boiler dev × {single, multi, multi+v3} and Cranfield dev multi+v3: 0 differences, no summary number changed |
| self-tests | `test_asset_params.py` 4, `test_tep_pack.py` 9 (pass; data tests skip without the files); runner tests 28 |
| mutation checks | signature window ignored; T2 tick hard-wired; level sign flipped; variability on values instead of changes (the first version of that test did NOT catch it: a ramp was added); all caught after the fix |
| stop rule: prompt size | multi v3 dev: median 626, max **1,736** tokens; **13 of 22,563 calls over 1,280**, all the verifier (it shows every fact of the tick, "flagged, never cut", Phase 1 rule). Single/multi max 1,192. Within the 4,096 context. In the 16 h board subset: 1 call |

## Results (mock — NOT agent results)
| set | arm | detection | false alarms before fault | fault-free false alarms /h | top-1 | belief top-1 | AI invoked |
|---|---|---|---|---|---|---|---|
| dev | single | 0.853 | 0.239 | 5.53 | 0.403 | 0.193 | 0.708 |
| dev | multi v3 | 0.853 | 0.239 | 5.53 | 0.435 | 0.193 | 0.684 |
| report | single | 0.837 | 0.273 | 5.29 | 0.384 | 0.126 | 0.700 |
| report | multi | 0.837 | 0.273 | 5.29 | 0.384 | 0.126 | 0.700 |
| report | multi v3 | 0.837 | 0.273 | 5.29 | 0.416 | 0.126 | 0.672 |

Per fault (report, 5 runs each, multi v3): detection 1.00 on 1, 4, 6, 7, 12, 14, 19; 0.96–0.99 on
2, 8, 11, 13, 17, 18; 0.82–0.90 on 10, 16, 20; **0.53 on 5; 0.25–0.28 on 3, 9, 15** (≈ the
false-alarm rate: not detected, as the TEP literature reports for these three). Top-1 ≥ 0.85 on
1, 2, 4, 6, 14; 0.5–0.8 on 7, 12, 16, 17, 19; 0 on the seven faults with no fitted signature.
No fault went wholly undetected (every run has some alarm after onset).

## Findings
1. **Slope-only signatures cannot describe TEP faults.** The movement-only fit gave 12 empty and 2
   identical signatures: TEP faults are steps that controllers absorb, leaving tags flat at a new
   LEVEL, or random variations that change VARIABILITY. With level and variability, 13 distinct
   signatures (+ 7 faults with none: 3, 5, 9, 10, 11, 13, 15). Signature vocabulary, not tuning,
   decided this; it is a result for the paper.
2. **False alarms scale with the number of sensors.** Each check is fitted to fire 0.1–0.3 % of the
   time per tag (p0.1/p99.9, p99.7); with 52 tags and three check kinds, some check fires on ~25 %
   of fault-free ticks (5.3 /h). The boiler (6 tags) hid this. A per-tag threshold corrected for the
   number of tags is the obvious fix; NOT applied (a new, pre-registered step decided on fault-free dev
   data).
3. **Detection delay is not meaningful while false alarms are this high** (many faults show the
   same 11.4 min: the first scored tick after onset is often already alarming).

## Disagreements recorded, not resolved
1. Verifier prompt over the 1,280 budget on 13 calls (rule: flagged, never cut). Cap the verifier's
   facts to the cited ones plus the most severe? A behaviour change for every plant: needs a decision.
2. `Q2_heldout_cases_without_episodes` lists the boiler's held-out cases on TEP summaries (cosmetic, as
   for Cranfield).

## Blocked / needs a decision
- Downs & Vogel 1993 (via IIITH) → `docs/TEP_DownsVogel1993.pdf`, to confirm names, units and base
  values (the PROVISIONAL row above).
- Multiple-testing correction of the thresholds (finding 2); verifier fact cap (disagreement 1).
- Board runs (handoff ready).

## What I could not verify
- Any LLM result on TEP: all mock.
- Whether Rieth's runs used the revised (Bathelt 2015) or original simulator; the variable set is the same.
