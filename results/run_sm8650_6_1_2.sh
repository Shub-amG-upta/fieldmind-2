#!/bin/zsh
# SM8650 runs for HANDOFF_SM8650.md, in the agreed order: (6) speed check at our settings, (1) 4-bit confirmation NPU
# arms (reports/echo_4bit_prereg.md A3), (2) FaultExplainer F1r and F2 (reports/ext_faultexplainer_prereg.md A3).
# Every lane at GGML_HEXAGON_NHVX=2. Reads no reply and no pick; nothing is scored here.
#   BOARD_SERIAL=<serial> nohup caffeinate -dimsu zsh results/run_sm8650_6_1_2.sh > results/sm8650_6_1_2.out 2>&1 < /dev/null &
set -u
cd "${0:A:h}/.."
export ANDROID_SERIAL=${BOARD_SERIAL:?set BOARD_SERIAL to the SM8650 serial from adb devices}
export BOARD_SERIAL
PYBIN=${PYBIN:-$([ -x .venv/bin/python ] && echo $PWD/.venv/bin/python || echo /Users/shubhamgupta/Desktop/field-mind/.venv/bin/python)}
PY=(env -u PYTHONPATH $PYBIN)
LOG=results/sm8650_runlog.txt
Q4=Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf; Q8=Llama-3.2-3B-Instruct-Q8_0-pure.gguf
Q8SHA=d91f61aba2e998c3fbfb46a4cd0710e8ed4c9b9fca2d4290f6dfc80ad0738fc2
say() { echo "$(date '+%F %T') $*" | tee -a $LOG; }
temp() { "${PY[@]}" -m bench.board temp < /dev/null 2>/dev/null | $PYBIN -c 'import json,sys; d=json.load(sys.stdin); print(d["cpu_max_c"], d.get("npu_max_c"))'; }
cool() {
  local t0=$(date +%s) c
  while true; do
    c=$(temp | cut -d' ' -f1)
    [[ -n $c && $c != None ]] && awk "BEGIN{exit !($c <= $COOL_C)}" && break
    [ $(( $(date +%s) - t0 )) -ge 900 ] && break
    sleep 20
  done
  say "cooled to $c C after $(( $(date +%s) - t0 )) s"
}
failed() { $PYBIN -c "import json,sys; r=[json.loads(l) for l in open(sys.argv[1])]; print(len(r), sum(x.get('status')!='ok' for x in r))" $1; }
lane() {  # model tag -> starts the NPU lane at NHVX=2 and checks its log
  "${PY[@]}" -m bench.board stop < /dev/null > /dev/null
  ND_LANE_ENV="GGML_HEXAGON_NHVX=2" "${PY[@]}" -m bench.board start npu $1 < /dev/null > results/sm8650_lane_$2.txt 2>&1
  "${PY[@]}" -m bench.board log npu < /dev/null | grep -E "llama_model_loader: - type|HTP0 hwinfo|offloaded|HTP0 model buffer|n_slots" >> results/sm8650_lane_$2.txt
  grep -q "hwinfo: threads 2" results/sm8650_lane_$2.txt || { say "lane $2: log does not show 2 threads; stop"; cat results/sm8650_lane_$2.txt >> $LOG; exit 1; }
  say "lane $2: $(grep -E 'hwinfo|offloaded [0-9]+/[0-9]+' results/sm8650_lane_$2.txt | tr '\n' ' ')"
}

# ---- 0. board identity, the 8-bit file, idle temperature ----
soc=$(adb shell getprop ro.soc.model < /dev/null | tr -d '\r')
say "board $ANDROID_SERIAL soc $soc"
[[ $soc == SM8650* ]] || { say "not an SM8650; stop"; exit 1; }
"${PY[@]}" -m bench.board stop < /dev/null > /dev/null
[[ -z "$(adb shell pidof llama-server < /dev/null | tr -d '\r')" ]] || { say "a llama-server is still running; stop"; exit 1; }
if ! adb shell ls /data/local/tmp/llm/$Q8 < /dev/null > /dev/null 2>&1; then
  avail=$(adb shell df /data < /dev/null | awk 'NR==2{print $4}')
  [ ${avail:-0} -ge 3670016 ] || { say "not enough space for $Q8 (${avail} KB); stop"; exit 1; }
  adb push ~/fieldmind-build/gguf/$Q8 /data/local/tmp/llm/ < /dev/null | tail -1 | tee -a $LOG
fi
bsha=$(adb shell sha256sum /data/local/tmp/llm/$Q8 < /dev/null | cut -d' ' -f1)
[[ $bsha == $Q8SHA ]] || { say "8-bit sha256 on the board $bsha != $Q8SHA; stop"; exit 1; }
say "8-bit file on the board, sha256 OK"
sleep 120
idle=$(temp | cut -d' ' -f1); COOL_C=$(awk "BEGIN{print $idle + 5}"); export COOL_C
say "idle $idle C after 2 min with no lane; cooling target $COOL_C C"

# ---- 6. speed check at our settings (one lane, NHVX=2, standard flags) ----
lane $Q4 speed_q4
"${PY[@]}" -m bench.board speed http://localhost:8080 < /dev/null > results/sm8650_speed_q4.json 2>&1
say "speed check q4 done: $(tr -d '\n' < results/sm8650_speed_q4.json | cut -c1-300)"

# ---- 1. 4-bit confirmation, NPU arms on the SM8650 (A3) ----
arm1() {  # model label
  local out=results/echo/h_prior_$2.jsonl
  cool; lane $1 $2; say "1 $2 start (temp $(temp))"
  "${PY[@]}" bench/echo_4bit.py run prior reports/data/echo_4bit_requests.json --url http://127.0.0.1:8080 --lane npu \
      --forms original --model $1 --label $2 --out $out < /dev/null >> $LOG 2>&1
  say "1 $2 end rc=$? (temp $(temp)); rows, failed = $(failed $out)"
}
for pair in "$Q4:npu8650_q4_0" "$Q8:npu8650_q8_0"; do
  model=${pair%%:*}; label=${pair#*:}; out=results/echo/h_prior_$label.jsonl
  arm1 $model $label
  nf=$(failed $out | cut -d' ' -f2)
  if [ ${nf:-999} -gt 20 ]; then
    mkdir -p results/echo/npu_failed; mv $out results/echo/npu_failed/h_prior_${label}_try1.jsonl
    say "1 $label: $nf failed > 20; moved aside; one rerun, same settings"
    arm1 $model $label
    nf=$(failed $out | cut -d' ' -f2)
    [ ${nf:-999} -gt 20 ] && { say "1 $label failed again ($nf); stop"; "${PY[@]}" -m bench.board stop < /dev/null; exit 1; }
  fi
done
say "run 1 done"

# ---- 2. FaultExplainer F1r (4-bit) and F2 (8-bit) on the SM8650 (A3) ----
for pair in "$Q4:F1r_sm8650_nhvx2:faultexplainer_F1r_sm8650" "$Q8:F2_sm8650_nhvx2_q8:faultexplainer_F2_sm8650"; do
  model=${pair%%:*}; rest=${pair#*:}; label=${rest%%:*}; file=${rest#*:}
  cool; lane $model $label
  FE_LOG=results/sm8650_runlog.txt PYBIN=$PYBIN zsh results/run_fe_rerun_sm8750.sh arm $label $model results/ext/$file.jsonl < /dev/null
  say "2 $label end rc=$?"
done
"${PY[@]}" -m bench.board stop < /dev/null > /dev/null
say "SM8650 runs 6, 1, 2 done"
