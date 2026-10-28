#!/usr/bin/env bash
# 临时：除 tn5k 外各队列 B6 — 10 例 Phase 1–2（无 LLM）+ 5× 稳定性
#
# 默认队列: thyroidxl zjh8k ddti_cls（与表 R9 多队列一致，不含 tn5k）
#
# 前置:
#   export DASHSCOPE_API_KEY=...
#   bash scripts/build_all_test_for_llm.sh
#
# 用法:
#   bash scripts/revision/b6/run_b6_stability_except_tn5k.sh
#   FORCE_REFRESH=1 bash ...     # 清 intermediate/manifest 后重跑
#   STABILITY_ONLY=1 bash ...    # 仅当各队列已有 10 例 intermediate + manifest 时用
#   COHORTS="tn3k thyroidxl" bash ...

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

export COHORTS="${COHORTS:-thyroidxl zjh8k ddti_cls}"
export SKIP_DONE="${SKIP_DONE:-0}"
export REPEATS="${REPEATS:-5}"
export DEVICE="${DEVICE:-cuda}"
export FORCE_REFRESH="${FORCE_REFRESH:-0}"
# 默认跑完整 B6 小段（缺 intermediate 会先 Phase 1–2）；已有缓存则只补稳定性
export STABILITY_ONLY="${STABILITY_ONLY:-0}"

echo "队列（不含 tn5k）: $COHORTS"
echo "STABILITY_ONLY=$STABILITY_ONLY （0=缺缓存则先 10 例 Phase 1–2）"
echo ""

exec bash scripts/revision/b6/run_b6_stability_remaining.sh
