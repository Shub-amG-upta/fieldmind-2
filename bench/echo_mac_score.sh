#!/bin/zsh
# Score every ECHO arm on the 24 GB Mac (HANDOFF_MAC_RUNS.md), 95% intervals (2,000 resamples, seed 20261111).
#   bench/echo_mac_score.sh            -> results/echo/scores/{R_pooled,R_<plant>,relabel,prior,mmlu}.json
# Laptop replays of the models, not NPU results.
set -eu
cd "${0:A:h}/.."
PY=(env -u PYTHONPATH .venv/bin/python)
OUT=${OUT:-results/echo}
S=$OUT/scores
mkdir -p $S
"${PY[@]}" bench/echo_test.py score reports/data/echo_requests.json $OUT/R_*.jsonl --bootstrap 2000 > $S/R_pooled.json
for p in boiler cranfield tep; do
  "${PY[@]}" bench/echo_test.py score reports/data/echo_requests.json $OUT/R_*.jsonl --bootstrap 2000 --plant $p > $S/R_$p.json
done
for t in relabel prior; do
  ls $OUT/${t}_*.jsonl >/dev/null 2>&1 || continue
  "${PY[@]}" bench/echo_causes.py score $t reports/data/echo_requests.json $OUT/${t}_*.jsonl --bootstrap 2000 \
      | tail -n +2 > $S/$t.json
done
if ls $OUT/mmlu_*.jsonl >/dev/null 2>&1; then
  "${PY[@]}" bench/echo_causes.py score mmlu reports/data/nd_public_requests.json $OUT/mmlu_*.jsonl --bootstrap 2000 \
      | tail -n +2 > $S/mmlu.json
fi
ls -la $S
