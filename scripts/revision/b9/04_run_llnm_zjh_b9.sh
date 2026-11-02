#!/usr/bin/env bash
# LLNM-Net: 5-fold OOF + full train + hold-out test (LymphUs predmask, my_run.md).
#
# Usage:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/revision/b9/04_run_llnm_zjh_b9.sh
#   --smoke  # 2 folds, 1 epoch
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=env_malig_b9.sh
source "$SCRIPT_DIR/env_malig_b9.sh"

SMOKE=0
for arg in "$@"; do
  [[ "$arg" == "--smoke" ]] && SMOKE=1
done

EPOCHS="${EPOCHS:-${SPECIALIST_EPOCHS:-30}}"
N_SPLITS="${N_SPLITS:-5}"
BATCH_SIZE="${BATCH_SIZE:-4}"
LR="${LEARNING_RATE:-1e-5}"
DEVICE="${DEVICE:-cuda}"

if [[ "$SMOKE" == "1" ]]; then
  N_SPLITS=2
  EPOCHS=1
  RUN_TAG="${RUN_TAG}_smoke"
fi

OUT_CV="$LLNM_ROOT/new_code/runs/revision_${RUN_TAG}_lnm_cv"
OUT_FT="$LLNM_ROOT/new_code/runs/revision_${RUN_TAG}_lnm_fulltrain"

cd "$LLNM_ROOT"

echo ">>> LLNM 5-fold CV (cluster=$LLNM_CLUSTER_KEY manifest=$MANIFEST_LNM_TRAIN)"
"$PYTHON" new_code/run_b9_patient_cv.py \
  --train_manifest "$MANIFEST_LNM_TRAIN" \
  --image_roots_json "$IMAGE_ROOTS_LNM" \
  --output_dir "$OUT_CV" \
  --n_splits "$N_SPLITS" \
  --cluster_key "$LLNM_CLUSTER_KEY" \
  --batch_size "$BATCH_SIZE" \
  --epochs "$EPOCHS" \
  --learning_rate "$LR" \
  --device "$DEVICE"

echo ">>> LLNM full train (monitor hold-out test during training)"
"$PYTHON" new_code/train.py \
  --train_json "$MANIFEST_LNM_TRAIN" \
  --test_json "$MANIFEST_LNM_TEST" \
  --image_roots_json "$IMAGE_ROOTS_LNM" \
  --output_dir "$OUT_FT" \
  --batch_size "$BATCH_SIZE" \
  --epochs "$EPOCHS" \
  --learning_rate "$LR" \
  --device "$DEVICE"

echo ">>> LLNM hold-out test eval"
"$PYTHON" new_code/evaluate.py \
  --test_json "$MANIFEST_LNM_TEST" \
  --image_roots_json "$IMAGE_ROOTS_LNM" \
  --weights "$OUT_FT/best_model.pth" \
  --norm_stats "$OUT_FT/train_norm_stats.pkl" \
  --output "$OUT_FT/holdout_test_eval.json" \
  --device "$DEVICE"

echo "Done."
echo "  OOF:       $OUT_CV/cv_summary.json"
echo "  Hold-out:  $OUT_FT/holdout_test_eval.json"
