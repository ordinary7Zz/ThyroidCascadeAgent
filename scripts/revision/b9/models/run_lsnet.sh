#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/_lib.sh"

run_baseline_full_zjh_both_tasks lsnet
run_baseline_dai_ftc lsnet
run_baseline_oof_both_tasks lsnet

echo "Done. Outputs: $OUT_ROOT/lsnet/"
