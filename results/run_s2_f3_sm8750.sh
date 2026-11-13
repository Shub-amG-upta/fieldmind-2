#!/bin/zsh
# Shubham's handoff (HANDOFF_MAC_RUNS.md) on the SM8750 1d9c8f40, agreed 2026-11-13 00:35 (see the notes there):
#   S2 = item 6 (sched_fix.md part D), the 6 commands printed by bench/paperB_board.py plan --item 6, in order
#   F3 = item 1 (reports/ext_faultexplainer_prereg.md), FaultExplainer F1 on the NPU lane
# Laya is started before S2 (HANDOFF_SCHED.md: v3x cells need it). Lanes are brought up before F3.
set -u
cd "${0:A:h}/.."
export ANDROID_SERIAL=1d9c8f40
LOG=results/run_s2_f3_sm8750.log
say() { echo "$(date '+%F %T') $*" | tee -a $LOG; }
PY=(env -u PYTHONPATH .venv/bin/python)
temp() { "${PY[@]}" -m bench.board temp 2>/dev/null | .venv/bin/python -c 'import json,sys; d=json.load(sys.stdin); print(d["cpu_max_c"], d.get("npu_max_c"))'; }
laya_up() { curl -s -m 5 localhost:8083/health | grep -q '"ok"'; }
say "S2+F3 driver start; board uptime $(adb shell cat /proc/uptime < /dev/null | cut -d' ' -f1) s; temp $(temp)"
"${PY[@]}" -m bench.board stop > /dev/null
"${PY[@]}" -m bench.board start laya laya-7b928d8-Q8_0.gguf > results/laya_start_s2.txt 2>&1; laya_up && say "laya up" || { say "laya failed to start; stopping"; exit 1; }
i=0
while read -r line; do
  i=$((i+1)); [ -z "$line" ] && continue
  laya_up || { say "laya down before S2 cell $i; restarting"; "${PY[@]}" -m bench.board start laya laya-7b928d8-Q8_0.gguf >> results/laya_start_s2.txt 2>&1; }
  say "S2 cell $i start: ${line[1,140]} (temp $(temp))"
  env -u PYTHONPATH ${=line} > results/s2_cell$i.out 2>&1 < /dev/null; rc=$?
  say "S2 cell $i end rc=$rc (temp $(temp))"
done < results/sched_s2_cmds.txt
say "S2 done"
"${PY[@]}" -m bench.board stop > /dev/null; "${PY[@]}" -m bench.board stop laya > /dev/null 2>&1
sleep 600
M=Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf
"${PY[@]}" -m bench.board start npu $M > results/f3_lanes.txt 2>&1; "${PY[@]}" -m bench.board start cpu $M >> results/f3_lanes.txt 2>&1
say "F3 start (temp $(temp))"
PYTHONPATH= .venv/bin/python bench/ext_faultexplainer.py run reports/data/ext_faultexplainer_requests.json --url http://127.0.0.1:8080 --model $M --label F1_board_npu --out results/ext/faultexplainer_F1.jsonl > results/f3_run.out 2>&1 < /dev/null; rc=$?
say "F3 end rc=$rc (temp $(temp))"
"${PY[@]}" -m bench.board stop > /dev/null
say "S2+F3 driver done"
