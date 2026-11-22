# AI 改稿文档（替代原 review-notes）

| 文件 | 谁维护 | 作用 |
|------|--------|------|
| [INSTRUCTIONS.md](./INSTRUCTIONS.md) | 偶尔与用户一起改规则 | 新对话必读：改哪些文件、固定分工、流程 |
| [WRITING_STYLE.md](./WRITING_STYLE.md) | 与用户/AI 增补 | **Nature 子刊回信语气**：禁止 meta 解释、段落衔接、表引用方式 |
| [PENDING.md](./PENDING.md) | **你** | 当前还没做的修改清单 |
| [MANUSCRIPT_REVISION_CHECKLIST.md](./MANUSCRIPT_REVISION_CHECKLIST.md) | **你/AI** | **主稿统稿**勾选项（对应 R2.1/R2.3/R3.3/R2.20；已从回信 red pending 迁出） |
| [HISTORY.md](./HISTORY.md) | **AI 每次改稿后追加** | 改了什么、怎么理解、**避免重犯** |

**工程真源（2026-11-22 起）**

| Overleaf 工程 | 目录 | 编译 |
|---------------|------|------|
| 完整回信 | [`../response_letter/`](../response_letter/) | `main.tex` → `main.pdf` |
| Nature 主稿 | [`../26_Nature_ThyroidAgent/`](../26_Nature_ThyroidAgent/) | `main_v2.tex` → `main_v2.pdf` |

内网预览：[`../latex-viewer/`](../latex-viewer/) 仅编译上述两目录。**不再**生成或维护中文回信。

**写作底线**：每条审稿意见要有**比较明确的回应**——先答「做没做 / 同不同意」，再指 `\responsetableref` 等证据；语气见 **[WRITING_STYLE.md](./WRITING_STYLE.md)**。

**新对话开场：**

@ `ai/INSTRUCTIONS.md` @ `ai/WRITING_STYLE.md` @ `ai/PENDING.md` → 请按 PENDING 改 `response_letter/`，并更新 HISTORY。