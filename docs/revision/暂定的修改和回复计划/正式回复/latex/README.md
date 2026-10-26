# 审稿回复 LaTeX（正式编辑源）

请在此目录维护回复信；**不要**用 `REVIEWER_RESPONSE_DRAFT_*.md` 与正式稿双向同步。

## 文件结构

| 路径 | 作用 |
|------|------|
| `generated/body_en.tex`、`generated/body_zh.tex` | 逐条回复正文（主要编辑对象） |
| `REVIEWER_RESPONSE_EN.tex`、`REVIEWER_RESPONSE_ZH.tex` | 语言壳（`\input` body + sty） |
| `reviewer_response.sty` | 版式、颜色、表图宏 |
| `generated/response_asset_registry.tex` | 语义键 → 信内编号 R1、R2… |
| `generated/*_tables_*.tex` | 信末支撑表（由 `body_*.tex` 末尾 `\input`） |
| 上级 `figures/` | 图文件（`\graphicspath`） |

内部返修计划与实验划分见 [`../../README.md`](../../README.md)、`docs/revision/`；**本 README 只写回信 LaTeX 编辑规则**。

## 版式要点

- 信头：`\responselettertitle`、`\responseletteropening` / `openingzh`（说明表图复现于信末）。
- 审稿意见：黑色斜体；作者回复：`ResponseBlue`。
- 分节：`\responsetoreviewer{…}`；无目录、无 `\hrule`。
- 正文引用表图：`\responsetableref{键}`、`\responsefigureref{键}`、`\responsetablerefrange{键A}{键B}`；**勿**在蓝色回复里重复 “见文末” / “at the end of this letter”。
- 信内表图编号**仅** R1–R17、图 R1–R2（见 `reviewer_response.sty` 页眉说明）；**不复用**稿件 Supplementary Table S* 序号。
- `authorresponse` 内尽量少用 `\textbf`；仅「支撑材料：」/ **Supporting material:** 加粗。表图编号用普通蓝字。批量弱化粗体：`scripts/soften_response_bold.py`。

## 表图注册与命名

1. 在 `generated/response_asset_registry.tex` 增加一行，例如 `\responsetableregister{tab_example}{R18}`（新增编号时同步改 `reviewer_response.sty` 中 R1–R* 范围说明）。
2. `\label{tab_example}` 与注册键、`\responsetableref{}` 参数**必须相同**（语义 slug，不含数字）。
3. 表题：`\caption{\responsetabletitle{tab_example}{短标题}}`。
4. 续表：`\responsetablesetcontinued{tab_…}`（显示为 R*（续））。
5. 长表分页：`\begin{responsepaginatedtable}…\end{responsepaginatedtable}`；单页浮动表：`\begin{responsetable}…\end{responsetable}`（含 `\centering`）。
6. 与投稿主表版式一致的复现块：`manuscriptresponsetable`（AUROC/AUPRC 或 Dice/HD95 分节、± 半宽 CI、灰底 ThyroidXAgent 行，见 `docs/ThyroidXAgent.md` 表标签）。
7. 附录 A1/A2 前：`\responseproseappendixstart`；附录内小表：`responseinlinetable`。Prompt：`promptverbatim`（`breaklines=true`）。

## 待定与修订稿承诺

- `\rpendingzh{…}` / `\rpending{…}`：红色 `[待补充：…]` / `[PENDING: …]`，**投稿前删除或换成终稿内容**。
- 蓝色正文若承诺写入**修订稿**而尚未改稿：用「将…」表述，并保留红色 `修订稿 …` pending（或等价 `\rpending`）。

## 性能表加粗规则

回复信中性能表（如外测、OOF 等块）数据格加粗表示**该指标块内该列点估计最优**（Dice/AUROC/AUPRC ↑，HD95 ↓）。校验：`python3 scripts/audit_response_table_bold.py`。

## 维护脚本（本目录 `scripts/`）

| 脚本 | 用途 |
|------|------|
| `soften_response_bold.py` | 弱化 `authorresponse` 内多余 `\textbf` |
| `audit_response_table_bold.py` | 检查性能表最优列加粗 |
| `patch_manuscript_table_format.py`、`turgify_body_tex.py`、`add_response_captions.py` | 表版式/信头批量调整 |
| `migrate_response_asset_refs.py`、`rename_response_asset_keys.py` | 表图键迁移 |

从指标 JSON **重新生成**某类长表（如 `generated/routing_ablation_tables_*.tex`）时，使用仓库 `scripts/revision/` 下对应导出脚本（索引见 [`scripts/README_REVISION.md`](../../../../../scripts/README_REVISION.md)）。**手编表**直接改 `generated/*_tables_*.tex`，并在 `body_*.tex` 信末保持 `\input` 顺序与正文引用一致。

## 编译与预览

```bash
# 本目录
xelatex REVIEWER_RESPONSE_ZH.tex
xelatex REVIEWER_RESPONSE_EN.tex

# 可选本地预览（上级 latex-viewer）
cd ../latex-viewer && python3 app.py
```

修改 `response_asset_registry.tex` 或新增 `\label` 后建议 **编译两次** 以稳定交叉引用。
