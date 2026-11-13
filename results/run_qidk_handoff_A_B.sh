#!/bin/zsh
# HANDOFF_QIDK_RUNS.md (branch fe-baseline), run on Gagan's Mac 2026-11-13: run A (HANDOFF_4BIT.md Q1-Q2, 4-bit then
# 8-bit Llama 3B, NPU, NHVX=2, 400 calls each), then run B (FaultExplainer F2, 8-bit, 108 calls). Not scored.
# Board handover: waits for nd-paper's M9-8 sweep to finish pass A (arm TA2), then stops that driver during its
# cooling wait (no call in flight), so no nd-paper arm is cut. The nd-paper session resumes its work afterwards.
# Cooling (decision, recorded in RUNLOG_4bit.txt): Shubham's SM8750 rule from reports/ext_faultexplainer_prereg.md A2
# (idle + 5 = 38.8 C, at most 900 s), since HANDOFF_4BIT says only "the usual cooling rule".
# Run from anywhere: nohup caffeinate -dimsu zsh ~/projects/fieldmind-bc/results/run_qidk_handoff_A_B.sh > ~/projects/fieldmind-bc/results/qidk_handoff_A_B.out 2>&1 < /dev/null &
set -u
cd "${0:A:h}/.."
export ANDROID_SERIAL=1d9c8f40
PY=(env -u PYTHONPATH $PWD/.venv/bin/python)
LOG=results/echo/RUNLOG_4bit.txt
ND=~/projects/fieldmind
NDLOG=$ND/results/nd/m9_threads_sm8750/m9.log
Q8=Llama-3.2-3B-Instruct-Q8_0-pure.gguf; Q8SHA=d91f61aba2e998c3fbfb46a4cd0710e8ed4c9b9fca2d4290f6dfc80ad0738fc2
Q4=Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf
say() { echo "$(date '+%F %T') $*" | tee -a $LOG; }
temp() { "${PY[@]}" -m bench.board temp < /dev/null 2>/dev/null | .venv/bin/python -c 'import json,sys; d=json.load(sys.stdin); print(d["cpu_max_c"], d.get("npu_max_c"))'; }
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
failed() { .venv/bin/python -c "import json,sys; r=[json.loads(l) for l in open(sys.argv[1])]; print(len(r), sum(x.get('status')!='ok' for x in r))" $1; }

# ---- 0. board handover from nd-paper M9-8 (after pass A) ----
say "handoff A+B driver start; waiting for nd-paper M9-8 pass A to end (arm TA2)"
while pgrep -f "zsh results/nd/run_m9_8.sh" > /dev/null && ! grep -q "TA2_nhvx2 done" $NDLOG; do sleep 15; done
pkill -f "results/nd/run_m9_8.sh"; pkill -f "bench/nd_queue.sh results/nd/m9_threads_sm8750"; sleep 3
echo "$(date '+%F %T') PAUSED after pass A (TA2 done), before any TB call: board lent to Shubham's QIDK handoff A+B (human 17:05). Pass B resumes afterwards." >> $NDLOG
"${PY[@]}" -m bench.board stop < /dev/null
[[ -z "$(adb shell pidof llama-server < /dev/null | tr -d '\r')" ]] || { say "a llama-server is still running; stop"; exit 1; }
say "board free; nd-paper M9-8 paused after pass A"

# ---- Q1. the 8-bit 3B on the board ----
avail=$(adb shell df /data < /dev/null | awk 'NR==2{print $4}')   # 1K blocks
if adb shell ls /data/local/tmp/llm/$Q8 < /dev/null > /dev/null 2>&1; then
  say "Q1: $Q8 already on the board; no push"
else
  say "Q1: board /data free ${avail} KB; need about 3.5 GB"
  [ ${avail:-0} -ge 3670016 ] || { say "Q1: not enough space; stop and ask"; exit 1; }
  adb push ~/fieldmind-build/gguf/$Q8 /data/local/tmp/llm/ < /dev/null | tail -1 | tee -a $LOG
fi
bsha=$(adb shell sha256sum /data/local/tmp/llm/$Q8 < /dev/null | cut -d' ' -f1)
lsha=$(shasum -a 256 ~/fieldmind-build/gguf/$Q8 | cut -d' ' -f1)
say "Q1: sha256 board $bsha laptop $lsha required $Q8SHA"
[[ $bsha == $Q8SHA && $lsha == $Q8SHA ]] || { say "Q1: sha256 mismatch; stop"; exit 1; }

# ---- Q2. run A: 4-bit then 8-bit ----
arm() {  # model label try
  local model=$1 label=$2 out=results/echo/h_prior_$2.jsonl
  "${PY[@]}" -m bench.board stop < /dev/null > /dev/null
  cool; say "A $label: temp before $(temp)"
  ND_LANE_ENV="GGML_HEXAGON_NHVX=2" "${PY[@]}" -m bench.board start npu $model < /dev/null > results/echo/lane_$label.txt 2>&1
  .venv/bin/python -c 'import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if d.get("nd_env")==["GGML_HEXAGON_NHVX=2"] else 1)' results/echo/lane_$label.txt || { say "A $label: start printout lacks nd_env NHVX=2; stop"; cat results/echo/lane_$label.txt >> $LOG; return 2; }
  "${PY[@]}" -m bench.board log npu < /dev/null | grep -i -E "hwinfo|offloaded|HTP0 model buffer" | tee -a results/echo/lane_$label.txt >> $LOG
  grep -q "hwinfo: threads 2, hvx 2" results/echo/lane_$label.txt || { say "A $label: log does not show 2 HVX threads; stop, arm not run"; return 2; }
  say "A $label: start"
  "${PY[@]}" bench/echo_4bit.py run prior reports/data/echo_4bit_requests.json --url http://127.0.0.1:8080 --lane npu \
      --forms original --model $model --label $label --out $out < /dev/null >> $LOG 2>&1
  say "A $label: end rc=$? temp after $(temp); rows, failed = $(failed $out)"
}
for pair in "$Q4:npu_q4_0" "$Q8:npu_q8_0"; do
  model=${pair%%:*}; label=${pair#*:}; out=results/echo/h_prior_$label.jsonl
  arm $model $label || exit 1
  nf=$(failed $out | cut -d' ' -f2)
  if [ ${nf:-999} -gt 20 ]; then
    mkdir -p results/echo/npu_failed; mv $out results/echo/npu_failed/h_prior_${label}_try1.jsonl
    say "A $label: $nf failed calls > 20; moved to npu_failed/h_prior_${label}_try1.jsonl; one rerun, same settings"
    arm $model $label || exit 1
    nf=$(failed $out | cut -d' ' -f2)
    [ ${nf:-999} -gt 20 ] && { say "A $label: failed again ($nf); stop"; "${PY[@]}" -m bench.board stop < /dev/null; exit 1; }
  fi
done
"${PY[@]}" -m bench.board stop < /dev/null > /dev/null
say "run A done"

# ---- run B: FaultExplainer F2, 8-bit ----
mkdir -p results/ext
cool
ND_LANE_ENV="GGML_HEXAGON_NHVX=2" "${PY[@]}" -m bench.board start npu $Q8 < /dev/null > results/ext/fe_lane_q8.txt 2>&1
"${PY[@]}" -m bench.board log npu < /dev/null | grep -E "llama_model_loader: - type|HTP0 hwinfo|offloaded|HTP0 model buffer|n_slots" >> results/ext/fe_lane_q8.txt
grep -q "hwinfo: threads 2, hvx 2" results/ext/fe_lane_q8.txt && grep -q "q8_0: *197 tensors" results/ext/fe_lane_q8.txt \
  || { say "B: lane check failed (threads 2 / q8_0 197 tensors); stop"; cat results/ext/fe_lane_q8.txt >> $LOG; exit 1; }
say "B: lane checked; F2 start"
zsh results/run_fe_rerun_sm8750.sh arm F2_npu_nhvx2_q8 $Q8 results/ext/faultexplainer_F2.jsonl < /dev/null
say "B: F2 end rc=$?"
"${PY[@]}" -m bench.board stop < /dev/null > /dev/null
say "handoff A+B driver done"
