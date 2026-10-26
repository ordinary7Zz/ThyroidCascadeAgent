#!/usr/bin/env bash
# 监视 B3 bundle 进度（不依赖终端 scrollback）。
# 用法: ./scripts/revision/b3/zjh/watch_b3_bundle_progress.sh zjh8k [interval_sec]

COHORT="${1:-zjh8k}"
INTERVAL="${2:-30}"
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
OUT="$ROOT/output/ablation/b3/$COHORT"
PROGRESS="$OUT/.bundle_progress.json"
PGREP_PATTERN="run_b3_batch.py --config config/revision/b3/${COHORT}.yaml"

echo "watching $OUT (every ${INTERVAL}s); Ctrl+C to stop"
while true; do
  echo "----- $(date '+%F %T') -----"
  pid="$(pgrep -f "$PGREP_PATTERN" 2>/dev/null | head -1 || true)"
  if [[ -n "$pid" ]]; then
    ps -p "$pid" -o pid=,etime=,rss=,pcpu=,stat= 2>/dev/null | awk '{printf "process: pid=%s etime=%s rss_kb=%s cpu%%=%s stat=%s\n", $1,$2,$3,$4,$5}'
  else
    echo "process: not running"
  fi
  if [[ -f "$PROGRESS" ]]; then
    cat "$PROGRESS"
  else
    echo "no .bundle_progress.json (当前进程若在改代码前启动，不会有此文件)"
  fi
  n="$(find "$OUT" -name b3_metrics.json 2>/dev/null | wc -l)"
  echo "b3_metrics.json count: ${n} / 6"
  subdirs="$(ls -1 "$OUT" 2>/dev/null | grep -v '^\.bundle_staging$' | grep -v '^\.bundle_progress.json$' || true)"
  if [[ -n "$subdirs" ]]; then
    echo "$subdirs" | head -10
  else
    echo "(no mode dirs yet — still bundle scan or not started)"
  fi
  sleep "$INTERVAL"
done
