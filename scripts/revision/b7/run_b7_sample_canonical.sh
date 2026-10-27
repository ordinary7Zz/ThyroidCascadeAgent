#!/usr/bin/env bash
# 示例 NHC（10 图）canonical 结构样板：prepare → Cascade(10) → B7 → 描述表 → CSV
# 需: conda activate .../thyroid_infer
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

PREP="${PREP:-output/b7/nhc_prepared_smoke}"
RAW="${RAW:-/mnt/wangbd8/workspace/ThyroidAgent/my_Thyroid_Infer/datasets/甲状腺私有数据/新建文件夹}"
CASCADE_OUT="${CASCADE_OUT:-output/b7/nhc_cascade_sample}"
B7_OUT="${B7_OUT:-output/b7/nhc_sample_canonical}"
DESC_OUT="${DESC_OUT:-output/b7/descriptive_canonical}"

PYTHON="${PYTHON:-python3}"

echo "== 1) prepare (skip if labels exist) =="
if [[ ! -f "$PREP/labels.json" ]]; then
  PYTHONPATH=. "$PYTHON" scripts/revision/b7/run_nhc_prepare.py \
    --input_dir "$RAW" --output_dir "$PREP" --skip_roi
fi

echo "== 2) Cascade 10 images =="
if [[ "${FORCE_REFRESH:-1}" == "1" ]]; then
  echo "  (FORCE_REFRESH=1: 清除 intermediate，避免曾用 max_images 较小时残留缓存)"
  rm -rf "$CASCADE_OUT/intermediate" "$CASCADE_OUT/results.json" \
    "$CASCADE_OUT"/per_image_*.jsonl "$CASCADE_OUT/metrics.json" 2>/dev/null || true
fi
"$PYTHON" run_pipeline.py --config config/revision/nhc_prepared_sample.yaml

echo "== 3) gland pred placeholder (Cascade 不产腺体 mask；示例用 GT 拷贝以验证 B7 列结构) =="
GLAND_PRED="$CASCADE_OUT/gland_pred_for_b7"
rm -rf "$GLAND_PRED"
cp -a "$PREP/gland_masks" "$GLAND_PRED"

echo "== 4) backfill center_id / uncertainty =="
PYTHONPATH=. "$PYTHON" scripts/revision/b8/backfill_results_metadata.py \
  --output-dir "$CASCADE_OUT" \
  --label-file "$PREP/labels.json" || true

echo "== 5) B7 analysis =="
PYTHONPATH=. "$PYTHON" scripts/revision/b7/run_b7_analysis.py \
  --re-evaluate \
  --output-dir "$CASCADE_OUT" \
  --gt-mask-dir "$PREP/nodule_masks" \
  --label-file "$PREP/labels.json" \
  --center-manifest "$PREP/center_manifest.json" \
  --gt-gland-mask-dir "$PREP/gland_masks" \
  --gland-pred-mask-dir "$GLAND_PRED" \
  --compute-gland \
  --out "$B7_OUT"

echo "== 6) descriptive + CSV =="
PYTHONPATH=. "$PYTHON" scripts/revision/b7/build_nhc_center_table.py \
  --label-file "$PREP/labels.json" \
  --center-stats "$PREP/center_stats.json" \
  --out "$DESC_OUT"
PYTHONPATH=. "$PYTHON" scripts/revision/b7/export_b7_tables.py \
  --report "$B7_OUT/b7_report.json" \
  --out-dir "$B7_OUT/csv"

echo "Done."
echo "  b7_report: $B7_OUT/b7_report.json"
echo "  descriptive: $DESC_OUT/nhc_center_descriptive.csv"
echo "  tables: $B7_OUT/csv/"
