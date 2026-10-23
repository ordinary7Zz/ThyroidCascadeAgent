# `pipeline/` 模块索引（返修 B1–B12）

主推理入口在仓库根目录 **`run_pipeline.py`**（调用 **`cascade.py`**）。  
返修实验 CLI 在 **`scripts/revision/`**（`run_pipeline` **不**依赖 `scripts`），见 [`../scripts/README_REVISION.md`](../scripts/README_REVISION.md)。

## 层级

| 层级 | 说明 |
|------|------|
| **核心** | 产品级联与评估，返修前后均需要 |
| **返修库** | 仅服务于 B3–B8 等补充分析，由 `scripts/*.py` 调用 |

## 文件一览

| 模块 | B 包 | 作用 |
|------|------|------|
| [`cascade.py`](cascade.py) | 核心 + B3/B5/B6 | Phase 1–5 级联；`stop_after_phase2`；learned router；routing 日志挂钩 |
| [`compare_models.py`](compare_models.py) | 核心 | Pipeline vs 独立分割/分类模型对比 |
| [`evaluate.py`](evaluate.py) | B2 + 通用 | Dice/HD95/AUROC/AUPRC；**图像级** bootstrap CI |
| [`routing_stability.py`](routing_stability.py) | **B6** | 复用 intermediate，5× LLM 路由 + `disagreement_tier` 汇总 |
| [`routing_ablation.py`](routing_ablation.py) | **B3** | 单次消融输出目录与 shared intermediate 约定 |
| [`static_b3_bundle.py`](static_b3_bundle.py) | **B3** | 波次 1：一次扫图多静态 routing_mode（含 lazy 大队列） |
| [`seg_routing_offline.py`](seg_routing_offline.py) | **B3** | 只读 intermediate 评非 LLM 分割路由 |
| [`routing_methods.py`](routing_methods.py) | B3 辅助 | 从 results 提取 strategy 签名 |
| [`ablation_metrics.py`](ablation_metrics.py) | **B3** | 单次 run → `b3_metrics.json` |
| [`ablation_summary.py`](ablation_summary.py) | **B3** | 多 mode 聚合 CSV + 点估计差分 |
| [`intermediate_manifest.py`](intermediate_manifest.py) | B3/B4 | intermediate 指纹校验 |
| [`b4_summary.py`](b4_summary.py) | **B4** | 组件消融主表 L1–L3 |
| [`b4_pathb_summary.py`](b4_pathb_summary.py) | **B4** | Path B 放射组学附录 |
| [`analyze_routing_bias.py`](analyze_routing_bias.py) | **B5** | routing_log → 中心×专家、互信息 |
| [`calibration.py`](calibration.py) | **B8** | ECE、Brier、可靠性分箱 |
| [`abstention.py`](abstention.py) | **B8** | 验证集定阈 + 拒答 + risk–coverage |
| [`plot_calibration.py`](plot_calibration.py) | **B8** | 可靠性图 |
| [`backfill_uncertainty.py`](backfill_uncertainty.py) | **B8** / NHC | 补写 uncertainty、center_id（无 GPU） |
| [`nhc_heterogeneity.py`](nhc_heterogeneity.py) | **B7** | NHC 按中心聚合性能 |
| [`meta_regression.py`](meta_regression.py) | **B7** | I²、简单 meta 回归 |
| [`__init__.py`](__init__.py) | — | 延迟 import，避免循环依赖 |

## 依赖关系（简图）

```text
run_pipeline.py → cascade.py → evaluate.py（评估阶段）
scripts/run_routing_ablation.py → routing_ablation.py → cascade（B3 消融外壳）
run_routing_stability.py → routing_stability.py → cascade（仅路由）

B3: static_b3_bundle / routing_ablation / seg_routing_offline → ablation_metrics → ablation_summary
B4: b4_summary / b4_pathb_summary（读 B3 输出）
B5: analyze_routing_bias（读 routing_log）
B8: backfill_uncertainty → calibration + abstention → plot_calibration
B7: nhc_heterogeneity + meta_regression
```
