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
- 信内表图编号**仅** R1–R20、图 R1–R3（见 `reviewer_response.sty` 页眉说明）；**不复用**稿件 Supplementary Table S* 序号。
- 图：先 `\includegraphics`，再 `\caption{\responsefiguretitle{键}{短标题}}`，图例正文用 `\responsefigurenote{…}`（题注在图下方）。
- `authorresponse` 内除「\textbf{支撑材料：}」/「\textbf{Supporting material:}」外**不用** `\textbf`（蓝色正文已足够区分；术语与数字用正常字重，表图用 `\responsetableref` 等引用即可）。

## 表图注册与命名

1. 在 `generated/response_asset_registry.tex` 增加一行，例如 `\responsetableregister{tab_example}{R20}`（新增编号时同步改 `reviewer_response.sty` 中 R1–R* 范围说明）。
2. `\label{tab_example}` 与注册键、`\responsetableref{}` 参数**必须相同**（语义 slug，不含数字）。
3. 表题：`\caption{\responsetabletitle{tab_example}{短标题}}`；正文与表注引用用 `\responsetableref` / `\responsetablerefrange`，勿手写「表 R*」。
4. 续表页眉（`longtable` 的 `\endhead`/`\endfoot`）：`\responsetablecontinuedrow{tab_…}`（勿用 `\responsetableref`，避免列宽异常）。正文引用续表可选 `\responsetablesetcontinued{tab_…}`。
5. 长表分页：`\begin{responsepaginatedtable}…\end{responsepaginatedtable}`；单页浮动表：`\begin{responsetable}…\end{responsetable}`（含 `\centering`）。
6. 与投稿主表版式一致的复现块：`manuscriptresponsetable`（AUROC/AUPRC 或 Dice/HD95 分节、± 半宽 CI、灰底 ThyroidXAgent 行，见 `docs/ThyroidXAgent.md` 表标签）。
7. 附录 A1/A2 前：`\responseproseappendixstart`；附录正文：`\begin{responseappendixprose}…\end{responseappendixprose}`；附录内表一律 `responseinlinetable` + `\responseinlinetablecaption`（勿用浮动 `responsetable`）。Prompt：`promptverbatim`（`breaklines=true`）。
8. **附录 / 表 R* / 图 R***：题注与正文按补充材料写法自洽表述，**不写**审稿意见编号（如 R2.9）或「本附录回应…」；对应关系仅在蓝色 **回复** 与「支撑材料」中正向引用附录 A1/A2 或 `\responsetableref`。
9. **附录少用加粗**：小节用 `\noindent 1.~标题`；prompt 说明用普通「System / User / 模型输出」标签；A2 表内版本号用 `\texttt`，数值与术语不必 `\textbf`（表题仍由 `\responseinlinetablecaption` 加粗）。

### 长表 `longtable` 版式陷阱（路由消融表 R12 / R13 等）

信内仅 `generated/routing_ablation_tables_*.tex` 使用 `responsepaginatedtable` + `longtable`。该表**多次**因续页页眉或边距宏被改坏版式，修改时请对照本节。

| 现象 | 常见原因 | 正确做法 |
|------|----------|----------|
| 表头/`\toprule` 行明显变窄 | 在 `\endhead` / `\endfoot` 的 `\multicolumn{…}{…}{\responsetableref{…}}` 里用交叉引用 | 续页页眉只用 `\responsetablecontinuedrow{tab_routing_ablation_seg}`（或 `tab_routing_ablation_cls`）。该宏为**纯文本**「表 R*（续）」+ `@{}r@{}` 跨列，避免 hyperref 链接盒参与 `longtable` 列宽计算。正文里仍用 `\responsetableref`。 |
| 表体贴左、不居中 | `responsepaginatedtable` 内把 `\LTleft` / `\LTright` 设为 `0pt` | 保持 sty 默认：`\setlength{\LTleft}{0pt plus 1fill}`、`\setlength{\LTright}{0pt plus 1fill}`（表宽小于版心时左右均分空白）。**不要**为「拉宽」而清零左右边距。 |
| 表题第一行只有「表 R12.」很短一行 | 表题在编号后的普通空格处断行 | 表题统一 `\responsetabletitle{键}{…}`（编号后已用 `\nobreakspace` 与标题粘连）。 |

**原则**：`longtable` 的续页页眉是版式行，不是正文引用；边距用 `plus 1fill` 居中，不要用 `\responsetableref` 换编号。

## 待定与修订稿承诺

- `\rpendingzh{…}` / `\rpending{…}`：红色 `[待补充：…]` / `[PENDING: …]`，**投稿前删除或换成终稿内容**。
- 蓝色正文若承诺写入**修订稿**而尚未改稿：用「将…」表述，并保留红色 `修订稿 …` pending（或等价 `\rpending`）。
- **NHC（表 R18--R20）**：回信正文与表注**不得**出现仓库路径、脚本名、配置键或内部文件名；暂行子集（10 图）数字定稿后替换为全量 8721 图。院方元数据用 `\rpending` 标出。NHC **无** 策略 7 / LLM 全系统层 / 元数据热图（托管政策，正文写 N/A）。

## 性能表加粗规则

回复信中性能表（如外测、OOF 等块）数据格加粗表示**该指标块内该列点估计最优**（Dice/AUROC/AUPRC ↑，HD95 ↓）；改表时在 `generated/*_tables_*.tex` 内人工核对。

## 编辑约定

回信 **LaTeX 为唯一编辑源**：直接改 `generated/body_*.tex`、`generated/*_tables_*.tex`、`reviewer_response.sty` 等；实验指标见 `docs/revision/b3/`、`output/ablation/` 的 CSV/JSON，**不再**用脚本覆盖 `generated/*.tex`。信末 `\input` 顺序须与正文 `\responsetableref` 一致。

## 编译与预览

```bash
# 本目录
xelatex REVIEWER_RESPONSE_ZH.tex
xelatex REVIEWER_RESPONSE_EN.tex

# 可选本地预览（上级 latex-viewer）
cd ../latex-viewer && python3 app.py
```

修改 `response_asset_registry.tex` 或新增 `\label` 后建议 **编译两次** 以稳定交叉引用。
