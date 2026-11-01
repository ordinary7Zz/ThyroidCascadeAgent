#!/usr/bin/env bash
# Run all per-model B9 scripts in a sensible order (after 01_export_shared_folds.sh).
#
# Usage:
#   export CUDA_VISIBLE_DEVICES=0 RUN_TAG=zjh20261101
#   bash scripts/revision/b9/01_export_shared_folds.sh
#   bash scripts/revision/b9/models/run_all.sh
#
#   MODELS="repvit llnm" bash scripts/revision/b9/models/run_all.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MODELS="${MODELS:-repvit lsnet ultrafedfm llnm tiger dino medgemma qwen3}"

for name in $MODELS; do
  script="$SCRIPT_DIR/${name}.sh"
  if [[ ! -f "$script" ]]; then
    echo "Skip missing $script" >&2
    continue
  fi
  echo ""
  echo "==================== model: $name ===================="
  bash "$script"
done

echo ""
echo "All models finished."
