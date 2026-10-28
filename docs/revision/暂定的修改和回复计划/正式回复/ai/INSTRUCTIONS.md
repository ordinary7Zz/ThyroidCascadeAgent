# 给 AI：审稿回复改稿说明（新对话请先读）

用户在新窗口会 @ 本文件，有时一并 @ `PENDING.md`。**没有聊天上下文时，以本目录文档为准。**

## 1. 改哪些文件

| 优先级 | 路径 | 说明 |
|--------|------|------|
| 主 | `latex/generated/body_en.tex` | 英文回复正文（**打磨细节的主战场**） |
| 同步 | `latex/generated/body_zh.tex` | 中文：与英文**语义对齐**的意译，不单独抠字字面 |
| 按需 | `latex/generated/*.tex` 表图片段 | 仅当 `PENDING.md` 或用户明确要求 |
| 少动 | `latex/REVIEWER_RESPONSE_*.tex`、`reviewer_response.sty` | 除非用户点名 |

编译入口：`latex/REVIEWER_RESPONSE_EN.tex` / `_ZH.tex`（viewer 或 `xelatex`）。

## 2. 固定写作与分工（必须遵守）

- **逐条明确回应（必守）**：对照 `\begin{reviewercomment}` 的**每一要求**写清：We agree / We report / We performed… + **表/图/附录**入口。禁止 METHOD-only bullet（只讲定义、不指 `\responsetableref`、不说是否已做）。审稿人列 (a)(b)(c) 时回复须**逐条对应**；做不到处 `\rpending` 并说明限制。改稿后自检：「删掉表号后这条还能否证明我们回应了？」——若不能，补一句「已…见…」。
- **只根据英文需求改稿**：用户不在中文稿上单独提修改意见；你改完 EN 后**同步更新 ZH** 对应段落。
- **回复信语气**：上面已有 `\begin{reviewercomment}` 时，作者回复用 **We clarify / We report / We agree** 等直接陈述，**避免** “The reviewer asks… / The reviewer notes…” 式元叙述。
- **数字与表**：正文避免堆过多与表耦合的数字例；细节放在 `\responsetableref{...}` 的表里。`PENDING.md` 若要求概括性 Main findings，遵守之。
- **待定内容**：用 `\rpending{...}`（英文）、`\rpendingzh{...}`（中文），与 `reviewer_response.sty` 一致。
- **少提修订稿（必守）**：勿写「将在修订稿 Methods…」；直接陈述已做分析与表图入口，**不要**在条目标题后加 `(this letter)` / `（本回复）` 等括号。必须在投稿正文改写的处，用 `\rpending{Manuscript: …}` / `\rpendingzh{正文：…}`（见 `latex/README.md` →「待定与正文修订」）。
- **同一条意见内**：避免 `below` / `as detailed below` /「如下」「见下条」等**段内跳转**（itemize 已按条展开；用 `\responsetableref` / `\responsefigureref` 或直接写内容即可）。**勿**在蓝色正文写「表注/图注/table note」——只引用表/图号（见 `latex/README.md`）。跨意见交叉引用（如 R2.2）可以保留。
- **Cluster-bootstrap CI**：**仅 R2.2** 写全 resampling 协议（含 1000、seed~42）。其它意见正文只写 **follow R2.2** + 表号即可，**不要**再写 table captions/notes 或重复参数；各表 `\responsetablenote` 仍可保留 1000/seed 供单独读表。
- **路由消融策略 (1)--(8)**：向审稿人写**可执行规则**（如何算分歧、如何选 mask/分类器），勿以「不含 radiomics 级联 / agreement-only」等内部实现细节作主句；完整系统与消融的差异放在 Methods/附录，不在 R1.2 用级联名词当对比重点。
- **审稿人可读性（必守）**：全文 PDF 叙述遵守 `latex/README.md` 专节「审稿人可读性：禁止内部/机器命名」——不写 Path A/B、Phase、路径/脚本/函数名、日志文件名等；附录 A1 小标题用自然语言（如「分类器不一致时的 LLM 裁决」）。
- **不要**恢复已删除的 latex-viewer「注释 / current.json / history.jsonl」流程。

## 3. 每次改稿前

1. 读 **`HISTORY.md` 末尾「教训 / 避免重犯」**（若有），避免重复错误。
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

> 请先读 @正式回复/ai/INSTRUCTIONS.md 和 @正式回复/ai/PENDING.md，按 PENDING 改英文并同步中文，改完后更新 @正式回复/ai/HISTORY.md。

## 6. 用户维护 `PENDING.md`

用户在 Cursor 对话里讨论后，把**仍待执行的修改**写进 `PENDING.md`（条目清晰即可，不必 JSON）。不在 viewer 里做注释。
