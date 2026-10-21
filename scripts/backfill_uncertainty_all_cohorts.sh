#!/usr/bin/env bash
# 为各测试队列的 pipeline_run 补写 uncertainty / center_id（无需重跑 GPU）。
#
# 前置：output/<队列>/pipeline_run 已有 results.json 与 intermediate/（Phase 1–2）。
#
# 用法：
#   ./scripts/backfill_uncertainty_all_cohorts.sh
#   ./scripts/backfill_uncertainty_all_cohorts.sh --skip-if-complete
#   ./scripts/backfill_uncertainty_all_cohorts.sh --from tn5k
#   ./scripts/backfill_uncertainty_all_cohorts.sh --exclude tn3k --continue-on-error
#   ./scripts/backfill_uncertainty_all_cohorts.sh --cohorts tn5k,thyroidxl,zjh8k
#   ./scripts/backfill_uncertainty_all_cohorts.sh --include-nhc
#
# 环境：PYTHON（默认 python3）、REPO_ROOT

set -euo pipefail

ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PY="${PYTHON:-python3}"

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

SKIP_IF_COMPLETE=false
CONTINUE_ON_ERROR=false
FROM_COHORT=""
EXCLUDE=()
COHORTS=()
INCLUDE_NHC=false

usage() {
  sed -n '2,14p' "$0" | sed 's/^# //'
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage 0 ;;
    --from) FROM_COHORT="$2"; shift 2 ;;
    --exclude) EXCLUDE+=("$2"); shift 2 ;;
    --cohorts) IFS=',' read -ra COHORTS <<< "$2"; shift 2 ;;
    --skip-if-complete) SKIP_IF_COMPLETE=true; shift ;;
    --continue-on-error) CONTINUE_ON_ERROR=true; shift ;;
    --include-nhc) INCLUDE_NHC=true; shift ;;
    *) echo "未知参数: $1" >&2; usage 1 ;;
  esac
done

if [[ ${#COHORTS[@]} -eq 0 ]]; then
  COHORTS=("${DEFAULT_COHORTS[@]}")
fi
if [[ "${INCLUDE_NHC}" == true ]]; then
  COHORTS+=("nhc_misd_tus")
fi

should_exclude() {
  local id="$1"
  for e in "${EXCLUDE[@]}"; do
    [[ "$id" == "$e" ]] && return 0
  done
  return 1
}

resolve_output_dir() {
  local cfg="$1"
  "${PY}" -c "
import sys
from pathlib import Path
import yaml
with open(sys.argv[1], encoding='utf-8') as f:
    c = yaml.safe_load(f)
out = (c.get('pipeline') or {}).get('output') or {}
d = out.get('output_dir') or ''
if not d:
    raise SystemExit('missing pipeline.output.output_dir')
print(d)
" "${cfg}"
}

uncertainty_complete() {
  local results_json="$1"
  "${PY}" -c "
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
if not p.is_file():
    raise SystemExit(1)
data = json.loads(p.read_text(encoding='utf-8'))
if not data:
    raise SystemExit(1)
n = len(data)
u = sum(1 for r in data if r.get('uncertainty'))
sys.exit(0 if u == n else 1)
" "${results_json}"
}

started=false
[[ -z "${FROM_COHORT}" ]] && started=true

echo "REPO: ${ROOT}"
echo "Python: ${PY}"
echo "队列: ${COHORTS[*]}"
echo ""

failures=()

for cohort in "${COHORTS[@]}"; do
  if should_exclude "${cohort}"; then
    echo ">>> 跳过（--exclude）: ${cohort}"
    continue
  fi
  if [[ "${started}" == false ]]; then
    if [[ "${cohort}" == "${FROM_COHORT}" ]]; then
      started=true
    else
      echo ">>> 跳过（--from ${FROM_COHORT}）: ${cohort}"
      continue
    fi
  fi

  cfg="${ROOT}/config/b3/${cohort}.yaml"
  if [[ ! -f "${cfg}" ]]; then
    echo ">>> 缺少配置: ${cfg}" >&2
    failures+=("${cohort}:missing_config")
    if [[ "${CONTINUE_ON_ERROR}" == true ]]; then continue; else exit 1; fi
  fi

  out_rel="$(resolve_output_dir "${cfg}")"
  if [[ "${out_rel}" == /* ]]; then
    out_dir="${out_rel}"
  else
    out_dir="${ROOT}/${out_rel}"
  fi
  results="${out_dir}/results.json"

  echo ""
  echo "======== backfill: ${cohort} ========"
  echo "  config:     config/b3/${cohort}.yaml"
  echo "  output-dir: ${out_dir}"

  if [[ ! -f "${results}" ]]; then
    echo ">>> 跳过: 无 results.json" >&2
    failures+=("${cohort}:no_results")
    if [[ "${CONTINUE_ON_ERROR}" == true ]]; then continue; else exit 1; fi
  fi
  if [[ ! -d "${out_dir}/intermediate" ]]; then
    echo ">>> 跳过: 无 intermediate/（需先跑 Phase 1–2）" >&2
    failures+=("${cohort}:no_intermediate")
    if [[ "${CONTINUE_ON_ERROR}" == true ]]; then continue; else exit 1; fi
  fi

  if [[ "${SKIP_IF_COMPLETE}" == true ]] && uncertainty_complete "${results}"; then
    echo ">>> 已全部含 uncertainty，跳过（--skip-if-complete）"
    continue
  fi

  set +e
  (
    cd "${ROOT}"
    "${PY}" scripts/backfill_results_metadata.py \
      --output-dir "${out_dir}" \
      --config "config/b3/${cohort}.yaml"
  )
  rc=$?
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
  echo "以下队列未成功: ${failures[*]}" >&2
  exit 1
fi
echo "全部 backfill 任务已跑完。"
