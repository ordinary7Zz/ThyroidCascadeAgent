# B3 审稿回复草稿片段（波次 1 部分结果）

> 可直接粘贴到 `ThyroidXAgent_返修计划与回复_中文.md` 或英文回复信。主表数字格式为 **点估计（95% CI）**（见 `B3_WAVE1_RESULTS.md`）；定稿前请替换为 **患者/检查级 cluster bootstrap** 并重算 CI，并补全 NHC 等队列。

---

## R1.2 / R2.8 — 路由消融（静态策略 + Oracle，进行中）

**中文（草稿）**

我们按审稿人建议，在**固定专家池与同一套 Phase 1–2 中间结果**上，系统比较了多种路由策略（验证集最优单专家、软投票、多数票、静态规则、最大置信度）及 Oracle 上界；分割与分类主指标均报告 **点估计及 95% CI**（定稿与 B2 一致为患者/检查级 cluster bootstrap），策略间比较采用 **配对 bootstrap 差分 CI**；分类同时报告**全测试集**与 **Path B（独立模型分歧）子集**，Path B 上静态策略**不**纳入 AutoGluon，以与后续 LLM 路由（投稿 S4 协议）区分。在已完成波次 1 的三个测试队列上（TN3K *n*=614，TN5K *n*=1000，ThyroidXL *n*=2090），主要发现如下：（1）分割上，最大置信度路由在 TN3K/TN5K 上显著劣于集成类策略（例如 TN5K Dice 0.63 vs 软投票 0.81），Oracle 上界（Dice 0.88–0.90）表明仍有可观路由增益空间；（2）分类上，**不存在单一静态策略在所有队列上最优**（例如 TN3K 软投票 AUROC 最高 0.83，TN5K 静态规则/最大置信度略优于软投票 0.95 vs 0.94）；（3）Path B 约占 40–45% 病例，是分类路由差异的主要来源。LLM 路由与非 LLM 学习型路由的完整八策略表、配对检验及 **NHC-MISD-TUS** 队列结果将在修订稿主表/补充表中一并给出（见 `docs/revision/b3/B3_WAVE1_RESULTS.md`）。

**English (draft)**

We performed routing ablation on a **fixed expert pool** with shared Phase 1–2 intermediates, comparing validation-selected best single expert, soft voting, majority vote, static rules, max-confidence routing, and an oracle upper bound. All primary metrics are reported as **point estimates with 95% CIs** (cluster bootstrap aligned with patient/exam-level resampling at revision freeze), with **paired bootstrap difference CIs** for strategy comparisons. Classification is reported on the **full test set** and on the **Path B disagreement subset** (~40–45% of cases), where static routers use independent models only (no AutoGluon), distinct from the submitted S4 LLM protocol. Across TN3K (*n*=614), TN5K (*n*=1000), and ThyroidXL (*n*=2090), no single static router dominates: max-confidence segmentation underperforms ensembling on TN3K/TN5K, while the best static classifier varies by cohort (e.g., soft voting AUROC 0.828 on TN3K vs. static rule/max-confidence 0.951 on TN5K). Oracle gaps (e.g., segmentation Dice up to ~0.90 vs. ~0.86 for the best deployable static route on TN3K) motivate our ongoing comparison with LLM and learned routers and external validation including NHC-MISD-TUS.

---

## R3.1 — 路由泛化（待补队列）

**中文（占位）**

波次 1 已完成 TN3K、TN5K、ThyroidXL 三队列；**ZJH-8K、RJH-7K、DDTI、PKTN 及 NHC-MISD-TUS** 正在同一协议下补跑。修订稿将报告各队列上 **最佳非 LLM 静态路由 vs LLM 路由** 的排序，并专门检验在未见中心（NHC）上与院内队列（如 ZJH-8K）上结论是否一致；中心级异质性（I² 等）见补充分析 B7。

---

## 建议正文/补充表题（Table caption 草案）

*Table X. Routing ablation (wave 1) on a shared expert pool.* Segmentation Dice and HD95 on the full test set; classification AUROC and AUPRC on the full set and on the Path B subset (independent-model disagreement only). Strategies 1–5 and 8 (oracle) are shown; LLM (strategy 7) and learned routing (strategy 6) are reported separately after wave 2–3. Oracle denotes a non-deployable upper bound. Cohorts: TN3K, TN5K, ThyroidXL (*n* as in text); additional cohorts including NHC-MISD-TUS in revision.
