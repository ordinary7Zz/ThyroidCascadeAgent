# B4 组件消融（L1–L3）

> **审稿**：R2.8（主）；与 B3 路由消融、B10 基线协议交叉引用。  
> **计划**：[`docs/REVISION_B3_B4_PLAN.md`](../../REVISION_B3_B4_PLAN.md) §5。  
> **进度与数字**：[`B4_STATUS_ZH.md`](./B4_STATUS_ZH.md)（本目录维护，有更新请改该文件）。

## 文档

| 文件 | 内容 |
|------|------|
| [B4_STATUS_ZH.md](./B4_STATUS_ZH.md) | **进度看板 + L1/L2 实验结果表** |
| [L1_METRICS_SCHEMA.md](./L1_METRICS_SCHEMA.md) | L1 JSON 字段与 `ingest_l1_metrics.py` |
| [examples/l1_provenance_template.json](./examples/l1_provenance_template.json) | L1 `provenance` 模板 |

## 代码与配置

| 用途 | 路径 |
|------|------|
| L1 跑数 | `scripts/revision/b4/run_l1_cohort.py`，`config/revision/b4/l1/<cohort>.yaml` |
| L1 批量 | `scripts/revision/b4/run_l1_remaining_background.sh` |
| 汇总主表 | `scripts/revision/b4/build_b4_tables.py`，`config/revision/b4/<cohort>.yaml` |
| Path B 附录 B-b | `scripts/revision/b4/run_b4_pathb_appendix.py` |
| L2/L3 数据源 | `output/ablation/b3/<cohort>/soft_voting|llm/b3_metrics.json` |

## 合并结果（自动生成）

收口 L1+L2 后生成：`output/ablation/b4/b4_l1_l2_summary.csv`  
各 cohort 主表：`output/ablation/b4/<cohort>/b4_component_table.csv`

```bash
for c in sample tn3k tn5k thyroidxl ddti_cls ddti_seg pktn zjh8k rjh7k; do
  python scripts/revision/b4/build_b4_tables.py --config config/revision/b4/$c.yaml
done
```
