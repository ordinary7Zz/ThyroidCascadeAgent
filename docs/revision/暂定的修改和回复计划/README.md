# 暂定的修改和回复计划

> 基于当前 `docs/revision/b*` 结论与 `ThyroidXAgent.md`、`Nature Communications Reviews.pdf` 整理。  
> 数值与占位项可在定稿前替换；不替代 `docs/ThyroidXAgent_返修计划与回复_中文.md` 中的逐条回复全文。  
> **写稿约定**：拟改内容只记在 **`MANUSCRIPT_REVISION_PLAN_*`**（尤其 §8）；**不提前改** `docs/ThyroidXAgent.md`，统稿时一次性合并。

## 本 README 的作用与更新规则

**作用**：维护 **「哪些 B 包仍在进行中」** 与 **「已归档包索引」** 两张快照。**不写**实验细节、不改稿、不替代同目录下的 `MANUSCRIPT_*` / `REVIEWER_*` / `B_DELIVERABLES_*` 或各 `docs/revision/b*/` 结论文档。

**包状态变更时（归档 / 新开）**：

| 步骤 | 改什么 |
|------|--------|
| 1 | 从下表 **进行中** 挪入 **已归档**（或反向，少见） |
| 2 | 同步 [`B_DELIVERABLES_CHECKLIST_ZH.md`](./B_DELIVERABLES_CHECKLIST_ZH.md) 总览行 |
| 3 | 更新 `MANUSCRIPT_REVISION_PLAN_ZH.md` / `REVIEWER_RESPONSE_PLAN_ZH.md` 页眉一句；**已归档包**在本目录只保留 **§/专项索引**（长表留在 `b*/` 或 `正式回复/latex`） |

**不要**：为单个 B 包在本 README 里另开二级标题、长表格或实验状态说明。

## 进行中的工作包（2026-10-27）

| 包 | 审稿/稿面侧重 | 仓库入口 | 当前阻塞 |
|----|---------------|----------|----------|
| **B5** | **R3.2**；prompt 元数据五 mode 消融（**仅 TN5K**） | `../b5/`；**§14**；`REVIEWER` **B5 专项**；**正式回信 `tab_metadata_ablation_*`** | **回信已定稿**；稿面 Supp. 统稿；**NHC 不跑 B5**（见 **§17.5**） |
| **B7** | **R1.3** NHC 异质性 + **R2.6** | `../b7/`；**§17**；`output/b7/nhc_sample_canonical/` | 示例 **10 图 / 2 中心** 已填入三计划；定稿换全量 NHC + **G3** |

其余 **B1–B4、B6、B8–B12** 均已 **归档**（见下表）；统稿时按各包真源与 `MANUSCRIPT` **§7–§16** 并入稿件即可。

## 已归档工作包（改稿真源不在本目录展开）

实验结论、改稿清单与（多数）正式回信已收敛；本目录 **仅保留交叉索引**，**勿**在三计划中重复维护长表。

| 包 | 审稿条（主） | 单一真源（统稿时优先改此处） | 本目录索引 |
|----|--------------|------------------------------|------------|
| **B1** | R1.1, R2.2, R2.4, R3.3 | `../b1/B1_结论与回复素材.md` | `MANUSCRIPT` §2.1、§3、§4；`REVIEWER` B1+B2 专项 |
| **B2** | R1.1, R2.2, R2.14（CI） | `../b2/conclusions/B2_结论与回复素材.md` | 同上；`b2/tables/` |
| **B3** | R1.2, R2.8, R3.1 | `../b3/B3_WAVE1_RESULTS.md`；`REVIEWER_RESPONSE_SNIPPETS_B3.md` | **§13**；`REVIEWER` **B3 专项**；正式回复 `tab_routing_ablation_*` |
| **B4** | R2.8 | `../b4/B4_STATUS_ZH.md`；L3 → `../b3/manuscript_llm_metrics.yaml` | **§15**；`REVIEWER` **B4 专项**；正式回复 `tab_component_ablation_*` |
| **B6** | R2.9 | `../b6/B6_ROUTING_STABILITY_CONCLUSIONS.md`；`docs/supplementary/router_spec.md` | **§11**；`REVIEWER` **B6 专项** |
| **B8** | R1.3（校准/拒答，不含 NHC） | `../b8/`；`output/b8/` | **§12**；`REVIEWER` **B8 专项** |
| **B9** | R2.10–12；S5 灰底 | [`../b9/B9_ThyroidXAgent_修改与回复计划.md`](../b9/B9_ThyroidXAgent_修改与回复计划.md) | **§16**；`REVIEWER` **B9 专项** |
| **B10** | R2.14 | `../b10/B10_结论与回复素材.md` | **§10**；`REVIEWER` **B10 专项** |
| **B11** | R2.20–21 | `../b11_b12/`；`docs/reproducibility_radiomics.md` | **§8.3–§8.4** |
| **B12** | R2.7, R2.1, R2.3, R1.4 | `../b11_b12/README.md`；回信 **`fig_image_dataflow`** `正式回复/figures/fig_image_dataflow.png` | **§8–§9**；`REVIEWER` B12 专项 |

**修改/回复计划中的对应位置**：进行中 **B5** → **§14** + **B5 专项**（TN5K；**无 NHC 热图**—托管机无 LLM）；进行中 **B7** → **§17** + **B7 专项** + R1.3/R2.6（B8 校准/拒答与 NHC 异质性分条）。

**B5 与 B3/B4 范围差**：B3/B4 为九队列全外测；B5 **性能消融仅单列 TN5K**（不必九队列五 mode）。见 `MANUSCRIPT` **§14** 稿面范围段。

## 范围（重要）

| 包含 | 不包含 |
|------|--------|
| 返修工作包 **B1–B12**（分割、分类、路由、LNM/FTC、基线协议、统计 CI、图像侧数据流等） | 返修计划中 **Shiyu 的 S1–S10**（报告生成、ThyClinScore 医生验证、模板审计、ReAct 失败模式、读者研究数据等） |
| 对应 `docs/revision/b1` … `b12`（及 `b11_b12`） | Fei Chen **F1–F10** 中纯临床/读者研究主责项（本目录仅标注「不由 B1–B12 覆盖」） |

**命名区分**：稿内 **Supplementary Table S3/S4**（补充表编号）≠ 内部任务 **S3/S4**（Shiyu）。本计划里的 S3/S4 若无说明，均指**论文补充表**。

**B12 与 S9**：B12 交付物为**图像侧**数据流（`b11_b12/DATAFLOW_*`）；与报告侧合并成全文 Fig.1 属共同作者协调，**不算入本目录的修改/回复任务**。

## 文件列表

| 文件 | 说明 |
|------|------|
| [MANUSCRIPT_REVISION_PLAN_ZH.md](./MANUSCRIPT_REVISION_PLAN_ZH.md) | 稿件修改计划（中文，**唯一稿本**） |
| [REVIEWER_RESPONSE_PLAN_ZH.md](./REVIEWER_RESPONSE_PLAN_ZH.md) | 审稿意见回复就绪度（中文，R1–R3，**唯一稿本**） |
| [REVIEWER_RESPONSE_DRAFT_EN.md](./REVIEWER_RESPONSE_DRAFT_EN.md) / [REVIEWER_RESPONSE_DRAFT_ZH.md](./REVIEWER_RESPONSE_DRAFT_ZH.md) | 历史 MD 稿本；**正式回信**以 `正式回复/latex/generated/body_*.tex` 为准 |
| [B_DELIVERABLES_CHECKLIST_ZH.md](./B_DELIVERABLES_CHECKLIST_ZH.md) | **B1–B12 交付清单**（文/图/表 + 稿面位置 + 仓库路径 + 状态） |
| [../../scripts/README_REVISION.md](../../scripts/README_REVISION.md) | **返修脚本 / pipeline 模块索引**（按 B 包归类） |

## 引用路径

- 稿件：`../../ThyroidXAgent.md`
- 审稿 PDF：`../../Nature Communications Reviews.pdf`
- **进行中**：`../b5/`、`../b7/`
- **已归档**：上表各 `../b*/` 真源；正式回信 `正式回复/latex/`
