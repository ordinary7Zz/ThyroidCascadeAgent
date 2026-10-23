# B2（cluster bootstrap + 补充表数据）

本目录为 **B2 任务工作区**：脚本产出、配置与结论文案。

| 路径 | 内容 |
|------|------|
| **`conclusions/`** | 写稿用 Markdown（**首选** [`B2_结论与回复素材.md`](./conclusions/B2_结论与回复素材.md)）；S3/S4 单页 [`B2_基线结论_已有输出.md`](./conclusions/B2_基线结论_已有输出.md) |
| **`tables/`** | B2 JSON：`<cohort>_b2.json`（ThyroidXAgent）、`baseline_*_b2.json`（对比基线）、`BASELINES_INDEX.json` |
| **`cluster_maps/`** | ZJH-8K、ThyroidXL 患者聚类映射 |
| **`cohort_tasks.yaml`** | 主系统 `run_b2_all` 各队列分类/分割任务定义 |
| **`B2_RUN_CHECKLIST.md`** | 跑批步骤与患者级规则 |

**B1 数据审计**（患者 ID、train/test 互斥）：[`../b1/`](../b1/)（结论见 [`../b1/B1_结论与回复素材.md`](../b1/B1_结论与回复素材.md)）。

**常用命令**：

```bash
# 主系统
bash scripts/revision/b2/run_b2_all.sh

# 对比基线（需先有 b2_exports）
bash scripts/revision/b2/run_b2_exports_all.sh
```
