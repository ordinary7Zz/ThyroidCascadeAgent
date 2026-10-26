# B4 进度与实验结果

**最后更新**：2026-10-26（L1 全队列批跑完成并收口 L1+L2 主表；不含 NHC）

---

## 1. 三层定义（主表）

| 层 | 系统 | 实验来源 | LLM |
|----|------|----------|-----|
| **L1** | 单 DINO `all_datasets` 专家（堆叠 development 联合训练） | `run_l1_cohort.py` → `artifacts/b4_l1_<cohort>.json` | 否 |
| **L2** | 专家池 + 固定软投票（B3 **策略 2**） | `b3/<cohort>/soft_voting/b3_metrics.json` | 否 |
| **L3** | 池 + LLM 全系统（B3 **策略 7** ≈ 投稿 S4） | `b3/<cohort>/llm/b3_metrics.json` | 是 |

**L1 单专家权重**（各 cohort 相同，见 `config/revision/b4/l1/_single_expert_models.yaml`）：

- 分割：`dinov3_unet` / `all_datasets` → `../Segmentation_Agent/weights/all_datasets/dino_unet_train_all_datasets_epoch_40.pth`
- 分类：`dinov3_unet_multitask` / `all_datasets` → `../Classification_Agent/weights/all_datasets/dino_unet_train_all_datasets_epoch_40.pth`
- 推理：`enable_agent=false`，`radiomics_judge=false`（无 AutoGluon）

---

## 2. 进度看板

| 交付项 | 状态 | 说明 |
|--------|------|------|
| L1 外测（9 cohort） | ✅ | sample, tn3k, tn5k, thyroidxl, ddti_cls, ddti_seg, pktn, zjh8k, rjh7k |
| L1 外测 NHC | ⏸️ | `labels.json` 路径不存在，批处理失败；暂搁置 |
| L2 写入 B4 主表 | ✅ | 来自既有 B3 `soft_voting`，已 `build_b4_tables` |
| L3 写入 B4 主表 | 🟡 | **仅 sample** 有旧版 `b3/sample/llm`（n=10）；**正式 8 队列缺全量 LLM** |
| Path B 附录 B-a/B-b/B-c | ⬜ | 依赖 `soft_voting`、`path_b_autogluon`、`llm` |
| S6 vs S4 对账备忘录 | ⬜ | `docs/B4_S6_S4_reconciliation.md` 仍为模板 |
| 层间 Δ 配对 bootstrap CI | ⬜ | 主表现为点估计 Δ |
| 稿面 Results / R2.8 段落 | ⬜ | 待 L3 定稿 |

---

## 3. L1 + L2 实验结果（点估计）

统计：`evaluate_pipeline` / B3 表内 **图像级 bootstrap**（1000 次，seed=42），与当前 B2 定稿前口径一致。  
**Δ** 来自 `b4_component_table.csv` 中 `Δ(L2-L1)` 行（点估计，无配对 CI）。

### 3.1 分割 Dice

| cohort | n（seg） | L1 Dice | L2 Dice | Δ(L2−L1) |
|--------|----------|---------|---------|----------|
| sample | 10 | 0.8567 | 0.8075 | −0.0492 |
| tn3k | 614 | 0.8454 | 0.8559 | +0.0105 |
| tn5k | 1000 | 0.8292 | 0.8097 | −0.0195 |
| thyroidxl | 2090 | 0.8792 | 0.8640 | −0.0153 |
| ddti_seg | 637 | 0.8492 | 0.8451 | −0.0041 |
| pktn | 150 | 0.8388 | 0.8376 | −0.0012 |
| zjh8k | 7958 | 0.8376 | 0.8356 | −0.0021 |
| rjh7k | 7288 | 0.9128 | 0.8931 | −0.0198 |

### 3.2 分类 AUROC

| cohort | n（cls） | L1 AUROC | L2 AUROC | Δ(L2−L1) |
|--------|----------|----------|----------|------------|
| sample | 10 | 0.8400 | 0.9200 | +0.0800 |
| tn3k | 614 | 0.7695 | 0.8282 | +0.0587 |
| tn5k | 1000 | 0.9544 | 0.9437 | −0.0107 |
| thyroidxl | 2090 | 0.9288 | 0.9359 | +0.0071 |
| ddti_cls | 349 | 0.7506 | 0.7537 | +0.0031 |
| zjh8k | 7958 | 0.9571 | 0.9322 | −0.0249 |

`ddti_seg` / `pktn` / `rjh7k` 当前 L1 配置为 **仅分割**，表中无 AUROC。`ddti_cls` 为 **仅分类**，无 Dice。

### 3.3 简要解读（供 R2.8 起草，非终稿结论）

- **TN3K**：L2 相对 L1 在 Dice / AUROC 上均有提升 → 专家池+平均有增量。
- **ZJH-8K**：L1 单专家 AUROC（0.957）高于 L2（0.932）→ 与 S6/S4 反差同一脉络，需对账备忘录说明协议差异；L3 全系统待 LLM 跑完后对比。
- **多队列**：L2 分割 Dice 并非处处高于 L1（如 tn5k、thyroidxl、rjh7k），主文应报告 **逐队列** 结果，避免声称「池化必然更好」。

### 3.4 L3（sample 仅作开发参考）

| cohort | L3 Dice | L3 AUROC | 备注 |
|--------|---------|----------|------|
| sample | 0.8368 | 0.9200 | 旧 `b3/sample/llm`，与 L2 同 n=10；**不替代正式队列 LLM** |
| 其余 8 队列 | — | — | 待 B3 波次 2 全量 `llm` |

---

## 4. 产物路径

| 类型 | 路径 |
|------|------|
| L1 指标 JSON | `artifacts/b4_l1_<cohort>.json` |
| L1 跑数目录 | `output/ablation/l1/<cohort>/run1/` |
| B4 主表 | `output/ablation/b4/<cohort>/b4_component_table.csv` |
| L1+L2 合并 CSV | `output/ablation/b4/b4_l1_l2_summary.csv` |
| L1 批处理日志 | `output/ablation/l1/l1_remaining_batch.log` |
| 批处理摘要 | `output/ablation/l1/_batch_logs/summary_20261026_001859.txt` |

---

## 5. 下一步（建议顺序）

1. **B3 波次 2**：各正式 cohort `routing_mode=llm`（需 `DASHSCOPE_API_KEY`），写出 `b3/<cohort>/llm/b3_metrics.json`。
2. **再跑** `build_b4_tables.py` → 补齐 L3、S4_check。
3. （可选）`run_b4_pathb_appendix.py` → Path B 放射组学分解表。
4. 填写 `docs/B4_S6_S4_reconciliation.md`；B2 cluster 定稿后重算 Δ CI。

---

## 6. 复现命令

```bash
# 单 cohort L1（全量重跑）
python scripts/revision/b4/run_l1_cohort.py --cohort tn3k --device cuda --fresh

# 收口 B4 表（L1+L2+L3 若已有 llm）
python scripts/revision/b4/build_b4_tables.py --config config/revision/b4/tn3k.yaml
```

批处理记录：2026-10-26 00:18–02:24，`run_l1_remaining_background.sh`，7/8 成功（NHC 失败）。
