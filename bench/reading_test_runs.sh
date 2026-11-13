#!/bin/zsh
# The reading test on the 24 GB Mac (reports/reading_test_prereg.md). One llama-server at a time, the echo replay's
# flags. Per arm: the three list forms, then per_case. Resumable: a call already in its file is not sent again.
#   bench/reading_test_runs.sh <label> <gguf> [<label> <gguf> ...]
#   REQ=reports/data/reading_requests_tep.json SUFFIX=_tep bench/reading_test_runs.sh <label> <gguf> ...
# REQ defaults to set H. For any other request file the `original` form is sent too (set H's original rows come from
# the 4-bit test's h_prior files; a new set has none): `echo_4bit.py run prior --forms original`, into
# h_prior_<label><SUFFIX>.jsonl. SUFFIX (for example _tep, _cranfield) keeps every output file apart from set H's.
set -u
cd "${0:A:h}/.."
B=${BUILD:-~/fieldmind-build}
PY=(env -u PYTHONPATH .venv/bin/python)
URL=http://127.0.0.1:8090
OUT=${OUT:-results/echo}
SET_H=reports/data/echo_4bit_requests.json
REQ=${REQ:-$SET_H}
SUFFIX=${SUFFIX:-}
[ "$REQ" = "$SET_H" ] || [ -n "$SUFFIX" ] || { echo "REQ is not set H: give SUFFIX (e.g. _tep) so set H's files are not mixed in"; exit 2; }
LIM=(${LIMIT:+--limit} ${LIMIT:-})
mkdir -p $OUT
log() { echo "$(date '+%F %T') $*" | tee -a $OUT/RUNLOG_reading.txt; }
while (( $# >= 2 )); do
  label=$1; gguf=$2; shift 2
  [ -f $gguf ] || { log "$label FAILED: missing $gguf"; continue; }
  log "arm $label file $gguf sha256 $(shasum -a 256 $gguf | cut -c1-64) requests $REQ"
  $B/llama.cpp/build-host/bin/llama-server -m $gguf --port 8090 -c 4096 -np 1 -ngl 99 --cache-ram 0 \
      > $OUT/server_reading_$label$SUFFIX.log 2>&1 &
  sp=$!
  for i in {1..120}; do curl -s -m 2 $URL/health | grep -q ok && break; sleep 1; done
  if [ "$REQ" != "$SET_H" ]; then
    log "$label original$SUFFIX start"
    "${PY[@]}" bench/echo_4bit.py run prior $REQ --url $URL --model ${gguf:t} --label $label --forms original \
        --out $OUT/h_prior_$label$SUFFIX.jsonl $LIM >> $OUT/RUNLOG_reading.txt 2>&1 || log "$label original$SUFFIX FAILED"
    log "$label original$SUFFIX end"
  fi
  for t in list per_case; do
    log "$label $t$SUFFIX start"
    "${PY[@]}" bench/reading_test.py run $t $REQ --url $URL --model ${gguf:t} --label $label \
        --out $OUT/reading_${t}_$label$SUFFIX.jsonl $LIM >> $OUT/RUNLOG_reading.txt 2>&1 || log "$label $t$SUFFIX FAILED"
    log "$label $t$SUFFIX end"
  done
  kill $sp; wait $sp 2>/dev/null
  log "$label server stopped"
done
