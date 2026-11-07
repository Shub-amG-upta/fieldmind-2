#!/usr/bin/env bash
# Build device/models/laya/laya-7b928d8-Q8_0.gguf exactly as recorded in bench.board.LAYA_FILES
# and check its sha256 (reports/laya_l1.md, HANDOFF_LAYA.md). Needs internet once (Hugging Face,
# GitHub, PyPI). Never edits LAYA_FILES: a different sha256 stops the script.
#   scripts/laya_build_gguf.sh            (PYTHON=python3.12 scripts/laya_build_gguf.sh to choose)
set -euo pipefail
cd "$(dirname "$0")/.."
REV=7b928d828b7b0e022f929d9bd2e44165aa270148            # convaiinnovations/laya revision
TAG=b11371; COMMIT=99b95488cac0f00ce3f05af113a8c1e287753f87  # the board's llama.cpp
OUT=device/models/laya; FILE=laya-7b928d8-Q8_0.gguf
mkdir -p "$OUT"
PY=${PYTHON:-python3}
[ -x .venv-laya-convert/bin/python ] || "$PY" -m venv .venv-laya-convert
V=.venv-laya-convert/bin/python
env -u PYTHONPATH "$V" -m pip install -q --upgrade pip
env -u PYTHONPATH "$V" -m pip install -q --extra-index-url https://download.pytorch.org/whl/cpu \
    -r bench/requirements-laya-convert.txt
[ -d "$OUT/llama.cpp-$TAG" ] || git clone -q --depth 1 --branch "$TAG" https://github.com/ggml-org/llama.cpp "$OUT/llama.cpp-$TAG"
[ "$(git -C "$OUT/llama.cpp-$TAG" rev-parse HEAD)" = "$COMMIT" ] || { echo "llama.cpp is not commit $COMMIT"; exit 1; }
SNAP=$(env -u PYTHONPATH "$V" -c "from huggingface_hub import snapshot_download as s; print(s('convaiinnovations/laya', revision='$REV', allow_patterns=['model.safetensors', 'rl_agent_config.json', 'encoder/*', 'tokenizer/*']))" | tail -1)
env PYTHONPATH="$OUT/llama.cpp-$TAG/gguf-py" "$V" "$OUT/llama.cpp-$TAG/convert_hf_to_gguf.py" "$SNAP" \
    --outtype q8_0 --outfile "$OUT/$FILE" > "$OUT/convert_q8_0.log" 2>&1
if command -v sha256sum >/dev/null; then GOT=$(sha256sum "$OUT/$FILE" | cut -d' ' -f1); else GOT=$(shasum -a 256 "$OUT/$FILE" | cut -d' ' -f1); fi
WANT=$(env -u PYTHONPATH .venv/bin/python -c "from bench.board import LAYA_FILES; print(LAYA_FILES['$FILE'])")
if [ "$GOT" = "$WANT" ]; then
    echo "OK  $OUT/$FILE  sha256 $GOT (matches bench.board.LAYA_FILES)"
else
    echo "STOP  $OUT/$FILE  sha256 $GOT  !=  recorded $WANT"
    echo "Do not edit LAYA_FILES. Report both values to Shubham (or use the file he copies over)."
    exit 1
fi
