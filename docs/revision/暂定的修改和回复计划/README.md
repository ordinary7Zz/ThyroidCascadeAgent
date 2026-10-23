# 暂定的修改和回复计划

> 基于当前 `docs/revision/b*` 结论与 `ThyroidXAgent.md`、`Nature Communications Reviews.pdf` 整理。  
> 数值与占位项可在定稿前替换；不替代 `docs/ThyroidXAgent_返修计划与回复_中文.md` 中的逐条回复全文。  
> **写稿约定**：拟改内容只记在 **`MANUSCRIPT_REVISION_PLAN_*`**（尤其 §8）；**不提前改** `docs/ThyroidXAgent.md`，统稿时一次性合并。

## 接近定稿的工作包（当前优先统稿）

下列四包 **实验/审计与结论文档已基本齐**，剩余以 **写入 `ThyroidXAgent.md`、Supp. 制表、回复信摘段** 为主（非新训练）。**先后顺序**为团队定稿习惯：先 B11/B12，再 B1/B2。

| 顺序 | 包 | 审稿/稿面侧重 | 仓库入口 | 统稿前常见小项 |
|:---:|---|---------------|----------|----------------|
| 1 | **B11** | R2.20–21；Methods 4.3（后处理、小结节、放射组学） | `../b11_b12/`；`docs/reproducibility_radiomics.md` | §8.3 入 Methods；R2_20 Supp. 表；mm/px 脚注 |
| 2 | **B12** | R2.7、R2.1、R2.3、R1.4；摘要/§2.2 宏平均；图像侧数据流 | `../b11_b12/README.md`；`DATAFLOW_FIGURE.mmd` | 摘要 **0.9001/0.8705**；Fig.1 导出；28,458 分层文案 |
| 3 | **B1** | R1.1、R2.2、R2.4、R3.3；数据边界与 **dHash** 近重复 | `../b1/B1_结论与回复素材.md`；`../b1/tables/` | 可选 F6 患者数；spot check；ZJH excl. Supp. 入稿 |
| 4 | **B2** | R1.1、R2.2、R2.14（CI 部分）；**S3/S4** cluster CI、患者级 | `../b2/conclusions/B2_结论与回复素材.md`；`../b2/tables/` | 刷 Supp. 表；**不含 NHC**；DDTI_cls **n=349** |
| 5 | **B10** | **R2.14**；Supp. 基线协议表；S3/S4 表注 | `../b10/B10_结论与回复素材.md`；`../b10/tables/baseline_training_protocol.md` | 定 **S[X]**；Methods 4.3 入稿；§6.2 核对 |

**修改/回复计划中的对应位置**：B11/B12 → `MANUSCRIPT_REVISION_PLAN_ZH.md` **§8–§9**；B1/B2 → **§2.1、§3、§4、§6** 与 `REVIEWER_RESPONSE_PLAN_ZH.md` **B1+B2 专项**；**B10** → 同文件 **§10** 与回复计划 **B10 专项（R2.14）**。其余 **B3–B9** 见 [`B_DELIVERABLES_CHECKLIST_ZH.md`](./B_DELIVERABLES_CHECKLIST_ZH.md)。

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
| [B_DELIVERABLES_CHECKLIST_ZH.md](./B_DELIVERABLES_CHECKLIST_ZH.md) | **B1–B12 交付清单**（文/图/表 + 稿面位置 + 仓库路径 + 状态） |
| [../../scripts/README_REVISION.md](../../scripts/README_REVISION.md) | **返修脚本 / pipeline 模块索引**（按 B 包归类） |

## 引用路径

- 稿件：`../../ThyroidXAgent.md`
- 审稿 PDF：`../../Nature Communications Reviews.pdf`
- 接近定稿四包：`../b11_b12/`、`../b1/`、`../b2/conclusions/`
- 其余包：`../b3/` … `../b10/` 等（见 `../README.md`）
