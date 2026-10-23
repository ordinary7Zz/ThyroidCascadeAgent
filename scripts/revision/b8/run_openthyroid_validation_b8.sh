#!/usr/bin/env bash
# OpenThyroidDB validation（路径 1）：四队列无 LLM pipeline → 合并 results → backfill → B8 定阈。
#
# 产出：
#   output/validation/no_llm_primary/results.json
#   output/validation/no_llm_primary/labels_merged.json
#   output/b8/fit/abstention_thresholds.json
#
# 默认张数：100 + 525(TN5K valid_copy) + 100 + 150 = 875（稿面 TN5K val=500 时差 25，见 config 注释）
#
# 用法：
#   export PYTHON=/mnt/wangbd8/workspace/envs/thyroid_infer/bin/python
#   export DEVICE=cuda
#   ./scripts/revision/b8/run_openthyroid_validation_b8.sh
#
#   ./scripts/revision/b8/run_openthyroid_validation_b8.sh --skip-pipeline    # 已有 _parts/*/results.json
#   ./scripts/revision/b8/run_openthyroid_validation_b8.sh --merge-only       # 仅合并 + backfill + fit
#   ./scripts/revision/b8/run_openthyroid_validation_b8.sh --with-cohort-eval # 定阈后跑 run_b8_all_cohorts.sh
#   ./scripts/revision/b8/run_openthyroid_validation_b8.sh --continue-on-error
#   ./scripts/revision/b8/run_openthyroid_validation_b8.sh --cohorts tn3k,tn5k

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
FIT_OUT="${B8_FIT_OUT:-${ROOT}/output/b8/fit}"
VAL_OUT="${VALIDATION_OUT:-${ROOT}/output/validation/no_llm_primary}"
NHC_CFG="${NHC_CFG:-config/revision/nhc_no_llm_primary.yaml}"

SKIP_PIPELINE=false
MERGE_ONLY=false
WITH_COHORT_EVAL=false
CONTINUE_ON_ERROR=false
COHORTS=()

usage() {
  sed -n '2,22p' "$0" | sed 's/^# //'
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage 0 ;;
    --skip-pipeline) SKIP_PIPELINE=true; shift ;;
    --merge-only) MERGE_ONLY=true; SKIP_PIPELINE=true; shift ;;
    --with-cohort-eval) WITH_COHORT_EVAL=true; shift ;;
    --continue-on-error) CONTINUE_ON_ERROR=true; shift ;;
    --device) DEVICE="$2"; shift 2 ;;
    --cohorts) IFS=',' read -ra COHORTS <<< "$2"; shift 2 ;;
    *) echo "未知参数: $1" >&2; usage 1 ;;
  esac
done

if [[ ${#COHORTS[@]} -eq 0 ]]; then
  COHORTS=(tn3k tn5k thyroidxl pktn)
fi

declare -A CFG_MAP=(
  [tn3k]=config/revision/validation/tn3k.yaml
  [tn5k]=config/revision/validation/tn5k.yaml
  [thyroidxl]=config/revision/validation/thyroidxl.yaml
  [pktn]=config/revision/validation/pktn.yaml
)

cd "${ROOT}"
failures=()

run_pipeline_cohort() {
  local cohort="$1"
  local cfg="${CFG_MAP[$cohort]:-}"
  if [[ -z "${cfg}" || ! -f "${cfg}" ]]; then
    echo ">>> 跳过 ${cohort}: 无配置 ${cfg}" >&2
    failures+=("${cohort}:no_config")
    return 1
  fi
  echo ""
  echo "======== validation pipeline: ${cohort} ========"
  echo "  config: ${cfg}"
  echo "  device: ${DEVICE}"
  set +e
  "${PY}" run_pipeline.py --config "${cfg}" --device "${DEVICE}"
  local rc=$?
  set -e
  if [[ "${rc}" -ne 0 ]]; then
    echo ">>> pipeline 失败 ${cohort} (exit ${rc})" >&2
    failures+=("${cohort}:pipeline_${rc}")
    return "${rc}"
  fi
  return 0
}

if [[ "${SKIP_PIPELINE}" != true ]]; then
  for cohort in "${COHORTS[@]}"; do
    if ! run_pipeline_cohort "${cohort}"; then
      [[ "${CONTINUE_ON_ERROR}" == true ]] || exit 1
    fi
  done
fi

echo ""
echo "======== 合并 validation results ========"
"${PY}" scripts/revision/b8/merge_validation_results.py --out-dir "${VAL_OUT}"

echo ""
echo "======== backfill uncertainty ========"
set +e
"${PY}" scripts/revision/b8/backfill_results_metadata.py \
  --output-dir "${VAL_OUT}" \
  --config "${NHC_CFG}" \
  --label-file "${VAL_OUT}/labels_merged.json"
rc=$?
set -e
if [[ "${rc}" -ne 0 ]]; then
  echo ">>> backfill 失败 (exit ${rc})" >&2
  failures+=("validation:backfill_${rc}")
  [[ "${CONTINUE_ON_ERROR}" == true ]] || exit "${rc}"
fi

echo ""
echo "======== B8 fit（验证集定阈）========"
"${PY}" scripts/revision/b8/run_calibration_abstention.py \
  --fit \
  --val-results "${VAL_OUT}/results.json" \
  --out "${FIT_OUT}" \
  --rule-subset nhc

echo ""
echo "完成。"
echo "  validation results: ${VAL_OUT}/results.json"
echo "  merge manifest:     ${VAL_OUT}/merge_manifest.json"
echo "  thresholds:         ${FIT_OUT}/abstention_thresholds.json"

if [[ "${WITH_COHORT_EVAL}" == true ]]; then
  echo ""
  echo "======== 各测试队列 B8 eval ========"
  "${ROOT}/scripts/revision/b8/run_b8_all_cohorts.sh" --skip-backfill \
    ${CONTINUE_ON_ERROR:+--continue-on-error}
fi

if [[ ${#failures[@]} -gt 0 ]]; then
  echo "部分失败: ${failures[*]}" >&2
  exit 1
fi
