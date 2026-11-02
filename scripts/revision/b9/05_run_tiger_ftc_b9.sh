#!/usr/bin/env bash
# Tiger-Model FTC/PTC: 5-fold OOF on filtered train manifest (image-level CV).
#
# Usage:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/revision/b9/05_run_tiger_ftc_b9.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=env_malig_b9.sh
source "$SCRIPT_DIR/env_malig_b9.sh"

NUM_EPOCHS="${NUM_EPOCHS:-${SPECIALIST_EPOCHS:-30}}"
OUT="$TIGER_ROOT/new_code/runs/revision_${RUN_TAG}_ftc_cv"

cd "$TIGER_ROOT"

JSON_PATH="${JSON_PATH:-$MANIFEST_FTC_TRAIN}"
BASE_DIR="${BASE_DIR:-$FTC_IMAGE_BASE}"
MASK_DIR="${MASK_DIR:-$FTC_MASK_DIR}"

echo ">>> Tiger FTC 5-fold CV json=$JSON_PATH base=$BASE_DIR cv_cluster=$B9_CV_CLUSTER_PY"
CUDA_VISIBLE_DEVICES="$CUDA_DEVICE" \
  JSON_PATH="$JSON_PATH" \
  BASE_DIR="$BASE_DIR" \
  MASK_DIR="$MASK_DIR" \
  CV_CLUSTER="$B9_CV_CLUSTER_PY" \
  OUTPUT_DIR="$OUT" \
  N_SPLITS="$N_SPLITS" \
  NUM_EPOCHS="$NUM_EPOCHS" \
  SEED="$CV_SEED" \
  bash new_code/run_b9_paper_cv.sh

echo "Done: $OUT/cv_summary.json"
