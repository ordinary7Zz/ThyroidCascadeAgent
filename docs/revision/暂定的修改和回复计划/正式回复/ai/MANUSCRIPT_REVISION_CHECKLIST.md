# 主稿修订清单（由回信 `\rpending` 迁出）

**用途：** 统稿时改 `docs/ThyroidXAgent.md`（及摘要/图注/补充材料），**不再**在 `latex/generated/body_{en,zh}.tex` 里用红色 pending 标注。  
**真源数字/表：** 以正式回信信末表为准（`\responsetableref{...}` 所指）。

状态：`[ ]` 未做 · `[x]` 已完成（统稿后自行勾选）

---

## R2.1 — 审稿人 2，意见 1

**审稿意见（原文摘要）**

> Several key values are inconsistent across the abstract, main text, figures, and supplementary materials.

**主稿待改**

- [ ] **摘要 + Results §2.2 总表对齐**：与回信表 `\responsetableref{tab_seg_ext}`、`\responsetableref{tab_cls_ext}`、`\responsetableref{tab_malig_oof}`、`\responsetableref{tab_malig_ext}` 一致；删改仍引用旧稿数值的句子/图注。
- [ ] **跨队列良恶性「均值」**：原稿 mean AUROC **0.9466**、mean AUPRC **0.8361**（主文 Fig.~2d–e）→ 按 R2.7 **五外测队列等权宏平均**（不按测试图数加权），改为 AUROC **0.9080**、AUPRC **0.8944**（ZJH 外测 **6807** 张；`\responsetableref{tab_dhash}`、`\responsetableref{tab_cls_ext}`）。
- [ ] **跨队列分割「均值」**：原稿 mean Dice **87.21%**、mean HD95 **6.90 mm** → 七队列宏平均 Dice **86.27%**、HD95 **7.87 mm**（6807 张 ZJH 子集；`\responsetableref{tab_seg_ext}`）。
- [ ] **主文 Fig.~3 示例图**：核对/替换为 ZJH 外测 hold-out 病例；PTC 亚型与 LNM 标签与图注一致（回信 R2.1 第 (3) 条已声明将替换误标 PTC/FTC 面板）。

---

## R2.3 + R3.3 — 审稿人 2 意见 3；审稿人 3 意见 3（28,458 表述）

**审稿意见（原文摘要）**

- **R2.3：** Please clarify why **28,458** observations are described as **"non-overlapping test cases,"** as this number appears to combine **19,737** test images with **8,721** NHC-MISD-TUS cases.
- **R3.3：** The definition of **"28,458 non-overlapping test cases"** is unclear. Please clearly describe the **data hierarchy** and confirm **patient-disjoint** splits. *(另：层级流程图见回信 pending / `PENDING.md` R3.3，属入信制图，非本条主稿文字任务。)*

**主稿待改**

- [ ] **删除或改写**易误解的 **「28,458 non-overlapping test cases」** 表述：改为与回信一致的分层计数——七个分割/分类外测 **19,737 张测试图** + NHC **8,721** 例（图像/病例勿混称为 cases）；并说明未计入报告生成与恶性子任务外测。分层逻辑与数字对齐回信 `\responsefigureref{fig_image_dataflow}`（R2.3 正文已澄清）。
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

## 维护说明

| 迁出前 `body_en.tex` pending 文案 | 本清单条目 |
|-----------------------------------|------------|
| `Manuscript abstract/Results sync` | R2.1 总项 |
| `Update abstract/§2.2 … benign--malignant …` | R2.1 良恶性均值 |
| `Update abstract/§2.2 … segmentation …` | R2.1 分割均值 |
| `Manuscript: remove ambiguous "cases" wording for 28,458` | R2.3 + R3.3 |
| `Manuscript: Methods "Segmentation, classification and radiomics" …` | R2.20 |

**仍在回信中的红色 pending（非本清单）：** R1.3 NHC 元数据/meta-regression；R3.3 层级流程图入信（见 `PENDING.md`）。
