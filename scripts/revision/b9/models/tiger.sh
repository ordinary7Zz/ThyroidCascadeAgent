#!/usr/bin/env bash
# Tiger FTC/PTC: (1) full train + hold-out test, (2) Dai, (3) 5-fold OOF.
#
# Usage:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/revision/b9/models/tiger.sh
#   SKIP_TRAIN=1 bash scripts/revision/b9/models/tiger.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../env_malig_b9.sh
source "$SCRIPT_DIR/../env_malig_b9.sh"

NUM_EPOCHS="${NUM_EPOCHS:-${SPECIALIST_EPOCHS:-30}}"
EXPORT_DAI="${EXPORT_DAI:-$TIGER_ROOT/export_results/revision_${RUN_TAG}_fangdai}"
EXPORT_HOLDOUT="${EXPORT_HOLDOUT:-$TIGER_ROOT/export_results/revision_${RUN_TAG}_ftc_holdout}"
OUT_CV="$TIGER_ROOT/new_code/runs/revision_${RUN_TAG}_ftc_cv"

cd "$TIGER_ROOT"

echo ">>> [Tiger] Step 1–2: full train on filtered train → Dai external (pipeline)"
PACK="$FTC_DAI_IMAGE_BASE" \
BASE_DIR="$FTC_IMAGE_BASE" \
TRAIN_JSON="$MANIFEST_FTC_TRAIN" \
VALID_JSON="$MANIFEST_FTC_TRAIN" \
TEST_JSON="$MANIFEST_DAI_FTC" \
EXPORT_DIR="$EXPORT_DAI" \
SKIP_TRAIN="${SKIP_TRAIN:-0}" \
SKIP_DATA="${SKIP_DATA:-0}" \
SKIP_EVAL="${SKIP_EVAL:-0}" \
SEED="$CV_SEED" \
NUM_EPOCHS="$NUM_EPOCHS" \
bash new_code/run_ftcptc_paper_pipeline.sh

echo ">>> [Tiger] Step 1 cont.: eval filtered hold-out test"
SAVE_DIR="$(ls -td "${TIGER_ROOT}/modelsaved/Thyroid_PTC_vs_FTC_paper_"* 2>/dev/null | head -1 || true)"
if [[ -z "$SAVE_DIR" ]]; then
  echo "ERROR: no modelsaved/Thyroid_PTC_vs_FTC_paper_* after train" >&2
  exit 1
fi
PTH="$(python new_code/pick_resnet_checkpoint.py "$SAVE_DIR" --criterion valid)"

mkdir -p "$EXPORT_HOLDOUT"
python new_code/test_model_export.py \
  --pth_path "$PTH" \
  --test_json_path "$MANIFEST_FTC_TEST" \
  --valid_json_path "$MANIFEST_FTC_TRAIN" \
  --image_base_path "$FTC_IMAGE_BASE" \
  --filename_key filename \
  --label_key FTCPTC \
  --ignore_labels -1 \
  --label_map "0:0,1:1" \
  --threshold_metric youden \
  --batch_size "${BATCH_SIZE:-8}" \
  --num_workers "${NUM_WORKERS:-4}" \
  --bootstrap_samples 1000 \
  --ci_level 0.95 \
  --seed "$CV_SEED" \
  --require_exists \
  --output_dir "$EXPORT_HOLDOUT"

echo ">>> [Tiger] Step 3: 5-fold OOF on filtered train (cv_cluster=$B9_CV_CLUSTER_PY)"
CUDA_VISIBLE_DEVICES="$CUDA_DEVICE" \
  JSON_PATH="$MANIFEST_FTC_TRAIN" \
  BASE_DIR="$FTC_IMAGE_BASE" \
  MASK_DIR="$FTC_MASK_DIR" \
  CV_CLUSTER="$B9_CV_CLUSTER_PY" \
  OUTPUT_DIR="$OUT_CV" \
  N_SPLITS="$N_SPLITS" \
  NUM_EPOCHS="$NUM_EPOCHS" \
  SEED="$CV_SEED" \
  bash new_code/run_b9_paper_cv.sh

echo "Done."
echo "  Dai:       $EXPORT_DAI"
echo "  Hold-out:  $EXPORT_HOLDOUT"
echo "  OOF:       $OUT_CV/cv_summary.json"
