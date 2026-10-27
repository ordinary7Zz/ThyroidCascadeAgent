#!/usr/bin/env bash
# B7：NHC 一条龙（backfill center_id → 分析 → 导出 CSV）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
PYTHON="${PYTHON:-python3}"
OUT="${OUT:-output/revision/nhc_no_llm_primary}"
CFG="${CFG:-config/revision/nhc_no_llm_primary.yaml}"

echo "== B7: backfill center_id (optional manifest via --center-manifest) =="
"$PYTHON" scripts/revision/b8/backfill_results_metadata.py \
  --output-dir "$OUT" \
  --config "$CFG" \
  ${CENTER_MANIFEST:+--center-manifest "$CENTER_MANIFEST"}

echo "== B7: run_b7_analysis =="
"$PYTHON" scripts/revision/b7/run_b7_analysis.py \
  --output-dir "$OUT" \
  --config "$CFG" \
  --re-evaluate \
  ${G3_CSV:+--g3-csv "$G3_CSV"} \
  ${COMPUTE_GLAND:+--compute-gland} \
  "$@"

echo "== B7: export CSV =="
"$PYTHON" scripts/revision/b7/export_b7_tables.py

echo "Done. See output/b7/nhc/"
