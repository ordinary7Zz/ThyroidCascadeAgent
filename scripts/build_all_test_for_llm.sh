#!/usr/bin/env bash
# 为 LLM 路由实验批量构建 test_for_llm 子集（n=250；源样本数 <=250 则整集复制）。
# DDTI 分两套：分割 all_seg（无 label）、分类 DDTI_Classification/all（images_processed，无 mask）。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${PYTHON:-python3}"
N=250
SEED=42
# 分层字段；输出目录为 test_for_llm_${LABEL_KEY} 或 <split>_for_llm_${LABEL_KEY}
LABEL_KEY="${LABEL_KEY:-malignancy}"
DATA_ROOT="/mnt/wangbd8/workspace/DataSets/ThyroidAgent"

run_subset() {
  local name="$1"
  shift
  echo ""
  echo "======== ${name} (label-key=${LABEL_KEY}) ========"
  "${PY}" "${ROOT}/scripts/build_test_for_llm.py" "$@" \
    --n "${N}" --seed "${SEED}" --label-key "${LABEL_KEY}" || true
}

# TN3K / TN5K / ThyroidXL：标准 test/images + test/masks + *_test_label.json
run_subset "TN3K" \
  --src "${DATA_ROOT}/train_val_test/TN3K/test"

run_subset "TN5K" \
  --src "${DATA_ROOT}/train_val_test/TN5K/test"

run_subset "ThyroidXL" \
  --src "${DATA_ROOT}/train_val_test/ThyroidXL/test"

# PKTN：test/；label 无 malignancy 字段 → 脚本内随机抽样（非分层）
run_subset "PKTN" \
  --src "${DATA_ROOT}/train_val_test/PKTN/test" \
  --label-file PKTN_test_label.json

# ZJH-8K：队列根目录
run_subset "ZJH-8K" \
  --src "${DATA_ROOT}/train_val_test/ZJH-8K" \
  --label-file ZJH-8K_BM_labels.json

# RJH-7K：image/ + mask/（非 images/masks）
run_subset "RJH-7K" \
  --src "${DATA_ROOT}/augtrain_PNG" \
  --images-dir image \
  --masks-dir mask

# DDTI 分割：all_seg，无 label
run_subset "DDTI_seg" \
  --src "${DATA_ROOT}/train_val_test/DDTI/all_seg" \
  --images-dir images \
  --masks-dir masks

# DDTI 分类：images_processed，无 mask（仓库内目录名为 images_processed）
run_subset "DDTI_cls" \
  --src "${DATA_ROOT}/train_val_test/DDTI_Classification/all" \
  --images-dir images_processed \
  --no-masks \
  --label-file DDTI_Classification_test_label.json

echo ""
echo "全部任务已调度完成。输出见各队列旁 test_for_llm_${LABEL_KEY} 或 <split>_for_llm_${LABEL_KEY} 目录。"
