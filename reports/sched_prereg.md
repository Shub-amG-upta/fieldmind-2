# Scheduling study — pre-registration

Committed before any study run on the board. Everything here is fixed in code by
`bench/sched_study.py` (the matrix) and `configs/sched_study.yaml` (the system). A change
after the first board run is recorded below under "Amendments" with its date and reason,
never made silently.

## Question

How should model work be placed and ordered across the QIDK's NPU and CPU lanes when the
plant tick arrives faster than the model lanes can finish everything? Measured as deadline
misses, answer age and accuracy, per placement policy, at two loads, for two configurations
of the best system.

## The system

- Best system: `configs/v3.yaml` (split diagnosticians, grammar-constrained ID answers,
  compact prompts, merge rule `hybrid`) with the accuracy fixes in code.
- **Same GGUF on both lanes** (HUMAN DECISION 2026-11-09, plan rule 3):
  `Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf`, NPU lane `--device HTP0 -ngl 99`, CPU lane
  `--device none -ngl 0`, both `-c 4096 -np 1 -fit off --cache-ram 0 -lv 4`.
- `v3`: the system above. `v3x`: the same plus the decision model (Laya,
  `configs/laya_board.yaml`) with `explain=on,clear_skip=on`; in real time explain is a
  two-stage job (Llama ranks, Laya cites, released together).
- Real time folds an answer one tick after its evidence at the earliest (the tick never
  waits). Lane rates follow measured calls (`adapt_rates: true`, EWMA 0.3).
- Lane planning rates for Llama 3B on both lanes are **measured on the board first**
  (HANDOFF_SCHED.md step 2) and written into `configs/sched_study.yaml`; the board runner
  refuses real time until `lane_rates_measured: true`.

## Matrix

| factor | levels |
|---|---|
| policy | `fixed` (v3's table: both diagnosticians NPU, verifier CPU), `earliest_finish`, `tick_alternation`, `priority_reserved` |
| configuration | `v3`, `v3x` |
| load (wall seconds per 30 s plant tick) | 10 (3x real time), 5 (6x) |
| episodes | boiler `dev_B01_tube_leak` (170 ticks), boiler `dev_A02_fcv_seize_fast` (80 ticks), Cranfield `cf_F5_5.1_slugging_conditions` (75 ticks, real rig data) |
| lockstep reference | one per configuration and plant, `fixed` placement |

32 real-time tests + 4 lockstep references (`bench/sched_study.py plan` prints every
command). One run per cell, plus the repeat cells below.

**Repeats (run-to-run spread).** `sched_v3_fixed_t5_boiler` and
`sched_v3_earliest_finish_t5_boiler` run a second time (`--again`). The spread between the
two runs of a cell (deadline-miss count, group top-1) is the smallest difference called a
difference; anything smaller is reported as a tie.

**Order.** Lockstep references, then load 10 s, then 5 s (`cells()` order); the chip is let
cool between episodes by the runner (`--cool-margin 5`, `--cool-max 900`).

**Board time.** Real-time cells: 325 ticks x (10 + 5) s x 8 policy-configurations = 10.8 h,
plus the lockstep references (earlier v3 lockstep board runs: 1.0–2.0 s per tick), the repeats
and cooling gaps. Split over sessions; a cell resumes where it stopped.

**Where the agent runs.** As in every earlier board run, the agent runs on the laptop and the
model calls on the board (lanes over `adb forward`). The agent on the phone (Stage B) is checked
separately (identity with the laptop, hard-path timing); driving the study from the board is a
later step. Decision (conservative: changes less), recorded in reports/sched_stage_b.md.

## Episodes (decision, 2026-11-10)

The plan's proposal was Cranfield F1, F5 and boiler dev B01. Counted on the mock backend
(deterministic triage): no Cranfield dev episode and not dev_B01 has a single URGENT tick, so
P1 work (urgent diagnosis) would never occur and `priority_reserved` could not differ from
`earliest_finish`. Boiler dev episodes with URGENT ticks: A02 (60 of 80), A03 (87 of 110),
D01 (99 of 310), D03 (71 of 150). Cranfield F1 is replaced by dev_A02 (shortest, most
URGENT share). This also lowers board time (Cranfield F1 has 149 ticks). Dev episodes only: nothing is tuned, and the 30 reporting episodes stay
unread.

## Metrics (per cell, episodes pooled; per run with `table --per-run`)

| metric | definition |
|---|---|
| deadline miss, P1 / P2 / P3 | a model call whose end is later than (deadline in ticks x wall tick) after the wall tick of its evidence; P1 1/3 tick, P2 1 tick, P3 2 ticks (base.yaml `rt_deadline_ticks`, DERIVED from the plan's 10 / 30 / 60 s at a 30 s tick). Recounted from the per-call spans. |
| replaced before running | jobs superseded by newer evidence while waiting (no call, so no deadline entry) |
| answer age | (call end - wall tick of its evidence) / wall tick, p50 and p95 |
| stale dropped | answers the gate refused as too old (stale rule: at most one tick old, or that side's evidence unchanged) |
| lane overlap | seconds both model lanes ran a call / busy seconds of the less busy lane |
| calls per lane | NPU / CPU / decision-model lane |
| accuracy | group top-1 (T2) from the evaluator, next to the lockstep reference |
| chip temperature | before and after every episode (runner) |
| energy | **not measured** (no meter); recorded as null |

## Primary comparison and what counts as winning

At each load and configuration, each policy against **real-time `fixed` at the same load**:

- a policy wins if its pooled P1 + P2 miss count is lower than `fixed`'s by more than the
  repeat spread, **and** its group top-1 is not lower than `fixed`'s at the same load by more
  than 0.02;
- the lockstep reference is reported as the ceiling (no lateness), not as the bar.

Why the bar is real-time `fixed` and not lockstep (decision recorded before any board run):
in real time every answer folds at least one tick after its evidence, under every policy, so
part of any real-time vs lockstep gap belongs to real time itself, not to a policy. On the mock
backend (plumbing only, no reasoning) that gap was -0.031 group top-1 on dev_B01 alone (0.922 vs
0.953) and +0.008 pooled over dev_B01 + dev_A02 (0.797 vs 0.789): the mock does not settle its
size or sign. Comparing each policy with `fixed` at the same load removes it.

Secondary: answer age p95; lane overlap (does using both lanes at once slow each lane — the
plan's shared-memory risk, measured separately in HANDOFF_SCHED.md step 3).

## Predictions (written before any study run)

From earlier board runs of the same Llama GGUF on the NPU (`results/benchmarks/bevideas_B_skip`,
`multi_v3`): on these boiler episodes split v3 makes **at most one** diagnostician call per tick
(dev_A02 / ep_A02: 35–38 of 80 ticks; dev_B01 / ep_B01: 51–53 of 170), each 2.8–3.1 s median,
p95 3.3–3.9 s. Those runs had Gemma 1B on the CPU lane (verifier only, a few calls per episode).

Cranfield F5 is different: in the mock lockstep reference (call decisions come from facts, not
from the model) it calls **both** sides on 43 of 75 ticks and one side on 31 (boiler: never both).
No Cranfield board timing of the split diagnosticians exists here; the predictions assume a call
takes about as long as on the boiler.

1. **10 s per tick:** no queue forms (boiler: one call of at most ~4 s per 10 s; Cranfield: two,
   ~6–8 s). P2 and P3 misses near zero under every policy; the four policies tie.
2. **5 s per tick, boiler:** still at most one ~3–4 s call per tick, so no sustained NPU queue; P2
   misses stay low and the policies tie. `earliest_finish` and `tick_alternation` move work to the
   CPU lane, whose Llama speed is unknown until step 3; if it is much slower, those two policies
   *add* P2 misses and answer age.
3. **5 s per tick, Cranfield:** under `fixed` both sides queue on the NPU (~6 s of calls per 5 s
   tick on 43 ticks), so the second side's answer misses P2 on most of those ticks. This is the one
   contended cell of the registered matrix; whether `earliest_finish` / `priority_reserved` beat
   `fixed` there depends on the CPU lane's Llama speed (a second-side call on the CPU must finish
   within one tick).
4. **P1** (URGENT ticks, dev_A02 only): its deadline is 1/3 tick = 3.3 s at 10 s and 1.7 s at
   5 s, at or below a single call's time, so P1 misses about half the time at 10 s and nearly
   always at 5 s, under every policy.
5. Real time scores below lockstep at every load (answers fold one tick late). On the mock backend
   the gap was 0.031 group top-1 on dev_B01 alone (0.922 vs 0.953, first dry run); pooled over
   dev_B01 + dev_A02 it was +0.008 (0.797 vs 0.789), so the direction is not settled by the mock.

## Open decision (Shubham, before step 4 of HANDOFF_SCHED.md)

If predictions 1–3 hold, the registered loads separate the policies in one cell only (Cranfield
at 5 s): the boiler episodes never contend for a lane. Options, none acted on:

- **A. Keep 10 s / 5 s.** A clean headroom result (policy does not matter below saturation) and a
  P1 feasibility result; 10.8 h.
- **B. Replace 10 s with a load where one call outlasts the tick (2–3 s per tick)** so queues,
  replacement and lane choice matter; deadlines in ticks become infeasible there, so answer age,
  replaced jobs and accuracy would be the primary measures at that load. 5 s + 2.5 s: 325 x 7.5 x
  8 = 5.4 h.
- **C. A capacity sweep** (e.g. 5, 4, 3, 2 s) for `fixed` and `earliest_finish` only: the fastest
  tick each policy sustains (P2 misses under 5 %); 325 x 14 x 4 = 5.1 h.

Whichever is chosen is entered under "Amendments" with its date before the first real-time cell.

## Not tuned, not changed

No threshold, band edge, deadline or stale rule is changed for or during the study. Policies
are compared as built (`fieldmind/multi/realtime.py`, commit of this pre-registration).

## Amendments

(none)
