#!/usr/bin/env bash
# B6 批跑：每队列仅 10 例 Phase 1–2（无 LLM）+ 同 10 例 5× LLM 稳定性
#
# 前置:
#   export DASHSCOPE_API_KEY=...
#   bash scripts/build_all_test_for_llm.sh
#
# 用法:
#   bash scripts/revision/b6/run_b6_stability_remaining.sh
#   COHORTS="tn5k thyroidxl" SAMPLE_MODE=first bash ...
#   FORCE_REFRESH=1 bash ...   # 删除旧 intermediate（曾跑 250 张时必须）
#
# 子集写在 config/revision/b6/<cohort>.yaml → pipeline.data.stability_sample
# 也可用环境变量覆盖: SAMPLE_SIZE SAMPLE_SEED SAMPLE_MODE

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
DEVICE="${DEVICE:-cuda}"
REPEATS="${REPEATS:-5}"
SKIP_DONE="${SKIP_DONE:-1}"
STABILITY_ONLY="${STABILITY_ONLY:-0}"
FORCE_REFRESH="${FORCE_REFRESH:-0}"

SAMPLE_SIZE="${SAMPLE_SIZE:-}"
SAMPLE_SEED="${SAMPLE_SEED:-}"
SAMPLE_MODE="${SAMPLE_MODE:-}"

COHORTS="${COHORTS:-tn5k thyroidxl zjh8k ddti_cls}"

if [[ -z "${DASHSCOPE_API_KEY:-}" ]]; then
  echo "ERROR: 请 export DASHSCOPE_API_KEY" >&2
  exit 1
fi

need_pipeline() {
  local out="$1"
  local inter="$out/intermediate"
  if [[ -d "$inter/seg" ]] && compgen -G "$inter/seg/*.npz" >/dev/null; then
    return 0
  fi
  if [[ -d "$inter/cls" ]] && compgen -G "$inter/cls/*.json" >/dev/null; then
    return 0
  fi
  return 1
}

run_one() {
  local cohort="$1"
  local cfg="config/revision/b6/${cohort}.yaml"
  local out="output/b6/${cohort}/pipeline_run"
  local -a pargs sargs

  pargs=(--stop-after-phase2)
  sargs=()
  if [[ -n "$SAMPLE_SIZE" ]]; then
    pargs+=(--sample-size "$SAMPLE_SIZE")
    sargs+=(--sample-size "$SAMPLE_SIZE")
  fi
  if [[ -n "$SAMPLE_SEED" ]]; then
    pargs+=(--sample-seed "$SAMPLE_SEED")
    sargs+=(--sample-seed "$SAMPLE_SEED")
  fi
  if [[ -n "$SAMPLE_MODE" ]]; then
    pargs+=(--sample-mode "$SAMPLE_MODE")
    sargs+=(--sample-mode "$SAMPLE_MODE")
  fi

  if [[ ! -f "$cfg" ]]; then
    echo "SKIP $cohort: 无配置 $cfg"
    return 0
  fi

  if [[ "$SKIP_DONE" == "1" && -f "$out/stability_summary.json" ]]; then
    echo "SKIP $cohort: 已有 stability_summary.json (SKIP_DONE=1)"
    return 0
  fi

  if [[ "$FORCE_REFRESH" == "1" ]]; then
    echo "FORCE_REFRESH: 清除 $out/intermediate 与 manifest"
    rm -rf "$out/intermediate" "$out/stability_case_manifest.json"
  fi

  echo ""
  echo "============================================================"
  echo "B6 cohort: $cohort"
  echo "  config: $cfg"
  echo "  out:    $out"
  echo "============================================================"

  if [[ "$STABILITY_ONLY" != "1" ]]; then
    if need_pipeline "$out"; then
      echo "  intermediate 已存在，跳过 Phase 1–2"
      if [[ ! -f "$out/stability_case_manifest.json" ]]; then
        echo "  ⚠️  无 stability_case_manifest.json（可能是旧版 250 张缓存）"
        echo "      建议: FORCE_REFRESH=1 bash scripts/revision/b6/run_b6_stability_remaining.sh"
      fi
    else
      echo "== Phase 1–2 only（10 例专家推理，无 LLM）=="
      "$PYTHON" run_pipeline.py --config "$cfg" --device "$DEVICE" "${pargs[@]}"
    fi
  else
    if ! need_pipeline "$out"; then
      echo "ERROR: STABILITY_ONLY=1 但缺少 intermediate" >&2
      exit 1
    fi
  fi

  echo "== 5× LLM 稳定性（仅 manifest 内病例）=="
  if ((${#sargs[@]})); then
    "$PYTHON" run_routing_stability.py \
      --config "$cfg" \
      --output-dir "$out" \
      --repeats "$REPEATS" \
      --device "$DEVICE" \
      "${sargs[@]}"
  else
    "$PYTHON" run_routing_stability.py \
      --config "$cfg" \
      --output-dir "$out" \
      --repeats "$REPEATS" \
      --device "$DEVICE"
  fi

  echo "✓ $cohort → $out/stability_summary.json"
}

echo "Repo: $ROOT"
echo "COHORTS=$COHORTS | DEVICE=$DEVICE | REPEATS=$REPEATS"
echo "子集默认见各 yaml stability_sample；覆盖: SAMPLE_SIZE/SEED/MODE"
echo "SKIP_DONE=$SKIP_DONE | FORCE_REFRESH=$FORCE_REFRESH | STABILITY_ONLY=$STABILITY_ONLY"

for c in $COHORTS; do
  run_one "$c"
done

echo ""
echo "完成。LLM 调用量 ≈ 每队列 (10 × ${REPEATS} × 分割路由) + Path B 分类重复。"
