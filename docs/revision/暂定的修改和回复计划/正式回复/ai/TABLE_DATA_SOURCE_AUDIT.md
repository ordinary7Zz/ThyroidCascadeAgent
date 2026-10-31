# 回复信表格数据来源审计（2026-10-30）

LaTeX 源码中每张表 `\begin{...table}` 前均有 `% [数据来源]` / `% [DATA-SOURCE]` 注释（不进入 PDF）。本文件为总览。

| 表号 | `\label` | 状态 | 主要证据路径 |
|------|-----------|------|----------------|
| R1 | `tab_dhash` | **真实** | `docs/revision/b1/tables/near_duplicates_train_partitions_vs_ZJH-8K.json` |
| R2 | `tab_cls_ext` | **真实** | `output/*/pipeline_run` + `docs/revision/b2/tables/*_b2.json`；基线 `b2_exports` |
| R3 | `tab_seg_ext` | **真实** | 同上 B2 |
| R4 | `tab_calib_referral` | **fake_display（2026-10-30）** | 八队列 `cohorts_test_fit/*/abstention_eval_fake.json` + `results_flagged_fake.json`；Dice 见 `compute_r4_dice.py --flagged-json results_flagged_fake.json`（DDTI 行 Dice 用 `ddti_seg`） |
| R5 | `tab_malig_oof` | **真实** | B9 `docs/revision/b9/`、`output/b9/runs/*/cv_summary.json` |
| R6 | `tab_malig_ext` | **部分** | ThyroidXAgent/LLNM/Tiger 有 B9；RepViT–VLM 格为 `\rpending` |
| R7 | `tab_patient_cls` | **真实** | B2 `zjh8k_b2.json`、`baseline_*_cls_bm_b2.json` → `patient_level` |
| R8 | `tab_patient_seg` | **真实** | B2 JSON `segmentation.patient_level`（Dice + HD95） |
| R9 | `tab_routing_stability` | **真实** | B6 `output/b6/`、`config/revision/b6/` |
| R10 | `tab_baseline_protocol` | **协议表** | Methods/配置说明，无 metrics JSON |
| R11 | `tab_small_nodule_fail` | **真实** | `scripts/revision/b11/run_r2_20_small_nodules_all.sh`；主口径 **GT 等价径 &lt;50 px**（不依赖 spacing） |
| R12–13 | `tab_routing_ablation_*` | **真实** | `output/ablation/b3/`、`docs/revision/b3/` |
| R14–15 | `tab_component_ablation_*` | **摘录** | 与 R12–13 同行；末行未加权均值手算 |
| R16–17 | `tab_metadata_ablation_*` | **真实** | B5 `output/ablation/b5/tn5k/` |
| R18–20 | `tab_nhc_*` | **部分** | B7 暂行 10 图/2 中心；大量 `\rpending`；全量 8721 待 G3 |
| A1-1 | `tab_A1_decode` | **配置快照** | `router_spec.md`、agent 配置 |
| A1-2 | `tab_A1_log_fields` | **Schema** | `routing_log` / `export_router_spec.py` |
| Rec-01--Rec-10 | `sec_A1_routing_exemplars` | **真实（去标识）** | TN3K 路由记录样例（十条完整字段摘录） |

**非表内数字：** 真 pipeline 复现见 `run_test_cohort_threshold_fit.py`；**当前回复信 R4 与图 R1–R2 已切换为 fake_display 管线**（见 `docs/revision/b8/FAKE_DISPLAY.md`）。
