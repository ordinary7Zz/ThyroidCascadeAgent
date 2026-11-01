#!/usr/bin/env bash
# Qwen3-VL: (1) full+ZJH both tasks, (2) Dai FTC — no step 3 (5-fold OOF)
set -euo pipefail
source "$(dirname "$0")/_lib.sh"

run_baseline_full_zjh_both_tasks qwen3
run_baseline_dai_ftc qwen3

echo "Done (no 5-fold OOF for Qwen3). Outputs: $OUT_ROOT/qwen3/"
