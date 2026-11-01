#!/usr/bin/env bash
# RepViT LNM + FTC/PTC: (1) full+ZJH, (2) Dai, (3) 5-fold OOF
# Train hparams: Classification_Models/RepViT/scripts/mytrain_LNMCN01.sh &
#   mytrain_FTCPTC.sh → --epochs 10, batch-size 16
set -euo pipefail
# shellcheck source=_lib.sh
source "$(dirname "$0")/_lib.sh"
export BASELINE_EPOCHS="${BASELINE_EPOCHS:-10}"

run_baseline_full_zjh_both_tasks repvit
run_baseline_dai_ftc repvit
run_baseline_oof_both_tasks repvit

echo "Done. Outputs: $OUT_ROOT/repvit/"
