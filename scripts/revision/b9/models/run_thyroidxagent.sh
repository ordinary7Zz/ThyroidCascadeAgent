#!/usr/bin/env bash
# ThyroidXAgent malignant subtasks:
#   (1) DINO full train → zjh_test (+ FTC Dai)  [tab_malig_ext / tab_ftcptc_ext_dai interim]
#   (3) DINO 5-fold OOF                           [tab_malig_oof]
# Full Cascade stack external remains future work (see B9_ThyroidXAgent_补充实验计划.md).
#
# DINO epochs: SPECIALIST_EPOCHS=30 default (per full-train run and per OOF fold).
set -euo pipefail
source "$(dirname "$0")/_lib.sh"

export EPOCHS="${EPOCHS:-${SPECIALIST_EPOCHS:-30}}"

if [[ "${SKIP_TX_FULL:-0}" != "1" ]]; then
  run_txagent_full_external
else
  echo ">>> SKIP_TX_FULL=1 — skipping DINO full external"
fi

if [[ "${SKIP_TX_OOF:-1}" != "0" ]]; then
  if [[ "${SKIP_TX_OOF:-1}" == "1" ]]; then
    echo ">>> SKIP_TX_OOF=1 — skipping DINO OOF (default when only refreshing external)"
  fi
else
  run_txagent_oof_both
fi

echo "Done."
echo "  External: $OUT_ROOT/thyroidxagent/*/full_external/external_summary.json"
echo "  OOF:      $DINO_ROOT/Malignant_Cls_Model/b9/runs/revision_${RUN_TAG}/"
