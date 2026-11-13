#!/bin/zsh
# S2 cells 4-6 with the runner's cooling gap between cells (<= 38.8 C, at most 900 s), after cell 3 finishes; then hands over.
set -u
cd "${0:A:h}/.."
export ANDROID_SERIAL=1d9c8f40
LOG=results/run_s2_f3_sm8750.log
say() { echo "$(date '+%F %T') $*" | tee -a $LOG; }
PY=(env -u PYTHONPATH .venv/bin/python)
temp() { "${PY[@]}" -m bench.board temp < /dev/null 2>/dev/null | .venv/bin/python -c 'import json,sys; d=json.load(sys.stdin); print(d["cpu_max_c"])'; }
laya_up() { curl -s -m 5 localhost:8083/health < /dev/null | grep -q '"ok"'; }
cool() { local t0=$(date +%s) c; while true; do c=$(temp); if [[ $c != None ]] && awk "BEGIN{exit !($c <= 38.8)}"; then break; fi; [ $(( $(date +%s) - t0 )) -ge 900 ] && break; sleep 20; done; say "cooled to $c C after $(( $(date +%s) - t0 )) s"; }
while pgrep -f "calibrated_finish_t3_cranfield" >/dev/null; do sleep 15; done
say "S2 cell 3 end (benchmark exited)"
i=0
while read -r -u 3 line; do
  i=$((i+1)); [ $i -le 3 ] && continue; [ -z "$line" ] && continue
  cool
  laya_up || { "${PY[@]}" -m bench.board start laya laya-7b928d8-Q8_0.gguf < /dev/null >> results/laya_start_s2.txt 2>&1; laya_up && say "laya (re)started" || { say "laya failed; stopping"; exit 1; }; }
  say "S2 cell $i start: ${line[1,140]} (temp $(temp))"
  env -u PYTHONPATH ${=line} > results/s2_cell$i.out 2>&1 < /dev/null; rc=$?
  say "S2 cell $i end rc=$rc (temp $(temp))"
done 3< results/sched_s2_cmds.txt
"${PY[@]}" -m bench.board stop < /dev/null > /dev/null; "${PY[@]}" -m bench.board stop laya < /dev/null > /dev/null 2>&1
say "S2 done (cells 1-6)"
cd ~/projects/fieldmind && zsh results/nd/run_m9_after_s2f3.sh
