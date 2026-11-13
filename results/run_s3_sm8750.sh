#!/bin/zsh
# S3 = Shubham's item 7 (agreed 2026-11-13 00:35): the capacity cells on more episodes, 3 repeats each, on the SM8750.
# Before every cell: chip cooled to <= 38.8 C (idle 33.8 + the runner's --cool-margin 5), at most 900 s; Laya up for v3x cells.
# Commands on fd 3 and adb stdin from /dev/null (tonight's two driver bugs). A cell that already has results resumes in the runner.
set -u
cd "${0:A:h}/.."
export ANDROID_SERIAL=1d9c8f40
LOG=results/run_s3_sm8750.log
say() { echo "$(date '+%F %T') $*" | tee -a $LOG; }
PY=(env -u PYTHONPATH .venv/bin/python)
temp() { "${PY[@]}" -m bench.board temp < /dev/null 2>/dev/null | .venv/bin/python -c 'import json,sys; d=json.load(sys.stdin); print(d["cpu_max_c"])'; }
laya_up() { curl -s -m 5 localhost:8083/health < /dev/null | grep -q '"ok"'; }
cool() { local t0=$(date +%s) c; while true; do c=$(temp); if [[ $c != None ]] && awk "BEGIN{exit !($c <= 38.8)}"; then break; fi; [ $(( $(date +%s) - t0 )) -ge 900 ] && break; sleep 20; done; say "cooled to $c C after $(( $(date +%s) - t0 )) s"; }
say "S3 start ($(wc -l < results/sched_s3_cmds.txt) cells); board uptime $(adb shell cat /proc/uptime < /dev/null | cut -d' ' -f1) s"
i=0
while read -r -u 3 line; do
  i=$((i+1)); [ -z "$line" ] && continue
  cool
  if [[ $line == *v3x* ]]; then laya_up || { "${PY[@]}" -m bench.board start laya laya-7b928d8-Q8_0.gguf < /dev/null >> results/laya_start_s3.txt 2>&1; laya_up && say "laya (re)started" || { say "laya failed; stopping"; exit 1; }; }; fi
  say "S3 cell $i start: ${line[1,150]} (temp $(temp))"
  env -u PYTHONPATH ${=line} > results/s3_cell$i.out 2>&1 < /dev/null; rc=$?
  say "S3 cell $i end rc=$rc (temp $(temp))"
done 3< results/sched_s3_cmds.txt
"${PY[@]}" -m bench.board stop < /dev/null > /dev/null; "${PY[@]}" -m bench.board stop laya < /dev/null > /dev/null 2>&1
say "S3 done"
