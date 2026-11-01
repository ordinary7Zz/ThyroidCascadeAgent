#!/usr/bin/env bash
# RepViT: per task — (1) full train + zjh_test, (2) Dai if FTC, (3) 5-fold OOF.
#
# Usage:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/revision/b9/models/repvit.sh
#   TASKS=ftcptc bash scripts/revision/b9/models/repvit.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../env_malig_b9.sh
source "$SCRIPT_DIR/../env_malig_b9.sh"
# shellcheck source=../_b9_model_lib.sh
source "$SCRIPT_DIR/../_b9_model_lib.sh"

b9_baseline_model_tasks repvit
