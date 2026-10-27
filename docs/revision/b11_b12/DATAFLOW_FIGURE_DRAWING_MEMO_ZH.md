# 数据流图绘制备忘（对话整理）

> 整理自返修讨论（R1.4 / R3.3 / R2.3、版式、风格、分工）。  
> 与 [`DATAFLOW_FIGURE_PLAN.md`](DATAFLOW_FIGURE_PLAN.md)（Mermaid 五泳道、队列数字）互补：本文侧重**审稿人意图、双 panel 策略、视觉风格、组件定义、协作边界**。  
> 回信：**图 R3**（`fig_image_dataflow`）；原文字版表 `tab_dataflow` 已删除。真源 PNG：`暂定的修改和回复计划/pictures/` 与 `正式回复/figures/fig_image_dataflow.png`。

---

## 1. 审稿人到底要几张图？

审稿人**未**要求「两张独立 Figure」，而是两条不同诉求，**合并为一张图、两个 panel** 是常见且合理的做法：

| 意见 | 审稿人原意（摘要） | 对应 panel |
|------|-------------------|------------|
| **R3.3** | 澄清数据层级；训练/验证/测试在适用处**患者互斥**；**简单流程图**：患者 → 检查 → 图像/视频 → 病灶 → **任务** | **(A) Data hierarchy & tasks** |
| **R1.4** | 因 **ZJH-8K** 双重用途，提供**完整数据流图**：**每个组件**用了哪些数据做 **训练、验证、阈值选择、测试** | **(B) Component-wise train · val · test**（图像臂主体） |
| **R2.3**（常一并写进 caption） | 「28,458 cases」混用 **19,737 测试图 + 8,721 NHC**；**不含**报告生成与恶性子任务外测的计数方式 | 多在 **(A) 角注 + caption**，不必单独第三 panel |

**R1.4 原文要点（中文回信）**：ZJH-8K 为分割与良恶性外测，恶性图又用于 LNM/FTC 开发；需完整数据流图说明各组件的 train/val/阈值/test。

**R3.3 原文要点**：层级与患者互斥 + 简单流程图（含 **images/videos** 与 **tasks**）。

---

## 2. R3.3 与 R1.4 的范围：是否包含报告生成？

### R3.3

- **应覆盖**：分割、良恶性分类、恶性子任务（LNM、FTC/PTC）、**报告生成**等在「任务」层的存在；检查层可区分 **image / video**（稿中 video 主要关联报告臂，如 TNVideo、读者研究）。
- **不必在同一张简单图里**：报告各队列的 train/val/test 细节（SMU-HMC、KMVE、模板库等）→ **Fig. 5 + Shiyu S9**。
- **28,458 澄清**：计数框按 **图像臂 + NHC** 写；**不要**把报告测试数塞进该合计。

### R1.4

- **动机与主体**：**图像分析流水线**（专家池、路由、850 val、拒答/校准、AutoGluon、外测队列）+ **ZJH 双角色** + **LNM/FTC 支路**。
- **「每个组件」**：指 **系统功能模块 × 数据划分**，**不是** Table S3/S4 里的对比基线（TransUNet、MedSAM 等）；基线协议见 **R2.14** / `tab_baseline_protocol`。
- **报告生成**：R1.4 字面「每个组件」可包含报告臂；**实操**由 **B12（图像双 panel）+ S9（报告数据流）+ Fig. 5** 交叉引用闭合，不必在 Panel (B) 再画一条 ReAct 全流程。

### 分工（返修计划）

| 负责人 | 交付 |
|--------|------|
| **Baidong / B12** | Panel (A)(B) 图像臂；`DATAFLOW_FIGURE.mmd` 泳道 A/B/D/E 等 |
| **Shiyu / S9** | 报告臂：SMU-HMC、KMVE、ZJH-TS、TNVideo、两套模板库的划分；与 B12 **合并**为正式 Supp. Fig. |
| **统稿** | Fig 编号、caption、回复 R1.4/R3.3 引用话术 |

---

## 3. R1.4 中「组件」指什么？

**不是**：ThyroidXAgent vs TransUNet vs … 每个 baseline 各画一条数据流。

**是**：ThyroidXAgent **流水线内**会接触数据、拟合或冻结配置的**功能块**，例如：

| 组件 | 图中应传达的划分信息 |
|------|---------------------|
| 分割 / 分类 **专家池**（多 checkpoint，非单个 baseline 名） | 堆叠 train ~18k；**850 val**（选专家等）；各外测 **test only** |
| **路由器**（静态 / 学习型 / LLM） | **850 val** 拟合或选型；外测冻结 |
| **拒答 / 校准** | **仅 val 拟合**阈值 |
| **PyRadiomics + AutoGluon** | development + 参考 mask 训练（如 17,774 行）；外测 **frozen** |
| **LNM / FTC–PTC 子任务** | ZJH 恶性子集开发 vs LymphUs C2 / FangDai 外测；与 ZJH 通用外测 **分岔（dual-role inset）** |

推理链（Seg → Cls → Route → Radiomics → Consensus）可画为 **一条主路径上的阶段**，不必与「组件」一一拆成满屏方框。

---

## 4. 推荐版式：一张图、双 panel（主文或 Supp.）

与稿内 **Fig. 4–6（Shiyu）** 风格对齐，而非 Lucidchart 式满屏绿块：

### Panel (A) — R3.3

- 左：可选甲状腺超声缩略图。
- 中：编号链 ① Patient → ② Examination → ③ Image/video → ④ Lesion (ROI)。
- 右：任务列（Seg、BM、LNM、FTC/PTC、**Report †**）。
- 脚注：患者互斥 / 一图一簇（与 R1.1、R2.2 一致）。
- 角注：**19,737（7 队列）+ 8,721 NHC**；不含报告/子任务外测计数。
- **Report †** → 图注指向 **Fig. 5 / Supp.（S9）**。

### Panel (B) — R1.4（图像臂）

- **主视觉**：一条 **sage green (#6B8F71)** 弧形主路径（仿 Fig. 5d），灰圆角卡片 + 轻阴影。
- 左：**Stacked development**（~18,277）；旁注 **ZJH-8K 未参与专家训练**。
- 中：Experts → Router → Radiomics → Fusion/Consensus；Router 外 **琥珀虚线 n=850**（expert pick、learned router、referral/calibration）。
- 右：**一个**「External evaluation」大区（Public / Institutional / Multicentre），**不要**三行重复七个绿块；外测 **⊘ train**。
- 右下 **紫色虚线 inset**：ZJH malignant subset → LNM dev → LymphUs C2 ext.；FTC/PTC dev → FangDai ext.；虚线连回 Institutional 区「same images · different tasks」。

### 图例（底部 4 项即可）

绿箭头 = development & inference flow；琥珀虚线 = validation fit (n=850)；灰绿区 + ⊘ = external test only；紫虚线 = shared subset / dual role。

### 与 AI 出图的迭代结论

1. **第一版**：信息全但像工程图，无设计感。  
2. **极简版**：好看但难对应审稿人。  
3. **Shiyu 风 + 补关键数字（v4 prompt）**：**适合作为手绘定稿母版**；数字与队列名须对照 Table S1 / 图 R3 人工核对（AI 易错 TN5K、RJH 等）。  
4. **Fusion** 命名：手绘时可改为 **Consensus / evidence fusion**，与 Methods 一致。  
5. **850 val 与 AutoGluon**：caption 建议一句分清——router/referral 在 pooled val 850；AutoGluon 在 classification development 集训练。

---

## 5. 主图 vs 补充材料

| 层级 | 内容 |
|------|------|
| **主图 / Supp. 双 panel** | 审稿人 5 秒可读的骨架 + R1.4/R3.3 硬信息 |
| **Supp. 详图或 `DATAFLOW_FIGURE.mmd`** | 全队列表、报告泳道 C、五泳道全量 |
| **Fig. 5** | 报告组装流程（不重复画进 Panel B） |
| **图 R3** | 回信图像侧数据流（已取代临时文字表） |

---

## 6. 手绘 / 定稿检查清单（Panel B 图像臂）

- [ ] ~18,277 stacked train；**850** unified validation 及三项用途  
- [ ] ZJH-8K：**专家未在 ZJH 训练** + dual-role inset（LNM/FTC）  
- [ ] 外测三大类；必要时 caption 列全队列（DDTI、RJH-7K、PKTN 等）  
- [ ] LymphUs C2、FangDai 外测端点  
- [ ] AutoGluon / 17,774 与 val 850 分工在图注写清  
- [ ] 不含「每个 baseline 模型一条流」  
- [ ] Panel (A) 含 Report 任务与 video 层级提示；28,458 拆解正确  

---

## 7. 绘图大模型 prompt（R1.4 单图 · v5.4）

- **定位**：仅 **R1.4**（组件 × train/val/test）；单图、无报告全流程。  
- **风格 / 构图**：三列通栏、纵向饱满（v5.2）；左卡正面列举 train/val、Router 不写 n=850、禁止 “not in”（v5.3）。  
- **v5.4 组件**：**AutoGluon 并入 Experts**（与 DINO 同为在左卡开发池上 fit 的 expert）；**取消独立 Radiomics 模块**；**不画 AutoGluon 路由支路**（推理期融合由 Router + Consensus 概括即可）。中间 **三模块**：Experts → Router（橙虚线 val-fit）→ Consensus。  
- **AutoGluon 配置**：写在 **Experts 卡内** 脚注（600 s、8-fold 等，R2.9），不重复数据量。  
- **数字真源**：Table S1 / `DATAFLOW_FIGURE_PLAN.md`。

### 完整英文 prompt（复制给生图模型）

```
Create a single wide scientific figure for a Nature Communications–style thyroid ultrasound AI paper. Scope: Reviewer R1.4 only — image-analysis component splits (train · validation · test). No multi-panel letters, no report-generation workflow (caption may cite Fig. 5 / Supp. elsewhere).

STYLE: Match manuscript Fig. 4–6 family — muted sage-green (#6B8F71) flow, light gray rounded cards (#F5F6F7), soft 4px shadows, thin strokes (#4A4A4A), pale blue (#D6E8F5) and pale sand (#F0E6D8) stacks, amber dashed validation (#E0A458 / #FFF6E8), purple dashed dual-role (#9B7BB8). Flat editorial vector — NOT Lucidchart, NOT rows of identical green tiles, NOT yellow sticky notes.

INFORMATION DESIGN (v5.3 + v5.4):
• POSITIVE train/val cohort lists on LEFT cards only. No “not in”, “excluded”, or “not the 850 pool”.
• Router: validation-fit operations only — no validation count on Router.
• AutoGluon = part of Expert pool for R1.4 data narrative (same pools as left cards). NO separate Radiomics box, NO AutoGluon routing side branch, NO train row counts.

CANVAS: landscape 16:9 or 2:1, white background. Use ~85–90% of canvas HEIGHT. Bottom: 4-item legend.

COMPOSITION — three balanced vertical columns:
• LEFT (~24%): Development data island (two task cards).
• CENTER (~40%): Shared pipeline — THREE stacked modules (Experts tall → Router → Consensus); sage arrow through column. NOT a 2×2 grid with a missing Radiomics cell.
• RIGHT (~36%): External evaluation + dual-role inset.

LEFT COLUMN — two task cards (8–9pt secondary lines allowed ONLY here for cohort lists):

【Main tasks — pale blue card】
Header: “Segmentation & benign–malignant classification”
• Train (seg, dataset_4): TN3K 4,633 · TN5K 3,500 · ThyroidXL 9,441 · PKTN 703 → total 18,277 images
• Train (cls, dataset_3): TN3K · TN5K · ThyroidXL (same cohort train splits; no PKTN)
• Validation (pooled OpenThyroid val): TN3K 100 · TN5K 500 · ThyroidXL 100 · PKTN 150 → total 850 images
(Do not mention ZJH-8K on this card.)

【Malignant subtasks — pale sand card】
Header: “LNM & FTC/PTC (shared pipeline, task-specific labels)”
• Train LNM: ZJH-8K malignant 4,573 + LymphUs C1 180 → 4,753 images
• Train FTC/PTC: ZJH-8K malignant 4,756 images
• Validation: patient-cluster stratified 5-fold CV (seed 42); LNM 882 clusters · FTC/PTC 722 clusters
(Optional one line: ZJH-8K malignant images listed above — same institution cohort also appears under external test on the right.)

Purple dashed footer inside left island (short): “Malignant dev validation = 5-fold CV (see sand card)” — no comparison to 850.

CENTER COLUMN (three modules only):

Top strip: “Seg → Cls → Route → Consensus” (AutoGluon is inside Experts, not a separate pipeline step label).

1) Experts — largest card. Title: “Expert pool (fit on pools ← left cards)”. Inside one card, two sub-lines:
   • Image experts — DINO checkpoints (seg + cls)
   • Tabular expert — PyRadiomics 2D + AutoGluon Tabular; 7pt config (max 3 bullets): GT reference masks on cls development set · 600 s fit budget · 8-fold bagged ensemble (internal CV); malignant subtasks: task-specific tabular expert on sand-card pools (same 5-fold CV).
   No duplicate train counts; no separate downstream Radiomics module.

2) Router — amber dashed halo only. “Validation-fit (pooled val from main-task card)” · expert selection · learned router · referral / abstention thresholds · frozen at external test.

3) Consensus / evidence fusion — one line: “Agreement shortcut or synthesize expert outputs (LLM in primary system)”. Do not diagram AutoGluon-specific routing here.

RIGHT COLUMN (unchanged intent — test metadata):
• External evaluation — three stacked rows: Public benchmarks (optional one 8pt line: TN3K · TN5K · ThyroidXL · DDTI · RJH-7K · PKTN test splits) · Institutional hold-out ZJH-8K 7,958 · Multicentre private NHC 8,721. Label row: “Evaluate only · frozen pipeline”.
• Dual-role inset: ZJH malignant subset → LNM dev → LymphUs C2 test 158; FTC/PTC dev → FangDai test ~200; purple link to Institutional with “same images · different tasks”.

Flow: left cards → Experts; green arrow through Router & Consensus → External zone.

TEXT: max ~32 labels; no Path A/B; no baseline names; no standalone Radiomics box.

LEGEND: sage arrow = dev & inference; amber dashed = validation-fit (counts on left); gray-green = external test; purple dashed = dual role / malignant dev.

AVOID: separate Radiomics module; AutoGluon routing branch; “not in”; n=850 on Router; train row counts; 2×2 pipeline grid; empty vertical gaps; TN5K / RJH-7K typos.
```

---

## 8. 回复信可引用话术（示例）

- **R3.3**：We added panel (A) of Supplementary Fig. X, depicting the patient–examination–image/video–lesion–task hierarchy and patient-disjoint split conventions; stratified external-test counts replace the misleading “28,458 cases” wording.  
- **R1.4**：Panel (B) summarizes train, validation (n=850), threshold fitting, and external testing for each image-analysis component; ZJH-8K roles for generic testing versus LNM/FTC development are shown in the dual-role inset. Report-generation splits are in Fig. 5 and Supplementary Fig. Y (S9).  

（中文回信已与 `body_zh.tex` 中 R1.4/R3.3 条目对齐，定稿图后统一引用 `\responsefigureref{fig_image_dataflow}`。）

---

## 9. 相关文件索引

| 文件 | 用途 |
|------|------|
| [`DATAFLOW_FIGURE_PLAN.md`](DATAFLOW_FIGURE_PLAN.md) | 队列数字、五泳道、视觉编码 |
| [`DATAFLOW_FIGURE.mmd`](DATAFLOW_FIGURE.mmd) | Mermaid 源图 |
| `docs/revision/暂定的修改和回复计划/正式回复/latex/generated/body_zh.tex` | R1.4 / R3.3 回复正文 |
| `docs/ThyroidXAgent_返修计划与回复_中文.md` | S9/B12 分工表 |
| `docs/revision/b11_b12/REVIEWER_SNIPPETS_ZH.md` | R1.4 回复片段（与 S9 合并） |

---

*文档版本：根据 2026-10 返修对话整理；图号 S[X]、主文 Fig. 编号以统稿为准。*
