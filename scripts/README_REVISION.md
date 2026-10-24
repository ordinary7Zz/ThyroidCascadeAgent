# 返修脚本索引（B1–B12）

> **命令详表**：[`docs/RUN_REVISION_COMMANDS.md`](../docs/RUN_REVISION_COMMANDS.md)  
> **Pipeline 库**：[`pipeline/README.md`](../pipeline/README.md)  
> **地基 CLI**：[`README.md`](README.md)（`build_test_for_llm`、`run_routing_ablation` 等）  
> **返修目录**：[`revision/`](revision/README.md)（`b1`–`b11`）

返修批处理在 `scripts/revision/{b1,…,b11}/`；Python 用 `revision/_path_setup.py` 或根目录 `repo_path.py`。

## 和 `run_pipeline` 的关系（重要）

| 层级 | 位置 | 作用 |
|------|------|------|
| **产品入口** | 仓库根 `run_pipeline.py`、`run_seg.py`、`run_cls.py`、`run_routing_stability.py` | 直接 `import pipeline` / `shared` / `segmentation` / `classification` |
| **可复用库** | [`pipeline/`](../pipeline/README.md)（核心）；[`pipeline/revision/`](../pipeline/revision/README.md)（B3–B8） | 返修 import：`pipeline.revision.b8.*` 等 |
| **地基 CLI** | [`scripts/README.md`](README.md) | for_llm、批量 `run_pipeline`、`run_routing_ablation`、生成 `config/b3` |
| **返修批处理** | `scripts/revision/**` | B1–B11 制表、审计、批量消融 |

级联**库**在 `pipeline/`；`scripts/` 下为命令行外壳，**不**被 `cascade` import。

---

## 推荐入口（每个 B 包只记一条）

| B | 你要做的事 | 首选命令 |
|---|------------|----------|
| **地基** | 建 LLM 小子集 | `bash scripts/build_all_test_for_llm.sh`（见 [`README.md`](README.md)） |
| **地基** | 各队列 Phase 1–2 / 全 pipeline | `bash scripts/run_pipeline_all_cohorts.sh` |
| **B3** | 单策略消融 | `python scripts/run_routing_ablation.py …` |
| **B1** | dHash 近重复审计 | `python scripts/revision/b1/audit_near_duplicates.py` |
| **B2** | 一键 cluster CI | `bash scripts/revision/b2/run_b2_all.sh` |
| **B3** | 波次 1 全队列 | `bash scripts/revision/b3/run_b3_wave1_all_cohorts.sh` |
| **B3** | 单队列 / 多 mode | `python scripts/revision/b3/run_b3_batch.py --config config/b3/tn3k.yaml …` |
| **B3** | ZJH 大队列（防 OOM） | `bash scripts/revision/b3/zjh/run_b3_zjh8k.sh` 或 chunk 版 `run_b3_zjh8k_chunks.sh` |
| **B3** | RJH 大队列（chunk 重推 + B3） | `run_rjh7k_reinfer_chunks.sh` → `run_b3_rjh7k_chunks.sh`（`scripts/revision/b3/rjh/`） |
| **B4** | 组件表 | `python scripts/revision/b4/build_b4_tables.py` |
| **B5** | 元数据消融 | `python scripts/revision/b5/run_b5_batch.py --config config/b5/tn3k.yaml` |
| **B6** | 导出 router 规格 | `python scripts/revision/b6/export_router_spec.py` |
| **B6** | 5× 稳定性 | 根目录 `python run_routing_stability.py`（非本目录） |
| **B7** | 中心异质性 | `python scripts/revision/b7/run_b7_analysis.py` |
| **B8** | 正式定阈 + 全队列 eval | `bash scripts/revision/b8/run_openthyroid_validation_b8.sh` → `run_b8_all_cohorts.sh` |
| **B10** | 基线协议表 | `python scripts/revision/b10/build_b10_protocol_table.py` |
| **B11** | &lt;5 mm 结节统计 | `bash scripts/revision/b11/run_r2_20_small_nodules_all.sh` |

**勿入稿**：`run_b8_smoke_test_as_val.sh`（test 当 val 的烟雾）。

---

## 按 B 包归类（全文件）

路径前缀：返修脚本在 **`scripts/revision/<子目录>/`**；地基 CLI 见 **[`README.md`](README.md)**。

### B1

| 文件 | 作用 |
|------|------|
| `audit_near_duplicates.py` | dHash 跨库近重复 |
| `audit_train_test_overlap.py` | train/test 文件名 stem 重叠（辅助） |
| `export_zjh_excl_train_dhash0.py` | ZJH 剔除 train-matched 图名单 |

### B2

| 文件 | 作用 |
|------|------|
| `run_b2_cluster_metrics.py` | 簇级 bootstrap CI（核心计算） |
| `build_cluster_maps.py` | 患者级 cluster 映射 |
| `run_b2_from_export.py` | 从 `b2_exports` 算指标 |
| `run_b2_exports_all.sh` | 扫 exports → `*_b2.json` + 索引 |
| `run_b2_all.py` / `run_b2_all.sh` | 读 `docs/revision/b2/cohort_tasks.yaml` 一键跑 |
| `run_b2_zjh8k_excl_baselines.sh` | ZJH excl 敏感性基线 B2 |

### B3

| 文件 | 作用 |
|------|------|
| `run_b3_batch.py` | **主批量**：多 routing_mode / preset |
| [`../run_routing_ablation.py`](../run_routing_ablation.py) | 单次 mode，Phase 3–5（地基 CLI，非 `revision/b3`） |
| `run_b3_static_bundle.py` | 静态 bundle 一次多 mode |
| `run_b3_wave1_all_cohorts.sh` | 全队列波次 1 |
| `run_b3_wave1_remaining_four.sh` | 补跑四队列 |
| `run_b3_zjh8k.sh` | ZJH 整包（fast5 → static_rule 分两趟） |
| `split_b3_intermediate_chunks.py` | 切 intermediate chunk |
| `run_b3_zjh8k_chunks.sh` | 按 chunk 跑 B3 + merge |
| `run_zjh8k_reinfer_chunks.sh` | ZJH 按 chunk 重推 Phase 1–2 |
| `rjh/run_rjh7k_reinfer_chunks.sh` | RJH 按 chunk 重推 Phase 1–2（仅 seg） |
| `rjh/run_b3_rjh7k_chunks.sh` | RJH 按 chunk 跑 B3 + merge（`--task seg`） |
| `merge_b3_chunk_outputs.py` | 合并 chunk 输出 |
| `check_b3_host_capacity.py` | 节点内存/GPU/intermediate 检查 |
| `watch_b3_bundle_progress.sh` | 监视 bundle 进度 |
| `fit_best_single_expert.py` | best_single artifact |
| `fit_learned_router.py` | learned 路由 joblib |
| `run_learned_b3.py` | learned 策略跑 B3 |
| `eval_seg_routing_offline.py` | 离线 seg 路由评测 CLI |

### B4

| 文件 | 作用 |
|------|------|
| `build_b4_tables.py` | 组件主表 |
| `run_b4_pathb_appendix.py` | Path B 附录 |

### B5

| 文件 | 作用 |
|------|------|
| `run_b5_batch.py` | 遍历 `metadata_mode` |
| `build_b5_tables.py` | 汇总 ablation/b5 表 |

### B6

| 文件 | 作用 |
|------|------|
| `export_router_spec.py` | 导出 `docs/supplementary/router_spec.md` |
| `generate_b6_configs.py` | 生成 `config/b6/*.yaml` |

### B7

| 文件 | 作用 |
|------|------|
| `run_b7_analysis.py` | 按中心分析 |
| `build_nhc_center_table.py` | NHC 中心描述表 |

### B8

| 文件 | 作用 |
|------|------|
| `run_calibration_abstention.py` | fit + eval CLI |
| `run_openthyroid_validation_b8.sh` | validation 合并定阈 |
| `run_b8_all_cohorts.sh` | 测试队列批量 eval |
| `run_b8_smoke_test_as_val.sh` | 烟雾（不可入稿） |
| `merge_validation_results.py` | 合并 validation results |
| `backfill_results_metadata.py` | backfill CLI |
| `backfill_uncertainty_all_cohorts.sh` | 多队列 backfill |

### B10

| 文件 | 作用 |
|------|------|
| `build_b10_protocol_table.py` | Supp. 基线训练协议表 |

### B11

| 文件 | 作用 |
|------|------|
| `analyze_r2_20_small_nodules.py` | 单队列小结节 N/M |
| `run_r2_20_small_nodules_all.sh` | 多队列批量 |

### B9 / B12

本目录 **无** 专用脚本；B9 实验多在 `new_code/` 等；B12 以稿面与 `docs/revision/b11_b12/` 为主。

---

## 重叠与运维包（整理时勿误删）

| 组合 | 说明 |
|------|------|
| `pipeline/evaluate.py` vs `run_b2_cluster_metrics.py` | 图像级 CI vs **簇级** CI |
| `pipeline/revision/b8/backfill_uncertainty.py` vs `backfill_results_metadata.py` | 库 vs CLI |
| `run_b3_zjh8k.sh` + `*_chunks.sh` + `run_zjh8k_reinfer_chunks.sh` | 同一 B3·ZJH 目标的 **OOM 运维变体** |

---

## 根目录相关（不在 `scripts/`）

| 文件 | B | 作用 |
|------|---|------|
| `run_pipeline.py` | 核心 | 调 `pipeline.cascade` |
| `run_routing_stability.py` | **B6** | 调 `pipeline.routing_stability` |
