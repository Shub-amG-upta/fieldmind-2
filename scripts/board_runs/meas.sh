#!/bin/bash
# The separate measuring pass (BEV_MEASUREMENT_PLAN.md: heavy tools never run in a timed arm).
# Idle baseline with the lanes loaded, then two dev episodes with memory snapshots each minute,
# a perfetto system trace and simpleperf on both lanes. These runs are NOT for timing or accuracy.
# A tool that fails is written down and never stops anything.
cd ~/fieldmind-2 || exit 1
unset PYTHONPATH
export PYTHONUTF8=1
A=~/platform-tools/adb
LOG=~/qidk_logs
M=results/benchmarks/cranfield_meas/measure
mkdir -p "$M"
OV=configs/v3.yaml,configs/cranfield.yaml

trace_cfg() { sed "s/duration_ms: [0-9]*/duration_ms: $1/" $LOG/sys.pbtx; }
perfetto_run() {   # perfetto_run <name> <ms>
    trace_cfg "$2" | $A shell "perfetto --txt -c - -o /data/misc/perfetto-traces/fm_$1.pftrace" >> "$M/perfetto.log" 2>&1
    $A pull "/data/misc/perfetto-traces/fm_$1.pftrace" "$M/$1.pftrace" >> "$M/perfetto.log" 2>&1
}
perf_stat() {      # perf_stat <name>: 20 s on each lane
    for p in $($A shell pidof llama-server | tr -d '\r'); do
        $A shell "simpleperf stat -p $p --duration 20 2>&1" > "$M/simpleperf_$1_$p.txt" &
    done
    wait
}
snapshot() {       # snapshot <name>
    .venv/bin/python -c "
import json, sys
from pathlib import Path
from bench import board_sampler as b
n = sys.argv[1]; d = Path('$M')
json.dump(b.memory_snapshot(d / f'memory_{n}.txt'), open(d / f'memory_{n}.json', 'w'), indent=1)" "$1"
}

echo ">>> $(date '+%F %T') measuring: idle baseline, 120 s, lanes loaded" | tee -a $LOG/queue.log
.venv/bin/python -m bench.board stop >/dev/null 2>&1
.venv/bin/python -m bench.board start npu Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf > "$M/idle_start.log" 2>&1
.venv/bin/python -m bench.board start cpu gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf >> "$M/idle_start.log" 2>&1
snapshot idle_after_load
.venv/bin/python -c "
import json, time
from pathlib import Path
from bench import board_sampler as b
d = Path('$M'); h = b.start('idle_baseline'); time.sleep(120)
json.dump(b.stop(h, d / 'idle_samples.txt'), open(d / 'idle_resources.json', 'w'), indent=1)" >> "$M/idle_start.log" 2>&1 &
perfetto_run idle 100000 &
perf_stat idle &
wait
snapshot idle_end
.venv/bin/python -m bench.board stop >/dev/null 2>&1

(
    n=0
    sleep 45
    while pgrep -f "bench/benchmark.py cranfield_meas" >/dev/null; do
        n=$((n + 1))
        if $A shell pidof llama-server >/dev/null 2>&1; then
            snapshot "during_$n"
            [ $((n % 3)) = 1 ] && { perfetto_run "during_$n" 60000 & perf_stat "during_$n" & wait; }
        fi
        sleep 60
    done
) &
LOOP=$!

echo ">>> $(date '+%F %T') measuring: two episodes with the tools on" | tee -a $LOG/queue.log
for try in 1 2 3; do
    scripts/benchmark.sh cranfield_meas cf_F5_5.1_slugging_conditions cf_F6_6.1_pressurization_of_the_2in_line \
        --overlay $OV --trace-to $LOG/current.trace.log
    rc=$?
    echo ">>> $(date '+%F %T') measuring: attempt $try ended, exit $rc" | tee -a $LOG/queue.log
    [ "$rc" = 0 ] && break
    sleep 60
done
kill $LOOP 2>/dev/null
wait $LOOP 2>/dev/null
exit 0
