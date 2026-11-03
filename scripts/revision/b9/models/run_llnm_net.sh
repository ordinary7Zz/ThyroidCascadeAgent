#!/usr/bin/env bash
# LLNM-Net: (1) full train + hold-out eval, (2) no Dai, (3) 5-fold OOF LNM
#
# Defaults: run step 1 + OOF; skip full train when my_run full_train exists (220/158);
# skip OOF when oof_n_images=220 cv_summary exists (SKIP_IF_LLNM_*=1).
#
# Optional skips (env):
#   SKIP_STEP1=1         — skip train + eval entirely (OOF only)
#   SKIP_FULL_TRAIN=1    — reuse best_model.pth (still eval unless SKIP_ZJH_EVAL=1)
#   SKIP_ZJH_EVAL=1      — skip evaluate.py
#   SKIP_OOF=1           — skip 5-fold OOF
#   SKIP_IF_LLNM_FULL=0  — force retrain
#   SKIP_IF_LLNM_OOF=0   — force OOF rerun (e.g. remove stale oof/ with old 3227-image cv)
#   SKIP_IF_CV_SUMMARY=1 — legacy alias: skip OOF if any cv_summary.json exists
set -euo pipefail
source "$(dirname "$0")/_lib.sh"

export EPOCHS="${EPOCHS:-${SPECIALIST_EPOCHS:-30}}"
export SKIP_OOF="${SKIP_OOF:-0}"
export SKIP_IF_LLNM_FULL="${SKIP_IF_LLNM_FULL:-1}"
export SKIP_IF_LLNM_OOF="${SKIP_IF_LLNM_OOF:-1}"

if [[ "${SKIP_STEP1:-0}" == "1" ]]; then
  run_llnm_full_zjh
elif [[ "${SKIP_IF_LLNM_FULL}" == "1" ]] && llnm_step1_ready; then
  echo ""
  echo ">>> [LLNM-Net/LNM] step 1 skipped (full_train + zjh_test_eval.json, my_run 220/158)"
  echo "    Force rerun: SKIP_IF_LLNM_FULL=0 or remove $(llnm_full_train_dir)/"
elif [[ "${SKIP_IF_LLNM_FULL}" == "1" ]] && llnm_full_train_ready; then
  echo ""
  echo ">>> [LLNM-Net/LNM] full train skipped (existing best_model + summary 220/158); running hold-out eval if needed"
  SKIP_FULL_TRAIN=1 run_llnm_full_zjh
else
  run_llnm_full_zjh
fi

if [[ "${SKIP_OOF}" == "1" ]]; then
  echo ""
  echo ">>> SKIP_OOF=1 — skipping LLNM 5-fold OOF"
else
  run_llnm_oof
fi

echo "Done. Outputs: $OUT_ROOT/llnm_net/"
echo "  full_train: $(llnm_full_train_dir)/ (zjh_test_eval.json)"
echo "  OOF:        $(llnm_oof_dir)/cv_summary.json"
