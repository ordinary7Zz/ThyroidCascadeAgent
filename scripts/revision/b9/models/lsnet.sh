#!/usr/bin/env bash
# LSNet: per task — full external → 5-fold OOF (see repvit.sh).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../env_malig_b9.sh
source "$SCRIPT_DIR/../env_malig_b9.sh"
# shellcheck source=../_b9_model_lib.sh
source "$SCRIPT_DIR/../_b9_model_lib.sh"

b9_baseline_model_tasks lsnet
