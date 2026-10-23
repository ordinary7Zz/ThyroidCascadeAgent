# shellcheck shell=bash
# Source from any scripts/revision/** shell script:
#   source "$(dirname "${BASH_SOURCE[0]}")/../_repo_root.sh"   # b1–b11 (one level)
#   source "$(dirname "${BASH_SOURCE[0]}")/../../_repo_root.sh" # b3/zjh (two levels)

revision_repo_root() {
  local caller="${BASH_SOURCE[1]:-${BASH_SOURCE[0]}}"
  local d
  d="$(cd "$(dirname "$caller")" && pwd)"
  while [[ -n "$d" && "$d" != "/" ]]; do
    if [[ -f "$d/run_pipeline.py" ]]; then
      printf '%s\n' "$d"
      return 0
    fi
    d="$(dirname "$d")"
  done
  return 1
}

revision_source_repo_root() {
  local _caller="${BASH_SOURCE[1]:-${BASH_SOURCE[0]}}"
  local _d _found=""
  _d="$(cd "$(dirname "$_caller")" && pwd)"
  while [[ -n "$_d" && "$_d" != "/" ]]; do
    if [[ -f "$_d/_repo_root.sh" ]]; then
      _found="${_d}/_repo_root.sh"
      break
    fi
    _d="$(dirname "$_d")"
  done
  if [[ -z "$_found" ]]; then
    echo "revision_source_repo_root: _repo_root.sh not found" >&2
    return 1
  fi
  # shellcheck source=/dev/null
  source "$_found"
}
