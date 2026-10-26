# B5 路由元数据消融

> **审稿**：R3.2（Reviewer 3 Major 2：元数据与中心特异偏好）  
> **详规（字段级）**：[`docs/REVISION_B5_PLAN.md`](../../REVISION_B5_PLAN.md)  
> **交付清单**：[`docs/revision/暂定的修改和回复计划/B_DELIVERABLES_CHECKLIST_ZH.md`](../暂定的修改和回复计划/B_DELIVERABLES_CHECKLIST_ZH.md) §B5

## 本目录文档

| 文件 | 内容 |
|------|------|
| [B5_UNDERSTANDING_ZH.md](./B5_UNDERSTANDING_ZH.md) | **任务理解**：科学问题、与 B3/B4/B6/B7 边界、五种 mode |
| [B5_BUILD_PLAN_ZH.md](./B5_BUILD_PLAN_ZH.md) | **构建与跑数计划**：依赖、验收、排期、仓库现状 |
| [B5_STATUS_ZH.md](./B5_STATUS_ZH.md) | **进度看板**（实验未开时以占位为主，跑数后更新） |

## 代码与配置（仓库已有骨架）

| 用途 | 路径 |
|------|------|
| 计划总览 | `docs/REVISION_B5_PLAN.md` |
| 配置 | `config/revision/b5/<cohort>.yaml`（`generate_ablation_configs.py`） |
| 批量跑数 | `scripts/revision/b5/run_b5_batch.py` |
| 单 mode | `scripts/run_routing_ablation.py --routing-mode llm --metadata-mode <mode>` |
| 字段过滤 | `shared/metadata_prompt.py` |
| 汇总表 | `scripts/revision/b5/build_b5_tables.py` |
| 热图 / 互信息 | `pipeline/revision/b5/analyze_routing_bias.py` |
| 单测 | `tests/test_metadata_prompt.py` |

## 输出布局（目标）

```
output/ablation/b5/<cohort>/<metadata_mode>/
  results.json
  b3_metrics.json          # 或带 metadata_mode 的 b5 指标
  routing_log.jsonl        # log_routing: true
  intermediate_manifest.json
```

汇总：`python scripts/revision/b5/build_b5_tables.py --root output/ablation/b5`
