# 02. How to read the bev-decider-3 data

## 1. Which runs

| label | run folder | config | what it is | date |
|---|---|---|---|---|
| **v3** | `results/benchmarks/multi_v3` | `configs/v3.yaml` | multi-agent v3 (hybrid merge rule, no group letters, raw notes) | 8 Oct |
| **bev3** (bev-decider-3) | `results/benchmarks/bev3_armB` | `configs/bev3.yaml` = v3.yaml + the decider | the same, plus bev-decider on HTP0 | 8 Oct |

Common to both:
- QIDK SM8650 board;
- Llama 3.2 3B on the NPU lane, Gemma 3 1B on the CPU lane;
- lockstep mode, temperature 0;
- the same **12 reporting episodes**: N01 (normal), A01–A03, B01–B03, C01–C03, D01, E01.

Scored ("fault") episodes: the **10** with a library cause (A01–D01). E01's fault has no library case; N01 has no
fault.

Checks that passed:
- every bev3 decider call succeeded (633, 0 failed, 0 rejected);
- every run's published ranking is reproduced exactly by replaying its saved answers (12 of 12 for each system).

## 2. Data files (`data/`)

| file | content |
|---|---|
| `bev3_vs_v3_summary.csv` | headline metrics for v3, bev3, belief alone and "bev3 decider removed", on three episode sets: `10 fault episodes`, `first 4 (A01 B01 C01 D01)`, `all 12 episodes` (cost and speed) |
| `bev3_vs_v3_per_episode.csv` | one row per episode: every metric for v3 and bev3 side by side, plus the decider's own stats (calls, picks right, filler picks, ticks fixed / broken) and chip temperatures |
| `model_call_costs.csv` | one row per (system, agent): calls, mean prompt and answer tokens, mean prefill and decode seconds, decode share, tok/s, median and total call time. Systems: single agent (for contrast), v3, bev3 |
| `decider_picks_by_family.csv` | on decider-call ticks after fault onset: share where the decider's pick, Llama's first pick and belief's top case are in the true group, by fault family |
| `decider_options_per_call.csv` | how many candidate causes each decider call had |
| `decider_trigger.json` | decider calls against non-quiet ticks |

## 3. Metrics

| metric | meaning |
|---|---|
| **group top-1** (headline) | share of scored ticks (fault onset onward, ticks with a published ranking) whose published **top cause is the true case or its look-alike**. Look-alikes are cases the six sensors can't tell apart |
| belief alone | the same for **belief**, the code-only ranking. It is identical in both systems because code computes it. This is the bar the models must beat |
| bev3 decider removed (replay) | the **same bev3 run**, re-scored after replaying its saved answers **without the decider's bonus**. It shows the decider's effect with zero run-to-run model noise |
| decider ticks fixed / broken | scored ticks where the decider's bonus turned a wrong top cause right / a right one wrong (from that replay) |
| exact top-1 | the exact true case on top (no look-alike credit). Not defined for C01 and C03, whose true cause is held out of the library |
| right group in top 3 | the true group anywhere in the published top 3 |
| right before the trip | group top-1 over ticks before the boiler trip (only A01–A03 and D01 have a trip) |
| first right after onset | minutes from fault onset to the first tick with the right group on top |
| lead time (exact) | minutes before the trip that the exact true case first reached the top |
| mean of episodes / pooled | "mean" averages the per-episode values (each episode counts once). "Pooled" divides all right ticks by all scored ticks (long episodes count more). Both are in the summary |
| decider pick right / Llama first pick right / belief top right | on ticks where the decider was called (after onset): is that source's first choice in the true group? |
| mean prefill / decode s | the board server's own timing of the two phases of a call: reading the prompt, and writing the answer |
| wall time | the episode's run time, laptop clock (agent code on the laptop plus model calls on the board) |

## 4. The numbers that matter (10 fault episodes)

| | v3 | bev3 | bev3, decider removed | belief |
|---|---|---|---|---|
| group top-1, mean of episodes | **0.703** | 0.680 | 0.707 | 0.575 |
| group top-1, pooled | **0.731** | 0.702 | 0.732 | 0.554 |
| decider ticks fixed / broken | – | 1 / 33 | – | – |

Per episode, v3 against bev3:

| | A01 | A02 | A03 | B01 | B02 | B03 | C01* | C02 | C03* | D01 |
|---|---|---|---|---|---|---|---|---|---|---|
| v3 | 0.89 | 0.58 | 0.81 | 1.00 | 1.00 | 0.60 | 0.63 | 0.32 | 0.38 | 0.83 |
| bev3 | 0.88 | 0.53 | 0.80 | 0.92 | 0.94 | 0.53 | 0.67 | 0.32 | 0.38 | 0.83 |

How to read it:
- **bev3 equals v3 within noise everywhere except the tube-leak episodes (B01–B03) and A02,** where the decider
  lowered it.
- **"Decider removed" (0.707) ≈ v3 (0.703).** The Llama answers were nearly the same in the two runs, so the
  whole gap between v3 and bev3 is the decider, not noise.

## 5. Why the decider lowered accuracy (verified on specific ticks)

1. **Its picks are less accurate than Llama's on this task** (`decider_picks_by_family.csv`):

   | family | decider | Llama first pick | belief |
   |---|---|---|---|
   | A feed water | **0.67** | 0.65 | 0.40 |
   | B tube leak | 0.31 | **0.69** | 0.44 |
   | C fuel | **0.72** | 0.45 | 0.66 |
   | D high-CV coal | 0.28 | 0.67 | **0.77** |
   | all | 0.47 | **0.64** | 0.51 |

   It picked a filler case (flat on every sensor) on 18% of calls, 35% on tube leaks. The guard blocks those, but the
   rest of its tube-leak and high-CV-coal picks are mostly wrong.

2. **Its bonus shares one cap with Llama's.** When Llama has already pushed the right case close to the 1.2 cap, the
   decider's agreement adds almost nothing. Its push on a wrong case is added in full.
   - Example: B01, tick 54. The right case had 1.05 from Llama and was capped at 1.2. The decider had built up 1.05 on
     a wrong case, which overtook the right one by 0.05.

3. **Where it can act.** Under `hybrid` the decider can't change the top cause on weak or tied ticks (the Llama picks
   lead there). It acts on "clear" ticks and in the order behind Llama's picks. Of the 33 broken ticks, 19 were clear,
   12 tied and 2 weak. On every one, Llama's picks didn't lead (on the tied and weak ones Llama had no usable
   pick), so the decider's bonus decided the order.

## 6. Speed and cost (all 12 episodes)

| | v3 | bev3 |
|---|---|---|
| Llama calls | 609 | 607 |
| Llama answer (decode) tokens, diagnosticians | 17,284 | 17,360 |
| decider calls / prompt tokens / answer tokens | – | 633 / 251,650 / **0** |
| median Llama diagnosis call | 3.05 s | 2.98 s |
| median decider call | – | 0.37 s |
| total model-call time | 1,794 s | 1,981 s |
| wall time | 1,947 s | 2,177 s (+12%) |
| ticks over the 30 s budget | 0 | 0 |
| slowest tick | 7.5 s | 7.5 s |

## 7. Figures

| figure | how to read it |
|---|---|
| `40_bev3_vs_v3_accuracy.png` | left: per-episode group top-1 (blue v3, teal bev3, grey belief). Right: means, including the decider-removed replay (light teal) |
| `30_decider_effect.png` | **top panel = bev3**: grey = same run without the decider, teal = published; labels = ticks fixed / broken. Bottom panel is bev-decider-2 (ignore for these slides) |
| `31_decider_picks_by_family.png` | **left panel = bev3**: decider (teal), Llama first pick (blue), belief (grey), by family. Right panel is bev-decider-2 |
| `41_call_time_split.png` | left: one call split into prefill (blue), decode (red), other (grey) for four kinds of call. Right: total model time over 12 episodes, v3 vs bev3, by agent |
| `26_call_latency.png` | box plots of call time by agent, lane and model (log scale); bev-decider is the last box |
| `14_bench_v3.png`, `16_bench_bev3.png` | one-page summaries per system: accuracy vs belief, wall time and model calls per episode |
| `33_timeline_A01.png`, `34_timeline_B01.png` | each cell is a 30 s tick: green = right group on top, red = wrong. Rows include other systems for context |
| `05_flow_bev_decider_3.png`, `06_board_deployment.png`, `03_flow_multi_v3.png` | architecture |

## 8. Pitfalls

1. **One run per system, on the reporting episodes.** v3's design was chosen on these episodes. Say "on the episodes
   measured".
2. **Don't present 0.680 vs 0.703 as noise.** The same-run replay shows it is the decider's effect (1 tick fixed, 33
   broken).
3. **Don't claim the decider "saves decode" in these runs.** Llama's decode tokens were unchanged; the decider was
   added on top.
4. **Conformance was not run:** the board version wasn't compared with the original model's answers. A port defect
   can't be excluded as part of the low pick accuracy.
5. **Chip temperature differed:** v3's episodes started at about 57 °C on average (a restart reset its cooling
   target), bev3's at about 46 °C. Model call times were not affected (Llama median 3.05 against 2.98 s).
6. **Times:** call times are board times; tick and wall times include laptop code.
7. **Energy was not measured.**
