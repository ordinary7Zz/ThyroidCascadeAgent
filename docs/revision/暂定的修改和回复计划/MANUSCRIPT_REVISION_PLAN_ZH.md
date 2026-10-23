# 稿件修改计划（中文）

> **对照稿件**：`docs/ThyroidXAgent.md`（LaTeX 源稿）  
> **对照结论**：`docs/revision/b*/` 各包结论文档  
> **用途**：指导修订稿 **Methods / Results / 摘要 / 图表** 的改写顺序；数值可先占位，定稿前用最新 JSON/表替换。  
> **不修改**：`docs/ThyroidXAgent_返修计划与回复_中文.md`（内部计划原件）。  
> **范围**：仅 **B1–B12** 对应的稿面修改；**不含** Shiyu **S1–S10**（报告生成 §2.5–2.6、Methods 4.4–4.5、Fig.5、读者研究等由共同作者另稿）。  
> **写稿流程**：**本文件为唯一「拟改稿」清单**；**暂不直接修改** `docs/ThyroidXAgent.md`，待返修统稿时按 §8–§9 等条目一次性合并进 LaTeX 源稿。  
> **语言**：仅维护本中文计划（无英文平行稿）。  
> **B11 / B12（当前范围）**：**无需补充实验**；B11 分析已完成，B12 除已定稿数据流图外均为 **改稿与回复文字**（数字已核对，见 `../b11_b12/README.md`）。  
> **接近定稿包**：**B11 → B12 → B1 → B2 → B10**（实验/审计/表素材已齐；剩 **统稿进 `ThyroidXAgent.md`、Supp. 编号**）。

---

## 接近定稿的工作包（优先统稿顺序）

| 顺序 | 包 | 稿面/回复 | 仓库入口 | 统稿前小项 |
|:---:|---|-----------|----------|------------|
| 1 | **B11** | R2.20–21；Methods 4.3 | `../b11_b12/` | §8.3 入稿；R2_20 Supp. |
| 2 | **B12** | R2.7、R2.1、R2.3、R1.4 | `../b11_b12/README.md` | 宏平均；数据流 Fig. |
| 3 | **B1** | R1.1、R2.2、R2.4 | `../b1/B1_结论与回复素材.md` | ZJH excl. Supp.；可选 F6 |
| 4 | **B2** | R1.1、R2.2、R2.14（CI） | `../b2/conclusions/B2_结论与回复素材.md` | 刷 S3/S4 |
| 5 | **B10** | **R2.14**；Supp. 协议表；S3/S4 表注 | `../b10/B10_结论与回复素材.md`；`../b10/tables/baseline_training_protocol.md` | 定 **S[X]**；§6.2 核对 |

其余 **B3–B9** 仍在本计划全文中索引，见 [`B_DELIVERABLES_CHECKLIST_ZH.md`](./B_DELIVERABLES_CHECKLIST_ZH.md)。

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
| LNM / FTC/PTC AUROC | 与 B9 新 CV 可能不一致 | 与 `b9/*结论.md` 统一数字；FTC/PTC 加 **域迁移/探索性** 限定 | B9；`b9/需要确认.md` | **框架可改**（术语待 F7） |

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
| LNM 训练规模 | **4753 CV 池 / 4936 未扣 val 写法** 与 **20 例 val 不参与 CV** 写清 | `b9/B9_LNM_*结论.md` | **可改** |
| FTC/PTC 训练标签 | 明确 **FVPTC ≠ FTC**；任务为迁移/探索性（若选 B 方案） | `b9/B9_FTCPTC_*`；临床定义待协作 | **框架可改** |

### 2.2 分割与分类（Agent-routed evidence…）【B2/B3/B10/B11】

| 修改点 | 建议 | 依据 | 就绪度 |
|--------|------|------|--------|
| Table S3/S4 点估计与 **95% CI** | 全表改为 **cluster-bootstrap CI**（1000, seed 42）；主系统 `b2/tables/*_b2.json`；监督基线 **58/58**（`BASELINES_INDEX.json`）；**不含 NHC** | `b2/conclusions/B2_结论与回复素材.md` | **可改**（计算已闭环） |
| 补充 **患者级** 分类表 | ZJH-8K、ThyroidXL 患者级 AUROC/AUPRC（概率平均、标签 max） | 同上 §3.2、§4.4 | **可改** |
| **新 Supp.：ZJH 敏感性** | 全量 ZJH vs excl. train dHash H=0（分类+分割；主系统+基线） | `*_b2_excl_train_dup.json`；`BASELINES_INDEX_excl_train_dup.json` | **可改**（统稿制表） |
| DDTI_cls 行 n | 表中 **349** 图、一图一簇 | `ddti_cls_b2.json` | **可改** |
| 正文「mean AUROC 0.9466」等 | 改为与 S4 **宏平均**一致并定义 unweighted | `b11_b12/README.md` | **可改** |
| NHC 柱状图 Fig.2h | CI 与中心异质性待 B7/B8 定稿；低 Dice 中心解释 | B7 计划；`b8` 烟雾版**勿写入** | **待协作** |
| **路由贡献** 新小节 | 增加静态路由消融结论：无单一最优、max-conf 分割差、Oracle 有空间 | `b3/B3_WAVE1_RESULTS.md`、`REVIEWER_RESPONSE_SNIPPETS_B3.md` | **框架可改**（仅 3 队列波次 1；CI 与 B2 对齐后更新） |
| S6 与 S4 ZJH 矛盾 | B4：在正文解释 **单专家消融 vs 完整 Agent 流水线** | `REVISION_B3_B4_PLAN`；B4 未落成稿 | **框架可改** |

### 2.3 交互分割与时间【稿内 §2.3，属图像工作流】

| 修改点 | 建议 | 依据 | 就绪度 |
|--------|------|------|--------|
| 时间数字统一 | 9.11 s 等与 Fig.2i 一致 | 内部数字核查清单 | **可改**（核对源日志） |

### 2.4 LNM 与 FTC/PTC【B9】

| 修改点 | 建议 | 依据 | 就绪度 |
|--------|------|------|--------|
| Methods/Results 协议 | 5 折患者级 CV、C2 外测、患者级聚合、cluster CI | `b9/B9_回复素材_仅基于两篇实验结论.md` | **可改**（数字可替换） |
| Fig.3 标签 | AUROC/AUPRC 标反问题（R2.1） | A7 | **可改** |

### 2.5–2.6 报告生成与读者研究

**不在 B1–B12 范围内**，本计划不列修改项。对应内部任务 **S1–S10 / F1–F3 / F10** 与审稿条 **R1.5–6、R2.13、R2.16–19、R3.4–5** 等，由 Shiyu / Fei Chen 另稿。

---

## 3. Methods（仅 B1–B12 相关小节）

| 小节 | 修改点 | 依据 | 就绪度 |
|------|--------|------|--------|
| **4.1 数据** | patient ID 表；无 ID 队列 **一图一簇**；**DDTI_cls=349**；**dHash** 跨库近重复（堆叠 train vs 外测、TN3K↔ZJH）；**不写** stem 互斥作主论据；TN3K–ZJH **患者**重叠 F6 或 Limitation | `b1/B1_结论与回复素材.md`；`b1/DATASET_AUDIT.md` | **可改**+**待协作**（F6 可选） |
| **4.6 统计** | cluster bootstrap（1000, seed 42）；患者级 **概率平均、标签 max**；ZJH **敏感性**：剔除与 stacked train dHash H=0 的图后重算（不重训） | `b2/conclusions/*`；`b1/B1_结论` §复现 | **可改** |
| **4.3 分割/分类/路由（B11）** | 见 **§8.3**；R2.20(b) Supp. 表见 **§8.4**（数字已生成） | `b11_b12/`、`reproducibility_radiomics.md` | **可改**（统稿时写入；不提前改正文源稿） |
| **4.3 路由** | 消融策略列表；prompt/schema（B6 定稿前可写「见补充」） | `b3`；`b6` 试点 | **框架可改** |
| **4.4–4.5 报告** | — | — | **范围外（S 任务）** |
| **基线训练（B10）** | Supp. **S[X]** 协议表 + Methods 4.3 段 + S3/S4 表注 | `b10/B10_结论与回复素材.md`；`b10/tables/baseline_training_protocol.md` | **接近定稿**（仅统稿） |

---

## 4. 图表与补充材料

| 项目 | 动作 | 依据 | 就绪度 |
|------|------|------|--------|
| **新 Fig. 数据流（图像臂）** | 自 `DATAFLOW_FIGURE.mmd` 导出 | B12 | **框架可改** |
| **S3/S4** | 更新 CI；基线 **58** 行与 `BASELINES_INDEX.json` 一致；**DDTI_cls n=349** | B2 | **可改** |
| **S5** | LNM/FTC 与 B9 一致 | B9 | **可改** |
| **新 Supp：患者级分类** | ZJH + ThyroidXL（全量 ZJH） | B2 | **可改** |
| **新 Supp：ZJH train-duplicate 敏感性** | 全量 vs excl.（992 图）；见 `BASELINES_INDEX_excl_train_dup.json` | B1+B2 | **可改** |
| **新 Supp（可选）：近重复审计** | dHash 配对计数或 `near_dup_pairs/stacked_train_vs_ZJH-8K.pairs.json` 摘要 | B1 | **框架可改** |
| **新 Supp：B3 路由消融** | 波次 1 表 + 待补队列 | B3 | **框架可改** |
| **R2.20 小结节表** | 七队列 N/M（`run_r2_20_small_nodules_all.sh`；当前 **mm/pixel=0.1**） | `b11_b12/tables/R2_20_SUMMARY.md` | **可改**（间距校准后重跑脚本即可，非新实验） |

---

## 5. Discussion 与 Limitations

| 主题 | 建议 | 就绪度 |
|------|------|--------|
| 统计独立性 / 同院重复 | dHash 筛查与 ZJH 敏感性（Supp.）；无 public ID 队列为图像级 bootstrap；**勿**声称 filename 互斥即无泄漏 | **可改** |
| 路由价值 | 与 B3 叙事一致；LLM vs 学习型路由留双分支表述 | **框架可改** |
| 校准/拒答（B8） | 指向 B8 定稿结果 | **待协作**（当前烟雾版不可入稿） |
| 读者研究 / 报告主张 | — | **范围外** |

---

## 6. 建议修改优先级（仅 B1–B12）

1. **R2.7 / R2.1**：摘要与 §2.2 宏平均 + CI 定义（`b11_b12` + `b2`）  
2. **R2.2 / R1.1**：Methods 4.1/4.6（**dHash** + cluster CI）+ S3/S4 + 患者级附表 + **ZJH 敏感性 Supp.**（`b1`+`b2`）  
3. **R2.14（B10，接近定稿）**：Supp. 协议表 + Methods/S3/S4 表注（`b10/B10_结论`；与 B2 CI 同条回复）  
4. **R2.20–21**：Methods 4.3 技术段（`b11_b12`）  
5. **R2.8 / R1.2**：新 Results 小节 + B3 表（`b3`）  
6. **R2.3 / R1.4**：图像侧数据流图（`b11_b12` + B1）  
7. **B7/B8/NHC**：B7 中心异质性；B8 校准拒答（数据到位后）  
8. **B4/B5**：组件消融、元数据消融（若纳入本轮 B 包）  

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
| B4–B8 | 计划见 `docs/REVISION_B*_PLAN.md`；结论文档以各 `b*` 目录为准 |
| B9 | `../b9/B9_回复素材_仅基于两篇实验结论.md` |
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
- LNM **4936/4753**、Fig.3 轴标签等见 B9 / A7 总表，改 B12 时 **顺带扫一眼** 即可。

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
