#!/usr/bin/env bash
# MedGemma: (1) full+ZJH both tasks, (2) Dai FTC — no step 3 (5-fold OOF)
set -euo pipefail
source "$(dirname "$0")/_lib.sh"

run_baseline_full_zjh_both_tasks medgemma
run_baseline_dai_ftc medgemma

echo "Done (no 5-fold OOF for MedGemma). Outputs: $OUT_ROOT/medgemma/"
