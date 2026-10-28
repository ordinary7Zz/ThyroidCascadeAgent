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

```markdown
## YYYY-MM-DD — 简短标题

**文件：**

**做了什么：**

**对意图的理解：**

**教训 / 避免重犯：**

```
