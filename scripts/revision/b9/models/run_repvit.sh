#!/usr/bin/env bash
# RepViT: (1) full+ZJH LNM & FTC, (2) Dai FTC, (3) 5-fold OOF both tasks
set -euo pipefail
# shellcheck source=_lib.sh
source "$(dirname "$0")/_lib.sh"

run_baseline_full_zjh_both_tasks repvit
run_baseline_dai_ftc repvit
run_baseline_oof_both_tasks repvit

echo "Done. Outputs: $OUT_ROOT/repvit/"
