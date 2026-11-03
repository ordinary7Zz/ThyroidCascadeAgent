#!/usr/bin/env bash
# 在最新 ZJH-8K 数据上重跑外测推理，并生成 6807 图（剔除 TN3K train dHash H=0）的 B2 cluster-bootstrap CI。
# 对应回信 tab_cls_ext / tab_seg_ext / tab_patient_cls 的 ZJH-8K 列。
#
# ThyroidXAgent 行：仅 dinov3_unet + dinov3_unet_multitask（all_datasets），见 config/revision/b2/zjh8k_dino_primary.yaml
# 监督基线：my_Thyroid_Infer/baseline_export/run_infer_batch.py → ../b2_exports → B2（带 exclude manifest）
# VLM（MedGemma / Qwen3 / GPT-5 / Gemini）：不在 my_Thyroid_Infer 批处理里，默认 SKIP_VLM=1；需另跑 for_llm / 稿面脚本后手工 B2
#
# 用法：
#   DEVICE=cuda bash scripts/revision/b2/run_zjh8k_external_refresh.sh
#   SKIP_AGENT=1 SKIP_BASELINE_INFER=1 bash ...   # 仅重算 B2（已有 results.json + b2_exports）
#   USE_CHUNKS=1 DEVICE=cuda bash ...             # 7958 图 OOM 时用分 chunk 重推（见 scripts/revision/b3/zjh/run_zjh8k_reinfer_chunks.sh）
#
# 环境变量：
#   PYTHON, REPO_ROOT, DATA_ROOT, DEVICE
#   EXCL_MANIFEST   默认 docs/revision/b1/tables/zjh_excl_tn3k_train_dhash0_manifest.json（6807 子集）
#   ZJH_PIPELINE_CFG / ZJH_PIPELINE_OUT
#   EXPORTS_ROOT    默认 ${REPO_ROOT}/../b2_exports
#   INFER_ROOT      默认 ${REPO_ROOT}/../my_Thyroid_Infer

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
cd "$ROOT"

_DEFAULT_PY="/mnt/wangbd8/workspace/envs/thyroid_infer/bin/python"
PY="${PYTHON:-${_DEFAULT_PY}}"
DATA_ROOT="${DATA_ROOT:-/mnt/wangbd8/workspace/DataSets/ThyroidAgent}"
DEVICE="${DEVICE:-cuda}"
EXCL_MANIFEST="${EXCL_MANIFEST:-${ROOT}/docs/revision/b1/tables/zjh_excl_tn3k_train_dhash0_manifest.json}"
ZJH_PIPELINE_CFG="${ZJH_PIPELINE_CFG:-${ROOT}/config/revision/b2/zjh8k_dino_primary.yaml}"
ZJH_PIPELINE_OUT="${ZJH_PIPELINE_OUT:-output/ZJH-8K/pipeline_run}"
EXPORTS_ROOT="${EXPORTS_ROOT:-$(dirname "$ROOT")/b2_exports}"
INFER_ROOT="${INFER_ROOT:-$(dirname "$ROOT")/my_Thyroid_Infer}"
B2_TABLE="${B2_TABLE:-docs/revision/b2/tables/zjh8k_b2_excl_tn3k_h0.json}"
CLUSTER_MAP="${CLUSTER_MAP:-docs/revision/b2/cluster_maps/zjh8k.json}"

SKIP_EXCL_CHECK="${SKIP_EXCL_CHECK:-0}"
SKIP_AGENT="${SKIP_AGENT:-0}"
SKIP_AGENT_B2="${SKIP_AGENT_B2:-0}"
SKIP_BASELINE_INFER="${SKIP_BASELINE_INFER:-0}"
SKIP_BASELINE_B2="${SKIP_BASELINE_B2:-0}"
SKIP_VLM="${SKIP_VLM:-1}"
USE_CHUNKS="${USE_CHUNKS:-0}"

export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-8}"

usage() {
  sed -n '2,22p' "$0" | sed 's/^# //'
  exit "${1:-0}"
}

[[ "${1:-}" == "-h" || "${1:-}" == "--help" ]] && usage 0

if [[ ! -x "$PY" && ! -f "$PY" ]]; then
  echo "Python 不存在: $PY" >&2
  exit 1
fi

echo "======== ZJH-8K 外测刷新 ========"
echo "REPO:          $ROOT"
echo "Python:        $PY"
echo "DATA_ROOT:     $DATA_ROOT"
echo "DEVICE:        $DEVICE"
echo "EXCL:          $EXCL_MANIFEST"
echo "Agent cfg:     $ZJH_PIPELINE_CFG"
echo "Pipeline out:  $ZJH_PIPELINE_OUT"
echo "b2_exports:    $EXPORTS_ROOT"
echo "Infer root:    $INFER_ROOT"
echo ""

# ---------- 0) 剔除名单（1151 张 → 报告 6807） ----------
if [[ "$SKIP_EXCL_CHECK" != "1" ]]; then
  if [[ ! -f "$EXCL_MANIFEST" ]]; then
    echo ">>> 生成 TN3K train ↔ ZJH H=0 剔除 manifest ..."
    "$PY" scripts/revision/b1/export_zjh_excl_tn3k_train_dhash0.py \
      --data-root "$DATA_ROOT" \
      --out "$EXCL_MANIFEST"
  else
    echo ">>> 使用已有 exclude manifest: $EXCL_MANIFEST"
  fi
fi

# ---------- 1) ThyroidXAgent（DINO 主专家）推理 ----------
if [[ "$SKIP_AGENT" != "1" ]]; then
  if [[ ! -f "$ZJH_PIPELINE_CFG" ]]; then
    echo "缺少配置: $ZJH_PIPELINE_CFG" >&2
    exit 1
  fi
  if [[ "$USE_CHUNKS" == "1" ]]; then
    echo ">>> USE_CHUNKS=1：未自动跑 pipeline（7958 图需分 chunk，避免 OOM）。"
    echo "    1) 用 ${ZJH_PIPELINE_CFG} 的数据/单专家权重生成 chunk 配置，或改 run_zjh8k_reinfer_chunks.sh 内 BASE_CFG"
    echo "    2) DEVICE=${DEVICE} ./scripts/revision/b3/zjh/run_zjh8k_reinfer_chunks.sh"
    echo "    3) 合并 intermediate → ${ZJH_PIPELINE_OUT}/intermediate 后:"
    echo "       ${PY} run_pipeline.py --config ${ZJH_PIPELINE_CFG} --device ${DEVICE}"
    echo "    然后: SKIP_AGENT=1 bash $0"
  else
    echo ">>> ThyroidXAgent DINO primary: run_pipeline ..."
    "$PY" run_pipeline.py --config "$ZJH_PIPELINE_CFG" --device "$DEVICE"
    if [[ ! -f "${ROOT}/${ZJH_PIPELINE_OUT}/results.json" ]]; then
      echo "未生成 ${ZJH_PIPELINE_OUT}/results.json" >&2
      exit 1
    fi
  fi
fi

# ---------- 2) ThyroidXAgent B2（6807 子集） ----------
if [[ "$SKIP_AGENT_B2" != "1" ]]; then
  RESULTS="${ROOT}/${ZJH_PIPELINE_OUT}/results.json"
  if [[ ! -f "$RESULTS" ]]; then
    echo "缺少 $RESULTS（先跑 Agent 推理或 SKIP_AGENT=0）" >&2
    exit 1
  fi
  echo ">>> B2 ThyroidXAgent → $B2_TABLE"
  "$PY" scripts/revision/b2/run_b2_cluster_metrics.py \
    --results "$RESULTS" \
    --cluster-map "${ROOT}/${CLUSTER_MAP}" \
    --pipeline-dir "${ROOT}/${ZJH_PIPELINE_OUT}" \
    --gt-mask-dir "${DATA_ROOT}/train_val_test/ZJH-8K/masks" \
    --task both \
    --patient-level \
    --exclude-images "$EXCL_MANIFEST" \
    --out "${ROOT}/${B2_TABLE}" \
    --n-bootstrap "${B2_N_BOOTSTRAP:-1000}" \
    --seed "${B2_SEED:-42}"
fi

# ---------- 3) 监督基线（S3/S4 行，不含 VLM） ----------
if [[ "$SKIP_BASELINE_INFER" != "1" ]]; then
  if [[ ! -d "$INFER_ROOT/baseline_export" ]]; then
    echo "缺少 my_Thyroid_Infer: $INFER_ROOT" >&2
    exit 1
  fi
  echo ">>> 基线推理 zjh8k（transunet, medsam2, medsegx, ultrafedfm, resnet50, repvit, lsnet, ultrafedfm cls）..."
  (
    cd "$INFER_ROOT"
    "$PY" baseline_export/run_infer_batch.py \
      --cohorts zjh8k \
      --skip-existing
  )
fi

if [[ "$SKIP_BASELINE_B2" != "1" ]]; then
  echo ">>> B2 基线（zjh8k* + exclude manifest）..."
  EXPORTS_ROOT="$EXPORTS_ROOT" \
    "$PY" scripts/revision/b2/run_b2_from_export.py \
      --scan-all \
      --exports-root "$EXPORTS_ROOT" \
      --cohort-substr zjh8k \
      --exclude-images "$EXCL_MANIFEST"
fi

# ---------- 4) VLM 基线（表 R3 中 MedGemma 等） ----------
if [[ "$SKIP_VLM" == "1" ]]; then
  echo ""
  echo ">>> SKIP_VLM=1：跳过 MedGemma / Qwen3-VL / GPT-5 / Gemini。"
  echo "    若需与稿面 S4 一致，请在 for_llm 或 b9 脚本产出 zjh8k 逐图预测后，对对应 b2_exports 目录单独 run_b2_from_export.py --exclude-images \"$EXCL_MANIFEST\"。"
else
  echo ">>> VLM：请在本脚本外完成 zjh8k 推理并写入 b2_exports，再运行 run_b2_from_export.py（带 --exclude-images）。"
fi

echo ""
echo "======== 完成 ========"
echo "ThyroidXAgent B2: ${ROOT}/${B2_TABLE}"
echo "基线 B2:          ${ROOT}/docs/revision/b2/tables/baseline_*_zjh8k_*_b2*.json"
echo "下一步：手工将 ZJH 列数值/sync 进 generated/body_*.tex（tab_cls_ext / tab_seg_ext / tab_patient_cls）。"
