#!/usr/bin/env bash
# ThyroidXAgent malignant subtasks:
#   (1) DINO full train → zjh_test (+ FTC Dai)  [tab_malig_ext / tab_ftcptc_ext_dai interim]
#   (3) DINO 5-fold OOF                           [tab_malig_oof]
# Full Cascade stack external remains future work (see B9_ThyroidXAgent_补充实验计划.md).
#
# Defaults: run steps 1 + 3; skip step 1 if external_summary.json already exists (SKIP_IF_TX_FULL=1).
# Skip step 3 only when my_run OOF cv_summary exists (220 / 532 images; SKIP_IF_TX_OOF=1).
#
# DINO epochs: SPECIALIST_EPOCHS=30 default (per full-train run and per OOF fold).
set -euo pipefail
source "$(dirname "$0")/_lib.sh"

export EPOCHS="${EPOCHS:-${SPECIALIST_EPOCHS:-30}}"
export SKIP_TX_OOF="${SKIP_TX_OOF:-0}"
export SKIP_IF_TX_FULL="${SKIP_IF_TX_FULL:-1}"
export SKIP_IF_TX_OOF="${SKIP_IF_TX_OOF:-1}"

if [[ "${SKIP_TX_FULL:-0}" == "1" ]]; then
  echo ">>> SKIP_TX_FULL=1 — skipping DINO full external"
elif [[ "${SKIP_IF_TX_FULL}" == "1" ]] && tx_full_external_ready; then
  echo ">>> [ThyroidXAgent] full external skipped (existing summaries under $OUT_ROOT/thyroidxagent/*/full_external/)"
  echo "    Force rerun: SKIP_IF_TX_FULL=0 or remove external_summary.json"
else
  run_txagent_full_external
fi

if [[ "${SKIP_TX_OOF}" == "1" ]]; then
  echo ">>> SKIP_TX_OOF=1 — skipping DINO OOF"
elif [[ "${SKIP_IF_TX_OOF}" == "1" ]] && tx_oof_cv_ready; then
  echo ">>> [ThyroidXAgent] 5-fold OOF skipped (existing my_run cv_summary: LNM n=220, FTC n=532)"
  echo "    Force rerun: SKIP_IF_TX_OOF=0 or remove $DINO_ROOT/Malignant_Cls_Model/b9/runs/revision_${RUN_TAG}/*_cv/"
else
  run_txagent_oof_both
fi

echo "Done."
echo "  External: $OUT_ROOT/thyroidxagent/*/full_external/external_summary.json"
echo "  OOF:      $DINO_ROOT/Malignant_Cls_Model/b9/runs/revision_${RUN_TAG}/"
