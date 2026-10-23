#!/usr/bin/env bash
# ZJH-8K：按图像 chunk 重跑 Phase 1–2（GPU），写出小 intermediate，再交给 run_b3_zjh8k_chunks.sh。
#
#   pkill -f split_b3_intermediate_chunks   # 若仍在拆 npz，先停
#   DEVICE=cuda ./scripts/revision/b3/zjh/run_zjh8k_reinfer_chunks.sh
#   CHUNK_ONLY=2 DEVICE=cuda ./scripts/revision/b3/zjh/run_zjh8k_reinfer_chunks.sh
#
# 完成后:
#   B3_CHUNK_ROOT=output/ZJH-8K/b3_reinfer SKIP_SPLIT=1 ./scripts/revision/b3/zjh/run_b3_zjh8k_chunks.sh

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
DEVICE="${DEVICE:-cuda}"
CHUNK_SIZE="${CHUNK_SIZE:-1000}"
TOTAL_IMAGES="${TOTAL_IMAGES:-7958}"
CHUNK_ONLY="${CHUNK_ONLY:-}"
BASE_CFG="${ROOT}/config/pipeline_zjh8k_b3.yaml"
REINFER_ROOT="${REINFER_ROOT:-${ROOT}/output/ZJH-8K/b3_reinfer}"
LOG_DIR="${ROOT}/output/ablation/b3/_batch_logs"

export PYTHONUNBUFFERED=1

cd "${ROOT}"
mkdir -p "${LOG_DIR}" "${REINFER_ROOT}"

n_chunks=$(( (TOTAL_IMAGES + CHUNK_SIZE - 1) / CHUNK_SIZE ))

run_chunk() {
  local idx="$1"
  local start=$(( idx * CHUNK_SIZE ))
  local count="${CHUNK_SIZE}"
  if (( start + count > TOTAL_IMAGES )); then
    count=$(( TOTAL_IMAGES - start ))
  fi
  local chunk_name
  chunk_name=$(printf "chunk_%02d" "${idx}")
  if [[ -n "${CHUNK_ONLY}" && "${chunk_name}" != "chunk_${CHUNK_ONLY}" ]]; then
    return 0
  fi

  local out_dir="${REINFER_ROOT}/${chunk_name}"
  local inter_seg="${out_dir}/intermediate/seg/all_datasets.npz"
  if [[ -f "${inter_seg}" ]]; then
    echo ">>> 跳过 ${chunk_name}（已有 intermediate）"
    return 0
  fi

  local tmp_cfg="${LOG_DIR}/pipeline_zjh8k_${chunk_name}.yaml"
  "${PY}" -c "
import yaml
from pathlib import Path
base = yaml.safe_load(Path('${BASE_CFG}').read_text(encoding='utf-8'))
base['pipeline']['data']['start_index'] = ${start}
base['pipeline']['data']['max_images'] = ${count}
base['pipeline']['output']['output_dir'] = '${out_dir}'
Path('${tmp_cfg}').write_text(yaml.dump(base, allow_unicode=True), encoding='utf-8')
"

  local log="${LOG_DIR}/zjh8k_reinfer_${chunk_name}_$(date +%Y%m%d_%H%M%S).log"
  echo ""
  echo "======== 重推 ${chunk_name}: start=${start} n=${count} ========"
  echo "  out: ${out_dir}"
  echo "  log: ${log}"

  "${PY}" run_pipeline.py --config "${tmp_cfg}" --device "${DEVICE}" 2>&1 | tee "${log}"

  "${PY}" -c "
import json
from pathlib import Path
meta = {
    'chunk_index': ${idx},
    'start_index': ${start},
    'end_index': ${start} + ${count},
    'count': ${count},
}
Path('${out_dir}/chunk_meta.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
"
  echo ">>> 完成 ${chunk_name}"
}

for idx in $(seq 0 $(( n_chunks - 1 )) ); do
  run_chunk "${idx}"
done

echo ""
echo "Phase1–2 重推结束。目录: ${REINFER_ROOT}"
echo "下一步: B3_CHUNK_ROOT=${REINFER_ROOT} SKIP_SPLIT=1 ./scripts/revision/b3/zjh/run_b3_zjh8k_chunks.sh"
