#!/usr/bin/env bash
# ThyroidXAgent: (1)(2) full stack external TBD, (3) DINO 5-fold OOF both tasks
set -euo pipefail
source "$(dirname "$0")/_lib.sh"

run_txagent_full_note
run_txagent_oof_both

echo "Done. DINO OOF: $DINO_ROOT/Malignant_Cls_Model/b9/runs/revision_${RUN_TAG}/"
