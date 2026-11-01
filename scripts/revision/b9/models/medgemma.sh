#!/usr/bin/env bash
# MedGemma: full train + zjh_test (+ Dai for FTC). No 5-fold CV.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../env_malig_b9.sh
source "$SCRIPT_DIR/../env_malig_b9.sh"
# shellcheck source=../_b9_model_lib.sh
source "$SCRIPT_DIR/../_b9_model_lib.sh"

b9_vlm_model_tasks medgemma
