#!/bin/zsh
# Redo of item 1's 8-bit arm npu8650_q8_0 (A3) after the SM8650 disconnected and rebooted at about 22:59 (250 of 400 calls).
# Decision (Gagan's Mac, conservative, recorded): the partial file is moved aside and the whole arm is rerun in one server
# session, as A2's rerun rule does; the same settings as results/run_sm8650_6_1_2.sh (NHVX=2, cooling target 36.2 C = the
# idle 31.2 C measured at 22:06 + 5, at most 900 s). Then nd-paper's M9-13 driver is restarted.
set -u
cd "${0:A:h}/.."
export ANDROID_SERIAL=ab8f6592
PYBIN=$PWD/.venv/bin/python; PY=(env -u PYTHONPATH $PYBIN)
LOG=results/sm8650_runlog.txt; COOL_C=36.2
Q8=Llama-3.2-3B-Instruct-Q8_0-pure.gguf; label=npu8650_q8_0; out=results/echo/h_prior_$label.jsonl
say() { echo "$(date '+%F %T') $*" | tee -a $LOG; }
temp() { "${PY[@]}" -m bench.board temp < /dev/null 2>/dev/null | $PYBIN -c 'import json,sys; d=json.load(sys.stdin); print(d["cpu_max_c"], d.get("npu_max_c"))'; }
cool() { local t0=$(date +%s) c; while true; do c=$(temp | cut -d' ' -f1); [[ -n $c && $c != None ]] && awk "BEGIN{exit !($c <= $COOL_C)}" && break; [ $(( $(date +%s) - t0 )) -ge 900 ] && break; sleep 20; done; say "cooled to $c C after $(( $(date +%s) - t0 )) s"; }
failed() { $PYBIN -c "import json,sys; r=[json.loads(l) for l in open(sys.argv[1])]; print(len(r), sum(x.get('status')!='ok' for x in r))" $1; }
mkdir -p results/echo/npu_failed
[ -e $out ] && { mv $out results/echo/npu_failed/h_prior_${label}_try1_disconnect.jsonl; say "1 $label: partial file (board disconnect) moved to npu_failed/h_prior_${label}_try1_disconnect.jsonl; whole arm rerun, same settings"; }
"${PY[@]}" -m bench.board stop < /dev/null > /dev/null
cool
ND_LANE_ENV="GGML_HEXAGON_NHVX=2" "${PY[@]}" -m bench.board start npu $Q8 < /dev/null > results/sm8650_lane_${label}_redo.txt 2>&1
"${PY[@]}" -m bench.board log npu < /dev/null | grep -E "hwinfo|offloaded|HTP0 model buffer" | tr '\n' ' ' >> results/sm8650_lane_${label}_redo.txt
grep -q "hwinfo: threads 2" results/sm8650_lane_${label}_redo.txt || { say "lane $label redo: log does not show 2 threads; stop"; exit 1; }
say "1 $label redo start (temp $(temp))"
"${PY[@]}" bench/echo_4bit.py run prior reports/data/echo_4bit_requests.json --url http://127.0.0.1:8080 --lane npu \
    --forms original --model $Q8 --label $label --out $out < /dev/null >> $LOG 2>&1
say "1 $label redo end rc=$? (temp $(temp)); rows, failed = $(failed $out)"
"${PY[@]}" -m bench.board stop < /dev/null > /dev/null
say "run 1 redo done"
cd ~/projects/fieldmind && nohup caffeinate -dimsu zsh results/nd/run_m9_13.sh >> results/nd/m9_master_sm8650.out 2>&1 < /dev/null &
