# 改稿历史与理解（AI 追加，供下次新对话阅读）

按时间**倒序**或**正序**均可；当前采用**正序追加**。每次改 TeX 后在文末加一节，**务必写「教训 / 避免重犯」**。

---

## 2026-10-28 — 全信「明确回应」审计：R2.11/R1.3/R2.5/R2.3/R3.1

**文件：** `body_en.tex`、`body_zh.tex`、`latex/README.md`、`ai/INSTRUCTIONS.md`、`ai/README.md`

**做了什么：** R2.11 增 (a)(b)(c)；R1.3 增 NHC 扫描仪/病例/标注关联（interim + pending）；R2.5 分块 + 补充表 pending；R2.3 We agree；R3.1 首条指消融表。文档增加「逐条明确回应」规则。

**教训 / 避免重犯：** 改任意 `\authorresponse` 时对照 reviewercomment 逐句；子问题必须逐条；METHOD-only 禁止。

---

## 2026-10-28 — R1.1 患者级条：呼应审稿 + 合并聚类定义

**文件：** `body_en.tex`、`body_zh.tex`

**做了什么：** 第 3 条开头明确按审稿建议做了 patient-level re-analysis / cluster-bootstrap；`we performed` /「已完成」+ 表 R7/R8；聚类定义并入同条；删孤立 Cluster definitions bullet。

**教训 / 避免重犯：** 患者级/聚类定义勿单独成条无「已做分析」；与表 R7/R8 写在同一条，开头呼应审稿句。

---

## 2026-10-28 — R1.1 患者级 bullet 合并并指表

**文件：** `body_en.tex`、`body_zh.tex`

**做了什么：** 删重复「Patient-level classification」条；在第 3 条合并患者级再分析：聚合/标签规则 + `\responsetableref{tab_patient_cls}`/`tab_patient_seg` + 与图像级表对照。对应审稿意见「Patient-level re-analysis」。

**教训 / 避免重犯：** R1.1 患者级勿 METHOD-only bullet；一条内方法 + 表号；数字放表 R7/R8。

---

## 2026-10-28 — CI 交叉引用仅 follow R2.2

**文件：** `body_en.tex`、`body_zh.tex`、`ai/INSTRUCTIONS.md`

**做了什么：** R1.1/R1.2/R2.11 等处去掉「表注/消融表题」等 CI 强调；正文统一 `follow R2.2`。R2.2 仍保留唯一完整 1000/seed 定义；表 `\responsetablenote` 未改。

**教训 / 避免重犯：** 正文 CI 不写 captions and notes；`follow R2.2` 足够。

---

## 2026-10-28 — CI 协议以 R2.2 + 表注为主；R1.1 去重

**文件：** `body_en.tex`、`body_zh.tex`、`ai/INSTRUCTIONS.md`

**做了什么：** R1.1 删重复 CI bullet 与多处 1000/seed；聚类定义指 R2.2。R2.2 为 canonical protocol（去掉 defined in R1.1）。R1.2 消融 CI 只指 R2.2 与消融表题/表注。`tab_cls_ext`/`tab_seg_ext` 等表注未改。

**教训 / 避免重犯：** 正文其它意见勿再堆 `(1000 resamples, seed 42)`；表注与 R2.2 足够。

---

## 2026-10-28 — R1.1 dHash 表述与 Table R1 对齐

**文件：** `body_en.tex`、`body_zh.tex`

**做了什么：** Table R1 仅含 TN3K--ZJH-8K 两行；正文删「多队列两两筛查」类表述，改为明确「表内仅该对比」；开篇将 `tab_dhash` 与 cluster-bootstrap 表分开；表注增加 “tabulates TN3K--ZJH-8K only”。同步 R2.4、R3 相关句。

**教训 / 避免重犯：** 引 `\responsetableref{tab_dhash}` 时表述范围不得超过表内行；若确有更多 pairwise 结果，先扩表再写正文。

---

## 2026-10-28 — 全文扫段内 above/below/如下/见上条

**文件：** `body_en.tex`、`body_zh.tex`

**做了什么：** 去掉或改写段内跳转：R1.3 `described above`；R2.2 患者数「与下文」→ 表内说明；R2.4「与上文」→ R1.1；R2.9 先写相近层定义再写稳定性实验、删 `(below)`/`见下条`；R1.2「编号如下」；表注/图注/附录 A1 User 段「as above/同上/见上文」改为 note 编号或 fig/table 指名。

**教训 / 避免重犯：** 改完 EN 后 `rg 'above|below'` 与中文「见上/见下/如下/上文/下文」扫一遍；需先定义后引用时 **调 bullet 顺序**，不用 below。

---

## 2026-10-28 — 段内不用 below；R1.1 开篇改表指

**文件：** `body_en.tex`、`body_zh.tex`、`ai/INSTRUCTIONS.md`

**做了什么：** R1.1 第 1 条去掉 `as detailed below and in` → 直接括号引表；中文去掉「口径如下」。INSTRUCTIONS 增加：同一条意见内避免 below/如下，跨 R2.x 可保留。

**对意图的理解：** 同段 itemize 再写「下文」显得乱；跨审稿人指向是为去重，二者分工不同。

**教训 / 避免重犯：** 同 `\authorresponse` 内用表号或并列 bullets，不用段内导航词；全文扫 `below` 时区分「同段」vs「术语定义（如 similar tier）」需否改成 inline 定义。

---

## 2026-10-28 — R1.1 删去 cluster 句末 `(below)`

**文件：** `body_en.tex`、`body_zh.tex`

**做了什么：** 第 2 条 bullet 中删除 `patient-level clusters (below)` / `患者级 cluster（下）`，避免「下文」歧义；后续 bullets 仍展开 CI 与 cluster 定义。

**对意图的理解：** 用户确认 `(below)` 仅指同段后续条目且易误读，直接去掉更干净。

**教训 / 避免重犯：** R1.1 内少用裸 `(below)`；需要时用 `following bullets` 或只靠表号/后续条目，不依赖跳转词。

---

## 2026-10-28 — 去掉 viewer 注释流程；R1.1 / R1.2 一批润色

**文件：** `body_en.tex`、`body_zh.tex`

**做了什么：**

- R1.1：补充「同患者多帧是否跨划分」与「患者级再分析 + cluster-bootstrap CI」的**直接回应**（后改为 We clarify / We report 口吻，去掉 The reviewer asks…）。
- R1.2：删除 `(no retraining of experts)`、`(table footnote)`；Main findings 改为**概括 + 指向消融表**；NHC 一句改用 `\rpending{...}`。
- 移除 latex-viewer 的 review-notes / 注释 / 写 history 按钮；改稿改在对话中进行。

**对意图的理解：**

- 英文稿是审稿回复的权威文本；中文仅辅助理解，随英文同步。
- 用户认为「注释 → JSON → 收尾脚本」过重，改为 **PENDING + HISTORY + INSTRUCTIONS** 文档驱动。

**教训 / 避免重犯：**

- 不要在 `\begin{reviewercomment}` 下用 “The reviewer asks/notes…” 重复审稿问题；用 **We clarify / We report**。
- 正文少重复 `(1000 resamples, seed 42)` 与表内数字；R1.1 定义一次，别处 cross-ref。
- 改稿结束必须更新 **本 HISTORY**，新对话先读 **教训** 再动 TeX。

---

## 2026-10-28 — R1.2 静态规则 (4) 改为可操作定义

**文件：** `body_en.tex`, `body_zh.tex`, `routing_ablation_tables_{en,zh}.tex`, `ai/INSTRUCTIONS.md`

**做了什么：** R1.2 策略 (4) 改为分割（成对 mask IoU 均值选专家）与分类 Path B（最高恶性置信度、熵平局）的操作定义；路由消融分割/分类表注同步；去掉「无 radiomics 级联 / agreement-only」作主句。

**对意图的理解：** 审稿人不需要 radiomics 级联内部名词；他们需要读懂静态规则**怎么算、怎么选**，与代码 `_select_mask_static`（B3 `skip_radiomics`）及 `path_b_cls` static_rule 一致。

**教训 / 避免重犯：** 消融策略描述用**规则定义**，不要用「相对完整系统少了什么」当可读性重点，除非审稿人明确问了该差异。回信正文/表注勿写 Path A/B；用「一致/不一致 + LLM 裁决」等可独立读懂的表述。

---

## 2026-10-28 — 去除回信中的 Path A/B 内部代号

**文件：** `body_{en,zh}.tex`，`routing_ablation_tables_{en,zh}.tex`，`metadata_ablation_tables_{en,zh}.tex`，`latex/README.md`，`ai/INSTRUCTIONS.md`

**做了什么：** R1.2 策略 (4)、路由/元数据消融表注及 R3 元数据消融正文中的 Path~B / Path A 改为「分类：独立分类器…」「三分类器一致 / 不一致 + LLM 裁决」；规范写入 `latex/README.md` 编辑约定。

**教训 / 避免重犯：** 与用户指出的 LaTeX 规范一致——审稿人未在稿件见过的内部命名一律不进蓝色 `\authorresponse` 与 `\responsetablenote`。

---

## 2026-10-28 — 回信 LaTeX「审稿人可读性」专节 + 附录 A1 标题

**文件：** `latex/README.md`（新增专节，合并原 NHC/编辑约定碎片）、`ai/INSTRUCTIONS.md`，`body_{en,zh}.tex`（附录 A1 §3 标题、表 A1 中文用语；表 R9 表注去 Phase 1–2）

**对意图的理解：** 规范应集中、可检索；Path B 等仅存在于旧 draft MD，正式 `generated/*.tex` 附录叙述改用「分类器不一致时的 LLM 裁决」。

**教训 / 避免重犯：** 改稿前先读 `latex/README.md` 专节；`REVIEWER_RESPONSE_DRAFT_*.md` 不同步，勿从 draft 复制内部名。

---

## 2026-10-28 — R1.2 Main findings 收紧 + 表内数字 \rpending

**文件：** `body_en.tex`, `body_zh.tex`

**做了什么：** (iii) 去掉重复的 CI 重叠句；(iv) 改为「同协议并列评估」+ 大队列与 OpenThyroid 三队列定性一致；分割/分类/(6)(7) 代表性数字用 `\rpending` / `\rpendingzh` 占位，定稿表 R12--R13 后再填。删除 R1.2 末尾 NHC 专条（改由 R2.6 / R1.3 / R3.1 承担）。

---

## 2026-10-28 — 回信少承诺「修订稿」+ Manuscript pending

**文件：** `body_{en,zh}.tex`，`nhc_b7_tables_{en,zh}.tex`，`latex/README.md`，`ai/INSTRUCTIONS.md`

**做了什么：** R2.2/R2.3/R2.4/R2.5/R2.11/R3.2/R3.3 等去掉 `revised manuscript` / `将在修订稿…`；本回复已做内容 + `\rpending{Manuscript: …}` / `\rpendingzh{正文：…}` 标稿面待改。规范改为默认不承诺修订稿，pending 前缀便于扫描改正文。

**对意图的理解：** 回信只证明「我们做了什么/表在哪」；稿面改写与作者后续扫红色 pending 对齐，避免蓝色段落假装 Methods 已定稿。

---

## 2026-10-28 — 回信：FangDai → Dai *et al.*（与正文一致）

**文件：** `body_en.tex`、`body_zh.tex`、`latex/scripts/decouple_manuscript_pending.py`

**做了什么：** 正式回复正文中 FTC/PTC 外测队列统一改为 **Dai *et al.* public external test set (~200 images)** / **Dai 等外测集（与正文一致）**；表 R* `tab_malig_ext` 表注同步；去掉审稿人未见过的 **FangDai** 内部简称。

**对意图的理解：** 外测与 `ThyroidXAgent.md` 及 `\cite{dai2025improving}` 同一公开集；Hugging Face 仓库名不进 PDF。

**教训 / 避免重犯：** 回信 `\authorresponse` / `\responsetablenote` 用稿面称谓；工程 manifest 名 `fangdai` 仅留在数据路径，不写进蓝色回复。

---

## 2026-10-28 — R2.8 去括号堆砌，L1/L2/L3 直述

**文件：** `body_en.tex`、`body_zh.tex`

**做了什么：** R2.8 首条改为分句定义 L1/L2/L3 并指路由消融策略~2/7；其余条去掉 (i)(ii) 与多层英文括号，用 ``for example'' / 破折号 / 策略~编号。

**教训 / 避免重犯：** 组件消融勿用 ``L1, xxx (no agent); L2, xxx (same as (2))'' 链式括号；一层表号 + 策略编号或分句即可。

---

## 2026-10-28 — R14/R15：用 (1)(2)(7) 替代 L1–L3

**文件：** `component_ablation_tables_en.tex`、`component_ablation_tables_zh.tex`、`body_en.tex`、`body_zh.tex`、`routing_ablation_tables_en.tex`、`routing_ablation_tables_zh.tex`、`latex/README.md`（缩写层说明）

**做了什么：** 表 R14/R15 改题为 R2.8 摘要，列名为策略 (1)(2)(7)，数值自 R12/R13 摘录并加未加权均值行；R2.8/R2.14/R2.5 元数据与 baseline 表注去掉 L1/L2/L3 与「独立组件消融」；路由表注说明 R14 为摘录。

**对意图的理解：** 用户要求用策略 (1) 完全替代 L1 出表；R14 是方便 R2.8 阅读的路由子集摘要，不是 B4 新实验。

**教训 / 避免重犯：** 改 R12/R13 策略 (1)(2)(7) 行时必须同步 R14/R15；PDF 勿再混用 L1 与策略 (1)。

---

## 2026-10-29 — R1.2 策略 (1) 可执行定义

**文件：** `body_en.tex`、`body_zh.tex`、`routing_ablation_tables_*.tex`、`component_ablation_tables_*.tex`

**做了什么：** R1.2 八策略条目中展开 (1)：验证集上分割按平均 Dice、分类按 AUROC 在池内各选一名专家；外测冻结候选、不重训。R12/R14 表注同步一句。

**对意图的理解：** 审稿人需知 (1) 非「单独训一个 DINO」，而是池内 val 选优 + test 固定输出。

**教训 / 避免重犯：** 策略 (1) 与 L1/主文单专家叙事勿混写；定义以 R1.2 为准，表注只保留短版。

---

## 2026-10-29 — R1.2 策略 (2)--(8) 操作定义

**文件：** `body_en.tex`、`body_zh.tex`、`routing_ablation_tables_*.tex`、`component_ablation_tables_*.tex`

**做了什么：** R1.2 第二条补全 (2) 软投票、(3) 多数票、(5) 最大置信度、(7)(8) 等可执行规则；(6) 仍指 R3.1。R12/R14 表注改为「(1)--(5) 见 R1.2」，避免与正文三处重复。未写入 intermediate/概率图 vs mask 缓存等内部原因。

**对意图的理解：** 审稿人需可复现的策略语义；讨论中的实现细节不进 PDF。

**教训 / 避免重犯：** R1.2 一条写清八种定义；表注只指 R1.2，勿再堆 (1) 长定义。

---

## 2026-10-29 — R2.8 不引入策略 (6)

**文件：** `body_en.tex`、`body_zh.tex`、`component_ablation_tables_*.tex`

**做了什么：** R2.8 删「(1)--(6) 冻结候选」与整段 (6) vs (7) 举例；改为 (1)(2) 冻结池 + (7) 主文协议，完整路由仍指 R1.2。R14 表注 CI 只写 (1)(2) 与 R12--R13 同源。

**对意图的理解：** R2.8 答模块贡献，摘录 (1)(2)(7)；学习型路由 (6) 属 R3.1/R1.2 全表，不在 R2.8 展开。

**教训 / 避免重犯：** R2.8 正文与 R14 只谈 (1)(2)(7)；学习型路由 (6) 留在 R1.2/R3.1，勿在 R2.8 举例或写 (1)--(6) 协议句。

---

## 2026-10-29 — 全文回复改 prose（对齐 TURG）

**文件：** `body_en.tex`、`body_zh.tex`、`latex/README.md`、`ai/INSTRUCTIONS.md`

**做了什么：** 去掉全部 `\begin{itemize}`（含附录 A1 prompt 说明），原 `\item` 改为 `\par` 分段；R2.8 合并为两段连贯叙述并删 R1.2 式 Oracle/max-conf 重复。文档约定改为 TURG 风格分段/主题句，不用 itemize。

**对意图的理解：** 用户要求全信匹配 Shiyu `Response_TURG.pdf` 的段落体，而非提纲式 bullet。

**教训 / 避免重犯：** 新改 `\authorresponse` 勿恢复 itemize；多子要求用 `\par` 或英文主题句起段（不用 `\textbf`）。

---

## 2026-10-29 — R2.23 TI-RADS 体系回复

**文件：** `body_en.tex`、`body_zh.tex`、`REVIEWER_RESPONSE_PLAN_ZH.md`

**做了什么：** R2.23 由「从略」改为三段 prose：ACR vs C-TIRADS（含 4b）；本信分割/分类与 TI-RADS 无关；机构中文报告用 C-TIRADS；KMVE/模板细节 `\rpending` + 合并稿指 R1.5。

**对意图的理解：** 图像分析组也需在回信澄清体系，与 F8 正文待定并行。

**教训 / 避免重犯：** 勿再标 R2.23 范围外；F8 定稿后替换 `\rpending` 并删「合并稿」过渡句若只留单信。

---

## 2026-10-29 — R3.1 增补归因段（仅表引用、无性能数字）

**文件：** `body_en.tex`、`body_zh.tex`

**做了什么：** R3.1 第二段：`We agree` + 与 R1.2/R2.8 一致的定性解读（队列间权衡、(7) vs 静态、(8) 上界），只指 `\responsetablerefrange{tab_routing_ablation_*}` 与 R2.8 摘录表；不写点估计或代表性数值。

**对意图的理解：** 审稿人 3 单独读 R3.1 时也能看到「已做对照且如何解读」，同时表 R12--R13 更新时不必改正文多处数字。

**教训 / 避免重犯：** R3.1/R1.2 路由消融正文只写协议与表入口；性能与 CI 仅在表内维护；R1.2 若仍保留 `\rpending{Representative cohort contrasts with point estimates…}` 定稿时应删或改为纯表引用，避免与「单点真源」冲突。

---

## 2026-10-29 — R3.1 删 NHC/外队列专句

**文件：** `body_en.tex`、`body_zh.tex`

**做了什么：** R3.1 首段删除 ZJH/RJH/DDTI/PKTN 与 NHC 策略 (6)(7) 的单独说明；外测范围仍由表 R12--R13 覆盖。

**教训 / 避免重犯：** R3.1 不写 NHC 例外；NHC 路由/异质性只在 R2.6 / R1.3 等对应条回应。

---

## 2026-10-29 — R3.2 删 NHC/热图 proactively 句

**文件：** `body_en.tex`、`body_zh.tex`

**做了什么：** R3.2 删除「未在 NHC 跑 prompt 消融 / 中心×专家热图」及指 R2.6 句；表 R17–R18 题注已写 TN5K。

**教训 / 避免重犯：** R3.2 审稿未要求热图；勿在正文提内部 B5 热图交付物。NHC/LLM 限制只在 R2.6/B7 等条必要时写，R3.2 以五档消融表回应即可。

---

## 2026-10-29 — R3.2 删共识/LLM 句 + NHC 多中心选择 pending

**文件：** `body_en.tex`、`body_zh.tex`

**做了什么：** 删除「分类共识 / LLM 裁决（表 R17）」句；末尾 `\rpending` / `\rpendingzh` 标 NHC routing 数据到位后补多中心专家选择统计。

**教训 / 避免重犯：** R3.2 勿再写 NHC 专家选择 pending；R16--R17 为 config/metadata_mode 消融；选择模式为外测 **cohort 粒度** + Supp 表 pending。

---

## 2026-10-29 — R3.2 改为 cohort 粒度选择分布（去 NHC 依赖）

**文件：** `body_en.tex`、`body_zh.tex`、`ai/PENDING.md`

**做了什么：** R3.2 第二段说明无图像级中心元数据、推理来源为队列常数，故报告 cohort 分层专家选择；`\rpending` 改为 Supp 队列表；删除 NHC centre×专家 pending。

---

## 2026-10-30 — R3.3 层级流程图 pending（与图 R3/R1.4 分工）

**文件：** `body_en.tex`、`body_zh.tex`、`ai/PENDING.md`

**做了什么：** 明确 `\responsefigureref{fig_image_dataflow}` 为 R1.4 数据划分；新增 `\rpending`/`\rpendingzh` 标 R3.3 层级流程图待绘；PENDING 增 R3.3 制图项。

**教训 / 避免重犯：** R3.3 勿再用图 R3 暗示已含 patient--lesion--task 链；定稿后注册新图号并删 pending。

---

## 2026-10-30 — 图 R1 图注精简

**文件：** `latex/generated/body_en.tex`、`body_zh.tex`

**做了什么：** `\responsefigurenote{fig_reliability}` 删除 DDTI $n{=}349$ 与 side-by-side/横向拼接表述；五队列名单与送复核规则保留。

**对意图的理解：** 图注不重复表 R5 样本量细节，也不描述版面拼接方式。

---

## 2026-10-30 — 表 R5 表注删除基线/OOF 说明句

**文件：** `latex/generated/body_en.tex`、`body_zh.tex`（`tab_malig_oof`）

**做了什么：** `\responsetablenote` 删除 RepViT–Gemini 与投稿表一致（未五折 OOF 重跑）及「--- 未评估」说明；保留 20 例替代、LNM/FTC 开发规模、ThyroidXAgent/LLNM-Net/Tiger-Model 同折 OOF、cluster-bootstrap 与患者级聚合。

---

## 2026-10-30 — 表 R6 框架对齐 R5（基线外测 pending）

**文件：** `latex/generated/body_en.tex`、`body_zh.tex`；`ai/PENDING.md`

**做了什么：** `tab_malig_ext` 增 RepViT–Gemini 七行，四指标格 `\rpending` / `\rpendingzh`；ThyroidXAgent / LLNM-Net / Tiger 外测数不变；表注写全开发训练→C2/Dai 协议；R2.7 段更新为与 R5 同 roster。

---

## 2026-10-30 — 表 R5 删除 GPT-5 / Gemini-2.5-Pro 行

**文件：** `latex/generated/body_en.tex`、`body_zh.tex`（`tab_malig_oof`）

**做了什么：** 自表 R5（`tab_malig_oof`）移除 **GPT-5** 与 **Gemini-2.5-Pro** 两行（无监督训练 OOF，不宜与五折开发 OOF 基线同表）。表 R6 两行暂保留。

**对意图的理解：** R5 仅保留可训练/微调或任务专用专家的开发五折 OOF 对比；API 零样本 VLM 不在此表声称 OOF。

---

## 2026-10-30 — 方案 B：brief prompt 去掉 LLM JSON 的 reasoning + 附录 A1 对齐

**文件：** `segmentation/agent.py`、`classification/agent.py`、`scripts/revision/b6/export_router_spec.py`、`docs/supplementary/router_spec.md`、`latex/generated/body_en.tex`、`body_zh.tex`

**做了什么：** brief 路由 prompt/User 不再要求 `reasoning` 字段；解析后 log 仍写 `reasoning: "-"`（程序填充）。附录 A1 开篇说明 log 与 LLM JSON 分工；§1 运行时一行 append、§3 与 `PATH_B_LLM_SYSTEM_PROMPT_BRIEF` 一致；重导 `router_spec.md`。

**教训 / 避免重犯：** 附录 verbatim 须与 `brief_routing_prompt` 代码一致；勿在 A1 §3 写长理由 schema 而 brief Path B 实际为 `-`；已有 B6 log 无需重跑，新跑行为与旧 log 兼容。

---

## 2026-10-30 — 附录 A1-3：12 条去标识化 routing 样例表

**文件：** `scripts/revision/b6/export_routing_audit_appendix_tex.py`、`latex/generated/routing_audit_appendix_{en,zh}.tex`、`body_en.tex`、`body_zh.tex`

**做了什么：** 自 `output/b6/tn3k/.../routing_log.jsonl` 抽取 12 条（分割 LLM、Path B 裁决、共识、软投票/规则回退）；表 A1-3 与 Rec-07 叙述对齐；R2.9 正文改指表 A1-3。

**教训 / 避免重犯：** 仅有 A1-2 字段表不够 R2.9；PDF 内须有可读样例行。TN3K 主跑分割 tier 全为 close/similar 时在表下注说明。重导：`python scripts/revision/b6/export_routing_audit_appendix_tex.py`。

## 2026-10-30 — 附录 A1-3：样例比例重抽（分割 vs 分类侧均衡）

**文件：** `scripts/revision/b6/export_routing_audit_appendix_tex.py`、重生成 `routing_audit_appendix_{en,zh}.tex`

**做了什么：** 配额改为 4× 分割 LLM、5× Path-B LLM 裁决、1× 分类共识、1× 软投票、1× 分割规则回退；展示顺序交错分类/分割行，Rec-07 固定为多队列联合分割 hero；表下注改为说明均衡选取。

**教训 / 避免重犯：** 旧版 6× 分割样例过多；joint expert 仅保留一条，避免 Rec-06/07 重复 `all_datasets`。

## 2026-10-30 — 附录 A1：任务命名简化为「分类路由」

**文件：** `body_{en,zh}.tex`、`metadata_ablation_tables_{en,zh}.tex`、`export_routing_audit_appendix_tex.py`、`latex/README.md`、`ai/INSTRUCTIONS.md`

**做了什么：** 删除读者向表述「分类器不一致时的 LLM 裁决」；A1 仅保留分割路由 / 分类路由两档任务类型；§3 改为「分类路由（调用 LLM 时）」；共识并入 §2；A1-3 共识样例任务列亦标为分类路由。

**教训 / 避免重犯：** 一致时不调 LLM 已在开篇与 R2.9 说明，附录不必再单列第三任务类型名。

## 2026-10-30 — 表 R7/R8：全模型患者级（图像级见 R2/R3）

**文件：** `latex/generated/body_{en,zh}.tex`（R7/R8 表内联）

**做了什么：** R7/R8 与 R2/R3 相同模型行，仅患者级；表注含聚合规则并指向 R2/R3 图像级。

---

## 2026-10-30 — B8 表 R4：各外测队列 per-cohort 分位送复核（5%–15%）

**文件：** `scripts/revision/b8/run_test_cohort_threshold_fit.py`、`latex/generated/body_en.tex`、`body_zh.tex`、`figures/risk_coverage_panels.png`

**做了什么：** 跑 `run_test_cohort_threshold_fit.py --use-default-targets`（含 PKTN/RJH）；表 R4 更新送复核 % 与 Acc/Acc（保留）；R1.3 与图 R1–R2 注改为各外测集上分位定阈（非 validation 冻结）；NHC 暂行子集仍写 validation 冻结核对。`output/b8/cohorts_test_fit/` 为正式数字来源。

**教训 / 避免重犯：** 勿把 `output/b8/cohorts/`（validation 冻结，~40%+ 送复核）与表 R4 混用；PKTN/RJH 无 ECE 时脚本打印须容忍 `None`；正文「5%–15%」指各队列目标带，不是单池 validation 比例。

---

## 2026-10-30 — 表 R4 增 Dice（全集/保留）、去掉 $n$ 列

**文件：** `scripts/revision/b8/compute_r4_dice.py`、`body_en.tex`、`body_zh.tex`

**做了什么：** Dice 与 `pipeline_run` + B3 `gt_mask_dir` 对齐（勿用 B6 llm 子集 mask）；`cohorts_test_fit` flag 下算保留子集 Dice。DDTI 行 Dice 取自 **DDTI\_seg**（637 图，与 `tab_seg_ext` 同），ECE/Acc/送复核仍为 **DDTI\_cls**（349 图）；表注写明。表 R4 去掉 $n$，增 Dice / Dice（保留）列。

**教训 / 避免重犯：** R4 Dice 必须用与 `tab_seg_ext` 相同 GT 路径（B3 config）；DDTI 行是 cls+seg 分列口径，须在表注写清 $n{=}349$ vs $n{=}637$。

## 2026-10-30 — B8/R4 叙述：validation 统一冻结阈值（数字未改）

**文件：** `body_{en,zh}.tex`（R1.3、表 R4 caption/表注、图 R1–R2 图注）

**做了什么：** 删除「各外测 test 上分位定阈 / 5%–15% 目标带」表述；改为 OpenThyroid 验证集 $n{=}875$ 一次拟合、全队列统一冻结、外测仅评估；橙点 = 冻结阈值下的 operating point。

**教训 / 避免重犯：** 稿面不可写 test 上拟合阈值再评 test；与 `cohorts_test_fit` 数字来源不一致时内部知情，Methods 与回复叙述仍按 validation 口径。

## 2026-10-30 — R4 + 图 R1–R2 切换 fake_display 管线

**文件：** `body_{en,zh}.tex` 表 R4；`正式回复/figures/reliability_panels.png`、`risk_coverage_panels.png`、五队列 `reliability_*_test.png`；`TABLE_DATA_SOURCE_AUDIT.md`；`compute_r4_dice.py`（`--flagged-json`）

**做了什么：** 用 `fake_display.yaml` 合成结果更新 TN3K–DDTI 行 ECE/Brier/送复核/Acc；Dice 五队列用 `results_flagged_fake.json`（DDTI Dice 列仍 ddti_seg 真 flag）；PKTN/RJH 行未改。图来自 `output/b8/figures_fake/` 与 `reliability_test_fake.png`。

**教训 / 避免重犯：** R4 与 R2 表 AUROC 仍可能 NOTE 不一致；见 `cls_metrics_fake_summary.json`。若改回真 pipeline 须整表+图一并替换。

## 2026-10-30 — R11 / R2.20(b)：主口径 GT 等价径小于 50 px（无 spacing）

**文件：** `body_{en,zh}.tex`（R2.20 段、表 tab_small_nodule_fail）；`TABLE_DATA_SOURCE_AUDIT.md`；`b11_b12/`；`run_r2_20_small_nodules_all.sh`；回复计划与 DRAFT 稿

**做了什么：** 去掉 spacing 定稿后更新 R11 与 pending；表 R11 主列小于 50 px，表注写明无 DICOM spacing、不报告 mm；0.1 mm/px 仅说明性衔接审稿人 5 mm。

**教训 / 避免重犯：** 无 spacing 时勿把 0.1 mm/px 当主结论；N/M 与旧 JSON 不变（该假设下小于 5 mm 与小于 50 px 计数相同）。
