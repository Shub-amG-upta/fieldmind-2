#!/bin/bash
# Continues after the pause at TEP episode 4: finished episodes are skipped, the cut one resumes.
unset PYTHONPATH
export PYTHONUTF8=1
L=~/qidk_logs
Q=$L/queue.log
OV=configs/v3.yaml,configs/tep.yaml
cd ~/fieldmind-tep || exit 1

run_set() {   # run_set <test name> <extra args...>
    local name=$1 rc; shift
    for try in $(seq 1 40); do
        echo ">>> $(date '+%F %T') $name: attempt $try" | tee -a $Q
        echo ">>> $name: attempt $try" >> $L/current.trace.log
        ~/platform-tools/adb shell 'pkill -f board_sampler.sh' >/dev/null 2>&1
        scripts/benchmark.sh "$name" "$@" --trace-to $L/current.trace.log
        rc=$?
        echo ">>> $(date '+%F %T') $name: attempt $try ended, exit $rc" | tee -a $Q
        [ "$rc" = 0 ] && return 0
        ~/platform-tools/adb start-server >/dev/null 2>&1
        sleep 60
    done
    echo ">>> $(date '+%F %T') $name: GAVE UP" | tee -a $Q
    return 1
}
run_set tep_v3_board $(ls data/episodes_tep_board) --overlay $OV;  t=$?
sleep 300
run_set cf_single_report $(ls data/episodes_cranfield) --arch single --overlay configs/cranfield.yaml;  s=$?
echo ">>> $(date '+%F %T') TEP queue ended: tep exit $t, single exit $s" | tee -a $Q
echo "tep=$t single=$s" > $L/TEP_ALL_DONE
echo ">>> ALL DONE"
