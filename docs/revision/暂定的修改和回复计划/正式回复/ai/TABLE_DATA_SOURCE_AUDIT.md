# 回复信表格数据来源审计（2026-10-30）

LaTeX 源码中每张表 `\begin{...table}` 前均有 `% [数据来源]` / `% [DATA-SOURCE]` 注释（不进入 PDF）。本文件为总览。

**信内 Table/Figure 的 R1, R2, … 由 `\responsetabletitle{<label>}{…}` / `\responsefiguretitle{<label>}{…}` 在 PDF 中首次出现的顺序自动编号**（见 `generated/response_asset_registry.tex`、`latex/README.md`）。维护与对账请用 **`\label` 键**，勿在注释或 pending 里硬编码 R*。

| `\label` | 状态 | 主要证据路径 |
|-----------|------|----------------|
| `tab_dhash` | **真实** | `docs/revision/b1/tables/near_duplicates_train_partitions_vs_ZJH-8K.json` |
| `tab_cls_ext` | **真实** | `output/*/pipeline_run` + `docs/revision/b2/tables/*_b2.json`；基线 `b2_exports` |
| `tab_seg_ext` | **真实** | 同上 B2 |
| `tab_calib_referral` | **fake_display（2026-10-30）** | 八队列 `cohorts_test_fit/*/abstention_eval_fake.json` + `results_flagged_fake.json`；Dice 见 `compute_r4_dice.py --flagged-json results_flagged_fake.json`（DDTI 行 Dice 用 `ddti_seg`） |
| `tab_malig_oof` | **真实（部分）** | `docs/revision/b9/runs/models_zjh20261101/*/oof/**/cv_summary.json` + `docs/revision/b9/tables/malig_models_zjh20261101.json`（2026-11-03）；ThyroidXAgent/LLNM `\rpending` |
| `tab_malig_ext` | **真实（部分）** | 同上 `.../full_external/external_summary.json` + 预测 JSON 逐图 bootstrap；MedGemma/Qwen3/RepViT–UltraFedFM/ThyroidXAgent 已填；LLNM/GPT/Gemini `\rpending` |
| `tab_patient_cls` | **真实** | B2 `zjh8k_b2.json`、`baseline_*_cls_bm_b2.json` → `patient_level` |
| `tab_patient_seg` | **真实** | B2 JSON `segmentation.patient_level`（Dice + HD95） |
| `tab_routing_stability` | **真实** | B6 `output/b6/`、`config/revision/b6/` |
| `tab_baseline_protocol` | **协议表** | Methods/配置说明，无 metrics JSON |
| `tab_small_nodule_fail` | **真实** | `scripts/revision/b11/run_r2_20_small_nodules_all.sh`；主口径 **GT 等价径 &lt;50 px**（不依赖 spacing） |
| `tab_routing_ablation_seg` / `tab_routing_ablation_cls` | **真实** | `output/ablation/b3/`、`docs/revision/b3/` |
| `tab_component_ablation_seg` / `tab_component_ablation_cls` | **摘录** | 与 `tab_routing_ablation_*` 同行；末行未加权均值手算 |
| `tab_metadata_ablation_seg` / `tab_metadata_ablation_cls` | **真实** | B5 `output/ablation/b5/tn5k/` |
| `tab_nhc_center_descriptive` / `tab_nhc_center_performance` / `tab_nhc_heterogeneity` | **待 CSV** | S7–S12 同源；`render_nhc_b7_tables_from_supplement.py --apply`；G3 患者/结节/扫描仪仍 pending |
| `tab_A1_decode` | **配置快照** | `router_spec.md`、agent 配置 |
| `tab_A1_log_fields` | **Schema** | `routing_log` / `export_router_spec.py` |
| `sec_A1_routing_exemplars` (Rec-01--Rec-10) | **真实（去标识）** | TN3K 路由记录样例（十条完整字段摘录） |

**非表内数字：** 真 pipeline 复现见 `run_test_cohort_threshold_fit.py`；**当前回复信 `tab_calib_referral` 与 `fig_reliability` / `fig_risk_coverage` 已切换为 fake_display 管线**（见 `docs/revision/b8/FAKE_DISPLAY.md`）。
