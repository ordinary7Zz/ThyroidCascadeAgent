# B9 · ThyroidXAgent 论文修改计划与回复计划（稿本 v0.1）

> **用途**：对照 docx Part A **B9** 与审稿 **R2.10–R2.12 / R2.11**，判断当前实验是否**覆盖要求**；稿内 **Table S5 灰底「ThyroidXAgent」行**先填入**当前 OOF 数值**，定稿前由全栈融合结果**整格替换数字**（n 通常不变，AUROC/AUPRC/CI 从新的 `cv_summary.json` 抄写）。  
> **数值来源（2026-10-24）**：`dino_unet_multitask/Malignant_Cls_Model/b9/runs/{lnm_cv,ftcptc_cv}/cv_summary.json`（DINO multitask，验证折分类概率 → 患者/簇 mean → OOF）。AutoGluon 五折进行中；外测 E2/E4 未做。  
> **专家行（LLNM-Net / Tiger）**：仍用 `B9_LNM_ZJH8K_LymphUs_C1C2结论.md`、`B9_FTCPTC_论文包结果结论文档.md`，**不得**与 ThyroidXAgent 行混用。

---

## 1. B9 要求覆盖度总表（自检）

| 要求 ID | docx / 审稿 | 要求摘要 | 当前状态 | 覆盖？ |
|---------|-------------|----------|----------|--------|
| **E1** | B9, R2.11, S5 LNM | ThyroidXAgent **患者级 5 折 OOF**（4753 图，882 簇） | DINO 五折 **已完成**；AG+路由 **未完成** | **🟡 协议+数字占位**；严格全栈 **⬜** |
| **E2** | R2.11, S5 | LNM **C2 158** 外测（全开发集训一套 + 路由） | 未启动 | **⬜** |
| **E3** | B9, R2.11, S5 FTC | FTC **患者级 5 折 OOF**（4756 图，722 簇） | 同 E1 | **🟡 / ⬜** |
| **E4** | R2.10, S5 | FangDai **199** 外测 | 未启动 | **⬜** |
| **E5** | R2.12 | LNM 仅 ZJH 敏感性 | 未做 | **⬜ 可选** |
| **E6** | R2.10, F7 | 真 FTC 重训 | 未做 | **⬜ 协作** |
| **折分** | B9 | 替换稿内 **20 例 val** → **5 折 CV** | 已实现（seed=42） | **✅** |
| **簇定义** | R2.12, LLNM 对齐 | ZJH **年/姓名**；LymphUs **每图一簇** | `packed_io` 已统一 | **✅** |
| **专家对照** | S5 非灰底行 | LLNM / Tiger 五折与外测 | 已有结论文档 | **✅**（与主系统无关） |

**结论（是否够写 B9 计划）**：**可以写**修改计划与回复信**框架**；**R2.11 主论点**（大样本 + 5 折 OOF 协议）可用当前数字支撑；**严格 docx「全栈 OOF + 双外测」** 仍缺 **AG 五折、路由融合、E2/E4**，需在回复中写清「进行中/将更新」或先报 OOF 再补外测行。

---

## 2. Supp. Table S5 · ThyroidXAgent 灰底行（**仅换数值列**）

> 下表 **患者级 OOF** 为稿面主报口径；图像级可放 Supp. 脚注。定稿时从 `runs/b9_txagent_*` 或 `*_ag_cv` 融合后的 `cv_summary.json` **整行替换** AUROC、AUPRC、CI（n 预期仍为 882 / 722）。

| 任务 | 模型（S5 行名） | n（簇） | AUROC | 95% CI | AUPRC | 95% CI |
|------|-----------------|--------|-------|--------|-------|--------|
| **LNM** | ThyroidXAgent | 882 | **0.718** | 0.678–0.754 | **0.598** | 0.536–0.655 |
| **FTC/PTC** | ThyroidXAgent | 722 | **0.521** | 0.442–0.602 | **0.109** | 0.076–0.160 |

**图像级 OOF（Supp. 或脚注，可选）**

| 任务 | n（图） | AUROC | AUPRC |
|------|---------|-------|-------|
| LNM | 4753 | 0.593 | 0.405 |
| FTC/PTC | 4756 | 0.556 | 0.116 |

**证据路径**

- LNM：`.../Malignant_Cls_Model/b9/runs/lnm_cv/cv_summary.json`、`oof_predictions.json`
- FTC：`.../Malignant_Cls_Model/b9/runs/ftcptc_cv/cv_summary.json`、`oof_predictions.json`

**表注（稿本，定稿前可弱化「仅 DINO」表述）**

- 患者级五折交叉验证，分层依据 **簇 ID**（ZJH：`年份/姓名`；LymphUs C1：**每张图一簇**）；bootstrap **1000** 次，**95%** CI，**seed=42**。
- 开发池：LNM `train_combined_zjh_plus_lymphus_c1.json`（**4753** 图）；FTC `zjh_dev_all.json`（**4756** 图）。
- ThyroidXAgent 实现为 **DINOv3 multitask**（联合分割+分类，`train_single_binary_with_mask.py`），每折 `best_f1` checkpoint 在验证折出分类概率；**定稿数值**为全系统（含 PyRadiomics–AutoGluon 与路由融合）OOF 时，仅更新上表点估计与 CI。

**外测（S5 另列或脚注，当前无 ThyroidXAgent 新数）**

| 任务 | 外测集 | n | ThyroidXAgent AUROC | 状态 |
|------|--------|---|---------------------|------|
| LNM | LymphUs C2 | 158 | *TBD* | E2 未跑 |
| FTC/PTC | FangDai | 199 | *TBD* | E4 未跑 |

稿面旧数（如 LNM 外测 ~0.864）**不得**与新协议混用，除非同协议重跑或 Limitation 说明。

---

## 3. 论文修改计划（MANUSCRIPT）

### 3.1 Abstract / Results §2.4（恶性分层）

| 修改项 | 建议表述要点 | 就绪度 |
|--------|--------------|--------|
| 验证协议 | 将固定 **20 例**验证改为 **患者（簇）级 5 折 CV**，报告 **OOF** AUROC/AUPRC 及 **95% CI** | ✅ 可写 |
| LNM 样本量 | 开发 **4753** 图、**882** 簇（ZJH 4573 + LymphUs C1 180）；与 **4936** 总标注池关系一句澄清（20 例 val 不参与本 CV） | ✅ 可写 |
| FTC 样本量 | ZJH 开发 **4756** 图、**722** 簇 | ✅ 可写 |
| S5 数字 | 用 **§2 表** ThyroidXAgent 行；与 Fig.3 轴标签 **AUROC/AUPRC 勿标反**（R2.1） | 🟡 待统稿 |
| FTC 域 | **FVPTC vs FTC** 与 FangDai **PTC vs FTC** 非同一标签目标 → **探索性/域迁移**（R2.10，见 `需要确认.md`） | 🟡 文责为主 |
| 外测 | C2 / FangDai：ThyroidXAgent **待更新** 或暂引专家行并脚注「主系统外测进行中」 | ⬜ |

### 3.2 Methods（建议新增或扩写 §4.x「恶性子任务」）

| 小节 | 内容 | 就绪度 |
|------|------|--------|
| 数据与簇 | packed manifest；`image_roots.json`；簇键规则（**§1 表**） | ✅ |
| CV | `n_splits=5`，`cv_seed=42`；簇分层；OOF 拼接 | ✅ |
| DINO | `DINOv3_S_UNet_MULTITASK`；seg+cls 联合训练；mask 来源（ZJH 预测 mask、LymphUs pred mask）；每折 epoch/选模 `best_f1` | ✅ |
| 分类 OOF | 验证折 **图像级** prob → **簇内 mean** → 患者级指标；cluster bootstrap | ✅ |
| AutoGluon | PyRadiomics 2D 特征 → `train_binary_task_resampled`；**五折与 DINO 同折**（编排 `binary_class/new_code`） | 🟡 训练进行中 |
| 路由 / 全栈 | 恶性任务专用 AG 与融合规则（非 BM `radiomics_judge`）；**定稿 S5 为融合后概率** | ⬜ 待实现文档化 |
| 与专家网络 | S5 **灰底=ThyroidXAgent**；**非灰底=LLNM-Net / Tiger**（同 packed、可对照折分，不同架构） | ✅ |

### 3.3 图表

| 项目 | 动作 |
|------|------|
| **Table S5** | 填入 §2；外测 ThyroidXAgent 列 *TBD* 或暂空 |
| **Fig.3** | 轴标签与 S5 一致；必要时仅改标注不改曲线（若曲线仍为旧实验则 **🟡 需核对**） |
| **新 Supp.** | 可选：`methods_snapshot.json`（mask、路由、AG 超参）；五折 `fold_splits.json` 与 LLNM 对照 |

---

## 4. 回复信计划（REVIEWER RESPONSE）

### 4.1 R2.11（LNM 样本量、验证、外测）— **主回复可起草**

**审稿关切（概括）**：LNM 开发集规模、验证方式、外测与训练分离。

**回复要点**

1. 我们已将恶性 LNM 的 **内部验证** 从 **20 例固定验证集** 改为 **4753 图、882 簇** 上的 **患者（簇）级分层 5 折交叉验证**，并报告 **out-of-fold（OOF）** 性能及 **聚类 bootstrap 95% CI**（1000 次，seed=42）。
2. **Table S5** 中 **ThyroidXAgent** 行 LNM 列已更新为上述 OOF：**AUROC 0.718（95% CI 0.678–0.754）**，**AUPRC 0.598（0.536–0.655）**，n=882 簇。
3. 训练数据包含 **ZJH-8K 恶性原发灶**（4573 图）与 **LymphUs Center1**（180 图）；**淋巴结图与原发灶图** 在 Methods 中按 **同一 LNM 标签键** 与 **不同成像域** 说明；簇划分上 LymphUs **按图**、ZJH **按年/姓名**（与淋巴结转移预测文献及本仓库 LLNM-Net B9 协议一致）。
4. **LymphUs Center2（n=158）** 外测：ThyroidXAgent 全系统将在 **全开发集重训** 后报告（**E2**，与稿面旧 val 协议不同）；修订稿中 **外测数字将更新** 或于回复中给出时间表。
5. 数据增强与表格模型：**DINO** 训练含分割与分类联合优化；**PyRadiomics + AutoGluon** 五折与图像专家 **同折**，全栈融合后 **仅更新 S5 数值**（协议不变）。

**覆盖度**：**CV + OOF 主数字 ✅**；**C2 外测 ThyroidXAgent ⬜**。

---

### 4.2 R2.10（FTC/PTC 标签与 FangDai 外测）— **部分回复**

**回复要点**

1. 我们承认 ZJH 开发标签为 **classic PTC vs follicular-variant PTC**，FangDai 外测为 **PTC vs FTC**，**组织学定义不完全一致**（见 `需要确认.md`）；修订稿将 **明确为探索性域迁移**，并与主结论区分。
2. **内部验证** 已改为 **4756 图、722 簇** 上 **5 折 OOF**；ThyroidXAgent 行：**AUROC 0.521（0.442–0.602）**，**AUPRC 0.109（0.076–0.160）**（Table S5）。
3. OOF 排序能力 **有限**，与先前 Tiger-Model 再分析趋势一致；**FangDai 外测（n=199）** ThyroidXAgent 结果 **待 E4 完成后填入**。
4. 真 FTC 组织学重训（**F7/E6**）属病理协作项，在 Limitation 或回复中 **单列**。

**覆盖度**：**OOF 协议与数字 ✅**；**域一致性论述 🟡**；**FangDai ThyroidXAgent ⬜**。

---

### 4.3 R2.12（LNM 术语 CN0/CN1、原发 vs 淋巴结）— **部分回复**

**回复要点**

1. 全文统一 **LNM 二分类标签键**（如 `LNM_CN01`）及 **临床定义** 一句（**待协作定稿**，见 `需要确认.md`）。
2. **患者级聚合**：同一簇内多图 **概率算术平均**；标签在同一簇内一致（ZJH）；LymphUs **一图一簇** 故无「同簇异标签」问题。
3. 与 **R2.11** 五折协议一致，见 Methods 与 Table S5。

**覆盖度**：**统计协议 ✅**；**临床定义句 ⬜ 协作**。

---

## 5. 与专家 B9 行的关系（回复中一句防混淆）

| S5 行 | 模型 | 能否用本文 §2 数字 |
|-------|------|-------------------|
| 灰底 **ThyroidXAgent** | 主系统（稿面）；当前数=**同协议 OOF**，定稿换融合后 `cv_summary` | **是（可替换）** |
| **LLNM-Net**（LNM） | 专家 | **否** → `B9_LNM_ZJH8K_LymphUs_C1C2结论.md` |
| **Tiger**（FTC） | 专家 | **否** → `B9_FTCPTC_论文包结果结论文档.md` |

---

## 6. 定稿前「只换数值」检查单

- [ ] 从 **全栈** `cv_summary.json` 抄写 **AUROC、AUPRC、CI**（勿手改点估计留旧 CI）。
- [ ] 核对 **n**（预期 882 / 722；若 AG 丢样本则随 json 更新）。
- [ ] 同步 **Abstract、§2.4、Table S5、回复信 R2.11** 四处数字一致。
- [ ] 填入 **C2 / FangDai** ThyroidXAgent 外测列（E2/E4）。
- [ ] 删除或更新表注中「 interim / 仅 DINO」若 Methods 已写全栈融合。
- [ ] `methods_snapshot.json` 归档路由与 AG 版本。

---

## 7. 仓库索引

| 文档 / 路径 | 作用 |
|-------------|------|
| 本文件 | B9 ThyroidXAgent **修改+回复+覆盖度** |
| `B9_ThyroidXAgent_补充实验计划.md` | 实验 E1–E4 技术计划 |
| `B9_回复素材_仅基于两篇实验结论.md` | **仅** LLNM / Tiger 回复句，非 ThyroidXAgent |
| `需要确认.md` | R2.10 / R2.12 临床表述 |
| `../暂定的修改和回复计划/MANUSCRIPT_REVISION_PLAN_ZH.md` §2.4 | 总计划索引 → **以本文件 §3 为准** |
| `../暂定的修改和回复计划/REVIEWER_RESPONSE_PLAN_ZH.md` R2.10–12 | 总回复索引 → **以本文件 §4 为准** |

---

*稿本 v0.1 · 2026-10-24 · 数值来自 DINO `b9/runs/*_cv/cv_summary.json`；AG/外测/全栈融合完成后替换 §2 表与 §4 引用的数字。*
