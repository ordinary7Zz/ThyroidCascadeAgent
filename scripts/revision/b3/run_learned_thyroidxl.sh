#!/usr/bin/env bash
# ThyroidXL：valid intermediate (n=100) fit → test infer → eval。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
PY="${PY:-python3}"
CFG="config/b3/thyroidxl.yaml"
VAL_INT="output/validation/_parts/thyroidxl/intermediate"
TEST_INT="output/ThyroidXL/pipeline_run/intermediate"
OUT="output/ablation/b3/thyroidxl/learned"

echo "== fit learned (val n=100) =="
"$PY" scripts/revision/b3/fit_learned_router.py --config "$CFG" --intermediate "$VAL_INT"

echo "== run learned on test =="
"$PY" scripts/revision/b3/run_learned_b3.py \
  --config "$CFG" \
  --shared-intermediate "$TEST_INT" \
  --output-dir "$OUT" \
  --force-phase3 \
  --device cpu

echo "== eval =="
"$PY" scripts/revision/b3/eval_merged_b3_cohort.py \
  --config "$CFG" \
  --root "$(dirname "$OUT")" \
  --modes learned

echo "Done: $OUT/b3_metrics.json"
