#!/bin/zsh
# ECHO on the 24 GB Mac (HANDOFF_MAC_RUNS.md). One llama-server at a time, the echo replay's flags.
#
#   bench/echo_mac_runs.sh <label> <gguf> [<label> <gguf> ...]
#
# Per arm, every step resumable (a call already in its output file is not sent again):
#   R        set R, 4 orderings        bench/echo_test.py run      -> results/echo/R_<label>.jsonl      (size curve, E5)
#   L        letters off, then on      bench/echo_test.py run      -> results/echo/L_<label>.jsonl
#   relabel  label vs position          bench/echo_causes.py relabel -> results/echo/relabel_<label>.jsonl (E6)
#   prior    content-free prior         bench/echo_causes.py prior   -> results/echo/prior_<label>.jsonl   (E7)
#   mmlu     shuffled MMLU control      bench/echo_causes.py mmlu    -> results/echo/mmlu_<label>.jsonl    (E8)
# For the arms already run (m1-m4) R and L are skipped automatically: every call is already in the file.
# Every start/end goes to $OUT/RUNLOG.txt (laptop time).
# Pilot / smoke test: LIMIT=3 OUT=/some/tmp/dir bench/echo_mac_runs.sh <label> <gguf> (first 3 requests only).
set -u
cd "${0:A:h}/.."
B=${BUILD:-~/fieldmind-build}
PY=(env -u PYTHONPATH .venv/bin/python)
URL=http://127.0.0.1:8090
OUT=${OUT:-results/echo}
LIM=(${LIMIT:+--limit} ${LIMIT:-})
mkdir -p $OUT
log() { echo "$(date '+%F %T') $*" | tee -a $OUT/RUNLOG.txt; }
step() {  # step <name> <command...>
  local name=$1; shift
  log "$label $name start"
  "$@" || { log "$label $name FAILED"; kill $spid; exit 1; }
  log "$label $name end"
}
while [ $# -ge 2 ]; do
  label=$1; file=$2; shift 2
  [ -f $file ] || { log "missing $file"; exit 1; }
  log "arm $label file $file sha256 $(shasum -a 256 $file | cut -c1-64)"
  cmd=($B/llama.cpp/build-host/bin/llama-server -m $file --port 8090 -c 4096 -np 1 --cache-ram 0 -ngl 99)
  log "server: ${cmd[*]}"
  "${cmd[@]}" > $OUT/server_$label.log 2>&1 < /dev/null &
  spid=$!
  for i in $(seq 1 120); do curl -s -m 2 $URL/health | grep -q ok && break; sleep 2; done
  curl -s -m 2 $URL/health | grep -q ok || { log "server for $label not healthy"; kill $spid; exit 1; }
  step R "${PY[@]}" bench/echo_test.py run reports/data/echo_requests.json --url $URL --model $file \
      --label $label --out $OUT/R_$label.jsonl "${LIM[@]}"
  step L_off "${PY[@]}" bench/echo_test.py run reports/data/echo_letter_pairs.json --url $URL --model $file \
      --label ${label}_letters_off --field prompt --only original --out $OUT/L_$label.jsonl "${LIM[@]}"
  step L_on "${PY[@]}" bench/echo_test.py run reports/data/echo_letter_pairs.json --url $URL --model $file \
      --label ${label}_letters_on --field prompt_letters --only original --out $OUT/L_$label.jsonl "${LIM[@]}"
  step relabel "${PY[@]}" bench/echo_causes.py run relabel reports/data/echo_requests.json --url $URL \
      --model $file --label $label --out $OUT/relabel_$label.jsonl "${LIM[@]}"
  step prior "${PY[@]}" bench/echo_causes.py run prior reports/data/echo_requests.json --url $URL \
      --model $file --label $label --out $OUT/prior_$label.jsonl "${LIM[@]}"
  step mmlu "${PY[@]}" bench/echo_causes.py run mmlu reports/data/nd_public_requests.json --url $URL \
      --model $file --label $label --out $OUT/mmlu_$label.jsonl "${LIM[@]}"
  kill $spid; wait $spid 2>/dev/null
  log "$label server stopped"
done
log "arms done"
