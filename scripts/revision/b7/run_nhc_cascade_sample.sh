#!/usr/bin/env bash
# NHC 示例数据 + Cascade 真推理（需 GPU 与 thyroid_infer 环境）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

if [[ -z "${CONDA_DEFAULT_ENV:-}" ]] || [[ "$CONDA_DEFAULT_ENV" != *thyroid_infer* ]]; then
  echo "请先: source ~/miniconda3/bin/activate && conda activate /mnt/wangbd8/workspace/envs/thyroid_infer"
  exit 1
fi

PREP="${PREP:-output/b7/nhc_prepared_smoke}"
if [[ ! -f "$PREP/labels.json" ]]; then
  echo "缺少 $PREP，先运行 run_nhc_prepare.py"
  exit 1
fi

CFG="${CFG:-config/revision/nhc_prepared_sample.yaml}"
echo "== Cascade on prepared sample (max_images in yaml) =="
python run_pipeline.py --config "$CFG"

echo "== B7 analysis =="
python scripts/revision/b8/backfill_results_metadata.py \
  --output-dir output/b7/nhc_cascade_sample \
  --label-file "$PREP/labels.json" || true

python scripts/revision/b7/run_b7_analysis.py --re-evaluate \
  --output-dir output/b7/nhc_cascade_sample \
  --label-file "$PREP/labels.json" \
  --center-manifest "$PREP/center_manifest.json" \
  --gt-gland-mask-dir "$PREP/gland_masks" \
  --out output/b7/nhc_smoke_report

echo "Done: output/b7/nhc_cascade_sample/results.json"
