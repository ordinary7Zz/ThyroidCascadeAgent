#!/usr/bin/env bash
# CNN/ViT baseline 5-fold OOF (RepViT, LSNet, UltraFedFM). Requires 01_export_shared_folds.sh.
#
# Usage:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/revision/b9/02_run_baselines_oof.sh
#   MODELS="repvit lsnet" TASKS=ftcptc bash scripts/revision/b9/02_run_baselines_oof.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=env_malig_b9.sh
source "$SCRIPT_DIR/env_malig_b9.sh"

if [[ ! -f "$SHARED_LNM/fold_manifest.json" || ! -f "$SHARED_FTC/fold_manifest.json" ]]; then
  echo "Missing shared folds. Run: bash scripts/revision/b9/01_export_shared_folds.sh" >&2
  exit 1
fi

export SHARED_LNM SHARED_FTC
export CUDA_DEVICE
export RUNS_ROOT="${RUNS_ROOT:-$B9_OOF_ROOT/runs/revision_$RUN_TAG}"
export MODELS="${MODELS:-repvit lsnet ultrafedfm}"
export TASKS="${TASKS:-lnm ftcptc}"
export PHASE="${PHASE:-all}"
export SKIP_IF_CV_SUMMARY="${SKIP_IF_CV_SUMMARY:-0}"

cd "$B9_OOF_ROOT"
bash scripts/run_all_baselines_cv.sh

echo "Summaries under: $RUNS_ROOT/<model>/<task>/cv_summary.json"
