#!/usr/bin/env bash
# 将 B6 输出目录下的 intermediate 指到已有主 pipeline Phase 1–2 缓存（避免重复 GPU 推理）
#
# 检查结论（本机）:
#   output/b6/{thyroidxl,zjh8k,ddti_cls}/pipeline_run/intermediate  默认不存在
#   但 for_llm 250 张文件名已落在:
#     output/ThyroidXL/pipeline_run/intermediate     (seg+cls, 250/250 覆盖)
#     output/ZJH-8K/pipeline_run/intermediate        (seg+cls, 250/250)
#     output/DDTI_cls/pipeline_run/intermediate      (仅 cls, 250/250；无 seg)
#
# 用法:
#   bash scripts/revision/b6/link_b6_intermediate_from_main.sh
#   bash scripts/revision/b6/link_b6_intermediate_from_main.sh --dry-run

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
DRY="${1:-}"

link_one() {
  local cohort="$1"
  local rel_src="$2"
  local b6_run="output/b6/${cohort}/pipeline_run"
  local b6_inter="${b6_run}/intermediate"
  local src="${ROOT}/${rel_src}"
  local rel_link="../../../${rel_src#output/}"

  mkdir -p "$b6_run"
  if [[ ! -d "$src/seg" && ! -d "$src/cls" ]]; then
    echo "SKIP $cohort: 源不存在 $src"
    return 1
  fi
  if [[ -e "$b6_inter" && ! -L "$b6_inter" ]]; then
    echo "SKIP $cohort: $b6_inter 已存在且非 symlink（请手动备份后删除）"
    return 1
  fi
  if [[ "$DRY" == "--dry-run" ]]; then
    echo "DRY: ln -sfn $rel_link $b6_inter"
    return 0
  fi
  rm -f "$b6_inter"
  ln -sfn "$rel_link" "$b6_inter"
  echo "OK $cohort -> $rel_src (link: $rel_link)"
}

link_one thyroidxl "output/ThyroidXL/pipeline_run/intermediate"
link_one zjh8k "output/ZJH-8K/pipeline_run/intermediate"
link_one ddti_cls "output/DDTI_cls/pipeline_run/intermediate"

echo ""
echo "完成后请写入 10 例 manifest 并跑稳定性，例如:"
echo "  COHORTS=thyroidxl bash scripts/revision/b6/run_b6_stability_remaining.sh"
echo "（会先 Phase 1–2 若 manifest 缺失；有 symlink 且仅需 10 例时可用 STABILITY_ONLY=1 + 先生成 manifest）"
