#!/usr/bin/env bash
# UltraFedFM LNM + FTC/PTC: (1) full+ZJH, (2) Dai, (3) 5-fold OOF
# Train hparams: UltraFedFM/scripts/my_class_pretrain_LNMCN01.sh &
#   my_class_pretrain_FTCPTC.sh → --epochs 10, batch_size 32
set -euo pipefail
source "$(dirname "$0")/_lib.sh"
export BASELINE_EPOCHS="${BASELINE_EPOCHS:-10}"

run_baseline_full_zjh_both_tasks ultrafedfm
run_baseline_dai_ftc ultrafedfm
run_baseline_oof_both_tasks ultrafedfm

echo "Done. Outputs: $OUT_ROOT/ultrafedfm/"
