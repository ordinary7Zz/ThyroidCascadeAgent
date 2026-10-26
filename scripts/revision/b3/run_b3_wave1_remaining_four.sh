#!/usr/bin/env bash
# B3 波次 1：补跑尚未完成波次 1 的四个队列（不含正在跑的 zjh8k）。
#
#   rjh7k (both), ddti_seg (seg), ddti_cls (cls), pktn (seg)
#
# 前置：各 cohort 的 shared_intermediate / pipeline_run/intermediate 已齐。
#
# 用法：
#   ./scripts/revision/b3/run_b3_wave1_remaining_four.sh
#   ./scripts/revision/b3/run_b3_wave1_remaining_four.sh --from pktn
#   ./scripts/revision/b3/run_b3_wave1_remaining_four.sh --continue-on-error
#   DEVICE=cuda ./scripts/revision/b3/run_b3_wave1_remaining_four.sh
#
# 环境：PYTHON（默认 python3）、REPO_ROOT、DEVICE（传给 run_b3_batch，默认 cuda）

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
PY="${PYTHON:-python3}"
DEVICE="${DEVICE:-cuda}"
LOG_DIR="${ROOT}/output/ablation/b3/_batch_logs"

# sklearn unpickle 版本警告：由 repo_path.install() → configure_sklearn_pickle_warnings() 抑制
# 勿用 PYTHONWARNINGS=ignore::sklearn.exceptions.*（Python 3.11 会报 Invalid -W）

PRESET="${PRESET:-wave1}"
# 先小队列、后 rjh7k（7288 张，最久）
JOBS=(
  "pktn:seg"
  "ddti_cls:cls"
  "ddti_seg:seg"
  "rjh7k:both"
)

FROM_JOB=""
CONTINUE_ON_ERROR=false

usage() {
  sed -n '2,14p' "$0" | sed 's/^# //'
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage 0 ;;
    --from) FROM_JOB="$2"; shift 2 ;;
    --continue-on-error) CONTINUE_ON_ERROR=true; shift ;;
    *) echo "未知参数: $1" >&2; usage 1 ;;
  esac
done

mkdir -p "${LOG_DIR}"
started=false
[[ -z "${FROM_JOB}" ]] && started=true

echo "REPO: ${ROOT}"
echo "Python: ${PY}"
echo "DEVICE: ${DEVICE}"
echo "队列: ${JOBS[*]}"
echo "日志: ${LOG_DIR}"
echo ""

failures=()

for job in "${JOBS[@]}"; do
  cohort="${job%%:*}"
  task="${job#*:}"
  if [[ "${started}" == false ]]; then
    if [[ "${cohort}" == "${FROM_JOB}" ]]; then
      started=true
    else
      echo ">>> 跳过（--from ${FROM_JOB}）: ${cohort}"
      continue
    fi
  fi

  cfg="${ROOT}/config/revision/b3/${cohort}.yaml"
  if [[ ! -f "${cfg}" ]]; then
    echo ">>> 缺少配置: ${cfg}" >&2
    failures+=("${cohort}:missing_config")
    if [[ "${CONTINUE_ON_ERROR}" == true ]]; then continue; else exit 1; fi
  fi

  ts="$(date +%Y%m%d_%H%M%S)"
  log="${LOG_DIR}/${cohort}_wave1_${ts}.log"
  echo ""
  echo "======== B3 ${PRESET}: ${cohort} (task=${task}) ========"
  echo "  config: config/revision/b3/${cohort}.yaml"
  echo "  log:    ${log}"

  set +e
  (
    cd "${ROOT}"
    "${PY}" scripts/revision/b3/run_b3_batch.py \
      --config "config/revision/b3/${cohort}.yaml" \
      --preset "${PRESET}" \
      --task "${task}" \
      --force-phase3 \
      --summarize \
      --device "${DEVICE}"
  ) 2>&1 | tee "${log}"
  rc=${PIPESTATUS[0]}
  set -e

  if [[ "${rc}" -ne 0 ]]; then
    echo ">>> 失败: ${cohort} (exit ${rc})" >&2
    failures+=("${cohort}:${rc}")
    if [[ "${CONTINUE_ON_ERROR}" != true ]]; then
      exit "${rc}"
    fi
  else
    echo ">>> 完成: ${cohort}"
  fi
done

echo ""
if [[ ${#failures[@]} -gt 0 ]]; then
  echo "以下队列失败: ${failures[*]}" >&2
  exit 1
fi
echo "四个队列 B3 ${PRESET} 已全部串行跑完。"
