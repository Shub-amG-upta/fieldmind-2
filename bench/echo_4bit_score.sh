#!/bin/zsh
# Score the 4-bit against 8-bit confirmation (reports/echo_4bit_prereg.md): 95% intervals, 2,000 resamples,
# seed 20261111. Writes $OUT/scores/4bit_{H,R_<plant>,mmluprob,squad}.json, plus 4bit_H_npu.json when the
# board rows exist. Laptop replays, not NPU results, except the npu_ arms.
#   bench/echo_4bit_score.sh            (OUT=results/echo by default)
set -eu
cd "${0:A:h}/.."
PY=(env -u PYTHONPATH .venv/bin/python)
OUT=${OUT:-results/echo}
S=$OUT/scores
mkdir -p $S
# the precision pairs of the pre-registration (low:high, same weights)
PAIRS=(--pair m1_q4_0:m2_q8_0 --pair m2_q8_0:m2b_bf16
       --pair m5_qwen25_05b_q4_0:m5_qwen25_05b_q8_0 --pair m6_gemma3_1b_q4_0:m6_gemma3_1b_q8_0
       --pair m7_qwen3_17b_q4_0:m7_qwen3_17b_q8_0 --pair m3_qwen25_7b_q4_0:m3_qwen25_7b_q8_0
       --pair m4_llama31_8b_q4_0:m4_llama31_8b_q8_0)
lap=($OUT/h_prior_m*.jsonl(N))
if (( $#lap )); then
  "${PY[@]}" bench/echo_4bit.py score signal reports/data/echo_4bit_requests.json $lap "${PAIRS[@]}" \
      --bootstrap 2000 | tail -n +2 > $S/4bit_H.json
fi
npu=($OUT/h_prior_npu_*.jsonl(N))
if (( $#npu )); then
  "${PY[@]}" bench/echo_4bit.py score signal reports/data/echo_4bit_requests.json $npu \
      --pair npu_q4_0:npu_q8_0 --bootstrap 2000 | tail -n +2 > $S/4bit_H_npu.json
fi
rr=($OUT/prior_m*.jsonl(N))
if (( $#rr )); then
  for p in boiler cranfield tep; do
    "${PY[@]}" bench/echo_4bit.py score signal reports/data/echo_requests.json $rr "${PAIRS[@]}" \
        --plant $p --bootstrap 2000 | tail -n +2 > $S/4bit_R_$p.json
  done
fi
mm=($OUT/mmluprob_m*.jsonl(N))
if (( $#mm )); then
  "${PY[@]}" bench/echo_4bit.py score mmluprob reports/data/nd_public_requests.json $mm "${PAIRS[@]}" \
      --bootstrap 2000 | tail -n +2 > $S/4bit_mmluprob.json
fi
sq=($OUT/squad_m*.jsonl(N))
if (( $#sq )); then
  "${PY[@]}" bench/echo_4bit.py score squad reports/data/echo_4bit_squad.json $sq "${PAIRS[@]}" \
      --bootstrap 2000 | tail -n +2 > $S/4bit_squad.json
fi
ls -la $S/4bit_*.json
