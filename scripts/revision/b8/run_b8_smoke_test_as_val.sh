#!/usr/bin/env bash
# B8 烟雾测试：用各队列 **test** pipeline_run 合并为「伪 validation」定阈，再对各 test 队列 eval。
#
# ⚠️ 仅用于检查输出是否合理；不可写入稿面/回复（存在 test 上 fit 的乐观偏倚）。
# 真 validation 就绪后请用：
#   ./scripts/revision/b8/run_openthyroid_validation_b8.sh
#   ./scripts/revision/b8/run_b8_all_cohorts.sh   # 使用 output/b8/fit/ 下正式阈值
#
# 用法：
#   export PYTHON=/mnt/wangbd8/workspace/envs/thyroid_infer/bin/python
#   ./scripts/revision/b8/run_b8_smoke_test_as_val.sh
#   ./scripts/revision/b8/run_b8_smoke_test_as_val.sh --skip-backfill

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
SMOKE_ROOT="${B8_SMOKE_ROOT:-${ROOT}/output/b8/smoke_test_as_val}"
PSEUDO_VAL="${SMOKE_ROOT}/pseudo_val/results.json"
FIT_OUT="${SMOKE_ROOT}/fit"
EVAL_ROOT="${SMOKE_ROOT}/cohorts"
SKIP_BACKFILL=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      sed -n '2,14p' "$0" | sed 's/^# //'
      exit 0
      ;;
    --skip-backfill) SKIP_BACKFILL=true; shift ;;
    *) echo "未知参数: $1" >&2; exit 1 ;;
  esac
done

# 内部四队列 test（与稿面 validation 来源一致，但这里是 test split）
declare -A RESULTS=(
  [tn3k]="${ROOT}/output/TN3K/pipeline_run/results.json"
  [tn5k]="${ROOT}/output/TN5K/pipeline_run/results.json"
  [thyroidxl]="${ROOT}/output/ThyroidXL/pipeline_run/results.json"
  [pktn]="${ROOT}/output/PKTN/pipeline_run/results.json"
)
declare -A CFG=(
  [tn3k]=config/b3/tn3k.yaml
  [tn5k]=config/b3/tn5k.yaml
  [thyroidxl]=config/b3/thyroidxl.yaml
  [pktn]=config/b3/pktn.yaml
)

cd "${ROOT}"
mkdir -p "${SMOKE_ROOT}/pseudo_val" "${FIT_OUT}" "${EVAL_ROOT}"

echo "======== B8 smoke：backfill（伪 val 来源队列）========"
if [[ "${SKIP_BACKFILL}" != true ]]; then
  for key in tn3k tn5k thyroidxl pktn; do
    out_dir="$(dirname "${RESULTS[$key]}")"
    if [[ ! -f "${RESULTS[$key]}" ]]; then
      echo ">>> 跳过 backfill ${key}: 无 results.json" >&2
      continue
    fi
    echo ">>> backfill ${key}"
    "${PY}" scripts/revision/b8/backfill_results_metadata.py \
      --output-dir "${out_dir}" \
      --config "${CFG[$key]}"
  done
fi

export ROOT SMOKE_ROOT PSEUDO_VAL

echo ""
echo "======== 合并 test → 伪 validation ========"
"${PY}" - <<'PY'
import json
from pathlib import Path
import os

root = Path(os.environ["ROOT"])
parts = [
    ("tn3k", root / "output/TN3K/pipeline_run/results.json"),
    ("tn5k", root / "output/TN5K/pipeline_run/results.json"),
    ("thyroidxl", root / "output/ThyroidXL/pipeline_run/results.json"),
    ("pktn", root / "output/PKTN/pipeline_run/results.json"),
]
merged = []
manifest = []
for name, path in parts:
    if not path.is_file():
        raise SystemExit(f"缺少 {name}: {path}")
    rows = json.loads(path.read_text(encoding="utf-8"))
    for r in rows:
        merged.append({**r, "smoke_pseudo_val_cohort": name})
    manifest.append({"cohort": name, "n": len(rows), "path": str(path)})
out = Path(os.environ["PSEUDO_VAL"])
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
meta = Path(os.environ["SMOKE_ROOT"]) / "pseudo_val/merge_manifest.json"
meta.write_text(
    json.dumps(
        {
            "warning": "SMOKE ONLY: test splits used as pseudo-validation for B8 fit",
            "n_total": len(merged),
            "parts": manifest,
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
print(f"n_pseudo_val={len(merged)} -> {out}")
PY

echo ""
echo "======== B8 fit（伪 validation / 实为 test）========"
"${PY}" scripts/revision/b8/run_calibration_abstention.py \
  --fit \
  --val-results "${PSEUDO_VAL}" \
  --out "${FIT_OUT}" \
  --rule-subset nhc

echo ""
echo "======== B8 eval（各 test 队列）========"
export B8_THRESHOLDS="${FIT_OUT}/abstention_thresholds.json"
export B8_EVAL_ROOT="${EVAL_ROOT}"
"${ROOT}/scripts/revision/b8/run_b8_all_cohorts.sh" --skip-backfill \
  --cohorts tn3k,tn5k,thyroidxl,zjh8k,rjh7k,ddti_seg,ddti_cls,pktn,sample \
  --continue-on-error

echo ""
echo "Smoke 完成（勿用于定稿）。"
echo "  伪 val:     ${PSEUDO_VAL}"
echo "  阈值:       ${FIT_OUT}/abstention_thresholds.json"
echo "  各队列 eval: ${EVAL_ROOT}/<cohort>/abstention_eval.json"
