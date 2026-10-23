#!/usr/bin/env bash
# Scan ThyroidAgent/b2_exports and write baseline_*_b2.json + BASELINES_INDEX.json
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
exec python "${ROOT}/scripts/revision/b2/run_b2_from_export.py" --scan-all
