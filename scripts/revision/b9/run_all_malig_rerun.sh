#!/usr/bin/env bash
# Master orchestrator (run steps manually if GPU time is limited).
#
#   bash scripts/revision/b9/run_all_malig_rerun.sh          # folds + CNN OOF only
#   STEPS="01 02 03 04 05 06" bash scripts/revision/b9/run_all_malig_rerun.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STEPS="${STEPS:-01 02}"

for step in $STEPS; do
  script="$SCRIPT_DIR/${step}_"*.sh
  # shellcheck disable=SC2086
  match=( $script )
  if [[ ! -f "${match[0]}" ]]; then
    echo "No script for step $step" >&2
    exit 1
  fi
  echo ""
  echo "========== STEP $step: ${match[0]} =========="
  bash "${match[0]}"
done

echo ""
echo "Next: fill tab_malig_oof / tab_malig_ext / tab_ftcptc_ext_dai from run outputs."
echo "Baselines external (RepViT/LSNet/UltraFedFM zjh_test+Dai): implement in b9_oof or mirror Tiger/LLNM pattern."
