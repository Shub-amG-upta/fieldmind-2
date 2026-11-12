#!/bin/zsh
# F3 retry (first attempt failed at 00:51: results/ext/ missing). Waits for S2 cells 2-6 to finish, cools 10 min, lanes up, F3.
set -u
cd "${0:A:h}/.."
export ANDROID_SERIAL=1d9c8f40
LOG=results/run_s2_f3_sm8750.log
say() { echo "$(date '+%F %T') $*" | tee -a $LOG; }
PY=(env -u PYTHONPATH .venv/bin/python)
temp() { "${PY[@]}" -m bench.board temp < /dev/null 2>/dev/null | .venv/bin/python -c 'import json,sys; d=json.load(sys.stdin); print(d["cpu_max_c"], d.get("npu_max_c"))'; }
until grep -q "S2 done (cells 1-6)" $LOG; do sleep 30; done
sleep 600
M=Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf
"${PY[@]}" -m bench.board start npu $M < /dev/null > results/f3_lanes.txt 2>&1; "${PY[@]}" -m bench.board start cpu $M < /dev/null >> results/f3_lanes.txt 2>&1
say "F3 (retry) start (temp $(temp))"
PYTHONPATH= .venv/bin/python bench/ext_faultexplainer.py run reports/data/ext_faultexplainer_requests.json --url http://127.0.0.1:8080 --model $M --label F1_board_npu --out results/ext/faultexplainer_F1.jsonl > results/f3_run.out 2>&1 < /dev/null; rc=$?
say "F3 (retry) end rc=$rc (temp $(temp))"
"${PY[@]}" -m bench.board stop < /dev/null > /dev/null
