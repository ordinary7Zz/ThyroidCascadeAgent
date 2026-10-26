# B3 审稿回复草稿片段（波次 1 + 策略 6 learned + 策略 7 LLM）

> 可直接粘贴到返修回复 LaTeX / Markdown。静态策略见 `B3_WAVE1_RESULTS.md`；**策略 6** 见 `B3_LEARNED_RESULTS.md`；**策略 7** 见 `B3_LLM_RESULTS.md`（= 主文 Table S3/S4，**2026-10-26**）。R14–R15 由 `export_b3_response_letter_tables.py` 导出（策略 7 读 `manuscript_llm_metrics.yaml`）。

---

## R1.2 / R2.8 — 路由消融（静态 + Oracle + learned）

**中文（草稿）**

我们按审稿人建议，在**固定专家池与同一套 Phase 1–2 中间结果**上，系统比较了多种路由策略（验证集最优单专家、软投票、多数票、静态规则、最大置信度）、**验证集拟合的多项逻辑回归学习型路由（策略 6）**及 Oracle 上界；分割与分类主指标均报告 **点估计及 95% CI**（cluster bootstrap，与 B2 一致），分类同时报告**全测试集**与 **Path B（独立模型分歧）子集**。在 OpenThyroid 三队列（TN3K *n*=614，TN5K *n*=1000，ThyroidXL *n*=2090）上，静态策略结论见波次 1 摘要：最大置信度分割在 TN3K/TN5K 明显劣于集成；分类上无单一静态策略全面占优。**学习型路由（策略 6）**在 TN5K 分割上与最优单专家相当（Dice 0.8309 vs 0.8309），TN3K 分类全量 AUROC 0.8141（Path B 0.6766）。**LLM 全系统路由（策略 7）** 与投稿主文一致（如 TN3K 分割 Dice 0.8528、分类 AUROC 0.8692；ZJH-8K 分割 Dice 0.9430），见 `B3_LLM_RESULTS.md`，未为节省 API 在消融 intermediate 上重跑。院外队列 learned 与静态策略见 `B3_LEARNED_RESULTS.md`。**NHC-MISD-TUS** 全系统结果见主文，未展开为八策略子表。

**English (draft)**

We compared routing strategies on a **fixed expert pool** with shared Phase 1–2 intermediates: validation-selected best single expert, ensembling and static rules, **validation-fitted multinomial logistic learned routers (strategy 6)**, and an oracle upper bound, with **95% cluster-bootstrap CIs** and full-set plus **Path B** classification metrics. On TN3K, TN5K, and ThyroidXL, static routers show cohort-dependent trade-offs (e.g., max-confidence segmentation underperforms ensembling on TN3K/TN5K). **Learned routing (strategy 6)** matches the best single expert on TN5K segmentation (Dice 0.8309) with TN3K full-set AUROC 0.8141 (Path B 0.6766). **LLM full-system routing (strategy 7)** matches the primary manuscript (Table S3/S4; e.g., TN3K segmentation Dice 0.8528, classification AUROC 0.8692; see `B3_LLM_RESULTS.md`) without re-invoking the API on ablation intermediates. External cohorts for strategies 1–6 and 6 are in `B3_LEARNED_RESULTS.md`. NHC-MISD-TUS full-system results remain as in the main text.

---

## R3.1 — 路由泛化

**中文（草稿）**

除 TN3K/TN5K/ThyroidXL 外，我们在 **ZJH-8K、RJH-7K（分割）、DDTI（分割/分类分队列）、PKTN（分割）** 上完成了与院内队列相同的 B3 协议（含策略 6）。例如 RJH-7K 学习型分割 Dice 0.909 (0.906–0.911)，稿面全系统（策略 7）RJH-7K 分割 Dice 0.9146；ZJH-8K 学习型分类 AUROC 0.957 (0.950–0.965)，策略 7 为 0.9175 (0.9008–0.9342)。**NHC-MISD-TUS** 八策略子表仍待补；其余队列策略 7 见 `B3_LLM_RESULTS.md`。

**English (draft)**

Beyond the three OpenThyroid test sets, we ran the same B3 protocol—including **learned routers**—on ZJH-8K, RJH-7K (segmentation only), DDTI (separate seg/cls cohorts), and PKTN (segmentation only); see `B3_LEARNED_RESULTS.md` for strategies 1–6 and 8. **Strategy 7** on these cohorts matches Table S3/S4 (e.g., RJH-7K segmentation Dice 0.9146; ZJH-8K classification AUROC 0.9175; `B3_LLM_RESULTS.md`). NHC-MISD-TUS remains pending for the eight-strategy sub-table.

---

## 建议正文/补充表题（Table caption 草案）

*Table X. Routing ablation on a shared expert pool.* Segmentation Dice and HD95 on the full test set; classification AUROC and AUPRC on the full set and on the Path B subset (where available). Strategies 1–5 and 8 from wave 1; strategy 6 from validation-fitted routers; **strategy 7 identical to primary ThyroidXAgent (Table S3/S4)**. Oracle is non-deployable.
