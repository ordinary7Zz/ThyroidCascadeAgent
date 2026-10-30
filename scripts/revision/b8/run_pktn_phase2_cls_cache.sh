#!/usr/bin/env bash
# 为 PKTN 补写 Phase 2 分类 intermediate（B8 送复核用），不重跑 Phase 3–5。
#
# 背景：pktn.yaml 默认 run_classification=false，intermediate/cls 为空 →
# backfill 得到 margin=0 → 送复核 100%。RJH 因留有 cls 缓存而正常。
#
# 前置：output/PKTN/pipeline_run/intermediate/seg/*.npz 已存在（当前 B3 分割跑数）。
# 后置：backfill uncertainty + 用正式 validation 阈值 eval pktn。
#
# 用法：
#   export PYTHON=/mnt/wangbd8/workspace/envs/thyroid_infer/bin/python
#   export CUDA_VISIBLE_DEVICES=0
#   ./scripts/revision/b8/run_pktn_phase2_cls_cache.sh
#   ./scripts/revision/b8/run_pktn_phase2_cls_cache.sh --skip-pipeline   # 仅 backfill+eval

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
PY="${PYTHON:-python3}"
CFG_B3="${ROOT}/config/revision/b3/pktn.yaml"
CFG_TMP="${ROOT}/output/PKTN/_pktn_phase2_for_b8.yaml"
OUT_DIR="${ROOT}/output/PKTN/pipeline_run"
THRESH="${B8_THRESHOLDS:-${ROOT}/output/b8/fit/abstention_thresholds.json}"
EVAL_OUT="${ROOT}/output/b8/cohorts/pktn"
SKIP_PIPELINE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      sed -n '2,16p' "$0" | sed 's/^# //'
      exit 0
      ;;
    --skip-pipeline) SKIP_PIPELINE=true; shift ;;
    *) echo "未知参数: $1" >&2; exit 1 ;;
  esac
done

cd "${ROOT}"

if [[ "${SKIP_PIPELINE}" != true ]]; then
  echo ">>> 生成临时 config（run_classification=true，其余同 pktn.yaml）"
  ROOT="${ROOT}" "${PY}" - <<'PY'
import copy
import os
from pathlib import Path
import yaml

root = Path(os.environ["ROOT"])
src = root / "config/revision/b3/pktn.yaml"
dst = root / "output/PKTN/_pktn_phase2_for_b8.yaml"
with open(src, encoding="utf-8") as f:
    cfg = yaml.safe_load(f)
cfg = copy.deepcopy(cfg)
cfg.setdefault("pipeline", {})["run_classification"] = True
dst.parent.mkdir(parents=True, exist_ok=True)
with open(dst, "w", encoding="utf-8") as f:
    yaml.dump(cfg, f, allow_unicode=True, sort_keys=False)
print("wrote", dst)
PY

  echo ">>> Phase 1–2 only（--stop-after-phase2；已有 seg npz 会跳过）"
  "${PY}" run_pipeline.py \
    --config "${CFG_TMP}" \
    --device cuda \
    --stop-after-phase2

  n_cls="$(find "${OUT_DIR}/intermediate/cls" -maxdepth 1 -name '*.json' 2>/dev/null | wc -l)"
  if [[ "${n_cls}" -lt 1 ]]; then
    echo "错误: intermediate/cls 仍无 json，请检查 Phase 2 日志" >&2
    exit 1
  fi
  echo ">>> cls 缓存文件数: ${n_cls}"
fi

echo ">>> backfill uncertainty"
"${PY}" scripts/revision/b8/backfill_results_metadata.py \
  --output-dir "${OUT_DIR}" \
  --config "${CFG_B3}"

if [[ ! -f "${THRESH}" ]]; then
  echo "错误: 缺少正式阈值 ${THRESH}；请先 run_openthyroid_validation_b8.sh + fit" >&2
  exit 1
fi

echo ">>> B8 eval（正式 validation 阈值）"
mkdir -p "${EVAL_OUT}"
"${PY}" scripts/revision/b8/run_calibration_abstention.py \
  --eval \
  --test-results "${OUT_DIR}/results.json" \
  --thresholds "${THRESH}" \
  --out "${EVAL_OUT}" \
  --rule-subset nhc

echo ">>> 完成。查看 ${EVAL_OUT}/abstention_eval.json"
