# B11 / B12 返修确认包

**B11/B12 的回复信与 Methods 改稿素材集中在本目录**（勿写入 `docs/ThyroidXAgent_返修计划与回复_中文.md`）。

| 文件 | 用途 |
|------|------|
| [`REVIEWER_SNIPPETS_ZH.md`](REVIEWER_SNIPPETS_ZH.md) | R2.20、R2.21、R2.7/R2.1、R1.4 中文回复草稿 |
| [`DATAFLOW_FIGURE_PLAN.md`](DATAFLOW_FIGURE_PLAN.md) | **数据流图版面与泳道设计（B12+S9）** |
| [`DATAFLOW_FIGURE.mmd`](DATAFLOW_FIGURE.mmd) | Mermaid 源图（可导出 SVG） |
| [`IMAGE_DATAFLOW_DRAFT.md`](IMAGE_DATAFLOW_DRAFT.md) | B12 图像侧要点（旧简稿） |
| [`../../reproducibility_radiomics.md`](../../reproducibility_radiomics.md) | R2.21 技术附录 |

本目录汇总 **已核对** 与 **待 B1/制图** 项。

## 已确认（无需重跑主实验）

### Table S4 宏平均（`docs/ThyroidXAgent.md` Table `tab:cls_performance` ThyroidXAgent 行）

| 指标 | 等权宏平均（5 个分类测试队列） | 按测试图像数加权 |
|------|--------------------------------|------------------|
| AUROC | **0.9001** | **0.9228** |
| AUPRC | **0.8705** | **0.9533** |

队列与点估计：TN3K 0.8692 / 0.8545，ThyroidXL 0.9676 / 0.9653，TN5K 0.9472 / 0.9752，DDTI 0.7991 / 0.5863，ZJH-8K 0.9175 / 0.9711。  
加权样本量：614 + 2090 + 1000 + 349 + 7958（Table S1）。

**稿件动作**：摘要/2.2 的 0.9466 / 0.8361 改为上表宏平均；图注写明「unweighted mean across five test cohorts」并可选给出加权列。

复算脚本：仓库内可用 `python3 -c` 对上述五点与 n 列表计算（见本 README 提交时的核对记录）。

### R2.21

见 [`docs/reproducibility_radiomics.md`](../../reproducibility_radiomics.md)。

### R2.20 机制（无 radiomics CCA）

- 上报 Dice：`selected_masks`。
- Radiomics：同一 mask，无二次 CCA。
- 专家 DINO：≥50 px CC + closing；集成可选最大连通域。

## 已跑分析（R2.20b）

见 **`tables/R2_20_SUMMARY.md`**（ZJH-8K：&lt;5 mm **N=1001，M=44**；TN3K：**N=68，M=2**；`mm_per_pixel=0.1` 为假设）。

| 队列 | 结果 JSON | 说明 |
|------|-----------|------|
| TN3K | `tables/r2_20_tn3k.json` | 本地 pipeline `output/TN3K/pipeline_run` |
| ZJH-8K | `tables/r2_20_zjh8k.json` | 本地 pipeline `output/ZJH-8K/pipeline_run` |

**毫米径**：定稿前需与 **B1/像素间距** 对齐后重跑 `scripts/revision/b11/analyze_r2_20_small_nodules.py`；主结果若用不同 routing config，需对 **同一 config 的 selected_masks** 重跑。

**批量（推荐）**：

```bash
./scripts/revision/b11/run_r2_20_small_nodules_all.sh
# MM_PER_PIXEL=0.1 可改；汇总表 tables/R2_20_SUMMARY.md 自动生成
```

单队列命令：

```bash
python scripts/revision/b11/analyze_r2_20_small_nodules.py \
  --gt-mask-dir /path/to/test/masks \
  --selected-npz output/<COHORT>/pipeline_run/intermediate/selected_masks.npz \
  --mm-per-pixel 0.1 \
  --output docs/revision/b11_b12/tables/r2_20_<cohort>.json
```

## B12 数据流（文字稿 + 待制图）

见 [`IMAGE_DATAFLOW_DRAFT.md`](IMAGE_DATAFLOW_DRAFT.md)。与 **S9** 报告侧合并前，节点样本量以 **Table S1** 与 **B1 审计** 为准。

## 仍依赖他人 / 未在本仓库完成

- [ ] **B1**：各队列 train/val/test 患者级互斥、ZJH-8K 内外部定性 → 填入数据流图。
- [ ] **S9**：SMU-HMC、KMVE、ZJH-TS、TNVideo、模板库划分。
- [ ] **B8**：拒答阈值 `abstention_thresholds.json`（验证集 fit）→ 图中标注。
- [ ] **主结果 config 快照**：投稿 LLM 路由 vs `nhc_no_llm_primary` 需在图中区分 S4 与 NHC 部署假设。
- [ ] **Fig.1 / Supp. 数据流** 最终版式（G2）。

## 回复信素材

见 [`REVIEWER_SNIPPETS_ZH.md`](REVIEWER_SNIPPETS_ZH.md)（对应返修计划 B11 / B12 与 A7 宏平均条目）。
