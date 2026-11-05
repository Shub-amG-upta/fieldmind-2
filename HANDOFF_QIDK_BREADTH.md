# QIDK handoff: Cranfield and TEP board runs (breadth B1/B2)

For whoever runs the board (and that laptop's Claude). Branch **`breadth-tep`** (it contains the
Cranfield work too). Everything below was run end to end in **mock** mode on 2026-11-06; nothing has
run on the board yet.

What is new for the board: two more plants, each a config overlay on the same agent.
- **Cranfield** (oil & gas rig, REAL data): 16 fault episodes (6 dev, 10 report), 30 s ticks.
- **TEP** (chemical plant, simulated): a 22-episode **board subset** — the dev runs cut to 16 h
  (8 h normal + 8 h fault, 320 ticks, 3-min ticks). Full 48 h episodes cost ~80 min each on the board
  (about 1,600 model calls), so the board runs only this subset (human decision 2026-11-07, option A);
  per-fault accuracy comes from the full mock runs.

## 1. Get the code
```bash
cd ~/field-mind            # the repo on the QIDK laptop
git fetch origin && git switch breadth-tep && git pull
.venv/bin/python -m pip install scipy pandas pyreadr
```

## 2. Get the data (not in git; once)
**Cranfield** (free MathWorks account):
download https://www.mathworks.com/matlabcentral/fileexchange/50938 → `cvatutor-1.1.0.zip` into
`data/reference/cranfield/`, then
```bash
env -u PYTHONPATH .venv/bin/python -m data.cranfield.convert      # 16 episodes, checks sha256 + column order
```
**TEP** (public domain, no login, ~1.4 GB):
```bash
mkdir -p data/reference/tep && cd data/reference/tep
for p in 3031241:TEP_FaultFree_Training 3031240:TEP_FaultFree_Testing \
         3031242:TEP_Faulty_Training 3031243:TEP_Faulty_Testing; do
  curl -sSL --retry 3 -o "${p#*:}.RData" "https://dataverse.harvard.edu/api/access/datafile/${p%%:*}"
done
cd ../../..
env -u PYTHONPATH .venv/bin/python -m data.tep.convert            # checks sha256 + row order; 132 episodes
env -u PYTHONPATH .venv/bin/python -m data.tep.convert --board    # the 22 board episodes (16 h)
```
Check: `.venv/bin/python -m pytest tests/test_cranfield_data.py tests/test_cranfield_pack.py tests/test_tep_pack.py tests/test_asset_params.py -q`
(all pass; they skip themselves if a data set is missing).

## 3. Board up
`/board-up` as usual: the **v3** models — Llama 3.2 3B (Q4_0 pure, embq8) on the NPU lane :8080,
Gemma 3 1B on the CPU lane :8081; `-c 4096 -np 1 --cache-ram 0 -fit off -lv 4`. Same as the boiler
runs; nothing new on the board side.

## 4. Runs (in this order; the runner logs chip temperature and cools between episodes)
```bash
# Cranfield, multi-agent v3: dev then report (~2-3 h in all)
scripts/benchmark.sh cf_v3_dev $(ls data/episodes_cranfield_dev) --overlay configs/v3.yaml,configs/cranfield.yaml
scripts/benchmark.sh cf_v3_report $(ls data/episodes_cranfield) --overlay configs/v3.yaml,configs/cranfield.yaml

# Cranfield, single agent (the baseline every multi-agent number is compared with)
scripts/benchmark.sh cf_single_report $(ls data/episodes_cranfield) --arch single --overlay configs/cranfield.yaml

# TEP board subset, multi-agent v3 (~18 min an episode, ~7 h; can be split over days: the
# same test name resumes, finished episodes are skipped)
scripts/benchmark.sh tep_v3_board $(ls data/episodes_tep_board) --overlay configs/v3.yaml,configs/tep.yaml
```
Mock dry run first if in doubt: add `--backend mock` (results go to `results/benchmarks_mock/`).

## 5. Send back
`results/benchmarks/{cf_v3_dev,cf_v3_report,cf_single_report,tep_v3_board}/` (RESULTS.md, test.json,
per-episode summaries and gzipped runs, temperatures). If the USB power meter is in, log its reading
per test with the laptop time.

## Things to know
- The results header names the data correctly per plant (Cranfield: real rig data; TEP: simulated).
- TEP prompts never name the benchmark (tags are plain names, case ids `PF-xx`): Llama has read TEP
  papers. Do not paste TEP variable numbers or fault numbers into anything the model sees.
- One TEP verifier prompt in the board subset (fault 12, last tick) is ~1,400 tokens: over our 1,280
  budget, inside the 4,096 context. It is flagged in the run (`over_limit`), not cut (Phase 1 rule).
- `bench/benchmark.py`: `test_real_time_answers_get_the_tokens_of_their_own_envelope` is flaky on
  `main` too (timing; 2 of 3 failures on a clean copy). Not caused by this branch.
- Reports: `reports/b1_cranfield_data.md`, `reports/b1_cranfield_pack.md`, `reports/b2_tep_pack.md`.
