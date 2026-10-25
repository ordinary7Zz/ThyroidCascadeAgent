# 审稿回复 LaTeX（正式编辑源）

请在此目录维护回复信，**不要**再通过 `REVIEWER_RESPONSE_DRAFT_*.md` 同步。

- **正文**：`generated/body_en.tex`、`generated/body_zh.tex`
- **壳文件**：`REVIEWER_RESPONSE_EN.tex`、`REVIEWER_RESPONSE_ZH.tex`
- **样式**：`reviewer_response.sty`
- **图片**：上级 `figures/`（由 `\graphicspath` 引用）

版式（参考 Response_TURG）：信头 `\responselettertitle` + `\responseletteropening` / `openingzh`；审稿意见黑色斜体、回复 `ResponseBlue`；按审稿人插入 `\responsetoreviewer{…}`；无目录、无 `\hrule` 分节。

图表：`responsetable` + `\caption{表 R1. …}` + `\responsetablenote{…}`（英文 *Note.* / 中文 *表注.*）；图 `responsefigure`。脚本：`scripts/turgify_body_tex.py`（正文结构）、`scripts/add_response_captions.py`（表题注）。

预览与自动编译：

```bash
cd ../latex-viewer && python3 app.py
```
