# QIDK handoff: Laya on the board's NPU (Track B3, reports/laya_l1.md)

For whoever runs the board (and that laptop's Claude). Branch **`laya`** (Shubham pushes it; nothing is
pushed from his laptop without his say). Nothing here changes the agent or the Llama/Gemma lanes.

## What this is
Laya (convaiinnovations, ModernBERT-large encoder + 2-layer decision head, 421M, Apache 2.0) is a System
One decision model like bev-decider. The pinned llama.cpp (`b11371`, already on the board) **serves it
natively**: `llama-server` answers `POST /v1/systemone`, the same protocol bev-decide speaks, so no new
binary is needed. This check answers: does it load fully on HTP0, does it give the same answers there as on
the laptop, and how long does a decision take.

Laptop results so far (Shubham's Mac, Homebrew llama.cpp 11429, CPU), 278 Cranfield dev decider requests
against PyTorch Laya:

| file | top answer identical | max \|Δp\| | median \|Δp\| |
|---|---|---|---|
| F16 (844 MB) | 278 / 278 | 0.0016 | 0.0002 |
| Q8_0 (449 MB) | 269 / 278 | 0.030 | 0.002 |

All 9 Q8_0 flips are near-ties (PyTorch's top-two margin ≤ 0.019). The pre-registered rule (identical on
every request) is failed by Q8_0; which file goes on the NPU is Shubham's decision. **Run Q8_0 only on the
NPU** (project rule: Q4_0 / Q8_0 only on HTP). Do not put F16 on the NPU unless he says so.

## 1. Get the model files (not in git)
Either Shubham copies them over (preferred), or regenerate:
```bash
python3 -m venv .venv-laya && .venv-laya/bin/pip install -r bench/requirements-laya.txt
git clone --depth 1 --branch b11371 https://github.com/ggml-org/llama.cpp /tmp/llama.cpp-b11371
.venv-laya/bin/python -c "from huggingface_hub import snapshot_download as s; \
  print(s('convaiinnovations/laya', revision='7b928d828b7b0e022f929d9bd2e44165aa270148', allow_patterns=['*.json','*.safetensors','tokenizer/*','encoder/*']))"
# SNAP = the folder printed above
mkdir -p device/models/laya
PYTHONPATH=/tmp/llama.cpp-b11371/gguf-py .venv-laya/bin/python /tmp/llama.cpp-b11371/convert_hf_to_gguf.py \
  $SNAP --outtype q8_0 --outfile device/models/laya/laya-7b928d8-Q8_0.gguf
sha256sum device/models/laya/laya-7b928d8-Q8_0.gguf
```
The sha256 must be `a972d557cc47ef3caf7ddfb81a51e92974cf9a977c5f15ceef967f667740b7b6` (`bench.board.LAYA_FILES`).
If it differs, stop and report both values: do not edit `LAYA_FILES` to make it pass.

## 2. Push and check
```bash
adb push device/models/laya/laya-7b928d8-Q8_0.gguf /data/local/tmp/llm/
adb shell sha256sum /data/local/tmp/llm/laya-7b928d8-Q8_0.gguf        # must equal the laptop value
```

## 3. Run (laptop time is logged by the scripts; the board clock is wrong)
```bash
mkdir -p results/laya_board
.venv/bin/python -m bench.board temp | tee results/laya_board/temp_before.json
.venv/bin/python -m bench.board start laya laya-7b928d8-Q8_0.gguf | tee results/laya_board/start_npu.json
.venv/bin/python -m bench.board log laya > results/laya_board/lane_laya_npu.log
```
**NPU use is confirmed only if** the log shows every layer offloaded (`offloaded N/N layers`, the 28
encoder blocks + 2 head blocks + output), a nonzero HTP0 buffer, and no weight buffer left on the CPU.
One small F32 table (`token_types.weight`, 1024 × 3, the question-type embedding) is not Q8_0; note where it
lands. If anything is not offloaded, record it and stop at step 4.

```bash
# 4. parity on the board, against the PyTorch answers committed in the branch
.venv/bin/python -m bench.laya_parity http://localhost:8083 cranfield_dev \
    --label board_npu_Q8_0 --base reports/data/laya_parity | tee results/laya_board/parity_npu.txt
cp results/laya_l1/parity_board_npu_Q8_0.json results/laya_board/
.venv/bin/python -m bench.board stop laya
# cool down, then the same file on the board CPU (placement comparison, as bev's T2)
.venv/bin/python -m bench.board start laya laya-7b928d8-Q8_0.gguf cpu | tee results/laya_board/start_cpu.json
.venv/bin/python -m bench.laya_parity http://localhost:8083 cranfield_dev \
    --label board_cpu_Q8_0 --base reports/data/laya_parity | tee results/laya_board/parity_cpu.txt
cp results/laya_l1/parity_board_cpu_Q8_0.json results/laya_board/
.venv/bin/python -m bench.board stop laya
.venv/bin/python -m bench.board temp | tee results/laya_board/temp_after.json
```
`ms per request` printed by the parity script is laptop wall clock over USB (request + answer), the same way
bev's decision time was measured.

Caution: `bench.board stop` (no argument) kills **every** llama-server on the board, Laya's included;
`stop laya` stops only the Laya lane (matched by port 8083).

## 5. Send back
`results/laya_board/` (start JSONs, lane log, both parity files, temperatures). Commit on a branch of your
own, as for the breadth runs.

## Later (Track C, only after Shubham's go, not now)
The agent with real Llama on the NPU and Laya in the bev slots: `configs/laya.yaml` with the lane `url`
set to `http://localhost:8083`, after `configs/bev3.yaml` (decider) or `configs/bev_ideas.yaml` (bev ideas).
The benchmark runner's `--arch bev` checks bev-decide specifically and needs a Laya variant first.
