# 稿件修改计划（中文）

> **对照稿件**：`docs/ThyroidXAgent.md`（LaTeX 源稿）  
> **对照结论**：`docs/revision/b*/` 各包结论文档  
> **用途**：指导修订稿 **Methods / Results / 摘要 / 图表** 的改写顺序；数值可先占位，定稿前用最新 JSON/表替换。  
> **不修改**：`docs/ThyroidXAgent_返修计划与回复_中文.md`（内部计划原件）。  
> **范围**：仅 **B1–B12** 对应的稿面修改；**不含** Shiyu **S1–S10**（报告生成 §2.5–2.6、Methods 4.4–4.5、Fig.5、读者研究等由共同作者另稿）。  
> **写稿流程**：**本文件为唯一「拟改稿」清单**；**暂不直接修改** `docs/ThyroidXAgent.md`，待返修统稿时按 §8–§9 等条目一次性合并进 LaTeX 源稿。  
> **语言**：仅维护本中文计划（无英文平行稿）。  
> **进行中（2026-10-26）**：**B5**（R3.2，§14，**接近定稿**：sample 占位 → TN5K 换数）、**B7**（R1.3 NHC + R2.6，G3）。  
> **已归档**：**B1–B4、B6、B8–B12** → 本文件 **§7–§16** 与各 `docs/revision/b*/` 真源；统稿时并入 `ThyroidXAgent.md` / `正式回复/latex`，**勿**在本目录扩写新长表。快照见 [`README.md`](./README.md)。

---

## 进行中的工作包

| 包 | 稿面/回复 | 仓库入口 | 备注 |
|----|-----------|----------|------|
| **B5** | R3.2；元数据消融 | `../b5/`；**§14** | 五 mode 已齐（**表内 sample 占位**）；**TN5K 换数**；NHC 热图待 |
| **B7** | R1.3（NHC 段）、R2.6 | `../b7/B7_NHC_SCOPE_SUMMARY_ZH.md` | 中心元数据 **G3** |

**已归档包索引**：B1/B2 → §2–§4 与 `REVIEWER` B1+B2 专项；B10 → §10；B6 → §11；B8 → §12；B3 → §13；B4 → §15；B9 → §16；B11/B12 → §8–§9。见 [`README.md`](./README.md) 归档表。

---

## 图例

| 就绪度 | 含义 |
|--------|------|
| **可改** | 结论文档与数字/叙事已齐，可直接写入修订稿（CI 等可后换数） |
| **框架可改** | 段落结构与定义可写，数字或图待补 |
| **待协作** | 依赖 Fei Chen / Shiyu / F6 / NHC 等，稿面仅写「将补充」或 Limitations |

---

## 1. 摘要（Abstract）

| 修改点 | 现稿问题 | 建议改写 | 依据 | 就绪度 |
|--------|----------|----------|------|--------|
| 测试规模表述（**图像/OpenThyroid 部分**） | 「28,458 … test cases」混用层级 | 在摘要/§2.1 写明 **分割+分类 test 图像数**、NHC 计数；**全文 28,458 的完整拆解**需与共同作者统一（报告/视频不在 B12 单包内） | B12 计划；B1 | **框架可改** |
| 平均 Dice / AUROC / AUPRC（**分类五队列**） | 与 Supplementary Table S4 不一致 | **无权重宏平均** AUROC **0.9001**、AUPRC **0.8705**（脚注可给加权） | `b11_b12/README.md` | **可改** |
| 摘要中报告/读者研究一句 | — | **不在本计划修改**（无 S 任务素材） | — | **范围外** |
| LNM / FTC/PTC AUROC | 与 **§16 / B9 归档** S5 灰底行一致 | OOF 数见 `b9/B9_ThyroidXAgent_修改与回复计划.md` §2；FTC **域迁移** 见 `需要确认.md` | **§16** | **可改**（全栈 OOF、E2/E4 在 b9 主文档更新） |

---

## 2. Results

### 2.1 数据与 OpenThyroidDB（§2.1 第一段及恶性亚组段）

| 修改点 | 建议 | 依据 | 就绪度 |
|--------|------|------|--------|
| 数据层级与流程图（**图像侧，B12**） | Fig.1 需按组件划分 train/val/test | 专家、路由、放射组学、LNM、FTC 的**图像任务**泳道；Mermaid 见 `b11_b12/` | **框架可改**（导出图；B1 节点待 F6） |
| ZJH-8K 定位 | **主结果**全量 **7958 图 / 1146 患者**；同院 TN3K 用 **dHash 图级重复** 表述（train↔ZJH **995** 对 H=0；TN3K test↔ZJH **2** 对 H=0）；**患者交集**仍待 F6（可选 Limitation） | `b1/B1_结论与回复素材.md`；`b1/tables/near_duplicates.json` | **可改**+**待协作**（F6 可选） |
| DDTI_cls 规模 | 分类外测 **n=349**（`DDTI_Classification/all/` + 标签 JSON）；勿与 `test/` 子目录 ~53 图混用；与 **DDTI_seg 637** 分任务叙述 | B1；`b2/tables/ddti_cls_b2.json` | **可改** |
| 训练–外测独立性（B1） | **主审计：dHash**（64-bit，H≤5）；**勿**写 stem=0 证明无泄漏（跨库命名无鉴别力）；stem JSON 仅仓库自检 | `scripts/revision/b1/audit_near_duplicates.py`；`b1/tables/train_test_overlap.json` | **可改** |
| ZJH 敏感性（train 重复图） | **主表仍全量**；Supp. 表：**全量 vs 剔除 train-matched（992 图，6966/1078）**；主系统+ZJH 基线 JSON 已算 | `zjh8k_b2_excl_train_dup.json`；`baseline_*_zjh8k_*_b2_excl_train_dup.json` | **可改** |
| LNM 训练规模 | **4753 图 / 882 簇**；20 例 val 不参与本 CV — 见 **§16** / b9 §3 | `B9_ThyroidXAgent_修改与回复计划.md` | **可改** |
| FTC/PTC 训练标签 | **FVPTC ≠ FTC**；探索性域 — **§16** | `b9/需要确认.md` | **框架可改** |

### 2.2 分割与分类（Agent-routed evidence…）【B2/B3/B10/B11】

| 修改点 | 建议 | 依据 | 就绪度 |
|--------|------|------|--------|
| Table S3/S4 点估计与 **95% CI** | 全表改为 **cluster-bootstrap CI**（1000, seed 42）；主系统 `b2/tables/*_b2.json`；监督基线 **58/58**（`BASELINES_INDEX.json`）；**不含 NHC** | `b2/conclusions/B2_结论与回复素材.md` | **可改**（计算已闭环） |
| 补充 **患者级** 分类表 | ZJH-8K、ThyroidXL 患者级 AUROC/AUPRC（概率平均、标签 max） | 同上 §3.2、§4.4 | **可改** |
| **新 Supp.：ZJH 敏感性** | 全量 ZJH vs excl. train dHash H=0（分类+分割；主系统+基线） | `*_b2_excl_train_dup.json`；`BASELINES_INDEX_excl_train_dup.json` | **可改**（统稿制表） |
| DDTI_cls 行 n | 表中 **349** 图、一图一簇 | `ddti_cls_b2.json` | **可改** |
| 正文「mean AUROC 0.9466」等 | 改为与 S4 **宏平均**一致并定义 unweighted | `b11_b12/README.md` | **可改** |
| NHC 柱状图 Fig.2h | 中心异质性待 **B7**；**B8** 校准/拒答已齐（**不含 NHC**），与 Fig.2h 数字无硬绑定 | B7 计划；B8 §12 | **待协作**（B7）；B8 **接近定稿** |
| **路由贡献** 新小节 | **波次 1（策略 1–5、8）** 九队列结论可写：无单一静态策略全胜；max-conf 分割在 TN3K/TN5K 明显差于集成；Path B ~40–45%；Oracle 上界；**策略 6 learned、7 LLM 仅留表位/一句待补数** | `b3/B3_WAVE1_RESULTS.md`、`REVIEWER_RESPONSE_SNIPPETS_B3.md`；`output/ablation/b3/<cohort>/_summary/b3_routing_table.csv` | **接近定稿**（learned/LLM 行 + cluster CI 定稿前换数） |
| **元数据消融（B5 · R3.2）** | **稿面主队列 TN5K**（单列表，非九队列）；**§14.1** 五 mode + **full→quality_only** 叙事已可写（**数字暂为 sample *n*=10**）；TN5K 跑完 **只换表内数字与路径** | `../b5/`；`output/ablation/b5/sample/`（占位）→ `tn5k/` | **可改**（TN5K 换数；NHC 热图待） |
| S6 与 S4 ZJH 矛盾 | **B4 L1–L3** 表 + `B4_S6_S4_reconciliation.md`：单专家/软投票 vs **稿面 LLM 全系统** 协议分述 | `../b4/B4_STATUS_ZH.md`；**§15** | **接近定稿**（对账备忘录待写） |
| **组件消融 L1–L3（B4 · R2.8）** | Supp. 逐队列 L1/L2/L3；L3=**B3 策略 7**（yaml）；叙事见 **§15** | `REVIEWER_RESPONSE_PLAN_ZH.md` **B4 专项** | **接近定稿** |

### 2.3 交互分割与时间【稿内 §2.3，属图像工作流】

| 修改点 | 建议 | 依据 | 就绪度 |
|--------|------|------|--------|
| 时间数字统一 | 9.11 s 等与 Fig.2i 一致 | 内部数字核查清单 | **可改**（核对源日志） |

### 2.4 LNM 与 FTC/PTC【B9 · 已归档】

> **不在本文件维护长表**。改稿、S5 数字、Methods/Results/回复信 → **[§16 B9 归档索引](#16-b9-归档索引r21012lnmftcptc)** 与 **`../b9/B9_ThyroidXAgent_修改与回复计划.md`**（§2–§4）。§2.4 仅保留稿面锚点。

| 修改点 | 建议 | 依据 | 就绪度 |
|--------|------|------|--------|
| Methods/Results + **S5 灰底** | 见 **§16** 摘要；统稿时只改 b9 主文档 | `B9_ThyroidXAgent_修改与回复计划.md` | **可改**（真源在 b9/） |
| 专家行 S5 | LLNM / Tiger | `B9_LNM_*`；`B9_FTCPTC_*`；`B9_回复素材_*` | **✅** |
| Fig.3 标签 | AUROC/AUPRC 勿标反 | A7 + §16 | **可改** |

### 2.5–2.6 报告生成与读者研究

**不在 B1–B12 范围内**，本计划不列修改项。对应内部任务 **S1–S10 / F1–F3 / F10** 与审稿条 **R1.5–6、R2.13、R2.16–19、R3.4–5** 等，由 Shiyu / Fei Chen 另稿。

---

## 3. Methods（仅 B1–B12 相关小节）

| 小节 | 修改点 | 依据 | 就绪度 |
|------|--------|------|--------|
| **4.1 数据** | patient ID 表；无 ID 队列 **一图一簇**；**DDTI_cls=349**；**dHash** 跨库近重复（堆叠 train vs 外测、TN3K↔ZJH）；**不写** stem 互斥作主论据；TN3K–ZJH **患者**重叠 F6 或 Limitation | `b1/B1_结论与回复素材.md`；`b1/DATASET_AUDIT.md` | **可改**+**待协作**（F6 可选） |
| **4.6 统计** | cluster bootstrap（1000, seed 42）；患者级 **概率平均、标签 max**；ZJH **敏感性**：剔除与 stacked train dHash H=0 的图后重算（不重训） | `b2/conclusions/*`；`b1/B1_结论` §复现 | **可改** |
| **4.3 分割/分类/路由（B11）** | 见 **§8.3**；R2.20(b) Supp. 表见 **§8.4**（数字已生成） | `b11_b12/`、`reproducibility_radiomics.md` | **可改**（统稿时写入；不提前改正文源稿） |
| **4.3 路由** | 消融 **八策略** 定义（波次 1 六策略已跑完；**learned / LLM 待补性能**）；**static_rule** 主表为 **agreement-only**（与 radiomics 完整级联区分）；透明性与 5× 稳定性（B6）见 **§11** | `b3`；`b6/`；`docs/supplementary/router_spec.md` | **接近定稿**（B3 叙事 §13；B6 TN3K 见 §11） |
| **4.4–4.5 报告** | — | — | **范围外（S 任务）** |
| **基线训练（B10）** | Supp. **S[X]** 协议表 + Methods 4.3 段 + S3/S4 表注 | `b10/B10_结论与回复素材.md`；`b10/tables/baseline_training_protocol.md` | **接近定稿**（仅统稿） |

---

## 4. 图表与补充材料

| 项目 | 动作 | 依据 | 就绪度 |
|------|------|------|--------|
| **新 Fig. 数据流（图像臂）** | 自 `DATAFLOW_FIGURE.mmd` 导出 | B12 | **框架可改** |
| **S3/S4** | 更新 CI；基线 **58** 行与 `BASELINES_INDEX.json` 一致；**DDTI_cls n=349** | B2 | **可改** |
| **S5** | ThyroidXAgent 灰底行与 **§16** / b9 §2 一致；专家行见 b9 素材 | **§16** | **可改**（全栈 OOF 换数在 b9 主文档） |
| **新 Supp：患者级分类** | ZJH + ThyroidXL（全量 ZJH） | B2 | **可改** |
| **新 Supp：ZJH train-duplicate 敏感性** | 全量 vs excl.（992 图）；见 `BASELINES_INDEX_excl_train_dup.json` | B1+B2 | **可改** |
| **新 Supp（可选）：近重复审计** | dHash 配对计数或 `near_dup_pairs/stacked_train_vs_ZJH-8K.pairs.json` 摘要 | B1 | **框架可改** |
| **新 Supp：B3 路由消融** | **九队列**波次 1 表（分割 + 全量/Path B 分类）；策略 **7** 见 `b3_llm_*.csv`；**learned** 列待补 | `../b3/tables/`；`export_b3_tables.py` | **接近定稿** |
| **新 Supp：B4 组件消融** | 七队列 × L1/L2/L3（Dice、AUROC）；L3 与策略 7 同源 | **§15**；`REVIEWER_RESPONSE_PLAN` **B4 专项** | **接近定稿** |
| **新 Supp：路由器规格（B6）** | `router_spec.md`（模型、解码、prompt、JSON schema） | `docs/supplementary/router_spec.md`；`export_router_spec.py` | **可改**（统稿前：`--config config/revision/b6/tn3k.yaml` 重导） |
| **新 Supp：路由稳定性（B6）** | *n* 例 × 5 次一致率；`disagreement_tier` 分层；1–2 例不稳定个案 | `output/b6/tn3k/pipeline_run/stability_summary.json`；§11.3 | **可改**（制 Supp. 表） |
| **新 Supp：routing log 样例（B6）** | ≥10 条结构化 `routing_log.jsonl` 摘录 | `output/b6/tn3k/pipeline_run/routing_log.jsonl`（575 行；主跑 250 + 稳定性追加） | **可改**（撰稿筛 ≥10 例） |
| **新 Supp：校准（B8）** | Validation pooled + **五队列** test：**ECE、Brier**；可靠性图 | `output/b8/fit/`；`cohorts/*/calibration_test.json`、`reliability_*.png` | **可改**（制 Supp. 表） |
| **新 Supp：送复核（B8）** | 固定 **validation 95 分位** 阈值的送复核率；保留子集 Acc；risk–coverage 图 | `abstention_eval.json`；`output/b8/figures/risk_coverage_*.png` | **可改**（`plot_risk_coverage.py`） |
| **R2.20 小结节表** | 七队列 N/M（`run_r2_20_small_nodules_all.sh`；当前 **mm/pixel=0.1**） | `b11_b12/tables/R2_20_SUMMARY.md` | **可改**（间距校准后重跑脚本即可，非新实验） |

---

## 5. Discussion 与 Limitations

| 主题 | 建议 | 就绪度 |
|------|------|--------|
| 统计独立性 / 同院重复 | dHash 筛查与 ZJH 敏感性（Supp.）；无 public ID 队列为图像级 bootstrap；**勿**声称 filename 互斥即无泄漏 | **可改** |
| 路由价值 | 与 **B3 波次 1** 一致；**B4 L1–L3** 说明堆叠→集成→全系统（**§15**）；策略 **7**=稿面 S3/S4；策略 **6 learned** 行待补 | **接近定稿** |
| 校准/拒答（B8） | Validation **n=875** 定阈（**q=0.95**，无 LLM）；五 BM test 队列报告 ECE/Brier 与送复核；外测复核率高于 val 设计比例时如实写 **分布偏移** | **接近定稿**（§12；`output/b8/`；**勿用** `smoke_test_as_val`） |
| 读者研究 / 报告主张 | — | **范围外** |

---

## 6. 建议修改优先级（仅 B1–B12）

1. **R2.7 / R2.1**：摘要与 §2.2 宏平均 + CI 定义（`b11_b12` + `b2`）  
2. **R2.2 / R1.1**：Methods 4.1/4.6（**dHash** + cluster CI）+ S3/S4 + 患者级附表 + **ZJH 敏感性 Supp.**（`b1`+`b2`）  
3. **R2.14（B10，接近定稿）**：Supp. 协议表 + Methods/S3/S4 表注（`b10/B10_结论`；与 B2 CI 同条回复）  
4. **R2.20–21**：Methods 4.3 技术段（`b11_b12`）  
5. **R2.8 / R1.2 / R3.1（B3，接近定稿）**：新 Results 小节 + Supp. B3 表（`b3` §13）；补 learned/LLM 行后定稿数字  
6. **R2.3 / R1.4**：图像侧数据流图（`b11_b12` + B1）  
7. **B8（接近定稿）**：Methods 校准/拒答 + Supp. 表图（§12）；**R1.3 校准句**（NHC 异质性仍归 **B7**）  
8. **B7/NHC**：中心表、I²、R2.6（G3 元数据）  
9. **R2.8（B4，接近定稿）**：组件消融 Supp. 表 + S6 对账句（**§15**）  
10. **B5 / R3.2**：元数据消融（**§14**；**TN5K 单队列主表**；当前 sample 占位 → TN5K 换数）  

### B1 / B2 工作包状态（2026-10-22）

| 交付物 | 状态 | 仓库入口 |
|--------|------|----------|
| B1 dHash 审计 | **完成** | `../b1/tables/near_duplicates.json` |
| B1 ZJH 剔除名单 | **完成** | `../b1/tables/zjh_excl_train_dhash0_manifest.json` |
| B2 主系统 CI（8 队列，含 **DDTI_cls=349**） | **完成** | `../b2/tables/*_b2.json` |
| B2 基线 CI **58/58** | **完成**（**无 NHC**） | `BASELINES_INDEX.json` |
| B2 ZJH 敏感性 | **完成** | `*_b2_excl_train_dup.json` |
| 统稿待做 | Methods 4.1/4.6、S3/S4、Supp. ZJH 敏感性表 | 本计划 §2.1、§4；`REVIEWER_RESPONSE_PLAN_ZH.md` B1+B2 专项 |
| 可选 | F6 患者重叠；近重复 spot check | B1 §2.4 |

### B10 工作包状态（2026-10-23，**接近定稿**）

| 交付物 | 状态 | 仓库入口 |
|--------|------|----------|
| 训练协议审计（dataset3/4、非 off-the-shelf） | **完成** | `../b10/B10_基线训练协议总结.md` |
| Supp. Table S[X] 草稿（10 监督 + Agent + VLM 块） | **完成** | `../b10/tables/baseline_training_protocol.md` |
| 与 B2 export 的 checkpoint 对齐 | **完成** | `b2_exports/*/manifest.json`；`build_b10_protocol_table.py` |
| R2.14 回信 + Methods 句式 | **素材就绪** | `../b10/B10_结论与回复素材.md` |
| 统稿待做 | Methods 4.3、S3/S4 表注、LaTeX Supp.、定 S[X] 编号 | 本计划 **§10** |
| 定稿前核对 | ResNet DDTI/ZJH 同 AUROC；MedSAM2 run 名 | `B10_结论` §五；`B10_基线` §6.2 |

**不需要**：为 B10 重训监督基线。

---

## 7. 内部索引（B1–B12）

| 包 | 写稿入口 |
|----|----------|
| B1 | `../b1/B1_结论与回复素材.md` |
| B2 | `../b2/conclusions/B2_结论与回复素材.md` |
| B3 | `../b3/REVIEWER_RESPONSE_SNIPPETS_B3.md` |
| B4–B7 | 计划见 `docs/REVISION_B*_PLAN.md`；结论文档以各 `b*` 目录为准 |
| B8 | `../b8/B8_CALIBRATION_ABSTENTION_CONCLUSIONS.md`（待刷新 q95 数字）；`docs/REVISION_B7_B8_PLAN.md` §B8 |
| B9（**已归档**） | `../b9/B9_ThyroidXAgent_修改与回复计划.md`；本计划 **§16** |
| B10 | `../b10/B10_结论与回复素材.md`；`../b10/tables/baseline_training_protocol.md` |
| B11/B12 | `../b11_b12/REVIEWER_SNIPPETS_ZH.md` |

---

## 8. B11 / B12 拟改稿明细（待统一写入 `ThyroidXAgent.md`）

> 下列为**计划正文**，非已入稿内容。英文段落草稿可对照 `../b11_b12/REVIEWER_SNIPPETS_ZH.md`、`../../reproducibility_radiomics.md` 撰写；定稿时替换 Supp. Note 编号 `[X]`。

### 8.1 摘要（B12 · R2.7）

| 位置 | 现稿 | 拟改为 |
|------|------|--------|
| Abstract 分类一句 | mean AUROC **0.9466**（及若出现的 AUPRC） | **五队列无权重宏平均** AUROC **0.9001**、AUPRC **0.8705**；一句点明 *unweighted macro-average across five classification test cohorts*，可指向 Supp. Table S4 |
| 分割 mean Dice | 保持 **87.21%** 直至与 S3 宏平均定义一并核对 | 与 B2/S3 定稿时同步，不单属 B11 |

### 8.2 Results §2.2 分割与分类（B12 · R2.7）

| 位置 | 现稿 | 拟改为 |
|------|------|--------|
| 分类均值句 | 0.9466 / 0.8361 | 宏平均 **0.9001 / 0.8705**；补充 **按测试图像数加权** 0.9228 / 0.9533（可选一句）；图注与正文统一写清「mean」定义 |

### 8.3 Methods「Segmentation, classification and radiomics」（B11 · R2.20 + R2.21）

**删除或改写**：送审版中易被理解为「radiomics 前统一 CCA 去孤立噪声」的表述；与实现不一致的句子一律改为下列口径。

**拟新增 / 扩充段落（插在路由段之后、放射组学段之前或合并为连贯一节）**：

1. **评估单位（R2.20c）**  
   - OpenThyroid 结节任务为 **一图一标注 ROI**；每图输出 **一个** router-selected mask。  
   - **不对**同图多结节做实例级逐灶分割（若数据集仅单灶标注，如实写）。

2. **专家内后处理（R2.20a）**  
   - DINO-UNet：prob **0.5** 二值化 → 去掉面积 **&lt;50 像素** 的连通域 → **5×5** 椭圆闭运算。  
   - 可选概率集成 mask：多连通域时 **仅保留面积最大** 的一块。  
   - 上述规则作用在 **专家/集成输出、路由之前**；**不再**对最终 selected mask 做第二次连通域精修。

3. **与指标、radiomics 的关系（R2.20 核心）**  
   - 上报 **Dice/HD95**、**PyRadiomics 输入**、Path B 分类均使用 **同一 selected mask**。  
   - **不存在** radiomics 专用的额外 connected-component analysis 步骤（与 `radiomics_judge/feature_extractor.py` 一致）。

4. **放射组学 / AutoGluon（R2.21）**  
   - PyRadiomics **3.1.0**，`radiomics_2d.yaml`（2D shape/一阶/纹理；normalize scale 100；binWidth 25；滤波器列表见 `reproducibility_radiomics.md`）。  
   - 训练：**GT mask**、`dataset_3`、**17,774** 图；提取 100 列 → AutoGluon 内部约 86 维数值特征。  
   - AutoGluon-Tabular **1.4.0**，`best_quality`，ROC-AUC，**600 s**，**8-fold** bagging，部署 **WeightedEnsemble**；推理用冻结权重，**测试集未参与拟合或调参**。  
   - 完整参数表 → **Supplementary Note / 代码仓库** `docs/reproducibility_radiomics.md`。

5. **&lt;5 mm 子集（R2.20b）**  
   - **主文 Methods**：一句指向 **Supplementary Note [X]** 即可。  
   - **Supp. 表**：直接采用 `../b11_b12/tables/R2_20_SUMMARY.md`（由 `scripts/revision/b11/run_r2_20_small_nodules_all.sh` 生成；JSON 在 `r2_20_*.json`）。  
   - **定稿前可选**：改 `MM_PER_PIXEL` 重跑脚本（~1 min）；核对各 JSON 中 `selected_masks_npz` 与投稿主 pipeline 一致。  
   - **不**新增 radiomics CCA；**不**为重表重训。

### 8.4 补充材料（B11）— 数据已就绪

| 项目 | 动作 | 就绪度 |
|------|------|--------|
| **Supplementary Note [X] + 表** | 粘贴 `R2_20_SUMMARY.md` 七行；脚注 `mm_per_pixel=0.1`（敏感性）及失败定义 | **可改** |
| **Radiomics 参数** | `reproducibility_radiomics.md` → Supp. Note 或 Methods 附表 | **可改** |
| **B11 与 B12** | 宏平均改稿在 §8.1–8.2（B12）；与 B11 Methods 可同期统稿 | **可改** |

**当前 Supp. 表数字（与回复计划一致）**：zjh8k N=1001/M=44；tn3k 68/2；tn5k 103/12；rjh7k 366/1；ddti_seg 54/1；pktn 15/1；thyroidxl 0/0。

### 8.8 B11 工作包状态（2026-10-22）

| 交付物 | 状态 |
|--------|------|
| R2.20(a)(c) Methods 条文 | 计划见 §8.3，**待统稿写入** |
| R2.20(b) 分析 | **完成**（缓存 npz，无新 inference） |
| R2.21 参数 | **完成**（`reproducibility_radiomics.md`） |
| 回复信 B11 | **可起草**（见 `REVIEWER_RESPONSE_PLAN_ZH.md` B11 专项） |
| 代码改动 | **不需要** |

### 8.5 B12 数据流图

| 项目 | 动作 | 就绪度 |
|------|------|--------|
| 图像侧数据流 | 组内 **假定已完成**（`DATAFLOW_FIGURE.mmd` / 设计见 `DATAFLOW_FIGURE_PLAN.md`）；统稿时插入 Supp. Fig. 编号与图注 | **可改**（入稿位置与编号） |
| 与 S9 合并全文 Fig.1 | 共同作者协调；**不阻塞** B12 文字条目 | 可选 |

### 8.6 回复信策略（R2.20，含 5 mm）— 不写英文全文，仅逻辑

见 [`REVIEWER_RESPONSE_PLAN_ZH.md`](./REVIEWER_RESPONSE_PLAN_ZH.md)；要点：

- **(a)(c)**：与 §8.3 一致，感谢审稿人，说明已扩充 Methods。  
- **(b) 5 mm**：见下文用户说明用「§8.7」。

### 8.7 审稿人「&lt;5 mm 是否被误删」— 回复逻辑（中文要点）

审稿人 **R2.20(b)** 的 5 mm **不是**你们原稿结论，而是他们用的 **临床尺度** 来问：连通域去噪会不会删掉小结节。

**建议回复结构（三句逻辑）**：

1. **澄清机制**：修订稿已写明，**不再**在 radiomics 前做额外 CCA；小连通域剔除仅发生在 **DINO 专家内部（50 像素）** 及可选 **集成取最大连通域**；**主文 Dice 与 radiomics 共用 selected mask**。  
2. **直接回应 (b)**：在测试集上，用 **GT 等价径** 统计 &lt;5 mm 病例数 **N**；再看 **路由/分割后** selected mask 是否失败（空或 Dice 极低）得 **M**——说明 **M 反映整条流水线**，不是「radiomics 前又删了一遍」。  
3. **诚实限定**：若尚无可靠像素间距，**明确写** mm 阈值为 **敏感性分析** 或引用 **&lt;50 px** 与专家规则同量级；数字放 Supp.，主文不夸大；**不**为此加新后处理、**不**重训。

**代码**：保持现状即可；**不要**为回复而加 radiomics 连通域模块。

---

## 9. B12 工作包（除数据流图外的改稿清单）

> **实验**：**不需要**。宏平均已由 Table S4 五行复算；数据流图按组内现状入稿即可。

### 9.1 必改文稿位置（统稿时一次性改 `ThyroidXAgent.md`）

| # | 位置 | 现稿（典型） | 拟改为 | 审稿条 |
|---|------|--------------|--------|--------|
| 1 | **Abstract** | mean AUROC **0.9466** | **无权重宏平均** AUROC **0.9001**、AUPRC **0.8705**；一句定义 *five test cohorts, unweighted macro-average* | R2.7 |
| 2 | **Results §2.2** 分类段 | 0.9466 / 0.8361 | 同上；可选括号给出加权 **0.9228 / 0.9533** | R2.7, R2.1 |
| 3 | **Fig.2d/e 图注** + **Supp. Table S4 表注** | 「mean」未定义或与旧摘要一致 | 明确 **unweighted macro-average**；与摘要、正文同一套数字 | R2.7 |
| 4 | **Abstract / §2.1** 测试规模 | 「28,458 non-overlapping test cases」 | 分层表述：OpenThyroid **图像级** test 数 + NHC **病例/图**；弱化或删除易误解的 non-overlapping；**28,458 全项**待 G2/协作 | R2.3, R3.3 |
| 5 | **Methods 4.1**（可选一句） | — | 与数据流图一致：各组件 train/val/test、ZJH 外测 vs LNM/FTC 子集分述 | R1.4 |

### 9.2 建议同步核对（仍属 R2.1，非新实验）

- 全文搜索 **0.9466、0.8361**，避免遗漏。  
- **分割** mean Dice **87.21%** 若审稿追问「均值」定义，与 **Supp. S3** 及 **B2** 宏平均口径一并定（不单开 B12 实验）。  
- LNM **4936/4753**、Fig.3 轴标签等见 **§16** / A7，改 B12 时 **顺带扫一眼** 即可。

### 9.3 B12 状态小结

| 交付物 | 状态 |
|--------|------|
| 数据流图 | **组内假定已完成** → 统稿插图注 |
| 宏平均数字 | **已核对** → 待写入摘要/§2.2/S4 注 |
| 28,458 文案 | **框架可写**（图像侧）；全量拆解 **待协作** |
| 回复信 R2.7/R2.1/R2.3/R1.4 | **可起草**（见 `REVIEWER_RESPONSE_PLAN_ZH.md` §B12） |

---

## 10. B10 拟改稿明细（R2.14，接近定稿）

> 下列为**计划正文**；统稿时合并进 `ThyroidXAgent.md` 与回复信。英文回信见 `../b10/B10_结论与回复素材.md` §二。

| # | 位置 | 拟改为 | 依据 |
|---|------|--------|------|
| 1 | **Methods §4.3**（基线） | dataset_4 / dataset_3 堆叠定义；外测仅 test；监督基线全量微调；VLM 零样本分述；指向 Supp. S[X] | `B10_结论` §三 |
| 2 | **Supp. Table S[X]** | 粘贴或改写 `baseline_training_protocol.md`（13 行） | `tables/baseline_training_protocol.json` |
| 3 | **Table S3 / S4 表注** | 一句：监督基线在堆叠开发集微调；CI 见 §4.6；协议见 Supp. S[X] | `B10_结论` §三 |
| 4 | **回复信 R2.14** | 与 B2 同条：公平性叙事 + 已补 Supp. 表 + S3/S4 cluster CI | `B10_结论` §一–§二 |

**B10 状态小结**：实验与表 **已闭环**；剩 **入稿 + 编号 + §6.2 核对** → 视为 **接近定稿**。

---

## 11. B6 拟改稿明细（R2.9 路由器透明性与 5× 稳定性）

> **实验状态（TN3K，2026-10-24）**：`output/b6/tn3k/pipeline_run/` 已具备主 pipeline（**250** 例 `test_for_llm_malignancy`）、`stability_summary.json`（稳定性子集 *n*=**10**，**5×**）、`routing_log.jsonl`（**575** 行：主跑审计 + 稳定性重复追加）、`results.json`；Path B 分类 **121/121** 为 LLM 裁决（`path_b_llm`）。  
> **早期试点**：`output/sample/pipeline_run/`（92% 一致率）仅作方法开发对照，**稿面主数字以下表 TN3K 为准**。  
> **统稿前**：`python scripts/revision/b6/export_router_spec.py --config config/revision/b6/tn3k.yaml` 更新 `docs/supplementary/router_spec.md`（当前文件可能仍为旧默认模型名）。同步润色 `b6/B6_ROUTING_STABILITY_CONCLUSIONS.md`、`b6/REVIEWER_RESPONSE_SNIPPETS_B6.md`（可与本 §11 互拷）。

### 11.1 数据卡（稿面主队列 **TN3K**；换队列时 **只改本表**）

| 字段 | 当前定稿值（**TN3K**） | 仓库来源 |
|------|------------------------|----------|
| 队列 / cohort | **TN3K** `test_for_llm_malignancy` | `config/revision/b6/tn3k.yaml` → `pipeline.data` |
| 主 pipeline 图像数 | **250** | `results.json`；`comparison_report.txt` N=250 |
| 稳定性子集 *n* | **10**（目录排序前 10 张） | `stability_summary.json` → `n_cases` |
| 重复次数 | **5** | `repeats`（与 R2.9 一致） |
| 平均选择一致率 | **0.98**（**98%**） | `mean_selection_agreement` |
| 五次完全一致 | **9 / 10** | `per_case` 中 `selection_agreement==1.0` |
| 低一致例 | **1 / 10** 为 **0.80**（`TN3K_test_0009.jpg`） | `per_case`；分割 4×`all_datasets` + 1×`TN3K` |
| 分层 `close` | **10 / 10**，层内均值 **0.98** | `by_disagreement_tier.close` |
| 分层 `easy` | **0**（本批未出现） | 若扩大 *n* 后出现则补 easy vs close 句 |
| LLM | **qwen3.8-27b**，T=**0.3**，`max_tokens`=**768** | `shared.agent_llm` |
| 配置 | `config/revision/b6/tn3k.yaml` | 与主 pipeline、稳定性共用 |
| 产物目录 | `output/b6/tn3k/pipeline_run/` | `stability_summary.json`、`routing_log.jsonl`、`results.json` |
| 审计 log | **575** 行（≥10 例制 Supp. 表） | 含 250 例单次路由 + 10 例×5× 稳定性追加 |
| 主系统分类（全量 250，参考） | Pipeline AUROC **0.8237**；Path B 子集 AUROC **0.7051** | `comparison.json`（非 R2.9 硬性，可不放正文） |

**分层定义（稿面一句，一般不改）**：分割候选按 inter-expert `average_agreement` 排序，top1 与 top2 差 ≤ **0.10** → `close`，否则 `easy`（`shared/routing_log.py`）。

### 11.2 拟改稿位置（正文 + 补充）

| # | 位置 | 拟写入（逻辑；数字取自 §11.1） | 就绪度 |
|---|------|--------------------------------|--------|
| 1 | **Methods §4.3（路由）** | 说明 LLM 路由器输入为各专家 mask 的质量摘要与 radiomics 裁判摘要；输出 JSON 选定专家（及可选 ensemble 权重）；完整 **prompt、模型 ID（qwen3.8-27b）、temperature/max_tokens、schema** 见 **Supp. Note**（`router_spec.md`）。 | **可改** |
| 2 | **Methods §4.3（稳定性协议）** | 在固定 Phase 1–2 专家输出前提下，对 **TN3K for_llm** 稳定性子集（*n*=**10**）每例重复 **5** 次 LLM **分割**路由；Path A 分类共识不重复 5× 分类；Path B 另报告分类侧 5× 一致率；按 `disagreement_tier` 汇总。 | **可改** |
| 3 | **Results 或 Discussion（短段）** | 报告平均选择一致率 **98%**（**9/10** 五次完全相同；**1/10** 为 **80%**，`close` 层、重复间 Dice range ≈ **0.017**）；说明全队列 **250** 例结构化 `routing_log` 已归档（另 **不必**写全量 250×5，除非稿面承诺）。 | **可改** |
| 4 | **Supp.** | 附 `router_spec.md`；稳定性表（总体 + close 层 + §11.3 个案）；≥10 条 `routing_log` 样例表。 | **可改**（制表） |
| 5 | **Limitations（可选一句）** | 5× 稳定性仅在 for_llm 子集 *n*=**10** 完整报告；API 成本限制未对 250 例全做 5×。 | **框架可改** |

### 11.3 不稳定例（TN3K 稳定性子集，供 Supp. / 回复举例）

| 图像 | Path | tier | 5× 分割一致率 | 备注 |
|------|------|------|---------------|------|
| `TN3K_test_0009.jpg` | A | close | **80%** | `all_datasets` 与 `TN3K` 混选一次；Dice range ≈ **0.017** |
| 其余 9 例 | A 或 B | close | **100%** | 含 5 例 Path B；分类 5× 一致率均为 **100%** |

### 11.4 统稿前 checklist（**不必再跑 B6 实验**）

1. `export_router_spec.py --config config/revision/b6/tn3k.yaml` → 刷新 `docs/supplementary/router_spec.md`。  
2. 将 §11.1–§11.3 写入 **Methods / Results / Supp.**；`routing_log` 筛 ≥10 例制表。  
3. 回复信 **R2.9** 用 `REVIEWER_RESPONSE_PLAN_ZH.md` **B6 专项** + `b6/REVIEWER_RESPONSE_SNIPPETS_B6.md`（数字与上表一致）。  
4. **不必**全队列 **250×5** 稳定性，除非正文明确承诺。

**B6 状态小结**：TN3K 实验与审计 **已闭环** → **接近定稿**（与 B10 同级：剩规格重导、Supp. 制表、正文/回信统稿）。

---

## 12. B8 拟改稿明细（R1.3 校准与送复核，接近定稿）

> **范围（稿面）**：**有良恶性分类标签** 的五队列外测 **TN3K、TN5K、ThyroidXL、ZJH-8K、DDTI_cls** + OpenThyroidDB **validation 合并集（n=875）** 定阈。**不含 NHC**。**RJH-7K、DDTI_seg、PKTN** 无分类标签 → **不写进 B8 Supp. 主表**（仓库 `cohorts/` 可保留 JSON 备查）。  
> **协议**：与主评估一致的 **无 LLM** cascade（`enable_agent: false`）；拒答规则 `rule_subset=nhc`（熵、top-2 margin、分割最小两两 IoU）；`combination=any`；阈值仅在 validation 上 **95 分位** 拟合（`fit_thresholds_quantile`，`quantile=0.95`），测试集 **只应用、不调参**。  
> **产物**：`output/validation/no_llm_primary/`；`output/b8/fit/abstention_thresholds.json`；`output/b8/cohorts/<cohort>/`；图 `output/b8/figures/`（`plot_risk_coverage.py`）。**勿用** `output/b8/smoke_test_as_val/`。

### 12.1 数据卡（定稿数字；统稿时只改本表）

| 字段 | 定稿值 | 仓库来源 |
|------|--------|----------|
| Validation 合并 *n* | **875**（TN3K 100 + TN5K 525 + ThyroidXL 100 + PKTN 150 valid） | `merge_manifest.json` |
| 定阈子集（有 BM 标签） | **n=725**；pooled **ECE=0.088**，**Brier=0.078** | `fit/calibration_val.json` |
| 分位数 | **0.95** | `abstention_thresholds.json`；复现加 `--quantile 0.95` |
| 冻结阈值 | 熵 **>1.0**；margin **<0.237**；seg min IoU **<0.058** | `fit/abstention_thresholds.json` |

**五队列 test（固定阈值）**

| 队列 | 校准 *n* | ECE | Brier | 送复核 % | 保留子集 cls Acc |
|------|----------|-----|-------|----------|------------------|
| TN3K | 614 | 0.183 | 0.200 | **48.2** | **0.827** |
| TN5K | 1000 | 0.066 | 0.083 | **44.4** | **0.942** |
| ThyroidXL | 2090 | 0.073 | 0.110 | **44.9** | **0.896** |
| ZJH-8K | 7958 | 0.097 | 0.110 | **43.1** | **0.892** |
| DDTI_cls | 349 | 0.093 | 0.110 | **3.7** | **0.866** |

**叙事注意**：validation 上分位数对应约 **5%** 极端不确定/每条规则，但 **test 送复核约 44–48%**（主队列），主因 **margin 分布外移** + `any` 组合；回复信如实报告，可选引用 **risk–coverage** 说明覆盖率–准确率权衡。DDTI_cls 送复核偏低与队列难度/信号分布有关，表内保留即可。

### 12.2 拟改稿位置

| # | 位置 | 拟写入 | 就绪度 |
|---|------|--------|--------|
| 1 | **Methods §4.x** | 分类校准（ECE、Brier、可靠性图）；拒答三信号与 **validation-only** 95 分位定阈；测试集仅评估 | **可改** |
| 2 | **Results（短段）或 Discussion** | 1–2 句：外测校准可报告；固定阈值下送复核比例与保留子集准确率；细节 **Supp.** | **可改** |
| 3 | **Supp. Table（校准）** | Val 一行 + 上表五队列 ECE/Brier | **可改**（JSON→表） |
| 4 | **Supp. Table（送复核）** | 五队列 *n*、flagged、%、保留子集 Acc | **可改** |
| 5 | **Supp. Fig.** | 可靠性图（val + 五 test）；risk–coverage（`figures/risk_coverage_*.png`） | **可改** |
| 6 | **F4 / R1.6** | 引用 `abstention_thresholds.json`、`results_flagged.json`；临床工作量由 Fei Chen 主笔 | **非稿面 JSON 已齐** |

### 12.3 统稿前 checklist（**不必再跑 B8 主实验**，除非 B3 重跑 test pipeline）

1. 刷新 `../b8/B8_CALIBRATION_ABSTENTION_CONCLUSIONS.md`（q95、真 validation、上表数字）。  
2. `python scripts/revision/b8/plot_risk_coverage.py --mark-operating-point --combined`（若改图）。  
3. Methods 写明 **quantile=0.95**；一键脚本默认可后续改为 0.95。  
4. 回复 **R1.3** 校准/拒答段见 `REVIEWER_RESPONSE_PLAN_ZH.md` **B8 专项**（NHC 异质性句仍待 **B7**）。

**B8 状态小结**：**OpenThyroid 五 BM 队列 + validation 定阈** 实验与图 **已闭环** → **接近定稿**（剩结论文档刷新、Supp. 入稿、与 B7/NHC 分条回复）。

---

## 13. B3 拟改稿明细（R1.2 / R2.8 / R3.1，接近定稿）

> **范围（稿面）**：在 **固定 Phase 1–2 专家池** 上比较 **八种路由策略**（见 Methods 4.3）；本包 **波次 1** 已产出 **策略 1–5、8** 的逐队列指标；**策略 7（LLM）** 性能与稿面 S3/S4 一致（`manuscript_llm_metrics.yaml`，**B4 L3 同源**）；**策略 6（learned）** test 行待齐后写入 Supp. 同行。  
> **主表口径**：策略 4 **`static_rule`** 为 B3 消融定义的 **agreement-only** 分割路由（`skip radiomics`），与主系统完整 radiomics 级联区分。  
> **产物**：`output/ablation/b3/<cohort_id>/_summary/b3_routing_table.csv`；叙事与三队列细表见 `../b3/B3_WAVE1_RESULTS.md`；回信见 `../b3/REVIEWER_RESPONSE_SNIPPETS_B3.md`。

### 13.1 数据卡（波次 1 覆盖；统稿时以 `_summary` CSV 为准）

| 字段 | 定稿值 | 仓库来源 |
|------|--------|----------|
| 波次 1 策略 | **1** 最优单专家、**2** 软投票、**3** 多数票、**4** 静态规则、**5** 最大置信度、**8** Oracle | `run_b3_batch.py --preset wave1` |
| 已汇总队列（波次 1 **6/6**） | **TN3K、TN5K、ThyroidXL、PKTN、DDTI_seg、DDTI_cls、ZJH-8K、RJH-7K**（大队列分块合并后汇总）；开发 **sample** 可作 smoke | 各 `output/ablation/b3/<id>/_summary/` |
| 待补策略 | **6** learned（val 拟合 LR → test 推理）；**7** LLM **稿面数** → `manuscript_llm_metrics.yaml`（与 **B4 L3** 同源，非 `b3/*/llm/` 重跑） | `fit_learned_router.py`；`B3_LLM_RESULTS.md` |
| **未纳入** 本包主表 | **NHC-MISD-TUS**（R3.1 最终主表须含 → 单独波次或 Limitation） | — |
| CI 口径 | **已与 B2 对齐**：`bootstrap.method=cluster`（1000, seed 42）；ZJH/ThyroidXL 用 `cluster_maps/` | `recompute_b3_cluster_ci.py`；`pipeline/revision/b3/cluster_ci.py` |

**Path B 占比（分类路由主战场，三队列示例）**：TN3K **279/614（45.4%）**；TN5K **404/1000（40.4%）**；ThyroidXL **921/2090（44.1%）**；外测大队列见各队列 `b3_routing_table.csv` 元数据行。

### 13.2 可直接写入 Results / Discussion 的结论（波次 1；learned/LLM 句末留「待补」）

1. **无单一静态策略在分割与分类上全面占优**；队列间排序不同，须在 **同一专家池** 上并列报告多策略及 **95% CI**（定稿前换为 cluster CI）。  
2. **分割**：TN3K/TN5K 上 **最大置信度（5）** 明显劣于软投票/多数票（Dice 约 **−9～−18 pp**）；ThyroidXL 上策略间分割差异较小，但 **Oracle（8）** 仍高于最佳可部署静态策略约 **2.5–4 pp Dice**，保留路由增益空间。  
3. **分类**：点估计因队列而异（如 TN3K 软投票 AUROC 最高；TN5K 静态规则/最大置信度与软投票 **CI 重叠**）；不宜仅凭单点排序。  
4. **对外报告**：回复信 **表 R14–R15** 与各队列测试集指标对齐；**不**向审稿人单独展开分类专家分歧子集（内部分析仍可在 `b3_metrics.json` / CSV 中查阅）。  
5. **Oracle** 量化可部署策略与理想路由上界；**策略 7（LLM）** 与稿面 S3/S4 一致；**策略 6** 填入后与静态策略及 Oracle 对照（「排第几」）。

### 13.3 拟改稿位置

| # | 位置 | 拟写入 | 就绪度 |
|---|------|--------|--------|
| 1 | **Methods §4.3** | 八策略列表；波次 1 静态六策略 + Oracle；static_rule = agreement-only；learned / LLM 定义 | **接近定稿** |
| 2 | **Results 新小节（路由）** | §13.2 五条 + 1–2 个代表性队列数字（TN3K/TN5K）；外测一句「九队列趋势一致，详见 Supp.」 | **接近定稿**（learned 行待补） |
| 3 | **Supp. Table B3** | 九队列 × 策略（分割 Dice/HD95；分类 AUROC/AUPRC）；策略 **7** 见 `b3_llm_*.csv`；**learned** 列待补 | **接近定稿** |
| 4 | **Discussion（R2.8）** | 路由价值与 B10 堆叠叙事交叉引用；静态不足以替代集成 + Oracle 余量 | **接近定稿** |
| 5 | **回复信 R1.2 / R3.1** | 同 `REVIEWER_RESPONSE_PLAN_ZH.md` **B3 专项** | **接近定稿** |

### 13.4 统稿前 checklist（**不必重跑波次 1**，除非专家池或 static_rule 口径变更）

1. learned（6）全队列：**fit**（`artifacts/b3/<cohort>/learned_router_*.joblib`）→ **test infer** → 写入 `b3_routing_table.csv` 新行。  
2. LLM（7）按 `config/revision/b3/*.yaml` 波次 2 跑完并 eval，同上汇总。  
3. `python scripts/revision/b3/recompute_b3_cluster_ci.py --all-wave1 --summarize`（若尚未跑）→ `export_b3_tables.py` 刷新 `../b3/tables/`。  
4. 更新 `B3_WAVE1_RESULTS.md` §1 覆盖表（ZJH/RJH/DDTI/PKTN 已完成波次 1）；§6 标题改为「九队列 + 三队列细表」。  
5. **NHC**：纳入同表或 Limitation + 回复承诺时间表（与 B7 分工）。

**B3 状态小结**：波次 1 **实验与叙事已闭环** → **接近定稿**；**策略 7** 见 yaml；**仍缺策略 6 全队列入表** + **CI 口径定稿** + **NHC 行**。

---

## 14. B5 拟改稿明细（R3.2 元数据消融）

> **实验状态（2026-10-26，假定跑数闭环）**：五 `metadata_mode` 已在 **sample** 上完整跑通（四 mode + B3 `llm`=`full`）；**稿面性能主证据仅单列 TN5K** `test_for_llm_malignancy`（*n*=**250**），**不与 B3/B4 九队列对齐**。  
> **换数约定**：下表 **性能数字与 Δ 暂用 sample（*n*=10）** 填入 Methods/Results/回复草稿；**TN5K `run_b5_batch.py --skip-full` 完成后**，只替换 **§14.1 表、路径列、主对比 Δ 与 CI**，§14.2 段落逻辑不变；与 `REVIEWER_RESPONSE_PLAN_ZH.md` **B5 专项** 互拷。真源目录：`output/ablation/b5/sample/`（占位）→ `output/ablation/b5/tn5k/` + `output/ablation/b3/tn5k/llm`（`full`）。

### 14.0 稿面范围（与 B3/B4 区分）

| 交付 | 范围 | 状态 |
|------|------|------|
| **性能消融表**（五 mode） | **仅 TN5K for_llm** 一行（主文或 Supp. 单表） | **正式回信 R17** 已写（sample 占位）；**TN5K 换数** |
| **主对比** | **`full` → `quality_only`**（ΔDice、ΔAUROC；定稿加 CI） | 叙事 **可写**；Δ 见 §14.1（sample） |
| **选择模式** | NHC（或协作环境）**`full`**：`routing_log` → 中心×专家热图 | **待** G3 / 院方数据（与 **B7** 分条） |
| **多队列五 mode** | **不要求**（可选 Supp. 扩展，非 R3.2 最小集） | 不纳入本 § 主表 |

### 14.1 数据卡（**稿面队列：TN5K**；**下表数字 = sample 占位**）

| 字段 | 占位（**sample**，当前写入稿/回信） | 换数后（**TN5K**，投稿主表） | 仓库来源 |
|------|-----------------------------------|------------------------------|----------|
| 队列 / 子集 | 开发 **sample** test（管线验证） | **TN5K** `test_for_llm_malignancy` | `config/revision/b5/sample.yaml` / `tn5k.yaml` |
| 图像数 *n* | **10** | **250** | 各 mode `b3_metrics.json` → `n_total` |
| 路由 | seg=**llm**，cls=**llm**；五档 `metadata_mode` | 同左 | `ablation_run.json` |
| intermediate | `output/sample/pipeline_run/intermediate` | `output/TN5K/pipeline_run/intermediate`（**image_name** 对齐 npz） | `shared_intermediate` |
| **`full`** | `output/ablation/b3/sample/llm/` | `output/ablation/b3/tn5k/llm/` | `--skip-full` 复用 B3 |
| 四 mode | `output/ablation/b5/sample/{drop_device,drop_source,drop_both,quality_only}/` | `output/ablation/b5/tn5k/<mode>/` | `run_b5_batch.py` |
| 汇总 | 手抄或 `build_b5_tables.py --cohort sample` | `build_b5_tables.py --cohort tn5k` | `artifacts/b5_*.csv` |

**五 mode 性能（占位：sample *n*=10；TN5K 跑完后替换本表数字列，可加 CI）**

| metadata_mode | Dice | HD95 | AUROC | AUPRC |
|---------------|------|------|-------|-------|
| **full**（B3 `llm`） | 0.837 | 14.0 | 0.92 | 0.927 |
| drop_device | 0.837 | 12.1 | 0.92 | 0.927 |
| drop_source | 0.838 | 12.0 | 0.92 | 0.927 |
| drop_both | 0.827 | 12.3 | 0.92 | 0.927 |
| quality_only | 0.837 | 12.1 | 0.92 | 0.927 |

**主对比（R3.2，占位数字）**：**full → quality_only** → ΔDice **≈ −0.0002**、ΔAUROC **0**；分割 Dice 跨 mode **0.827–0.838**（`drop_both` 最低）。Path B 仅 **1/10** 触发 LLM → 分类五 mode 同为 **0.92** / **0.927**，**不可外推**；稿面以 **TN5K** 换数后的 Δ 与 CI 为准。

**Results 可写一句（占位版）**：在 TN5K for_llm 子集上（*n*=250，数字待换），固定 LLM 路由下剔除设备/来源元数据后，**`quality_only` 相对 `full` 的分割与分类指标变化很小**（试点 sample 上 ΔDice≈0、ΔAUROC=0），提示路由性能主要由 **质量与分歧信号** 驱动而非数据集名称 alone；中心级专家偏好见 NHC 热图（待补）。

### 14.2 拟改稿位置

| # | 位置 | 拟写入 | 就绪度 |
|---|------|--------|--------|
| 1 | **Methods §4.3（LLM 路由）** | 五档 `metadata_mode`；与 `router_spec.md`、B6 一致；Path A 共识不调 LLM；**单队列 TN5K** 性能消融协议 | **可改** |
| 2 | **Results 短段（R3.2）** | 上 §14.1 主对比 + 五 mode 一句；**明确稿面仅 TN5K 一表** | **可改**（TN5K **换数**） |
| 3 | **Supp. Table B5** | **TN5K × 五 mode**（点估计 ± CI）；`build_b5_tables.py` | **可改**（结构）；数字 **sample→TN5K** |
| 4 | **Supp. Fig.（NHC）** | **`full`** 中心×专家热图 | **待 NHC** |
| 5 | **Discussion** | Δ 小 → 元数据非主导；热图若集中选专家 → 混杂与 **B7** | **可改** |

### 14.3 统稿前 checklist

- [x] sample 五 mode + `full` 复用 B3 `llm`（`output/ablation/b5/sample/`）  
- [x] §14 / **B5 专项** 表结构与回复要点（**sample 数字**）  
- [ ] **TN5K** 四 mode + `build_b5_tables.py` → **仅替换 §14.1 与专项表数字/CI**  
- [x] 正式回复 R3.2：**表 R17** + 段落已写入 `正式回复/latex/generated/body_*.tex`（sample 占位；`\rpending` 标 TN5K/NHC/修订稿）  
- [ ] TN5K 换数后：更新 R17、删/改 R3.2 相关 `\rpending`  
- [ ] NHC **`full`** 热图（可选加强 R3.2「选择模式」；不阻塞性能主表）

**B5 状态小结**：**接近定稿**（Methods/Results/回复 **可起草**；**TN5K 换数** + **NHC 热图** 为剩余项；**不必**九队列五 mode）。

---

## 15. B4 拟改稿明细（R2.8 组件消融 + S6/S4 对账）【已归档】

> **状态：已归档（2026-10-26）** — 数字真源 `../b4/B4_STATUS_ZH.md`；正式回信 **表 R15–R16**（`正式回复/latex/generated/component_ablation_tables_*.tex`）。可选后续：Path B 附录、`B4_S6_S4_reconciliation.md` 仅在 b4/ 维护。  
> **数据约定（2026-10-26）**：**L1/L2** = `run_l1_cohort` + B3 `soft_voting`（shared-intermediate 消融栈，见 `../b4/B4_STATUS_ZH.md` §3）。**L3** = **B3 策略 7** = `manuscript_llm_metrics.yaml` / `B3_LLM_RESULTS.md`（稿面 Table S3/S4），**与 L1/L2 非同一重跑协议**；回复与 Discussion 须分述，避免把 L3−L2 写成逐步加模块的因果链。  
> **统稿**：数字以 `REVIEWER_RESPONSE_PLAN_ZH.md` **B4 专项** 表为准；主文 S3/S4 改数后 **只改 yaml** 并同步 §15 与 B4 专项。

### 15.1 组件主表（外测七队列；点估计）

与 **B4 专项** 相同：分割表（tn3k–rjh7k 七行）、分类表（五 BM 队列）。**代表性数字（TN3K）**：L1 Dice **0.845** / AUROC **0.770** → L2 **0.856** / **0.828** → L3 **0.853** / **0.869**（L3 稿面全系统）。

### 15.2 拟改稿位置

| # | 位置 | 拟写入 | 就绪度 |
|---|------|--------|--------|
| 1 | **Results（R2.8 短段）** | L1→L2→L3 定义；逐队列或 2–3 个代表队列；强调路由/全系统相对固定集成的增益 **因队列而异** | **接近定稿** |
| 2 | **Supp. Table B4** | 全表 L1/L2/L3 + 可选 Δ(L2−L1)、Δ(L3−L2) 行 | **接近定稿** |
| 3 | **Discussion / Limitations** | ZJH L1 AUROC &gt; L2、ZJH L3 Dice &gt;&gt; L2 → 指向 **S6 逐级消融 vs 投稿 S4 全系统**（`B4_S6_S4_reconciliation.md`） | **框架可改** |
| 4 | **与 B3/B10 交叉** | B3：静态路由无全胜；B10：监督基线微调公平性 | **接近定稿** |

### 15.3 统稿前 checklist（**不必为 L3 跑 LLM API**）

1. 主文 S3/S4 若修订 → 更新 `manuscript_llm_metrics.yaml` → 刷新 **§15.1** 与 **B4 专项**。  
2. （可选）物化 `b3/<cohort>/llm/b3_metrics.json` + `build_b4_tables.py` 生成 CSV，与文档表核对。  
3. 起草 `docs/B4_S6_S4_reconciliation.md`（ZJH、ThyroidXL 等反差队列）。  
4. Path B 附录 **B-a/B-b/B-c**：待 `run_b4_pathb_appendix.py` 与 `path_b_autogluon` 产物。

**B4 状态小结**：**已归档** → 统稿从 §15 + b4 真源 + 回信 R15–R16 并入稿件即可。

---

## 16. B9 归档索引（R2.10–12 · LNM/FTC/PTC）

> **状态：已归档（2026-10-26）** — 实验包、**Supp. Table S5 灰底行**、Methods/Results §2.4 改稿清单、**R2.10–12 回复要点** 的 **唯一维护处** 为 [`../b9/B9_ThyroidXAgent_修改与回复计划.md`](../b9/B9_ThyroidXAgent_修改与回复计划.md)。  
> **本 §** 仅供 `MANUSCRIPT_REVISION_PLAN` 与 `REVIEWER_RESPONSE_PLAN` **交叉引用**；数字更新时 **只改 b9 主文档 §2**，再顺手改 **§16.2 一行** 与 **B9 专项** 同行。

### 16.1 覆盖度摘要（与 b9 §1 同步）

| 项 | 状态 |
|----|------|
| 5 折患者（簇）级 OOF + CI | **✅** DINO multitask 五折已完成 |
| Table S5 ThyroidXAgent 灰底（LNM / FTC） | **🟡** 当前 OOF 可写稿；**定稿**由全栈（AG+路由）融合后 **整格换数** |
| 外测 E2（LNM C2）、E4（FangDai FTC） | **⬜** ThyroidXAgent 未报 |
| 专家 S5 行（LLNM / Tiger） | **✅** 独立素材，不与灰底混用 |
| R2.10 域 / FVPTC≠FTC | **🟡** 文责 + `需要确认.md` |

### 16.2 S5 灰底（一行索引）

**患者级 OOF（DINO 五折，非终稿全栈）**：完整表与 95% CI → [`../b9/B9_ThyroidXAgent_修改与回复计划.md`](../b9/B9_ThyroidXAgent_修改与回复计划.md) **§2**（`frozen_date` **2026-10-26**）— LNM **882** 簇 AUROC **0.718** / AUPRC **0.598**；FTC/PTC **722** 簇 AUROC **0.521** / AUPRC **0.109**；开发 **4753** / **4756** 图；证据 `b9/runs/{lnm_cv,ftcptc_cv}/cv_summary.json`。

### 16.3 本计划中的稿面锚点（统稿 checklist）

| # | 稿面 | 动作 |
|---|------|------|
| 1 | **Abstract / Results §2.4** | 5 折 OOF 协议、样本量、探索性 FTC 域 — 从 b9 **§3** 并入 `ThyroidXAgent.md` |
| 2 | **Supp. Table S5** | 灰底两行 — 从 b9 **§2** 抄写；外测 TBD 脚注 |
| 3 | **Fig.3** | 轴标签 AUROC/AUPRC（R2.1） |
| 4 | **回复信** | R2.11 主、R2.10/R2.12 部分 — b9 **§4**；与 `REVIEWER_RESPONSE_PLAN` **B9 专项** 互拷 |

**B9 状态小结（本目录）**：**已归档** → 勿在 §2.4 扩写新表；统稿与换数以 **b9 主文档** 为准。
