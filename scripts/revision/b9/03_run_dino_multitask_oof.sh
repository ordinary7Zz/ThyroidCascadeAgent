#!/usr/bin/env bash
# ThyroidXAgent DINO multitask 5-fold OOF (LNM + FTC/PTC), separate from generic CNN baselines.
#
# Usage:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/revision/b9/03_run_dino_multitask_oof.sh
#   TASKS=ftcptc MAX_FOLDS=1 EPOCHS=2 bash scripts/revision/b9/03_run_dino_multitask_oof.sh  # smoke
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=env_malig_b9.sh
source "$SCRIPT_DIR/env_malig_b9.sh"

TASKS="${TASKS:-lnm ftcptc}"
EPOCHS="${EPOCHS:-${SPECIALIST_EPOCHS:-30}}"
MAX_FOLDS="${MAX_FOLDS:-}"
DRY_RUN="${DRY_RUN:-0}"

cd "$DINO_ROOT"

run_task() {
  local task="$1"
  local packed manifest out_dir
  case "$task" in
    lnm)
      packed="$LNM_PACK"
      manifest="$MANIFEST_ZJH_TRAIN_LNM"
      out_dir="Malignant_Cls_Model/b9/runs/revision_${RUN_TAG}/lnm_cv"
      ;;
    ftcptc)
      packed="$FTC_PACK"
      manifest="$MANIFEST_ZJH_TRAIN_FTC"
      out_dir="Malignant_Cls_Model/b9/runs/revision_${RUN_TAG}/ftcptc_cv"
      ;;
    *)
      echo "Unknown task $task" >&2
      return 1
      ;;
  esac

  local -a extra=()
  [[ -n "$MAX_FOLDS" ]] && extra+=(--max_folds "$MAX_FOLDS")
  [[ "$DRY_RUN" == "1" ]] && extra+=(--dry_run)

  echo ">>> DINO CV task=$task manifest=$manifest"
  CUDA_VISIBLE_DEVICES="$CUDA_DEVICE" "$PYTHON" Malignant_Cls_Model/b9/run_patient_cv.py \
    --task "$task" \
    --packed_root "$packed" \
    --train_manifest "$manifest" \
    --output_dir "$out_dir" \
    --n_splits "$N_SPLITS" \
    --cv_seed "$CV_SEED" \
    --epochs "$EPOCHS" \
    --cuda_device 0 \
    "${extra[@]}"
}

for task in $TASKS; do
  run_task "$task"
done

echo "DINO OOF outputs: $DINO_ROOT/Malignant_Cls_Model/b9/runs/revision_${RUN_TAG}/"
