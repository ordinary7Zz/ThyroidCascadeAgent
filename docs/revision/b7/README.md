# B7　NHC 中心异质性

| 文件 | 说明 |
|------|------|
| [**NHC_CONVERSATION_BUILD_AND_REPLY_HISTORY_ZH.md**](./NHC_CONVERSATION_BUILD_AND_REPLY_HISTORY_ZH.md) | **对话梳理**：示例流水线、政策、回信 LaTeX（R18–R20）、checklist |
| [B7_NHC_SCOPE_SUMMARY_ZH.md](./B7_NHC_SCOPE_SUMMARY_ZH.md) | 审稿对应、实验/元数据清单 |
| [NHC_GPU_AND_WEIGHTS_ZH.md](./NHC_GPU_AND_WEIGHTS_ZH.md) | Conda/GPU、`my_Thyroid_Infer/config.yaml` 与 Cascade 权重 |
| [nhc_sample 示例全流程配置](../nhc_sample/README.md) | B3/B4/B8/B2/infer 示例 yaml 与运行顺序 |
| 回信表 R18–R20 | `docs/revision/暂定的修改和回复计划/正式回复/latex/generated/nhc_b7_tables_*.tex`（registry：`tab_nhc_*` → R18/R19/R20） |

## 代码布局（B7 专有）

| 层 | 路径 |
|----|------|
| **pipeline** | `pipeline/revision/b7/` — NHC 预处理（`nhc_prepare_data.py`）、聚合、I²、报告 JSON |
| **scripts** | `scripts/revision/b7/` — `run_nhc_prepare.py`、`run_b7_nhc.sh` 等 CLI |

共享依赖（非 B7 目录）：`shared/center_manifest.py`、`pipeline/evaluate.py`（结节 mask 评估）、`scripts/revision/b8/backfill_results_metadata.py`（补 `center_id`）。

## NHC 原始数据预处理（B7，可选）

自 `my_Thyroid_Infer/prepare_data.py` 复制到本仓库，**不修改** `my_Thyroid_Infer/pipeline.py`。输出含 `center_id` / `patient_id` 与 `center_stats.json`。

```bash
python scripts/revision/b7/run_nhc_prepare.py \
  --input_dir /path/to/甲状腺私有数据/新建文件夹 \
  --output_dir output/b7/nhc_prepared \
  --skip_roi

# 启用 ROI 时需 my_Thyroid_Infer 与权重；默认 THYROID_INFER_ROOT=../my_Thyroid_Infer
# python scripts/revision/b7/run_nhc_prepare.py --input_dir ... --checkpoint /path/to/best_dice_model.pth
```

产出：`images/`、`gland_masks/`、`nodule_masks/`、`labels.json`、`center_stats.json`、`center_manifest.json`（及可选 `name_mapping.json`）。

可将 `nhc_no_llm_primary.yaml` 的 `image_input` / `gt_mask_dir` / `label_file` 指向上述目录；`center_manifest.json` 也可作为 `pipeline.revision.center_manifest`。

**示例 canonical 样板（10 图真 Cascade + B7，推荐写表结构）**：

```bash
conda activate /mnt/wangbd8/workspace/envs/thyroid_infer
bash scripts/revision/b7/run_b7_sample_canonical.sh
```

产出：`output/b7/nhc_sample_canonical/b7_report.json`、`csv/`、`descriptive_canonical/nhc_center_descriptive.csv`（含 `n_patients`）。  
默认 `FORCE_REFRESH=1` 会清 `intermediate`，避免 `max_images` 改大后仍用旧缓存。

**B7 冒烟（无需 GPU）**：用 GT 模拟 pipeline 输出后跑分析链。

```bash
python scripts/revision/b7/run_nhc_prepare.py --input_dir ... --output_dir output/b7/nhc_prepared_smoke --skip_roi
python scripts/revision/b7/smoke_b7_prepared_sample.py
# 再 evaluate + run_b7_analysis（见 scripts/revision/b7/smoke_b7_prepared_sample.py 注释或 output/b7/nhc_smoke_report）
```

## 运行顺序

```bash
# 1) 已有 NHC pipeline 输出：output/revision/nhc_no_llm_primary/results.json

# 2) 补 center_id（labels 或 center manifest）
python scripts/revision/b8/backfill_results_metadata.py \
  --config config/revision/nhc_no_llm_primary.yaml

# 3) B7 分析（--re-evaluate 生成/刷新 per_image_* jsonl）
python scripts/revision/b7/run_b7_analysis.py --re-evaluate \
  --g3-csv /path/to/g3_centers.csv

# 4) 导出 CSV
python scripts/revision/b7/export_b7_tables.py

# 或一条龙
G3_CSV=/path/to/g3.csv bash scripts/revision/b7/run_b7_nhc.sh
```

## 配置（可选全腺体）

在 `config/revision/nhc_no_llm_primary.yaml` 的 `pipeline.data` 下可增加：

```yaml
gt_gland_mask_dir: /path/to/gland_gt_masks
gland_pred_mask_dir: /path/to/gland_pred_masks
```

或 CLI：`--gt-gland-mask-dir`、`--gland-pred-mask-dir`、`--compute-gland`。

## 产出

| 路径 | 内容 |
|------|------|
| `output/b7/nhc/b7_report.json` | 中心性能、I²/τ²、中心内 SD/CV、meta 回归 |
| `output/b7/nhc/center_metrics.json` | 兼容旧字段 |
| `output/b7/nhc/*.csv` | `export_b7_tables.py` |
| `output/b7/descriptive/` | `build_nhc_center_table.py` |

## 测试

```bash
PYTHONPATH=. python3 -m pytest tests/revision/test_b7_heterogeneity.py -q
```
