# 回信写作风格（Nature 子刊口径）

与 [`INSTRUCTIONS.md`](./INSTRUCTIONS.md) 流程规则、`../latex/README.md` 版式与「审稿人可读性」并列。**改 `body_*.tex` 正文语气时必读本节。**

## 1. 总体目标

- 语气接近 **Nature 子刊** 的 author response / 正文：**直接、克制、可独立阅读**，像已发表稿的 Results 或 Methods 补充说明，不像内部备忘录或给合作者的编辑说明。
- 每条 `\authorresponse` 仍须 **We agree / We report / We performed… + 表/图/附录**（见 INSTRUCTIONS），但证据用 **嵌入句子的 `\responsetableref`** 带过，不在正文重复表内数字或大段解释「我们为什么没写数字」。

## 2. 禁止：meta 叙述与「不专业」解释

下列写法**不要**出现在蓝色 `\authorresponse` 正文（表注 `\responsetablenote` 也只写方法/定义，不写编辑过程）：

| 避免 | 原因 |
|------|------|
| 「具体数值以表为准」「不作逐项对齐」「与某表报告范围不同」 | 表号即证据；范围差异应在 Methods/表注一次说清，不在回复里向审稿人解释排版/对齐策略 |
| 「占位」「定稿后将替换」「entries may be updated」 | 用户与编辑内部知情即可，不出现在 PDF |
| 「下文在此前提下解读」「read under that premise」 | 元叙述；应把前提写进一句机制说明，直接接表引用 |
| 「We do not restate table entries here」 | 默认不写表内数字；不必声明 |
| 长括号堆砌限制条件 `(…; …; …)` | 拆成短句或删去审稿人无需知道的内部约束 |
| `\textbf{机制说明。}` `\textbf{Performance ablation.}` 等**假小标题** | 易读成 slide bullet；改用 `\par` 分段 + 首句主题（*Audit design.* 式） |
| 用 **NHC** 举例说明 BM 外测上的 metadata 粒度 | 队列不同、易混淆；用 TN3K / TN5K / ThyroidXL 等 **BM 外测** 说明即可 |
| 在 **R3.2** 写 R2.6/R2.8 专属内容（如 NHC 各中心性能、$I^2$ 异质性长段） | 意见分工；交叉引用其他 R* 一句即可，不抢答 |

## 3. 推荐写法

### 3.1 引用表图

- **一句一引用**：`…见 \responsetableref{tab_…}` / `…are in \responsetablerefrange{…}{…}`，勿再附「（见表 R*）」或「at the end of this letter」。
- **不在正文复述表内点估计与 CI**（除非审稿人点名要一句主结论且表尚未定稿——此时用 `\rpending` 而非写可能过期的数字）。
- **不单独指「表注」**（见 `latex/README.md`）；需要细节时只引用表号。

### 3.2 段落与衔接

- 同一条意见内用 **2–4 个 `\par` 段**：协议/定义 → 机制一句 → 表 A → 表 B → 例外（如 NHC 一句）。
- 段首可用简短主题句（英文 *We also note that…*；中文「LLM 路由器未以…」），**不用**加粗标题行。
- 用连接词衔接（「因此」「在此协议下」「For NHC-MISD-TUS, …」），避免五段互无关的清单感。

### 3.3 表题与表注（`generated/*_tables_*.tex`）

- 表题：**短、自洽**（说明对象 + 指标即可），不必在题里堆「策略 (7)」「LLM 路由」若正文已定义协议。
- 表注：方法定义、队列、CI 协议；**不写**「待补」「与某实验目录一致」等仓库/流水线说明（`%` 注释可保留 `[DATA-SOURCE]` 给维护者）。

### 3.4 与 INSTRUCTIONS 其它条的关系

- **仍遵守**：勿写 Path A/B、Phase、脚本名、日志文件名（`latex/README.md` 专节）。
- **仍遵守**：R2.2 外不写满 bootstrap 参数；`\rpending` 只用于真正未定稿处。
- **中英文**：先改 `body_en.tex`，再 **语义对齐** 更新 `body_zh.tex`（中文不必更「解释性」 than 英文）。

## 4. 自检（改完 R* 段落后）

1. 删掉所有表号后，是否仍能看出 **已回应审稿人每条要求**？若不能，补 **We report… + `\ref`**，不要补 meta 说明。  
2. 全文搜索：`以表为准`、`不对齐`、`占位`、`below`、`\textbf{…。}`（句号标题）——应无或极少。  
3. 是否有多余 **双重否定/双重限制**（「无法提供…亦未执行…」）？能合并成一句事实陈述则合并。

## 5. 示例（R3.2 类：metadata + 专家占比）

**Prefer（简）**

> Segmentation and classification results under the metadata ablation are in Tables R*–R*; per-cohort LLM expert-selection shares are in Tables R* and R*.

**Avoid**

> …to test whether performance systematically depends on device/source (**table entries are authoritative; that table is not row-aligned with…**). …(**具体数值以表为准；该表与多队列路由性能表报告范围不同，不作逐项对齐**).

---

改稿后若新增风格教训，在 [`HISTORY.md`](./HISTORY.md) **教训 / 避免重犯** 写一行，并视需要增补本节（勿只堆 HISTORY 不更新本文）。
