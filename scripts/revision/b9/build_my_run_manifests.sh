#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=env_malig_b9.sh
source "$SCRIPT_DIR/env_malig_b9.sh"
"$PYTHON" "$SCRIPT_DIR/build_my_run_manifests.py"
