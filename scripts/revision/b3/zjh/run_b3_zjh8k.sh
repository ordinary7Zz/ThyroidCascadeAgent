#!/usr/bin/env bash
# ZJH-8K B3 波次 1（bundle + 整包预加载，见 config/b3/zjh8k.yaml bundle_lazy_seg_min_images）。
#
# 默认分两趟扫图（fast5 → static_rule），避免单次 wave1 在内存中攒 6 套全队列 mask 导致 OOM（exit 137）。
#
# 前置：output/ZJH-8K/pipeline_run/intermediate 已齐。
#
# 用法：
#   ./scripts/revision/b3/zjh/run_b3_zjh8k.sh
#   nohup ./scripts/revision/b3/zjh/run_b3_zjh8k.sh > output/ablation/b3/_batch_logs/zjh8k_nohup.log 2>&1 &
#   FAST5_ONLY=1 ./scripts/revision/b3/zjh/run_b3_zjh8k.sh       # 只跑 fast5
#   STATIC_RULE_ONLY=1 ./scripts/revision/b3/zjh/run_b3_zjh8k.sh # 只补 static_rule（fast5 已完）
#   WAVE1_ONE_SHOT=1 ./scripts/revision/b3/zjh/run_b3_zjh8k.sh   # 旧行为：单次 --preset wave1（易 OOM，不推荐）
#   DEVICE=cuda ./scripts/revision/b3/zjh/run_b3_zjh8k.sh
#
# 环境：REPO_ROOT、PYTHON（默认 thyroid_infer；勿用 sklearn161 若 NFS 上解释器起不来）、DEVICE（默认 cpu）

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
_DEFAULT_PY="/mnt/wangbd8/workspace/envs/thyroid_infer/bin/python"
PY="${PYTHON:-${_DEFAULT_PY}}"
DEVICE="${DEVICE:-cpu}"

export PYTHONUNBUFFERED=1
LOG_DIR="${ROOT}/output/ablation/b3/_batch_logs"
CFG="${ROOT}/config/b3/zjh8k.yaml"
FAST5_ONLY="${FAST5_ONLY:-0}"
STATIC_RULE_ONLY="${STATIC_RULE_ONLY:-0}"
WAVE1_ONE_SHOT="${WAVE1_ONE_SHOT:-0}"

FAST5_MODES="soft_voting,majority,max_confidence,best_single,oracle"

export OMP_NUM_THREADS="${OMP_NUM_THREADS:-8}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-8}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-8}"

usage() {
  sed -n '2,16p' "$0" | sed 's/^# //'
  exit "${1:-0}"
}

run_batch() {
  local label="$1"
  local logfile="$2"
  shift 2

  echo ""
  echo "======== ${label} ========"
  echo "  log: ${logfile}"

  set +e
  "${PY}" scripts/revision/b3/run_b3_batch.py "$@" 2>&1 | tee "${logfile}"
  local rc=${PIPESTATUS[0]}
  set -e

  if [[ "${rc}" -ne 0 ]]; then
    echo ">>> 失败: ${label} (exit ${rc})" >&2
    return "${rc}"
  fi
  echo ">>> 完成: ${label}"
  return 0
}

[[ "${1:-}" == "-h" || "${1:-}" == "--help" ]] && usage 0

if [[ ! -f "${CFG}" ]]; then
  echo "缺少配置: ${CFG}" >&2
  exit 1
fi
if [[ ! -x "${PY}" && ! -f "${PY}" ]]; then
  echo "Python 不存在: ${PY}" >&2
  exit 1
fi

if ! timeout 20 "${PY}" -c "print('python_startup_ok')" >/dev/null 2>&1; then
  echo "Python 无法在 20s 内启动（NFS 上 env 常会卡 D 状态）: ${PY}" >&2
  echo "建议: PYTHON=${_DEFAULT_PY} ./scripts/revision/b3/zjh/run_b3_zjh8k.sh" >&2
  exit 1
fi

if [[ "${FAST5_ONLY}" == "1" && "${STATIC_RULE_ONLY}" == "1" ]]; then
  echo "不能同时设置 FAST5_ONLY=1 与 STATIC_RULE_ONLY=1" >&2
  exit 1
fi

mkdir -p "${LOG_DIR}"
ts="$(date +%Y%m%d_%H%M%S)"

echo "REPO:   ${ROOT}"
echo "Python: ${PY}"
echo "DEVICE: ${DEVICE}"
echo "config: ${CFG}"
echo "logs:   ${LOG_DIR}/zjh8k_*_${ts}.log"
echo ""

cd "${ROOT}"

common_args=(
  --config "${CFG}"
  --force-phase3
  --device "${DEVICE}"
)

if [[ "${WAVE1_ONE_SHOT}" == "1" ]]; then
  echo "⚠️  WAVE1_ONE_SHOT=1：单次 wave1 bundle（大队列可能 OOM exit 137）"
  run_batch "ZJH wave1 one-shot" "${LOG_DIR}/zjh8k_wave1_${ts}.log" \
    "${common_args[@]}" --preset wave1 --summarize || exit $?
elif [[ "${STATIC_RULE_ONLY}" == "1" ]]; then
  run_batch "ZJH static_rule" "${LOG_DIR}/zjh8k_static_rule_${ts}.log" \
    "${common_args[@]}" --modes static_rule --summarize || exit $?
elif [[ "${FAST5_ONLY}" == "1" ]]; then
  run_batch "ZJH fast5" "${LOG_DIR}/zjh8k_fast5_${ts}.log" \
    "${common_args[@]}" --modes "${FAST5_MODES}" --summarize || exit $?
else
  echo "模式: 默认 wave1 分两趟（fast5 → static_rule，降低峰值内存）"
  run_batch "ZJH fast5" "${LOG_DIR}/zjh8k_fast5_${ts}.log" \
    "${common_args[@]}" --modes "${FAST5_MODES}" --no-summarize || exit $?
  run_batch "ZJH static_rule" "${LOG_DIR}/zjh8k_static_rule_${ts}.log" \
    "${common_args[@]}" --modes static_rule --summarize || exit $?
fi

echo ""
echo "ZJH-8K B3 完成。结果: output/ablation/b3/zjh8k/"
