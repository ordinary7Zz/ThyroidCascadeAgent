# B4 L1 单专家外测配置

- **含义**：仅 `all_datasets` 联合训练的 **1 个分割 + 1 个分类** DINO 专家；`enable_agent: false`；`radiomics_judge: false`（无 AutoGluon / LLM）。
- **生成**：`python scripts/generate_ablation_configs.py` → `config/revision/b4/l1/<cohort>.yaml`
- **权重路径**：`config/revision/b4/l1/_single_expert_models.yaml`（与 B3 池中 `all_datasets` 成员一致；可手改）

## 跑单个队列

```bash
# 冒烟（5 张）
python scripts/revision/b4/run_l1_cohort.py --cohort sample --max-images 5

# 全量
python scripts/revision/b4/run_l1_cohort.py --cohort tn3k
```

输出：`output/ablation/l1/<cohort>/run1/` + `artifacts/b4_l1_<cohort>.json`

## 批量

```bash
# 后台跑剩余队列（跳过 sample、tn3k）
nohup bash scripts/revision/b4/run_l1_remaining_background.sh \
  >> output/ablation/l1/l1_remaining_batch.log 2>&1 &

# 含 sample/tn3k 的全量顺序跑
bash scripts/revision/b4/run_l1_all_cohorts.sh
```

单 cohort 全量重跑请加 `--fresh`（或删 `output/ablation/l1/<cohort>/run1`）。

## 汇总 B4 主表

```bash
python scripts/revision/b4/build_b4_tables.py --config config/revision/b4/tn3k.yaml
```

字段说明：`docs/revision/b4/L1_METRICS_SCHEMA.md`
