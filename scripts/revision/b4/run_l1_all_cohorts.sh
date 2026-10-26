#!/usr/bin/env bash
# 顺序跑全部 cohort（含 sample/tn3k）。大队列建议用 run_l1_remaining_background.sh。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
export RUN_ALL_L1=1
export COHORTS="sample tn3k tn5k thyroidxl zjh8k rjh7k pktn ddti_seg ddti_cls nhc_misd_tus"
export SKIP_COHORTS=""
exec bash "$ROOT/scripts/revision/b4/run_l1_remaining_background.sh"
