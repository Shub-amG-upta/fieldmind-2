#!/bin/zsh
# Echo replay arms on Gagan's Mac (HANDOFF_ECHO_REPLAY.md section 6), one llama-server at a time, the handoff's flags.
#   results/echo/run_arms.sh <label> <gguf> [<label> <gguf> ...]
# Per arm: server start, 6b (set R, all orderings), 6c (set L, letters off then on), server stop. Resumable: echo_test.py
# run skips calls already in its output file. Every start/end goes to results/echo/RUNLOG.txt (laptop time).
set -u
cd "${0:A:h}/../.."
B=~/fieldmind-build
PY=(env -u PYTHONPATH .venv/bin/python)
log() { echo "$(date '+%F %T') $*" | tee -a results/echo/RUNLOG.txt; }
while [ $# -ge 2 ]; do
  label=$1; file=$2; shift 2
  [ -f $file ] || { log "missing $file"; exit 1; }
  log "arm $label file $file sha256 $(shasum -a 256 $file | cut -c1-64)"
  cmd=($B/llama.cpp/build-host/bin/llama-server -m $file --port 8090 -c 4096 -np 1 --cache-ram 0 -ngl 99)
  log "server: ${cmd[*]}"
  "${cmd[@]}" > results/echo/server_$label.log 2>&1 < /dev/null &
  spid=$!
  for i in $(seq 1 120); do curl -s -m 2 127.0.0.1:8090/health | grep -q ok && break; sleep 2; done
  curl -s -m 2 127.0.0.1:8090/health | grep -q ok || { log "server for $label not healthy"; kill $spid; exit 1; }
  log "$label R start"
  "${PY[@]}" bench/echo_test.py run reports/data/echo_requests.json --url http://127.0.0.1:8090 \
      --model $file --label $label --out results/echo/R_$label.jsonl || { log "$label R failed"; kill $spid; exit 1; }
  log "$label R end; L start"
  "${PY[@]}" bench/echo_test.py run reports/data/echo_letter_pairs.json --url http://127.0.0.1:8090 \
      --model $file --label ${label}_letters_off --field prompt --only original --out results/echo/L_$label.jsonl \
      || { log "$label L off failed"; kill $spid; exit 1; }
  "${PY[@]}" bench/echo_test.py run reports/data/echo_letter_pairs.json --url http://127.0.0.1:8090 \
      --model $file --label ${label}_letters_on --field prompt_letters --only original --out results/echo/L_$label.jsonl \
      || { log "$label L on failed"; kill $spid; exit 1; }
  log "$label L end"
  kill $spid; wait $spid 2>/dev/null
  log "$label server stopped"
done
log "arms done"
