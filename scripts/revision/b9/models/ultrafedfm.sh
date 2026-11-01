#!/usr/bin/env bash
# UltraFedFM: per task — full external → 5-fold OOF (uses ULTRAFEDFM_PYTHON if set).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../env_malig_b9.sh
source "$SCRIPT_DIR/../env_malig_b9.sh"
# shellcheck source=../_b9_model_lib.sh
source "$SCRIPT_DIR/../_b9_model_lib.sh"

export ULTRAFEDFM_PYTHON="${ULTRAFEDFM_PYTHON:-/mnt/wangbd8/workspace/envs/ultrafedfm/bin/python}"
b9_baseline_model_tasks ultrafedfm
