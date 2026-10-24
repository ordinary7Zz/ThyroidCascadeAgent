# B1–B12 交付清单（稿面位置 + 仓库产物）

> **用途**：排工与验收；勾选「必交付」项，避免只做实验不写稿/不回信。  
> **范围**：仅 B1–B12（不含 Shiyu S1–S10）。  
> **关联**：[REVIEWER_RESPONSE_PLAN_ZH.md](./REVIEWER_RESPONSE_PLAN_ZH.md)、[MANUSCRIPT_REVISION_PLAN_ZH.md](./MANUSCRIPT_REVISION_PLAN_ZH.md)、`docs/ThyroidXAgent_返修计划与回复_中文.md` Part A。

**图例**：✅ 已有可引用素材　🟡 部分/占位　⬜ 未做　🔒 依赖协作方

---

## 总览（按交付形态）

| B | 新主文图 | 新/改补图 | 新/改补表 | Methods 文 | Results 文 | 回复信 R 条 | 非稿面产物 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| B1 | ⬜ | ⬜ | ✅ | ✅ | ✅ | R1.1, R2.2, R2.4, R3.3 | 审计 JSON、筛查脚本 |
| B2 | ⬜ | ⬜ | ✅ | ✅ | ✅ | R1.1, R2.2, R2.14 | `b2/tables/*.json` |
| B3 | 🟡 | 🟡 | 🟡 | ✅ | ✅ | R1.2, R2.8, R3.1 | pipeline 多策略输出 |
| B4 | ⬜ | ⬜ | ⬜ | 🟡 | ⬜ | R2.8 | 单专家训练+评测 |
| B5 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | R3.2 | LLM×5 metadata 跑数 |
| B6 | ⬜ | ⬜ | 🟡 | ✅ | 🟡 | R2.9 | sample 已闭环；TN3K 5× 待跑；§11 / B6 专项 |
| B7 | ⬜ | ⬜ | ⬜ | 🟡 | ⬜ | R1.3, R2.6 | 🔒 G3 中心元数据 |
| B8 | ⬜ | 🟡 | 🟡 | ✅ | 🟡 | R1.3 | **接近定稿**；q=0.95；五 BM 队列；不含 NHC |
| B9 | ⬜ | ⬜ | ✅ | ✅ | ✅ | R2.10–12 | B9 实验包/表 |
| B10 | ⬜ | ⬜ | ✅ | ✅ | 🟡 | R2.14 | **接近定稿**；统稿入稿 |
| B11 | ⬜ | ⬜ | 🟡 | ✅ | 🟡 | R2.20–21 | `reproducibility_radiomics.md` |
| B12 | 🟡 | 🟡 | ⬜ | 🟡 | ✅ | R1.4, R2.1, R2.3, R2.7 | Mermaid → 导出 Fig |

---

## B1　数据审计与患者 ID

| 类别 | 必交付项 | 稿内位置（建议） | 仓库入口 / 产物 | 状态 |
|------|----------|------------------|-----------------|------|
| **补表** | 各队列 patient/case ID 可用性；bootstrap 聚类规则一行说明 | Supp.（新表或并入数据说明表） | `../b1/B1_结论与回复素材.md` §2.1 | ✅ |
| **补表/数据** | **dHash** 近重复（堆叠 train vs 外测；TN3K↔ZJH） | Methods 4.1 + 可选 Supp. | `../b1/tables/near_duplicates.json`；`near_dup_pairs/` | ✅ |
| **补表/数据** | stem 互斥（**不作稿面主结论**） | 仅仓库记录 | `../b1/tables/train_test_overlap.json` | ✅ |
| **文** | 无 ID 队列声明；ZJH 1146/1149、7958 图；**DDTI_cls n=349** | Methods 4.1 | `B1_结论`；`DATASET_AUDIT.md` | ✅ / 🔒 F6 |
| **文** | TN3K↔ZJH 同院（**图级 dHash** + ZJH 敏感性 Supp.） | Methods + Supp. | `B1_结论` §三 | ✅ / 🔒 F6 患者数 |
| **补表/流程** | ZJH excl. train-dup 敏感性 | Supp. Table | `../b2/tables/*_excl_train_dup.json` | ✅（待入稿制表） |
| **补表/流程** | 近重复 **spot check** 10–20 对 | Methods 一句 | — | ⬜ |
| **图** | 可选：数据层级示意（常与 B12 合并，不单独必画） | Fig.1 子面板 | B12 | 🟡 |
| **回** | R1.1 / R2.2 / R2.4 / R3.3 段落 | 回复信 | 摘 `B1_结论与回复素材.md` | 🟡 |

**验收**：独立性以 **dHash** 表述；**勿**用 stem=0 作主论据；患者互斥需 F6 或 Limitation。

---

## B2　Cluster bootstrap CI + 患者级分类

| 类别 | 必交付项 | 稿内位置 | 仓库入口 | 状态 |
|------|----------|----------|----------|------|
| **改表** | ThyroidXAgent + 监督基线 **95% CI**（**58/58**；**不含 NHC**） | **Supp. Table S3、S4** | `../b2/tables/`；`BASELINES_INDEX.json` | ✅ |
| **新补表** | ZJH **全量 vs excl. train-dup** 敏感性 | Supp. | `*_b2_excl_train_dup.json` | ✅（待入稿） |
| **新补表** | ZJH-8K、ThyroidXL **患者级** AUROC/AUPRC；聚合规则一句 | Supp. 新表 | B2 §4.2；`cluster_maps/` | ✅ |
| **文** | Methods **4.6** 统计（bootstrap、患者级 mean prob / max label） | Methods | B2 结论 | ✅ |
| **文** | Results §2.2 引用 CI，不与旧稿点估计矛盾 | Results | 填表时同步改正文 | 🟡 |
| **图** | 无必须新图 | — | — | — |
| **回** | R1.1、R2.2；R2.14 的 CI 部分与 B10 合用 | 回复信 | B2 结论 | ✅ |

**验收**：定稿前用最新 `*_b2.json` 刷表；`BASELINES_INDEX.json` 与稿面行一致。

---

## B3　路由消融（同专家池）

| 类别 | 必交付项 | 稿内位置 | 仓库入口 | 状态 |
|------|----------|----------|----------|------|
| **表或图** | 8 策略 × 分割/分类 × **全测试集（含 NHC 协议）**；Oracle 上界 | Results 新小节 + **正文表或 Fig** 或 Supp. | `../b3/B3_WAVE1_RESULTS.md`；`../b3/tables/` | 🟡 仅波次 1 |
| **文** | Methods 4.3 消融列表；NHC **非 LLM** 主结果与 LLM 消融分报告 | Methods + Limitations | `REVISION_B3_B4_PLAN.md` | 🟡 |
| **统计** | 与 B2 一致的 **配对 cluster bootstrap** | 表注 / Methods | 定稿前重算 | ⬜ |
| **回** | R1.2、R2.8、R3.1 | 回复信 | `../b3/REVIEWER_RESPONSE_SNIPPETS_B3.md` | 🟡 |

**验收**：波次 1 可写「主论点 + 待补队列」；勿把 LLM/学习型/NHC 全队列写死。

---

## B4　组件消融 + S6/S4 对账

| 类别 | 必交付项 | 稿内位置 | 仓库入口 | 状态 |
|------|----------|----------|----------|------|
| **补表** | L1 单专家 / L2 专家池 / L3+路由；Path B 放射组学分解 | Supp. + Results | `docs/REVISION_B3_B4_PLAN.md` | ⬜ |
| **文** | 解释 **S6 单专家 ZJH AUROC vs S4 全系统** | Results + **更正 Supp. S6 表注** | 对账段落（计划 §） | ⬜ |
| **图** | 非必须 | — | — | — |
| **回** | R2.8（与 B3、B10 交叉引用） | 回复信 | 待 B4 定稿 | ⬜ |

---

## B5　路由元数据消融

| 类别 | 必交付项 | 稿内位置 | 仓库入口 | 状态 |
|------|----------|----------|----------|------|
| **补表** | 5 种 `metadata_mode` × 测试性能 | Supp. | `docs/REVISION_B5_PLAN.md` | ⬜ |
| **补图** | **中心 × 专家选择热图** | Supp. Fig. | 同上；需 `routing_log.jsonl` | ⬜ |
| **文/回** | R3.2：Δ 与中心–专家关联（互信息等） | Results 短段 + 回复信 | 依赖 B3 波次 2 LLM | ⬜ |

---

## B6　路由器透明性与稳定性

| 类别 | 必交付项 | 稿内位置 | 仓库入口 | 状态 |
|------|----------|----------|----------|------|
| **补材料** | 完整 prompt、模型名/版本、解码参数、JSON schema | Supp. Methods 或 Supp. Note | `docs/supplementary/router_spec.md` | ✅（TN3K 可重导） |
| **补表** | 每例 **5×** 路由一致率；按候选质量分层波动 | Supp. | `../b6/B6_ROUTING_STABILITY_CONCLUSIONS.md`；`output/sample/.../stability_summary.json` | 🟡 sample *n*=10；TN3K 换数 |
| **数据** | ≥10 条结构化 **routing log** 样例 | Supp. 或 GitHub | `output/sample/pipeline_run/routing_log.jsonl` | ✅ |
| **图** | 可选（一致率条形图） | Supp. | — | ⬜ |
| **回** | R2.9 | 回复信 | `../b6/REVIEWER_RESPONSE_SNIPPETS_B6.md`；`REVIEWER_RESPONSE_PLAN_ZH.md` B6 专项 | 🟡 可起草；统稿入信 |

---

## B7　NHC 中心异质性

| 类别 | 必交付项 | 稿内位置 | 仓库入口 | 状态 |
|------|----------|----------|----------|------|
| **补表** | 每中心：患者/结节/图像/扫描仪/标签；中心级宏平均；**I²、τ²** | Supp. | `docs/REVISION_B7_B8_PLAN.md` | ⬜ |
| **文** | THYB_S_ZJ24 个案；全腺体 Dice 59.28% 与结节 pipeline 边界 | Results | 同上 | ⬜ |
| **补图** | Meta 回归、分布图（可选） | Supp. Fig. | — | ⬜ |
| **协作** | 中心元数据 | — | 🔒 **G3** | ⬜ |
| **回** | R1.3、R2.6（图像侧描述；校准句归 B8） | 回复信 | — | ⬜ |

---

## B8　校准与拒答

| 类别 | 必交付项 | 稿内位置 | 仓库入口 | 状态 |
|------|----------|----------|----------|------|
| **补图** | 可靠性图；**风险–覆盖率**曲线 | Supp. Fig. | `output/b8/fit/reliability_val.png`；`cohorts/*/reliability_test.png`；`output/b8/figures/` | 🟡 PNG 已齐；Supp. 编号待入稿 |
| **补表** | ECE、Brier；五 BM 队列 **送复核比例** | Supp. | `output/b8/fit/` + `cohorts/*/`（**不含** RJH/DDTI_seg/PKTN） | 🟡 JSON 已齐；制表待做 |
| **文** | 触发规则；**validation 95 分位** 定阈 | Methods 4.x | `MANUSCRIPT` **§12**；`REVISION_B7_B8_PLAN.md` | 🟡 计划已写；入 LaTeX 待统稿 |
| **非稿面** | `abstention_thresholds.json` 供 **F4** | — | `output/b8/fit/abstention_thresholds.json` | ✅ |
| **回** | R1.3（校准/拒答）；R1.6 临床句 mainly F4 | 回复信 | `REVIEWER_RESPONSE_PLAN` **B8 专项** | 🟡 可起草；B7 NHC 段另补 |

**验收**：**勿用** `smoke_test_as_val`；结论文档刷新 q95 后 **零句 smoke 进稿**。

---

## B9　LNM 与 FTC/PTC

| 类别 | 必交付项 | 稿内位置 | 仓库入口 | 状态 |
|------|----------|----------|----------|------|
| **改表** | **Supp. Table S5** ThyroidXAgent 灰底行（OOF；定稿换全栈数） | S5；Fig.3 轴标签 | `../b9/B9_ThyroidXAgent_修改与回复计划.md` §2 | 🟡 数已有 / 外测 TBD |
| **文** | 5 折患者级 CV；4753/882、4756/722；簇定义；DINO+AG+路由 | Methods 4.x；Results §2.4 | 同上 §3；`B9_ThyroidXAgent_补充实验计划.md` | 🟡 AG/路由进行中 |
| **文** | FVPTC≠FTC；探索性/域迁移限定 | Results + Limitations | `../b9/需要确认.md` | 🟡 |
| **图** | 一般不新画（沿用稿内 Fig.3） | Fig.3 标签修正 | A7 清单 | 🟡 |
| **回** | R2.11（主）；R2.10、R2.12（部分） | 回复信 | `B9_ThyroidXAgent_修改与回复计划.md` §4 | 🟡 |
| **专家行** | LLNM / Tiger S5 非灰底 | S5 | `B9_LNM_*`；`B9_FTCPTC_*`；`B9_回复素材_*` | ✅ |
| **协作** | 真 FTC 重训 | — | 🔒 **F7** | ⬜ |

---

## B10　基线训练协议公平性

| 类别 | 必交付项 | 稿内位置 | 仓库入口 | 状态 |
|------|----------|----------|----------|------|
| **新补表** | 各基线：数据（dataset3/4）、微调 vs 零样本、权重来源 | **Supp. 新表 S[X]** | `../b10/tables/baseline_training_protocol.md` | ✅ |
| **改表** | S3/S4 基线行与 B2 CI、checkpoint 注 | S3/S4 | B2 + `b10/tables/` | 🟡 表注入稿 |
| **文** | Methods 基线段落与表一致 | Methods 4.3 | B10 | ✅ |
| **图** | 无 | — | — | — |
| **回** | R2.14 | 回复信 | B10 + B2 | ✅ |

---

## B11　方法细节（后处理、小结节、放射组学栈）

| 类别 | 必交付项 | 稿内位置 | 仓库入口 | 状态 |
|------|----------|----------|----------|------|
| **文** | 连通域 ≥50 px；Dice 用 `selected_masks`；**无** radiomics CCA | Methods **4.3** | `../b11_b12/REVIEWER_SNIPPETS_ZH.md` | ✅ |
| **文/表** | &lt;5 mm 结节 N/M（注明 mm/像素假设） | Methods 或 Supp. 小表 | `../b11_b12/tables/R2_20_*` | 🟡 |
| **文** | AutoGluon 版本/预设/bagging；PyRadiomics 特征数 | Methods + Supp. | `docs/reproducibility_radiomics.md` | ✅ |
| **图** | 无必须 | — | — | — |
| **回** | R2.20、R2.21 | 回复信 | b11_b12 snippets | ✅ / 🟡 |

---

## B12　图像侧数据流 + 宏平均定义

| 类别 | 必交付项 | 稿内位置 | 仓库入口 | 状态 |
|------|----------|----------|----------|------|
| **主图/补图** | **图像臂**数据流（train/val/test 按组件；阈值在哪定） | **Fig.1**（或与共同作者拼全图） | `../b11_b12/DATAFLOW_FIGURE.mmd`；`DATAFLOW_FIGURE_PLAN.md` | 🟡 未导出 |
| **文** | 五队列 **无权重宏平均** AUROC/AUPRC；修正摘要/§2.2 旧「均值」 | Abstract；Results §2.2 | `../b11_b12/README.md` | ✅ 数字 |
| **文** | 28,458 **分层计数**（图像侧能写的先写） | Abstract；§2.1 | B1 + B12 计划 | 🟡 |
| **回** | R1.4、R2.1、R2.3、R2.7 | 回复信 | b11_b12 | 🟡 |

**说明**：B11 与 B12 共用目录 `b11_b12/`；B11 偏 Methods 字，B12 偏 Fig + 全文数字定义。

---

## 回复信拼装顺序（建议）

1. **R2.2 + R1.1** ← B1 + B2  
2. **R2.7 + R2.1（分类宏平均）** ← B12/B11  
3. **R2.14** ← B10 + B2  
4. **R2.20–21** ← B11  
5. **R2.11–12 + R2.10** ← B9  
6. **R1.2 + R2.8 + R3.1** ← B3（+ 日后 B4）  
7. **R1.4 + R2.3 + R3.3** ← B12 + B1  

**暂勿用数字回复**：B7、B8 定稿前；B4/B5 未完成前勿写死 R2.8/R3.2 细节。

---

## 除文图表外的通用要求（勿漏）

- [ ] 回复信每条：**引用审稿原文一句** + 对应 B 包结论（见 `REVIEWER_RESPONSE_PLAN_ZH.md`）。  
- [ ] 改 Supp. 表时同步改 **正文一句 + 摘要**（尤其 B2、B9、B12）。  
- [ ] 新实验：**配置与 `results.json` 路径**可归档（G4 代码发布前）。  
- [ ] NHC：**LLM 消融 vs 主表 no-LLM** 在 Methods/Limitations 写清（B3/B7/B8）。  
- [ ] 协作项在稿面写 **Limitation 或「院内数据待补充」**，不冒充已完成（F6、G3、F7）。

---

*最后更新：与 `docs/revision/` 目录状态一致；状态列随实验推进改 ✅/⬜。*
