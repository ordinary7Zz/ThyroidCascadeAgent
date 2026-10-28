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

## 审稿人可读性：禁止内部/机器命名

回信面向未读仓库的审稿人。**凡会出现在 PDF 里的叙述**（蓝色 `\authorresponse`、`\responsetablenote`、`\responsefigurenote`、附录 A1/A2 的小标题与说明文字、表 A* 的「说明」列）须能**脱离代码库独立读懂**。

**不得写入（非穷举）**

- 仓库/实现流程代号：Path A / Path B、Phase 1–2/5、`enable_agent`、B3/B4/B6 等返修批次名（TeX 源文件 `%` 注释除外）。
- 路径与文件名：磁盘路径、`routing_log.jsonl`、`.py` / `.yaml` / `.csv`、配置键、脚本名、内部队列别名（如 `test_for_llm_malignancy`、`all_datasets` 作公开标识）。
- 程序标识：函数名、类名、JSON 字段名（如 `cls_path_b`、`agent_path_b_llm`、`selected_model`）——除非封在 `promptverbatim` 内且为部署 prompt **原文**的一部分。
- 以**图像文件名**作病例公开 ID（可写去标识化 Rec-07、队列内序号等）。

**改写成什么**

- 用稿件/Methods 已有概念或本信已定义术语（ThyroidXAgent、策略 (1)–(8)、三独立分类器一致/不一致、LLM 路由、确定性共识、冻结的上游专家输出等）。
- 附录 A1：小节标题与 bullet 用自然语言（例：**分类 --- 分类器不一致时的 LLM 裁决**）；`promptverbatim` 内保留 API 实际措辞；叙述性 wrap 用「程序拼接」「结构化路由记录」，不写日志文件名。
- 附录 A2 / 表 A2：版本号用 `\texttt{包名 版本}` 即可；不必写训练环境配置文件名（可写「与训练环境配置一致」）。

**允许例外**

- 复现所必需的 **API 端点、模型 ID**（表 A1-1）。
- 本信**表内已定义**的缩写层（L1/L2/L3、策略编号、R* 表号）。
- `\rpending{…}` 中若需内部跟踪，投稿前仍应改成审稿人可读表述或删除。

NHC 表 R18–R20 另遵守下文「待定与修订稿承诺」中的 NHC 条款（与本节一致，不重复写路径/脚本）。

## 版式要点

- 信头：`\responselettertitle`、`\responseletteropening` / `openingzh`（说明表图复现于信末）。
- 审稿意见：黑色斜体；作者回复：`ResponseBlue`。
- 分节：`\responsetoreviewer{…}`；无目录、无 `\hrule`。
- `authorresponse` 内**不用** `\textbf`（不另设「支撑材料：」行；表图在正文句中引用，信末 `\responseappendix` 集中复现，与 TURG 样稿一致）。
- **逐条明确回应**：每条 `\reviewercomment` 下的回复须让审稿人看出「**是否同意/是否已做** + **证据在哪**（`\responsetableref` / `\responsefigureref` / 附录 / 修订稿 Methods）」。避免只有方法描述或 cross-ref 而无「我们已…」；多子问题时用 `(a)(b)(c)` 或分 `\item` 逐条对应；暂缺数据用 `\rpending`，勿留看似未写完的单句。
- 正文引用：`\responsetableref` / `\responsefigureref` / `\responsetablerefrange` 嵌入句子；**勿** `（见表 R*）`、**勿**「见信末」/ “at the end of this letter”、**勿**每条末尾重复表号清单。
- **只引用表/图，不单独引用「表注/图注」**：Nature 系回复信与正文一样，交叉引用对象是 **Table/Figure**（本信用 `\responsetableref`）；表注 `\responsetablenote` 是表的一部分，读者跟表号即可。**勿**写 “in Table~R12 **notes**” /「见 \responsetableref{…} **表注**」——除非正文刻意不写细节、且细节**仅**在表注（此时也只写 `\responsetableref{…}`，不必点「表注」二字）。同一句里已写清操作定义时，**删除**再指向表注的尾巴（避免重复）。
- 信内表图编号**仅** R1–R20、图 R1–R3（见 `reviewer_response.sty` 页眉说明）；**不复用**稿件 Supplementary Table S* 序号。
- 图：先 `\includegraphics`，再 `\caption{\responsefiguretitle{键}{短标题}}`，图例正文用 `\responsefigurenote{…}`（题注在图下方）。

## 表图注册与命名

1. 在 `generated/response_asset_registry.tex` 增加一行，例如 `\responsetableregister{tab_example}{R20}`（新增编号时同步改 `reviewer_response.sty` 中 R1–R* 范围说明）。
2. `\label{tab_example}` 与注册键、`\responsetableref{}` 参数**必须相同**（语义 slug，不含数字）。
3. 表题：`\caption{\responsetabletitle{tab_example}{短标题}}`；正文与表注引用用 `\responsetableref` / `\responsetablerefrange`，勿手写「表 R*」。
4. 续表页眉（`longtable` 的 `\endhead`/`\endfoot`）：`\responsetablecontinuedrow{tab_…}`（勿用 `\responsetableref`，避免列宽异常）。正文引用续表可选 `\responsetablesetcontinued{tab_…}`。
5. 长表分页：`\begin{responsepaginatedtable}…\end{responsepaginatedtable}`；单页浮动表：`\begin{responsetable}…\end{responsetable}`（含 `\centering`）。
6. 与投稿主表版式一致的复现块：`manuscriptresponsetable`（AUROC/AUPRC 或 Dice/HD95 分节、± 半宽 CI、灰底 ThyroidXAgent 行，见 `docs/ThyroidXAgent.md` 表标签）。
7. 附录 A1/A2 前：`\responseproseappendixstart`；附录正文：`\begin{responseappendixprose}…\end{responseappendixprose}`；附录内表一律 `responseinlinetable` + `\responseinlinetablecaption`（勿用浮动 `responsetable`）。Prompt：`promptverbatim`（`breaklines=true`）。
8. **附录 / 表 R* / 图 R***：题注与正文按补充材料写法自洽表述，**不写**审稿意见编号；表图在蓝色回复正文中嵌入引用，信末 `\responseappendix` 集中复现。
9. **附录少用加粗**：小节用 `\noindent 1.~标题`；prompt 说明用普通「System / User / 模型输出」标签；A2 表内版本号用 `\texttt`，数值与术语不必 `\textbf`（表题仍由 `\responseinlinetablecaption` 加粗）。

### 长表 `longtable` 版式陷阱（路由消融表 R12 / R13 等）

信内仅 `generated/routing_ablation_tables_*.tex` 使用 `responsepaginatedtable` + `longtable`。该表**多次**因续页页眉或边距宏被改坏版式，修改时请对照本节。

| 现象 | 常见原因 | 正确做法 |
|------|----------|----------|
| 表头/`\toprule` 行明显变窄 | 在 `\endhead` / `\endfoot` 的 `\multicolumn{…}{…}{\responsetableref{…}}` 里用交叉引用 | 续页页眉只用 `\responsetablecontinuedrow{tab_routing_ablation_seg}`（或 `tab_routing_ablation_cls`）。该宏为**纯文本**「表 R*（续）」+ `@{}r@{}` 跨列，避免 hyperref 链接盒参与 `longtable` 列宽计算。正文里仍用 `\responsetableref`。 |
| 表体贴左、不居中 | `responsepaginatedtable` 内把 `\LTleft` / `\LTright` 设为 `0pt` | 保持 sty 默认：`\setlength{\LTleft}{0pt plus 1fill}`、`\setlength{\LTright}{0pt plus 1fill}`（表宽小于版心时左右均分空白）。**不要**为「拉宽」而清零左右边距。 |
| 表题第一行只有「表 R12.」很短一行 | 表题在编号后的普通空格处断行 | 表题统一 `\responsetabletitle{键}{…}`（编号后已用 `\nobreakspace` 与标题粘连）。 |

**原则**：`longtable` 的续页页眉是版式行，不是正文引用；边距用 `plus 1fill` 居中，不要用 `\responsetableref` 换编号。

## 待定与正文修订（`\rpending`）

- `\rpendingzh{…}` / `\rpending{…}`：红色 `[待补充：…]` / `[PENDING: …]`。**两类用途**：（1）实验/表数字尚未定稿；（2）**必须在投稿正文中改写的句子**——前缀建议 `Manuscript:` / `正文：`，便于你后续全文扫描 pending。
- **回复信蓝色正文默认不写「修订稿」「将在 Methods 中…」**；直接写协议与结果，用 `\responsetableref` / `\responsefigureref` 锚定证据，勿加「(本回复)」「(this letter)」类括号说明。对**送审稿**的事实性对照（如 layout 与投稿补充表一致）可保留，但不要承诺「修订稿将…」。
- 确需改正文时：**本回复已给出的实质内容 + 一句 `\rpending{Manuscript: …}`**，勿在蓝色段落展开未来稿面全文。
- **NHC（表 R18--R20）**：遵守上文「审稿人可读性」；暂行子集（10 图）数字定稿后替换为全量 8721 图。院方元数据用 `\rpending` 标出。NHC **无** 策略 7 / LLM 全系统层 / 元数据热图（托管政策，正文写 N/A）。

## 性能表加粗规则

回复信中性能表（如外测、OOF 等块）数据格加粗表示**该指标块内该列点估计最优**（Dice/AUROC/AUPRC ↑，HD95 ↓）；改表时在 `generated/*_tables_*.tex` 内人工核对。

## 编辑约定

回信 **LaTeX 为唯一编辑源**：直接改 `generated/body_*.tex`、`generated/*_tables_*.tex`、`reviewer_response.sty` 等；实验指标见 `docs/revision/b3/`、`output/ablation/` 的 CSV/JSON，**不再**用脚本覆盖 `generated/*.tex`。信末 `\input` 顺序须与正文 `\responsetableref` 一致。

改稿前对照 **`latex/README.md` →「审稿人可读性：禁止内部/机器命名」**；`ai/INSTRUCTIONS.md` 与之同步。

## 编译与预览

```bash
# 本目录
xelatex REVIEWER_RESPONSE_ZH.tex
xelatex REVIEWER_RESPONSE_EN.tex

# 可选本地预览（上级 latex-viewer）
cd ../latex-viewer && python3 app.py
```

修改 `response_asset_registry.tex` 或新增 `\label` 后建议 **编译两次** 以稳定交叉引用。
