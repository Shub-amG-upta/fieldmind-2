# bev conformance: the 8/24 mismatch is probably in the reference, not the board

This follows your T3 result in `reports/bev_measurement.md`. Thanks for running it and writing it down so clearly; it led
straight to this.

**In short:** the reference was most likely built with the wrong RoPE setting (RoPE encodes each token's position).
The board build is probably right. This file says how to check that, how to rebuild the reference, and what to send
back. About 30–45 minutes on the QIDK laptop. No benchmark reruns.

## What we saw

- 24 real dev requests. The input tokens were identical on the board and in the reference (24/24).
- The top answer matched only **8/24**: median |Δp| 0.11, max 0.74.
- The NPU Q8 build and the CPU 16-bit build gave the same 8/24 and agreed with each other 24/24.

So it was not quantisation. Something computed differently on one side.

## The likely cause (found by reading the code; not yet tested)

bev-decider's `backbone_config.json` stores the RoPE base in the newer transformers format:

```json
"rope_parameters": { "rope_theta": 1000000, "rope_type": "default" }
```

- **The board build reads it correctly.** The pinned llama.cpp converter (commit `99b95488`) reads
  `rope_parameters` and writes `rope_theta = 1000000` into the GGUF.
- **The reference reads it wrongly.** The reference ran under **transformers 4.57.6**. In that version
  `Qwen3Config` has no idea what `rope_parameters` is: it ignores the key and uses its default
  `rope_theta = 10000.0`. The model's config was saved with transformers 5.x. bev-decider says it supports
  transformers ≥ 4.56, so nothing warned anyone.

That would make the reference run the model with a position setting 100× smaller than the one it was trained with.
This fits everything we saw: every request off by a similar amount; NPU and CPU builds agreeing with each other
(both have the right setting); 16-bit no better than Q8.

I also compared the rest of `bev-decide` (`device/bev_decide/bev_core.hpp`) with bev-decider 0.2.1's `encode.py` and
`model.py` line by line: the prompt layout, the option and answer positions, the attention mask, the read positions
and the decision head. They match. RoPE is the only difference I found.

## Steps

Use the same Python and package folder you used to build `reports/data/bev_reference.json` (your report: bev-decider
0.2.1 installed with `--target` into a scratch folder, torch 2.11.0+cpu, transformers 4.57.6). Below, `PY` means that
Python with that folder on its path. `SRC` is the original `bev-decider-0.4B` folder (after `git lfs pull`), and
`BUILD` is `~/fieldmind-build`.

```bash
cd ~/field-mind        # or wherever the repo is
git switch bev-ideas-results && git pull
export SRC=<path to bev-decider-0.4B> BUILD=$HOME/fieldmind-build
PY="<the reference python, with PYTHONPATH set to your scratch --target folder>"
```

### 1. Confirm the two settings (5 min)

```bash
# board side: expect qwen3.rope.freq_base = 1000000 in BOTH files
$BUILD/venv-convert/bin/python $BUILD/llama.cpp/gguf-py/gguf/scripts/gguf_dump.py \
    $BUILD/gguf/bev/bev-decider-0.4B-backbone-Q8_0.gguf | grep -i rope
$BUILD/venv-convert/bin/python $BUILD/llama.cpp/gguf-py/gguf/scripts/gguf_dump.py \
    $BUILD/gguf/bev/backbone-16bit.gguf | grep -i rope

# reference side: expect transformers 4.57.6 and rope_theta 10000.0 (that is the bug)
$PY -c "import transformers; from transformers import Qwen3Config; \
c = Qwen3Config.from_pretrained('$SRC/backbone_config.json'); print(transformers.__version__, c.rope_theta)"
```

If the GGUF does **not** say 1000000, or the reference already says 1000000.0, **stop**. The cause is something
else: send both outputs and skip the rest.

### 2. Build a fixed copy of the model folder (never edit `SRC`)

```bash
export FIX=$BUILD/bev-ref-rope1e6
mkdir -p "$FIX"
for f in "$SRC"/*; do ln -sf "$f" "$FIX/"; done      # links to the same weights and tokenizer
rm "$FIX/backbone_config.json"
$PY - <<'EOF'
import json, os
src, fix = os.environ["SRC"], os.environ["FIX"]
c = json.load(open(f"{src}/backbone_config.json"))
c["rope_theta"] = c["rope_parameters"]["rope_theta"]   # the value the model was saved with
json.dump(c, open(f"{fix}/backbone_config.json", "w"), indent=2)
EOF
# check: expect 1000000.0 (or 1000000)
$PY -c "from transformers import Qwen3Config; print(Qwen3Config.from_pretrained('$FIX/backbone_config.json').rope_theta)"
```

### 3. Rebuild the reference under a new name (keep the old file)

```bash
$PY -m bench.bev_conformance reference "$FIX" \
    --requests reports/data/bev_requests.json --out reports/data/bev_reference_rope1e6.json
```

### 4. Compare the board against the new reference

```bash
# NPU, Q8 (the build the benchmarks used)
.venv/bin/python -m bench.board start bev bev-decider-0.4B-backbone-Q8_0.gguf
curl -s http://localhost:8082/health
.venv/bin/python -m bench.bev_conformance compare http://localhost:8082 \
    --reference reports/data/bev_reference_rope1e6.json --label npu-q8-rope1e6 \
    --out reports/data/bev_conformance_npu-q8-rope1e6.json

# CPU, 16-bit (separates rounding from everything else)
.venv/bin/python -m bench.board stop bev
.venv/bin/python -m bench.board start bev backbone-16bit.gguf cpu
.venv/bin/python -m bench.bev_conformance compare http://localhost:8082 \
    --reference reports/data/bev_reference_rope1e6.json --label cpu-16bit-rope1e6 \
    --out reports/data/bev_conformance_cpu-16bit-rope1e6.json

# leave bev back on the NPU
.venv/bin/python -m bench.board stop bev
.venv/bin/python -m bench.board start bev bev-decider-0.4B-backbone-Q8_0.gguf
```

## How to read the result (decided now, before any run)

| Result | Meaning |
|---|---|
| Tokens 24/24, top answer matches on (nearly) all 24, median \|Δp\| far below 0.11, any disagreement only where the reference's top-two margin is tiny | **Fixed.** The board was right all along and the old reference was wrong. |
| CPU 16-bit matches almost exactly but NPU Q8 has a few near-tie flips | Fixed. The flips are Q8 rounding; report them as they are. |
| Still about 8/24 on both builds | **The RoPE idea was wrong**, or not the only cause. Stop and send the files. The next step is comparing hidden values per option, which needs a debug output added to `bev-decide`. |
| Something in between | Send it as it is. Don't adjust anything. |

Exit code 4 from `compare` just means "some top answers differ"; it lists each one with the reference's margin.
That's a result to report, not a failure.

## Optional cross-check (if you have 15 more minutes)

Build the reference a second time on the **original** folder `SRC`, in a separate scratch folder with
**transformers 5.x** (which understands `rope_parameters` without the patch). Output to
`reports/data/bev_reference_tf5.json`. It should match `bev_reference_rope1e6.json` to about 1e-5. If it does, the
patch in step 2 is exactly equivalent to the original config read correctly.

## Rules

- Never edit the original `bev-decider-0.4B` folder, the GGUF files, `bev-decide`, or any benchmark settings.
- Keep the old `bev_reference.json` and the old `bev_conformance_*.json` files. They are the evidence of the bug.
- Dev requests only (`reports/data/bev_requests.json`), which is what the file already contains.
- No benchmark reruns are needed for this. If the fix holds, the existing board results stand as they are.

## What to send back

1. The full output of step 1 (both `gguf_dump` greps and the reference `rope_theta` line).
2. `reports/data/bev_reference_rope1e6.json`, `bev_conformance_npu-q8-rope1e6.json`,
   `bev_conformance_cpu-16bit-rope1e6.json`, and `bev_reference_tf5.json` if you did the cross-check.
3. The printed summary of each `compare` (tokens identical, rank-1 agree, max and median |Δp|, the disagreement list).
4. Commit them on `bev-ideas-results` with a short note in `reports/bev_measurement.md` under T3, and push.

## What it changes if it's fixed

- bev's accuracy numbers from the board runs become bev-decider's own numbers (within Q8 rounding). That covers
  77% citation agreement, 38% on root cause, and yes to 836 of 837 actions. The "our build only" warnings come off
  the reports and pages.
- Speed and memory numbers never depended on this.
- I'll add a guard to `bench/bev_conformance.py`: the reference step stops if transformers' RoPE base differs from
  the one in `rope_parameters`. I'll also report the transformers ≥ 4.56 problem to the bev-decider project, since
  anyone on 4.56–4.57 silently gets wrong answers from this model.
