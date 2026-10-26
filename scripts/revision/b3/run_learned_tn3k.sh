#!/usr/bin/env bash
# TN3K：在 OpenThyroid valid intermediate 上 fit learned router，在 test intermediate 上跑 B3 learned。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
PY="${PY:-python3}"
CFG="config/revision/b3/tn3k.yaml"
VAL_INT="output/validation/_parts/tn3k/intermediate"
TEST_INT="output/TN3K/pipeline_run/intermediate"
OUT="output/ablation/b3/tn3k/learned"

echo "== fit learned (val n=100) =="
"$PY" scripts/revision/b3/fit_learned_router.py \
  --config "$CFG" \
  --intermediate "$VAL_INT"

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
