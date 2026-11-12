#!/bin/zsh
# The 4-bit against 8-bit confirmation on the 24 GB Mac (reports/echo_4bit_prereg.md, HANDOFF_4BIT.md).
# One llama-server at a time, the echo replay's flags.
#
#   bench/echo_4bit_runs.sh <label> <gguf> [<label> <gguf> ...]
#
# Per arm, every step resumable (a call already in its output file is not sent again):
#   h_prior   held-out set H, real prompt + content-free   -> $OUT/h_prior_<label>.jsonl
#   prior     set R, the same two calls                     -> $OUT/prior_<label>.jsonl   (already done for m1-m7, m2, m2b)
#   mmluprob  300 MMLU questions, letter probabilities      -> $OUT/mmluprob_<label>.jsonl
#   squad     300 SQuAD questions: alone, passage, swapped  -> $OUT/squad_<label>.jsonl
# Every start/end goes to $OUT/RUNLOG_4bit.txt (laptop time).
# Pilot: LIMIT=3 OUT=/some/tmp/dir bench/echo_4bit_runs.sh <label> <gguf>   (first 3 requests only, not scored)
#
# To build an 8-bit file from the 16-bit GGUF that bench/build_candidate_gguf.sh left behind:
#   bench/echo_4bit_runs.sh --q8 <name>      ->  $BUILD/gguf/<name>-Q8_0-pure.gguf   (every matrix Q8_0)
set -u
cd "${0:A:h}/.."
B=${BUILD:-~/fieldmind-build}
PY=(env -u PYTHONPATH .venv/bin/python)
URL=http://127.0.0.1:8090
OUT=${OUT:-results/echo}
LIM=(${LIMIT:+--limit} ${LIMIT:-})
mkdir -p $OUT
log() { echo "$(date '+%F %T') $*" | tee -a $OUT/RUNLOG_4bit.txt; }

if [ "${1:-}" = "--q8" ]; then
  name=$2; mid=$B/gguf/$name-16bit.gguf; out=$B/gguf/$name-Q8_0-pure.gguf
  [ -f $mid ] || { echo "missing $mid: build it first with bench/build_candidate_gguf.sh $name <hf_source_dir>"; exit 1; }
  mkdir -p logs
  log "q8 $name: llama.cpp $(git -C $B/llama.cpp rev-parse HEAD)"
  $B/llama.cpp/build-host/bin/llama-quantize --pure "${@:3}" $mid $out Q8_0 > logs/quantize_q8_$name.log 2>&1 \
      || { log "q8 $name FAILED (logs/quantize_q8_$name.log)"; exit 1; }
  "${PY[@]}" -m bench.gguf_types $out > logs/gguf_types_q8_$name.log
  grep -E '"(type_counts|F32|F16|BF16|Q4_0|Q8_0|verdict)"' logs/gguf_types_q8_$name.log
  log "q8 $name: 16-bit sha256 $(shasum -a 256 $mid | cut -c1-64)"
  log "q8 $name: file $out sha256 $(shasum -a 256 $out | cut -c1-64)"
  exit 0
fi

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
  "${cmd[@]}" > $OUT/server4bit_$label.log 2>&1 < /dev/null &
  spid=$!
  for i in $(seq 1 180); do curl -s -m 2 $URL/health | grep -q ok && break; sleep 2; done
  curl -s -m 2 $URL/health | grep -q ok || { log "server for $label not healthy"; kill $spid; exit 1; }
  step h_prior "${PY[@]}" bench/echo_4bit.py run prior reports/data/echo_4bit_requests.json --url $URL \
      --model $file --label $label --out $OUT/h_prior_$label.jsonl "${LIM[@]}"
  step prior "${PY[@]}" bench/echo_4bit.py run prior reports/data/echo_requests.json --url $URL \
      --model $file --label $label --out $OUT/prior_$label.jsonl "${LIM[@]}"
  step mmluprob "${PY[@]}" bench/echo_4bit.py run mmluprob reports/data/nd_public_requests.json --url $URL \
      --model $file --label $label --out $OUT/mmluprob_$label.jsonl "${LIM[@]}"
  step squad "${PY[@]}" bench/echo_4bit.py run squad reports/data/echo_4bit_squad.json --url $URL \
      --model $file --label $label --out $OUT/squad_$label.jsonl "${LIM[@]}"
  kill $spid; wait $spid 2>/dev/null
  log "$label server stopped"
done
log "arms done"
