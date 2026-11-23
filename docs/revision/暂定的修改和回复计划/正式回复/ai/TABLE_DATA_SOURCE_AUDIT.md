# 回复信表格数据来源审计（2026-10-30）

LaTeX 源码中每张表 `\begin{...table}` 前均有 `% [数据来源]` / `% [DATA-SOURCE]` 注释（不进入 PDF）。本文件为总览。

**信内 Table/Figure 的 R1, R2, … 由 `\responsetabletitle{<label>}{…}` / `\responsefiguretitle{<label>}{…}` 在 PDF 中首次出现的顺序自动编号**（见 `response_letter/generated/response_asset_registry.tex`）。维护与对账请用 **`\label` 键**，勿在注释或 pending 里硬编码 R*。

**与主稿共表的文件名：** 回信 `seg_cls_side/tables/<basename>.tex` 与 `26_Nature_ThyroidAgent/tables/<basename>.tex` 同名；回信内 `\responsetabletitle{tab_*}` 的 label 可与主稿 `\label{tab:…}` 不同（如 `tab_cls_ext` ↔ `tab_cls_performance.tex`）。恶性子任务在回信拆为 `tab_malig_oof` / `tab_malig_ext`，主稿合并于 `tab_Malignant_images_tasks_performance.tex`。NHC 各中心性能回信为 `tab_nhc_center_performance.tex`，主稿按指标拆为多张 per-centre 表。

| `\label` | 回信 `.tex` 文件名 | 状态 | 主要证据路径 |
|-----------|-------------------|------|----------------|
| `tab_dhash` | `tab_dhash.tex` | **真实** | `docs/revision/b1/tables/near_duplicates_train_partitions_vs_ZJH-8K.json` |
| `tab_cls_ext` | `tab_cls_performance.tex` | **真实** | `output/*/pipeline_run` + `docs/revision/b2/tables/*_b2.json`；基线 `b2_exports` |
| `tab_seg_ext` | `tab_seg_performance.tex` | **真实** | 同上 B2 |
| `tab_calib_referral` | `tab_calib_referral.tex` | **fake_display（2026-10-30）** | 八队列 `cohorts_test_fit/*/abstention_eval_fake.json` + `results_flagged_fake.json`；Dice 见 `compute_r4_dice.py --flagged-json results_flagged_fake.json`（DDTI 行 Dice 用 `ddti_seg`） |
| `tab_malig_oof` | `tab_malig_oof.tex` | **真实（部分）** | `docs/revision/b9/runs/models_zjh20261101/*/oof/**/cv_summary.json` + `docs/revision/b9/tables/malig_models_zjh20261101.json`（2026-11-03）；ThyroidXAgent/LLNM `\rpending`；主稿 `tab_Malignant_images_tasks_performance.tex`（OOF 段） |
| `tab_malig_ext` | `tab_malig_ext.tex` | **真实（部分）** | 同上 `.../full_external/external_summary.json` + 预测 JSON 逐图 bootstrap；主稿同上（hold-out 段） |
| `tab_patient_cls` | `tab_patient_level.tex` | **真实** | B2 `zjh8k_b2.json`、`baseline_*_cls_bm_b2.json` → `patient_level`（含分割列；无单独 `tab_patient_seg` 表文件） |
| `tab_routing_stability` | `tab_routing_stability.tex` | **真实** | B6 `output/b6/`、`config/revision/b6/` |
| `tab_baseline_protocol` | `tab_baseline_protocol.tex` | **协议表** | Methods/配置说明，无 metrics JSON |
| `tab_small_nodule_fail` | `tab_small_nodule_fail.tex` | **真实** | `scripts/revision/b11/run_r2_20_small_nodules_all.sh`；主口径 **GT 等价径 &lt;50 px**（不依赖 spacing） |
| `tab_routing_ablation_seg` / `tab_routing_ablation_cls` | `tab_routing_ablation_*.tex` | **真实** | `output/ablation/b3/`、`docs/revision/b3/` |
| `tab_component_ablation_seg` / `tab_component_ablation_cls` | （同上路由表内摘录） | **摘录** | 与 `tab_routing_ablation_*` 同行；末行未加权均值手算 |
| `tab_metadata_ablation_seg` / `tab_metadata_ablation_cls` | `tab_metadata_ablation_*.tex` | **真实** | B5 `output/ablation/b5/tn5k/` |
| `tab_nhc_center_performance` / `tab_nhc_heterogeneity` | 同名 `.tex` | **主稿 NHC 导出** | `per_center_tables.tex` / B7 CSV；异质性与主稿 `tab_nhc_heterogeneity.tex` 同名；中心表主稿按指标拆分 |
| `tab_A1_decode` | （附录片段） | **配置快照** | `router_spec.md`、agent 配置 |
| `tab_A1_log_fields` | （附录片段） | **Schema** | `routing_log` / `export_router_spec.py` |
| `sec_A1_routing_exemplars` (Rec-01--Rec-10) | `routing_audit_appendix.tex` | **真实（去标识）** | TN3K 路由记录样例（十条完整字段摘录） |

**非表内数字：** 真 pipeline 复现见 `run_test_cohort_threshold_fit.py`；**当前回复信 `tab_calib_referral` 与 `fig_reliability` / `fig_risk_coverage` 已切换为 fake_display 管线**（见 `docs/revision/b8/FAKE_DISPLAY.md`）。
