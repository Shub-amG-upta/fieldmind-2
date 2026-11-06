#!/bin/bash
# After Cranfield with the decider: Cranfield dev then TEP board subset, bev ideas explain + clear_skip.
# Each finished test is committed locally to breadth-board-runs (never pushed). Needs the conformance gate.
unset PYTHONPATH; export PYTHONUTF8=1
export PATH=$HOME/platform-tools:$PATH
L=~/qidk_logs; Q=$L/queue.log; cd ~/fieldmind-tep || exit 1
IFS=$'\t' read -r GN GE < $L/gitid

commit() {   # commit <test name> <what>
    mkdir -p results/board_runs_logs
    cp $L/queue.log $L/bev_gate.log results/board_runs_logs/ 2>/dev/null
    git add -f results/board_runs_logs >/dev/null 2>&1
    git add results/benchmarks reports/data scripts/board_runs >/dev/null 2>&1
    if git -c user.name="$GN" -c user.email="$GE" commit -q -m "Board run finished: $1 ($2)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"; then
        echo ">>> $(date '+%F %T') committed $1: $(git log --oneline -n 1 | cut -c1-8)" | tee -a $Q
    else
        echo ">>> $(date '+%F %T') COMMIT FAILED or nothing to commit for $1" | tee -a $Q
    fi
}

run_set() {  # run_set <test name> <episode folder> <overlay>
    local name=$1 dir=$2 ov=$3 rc
    for try in $(seq 1 40); do
        echo ">>> $(date '+%F %T') $name: attempt $try" | tee -a $Q
        adb shell 'pkill -f board_sampler.sh' >/dev/null 2>&1
        scripts/benchmark.sh "$name" $(ls "$dir") --overlay "$ov" --bev "explain=on,clear_skip=on" --trace-to $L/current.trace.log
        rc=$?
        echo ">>> $(date '+%F %T') $name: attempt $try ended, exit $rc" | tee -a $Q
        [ "$rc" = 0 ] && return 0
        adb start-server >/dev/null 2>&1
        sleep 60
    done
    echo ">>> $(date '+%F %T') $name: GAVE UP" | tee -a $Q
    return 1
}

until [ -f $L/BEV_DONE ] || [ -f $L/BEV_BLOCKED ]; do sleep 30; done
if [ -f $L/BEV_BLOCKED ]; then
    echo ">>> $(date '+%F %T') bev ideas not run: conformance did not pass" | tee -a $Q
    echo "blocked" > $L/BEVTEP_ALL_DONE; exit 1
fi
cp $L/run_ideas.sh $L/run_bev.sh scripts/board_runs/ 2>/dev/null
commit cranfield_dev_v3_bev "6 episodes, bev decider"
sleep 300
run_set cranfield_dev_bev_explain_skip data/episodes_cranfield_dev configs/bev_ideas.yaml,configs/cranfield.yaml; a=$?
commit cranfield_dev_bev_explain_skip "6 episodes, explain + clear_skip, exit $a"
sleep 300
run_set tep_bev_explain_skip_board data/episodes_tep_board configs/bev_ideas.yaml,configs/tep.yaml; b=$?
commit tep_bev_explain_skip_board "22 episodes, explain + clear_skip, exit $b"
echo "cranfield=$a tep=$b" > $L/BEVTEP_ALL_DONE
echo ">>> ALL DONE"
