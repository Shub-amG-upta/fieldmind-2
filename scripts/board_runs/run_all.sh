#!/bin/bash
# Overnight queue: Cranfield dev (6), then report (10), multi-agent v3 on the QIDK; then the
# separate measuring pass; then the full test suite. A failed batch is run again with the same
# command, which skips finished episodes and resumes a cut one from its saved answers.
export PYTHONUTF8=1
unset PYTHONPATH
cd ~/fieldmind-2 || exit 1
LOG=~/qidk_logs
OV=configs/v3.yaml,configs/cranfield.yaml
MAX_TRIES=40

ids() { ls "$1" | grep '^cf_' | tr '\n' ' '; }

run_set() {   # run_set <test name> <episode folder>
    local name=$1 eps rc; eps=$(ids "$2")
    for try in $(seq 1 $MAX_TRIES); do
        echo ">>> $(date '+%F %T') $name: attempt $try" | tee -a $LOG/queue.log
        echo ">>> $name: attempt $try" >> $LOG/current.trace.log
        # a hard crash can leave a sampler on the board; the runner starts its own (by name, no file removed)
        ~/platform-tools/adb shell 'pkill -f board_sampler.sh' >/dev/null 2>&1
        scripts/benchmark.sh "$name" $eps --overlay $OV --trace-to $LOG/current.trace.log
        rc=$?
        echo ">>> $(date '+%F %T') $name: attempt $try ended, exit $rc" | tee -a $LOG/queue.log
        [ "$rc" = 0 ] && return 0
        ~/platform-tools/adb start-server >/dev/null 2>&1
        sleep 60
    done
    echo ">>> $(date '+%F %T') $name: GAVE UP after $MAX_TRIES attempts" | tee -a $LOG/queue.log
    return 1
}

# the runner's cooling target is the chip temperature at batch start, so let it cool first
echo ">>> $(date '+%F %T') waiting 10 minutes for the chip to cool" | tee -a $LOG/queue.log
sleep 600
run_set cranfield_dev_v3 data/episodes_cranfield_dev;  dev=$?
run_set cranfield_report_v3 data/episodes_cranfield;   rep=$?
echo ">>> $(date '+%F %T') timed runs ended: dev exit $dev, report exit $rep. Cooling, then the measuring pass." | tee -a $LOG/queue.log
sleep 600
bash $LOG/meas.sh
echo ">>> $(date '+%F %T') measuring pass ended. Full test suite next." | tee -a $LOG/queue.log
timeout 5400 .venv/bin/python -m pytest -q --tb=line > $LOG/full_tests.log 2>&1
echo ">>> $(date '+%F %T') full test suite exit $?: $(tail -1 $LOG/full_tests.log)" | tee -a $LOG/queue.log
echo "dev=$dev report=$rep" > $LOG/ALL_DONE
echo ">>> ALL DONE"
