#!/bin/zsh
# The reading test on the 24 GB Mac (reports/reading_test_prereg.md). One llama-server at a time, the echo replay's
# flags. Per arm: the three list forms, then per_case. Resumable: a call already in its file is not sent again.
#   bench/reading_test_runs.sh <label> <gguf> [<label> <gguf> ...]
set -u
cd "${0:A:h}/.."
B=${BUILD:-~/fieldmind-build}
PY=(env -u PYTHONPATH .venv/bin/python)
URL=http://127.0.0.1:8090
OUT=${OUT:-results/echo}
REQ=reports/data/echo_4bit_requests.json
LIM=(${LIMIT:+--limit} ${LIMIT:-})
mkdir -p $OUT
log() { echo "$(date '+%F %T') $*" | tee -a $OUT/RUNLOG_reading.txt; }
while (( $# >= 2 )); do
  label=$1; gguf=$2; shift 2
  [ -f $gguf ] || { log "$label FAILED: missing $gguf"; continue; }
  log "arm $label file $gguf sha256 $(shasum -a 256 $gguf | cut -c1-64)"
  $B/llama.cpp/build-host/bin/llama-server -m $gguf --port 8090 -c 4096 -np 1 -ngl 99 --cache-ram 0 \
      > $OUT/server_reading_$label.log 2>&1 &
  sp=$!
  for i in {1..120}; do curl -s -m 2 $URL/health | grep -q ok && break; sleep 1; done
  for t in list per_case; do
    log "$label $t start"
    "${PY[@]}" bench/reading_test.py run $t $REQ --url $URL --model ${gguf:t} --label $label \
        --out $OUT/reading_${t}_$label.jsonl $LIM >> $OUT/RUNLOG_reading.txt 2>&1 || log "$label $t FAILED"
    log "$label $t end"
  done
  kill $sp; wait $sp 2>/dev/null
  log "$label server stopped"
done
