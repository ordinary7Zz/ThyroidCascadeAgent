#!/usr/bin/env bash
# Regenerate B2 tables for all zjh8k b2_exports with train–ZJH dHash H=0 exclusion (no re-inference).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_find_revision_repo_root() {
  local d="$SCRIPT_DIR"
  while [[ -n "$d" && "$d" != "/" ]]; do
    if [[ -f "$d/run_pipeline.py" ]]; then
      printf '%s\n' "$d"
      return 0
    fi
    d="$(dirname "$d")"
  done
  return 1
}
ROOT="${REPO_ROOT:-$(_find_revision_repo_root)}"
cd "$ROOT"
EXCL="${ROOT}/docs/revision/b1/tables/zjh_excl_train_dhash0_manifest.json"
EXPORTS_ROOT="${EXPORTS_ROOT:-$(dirname "$ROOT")/b2_exports}"
python "${ROOT}/scripts/revision/b2/run_b2_from_export.py" \
  --scan-all \
  --exports-root "$EXPORTS_ROOT" \
  --cohort-substr zjh8k \
  --exclude-images "$EXCL"
