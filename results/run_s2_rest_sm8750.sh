#!/bin/zsh
# S2 cells 2-6 (skipped by a driver bug in run_s2_f3_sm8750.sh), then amendment M9-4 (our M9-2/M9-3). Waits for the F3 driver.
set -u
cd "${0:A:h}/.."
export ANDROID_SERIAL=1d9c8f40
LOG=results/run_s2_f3_sm8750.log
say() { echo "$(date '+%F %T') $*" | tee -a $LOG; }
PY=(env -u PYTHONPATH .venv/bin/python)
temp() { "${PY[@]}" -m bench.board temp < /dev/null 2>/dev/null | .venv/bin/python -c 'import json,sys; d=json.load(sys.stdin); print(d["cpu_max_c"], d.get("npu_max_c"))'; }
laya_up() { curl -s -m 5 localhost:8083/health < /dev/null | grep -q '"ok"'; }
while pgrep -f "run_s2_f3_sm8750.sh" >/dev/null; do sleep 60; done
say "S2 cells 2-6 start (after F3)"
"${PY[@]}" -m bench.board start laya laya-7b928d8-Q8_0.gguf < /dev/null >> results/laya_start_s2.txt 2>&1; laya_up && say "laya up" || { say "laya failed; stopping"; exit 1; }
i=0
while read -r -u 3 line; do
  i=$((i+1)); [ $i -eq 1 ] && continue; [ -z "$line" ] && continue
  laya_up || { say "laya down before S2 cell $i; restarting"; "${PY[@]}" -m bench.board start laya laya-7b928d8-Q8_0.gguf < /dev/null >> results/laya_start_s2.txt 2>&1; }
  say "S2 cell $i start: ${line[1,140]} (temp $(temp))"
  env -u PYTHONPATH ${=line} > results/s2_cell$i.out 2>&1 < /dev/null; rc=$?
  say "S2 cell $i end rc=$rc (temp $(temp))"
done 3< results/sched_s2_cmds.txt
"${PY[@]}" -m bench.board stop < /dev/null > /dev/null; "${PY[@]}" -m bench.board stop laya < /dev/null > /dev/null 2>&1
say "S2 done (cells 1-6)"
cd ~/projects/fieldmind && zsh results/nd/run_m9_after_s2f3.sh
