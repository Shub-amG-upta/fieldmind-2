#!/bin/bash
unset PYTHONPATH; export PYTHONUTF8=1
L=~/qidk_logs; Q=$L/queue.log; cd ~/fieldmind-tep || exit 1
OV=configs/v3.yaml,configs/cranfield.yaml,configs/case_shuffled.yaml
echo ">>> shuffled test" >> $L/current.trace.log
for try in $(seq 1 25); do
    echo ">>> $(date '+%F %T') cranfield_dev_v3_shuffled: attempt $try" | tee -a $Q
    ~/platform-tools/adb shell 'pkill -f board_sampler.sh' >/dev/null 2>&1
    scripts/benchmark.sh cranfield_dev_v3_shuffled $(ls data/episodes_cranfield_dev) --overlay $OV --trace-to $L/current.trace.log
    rc=$?
    echo ">>> $(date '+%F %T') cranfield_dev_v3_shuffled: attempt $try ended, exit $rc" | tee -a $Q
    [ "$rc" = 0 ] && break
    ~/platform-tools/adb start-server >/dev/null 2>&1
    sleep 60
done
echo "rc=$rc" > $L/SHUF_DONE
echo ">>> SHUFFLED TEST DONE"
