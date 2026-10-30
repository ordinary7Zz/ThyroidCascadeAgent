#!/usr/bin/env bash
# Forward to Classification_Models/b9_oof/scripts/run_all_baselines_cv.sh
set -euo pipefail
THYROID_AGENT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
SCRIPT="$THYROID_AGENT/Classification_Models/b9_oof/scripts/run_all_baselines_cv.sh"
if [[ ! -x "$SCRIPT" ]]; then
  chmod +x "$SCRIPT" 2>/dev/null || true
fi
exec bash "$SCRIPT" "$@"
