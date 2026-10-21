#!/usr/bin/env bash
# B8：对有 pipeline_run/results.json 的队列批量 backfill（可选）+ 校准/拒答评估。
#
# 前置：
#   1) 各队列已跑过 run_pipeline（或等价），存在 results.json + intermediate/
#   2) 已用 --fit 生成全局阈值：output/b8/fit/abstention_thresholds.json
#
# 用法：
#   export PYTHON=/mnt/wangbd8/workspace/envs/thyroid_infer/bin/python
#   ./scripts/run_b8_all_cohorts.sh --fit-first --val-results output/sample/pipeline_run/results.json
#   ./scripts/run_b8_all_cohorts.sh
#   ./scripts/run_b8_all_cohorts.sh --skip-backfill --continue-on-error
#   ./scripts/run_b8_all_cohorts.sh --cohorts tn3k,tn5k,thyroidxl
#
# 定稿：--val-results 应为 Methods 验证集（如 output/validation/no_llm_primary/results.json），
#       勿用各测试队列 pipeline_run 定阈。

set -euo pipefail

ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PY="${PYTHON:-python3}"
THRESH="${B8_THRESHOLDS:-${ROOT}/output/b8/fit/abstention_thresholds.json}"
FIT_OUT="${B8_FIT_OUT:-${ROOT}/output/b8/fit}"
EVAL_ROOT="${B8_EVAL_ROOT:-${ROOT}/output/b8/cohorts}"

DEFAULT_COHORTS=(
  tn3k
  tn5k
  thyroidxl
  zjh8k
  rjh7k
  ddti_seg
  ddti_cls
  pktn
  sample
)

FIT_FIRST=false
VAL_RESULTS=""
SKIP_BACKFILL=false
CONTINUE_ON_ERROR=false
COHORTS=()

usage() {
  sed -n '2,20p' "$0" | sed 's/^# //'
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage 0 ;;
    --fit-first) FIT_FIRST=true; shift ;;
    --val-results) VAL_RESULTS="$2"; shift 2 ;;
    --skip-backfill) SKIP_BACKFILL=true; shift ;;
    --continue-on-error) CONTINUE_ON_ERROR=true; shift ;;
    --cohorts) IFS=',' read -ra COHORTS <<< "$2"; shift 2 ;;
    *) echo "未知参数: $1" >&2; usage 1 ;;
  esac
done

if [[ ${#COHORTS[@]} -eq 0 ]]; then
  COHORTS=("${DEFAULT_COHORTS[@]}")
fi

resolve_output_dir() {
  local cfg="$1"
  "${PY}" -c "
import sys, yaml
from pathlib import Path
with open(sys.argv[1], encoding='utf-8') as f:
    c = yaml.safe_load(f)
out = (c.get('pipeline') or {}).get('output') or {}
d = out.get('output_dir') or ''
if not d:
    raise SystemExit('missing pipeline.output.output_dir')
print(d)
" "${cfg}"
}

cd "${ROOT}"
mkdir -p "${EVAL_ROOT}"

if [[ "${FIT_FIRST}" == true ]]; then
  if [[ -z "${VAL_RESULTS}" ]]; then
    echo ">>> --fit-first 需要 --val-results <validation/results.json>" >&2
    exit 1
  fi
  if [[ ! -f "${VAL_RESULTS}" ]]; then
    echo ">>> 找不到验证集 results: ${VAL_RESULTS}" >&2
    exit 1
  fi
  echo "======== B8 fit（验证集定阈）========"
  echo "  val-results: ${VAL_RESULTS}"
  echo "  out:         ${FIT_OUT}"
  "${PY}" scripts/run_calibration_abstention.py \
    --fit \
    --val-results "${VAL_RESULTS}" \
    --out "${FIT_OUT}" \
    --rule-subset nhc
  THRESH="${FIT_OUT}/abstention_thresholds.json"
fi

if [[ ! -f "${THRESH}" ]]; then
  echo ">>> 缺少阈值文件: ${THRESH}" >&2
  echo "    请先: ./scripts/run_b8_all_cohorts.sh --fit-first --val-results <path>" >&2
  exit 1
fi

failures=()

for cohort in "${COHORTS[@]}"; do
  cfg="${ROOT}/config/b3/${cohort}.yaml"
  if [[ ! -f "${cfg}" ]]; then
    echo ">>> 跳过 ${cohort}: 无 config/b3/${cohort}.yaml" >&2
    failures+=("${cohort}:no_config")
    continue
  fi

  out_rel="$(resolve_output_dir "${cfg}")"
  if [[ "${out_rel}" == /* ]]; then
    out_dir="${out_rel}"
  else
    out_dir="${ROOT}/${out_rel}"
  fi
  results="${out_dir}/results.json"
  eval_out="${EVAL_ROOT}/${cohort}"

  echo ""
  echo "======== B8 eval: ${cohort} ========"
  echo "  results: ${results}"
  echo "  out:     ${eval_out}"

  if [[ ! -f "${results}" ]]; then
    echo ">>> 跳过: 无 results.json" >&2
    failures+=("${cohort}:no_results")
    [[ "${CONTINUE_ON_ERROR}" == true ]] && continue || exit 1
  fi
  if [[ ! -d "${out_dir}/intermediate" ]]; then
    echo ">>> 跳过: 无 intermediate/" >&2
    failures+=("${cohort}:no_intermediate")
    [[ "${CONTINUE_ON_ERROR}" == true ]] && continue || exit 1
  fi

  if [[ "${SKIP_BACKFILL}" != true ]]; then
    set +e
    "${PY}" scripts/backfill_results_metadata.py \
      --output-dir "${out_dir}" \
      --config "config/b3/${cohort}.yaml"
    rc=$?
    set -e
    if [[ "${rc}" -ne 0 ]]; then
      echo ">>> backfill 失败 ${cohort} (exit ${rc})" >&2
      failures+=("${cohort}:backfill_${rc}")
      [[ "${CONTINUE_ON_ERROR}" == true ]] && continue || exit "${rc}"
    fi
  fi

  set +e
  "${PY}" scripts/run_calibration_abstention.py \
    --eval \
    --test-results "${results}" \
    --thresholds "${THRESH}" \
    --out "${eval_out}" \
    --rule-subset nhc
  rc=$?
  set -e
  if [[ "${rc}" -ne 0 ]]; then
    echo ">>> B8 eval 失败 ${cohort} (exit ${rc})" >&2
    failures+=("${cohort}:eval_${rc}")
    [[ "${CONTINUE_ON_ERROR}" == true ]] && continue || exit "${rc}"
  else
    echo ">>> 完成: ${eval_out}/abstention_eval.json"
  fi
done

echo ""
if [[ ${#failures[@]} -gt 0 ]]; then
  echo "未成功: ${failures[*]}" >&2
  exit 1
fi
echo "全部 B8 eval 完成。汇总目录: ${EVAL_ROOT}"
