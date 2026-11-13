#!/bin/zsh
# FaultExplainer rerun (Amendment A2 of reports/ext_faultexplainer_prereg.md), SM8750 1d9c8f40, driven from
# Shubham's laptop on 2026-11-13. The lane is started separately (the nd-paper bench/board.py, which can set
# GGML_HEXAGON_NHVX); this script only cools, runs and reports health. It reads no reply and no pick.
#
#   results/run_fe_rerun_sm8750.sh check <label> <model file> <out.jsonl> [url]   8 calls: requests 0-1, app, 4 orderings
#   results/run_fe_rerun_sm8750.sh arm   <label> <model file> <out.jsonl> [url]   108 calls in 3 blocks: eval, eval_noleak, app
set -u
cd "${0:A:h}/.."
export ANDROID_SERIAL=1d9c8f40
PYBIN=${PYBIN:-$([ -x .venv/bin/python ] && echo $PWD/.venv/bin/python || echo /Users/shubhamgupta/Desktop/field-mind/.venv/bin/python)}
PY=(env -u PYTHONPATH $PYBIN)
LOG=results/ext/fe_rerun_log.txt
REQ=reports/data/ext_faultexplainer_requests.json
say() { echo "$(date '+%F %T') $*" | tee -a $LOG; }
temp() { "${PY[@]}" -m bench.board temp < /dev/null 2>/dev/null | $PYBIN -c 'import json,sys; d=json.load(sys.stdin); print(d["cpu_max_c"], d.get("npu_max_c"))'; }
# A2 section 5: cool to idle + 5 C, at most 900 s. CITED: results/run_s3_sm8750.sh (idle 33.8 C, so 38.8 C).
cool() {
  local t0=$(date +%s) c
  while true; do
    c=$(temp | cut -d' ' -f1)
    [[ -n $c && $c != None ]] && awk "BEGIN{exit !($c <= 38.8)}" && break
    [ $(( $(date +%s) - t0 )) -ge 900 ] && break
    sleep 20
  done
  say "cooled to $c C after $(( $(date +%s) - t0 )) s"
}
what=$1; label=$2; model=$3; out=$4; url=${5:-http://127.0.0.1:8080}
case $what in
  check)
    cool; say "check $label start (temp $(temp)) model $model url $url"
    "${PY[@]}" bench/ext_faultexplainer.py run $REQ --url $url --model $model --label $label --forms app --limit 2 --out $out < /dev/null >> $LOG 2>&1; rc=$?
    say "check $label end rc=$rc (temp $(temp))"
    "${PY[@]}" bench/ext_faultexplainer.py health $out | tee -a $LOG ;;
  arm)
    for form in eval eval_noleak app; do
      cool; say "arm $label form $form start (temp $(temp)) model $model url $url"
      "${PY[@]}" bench/ext_faultexplainer.py run $REQ --url $url --model $model --label $label --forms $form --out $out < /dev/null >> $LOG 2>&1; rc=$?
      say "arm $label form $form end rc=$rc (temp $(temp))"
      [ $rc -ne 0 ] && { say "arm $label STOPPED (rc $rc)"; exit 1; }
    done
    "${PY[@]}" bench/ext_faultexplainer.py health $out | tee -a $LOG ;;
  *) echo "usage: $0 check|arm <label> <model file> <out.jsonl> [url]"; exit 2 ;;
esac
