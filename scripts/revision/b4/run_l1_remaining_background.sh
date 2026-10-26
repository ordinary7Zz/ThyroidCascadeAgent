#!/usr/bin/env bash
# 后台顺序跑 B4 L1（默认跳过已完成的 sample、tn3k）。
#
# 启动:
#   cd /path/to/ThyroidCascadeAgent
#   nohup bash scripts/revision/b4/run_l1_remaining_background.sh >> output/ablation/l1/l1_remaining_batch.log 2>&1 &
#   echo $!   # 记下 PID
#
# 查看:
#   tail -f output/ablation/l1/l1_remaining_batch.log
#   tail -f output/ablation/l1/<cohort>/l1_run.log
#
# 环境变量:
#   DEVICE=cuda|cuda:0     默认 cuda
#   SKIP_COHORTS="a b"     额外跳过（空格分隔）
#   COHORTS="tn5k ..."     覆盖默认队列列表

set -u
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

DEVICE="${DEVICE:-cuda}"
PYTHON="${PYTHON:-python}"
RUNNER="scripts/revision/b4/run_l1_cohort.py"
BUILD="scripts/revision/b4/build_b4_tables.py"

# 已完成 / 默认跳过（RUN_ALL_L1=1 时不跳过，见 run_l1_all_cohorts.sh）
if [[ "${RUN_ALL_L1:-0}" == "1" ]]; then
  DEFAULT_SKIP=()
else
  DEFAULT_SKIP=(sample tn3k)
fi
if [[ -n "${SKIP_COHORTS:-}" ]]; then
  read -r -a EXTRA_SKIP <<< "$SKIP_COHORTS"
else
  EXTRA_SKIP=()
fi

should_skip() {
  local c="$1"
  for s in "${DEFAULT_SKIP[@]}" "${EXTRA_SKIP[@]}"; do
    [[ "$c" == "$s" ]] && return 0
  done
  return 1
}

if [[ -n "${COHORTS:-}" ]]; then
  read -r -a QUEUE <<< "$COHORTS"
else
  QUEUE=(tn5k thyroidxl ddti_cls ddti_seg pktn zjh8k rjh7k nhc_misd_tus)
fi

BATCH_LOG_DIR="$ROOT/output/ablation/l1/_batch_logs"
mkdir -p "$BATCH_LOG_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
SUMMARY="$BATCH_LOG_DIR/summary_${STAMP}.txt"

echo "=== L1 remaining batch start $(date -Iseconds) ==="
echo "ROOT=$ROOT DEVICE=$DEVICE"
echo "QUEUE=${QUEUE[*]}"
echo "DEFAULT_SKIP=${DEFAULT_SKIP[*]} EXTRA_SKIP=${EXTRA_SKIP[*]:-}"

FAILED=()
OK=()

for cohort in "${QUEUE[@]}"; do
  if should_skip "$cohort"; then
    echo "[skip] $cohort (in skip list)"
    continue
  fi

  if [[ ! -f "config/revision/b4/l1/${cohort}.yaml" ]]; then
    echo "[skip] $cohort — missing config/revision/b4/l1/${cohort}.yaml"
    continue
  fi

  COHORT_LOG="$ROOT/output/ablation/l1/${cohort}/l1_run.log"
  mkdir -p "$(dirname "$COHORT_LOG")"

  echo ""
  echo "======== $(date -Iseconds) L1 cohort: $cohort ========"

  set +e
  "$PYTHON" -u "$RUNNER" --cohort "$cohort" --device "$DEVICE" --fresh \
    2>&1 | tee "$COHORT_LOG"
  rc=${PIPESTATUS[0]}
  set -e

  if [[ $rc -ne 0 ]]; then
    echo "FAILED $cohort exit=$rc" | tee -a "$SUMMARY"
    FAILED+=("$cohort")
    continue
  fi

  if [[ -f "artifacts/b4_l1_${cohort}.json" ]]; then
    "$PYTHON" "$BUILD" --config "config/revision/b4/${cohort}.yaml" 2>&1 | tee -a "$COHORT_LOG" || true
  fi

  echo "OK $cohort" | tee -a "$SUMMARY"
  OK+=("$cohort")
done

echo ""
echo "=== L1 remaining batch end $(date -Iseconds) ==="
echo "OK (${#OK[@]}): ${OK[*]:-none}"
echo "FAILED (${#FAILED[@]}): ${FAILED[*]:-none}"
echo "Summary: $SUMMARY"

if [[ ${#FAILED[@]} -gt 0 ]]; then
  exit 1
fi
