#!/usr/bin/env bash
# Export image-level 5-fold splits (seed=42) for RepViT/LSNet/UltraFedFM/MedGemma/Qwen OOF.
#
# Prerequisite: bash scripts/revision/b9/build_my_run_manifests.sh
#
# Usage:
#   bash scripts/revision/b9/01_export_shared_folds.sh
#   TASKS=lnm bash scripts/revision/b9/01_export_shared_folds.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=env_malig_b9.sh
source "$SCRIPT_DIR/env_malig_b9.sh"

TASKS="${TASKS:-lnm ftcptc}"
EXPORT="$REPO_ROOT/scripts/revision/b9/export_folds.py"

for task in $TASKS; do
  case "$task" in
    lnm)
      out="$SHARED_LNM"
      manifest="$MANIFEST_LNM_TRAIN"
      packed="$LNM_PACK"
      roots="$IMAGE_ROOTS_LNM"
      ;;
    ftcptc)
      out="$SHARED_FTC"
      manifest="$MANIFEST_FTC_TRAIN"
      packed="$FTC_PACK"
      roots="$IMAGE_ROOTS_FTC"
      ;;
    *)
      echo "Unknown task: $task" >&2
      exit 1
      ;;
  esac
  echo ">>> export_folds task=$task cv_cluster=$B9_CV_CLUSTER_PY manifest=$manifest -> $out"
  "$PYTHON" "$EXPORT" \
    --task "$task" \
    --packed_root "$packed" \
    --train_manifest "$manifest" \
    --image_roots_json "$roots" \
    --output_dir "$out" \
    --n_splits "$N_SPLITS" \
    --cv_seed "$CV_SEED" \
    --cv_cluster "$B9_CV_CLUSTER_PY"
done

echo "Done. Fold roots:"
echo "  LNM:    $SHARED_LNM/fold_manifest.json"
echo "  FTCPTC: $SHARED_FTC/fold_manifest.json"
