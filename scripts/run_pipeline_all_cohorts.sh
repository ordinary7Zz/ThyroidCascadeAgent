#!/usr/bin/env bash
# 串行对各队列执行 run_pipeline.py，写满 config/revision/b3/<id>.yaml 中多 DINO 专家的
# Phase 1–2 缓存（及完整级联的 selected_masks / autogluon 等，见 pipeline.output.output_dir）。
#
# 默认与 B3 波次 1 队列一致（不含 nhc_misd_tus）：
#   tn3k, tn5k, thyroidxl, zjh8k, rjh7k, ddti_seg, ddti_cls, pktn, sample
#
# 用法：
#   ./scripts/run_pipeline_all_cohorts.sh
#   ./scripts/run_pipeline_all_cohorts.sh --exclude tn3k
#   ./scripts/run_pipeline_all_cohorts.sh --from tn5k
#   ./scripts/run_pipeline_all_cohorts.sh --cohorts tn5k,ddti_seg
#   ./scripts/run_pipeline_all_cohorts.sh --skip-complete --continue-on-error
#   ./scripts/run_pipeline_all_cohorts.sh --device cuda
#
# 环境：PYTHON（默认 python3）、REPO_ROOT、DEVICE（默认 cuda）

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
LOG_DIR="${ROOT}/output/_pipeline_batch_logs"

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

SKIP_COMPLETE=false
CONTINUE_ON_ERROR=false
FROM_COHORT=""
EXCLUDE=()
COHORTS=()

usage() {
  sed -n '2,16p' "$0" | sed 's/^# //'
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage 0 ;;
    --from) FROM_COHORT="$2"; shift 2 ;;
    --exclude) EXCLUDE+=("$2"); shift 2 ;;
    --cohorts) IFS=',' read -ra COHORTS <<< "$2"; shift 2 ;;
    --skip-complete) SKIP_COMPLETE=true; shift ;;
    --continue-on-error) CONTINUE_ON_ERROR=true; shift ;;
    --device) DEVICE="$2"; shift 2 ;;
    --no-sample) EXCLUDE+=(sample); shift ;;
    *) echo "未知参数: $1" >&2; usage 1 ;;
  esac
done

if [[ ${#COHORTS[@]} -eq 0 ]]; then
  COHORTS=("${DEFAULT_COHORTS[@]}")
fi

should_exclude() {
  local c="$1"
  for e in "${EXCLUDE[@]}"; do
    [[ "$c" == "$e" ]] && return 0
  done
  return 1
}

phase12_complete() {
  local cfg="$1"
  "${PY}" -c "
import sys, yaml
from pathlib import Path

cfg_path = Path(sys.argv[1])
root = Path(sys.argv[2])
with open(cfg_path, encoding='utf-8') as f:
    c = yaml.safe_load(f)
pipe = c.get('pipeline', {})
ab = pipe.get('ablation', {})
task = ab.get('task', 'both')
run_seg = pipe.get('run_segmentation', task in ('seg', 'both'))
run_cls = pipe.get('run_classification', task in ('cls', 'both'))
inter = root / ab.get('shared_intermediate', '')
if not inter.is_dir():
    sys.exit(1)
seg_d, cls_d = inter / 'seg', inter / 'cls'
for m in c.get('segmentation', {}).get('models', []):
    if run_seg and not (seg_d / f\"{m['name']}.npz\").is_file():
        sys.exit(1)
for m in c.get('classification', {}).get('models', []):
    if run_cls and not (cls_d / f\"{m['name']}.json\").is_file():
        sys.exit(1)
sys.exit(0)
" "${cfg}" "${ROOT}"
}

mkdir -p "${LOG_DIR}"
started=false
[[ -z "${FROM_COHORT}" ]] && started=true

echo "REPO: ${ROOT}"
echo "Python: ${PY}  device: ${DEVICE}"
echo "队列: ${COHORTS[*]}"
echo "日志: ${LOG_DIR}"
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

  cfg="${ROOT}/config/revision/b3/${cohort}.yaml"
  if [[ ! -f "${cfg}" ]]; then
    echo ">>> 缺少配置: ${cfg}" >&2
    failures+=("${cohort}:missing_config")
    if [[ "${CONTINUE_ON_ERROR}" == true ]]; then continue; else exit 1; fi
  fi

  if [[ "${SKIP_COMPLETE}" == true ]] && phase12_complete "${cfg}"; then
    echo ">>> Phase 1–2 专家缓存已齐，跳过: ${cohort}"
    continue
  fi

  ts="$(date +%Y%m%d_%H%M%S)"
  log="${LOG_DIR}/${cohort}_${ts}.log"
  echo ""
  echo "======== run_pipeline: ${cohort} ========"
  echo "  config: config/revision/b3/${cohort}.yaml"
  echo "  log:    ${log}"

  set +e
  (
    cd "${ROOT}"
    "${PY}" run_pipeline.py --config "config/revision/b3/${cohort}.yaml" --device "${DEVICE}"
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
echo "全部队列 pipeline 已串行跑完；intermediate 见各 yaml 的 pipeline.ablation.shared_intermediate。"
