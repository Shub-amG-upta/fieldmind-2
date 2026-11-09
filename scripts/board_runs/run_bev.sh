#!/bin/bash
# After the shuffled test: the live conformance check BEV_CONFORMANCE_FIX.md asks for, then, only if it
# passes, Cranfield dev with the bev-decider. Rule written down before the check: a pass is tokens
# 24/24 and the top answer matching on nearly all 24; about 8/24 means stop.
unset PYTHONPATH; export PYTHONUTF8=1
export PATH=$HOME/platform-tools:$PATH
L=~/qidk_logs; Q=$L/queue.log; cd ~/fieldmind-tep || exit 1
GG=bev-decider-0.4B-backbone-Q8_0.gguf
until [ -f $L/SHUF_DONE ]; do sleep 30; done
# human decision: push everything to git first; started by creating PUSH_DONE
until [ -f $L/PUSH_DONE ]; do sleep 20; done
sleep 60
blocked() { echo ">>> $(date '+%F %T') BEV NOT RUN: $1" | tee -a $Q; echo "$1" > $L/BEV_BLOCKED; exit 1; }
echo ">>> $(date '+%F %T') bev: live conformance check" | tee -a $Q
.venv/bin/python -m bench.board stop >/dev/null 2>&1
.venv/bin/python -m bench.board start bev $GG > $L/bev_start.log 2>&1 || blocked "bev-decide did not start: $(tail -1 $L/bev_start.log | cut -c1-200)"
R=reports/data/bev_reference_rope1e6.json
.venv/bin/python -m bench.bev_conformance compare http://localhost:8082 --reference $R --label npu-q8-rope1e6 \
    --out reports/data/bev_conformance_npu-q8-rope1e6.json > $L/bev_conf_npu.log 2>&1
echo "conformance npu exit $?" | tee -a $Q
.venv/bin/python -m bench.board stop bev >/dev/null 2>&1
.venv/bin/python - > $L/bev_gate.log 2>&1 <<'PY'
import json
r = json.load(open("reports/data/bev_conformance_npu-q8-rope1e6.json"))
n = len(r["rows"])
print({k: r.get(k) for k in ("tokens_identical", "rank1_agree", "median_abs_dp", "max_abs_dp", "latency_ms_median")}, "of", n)
for d in r.get("rank1_disagreements") or []:
    print(" disagreement:", {k: d.get(k) for k in list(d)[:6]})
raise SystemExit(0 if r["pass_tokens"] and n and r["rank1_agree"] >= n - 2 else 1)
PY
g=$?
cat $L/bev_gate.log | cut -c1-200 | tee -a $Q
[ "$g" = 0 ] || blocked "conformance did not pass: see bev_gate.log"
OV=configs/bev3.yaml,configs/cranfield.yaml
sleep 240
for try in $(seq 1 25); do
    echo ">>> $(date '+%F %T') cranfield_dev_v3_bev: attempt $try" | tee -a $Q
    adb shell 'pkill -f board_sampler.sh' >/dev/null 2>&1
    scripts/benchmark.sh cranfield_dev_v3_bev $(ls data/episodes_cranfield_dev) --arch bev --overlay $OV --trace-to $L/current.trace.log
    rc=$?
    echo ">>> $(date '+%F %T') cranfield_dev_v3_bev: attempt $try ended, exit $rc" | tee -a $Q
    [ "$rc" = 0 ] && break
    adb start-server >/dev/null 2>&1
    sleep 60
done
echo "rc=$rc" > $L/BEV_DONE
echo ">>> BEV DONE"
