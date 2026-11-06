# Laya L1 — Laya as the System One model (laptop accuracy, NPU port check) — report

## Status
PARTIAL — pre-registration only (this section is committed before any Laya answer is seen). Plan:
`~/.claude/plans/declarative-seeking-rabin.md` (approved 2026-11-07). Branch `laya`, from
`mine/breadth-board-runs` at `ffc4312`.

All boiler data is synthetic; Cranfield is real rig data; TEP is a simulated benchmark. Laya runs on the
laptop CPU (Apple M2) in Track A: its timings are laptop timings, never NPU timings. Energy: null.

## Pre-registration (fixed before any Laya answer)

### Model
- Laya, convaiinnovations, Apache 2.0, `pip install laya` in `.venv-laya/` (versions in
  `bench/requirements-laya.txt`, Hugging Face revision of each checkpoint recorded below once downloaded).
- **Primary checkpoint: `convaiinnovations/laya`** (English root). Sensitivity rows: the `typed-decisions` and
  `multilingual` subfolders. They are reported next to the primary and never selected on results.
- Each checkpoint's own default context length. Truncation is measured and reported, never fixed in L1 (a
  shortened-criteria variant would be its own pre-registered step).

### Requests (never edited for Laya)
- Questions: the existing `multi.bev.questions` sentences in `configs/base.yaml`, unedited. `q_root` is the
  decider's signed sentence; the others are still PROPOSED (reports/bev_ideas.md), so any `on` result from
  them is reported as resting on unsigned questions, exactly as for bev.
- Criteria: the agents' own option texts (`DeciderAgent.offered`, `bev.py` builders), unedited.
- `multi.bev.noul_threshold` stays 0.5 (DESIGN, as bev; range 0.3–0.7).
- `multi.bev.first_threshold` for Laya: the table from `bench/bev_calibrate.py` on boiler dev shadow runs only.
  The tool picks nothing; the threshold is a **human decision**, so `first: on` with Laya is not run until it
  is given (stop rule 1). The tool accepts only boiler `dev_*` episodes; Cranfield and TEP get no threshold.

### Sets
| set | episodes | requests from | compared with |
|---|---|---|---|
| boiler dev quick set | 8 fault + 2 normal (`dev_A01 … dev_N02`) | mock run, `configs/bev3.yaml` | belief, retriever; bev per idea from `bevideas_shadow` |
| Cranfield dev | 6 fault | mock run, `configs/bev3.yaml,configs/cranfield.yaml`; and the board run's journal | belief, retriever, bev (`cranfield_dev_v3_bev`) |
| TEP board subset | 20 fault + 2 normal (dev runs, 16 h) | mock run, `configs/bev3.yaml,configs/tep.yaml` | belief, retriever |
| boiler reporting | 10 fault (`bev3_armB`) | rebuilt from the run file | bev (reported once, never used to decide) |

Requests from mock runs carry the mock diagnosticians' top cases (retriever order), which Llama matched in
98.5–99.6% of its board answers. They are labelled "mock diagnosticians".

### Metrics
- **Decider pick accuracy**: on decider requests whose tick is at or after fault onset (tick k dated at
  (k+1)·tick, as T7), the share where the pick is in the episode's true group (summary `true_group`). Same
  for belief's top (offered[0]), the retriever's top (line 1 of that tick's diagnostician prompt, either
  side), bev where recorded, and chance (mean share of offered cases in the true group).
- First-option rate and chance; **shuffle invariance**: share of requests whose choice is unchanged when the
  options are given in one seeded shuffled order (seed 20261107, derived per request).
- Truncation rate per checkpoint and per request kind.
- Interval: bootstrap over episodes (2,000 resamples, seed 20261107), because consecutive ticks are correlated.
- Per bev idea (shadow): Laya's answer distribution and agreement with bev on the same boiler dev requests.

### Rule for going to Track C (board accuracy run)
Laya's decider pick accuracy is higher than the retriever's top on the same requests on **at least 2 of the 3
dev sets** (boiler dev, Cranfield dev, TEP subset). Otherwise L1 is reported as a negative zero-shot result
and L2 (fit on a training split) is proposed instead. Track B (port feasibility) runs either way.

### Track B pass rule (host parity of the GGUF backbone)
Pinned `b11371` converter; F16 and Q8_0 (every matrix Q8_0). Laya's own head on the GGUF hidden states against
PyTorch end to end: top answer identical on all compared requests (as bev's conformance); max |Δp| reported.

### Clarifications added after scoring started, before any Laya answer was read (2026-11-07)
- Population for pick accuracy: every decider request at or after fault onset in an episode with a true group,
  held-out episodes included (their true cause is never offered, so every model scores 0 there). A
  "library episodes only" row is reported as secondary. "Same requests" for the retriever comparison means the
  requests whose evidence tick also has a diagnostician prompt (the retriever's top exists).
- Request sources: board runs keep every decider prompt verbatim in their run files (`bev3_armB`: 633 of 633;
  `cranfield_dev_v3_bev`: 347 of 347), so nothing is rebuilt; `DeciderAgent.state_text` reconstruction (plan A4)
  was not needed.
- Onset dating: (k+1)·tick as pre-registered (T7). The evaluator's T2 dates ticks at k·tick; the two differ by
  one tick at onset. Recorded, not changed.
