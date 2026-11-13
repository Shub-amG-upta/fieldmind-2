#!/bin/zsh
# H1 timing measurement (reports/reading_test_prereg.md A2): ranking call vs one-token check on the NPU.
# SM8650 ab8f6592, Llama 3B Q4_0 (board file), NHVX=2, 40 set H requests. A measurement, no threshold; answers not scored.
set -u
cd "${0:A:h}/../.."
export ANDROID_SERIAL=ab8f6592
PY=(env -u PYTHONPATH .venv/bin/python)
O=results/npu_timing; LOG=$O/timing_log.txt
M=Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf; REQ=reports/data/echo_4bit_requests.json
say() { echo "$(date '+%F %T') $*" | tee -a $LOG; }
temp() { "${PY[@]}" -m bench.board temp < /dev/null 2>/dev/null | .venv/bin/python -c 'import json,sys; d=json.load(sys.stdin); print(d["cpu_max_c"], d.get("npu_max_c"))'; }
cool() { local t0=$(date +%s) c; while true; do c=$(temp | cut -d' ' -f1); [[ -n $c && $c != None ]] && awk "BEGIN{exit !($c <= 36.2)}" && break; [ $(( $(date +%s) - t0 )) -ge 900 ] && break; sleep 20; done; say "cooled to $c C"; }
"${PY[@]}" -m bench.board stop < /dev/null > /dev/null
ND_LANE_ENV="GGML_HEXAGON_NHVX=2" "${PY[@]}" -m bench.board start npu $M < /dev/null > $O/lane.txt 2>&1
"${PY[@]}" -m bench.board log npu < /dev/null | grep -E "HTP0 hwinfo|offloaded [0-9]+/" | tee -a $O/lane.txt >> $LOG
grep -q "hwinfo: threads 2" $O/lane.txt || { say "lane not at 2 threads; stop"; exit 1; }
cool; say "ranking calls start (temp $(temp))"
"${PY[@]}" bench/echo_4bit.py run prior $REQ --url http://127.0.0.1:8080 --lane npu --forms original --model $M \
    --label npu8650_timing --out $O/ranking_sm8650.jsonl --limit 40 < /dev/null >> $LOG 2>&1
say "ranking calls end (temp $(temp))"
cool; say "one-token calls start (temp $(temp))"
"${PY[@]}" bench/reading_test.py run per_case $REQ --url http://127.0.0.1:8080 --lane npu --model $M \
    --label npu8650_timing --out $O/one_token_sm8650.jsonl --limit 40 < /dev/null >> $LOG 2>&1
say "one-token calls end (temp $(temp))"
"${PY[@]}" -m bench.board stop < /dev/null > /dev/null
say "done"
