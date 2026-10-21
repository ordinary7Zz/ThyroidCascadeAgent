# B8　校准与拒答（结论文档 · 草稿）

> **审稿关切**：R1.3 / R1.6 — 可靠性（ECE、Brier）、拒答/强制复核规则、风险–覆盖率及各中心送复核比例（供 F4 临床叙事）。  
> **状态**：**烟雾版数值**（伪 validation = TN3K+TN5K+ThyroidXL+PKTN 的 **test** 合并定阈，`n=3854`）。**不可写入稿面**；正式稿仅替换为 `output/validation/no_llm_primary` + `output/b8/fit/` 定稿结果。

---

## 1. 数据卡（换 **真 validation** 时 **优先改本节**）

| 字段 | 当前值（smoke） | 定稿替换为 |
|------|-----------------|------------|
| 定阈数据 | 伪 val：`output/b8/smoke_test_as_val/pseudo_val/results.json` | `output/validation/no_llm_primary/results.json` |
| 定阈样本量 `n_val` | **3854**（614+1000+2090+150 test） | `merge_manifest.json` → `n_total`（目标 **875** 或稿面 **850**） |
| 阈值文件 | `output/b8/smoke_test_as_val/fit/abstention_thresholds.json` | `output/b8/fit/abstention_thresholds.json` |
| 各队列 eval 目录 | `output/b8/smoke_test_as_val/cohorts/<cohort>/` | `output/b8/cohorts/<cohort>/` |
| Pipeline 协议 | 与各队列 **test** `pipeline_run` 一致（B3 主配置） | 与 **`config/revision/nhc_no_llm_primary.yaml`** 一致（**`enable_agent: false`**）的 validation pipeline |
| 规则子集 | `rule_subset=nhc`（熵、margin、分割 IoU；无 LLM 路由标志） | 同左 |
| 组合逻辑 | `combination=any`（任一规则触发即送复核） | 同左 |
| 分位数 | `quantile=0.9`（`fit_thresholds_quantile`） | 同左（若改分位数需同步 Methods） |

**复现命令（定稿）：**

```bash
export PYTHON=/mnt/wangbd8/workspace/envs/thyroid_infer/bin/python
./scripts/run_openthyroid_validation_b8.sh          # 或 --skip-pipeline
./scripts/run_b8_all_cohorts.sh
```

烟雾版仅作对照：

```bash
./scripts/run_b8_smoke_test_as_val.sh
```

---

## 2. 方法要点（换数时 **一般不必改**）

1. **校准**：在测试集 `results.json` 上报告 **ECE**、**Brier** 及可靠性图（`calibration_test.json`、`reliability_test.png`）。  
2. **拒答**：在 **validation** 上按不确定度字段分位数定阈，导出 `abstention_thresholds.json`；在 **test** 上应用同一阈值，报告送复核比例及 **risk–coverage**（`abstention_eval.json`）。  
3. **信号（NHC 子集）**：`vote_entropy`（高→拒答）、`margin_top2_min`（低→拒答）、`seg_min_pairwise_iou`（低→拒答）。  
4. **与 F4 衔接**：`results_flagged.json` 中 `flagged_for_review` 供误分类与工作量统计。

---

## 3. 冻结阈值（smoke，`n_val=3854`）

| 规则名 | 字段 | 操作 | 阈值 |
|--------|------|------|------|
| `cls_vote_entropy` | `vote_entropy` | `>` | **0.918** |
| `cls_margin_low` | `margin_top2_min` | `<` | **0.036** |
| `seg_iou_low` | `seg_min_pairwise_iou` | `<` | **0.0049** |

伪 validation 上 pooled 分类校准（有 `malignancy` 标签者 **n≈3704**）：**ECE ≈ 0.080**，**Brier ≈ 0.118**。

---

## 4. 各测试队列评估（smoke 阈值；§4 表格 **整表替换**）

送复核比例 = `n_flagged / n_total`。分类准确率仅在存在 `malignancy` 标签的病例上计算；**保留子集** = 未 `flagged_for_review` 的子集。

| 队列 | n | 送复核 n | 送复核 % | ECE | Brier | 全量 cls Acc | 保留子集 cls Acc | Δ Acc |
|------|---|----------|----------|-----|-------|--------------|------------------|-------|
| TN3K | 614 | 153 | 24.9% | 0.183 | 0.200 | 75.1% | 79.2% | +4.1 pp |
| TN5K | 1000 | 255 | 25.5% | 0.066 | 0.083 | 90.3% | 93.2% | +2.9 pp |
| ThyroidXL | 2090 | 431 | 20.6% | 0.073 | 0.110 | 86.6% | 90.9% | +4.3 pp |
| ZJH-8K | 7958 | 2129 | 26.8% | 0.097 | 0.110 | 88.1% | 89.1% | +1.1 pp |
| DDTI_cls | 349 | 38 | 10.9% | 0.093 | 0.110 | 86.8% | 90.4% | +3.5 pp |
| RJH-7K | 7288 | 1180 | 16.2% | —† | —† | — | — | — |
| DDTI_seg | 637 | 637 | **100%** | —† | —† | — | — | — |
| PKTN | 150 | 150 | **100%** | —† | —† | — | — | — |
| sample | 10 | 2 | 20.0% | 0.256 | 0.182 | 70.0% | 87.5% | +17.5 pp‡ |

† 无（或极少）恶性标签用于分类校准，ECE/Brier 记为 0 或不可估，**不代表模型完美**。  
‡ `n=10`，仅调试，不写入主文。

**smoke 解读（定稿后需用 validation 阈值重述）：**

- 有 BM 标签的主外测队列送复核约 **21%–27%**，与「不确定度分位数定阈」预期一致。  
- 保留子集分类准确率略高于全量（约 **+1～+4 pp**），说明信号与错例有一定相关；**因阈值在含同队列 test 的伪 val 上拟合，该提升偏乐观**，真 validation 后应下调表述强度。  
- **PKTN / DDTI_seg 全员送复核**：伪 val 含 PKTN test、且 seg-only/无 BM 队列与 **同一套分类阈值** 不兼容所致；定稿时建议 **主文只汇总有 BM 的队列**，或单独说明 seg-only 队列仅报告分割侧不确定度（待与 F4 对齐）。

---

## 5. 撰稿占位（validation 定稿后填数）

> We fixed abstention thresholds on the OpenThyroidDB **validation** set (*n* = **[850 或 875]**) using the same non-LLM cascade as the primary evaluation (`enable_agent: false`). A case was flagged for human review if **any** of the following held: classification vote entropy **> [T1]**, top-2 margin **< [T2]**, or minimum pairwise segmentation IoU **< [T3]**. On **[cohort]** (*n* = **[N]**), **[X]%** of cases were flagged; among non-flagged cases with histology labels, classification accuracy was **[Y]%** (vs **[Z]%** without abstention). Pooled validation calibration yielded ECE **[…]** and Brier **[…]** (reliability diagram: Supplementary Fig. **[…]**).

将 `[T1–T3]`、`[X/Y/Z]`、ECE/Brier 从 §3–§4 换为定稿表即可。

---

## 6. 定稿检查清单

- [ ] `abstention_thresholds.json` 的 `n_val` 与 `merge_manifest.json` 一致，且 **≠ smoke 的 3854**  
- [ ] 阈值路径为 `output/b8/fit/`，eval 为 `output/b8/cohorts/`（**非** `smoke_test_as_val`）  
- [ ] NHC 主结果（若单独跑）使用同一阈值文件做 `run_calibration_abstention.py --eval`  
- [ ] 补充图：各主队列 `reliability_test.png`、risk–coverage 曲线（由 `abstention_eval.json` 绘制）  
- [ ] 与 `docs/ThyroidXAgent_返修计划与回复_中文.md` B8 / F4 条目数字一致  

---

## 7. 相关路径

| 用途 | 路径 |
|------|------|
| 计划 | `docs/REVISION_B7_B8_PLAN.md` |
| 烟雾脚本 | `scripts/run_b8_smoke_test_as_val.sh` |
| Validation 一键 | `scripts/run_openthyroid_validation_b8.sh` |
| 测试队列批量 eval | `scripts/run_b8_all_cohorts.sh` |
| 代码 | `pipeline/calibration.py`、`pipeline/abstention.py`、`scripts/run_calibration_abstention.py` |
