#!/usr/bin/env bash
# Tiger-Model FTC/PTC: full-train on zjh_train, then eval on zjh_test and/or Dai (FangDai).
#
# EXTERNAL_STEP: zjh | dai | both (default both)
#
# Usage:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/revision/b9/06_run_tiger_ftc_external.sh
#   EXTERNAL_STEP=zjh bash scripts/revision/b9/06_run_tiger_ftc_external.sh
#   EXTERNAL_STEP=dai SKIP_TRAIN=1 bash scripts/revision/b9/06_run_tiger_ftc_external.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=env_malig_b9.sh
source "$SCRIPT_DIR/env_malig_b9.sh"

EXTERNAL_STEP="${EXTERNAL_STEP:-both}"
EXPORT_DAI="${EXPORT_DAI:-$TIGER_ROOT/export_results/revision_${RUN_TAG}_fangdai}"
EXPORT_ZJH="${EXPORT_ZJH:-$TIGER_ROOT/export_results/revision_${RUN_TAG}_zjh_test}"

cd "$TIGER_ROOT"

pick_checkpoint() {
  SAVE_DIR="$(ls -td "${TIGER_ROOT}/modelsaved/Thyroid_PTC_vs_FTC_paper_"* 2>/dev/null | head -1 || true)"
  if [[ -z "$SAVE_DIR" ]]; then
    echo "WARN: no modelsaved/Thyroid_PTC_vs_FTC_paper_*" >&2
    return 1
  fi
  python new_code/pick_resnet_checkpoint.py "$SAVE_DIR" --criterion valid
}

export_zjh_test() {
  local pth="$1"
  mkdir -p "$EXPORT_ZJH"
  python new_code/test_model_export.py \
    --pth_path "$pth" \
    --test_json_path "$MANIFEST_ZJH_TEST_FTC" \
    --valid_json_path "$MANIFEST_ZJH_TRAIN_FTC" \
    --image_base_path "$FTC_PACK" \
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
    --output_dir "$EXPORT_ZJH"
}

export_dai() {
  local pth="$1"
  mkdir -p "$EXPORT_DAI"
  python new_code/test_model_export.py \
    --pth_path "$pth" \
    --test_json_path "$MANIFEST_DAI_FTC" \
    --valid_json_path "$MANIFEST_ZJH_TRAIN_FTC" \
    --image_base_path "$FTC_PACK" \
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
    --output_dir "$EXPORT_DAI"
}

if [[ "$EXTERNAL_STEP" == "zjh" || "$EXTERNAL_STEP" == "both" ]]; then
  echo ">>> Tiger full train + ZJH hold-out"
  PACK="$FTC_PACK" \
  TRAIN_JSON="$MANIFEST_ZJH_TRAIN_FTC" \
  VALID_JSON="$MANIFEST_ZJH_TRAIN_FTC" \
  TEST_JSON="$MANIFEST_ZJH_TEST_FTC" \
  EXPORT_DIR="$EXPORT_ZJH" \
  SKIP_TRAIN="${SKIP_TRAIN:-0}" \
  SKIP_DATA="${SKIP_DATA:-0}" \
  SKIP_EVAL="${SKIP_EVAL:-0}" \
  SEED="$CV_SEED" \
  NUM_EPOCHS="${NUM_EPOCHS:-${SPECIALIST_EPOCHS:-30}}" \
  bash new_code/run_ftcptc_paper_pipeline.sh
fi

if [[ "$EXTERNAL_STEP" == "dai" || "$EXTERNAL_STEP" == "both" ]]; then
  echo ">>> Tiger FangDai external (reuse checkpoint)"
  PTH="$(pick_checkpoint)" || exit 1
  export_dai "$PTH"
fi

echo "Done."
echo "  Dai:      $EXPORT_DAI"
echo "  ZJH test: $EXPORT_ZJH"
