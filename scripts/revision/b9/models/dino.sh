#!/usr/bin/env bash
# ThyroidXAgent DINO multitask: Step 3 = 5-fold OOF. Steps 1–2 (full train → zjh_test + Dai)
# are not wired in b9/ yet — run after run_full_external is added, or train manually (README).
#
# Usage:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/revision/b9/models/dino.sh
#   SKIP_FULL=1 bash scripts/revision/b9/models/dino.sh   # OOF only (default if full missing)
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../env_malig_b9.sh
source "$SCRIPT_DIR/../env_malig_b9.sh"

TASKS="${TASKS:-lnm ftcptc}"
EPOCHS="${EPOCHS:-${SPECIALIST_EPOCHS:-30}}"
MAX_FOLDS="${MAX_FOLDS:-}"
DRY_RUN="${DRY_RUN:-0}"
SKIP_FULL="${SKIP_FULL:-0}"

FULL_SCRIPT="$SCRIPT_DIR/../08_run_dino_full_external.sh"
if [[ "$SKIP_FULL" != "1" && -x "$FULL_SCRIPT" ]]; then
  OUT_ROOT="${OUT_ROOT:-$REPO_ROOT/docs/revision/b9/runs/models_${RUN_TAG}}" \
    bash "$FULL_SCRIPT"
elif [[ "$SKIP_FULL" != "1" ]]; then
  echo "WARN: $FULL_SCRIPT not found — skipping Steps 1–2 (set SKIP_FULL=1 to silence)" >&2
else
  echo ">>> [DINO] Steps 1–2 skipped (SKIP_FULL=1)."
fi

cd "$DINO_ROOT"

run_cv() {
  local task="$1"
  local packed manifest roots out_dir
  case "$task" in
    lnm)
      packed="$LNM_PACK"
      manifest="$MANIFEST_LNM_TRAIN"
      roots="$IMAGE_ROOTS_LNM"
      out_dir="Malignant_Cls_Model/b9/runs/revision_${RUN_TAG}/lnm_cv"
      ;;
    ftcptc)
      packed="$FTC_PACK"
      manifest="$MANIFEST_FTC_TRAIN"
      roots="$IMAGE_ROOTS_FTC"
      out_dir="Malignant_Cls_Model/b9/runs/revision_${RUN_TAG}/ftcptc_cv"
      ;;
    *) echo "Unknown task $task" >&2; return 1 ;;
  esac

  local -a extra=()
  [[ -n "$MAX_FOLDS" ]] && extra+=(--max_folds "$MAX_FOLDS")
  [[ "$DRY_RUN" == "1" ]] && extra+=(--dry_run)

  echo ">>> [DINO/$task] Step 3: 5-fold OOF (cv_cluster=$B9_CV_CLUSTER_PY)"
  CUDA_VISIBLE_DEVICES="$CUDA_DEVICE" "$PYTHON" Malignant_Cls_Model/b9/run_patient_cv.py \
    --task "$task" \
    --packed_root "$packed" \
    --train_manifest "$manifest" \
    --image_roots_json "$roots" \
    --output_dir "$out_dir" \
    --n_splits "$N_SPLITS" \
    --cv_seed "$CV_SEED" \
    --cv_cluster "$B9_CV_CLUSTER_PY" \
    --epochs "$EPOCHS" \
    --cuda_device 0 \
    "${extra[@]}"
}

for task in $TASKS; do
  run_cv "$task"
done

echo "DINO OOF: $DINO_ROOT/Malignant_Cls_Model/b9/runs/revision_${RUN_TAG}/"
