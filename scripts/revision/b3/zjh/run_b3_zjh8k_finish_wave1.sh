#!/usr/bin/env bash
# ZJH-8K B3 波次 1 收尾：补跑 8 chunk static_rule + 合并 6 策略到 output/ablation/b3/zjh8k
#
# 前置：
#   - output/ZJH-8K/b3_reinfer/chunk_* 已齐（run_zjh8k_reinfer_chunks.sh）
#   - zjh8k_chunks 下 fast5 五策略已齐（可先跑过 run_b3_zjh8k_chunks.sh 的 fast5 段）
#
# 用法：
#   ./scripts/revision/b3/zjh/run_b3_zjh8k_finish_wave1.sh
#   DEVICE=cpu nohup ./scripts/revision/b3/zjh/run_b3_zjh8k_finish_wave1.sh \
#     > output/ablation/b3/_batch_logs/zjh8k_finish_wave1_nohup.log 2>&1 &
#   SKIP_STATIC_RULE=1 ./scripts/revision/b3/zjh/run_b3_zjh8k_finish_wave1.sh   # 只 merge

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHUNKS_SH="${SCRIPT_DIR}/run_b3_zjh8k_chunks.sh"
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
PY="${PYTHON:-/mnt/wangbd8/workspace/envs/thyroid_infer/bin/python}"
DEVICE="${DEVICE:-cpu}"
LOG_DIR="${ROOT}/output/ablation/b3/_batch_logs"
SKIP_STATIC_RULE="${SKIP_STATIC_RULE:-0}"

FAST5_MODES="soft_voting,majority,max_confidence,best_single,oracle"
ALL_MODES="${FAST5_MODES},static_rule"

export OMP_NUM_THREADS="${OMP_NUM_THREADS:-8}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-8}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-8}"
export PYTHONUNBUFFERED=1

cd "${ROOT}"
mkdir -p "${LOG_DIR}"

ts="$(date +%Y%m%d_%H%M%S)"

if [[ "${SKIP_STATIC_RULE}" != "1" ]]; then
  echo ">>> [1/2] ZJH-8K static_rule（8 chunk，b3_reinfer）"
  B3_CHUNK_ROOT="${B3_CHUNK_ROOT:-${ROOT}/output/ZJH-8K/b3_reinfer}" \
  SKIP_SPLIT=1 \
  STATIC_RULE_ONLY=1 \
  DEVICE="${DEVICE}" \
  REPO_ROOT="${ROOT}" \
  PYTHON="${PY}" \
  "${CHUNKS_SH}" 2>&1 | tee "${LOG_DIR}/zjh8k_finish_static_rule_${ts}.log"
else
  echo ">>> 跳过 static_rule（SKIP_STATIC_RULE=1）"
fi

echo ""
echo ">>> [2/2] 合并 chunk → output/ablation/b3/zjh8k"
"${PY}" scripts/revision/b3/zjh/merge_b3_chunk_outputs.py \
  --chunks "${ROOT}/output/ablation/b3/zjh8k_chunks" \
  --dest "${ROOT}/output/ablation/b3/zjh8k" \
  --modes "${ALL_MODES}" \
  --summarize

echo ""
echo "ZJH-8K B3 波次 1 收尾完成: ${ROOT}/output/ablation/b3/zjh8k"
