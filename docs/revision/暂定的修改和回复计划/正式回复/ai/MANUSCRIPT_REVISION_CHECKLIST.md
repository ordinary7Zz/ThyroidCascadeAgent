# 主稿与回信修订清单（由回信 `\rpending` 迁出）

**用途：** 统稿时改 `docs/ThyroidXAgent.md`（及摘要/图注/补充材料），以及回信须补的制图等；**一律**在本文件跟踪，**不再**在 `response_letter/generated/body_en_merged.tex` 里用红色 `\rpending`（除必须保留的 Manuscript pending）。  
**真源数字/表：** 以正式回信信末表为准（`\responsetableref{...}` 所指）。

状态：`[ ]` 未做 · `[x]` 已完成（统稿后自行勾选）

---

## R2.1 — 审稿人 2，意见 1

**审稿意见（原文摘要）**

> Several key values are inconsistent across the abstract, main text, figures, and supplementary materials.

**主稿待改**

- [ ] **摘要 + Results §2.2 总表对齐**：与回信表 `\responsetableref{tab_seg_ext}`、`\responsetableref{tab_cls_ext}`、`\responsetableref{tab_malig_oof}`、`\responsetableref{tab_malig_ext}` 一致；删改仍引用旧稿数值的句子/图注。
- [ ] **跨队列良恶性「均值」**：原稿 mean AUROC **0.9466**、mean AUPRC **0.8361**（主文 Fig.~2d–e）→ 按 R2.7 **五外测队列等权宏平均**（不按测试图数加权），改为 AUROC **0.9080**、AUPRC **0.8964**（ZJH 外测 **6807** 张；`\responsetableref{tab_dhash}`、`\responsetableref{tab_cls_ext}`）。
- [ ] **跨队列分割「均值」**：原稿 mean Dice **87.21%**、mean HD95 **6.90 mm** → 七队列宏平均 Dice **86.27%**、HD95 **7.73 mm**（6807 张 ZJH 子集；`\responsetableref{tab_seg_ext}`）。
- [ ] **主文 Fig.~3 示例图**：核对/替换为 ZJH 外测 hold-out 病例；PTC 亚型与 LNM 标签与图注一致（回信 R2.1 第 (3) 条已声明将替换误标 PTC/FTC 面板）。

---

## R2.3 + R3.3 — 审稿人 2 意见 3；审稿人 3 意见 3（28,458 表述）

**审稿意见（原文摘要）**

- **R2.3：** Please clarify why **28,458** observations are described as **"non-overlapping test cases,"** as this number appears to combine **19,737** test images with **8,721** NHC-MISD-TUS cases.
- **R3.3：** The definition of **"28,458 non-overlapping test cases"** is unclear. Please clearly describe the **data hierarchy** and confirm **patient-disjoint** splits.

**主稿待改（28,458 / 层级文字）**

- [ ] **删除或改写**易误解的 **「28,458 non-overlapping test cases」** 表述：改为与回信一致的分层计数——七个分割/分类外测 **19,737 张测试图** + NHC-MISD-TUS **8,721 张**腺体分割测试图（及任务特异 $n$；**勿**将图像数写作 cases/病例）；并说明未计入报告生成与恶性子任务外测。分层逻辑与数字对齐回信 `\responsefigureref{fig_image_dataflow}`（R2.3 正文已澄清）。
- [ ] **数据层级与患者互斥**：在 Methods/数据段写清 patient / examination / image / task 层级，以及 train/val/test 在具备 patient ID 时的互斥规则（与回信 R3.3 叙述一致即可，不必重复 28,458 旧措辞）。

---

## R2.20 — 审稿人 2，意见 20

**审稿意见（原文摘要）**

> Thresholds for connected-component analysis in post-processing are unspecified. The manuscript mentions removing isolated noise regions via connected-component analysis but does not specify: **(a)** minimum connected-component area threshold; **(b)** whether small nodules (&lt; 5 mm) may be erroneously removed; **(c)** algorithm for separating multiple nodules.

**主稿待改**

- [ ] 在 Methods **「Segmentation, classification and radiomics」**（或等价小节）补全 **专家内**连通域规则（与回信一致，**非**路由器最终 mask 再二次删小连通域）：
  - 概率图 **0.5** 二值化；
  - 去除面积 **&lt; 50 px** 的连通域 + **5×5** 闭运算；
  - 集成 mask 多连通域时 **保留最大连通域**；
  - **单 ROI / 不逐灶分多结节**（对应审稿 (c)）。
- [ ] **小结节表述**：与回信 `\responsetableref{tab_small_nodule_fail}` 一致（&lt;50 px 子集、路由器最终 mask 不重复施加 ≥50 px 规则；&lt;5 mm 列为 0.1 mm/px 说明性换算时可加注）。

---

## R2.15 — 审稿人 2，意见 15（伦理、知情同意、NHC-MISD-TUS 治理）

**审稿意见（原文摘要）**

> Ethics approval number without consent/waiver; institutional datasets need design, period, de-identification, governance; co-author authorization for NHC-MISD-TUS does not replace ethical approval and regulatory compliance.

**前提（与回信 R2.15 一致）**

- **ZJH 机构数据**：珠江医院伦理 **2026-KY-081-01**（回顾性、知情同意豁免等）。
- **NHC-MISD-TUS**：**不**挂靠 2026-KY-081；主稿写「国家卫生健康委医学影像标准数据库授权子集 + 已签署数据库合作/数据合规协议（回信不附协议全文）」；外测 only。

**主稿待改**（`ThyroidXAgent.md` Ethics / Methods / Data availability）

- [ ] **Ethics 段（新建或扩写）**：回顾性设计；**2026-KY-081-01**；书面知情同意 **豁免**（附伦理办对外原句）；去标识程序（一句）；机构数据治理。
- [ ] **点名 NHC-MISD-TUS**：国家卫生健康委医学影像标准数据库授权甲状腺外测子集；**数据库合作/数据合规协议**（不附全文）；**仅外测**、未参与堆叠训练；去标识/数据使用条件与 R2.6 一致（**勿**写纳入 2026-KY-081-01）。
- [ ] **Data availability**：改写原「仅 Prof. Kong authorized access」句——共同作者协助准入 **supplementary**，不替代伦理批件与库方数据使用治理；与 Ethics 段不矛盾。
- [ ] **ZJH 机构集**：研究时段、ZJH-8K（及稿面涉及的 ZJH 恶性/报告资源若适用）与伦理批件对应。
- [ ] **公开集**：主稿 Data availability 保留「按各数据集发表文献与许可」一句即可；**R2.15 回信不必逐列**（见 R2.5 / Methods）。
- [ ] **报告/读者研究等**（若主稿保留）：SMU-HMC、ZJH-TS、读者研究伦理在本节或单独句补全（本回信已说明在修订稿统一表述中展开）。

---

## R2.6 — 审稿人 2，意见 6（NHC-MISD-TUS）

**审稿意见（原文摘要）**

> The NHC-MISD-TUS cohort is insufficiently described … numbers of patients, nodules, and images per centre … centre-level performance and heterogeneity.

**主稿待改**（回信已澄清；以下同步 `ThyroidXAgent.md` / 摘要 / Data availability，**不在** `body_*.tex` 用 `\rpending`）

- [ ] **NHC-MISD-TUS 来源与角色**：Methods 与 Data availability 写明数据来自 **国家卫生健康委医学影像标准数据库**授权子集；**仅外测**、未参与堆叠训练；与回信 R2.6 一致。
- [ ] **规模与计数口径**：全文（摘要、Results、图注）将 NHC-MISD-TUS **8,721** 统一为**全腺体分割外测图像数**；结节 **6,384**、良恶性 **4,999** 为任务可评图像数；**勿**写「8,721 cases/病例」或与 28,458 混用「cases」。**勿**在 Fig.~3 / 数据流图 caption 中暗示 6384/4999 任务分层（该分层仅在 NHC-MISD-TUS 逐中心表与回信 R2.6 叙述；图只承担队列—划分—用途时可保留 8721 或 NHC-MISD-TUS 外测块）。
- [ ] **35 站点**：表述为 **35 个去标识参与站点**（Centre ID）；**不**公开医院名称、逐站患者/结节数或扫描仪型号（与回信披露边界一致）。
- [ ] **入库与标注（概括）**：Methods 增加一两句：多中心按平台统一结构化规范入库，平台质控后形成任务参考标注（不写院内操作者细节）。
- [ ] **结果叙述**：稿面 NHC-MISD-TUS 性能与投稿补充材料中 **NHC-MISD-TUS 逐中心表**（序号以当时稿面为准）及 B7 真源一致；异质性表述与回信 `\responsetableref{tab_nhc_heterogeneity}` 一致（不要求稿面重复逐站表；**回信勿写死** Supp. S*）。

---

## R3.3 — 审稿人 3，意见 3（层级流程图入信）

**审稿意见（原文摘要）**

> Besides, a simple flowchart showing the relationship of **patient, examination, image/video, lesion and task** would greatly improve the clarity.

**回信待补**（R3.3 正文已用文字 + `\responsefigureref{fig_image_dataflow}` 回应划分与互斥；**单独层级图**在此跟踪，非 `ThyroidXAgent.md` 主稿换图）

- [ ] 绘制 **患者—检查—图像/视频—病灶—任务** 层级流程图（与 `fig_image_dataflow` 的队列—划分—用途数据流图**分工**，勿混为一图）
- [ ] 图入正式回信（`response_letter/figures/`）、注册 `\responsefigureref{fig_*}`，图题与 `body_en_merged.tex` 一致
- [ ] R3.3 末段（或合适句）补一句引用该层级图（与现「上文概括 + 数据流图相区分」衔接）

---

## 维护说明

| 迁出前 `body_en.tex` pending 文案 | 本清单条目 |
|-----------------------------------|------------|
| `Manuscript abstract/Results sync` | R2.1 总项 |
| `Update abstract/§2.2 … benign--malignant …` | R2.1 良恶性均值 |
| `Update abstract/§2.2 … segmentation …` | R2.1 分割均值 |
| `Manuscript: remove ambiguous "cases" wording for 28,458` | R2.3 + R3.3 |
| `Manuscript: Methods "Segmentation, classification and radiomics" …` | R2.20 |
| R2.15 ethics / NHC-MISD-TUS governance / consent waiver | **R2.15** 节 |
| R2.6 NHC-MISD-TUS 稿面 Methods / 8721 cases 等 | **R2.6** 节 |
| add hierarchy flowchart to this letter / 层级流程图入信 | **R3.3** 节（入信制图） |

**`body_{en,zh}.tex`：** 无红色 `\rpending`；未勾选项仅在本清单与 `PENDING.md` 维护。
