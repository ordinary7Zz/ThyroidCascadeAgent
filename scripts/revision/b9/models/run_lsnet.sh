#!/usr/bin/env bash
# LSNet LNM + FTC/PTC: (1) full+ZJH, (2) Dai, (3) 5-fold OOF
# Train hparams: Classification_Models/lsnet/scripts/mytrain_LNMCN01.sh &
#   mytrain_FTCPTC.sh → --epochs 10, batch-size 32
set -euo pipefail
source "$(dirname "$0")/_lib.sh"
export BASELINE_EPOCHS="${BASELINE_EPOCHS:-10}"

run_baseline_full_zjh_both_tasks lsnet
run_baseline_dai_ftc lsnet
run_baseline_oof_both_tasks lsnet

echo "Done. Outputs: $OUT_ROOT/lsnet/"
