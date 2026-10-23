#!/usr/bin/env bash
# ZJH-8K B3：按 chunk 小 intermediate 跑（~40G cgroup，共享 NFS，无需本机盘）。
#
# 1) 一次性切分（若尚未有 intermediate_chunks）:
#    python scripts/revision/b3/zjh/split_b3_intermediate_chunks.py \\
#      --source output/ZJH-8K/pipeline_run/intermediate \\
#      --dest output/ZJH-8K/pipeline_run/intermediate_chunks \\
#      --chunk-size 1000
#
# 2) 本脚本：逐 chunk 跑 fast5，再逐 chunk 跑 static_rule，最后 merge。
#
#   CHUNK_SIZE=1000 ./scripts/revision/b3/zjh/run_b3_zjh8k_chunks.sh
#   CHUNK_ONLY=03 ./scripts/revision/b3/zjh/run_b3_zjh8k_chunks.sh   # 只跑 chunk_03
#   SKIP_SPLIT=1 ./scripts/revision/b3/zjh/run_b3_zjh8k_chunks.sh
#   B3_CHUNK_ROOT=output/ZJH-8K/b3_reinfer SKIP_SPLIT=1 ./scripts/revision/b3/zjh/run_b3_zjh8k_chunks.sh  # 重推后

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
PY="${PYTHON:-/mnt/wangbd8/workspace/envs/thyroid_infer/bin/python}"
DEVICE="${DEVICE:-cpu}"
CHUNK_SIZE="${CHUNK_SIZE:-1000}"
SKIP_SPLIT="${SKIP_SPLIT:-0}"
CHUNK_ONLY="${CHUNK_ONLY:-}"
FAST5_ONLY="${FAST5_ONLY:-0}"
STATIC_RULE_ONLY="${STATIC_RULE_ONLY:-0}"

SRC_INTER="${ROOT}/output/ZJH-8K/pipeline_run/intermediate"
CHUNK_INTER="${B3_CHUNK_ROOT:-${ROOT}/output/ZJH-8K/pipeline_run/intermediate_chunks}"
OUT_CHUNKS="${ROOT}/output/ablation/b3/zjh8k_chunks"
OUT_FINAL="${ROOT}/output/ablation/b3/zjh8k"
CFG="${ROOT}/config/b3/zjh8k.yaml"
LOG_DIR="${ROOT}/output/ablation/b3/_batch_logs"

FAST5_MODES="soft_voting,majority,max_confidence,best_single,oracle"
ALL_MODES="${FAST5_MODES},static_rule"

export OMP_NUM_THREADS="${OMP_NUM_THREADS:-8}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-8}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-8}"
export PYTHONUNBUFFERED=1

cd "${ROOT}"
mkdir -p "${LOG_DIR}" "${OUT_CHUNKS}"

if [[ "${SKIP_SPLIT}" != "1" && ! -d "${CHUNK_INTER}/chunk_00/seg" && ! -d "${CHUNK_INTER}/chunk_00/intermediate/seg" ]]; then
  echo ">>> 切分 intermediate → ${CHUNK_INTER}"
  "${PY}" scripts/revision/b3/zjh/split_b3_intermediate_chunks.py \
    --source "${SRC_INTER}" \
    --dest "${CHUNK_INTER}" \
    --chunk-size "${CHUNK_SIZE}"
fi

mapfile -t CHUNK_DIRS < <(ls -d "${CHUNK_INTER}"/chunk_* 2>/dev/null | sort)
if [[ ${#CHUNK_DIRS[@]} -eq 0 ]]; then
  echo "无 chunk 目录: ${CHUNK_INTER}" >&2
  exit 1
fi

_chunk_shared_dir() {
  local chunk_dir="$1"
  if [[ -d "${chunk_dir}/intermediate/seg" ]]; then
    echo "${chunk_dir}/intermediate"
  else
    echo "${chunk_dir}"
  fi
}

run_one_chunk() {
  local chunk_dir="$1"
  local label="$2"
  local modes="$3"
  local summarize_flag="$4"
  local base
  base="$(basename "${chunk_dir}")"
  if [[ -n "${CHUNK_ONLY}" && "${base}" != "chunk_${CHUNK_ONLY}" ]]; then
    return 0
  fi

  local start count
  if [[ -f "${chunk_dir}/chunk_meta.json" ]]; then
    start="$(python3 -c "import json; print(json.load(open('${chunk_dir}/chunk_meta.json'))['start_index'])")"
    count="$(python3 -c "import json; print(json.load(open('${chunk_dir}/chunk_meta.json'))['count'])")"
  else
    local idx="${base#chunk_}"
    start=$((10#${idx} * CHUNK_SIZE))
    count="${CHUNK_SIZE}"
  fi
  local shared
  shared="$(_chunk_shared_dir "${chunk_dir}")"

  local log="${LOG_DIR}/zjh8k_${base}_${label}_$(date +%Y%m%d_%H%M%S).log"
  echo ""
  echo "======== ${base} start_index=${start} n=${count} ${label} ========"
  echo "  shared: ${shared}"
  echo "  log: ${log}"

  local sum_args=(--no-summarize)
  if [[ "${summarize_flag}" == "1" ]]; then
    sum_args=(--summarize)
  fi

  "${PY}" scripts/revision/b3/run_b3_batch.py \
    --config "${CFG}" \
    --shared-intermediate "${shared}" \
    --output-root "${OUT_CHUNKS}/${base}" \
    --start-index "${start}" \
    --max-images "${count}" \
    --modes "${modes}" \
    --force-phase3 \
    --device "${DEVICE}" \
    "${sum_args[@]}" \
    2>&1 | tee "${log}"
}

if [[ "${STATIC_RULE_ONLY}" == "1" ]]; then
  for d in "${CHUNK_DIRS[@]}"; do
    run_one_chunk "${d}" "static_rule" "static_rule" "0"
  done
elif [[ "${FAST5_ONLY}" == "1" ]]; then
  for d in "${CHUNK_DIRS[@]}"; do
    run_one_chunk "${d}" "fast5" "${FAST5_MODES}" "0"
  done
else
  for d in "${CHUNK_DIRS[@]}"; do
    run_one_chunk "${d}" "fast5" "${FAST5_MODES}" "0"
  done
  for d in "${CHUNK_DIRS[@]}"; do
    run_one_chunk "${d}" "static_rule" "static_rule" "0"
  done
fi

if [[ -z "${CHUNK_ONLY}" && "${STATIC_RULE_ONLY}" != "1" && "${FAST5_ONLY}" != "1" ]]; then
  echo ""
  echo ">>> 合并 chunk 输出 → ${OUT_FINAL}"
  "${PY}" scripts/revision/b3/zjh/merge_b3_chunk_outputs.py \
    --chunks "${OUT_CHUNKS}" \
    --dest "${OUT_FINAL}" \
    --modes "${ALL_MODES}" \
    --summarize
elif [[ "${FAST5_ONLY}" == "1" ]]; then
  "${PY}" scripts/revision/b3/zjh/merge_b3_chunk_outputs.py \
    --chunks "${OUT_CHUNKS}" \
    --dest "${OUT_FINAL}" \
    --modes "${FAST5_MODES}" \
    --summarize
fi

echo "完成。分 chunk 输出: ${OUT_CHUNKS}；合并结果: ${OUT_FINAL}"
