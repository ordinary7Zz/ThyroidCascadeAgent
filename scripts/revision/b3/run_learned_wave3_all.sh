#!/usr/bin/env bash
# B3 策略 6（learned）批量：按固定顺序跑 7 个队列。
#
# 每个队列：val 上 fit（仅 ablation.task 所需的路由器）→ test 上 infer → eval。
#   both   → seg + cls 逻辑回归
#   seg    → 仅 seg（pktn, ddti_seg, rjh7k）
#   cls    → 仅 cls（ddti_cls）
#
# 前置（缺 intermediate 时会失败）：
#   - TN5K / ThyroidXL / PKTN：output/validation/_parts/<id>/intermediate 已存在
#   - DDTI：python run_pipeline.py --config config/revision/validation/ddti_seg.yaml
#           python run_pipeline.py --config config/revision/validation/ddti_cls.yaml
#   - ZJH / RJH：b3_reinfer chunk_* 已齐（与 wave1 相同）
#
# 环境：
#   PY=/path/to/python  DEVICE=cpu  CONTINUE_ON_ERROR=1  SKIP_FIT=1  SKIP_EVAL=1
#
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
PY="${PY:-python3}"
DEVICE="${DEVICE:-cpu}"
MANIFEST="${MANIFEST:-config/revision/b3/learned_wave3_cohorts.yaml}"
LOG_DIR="${LOG_DIR:-output/ablation/b3/_batch_logs}"
mkdir -p "$LOG_DIR"

# 顺序固定；可用环境变量覆盖，例如：
#   COHORTS="tn5k thyroidxl" bash scripts/revision/b3/run_learned_wave3_all.sh
if [[ -n "${COHORTS:-}" ]]; then
  # shellcheck disable=SC2206
  COHORTS=($COHORTS)
else
  COHORTS=(tn5k thyroidxl pktn ddti_seg ddti_cls zjh8k rjh7k)
fi

_run_one() {
  local id="$1"
  local log="${LOG_DIR}/learned_${id}_$(date +%Y%m%d_%H%M%S).log"
  echo ""
  echo "======== learned wave3: ${id} ========"
  echo "  log: ${log}"
  local extra=()
  [[ "${SKIP_FIT:-0}" == "1" ]] && extra+=(--skip-fit)
  [[ "${SKIP_INFER:-0}" == "1" ]] && extra+=(--skip-infer)
  [[ "${SKIP_EVAL:-0}" == "1" ]] && extra+=(--skip-eval)
  if ! "$PY" scripts/revision/b3/run_learned_cohort.py \
    --manifest "$MANIFEST" \
    --cohort-meta "$id" \
    --device "$DEVICE" \
    "${extra[@]}" \
    2>&1 | tee "$log"; then
    if [[ "${CONTINUE_ON_ERROR:-0}" == "1" ]]; then
      echo "!!! ${id} 失败，CONTINUE_ON_ERROR=1 继续下一队列" >&2
      return 0
    fi
    return 1
  fi
}

for id in "${COHORTS[@]}"; do
  _run_one "$id"
done

echo ""
echo "全部队列 learned 流程结束。汇总表见各 output/ablation/b3/<id>/_summary/b3_routing_table.csv"
