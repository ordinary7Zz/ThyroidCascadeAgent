#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/_lib.sh"

run_baseline_full_zjh_both_tasks ultrafedfm
run_baseline_dai_ftc ultrafedfm
run_baseline_oof_both_tasks ultrafedfm

echo "Done. Outputs: $OUT_ROOT/ultrafedfm/"
