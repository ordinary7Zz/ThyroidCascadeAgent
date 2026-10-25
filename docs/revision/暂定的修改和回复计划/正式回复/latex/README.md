# 审稿回复 LaTeX（正式编辑源）

请在此目录维护回复信，**不要**再通过 `REVIEWER_RESPONSE_DRAFT_*.md` 同步。

- **正文**：`generated/body_en.tex`、`generated/body_zh.tex`
- **壳文件**：`REVIEWER_RESPONSE_EN.tex`、`REVIEWER_RESPONSE_ZH.tex`
- **样式**：`reviewer_response.sty`
- **图片**：上级 `figures/`（由 `\graphicspath` 引用）

预览与自动编译：

```bash
cd ../latex-viewer && python3 app.py
```
