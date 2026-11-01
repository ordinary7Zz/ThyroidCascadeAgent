#!/usr/bin/env bash
# Tiger-Model FTC/PTC: 5-fold OOF on zjh_train (packed manifest).
#
# Usage:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/revision/b9/05_run_tiger_ftc_b9.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=env_malig_b9.sh
source "$SCRIPT_DIR/env_malig_b9.sh"

NUM_EPOCHS="${NUM_EPOCHS:-50}"
OUT="$TIGER_ROOT/new_code/runs/revision_${RUN_TAG}_ftc_cv"

cd "$TIGER_ROOT"

JSON_PATH="${JSON_PATH:-$MANIFEST_ZJH_TRAIN_FTC}"
PACK="${PACK:-$FTC_PACK}"

echo ">>> Tiger FTC 5-fold CV json=$JSON_PATH"
CUDA_VISIBLE_DEVICES="$CUDA_DEVICE" \
  JSON_PATH="$JSON_PATH" \
  BASE_DIR="$PACK" \
  OUTPUT_DIR="$OUT" \
  N_SPLITS="$N_SPLITS" \
  NUM_EPOCHS="$NUM_EPOCHS" \
  SEED="$CV_SEED" \
  bash new_code/run_b9_paper_cv.sh

echo "Done: $OUT/cv_summary.json"
