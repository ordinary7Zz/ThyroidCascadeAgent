# B2 运行清单（cluster bootstrap + 患者级分类）

> **结论文案**：`conclusions/B2_结论与回复素材.md`；B1 见 `../b1/B1_结论与回复素材.md`。本目录总览见 **`README.md`**。  
> **依赖**：B1 审计定稿（聚类键、披露句式）。一键跑批按 **`cohort_tasks.yaml`** 区分分类/分割，勿对仅分割队列跑分类 B2。  

**基线模型**：导出至父级 **`../b2_exports/`** 后运行 `bash scripts/revision/b2/run_b2_exports_all.sh`（见 `b2_exports/README.md`）。
> **对齐**：B3/B8/B9 的 CI 在 B2 定稿后统一重算（seed=42，1000 次，95% 百分位区间）。

---

## A. 目标产出

| 产出 | 说明 |
|------|------|
| 全表 CI 更新 | S3–S5、S7–S12 中 ThyroidXAgent 及基线行的 **cluster-bootstrap 95% CI** |
| 补充患者级表 | **ZJH-8K**、**ThyroidXL** 分类：患者级 AUROC/AUPRC（+ 可选 Acc/F1） |
| 聚类映射文件 | `docs/revision/b2/cluster_maps/*.json`（由 `scripts/revision/b2/build_cluster_maps.py` 生成） |
| Methods | 写明聚合规则：**主分析 = 同一患者多图恶性概率算术平均**；敏感性（如 max）可选 |

---

## B. 患者级分类：聚合规则（建议主分析）

1. 每张图：从 `results.json` 取恶性概率 `p_mal`（如 `final_confidence` + `final_label`，或 `cls_decision` 中恶性类概率——与现 `evaluate.py` 一致）。  
2. 按 `cluster_id` 分组。  
3. **患者标签**：若组内 `malignancy` 一致则取之；若冲突则 **max malignancy（任一恶性→恶性）** 并记入审计附注。  
4. **患者分数**：`mean(p_mal)`。  
5. 在患者级计算 AUROC/AUPRC；CI 对患者 **有放回重采样** 1000 次。

分割（Dice/HD95）：建议与现 pipeline 一致——**先逐图 Dice，再对患者内图取平均，再对患者 cluster bootstrap 均值的 CI**（实现时在脚本中与稿内原图像级定义对照一次）。

---

## C. 输入文件（主 pipeline 已跑通部分）

| 队列 | `results.json` | `selected_masks.npz` | 标签 | 聚类映射 |
|------|----------------|----------------------|------|----------|
| TN3K | `output/TN3K/pipeline_run/results.json` | `.../intermediate/selected_masks.npz` | `train_val_test/TN3K/test/*_label.json` | 图级（无 map） |
| TN5K | `output/TN5K/pipeline_run/` | 同上 | `train_val_test/TN5K/test/` | 图级 |
| ThyroidXL | `output/ThyroidXL/pipeline_run/` | 同上 | `ThyroidXL/test/ThyroidXL_test_label.json` | `cluster_maps/thyroidxl_test.json` |
| ZJH-8K | `output/ZJH-8K/pipeline_run/` | 同上 | `ZJH-8K/ZJH-8K_BM_labels.json` | `cluster_maps/zjh8k.json` |
| DDTI seg/cls | `output/DDTI_seg/`、`output/DDTI_cls/` | 若有 | seg：`DDTI/all_seg/`；cls：**349** → `DDTI_Classification/all/` | 图级 |
| RJH-7K | `output/RJH-7K/pipeline_run/` | 同上 | config 内 `label_file` | 图级 |
| PKTN | `output/PKTN/pipeline_run/` | 同上 | 仅分割 | 图级 |
| NHC | **缺失** | — | — | TBD |

**当前 `metrics.json`**（各 `output/*/pipeline_run/metrics.json`）为图像级 CI，**不可直接作 B2 定稿**，仅作对照。

---

## D. 命令步骤（推荐顺序）

### D1. 生成聚类映射（已有脚本）

```bash
cd /mnt/wangbd8/workspace/ThyroidAgent/ThyroidCascadeAgent

python scripts/revision/b2/build_cluster_maps.py \
  --out-dir docs/revision/b2/cluster_maps
```

检查输出：

- `thyroidxl_test.json`：2090 项，**739** 个唯一 `patient_id`
- `zjh8k.json`：7958 项，**1146** 个唯一 `patient_id`（`Pxxxx`）

### D2. 实现并运行 B2 指标（**待开发**）

建议新增 `scripts/revision/b2/run_b2_cluster_metrics.py`：

- 输入：`--results`、`--cluster-map`（可选）、`--label-file`、`--output-json`
- 输出：图像级 + 患者级（若有 map）点估计与 cluster-bootstrap CI
- 逻辑：复用 `evaluate.py` 的逐图 metric 计算，bootstrap 层改为 `rng.choice(unique_clusters, size=n_clusters, replace=True)` 再展开到图像

**占位运行（实现后）**：

```bash
# ThyroidXL 患者级分类
python scripts/revision/b2/run_b2_cluster_metrics.py \
  --results output/ThyroidXL/pipeline_run/results.json \
  --cluster-map docs/revision/b2/cluster_maps/thyroidxl_test.json \
  --label-file /mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/ThyroidXL/test/ThyroidXL_test_label.json \
  --task classification \
  --out docs/revision/b2/tables/thyroidxl_patient_level.json

# ZJH-8K 患者级分类
python scripts/revision/b2/run_b2_cluster_metrics.py \
  --results output/ZJH-8K/pipeline_run/results.json \
  --cluster-map docs/revision/b2/cluster_maps/zjh8k.json \
  --label-file /mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/ZJH-8K/ZJH-8K_BM_labels.json \
  --task classification \
  --out docs/revision/b2/tables/zjh8k_patient_level.json

# 全队列图像级/图簇 CI（无 map 时 cluster=filename）
for cohort in TN3K TN5K ThyroidXL ZJH-8K DDTI_cls DDTI_seg RJH-7K PKTN; do
  # 按 cohort 填 config 路径后批量调用
  true
done
```

### D3. 基线与补充表（S3/S4…）

- 基线模型 CI：需各基线 **逐图预测** 或复跑评估；若仅有稿面点估计，需从对应 infer 输出补预测文件再走 D2。  
- B9 LNM：已含 cluster bootstrap，将 `confidence_intervals` 字段与 B2 全局参数对齐后写入总表。

### D4. 回写 B3

```bash
# 定稿后重导 B3 表（示例）
python docs/revision/b3/scripts/export_b3_tables.py   # 需改为读 cluster CI
```

---

## E. 验收标准

- [ ] ThyroidXL test：患者数 = **739**（± 与官方 2094 图差异说明）  
- [ ] ZJH-8K：患者数 = **1146**（稿面 1149 在 Methods 解释）  
- [ ] 无 map 队列：Methods 明确 **image-level cluster**  
- [ ] 患者级 AUROC ≤ 图像级 AUROC 不一定成立，但 CI 应**不窄于**原图像级 CI（多数队列）  
- [ ] `seed=42`、`n_bootstrap=1000` 与 B9 一致  

---

## F. 阻塞项

| 项 | 负责人/动作 |
|----|-------------|
| `run_b2_cluster_metrics.py` 未实现 | 工程：扩展 `evaluate.py` 或独立脚本 |
| NHC 数据与预测 | 数据同步 + 再跑 pipeline |
| S3/S4 基线逐图分数 | 从各 infer 日志或重跑 `evaluate` |
| TN3K–ZJH 重叠 | F6 + 近重复表（B1，不阻塞 CI 重算但阻塞 R2.4 表述） |
