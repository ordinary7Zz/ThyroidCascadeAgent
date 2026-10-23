#!/usr/bin/env bash
# B2 one-shot (task-aware: cls / seg / both per docs/revision/b2/cohort_tasks.yaml)
# Usage: bash scripts/revision/b2/run_b2_all.sh
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
exec python "${ROOT}/scripts/revision/b2/run_b2_all.py"
