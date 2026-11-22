# 给 AI：审稿回复改稿说明（新对话请先读）

用户在新窗口会 @ 本文件，有时一并 @ `PENDING.md`。**没有聊天上下文时，以本目录文档为准。**

## 1. 改哪些文件

**真源：两个 Overleaf 工程**（`latex-viewer` 只编译这两棵目录，见 `../latex-viewer/README.md`）

| 工程 | 路径 | 说明 |
|------|------|------|
| **回信（完整）** | `response_letter/` | 编译 `main.tex` → `main.pdf`；正文 `\input{generated/body_en_merged.tex}` + `report_side` 合并稿 |
| **主稿** | `26_Nature_ThyroidAgent/` | 编译 `main_v2.tex` → `main_v2.pdf` |

| 优先级 | 路径 | 说明 |
|--------|------|------|
| 主 | `response_letter/generated/body_en_merged.tex` | 合并后的英文回复正文 |
| 按需 | `response_letter/generated/*.tex` | 表图、附录片段；**手改 tex 为真源** |
| 导言/样式 | `response_letter/main.tex`、`reviewer_response.sty`、`report_side.sty` | 除非用户点名 |
| 可选草稿 | `latex/generated/body_en.tex` | **非 viewer 编译源**；若仍在此分段改稿，须自行合并进 `body_en_merged.tex` |

- **不再维护中文回信**（无 `body_zh`、不同步 ZH）。
- 编译：回信 `pdflatex`（`main.tex`）；主稿 `xelatex` + `bibtex`。

## 2b. LaTeX 真源 vs 脚本（必守）

- **直接改 TeX**：`response_letter/generated/*.tex`；表数字、表题、表注、`\rpending` 均在 tex 维护。
- **勿依赖 py 改 generated**：表数字与表注在 `generated/*_tables_*.tex` 手改维护。

## 2. 固定写作与分工（必须遵守）

- **Nature 子刊语气（必守）**：详见 **[WRITING_STYLE.md](./WRITING_STYLE.md)**——直接陈述 + 表图引用；禁止「以表为准/不对齐/占位/定稿后替换」等 meta；避免 `\textbf{小标题。}` 清单体；正文不堆表内数字、不向审稿人解释编辑策略。
- **逐条明确回应（必守）**：对照 `\begin{reviewercomment}` 的**每一要求**写清：We agree / We report / We performed… + **表/图/附录**入口。禁止 METHOD-only 段落（只讲定义、不指 `\responsetableref`、不说是否已做）。审稿人列 (a)(b)(c) 时须**逐条覆盖**，优先用**连贯段落**（因果、先协议后证据、先定义后表）串联，避免去掉 `itemize` 后仍像互无关的并列块；做不到处 `\rpending` 并说明限制。改稿后自检：「删掉表号后这条还能否证明我们回应了？」——若不能，补一句「已…见…」。
- **仅英文回信**：用户不要求生成或维护中文稿。
- **回复信语气**：上面已有 `\begin{reviewercomment}` 时，作者回复用 **We clarify / We report / We agree** 等直接陈述，**避免** “The reviewer asks… / The reviewer notes…” 式元叙述。
- **数字与表**：正文避免堆过多与表耦合的数字例；细节放在 `\responsetableref{...}` 的表里。`PENDING.md` 若要求概括性 Main findings，遵守之。
- **待定内容**：用 `\rpending{...}`，与 `reviewer_response.sty` 一致。
- **少提修订稿（必守）**：勿写「将在修订稿 Methods…」；直接陈述已做分析与表图入口，**不要**在条目标题后加 `(this letter)`。必须在投稿正文改写的处，用 `\rpending{Manuscript: …}`。
- **同一条意见内**：避免 `below` / `as detailed below` 等**段内跳转**（用 `\par` 分段 + `\responsetableref` / `\responsefigureref`）。**勿**在蓝色正文写「表注/图注/table note」——只引用表/图号。跨意见交叉引用（如 R2.2）可以保留。
- **Cluster-bootstrap CI**：**仅 R2.2** 写全 resampling 协议（含 1000、seed~42）。其它意见正文只写 **follow R2.2** + `\responsetableref{…}` / `\responsetablerefrange{…}{…}` 即可，**不要**再写 table captions/notes 或重复参数；各表 `\responsetablenote` 仍可保留 1000/seed 供单独读表。
- **路由消融策略 (1)--(8)**：向审稿人写**可执行规则**（如何算分歧、如何选 mask/分类器），勿以「不含 radiomics 级联 / agreement-only」等内部实现细节作主句；完整系统与消融的差异放在 Methods/附录，不在 R1.2 用级联名词当对比重点。
- **审稿人可读性（必守）**：不写 Path A/B、Phase、路径/脚本/函数名、日志文件名等；附录小标题用自然语言（如「分类路由」）。`% [SYNC]` 注释可保留路径供对账。
- **不要**恢复已删除的 latex-viewer「注释 / current.json / history.jsonl」流程。

## 3. 每次改稿前

1. 读 **[WRITING_STYLE.md](./WRITING_STYLE.md)**（改正文语气）与 **`HISTORY.md` 末尾「教训 / 避免重犯」**（若有），避免重复错误。
2. 读 **`PENDING.md`**：逐条处理；处理完在 `PENDING.md` 里勾选或删除已完条目（与用户确认策略：通常 AI 改稿后清空已完成的 pending 项并移到 HISTORY）。
3. 定位：优先 `PENDING` 里的文件与说明；必要时在 `body_en.tex` 内搜索关键词或章节号（R1.1、R1.2…）。

## 4. 每次改稿后（必须做）

在 **`HISTORY.md` 追加一节**（模板见该文件底部），包含：

- 日期与简短标题  
- 改了哪些文件、对应审稿位置  
- 对用户/审稿意图的理解（1–3 句）  
- **教训 / 避免重犯**（格式、语气、与表数字耦合等——供下次新对话读）

**不要**只改 TeX 不写 HISTORY。

## 5. 用户在新对话里怎么说（示例）

> 请先读 @正式回复/ai/INSTRUCTIONS.md、@正式回复/ai/WRITING_STYLE.md 和 @正式回复/ai/PENDING.md，按 PENDING 改 `response_letter/`，改完后更新 @正式回复/ai/HISTORY.md。

## 6. 用户维护 `PENDING.md`

用户在 Cursor 对话里讨论后，把**仍待执行的修改**写进 `PENDING.md`（条目清晰即可，不必 JSON）。不在 viewer 里做注释。
