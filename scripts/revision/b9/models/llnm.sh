#!/usr/bin/env bash
# LLNM-Net (LNM only): (1) full train + zjh_test, (2) no Dai, (3) 5-fold OOF.
#
# Usage:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/revision/b9/models/llnm.sh
#   bash scripts/revision/b9/models/llnm.sh --smoke
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../env_malig_b9.sh
source "$SCRIPT_DIR/../env_malig_b9.sh"

SMOKE=0
for arg in "$@"; do
  [[ "$arg" == "--smoke" ]] && SMOKE=1
done

EPOCHS="${EPOCHS:-50}"
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

echo ">>> [LLNM] Step 1: full train on zjh_train + monitor zjh_test"
"$PYTHON" new_code/train.py \
  --train_json "$MANIFEST_ZJH_TRAIN_LNM" \
  --test_json "$MANIFEST_ZJH_TEST_LNM" \
  --image_roots_json "$LNM_PACK/image_roots.json" \
  --output_dir "$OUT_FT" \
  --batch_size "$BATCH_SIZE" \
  --epochs "$EPOCHS" \
  --learning_rate "$LR" \
  --device "$DEVICE"

echo ">>> [LLNM] Step 1 cont.: eval zjh_test (hold-out)"
"$PYTHON" new_code/evaluate.py \
  --test_json "$MANIFEST_ZJH_TEST_LNM" \
  --image_roots_json "$LNM_PACK/image_roots.json" \
  --weights "$OUT_FT/best_model.pth" \
  --norm_stats "$OUT_FT/train_norm_stats.pkl" \
  --output "$OUT_FT/zjh_test_eval.json" \
  --device "$DEVICE"

echo ">>> [LLNM] Step 2: Dai — N/A (LNM task)"

echo ">>> [LLNM] Step 3: 5-fold patient OOF"
"$PYTHON" new_code/run_b9_patient_cv.py \
  --train_manifest "$MANIFEST_ZJH_TRAIN_LNM" \
  --image_roots_json "$LNM_PACK/image_roots.json" \
  --output_dir "$OUT_CV" \
  --n_splits "$N_SPLITS" \
  --batch_size "$BATCH_SIZE" \
  --epochs "$EPOCHS" \
  --learning_rate "$LR" \
  --device "$DEVICE"

echo "Done."
echo "  ZJH test:  $OUT_FT/zjh_test_eval.json"
echo "  OOF:       $OUT_CV/cv_summary.json"
