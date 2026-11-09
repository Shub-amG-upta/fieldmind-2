#!/bin/bash
# After the Cranfield queue: TEP data, safety checks, TEP board subset, then the Cranfield
# single-agent baseline. Needs no one. A setup failure stops before the board and says why.
unset PYTHONPATH
export PYTHONUTF8=1
L=~/qidk_logs
Q=$L/queue.log
cd ~/fieldmind-tep || exit 1
fail() { echo ">>> $(date '+%F %T') TEP SETUP FAILED: $1" | tee -a $Q; echo "$1" > $L/TEP_SETUP_FAILED; exit 1; }

while pgrep -f 'dataverse.harvard.edu' >/dev/null; do sleep 30; done
echo ">>> $(date '+%F %T') TEP: download ended, building episodes" | tee -a $Q
nice -n 19 .venv/bin/python -m data.tep.convert > $L/tep_convert.log 2>&1 || fail "convert: $(tail -1 $L/tep_convert.log)"
nice -n 19 .venv/bin/python -m data.tep.convert --board >> $L/tep_convert.log 2>&1 || fail "convert --board: $(tail -1 $L/tep_convert.log)"
n=$(ls data/episodes_tep_board | wc -l)
[ "$n" = 22 ] || fail "expected 22 board episodes, found $n"
timeout 900 nice -n 19 .venv/bin/python -m pytest -q --tb=short tests/test_asset_params.py tests/test_tep_pack.py tests/test_call_journal.py > $L/tep_tests.log 2>&1 \
    || fail "tests: $(tail -1 $L/tep_tests.log)"

# safety test on mock: kill -9 mid-episode, resume, rankings must equal an uncut run
OV=configs/v3.yaml,configs/tep.yaml
E=$(ls data/episodes_tep_board | grep -v -i normal | head -1)
R=results/benchmarks_mock
rm -rf $R/tep_whole $R/tep_cut
scripts/benchmark.sh tep_whole "$E" --backend mock --overlay $OV --trace > $L/tep_mock1.log 2>&1 || fail "mock run: $(tail -1 $L/tep_mock1.log)"
scripts/benchmark.sh tep_cut "$E" --backend mock --overlay $OV --trace > $L/tep_mock2.log 2>&1 &
for i in $(seq 1 1200); do
    c=$(cat $R/tep_cut/*.calls.jsonl 2>/dev/null | grep -c '"event": "done"')
    [ "${c:-0}" -ge 25 ] && break
    sleep 0.1
done
pkill -9 -f 'bench/benchmark.py tep_cut'; pkill -9 -f 'run_demo.py.*tep_cut'; sleep 2
scripts/benchmark.sh tep_cut "$E" --backend mock --overlay $OV --trace > $L/tep_mock3.log 2>&1 || fail "mock resume: $(tail -1 $L/tep_mock3.log)"
.venv/bin/python - > $L/tep_mock_check.log 2>&1 <<'PY' || fail "cut and resumed mock run differs: see tep_mock_check.log"
import glob, gzip, json
def load(t):
    return json.load(gzip.open(glob.glob(f"results/benchmarks_mock/{t}/*_multi.run.json.gz")[0], "rt"))
def rk(r):
    return [(a["tick"], a["state"], a["triage"], [h.get("case_ref") for h in a.get("hypotheses") or []], a.get("confidence")) for a in r["assessments"]]
a, b = load("tep_whole"), load("tep_cut")
print("ticks", len(a["assessments"]), "resume", b.get("resume"), "same", rk(a) == rk(b))
raise SystemExit(0 if rk(a) == rk(b) and b["resume"]["resumed"] else 1)
PY
echo ">>> $(date '+%F %T') TEP: setup and mock kill test passed; waiting for the Cranfield queue" | tee -a $Q

until [ -f $L/ALL_DONE ]; do sleep 60; done
pgrep -f 'bench/benchmark.py' >/dev/null && sleep 120
sleep 300     # cooling, so the batch's temperature target is not set by a hot chip
tmux select-window -t qidk:tep 2>/dev/null

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
