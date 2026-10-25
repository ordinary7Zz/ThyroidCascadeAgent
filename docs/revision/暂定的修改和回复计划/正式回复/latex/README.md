# 审稿回复 LaTeX（正式编辑源）

请在此目录维护回复信，**不要**再通过 `REVIEWER_RESPONSE_DRAFT_*.md` 同步。

- **正文**：`generated/body_en.tex`、`generated/body_zh.tex`
- **壳文件**：`REVIEWER_RESPONSE_EN.tex`、`REVIEWER_RESPONSE_ZH.tex`
- **样式**：`reviewer_response.sty`
- **图片**：上级 `figures/`（由 `\graphicspath` 引用）

版式（参考 Response_TURG）：信头 `\responselettertitle` + `\responseletteropening` / `openingzh`（已说明表图复现于信末）；审稿意见黑色斜体、回复 `ResponseBlue`；按审稿人插入 `\responsetoreviewer{…}`；无目录、无 `\hrule` 分节。正文引用支撑表图时直接写 **Table R7** / **表 R7**，勿重复 “at the end of this letter” / “见文末”。`authorresponse` 内尽量少用 `\textbf`（整段已是蓝色）；蓝色回复内仅保留「支撑材料：」/ **Supporting material:** 加粗；表图编号（如 Table R8、表 R8（续））用普通蓝字。批量去粗体：`scripts/soften_response_bold.py`。定稿前占位：`\rpendingzh{…}` / `\rpending{…}`（红色 `[待补充：…]` / `[PENDING: …]`，提交前删除或替换）；信头 opening 已说明。性能表（R2/R4/R8）数据格加粗 = **该指标块内该列点估计最优**（Dice/AUROC/AUPRC ↑，HD95 ↓）；校验：`python3 scripts/audit_response_table_bold.py`。

图表：`responsetable` / `responsefigure` 使用 `[H]` 按源顺序排版；附录 A1/A2 前 `\responseproseappendixstart`；A1 解码参数表用 `responseinlinetable`。与投稿稿 **Supplementary Tables S3–S5** 对齐的复现表用 `manuscriptresponsetable`（版式见 `docs/ThyroidXAgent.md` 中 `tab:seg_performance` / `tab:cls_performance` / S5：单表内 AUROC/AUPRC 或 Dice/HD95 分节、$\pm$ 半宽 CI、ThyroidXAgent 灰底行）。Prompt 块 `promptverbatim` 经 `fvextra` 启用 `breaklines=true`，避免长行溢出边框。脚本：`scripts/patch_manuscript_table_format.py`、`scripts/turgify_body_tex.py`、`scripts/add_response_captions.py`。

B3 路由消融回复表（**表 R14–R15**：分割 + 分类）由指标 JSON 生成后 `\input` 进 `body_*.tex`：

```bash
python scripts/revision/b3/export_b3_response_letter_tables.py
```

预览与自动编译：

```bash
cd ../latex-viewer && python3 app.py
```
