#!/usr/bin/env bash
# RJH-7K B3 波次 1 全流程：fast5 → static_rule（8 chunk，task=seg）→ 合并
#
# 前置：output/RJH-7K/b3_reinfer/chunk_* 已齐（run_rjh7k_reinfer_chunks.sh）
#
# 用法：
#   ./scripts/revision/b3/rjh/run_b3_rjh7k_wave1.sh
#   DEVICE=cpu nohup ./scripts/revision/b3/rjh/run_b3_rjh7k_wave1.sh \
#     > output/ablation/b3/_batch_logs/rjh7k_wave1_nohup.log 2>&1 &
#   SKIP_FAST5=1 ./scripts/revision/b3/rjh/run_b3_rjh7k_wave1.sh        # 仅 static_rule + merge
#   SKIP_STATIC_RULE=1 SKIP_FAST5=1 ...                                   # 仅 merge

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHUNKS_SH="${SCRIPT_DIR}/run_b3_rjh7k_chunks.sh"
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
SKIP_FAST5="${SKIP_FAST5:-0}"
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

if [[ "${SKIP_FAST5}" != "1" ]]; then
  echo ">>> [1/3] RJH-7K fast5（8 chunk）"
  FAST5_ONLY=1 \
  DEVICE="${DEVICE}" \
  REPO_ROOT="${ROOT}" \
  PYTHON="${PY}" \
  "${CHUNKS_SH}" 2>&1 | tee "${LOG_DIR}/rjh7k_wave1_fast5_${ts}.log"
else
  echo ">>> 跳过 fast5（SKIP_FAST5=1）"
fi

if [[ "${SKIP_STATIC_RULE}" != "1" ]]; then
  echo ""
  echo ">>> [2/3] RJH-7K static_rule（8 chunk）"
  STATIC_RULE_ONLY=1 \
  DEVICE="${DEVICE}" \
  REPO_ROOT="${ROOT}" \
  PYTHON="${PY}" \
  "${CHUNKS_SH}" 2>&1 | tee "${LOG_DIR}/rjh7k_wave1_static_rule_${ts}.log"
else
  echo ">>> 跳过 static_rule（SKIP_STATIC_RULE=1）"
fi

echo ""
echo ">>> [3/3] 合并 chunk → output/ablation/b3/rjh7k"
"${PY}" scripts/revision/b3/zjh/merge_b3_chunk_outputs.py \
  --chunks "${ROOT}/output/ablation/b3/rjh7k_chunks" \
  --dest "${ROOT}/output/ablation/b3/rjh7k" \
  --modes "${ALL_MODES}" \
  --summarize

echo ""
echo "RJH-7K B3 波次 1 完成: ${ROOT}/output/ablation/b3/rjh7k"
