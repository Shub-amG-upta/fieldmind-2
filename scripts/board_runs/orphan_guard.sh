#!/bin/bash
# If a board run_demo is alive with no runner above it, stop it: its answers are journalled and the
# queue's next attempt resumes from them. Without this, retries are refused until it ends by itself.
L=~/qidk_logs
until [ -f $L/TEP_ALL_DONE ]; do
    if pgrep -f 'run_demo.py --backend llamaserver' >/dev/null && ! pgrep -f 'bench/benchmark.py' >/dev/null; then
        sleep 10
        if pgrep -f 'run_demo.py --backend llamaserver' >/dev/null && ! pgrep -f 'bench/benchmark.py' >/dev/null; then
            pkill -f 'run_demo.py --backend llamaserver'
            echo ">>> $(date '+%F %T') orphan_guard: stopped a run with no runner above it" >> $L/queue.log
        fi
    fi
    sleep 20
done
