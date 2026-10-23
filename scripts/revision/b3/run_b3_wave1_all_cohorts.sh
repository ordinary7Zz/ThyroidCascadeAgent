#!/usr/bin/env bash
# 串行对各测试队列跑 B3 波次 1（static bundle：6 种静态路由，无 learned/llm）。
#
# 默认队列（不含 nhc_misd_tus；DDTI 拆为 ddti_seg + ddti_cls；PKTN 仅分割）：
#   tn3k, tn5k, thyroidxl, zjh8k, rjh7k, ddti_seg, ddti_cls, pktn, sample
#
# 前置：每个 config/b3/<id>.yaml 已配置数据路径，且 shared_intermediate 对应 Phase 1–2 已跑满。
#
# 用法：
#   ./scripts/revision/b3/run_b3_wave1_all_cohorts.sh
#   ./scripts/revision/b3/run_b3_wave1_all_cohorts.sh --from ddti_seg
#   ./scripts/revision/b3/run_b3_wave1_all_cohorts.sh --exclude tn3k
#   ./scripts/revision/b3/run_b3_wave1_all_cohorts.sh --jobs tn3k:both,ddti_cls:cls
#   ./scripts/revision/b3/run_b3_wave1_all_cohorts.sh --skip-complete --continue-on-error
#
# 环境：PYTHON（默认 python3）、REPO_ROOT

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
LOG_DIR="${ROOT}/output/ablation/b3/_batch_logs"

PRESET="${PRESET:-wave1}"
BASE_BATCH_ARGS=(--preset "${PRESET}" --force-phase3 --summarize)

# cohort_id:ablation_task（task 与 run_b3_batch.py --task 一致：seg | cls | both）
DEFAULT_JOBS=(
  tn3k:both
  tn5k:both
  thyroidxl:both
  zjh8k:both
  rjh7k:both
  ddti_seg:seg
  ddti_cls:cls
  pktn:seg
  sample:both
)

WAVE1_MODES=(soft_voting majority max_confidence static_rule best_single oracle)

SKIP_COMPLETE=false
CONTINUE_ON_ERROR=false
FROM_JOB=""
EXCLUDE=()
JOBS=()

usage() {
  sed -n '2,16p' "$0" | sed 's/^# //'
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage 0 ;;
    --from) FROM_JOB="$2"; shift 2 ;;
    --exclude) EXCLUDE+=("$2"); shift 2 ;;
    --jobs) IFS=',' read -ra JOBS <<< "$2"; shift 2 ;;
    --cohorts)
      # 兼容旧参数：仅 cohort 名，task 从 yaml 的 pipeline.ablation.task 读取
      IFS=',' read -ra _c <<< "$2"
      for c in "${_c[@]}"; do JOBS+=("${c}:"); done
      shift 2
      ;;
    --skip-complete) SKIP_COMPLETE=true; shift ;;
    --continue-on-error) CONTINUE_ON_ERROR=true; shift ;;
    --no-sample) EXCLUDE+=(sample); shift ;;
    --include-nhc)
      JOBS+=("nhc_misd_tus:both")
      shift
      ;;
    --) shift; BASE_BATCH_ARGS+=("$@"); break ;;
    *) echo "未知参数: $1" >&2; usage 1 ;;
  esac
done

if [[ ${#JOBS[@]} -eq 0 ]]; then
  JOBS=("${DEFAULT_JOBS[@]}")
fi

should_exclude() {
  local job_id="$1"
  for e in "${EXCLUDE[@]}"; do
    [[ "$job_id" == "$e" ]] && return 0
  done
  return 1
}

resolve_task() {
  local cohort="$1"
  local task="$2"
  local cfg="$3"
  if [[ -n "${task}" ]]; then
    echo "${task}"
    return
  fi
  "${PY}" -c "
import sys, yaml
with open(sys.argv[1], encoding='utf-8') as f:
    c = yaml.safe_load(f)
print(c.get('pipeline', {}).get('ablation', {}).get('task', 'both'))
" "${cfg}"
}

cohort_complete() {
  local cfg="$1"
  local out_root
  out_root="$("${PY}" -c "
import sys, yaml
with open(sys.argv[1], encoding='utf-8') as f:
    c = yaml.safe_load(f)
print(c.get('pipeline', {}).get('ablation', {}).get('output_root', '') or '')
" "${cfg}")"
  [[ -z "${out_root}" ]] && return 1
  local root
  if [[ "${out_root}" == /* ]]; then
    root="${out_root}"
  else
    root="${ROOT}/${out_root}"
  fi
  local mode
  for mode in "${WAVE1_MODES[@]}"; do
    [[ -f "${root}/${mode}/b3_metrics.json" ]] || return 1
  done
  return 0
}

mkdir -p "${LOG_DIR}"
started=false
[[ -z "${FROM_JOB}" ]] && started=true

echo "REPO: ${ROOT}"
echo "Python: ${PY}"
echo "任务: ${JOBS[*]}"
echo "batch 基础参数: ${BASE_BATCH_ARGS[*]}"
echo "日志: ${LOG_DIR}"
echo ""

failures=()

for job in "${JOBS[@]}"; do
  cohort="${job%%:*}"
  task="${job#*:}"
  if [[ "${cohort}" == "${task}" ]]; then
    task=""
  fi
  job_id="${cohort}"
  [[ -n "${task}" ]] && job_id="${cohort}:${task}"

  if should_exclude "${cohort}" || should_exclude "${job_id}"; then
    echo ">>> 跳过（--exclude）: ${job_id}"
    continue
  fi
  if [[ "${started}" == false ]]; then
    if [[ "${job_id}" == "${FROM_JOB}" || "${cohort}" == "${FROM_JOB}" ]]; then
      started=true
    else
      echo ">>> 跳过（--from ${FROM_JOB}）: ${job_id}"
      continue
    fi
  fi

  cfg="${ROOT}/config/b3/${cohort}.yaml"
  if [[ ! -f "${cfg}" ]]; then
    echo ">>> 缺少配置: ${cfg}" >&2
    failures+=("${job_id}:missing_config")
    if [[ "${CONTINUE_ON_ERROR}" == true ]]; then continue; else exit 1; fi
  fi

  task_resolved="$(resolve_task "${cohort}" "${task}" "${cfg}")"

  if [[ "${SKIP_COMPLETE}" == true ]] && cohort_complete "${cfg}"; then
    echo ">>> 已完成（6/6 b3_metrics），跳过: ${job_id}"
    continue
  fi

  ts="$(date +%Y%m%d_%H%M%S)"
  log="${LOG_DIR}/${cohort}_${task_resolved}_${ts}.log"
  echo ""
  echo "======== B3 ${PRESET}: ${cohort} (task=${task_resolved}) ========"
  echo "  config: ${cfg}"
  echo "  log:    ${log}"

  batch_args=("${BASE_BATCH_ARGS[@]}" --task "${task_resolved}")

  set +e
  (
    cd "${ROOT}"
    "${PY}" scripts/revision/b3/run_b3_batch.py --config "config/b3/${cohort}.yaml" "${batch_args[@]}"
  ) 2>&1 | tee "${log}"
  rc=${PIPESTATUS[0]}
  set -e

  if [[ "${rc}" -ne 0 ]]; then
    echo ">>> 失败: ${job_id} (exit ${rc})" >&2
    failures+=("${job_id}:${rc}")
    if [[ "${CONTINUE_ON_ERROR}" != true ]]; then
      exit "${rc}"
    fi
  else
    echo ">>> 完成: ${job_id}"
  fi
done

echo ""
if [[ ${#failures[@]} -gt 0 ]]; then
  echo "以下任务失败: ${failures[*]}" >&2
  exit 1
fi
echo "全部 B3 ${PRESET} 任务已串行跑完。"
