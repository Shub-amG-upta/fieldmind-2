# Breadth B1, Step 0 — Cranfield 2015 benchmark data — report

## Status
PARTIAL — data acquired, verified and converted to FieldMind episodes; normal-data fingerprint
built. BLOCKED for Step 2 on one decision: the planned liquid mass balance does not close on
normal data (below).

## Source
| item | value |
|---|---|
| data | MATLAB File Exchange 50938, "A Benchmark Case for Statistical Process Monitoring – Cranfield Multiphase Flow Facility" (Yi Cao, v1.1.0, BSD licence), `cvatutor-1.1.0.zip`, sha256 `3af7686da0fd963b1f7814be1bb59b5a8b990df2cce7b553de3debcf67b8ba6a` |
| why not IEEE DataPort | the DataPort copy (doi 10.21227/0b7j-q780) needs a paid subscription despite its CC-BY licence |
| paper (tag meanings, fault windows) | Ruiz-Cárcel, Cao, Mba, Lao, Samuel, "Statistical process monitoring of a multiphase flow facility", Control Eng. Practice 42 (2015) 74–88 — Table 1 (variables), Table 3 (faults), Tables 4–9 (fault start/end) |
| not used for this data | Ruiz-Cárcel et al. 2016 (CEP 54) — a different experiment on the same rig (17 measurements, 3 other faults); kept for rig description only |
| in git | no: third-party data and generated episodes are gitignored; the two paper PDFs are left untracked (publisher copyright) |

## What the data is
- 24 variables (Table 1), 1 Hz, no missing values. Variable 24 (PT417, 2" line pressure) is used by
  the authors only for fault case 6.
- Normal: T1, T2, T3 (10,372 / 9,825 / 13,200 s), with deliberate air/water set-point changes.
- Faults: 6 cases, 16 data sets (3/3/3/3/2/2). Types (Table 3): 1 air line blockage, 2 water line
  blockage, 3 top separator input blockage, 4 open direct bypass (incipient); 5 slugging
  (intermittent; 2 and 3 fault windows); 6 pressurization of the 2" line (abrupt, runs to the end).

## Conversion (`data/cranfield/convert.py`)
- Episodes in the existing format (`timeseries.csv`, `ground_truth.json`, empty notes), `t` = sample
  index in s, 24 tags named `<location>_<magnitude>` (Table 1), tick 30 s (as the boiler).
- `ground_truth.fault_windows` = Tables 4–9 exactly; `fault_onset_t` = first start; no trip.
- **Pre-registered split** (before any agent run; needs advisor confirmation): dev = 1.2, 2.2, 3.2,
  4.2, 5.1, 6.1 (one set per fault); report = the other 10. T1–T3 are calibration only, not scored.
  False alarms will be measured on the pre-fault part of each fault set, as the paper does.

## Verification
| step | result |
|---|---|
| ran the module | `--check` PASS; 16 episodes written (6 dev, 10 report) |
| self-tests | `tests/test_cranfield_data.py` 4 passed (skip when the archive is absent) |
| independent re-derivation 1: column order + units | on all 8 steady sets the measured pre-fault water (col 9) and air (col 8) flows equal the paper's set points (e.g. set 1.2: 2.000 kg/s vs 2, 0.0417 vs 0.0417 Sm³/s; worst 2.3 air 0.0416 vs 0.0417, 0.2 %). Col 5 = 0.0997–0.1001 MPa on 7 of 8 sets vs the paper's "pressurized to 0.1 MPa" (set 3.2: 0.1071) |
| independent re-derivation 2: column order from physics | pressure falls along the flow path on 100 % of normal samples (PT312 > PT401 > PT408; PT403 > PT501); col 6 equals PT401 − PT408 to a median 0.40 % (a separate dP transmitter, so not exact) |
| independent re-derivation 3: fault windows | where `EvoFault` is an on/off flag (cases 4–6) its segments match the tables within 1–5 s (e.g. 4.2: 850–3850 vs 851–3851; 5.2: 8052 vs 8057) |
| mutation check | fault start 4.2 851→951: 2 tests fail; set 2.3 air set point 0.0417→0.0278: 1 fails; columns 1/2 swapped in the data: 1 fails. The first version of the checks did NOT catch a column swap at conversion time (only against already-written episodes); the physics check above was added because of that |

## Direction checks
| claim | expected | measured | |
|---|---|---|---|
| air flows from supply to riser bottom | PT312 > PT401 | 100 % of normal samples | OK |
| hydrostatic head in the riser | PT401 > PT408 | 100 % | OK |
| top separator above the 3-phase separator | PT403 > PT501 | 100 % | OK |
| riser top feeds the top separator | PT408 > PT403 expected | **0.006 %** (PT403 reads higher almost always) | **unexplained**, see below |

## Constants introduced
| symbol | value | provenance | range | affects |
|---|---|---|---|---|
| `TICK_PERIOD_S` | 30 s | DESIGN: same as the boiler so the cost study compares like with like | 10–60 s (to be swept in Step 4) | number of assessments and model calls per episode |
| `DEV_SETS` | 1.2, 2.2, 3.2, 4.2, 5.1, 6.1 | DESIGN, pre-registered | — | which sets may drive keep/revert decisions |
| fault windows, durations, set points | Tables 3–9 | CITED | — | ground truth |

## Normal-data fingerprint (`data/reference/cranfield/fingerprint.json`)
Per tag over T1–T3: range, p0.1/p99.9, per-sample step noise, lag-1 autocorrelation, 3-min MAD,
and |OLS slope| p50/p85/p99.7 over 3/5/10-min windows taken every 30 s. Highlights:
- Like the boiler's real reference data, most tags are very smooth (lag-1 ac 0.997–1.000).
- **Three tags sit exactly flat for minutes on healthy data** (3-min MAD minimum 0): FT407 flow,
  FT407 temperature, PT417. The boiler's stuck-instrument rule would mark them untrusted on normal
  operation; Step 2 must set validity per tag from this file, not copy the boiler's.
- PO1 pump current is quantized/noisy (lag-1 ac 0.56).

## Disagreements recorded, not resolved
1. **Liquid mass balance does not close (STOP for Step 2).** Plan Step 2 named an air balance; there
   is no air-outlet meter among the 24 variables, so the only candidate is liquid: water in (FT104)
   vs top-separator liquid out (FT406) + accumulation (LI405 slope × π·0.25² m² × 1000 kg/m³; the
   0.5 m diameter is from the 2016 paper, same rig). On 5-min blocks of T1/T2/T3: water in 2.61 /
   2.45 / 2.59 kg/s, FT406 0.52 / 0.38 / 0.60 kg/s, residual median **1.85 / 1.56 / 1.87 kg/s**.
   FT407 (riser-top flow) sits at its floor (< −0.24 kg/s) 50–58 % of the time and is uncorrelated
   with water in (r −0.05…0.09). Cause **unexplained** (candidates, untested: an unmetered liquid
   path out of the top separator; Coriolis meters unreliable in two-phase flow). Not tuned.
2. **PT403 > PT408** although flow runs from the riser top into the top separator. Unexplained
   (candidates, untested: transmitter elevation, calibration offset).
3. **Column 7 units.** Table 1 says MPa; values reach 1.6, and col 7 / (PT408 − PT403) has median
   −138. Unexplained; the tag is kept with its measured values, unit marked as the paper's.

## Blocked / needs a decision
- **What replaces the BALANCE family for Cranfield** (options in the chat message of 2026-11-05):
  (a) no balance family: LIMIT, RATE and signatures only; (b) relations FITTED on the normal sets
  (e.g. FT406 vs FT104) and their residual used as a check — fitted, not derived; (c) a derived
  hydrostatic relation (riser dP vs liquid hold-up) — needs a hold-up model, larger work.
- Advisor confirmation of the dev/report split.

## What I could not verify
- The meaning of `EvoFault` for cases 1–3 is taken from the paper's text (valve angle), not from a
  data dictionary.
- Whether column 7's unit is really MPa.
