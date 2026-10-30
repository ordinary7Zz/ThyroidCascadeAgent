#!/usr/bin/env bash
set -euo pipefail
THYROID_AGENT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
exec bash "$THYROID_AGENT/Classification_Models/b9_oof/scripts/run_medgemma_cv.sh" "$@"
