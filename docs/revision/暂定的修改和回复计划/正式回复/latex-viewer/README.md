# 审稿回复 LaTeX 预览（内网）

**以 TeX 为唯一编辑源**：直接改 `../latex/` 下的文件，用 XeLaTeX 编译并在浏览器中切换中英文 PDF。

## 编辑哪里

| 文件 | 作用 |
|------|------|
| `../latex/generated/body_en.tex` | 英文回复正文 |
| `../latex/generated/body_zh.tex` | 中文回复正文 |
| `../latex/REVIEWER_RESPONSE_EN.tex` | 英文导言区、`\input`、标题 |
| `../latex/REVIEWER_RESPONSE_ZH.tex` | 中文导言区 |
| `../latex/reviewer_response.sty` | 版式、表格环境、图表路径 |

上级目录中的 `REVIEWER_RESPONSE_DRAFT_*.md` 仅作历史备份；**预览服务不会读取或覆盖 TeX**。

## 依赖

- Python 3 + Flask
- `xelatex`（`texlive-xetex`、`texlive-latex-extra`；中文另需 `texlive-lang-chinese` 或文泉驿字体）

## 用法

```bash
# 启动内网预览（默认 http://0.0.0.0:8765）
python3 app.py

# 自定义端口、关闭自动监视
python3 app.py --port 8888 --no-watch
```

浏览器工作区：

- 左侧：`latex/` 文件树（按 English / 中文 / 共用分组）
- 中间：TeX 编辑器，**保存** 写回磁盘（Ctrl+S）
- 右侧：PDF 预览（无页缩略图侧栏），可切换 **EN / ZH**，或点 **对照** 左右并排看中英文

保存 TeX 后约每 3 秒自动重编 EN/ZH 两份 PDF，也可点「编译」。改稿与审稿讨论请在 Cursor 对话中进行。

## 手动编译（不用网页）

```bash
cd ../latex
xelatex -interaction=nonstopmode REVIEWER_RESPONSE_EN.tex
xelatex -interaction=nonstopmode REVIEWER_RESPONSE_ZH.tex
# 需要更新目录时再各跑一遍
```

正文与表图请在 `../latex/generated/` 内直接编辑 TeX；本预览器只编译现有源文件。
