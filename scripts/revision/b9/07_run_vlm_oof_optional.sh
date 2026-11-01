#!/usr/bin/env bash
# Optional: MedGemma / Qwen3 five-fold OOF (not in tab_malig_oof letter table).
# Requires 01_export_shared_folds.sh (VLM JSON under each fold_*).
#
# Usage:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/revision/b9/07_run_vlm_oof_optional.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=env_malig_b9.sh
source "$SCRIPT_DIR/env_malig_b9.sh"

export SHARED_LNM SHARED_FTC CUDA_DEVICE
export RUNS_ROOT="${RUNS_ROOT:-$B9_OOF_ROOT/runs/revision_${RUN_TAG}_vlm}"

cd "$B9_OOF_ROOT"
bash scripts/run_medgemma_cv.sh
bash scripts/run_qwen3_cv.sh

echo "VLM OOF under: $RUNS_ROOT"
