#!/usr/bin/env bash
# R2.20(b): 对已缓存的 pipeline_run/selected_masks.npz 批量统计 GT 等价径 <50 px 子集 vs selected mask。
#
# 当前本机可直接计算的队列（需同时存在 selected_masks.npz 与 GT mask 目录）：
#   TN3K, TN5K, ThyroidXL, RJH-7K, ZJH-8K, DDTI_seg, PKTN
# 无主 pipeline 缓存时跳过（例如 NHC-MISD-TUS）。
#
# 用法：
#   ./scripts/revision/b11/run_r2_20_small_nodules_all.sh
#   MM_PER_PIXEL=0.12 ./scripts/revision/b11/run_r2_20_small_nodules_all.sh
#   PYTHON=/path/to/python ./scripts/revision/b11/run_r2_20_small_nodules_all.sh
#
# 输出：
#   docs/revision/b11_b12/tables/r2_20_<cohort>.json
#   docs/revision/b11_b12/tables/R2_20_SUMMARY.md  （由 JSON 汇总生成）

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

REPO_ROOT="${REPO_ROOT:-$(_find_revision_repo_root)}"
cd "$REPO_ROOT"

PYTHON="${PYTHON:-python3}"
DATA_ROOT="${DATA_ROOT:-/mnt/wangbd8/workspace/DataSets/ThyroidAgent}"
OUT_DIR="${OUT_DIR:-docs/revision/b11_b12/tables}"
MM_PER_PIXEL="${MM_PER_PIXEL:-0.1}"
MAX_DIAMETER_MM="${MAX_DIAMETER_MM:-5.0}"

mkdir -p "$OUT_DIR"

# cohort_id|gt_mask_dir|output_subdir (under output/)
COHORTS=(
  "TN3K|${DATA_ROOT}/train_val_test/TN3K/test/masks|TN3K"
  "TN5K|${DATA_ROOT}/train_val_test/TN5K/test/masks|TN5K"
  "ThyroidXL|${DATA_ROOT}/train_val_test/ThyroidXL/test/masks|ThyroidXL"
  "RJH-7K|${DATA_ROOT}/augtrain_PNG/mask|RJH-7K"
  "ZJH-8K|${DATA_ROOT}/train_val_test/ZJH-8K/masks|ZJH-8K"
  "DDTI_seg|${DATA_ROOT}/train_val_test/DDTI/all_seg/masks|DDTI_seg"
  "PKTN|${DATA_ROOT}/train_val_test/PKTN/test/masks|PKTN"
)

# JSON 文件名（与历史 r2_20_zjh8k.json 等保持一致）
json_slug() {
  case "$1" in
    TN3K) echo tn3k ;;
    TN5K) echo tn5k ;;
    ThyroidXL) echo thyroidxl ;;
    RJH-7K) echo rjh7k ;;
    ZJH-8K) echo zjh8k ;;
    DDTI_seg) echo ddti_seg ;;
    PKTN) echo pktn ;;
    *) echo "$1" | tr '[:upper:]' '[:lower:]' | tr '-' '_' ;;
  esac
}

ran=0
skipped=0

echo "=== R2.20 small-nodule analysis (primary: GT equiv. diam. <50 px; mm_per_pixel=${MM_PER_PIXEL} optional for JSON) ==="

for entry in "${COHORTS[@]}"; do
  IFS='|' read -r label gt_dir out_sub <<< "$entry"
  slug="$(json_slug "$label")"
  npz="${REPO_ROOT}/output/${out_sub}/pipeline_run/intermediate/selected_masks.npz"
  json_out="${OUT_DIR}/r2_20_${slug}.json"

  if [[ ! -d "$gt_dir" ]]; then
    echo "[SKIP] ${label}: GT mask dir missing: ${gt_dir}"
    skipped=$((skipped + 1))
    continue
  fi
  if [[ ! -f "$npz" ]]; then
    echo "[SKIP] ${label}: no cache ${npz}"
    skipped=$((skipped + 1))
    continue
  fi

  echo "[RUN] ${label} -> ${json_out}"
  "$PYTHON" scripts/revision/b11/analyze_r2_20_small_nodules.py \
    --gt-mask-dir "$gt_dir" \
    --selected-npz "$npz" \
    --mm-per-pixel "$MM_PER_PIXEL" \
    --max-diameter-mm "$MAX_DIAMETER_MM" \
    --output "$json_out"
  ran=$((ran + 1))
done

echo "=== Summarizing ${OUT_DIR}/r2_20_*.json -> ${OUT_DIR}/R2_20_SUMMARY.md ==="

"$PYTHON" - <<'PY'
import json
from pathlib import Path
import os

out_dir = Path(os.environ.get("OUT_DIR", "docs/revision/b11_b12/tables"))
mm = os.environ.get("MM_PER_PIXEL", "0.1")
max_mm = os.environ.get("MAX_DIAMETER_MM", "5.0")

rows = []
for p in sorted(out_dir.glob("r2_20_*.json")):
    data = json.loads(p.read_text(encoding="utf-8"))
    s = data["summary"]
    cohort = p.stem.replace("r2_20_", "")
    rows.append(
        {
            "cohort": cohort,
            "json": p.name,
            "n_matched": s.get("n_matched"),
            "n_lt_5mm": s.get("n_gt_below_max_diameter_mm"),
            "n_fail": s.get("n_pred_fail_small"),
            "mean_dice_small": s.get("mean_dice_small_gt"),
            "n_lt_50px": s.get("n_gt_foreground_area_below_min_component_disk"),
            "npz": s.get("selected_masks_npz"),
        }
    )

md = f"""# R2.20(b) 小结节统计摘要（自动生成）

**生成命令**: `scripts/revision/b11/run_r2_20_small_nodules_all.sh`  
**主口径**: GT 等价直径 **<50 px**（`min_component_px=50`；不依赖 DICOM spacing）  
**可选**: `mm_per_pixel = {mm}`, `max_diameter_mm = {max_mm}`（JSON 内 mm 敏感性；与 <50 px 在 0.1 mm/px 下数值相同）

**失败定义**: selected mask 为空或 Dice < 0.1（整条分割+路由流水线，非 radiomics 前 CCA）。

| 队列 | n 匹配 | GT 等价径 <50 px (N) | 失败 (M) | 子集 mean Dice | （参考）<{max_mm} mm @0.1 mm/px |
|------|--------|----------------------|----------|----------------|-------------------------------|
"""
for r in rows:
    dice = r["mean_dice_small"]
    dice_s = f"{dice:.3f}" if dice is not None else "—"
    md += (
        f"| {r['cohort']} | {r['n_matched']} | {r['n_lt_50px']} | {r['n_fail']} | "
        f"{dice_s} | {r['n_lt_5mm']} |\n"
    )

md += "\n逐队列 JSON：`r2_20_*.json`（含 `selected_masks_npz` 路径，便于核对主结果 config）。\n"

if not rows:
    md += "\n（无 JSON：请先成功跑完至少一个队列。）\n"

summary_path = out_dir / "R2_20_SUMMARY.md"
summary_path.write_text(md, encoding="utf-8")
print(f"Wrote {summary_path} ({len(rows)} cohorts)")
PY

echo "=== Done: ran=${ran}, skipped=${skipped} ==="
