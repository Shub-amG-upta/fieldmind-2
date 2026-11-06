#!/bin/bash
# After Cranfield with bev: the 22 TEP board episodes with the bev-decider. Needs the conformance gate
# in run_bev.sh to have passed; if it did not, this does not run.
unset PYTHONPATH; export PYTHONUTF8=1
export PATH=$HOME/platform-tools:$PATH
L=~/qidk_logs; Q=$L/queue.log; cd ~/fieldmind-tep || exit 1
until [ -f $L/BEV_DONE ] || [ -f $L/BEV_BLOCKED ]; do sleep 30; done
if [ -f $L/BEV_BLOCKED ]; then
    echo ">>> $(date '+%F %T') TEP with bev not run: conformance did not pass" | tee -a $Q
    echo "blocked" > $L/BEVTEP_ALL_DONE; exit 1
fi
sleep 300
OV=configs/bev3.yaml,configs/tep.yaml
for try in $(seq 1 40); do
    echo ">>> $(date '+%F %T') tep_v3_bev_board: attempt $try" | tee -a $Q
    adb shell 'pkill -f board_sampler.sh' >/dev/null 2>&1
    scripts/benchmark.sh tep_v3_bev_board $(ls data/episodes_tep_board) --arch bev --overlay $OV --trace-to $L/current.trace.log
    rc=$?
    echo ">>> $(date '+%F %T') tep_v3_bev_board: attempt $try ended, exit $rc" | tee -a $Q
    [ "$rc" = 0 ] && break
    adb start-server >/dev/null 2>&1
    sleep 60
done
echo "rc=$rc" > $L/BEVTEP_ALL_DONE
echo ">>> BEV TEP DONE"
