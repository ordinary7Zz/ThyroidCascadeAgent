# B9 · ThyroidXAgent 补充实验计划（对齐 docx）

> **依据**：`docs/ThyroidXAgent_revision_plan_and_response.docx` Part A **B9**（*replace 20-case validation with patient-level 5-fold CV*）及 Part B **R2.11** 回复草稿（DINOv3 + AutoGluon + 5-fold + C2 外测）。  
> **现状**：`LNM_ZJH8K_LymphUs_C1C2_packed` / `FTCPTC_ZJH8K_FangDai_packed` 上 **LLNM-Net / Tiger-Model** 五折已完成（见 `B9_LNM_*`、`B9_FTCPTC_*`）。**ThyroidXAgent 恶性主系统五折：无。**  
> **LLNM-Net 侧说明**：`LLNM-Net/docs/B9_LNM_构建计划.md` §1 已写明 *ThyroidXAgent DINOv3+AutoGluon 不在本仓库*——故 docx 闭环需 **本计划**。

---

## 1. 是否必须补实验？

| 路径 | 是否还要跑 GPU 实验 |
|------|---------------------|
| **严格按 docx + Part B R2.11 填主系统** | **是**：**Table S5 灰底 ThyroidXAgent 行** = 恶性任务 **端到端主系统**（非 LLNM-Net/Tiger）患者级 **5 折 OOF** + C2/FangDai 外测 |
| **改回复/表结构**（五折仅专家 Supp.） | **否**（与 docx 字面略弱，需团队接受） |

**本文档默认：走严格 docx 路径，需要补充实验。**

---

## 2. 还要补哪些实验（清单）

| ID | 实验 | 数据 | docx / 审稿 | 已有替代？ |
|----|------|------|-------------|------------|
| **E1** | **ThyroidXAgent · LNM** 患者级 5 折 OOF（**全栈输出**） | `train_combined` **4753**，882 簇，seed=42 | R2.11, B9, **S5 LNM 列** | LLNM-Net 五折 **不能**顶替 |
| **E2** | **ThyroidXAgent · LNM** C2 **158** 外测 | 全开发集训齐三支 + 路由后外测 | R2.11, S5 | 稿面 0.864 需同协议重跑或书面说明 |
| **E3** | **ThyroidXAgent · FTC/PTC** 患者级 5 折 OOF | ZJH **4756** 池 | R2.11, B9 | Tiger 五折 **不能**顶替 |
| **E4** | **ThyroidXAgent · FTC/PTC** FangDai **199** 外测 | 4573+183 开发集 | R2.10 B + S5 | Tiger 外测仅专家行 |
| **E5** | LNM 仅 ZJH 训练敏感性 | 子集 → C2/OOF | R2.12 | 未做 |
| **E6** | F7 真 FTC 重训 | 病理清单 | R2.10 A/B | 可选 |

**本期范围（已定）**：**E1–E4 一起做**（LNM + FTC/PTC 均补 ThyroidXAgent 五折与外测）。E5/E6 仍可选。

---

## 3. Table S5 报什么？恶性 ThyroidXAgent 栈（非 BM 五专家池）

### 3.1 与良恶性主任务的区别

| | 良恶性（§2.3 / S4） | **恶性分层（S5 · ThyroidXAgent 灰底行）** |
|---|---------------------|------------------------------------------|
| 数据 | 良+恶混合多队列 | **仅恶性**（ZJH-8K 恶性 + LymphUs C1 等） |
| 专家规模 | 5 分割 + 3 图像分类 + … | **瘦身栈**：**1 路分割 + 2 路分类 + 大路由器** |
| S5 数字 | 不混用 | **路由后的最终概率**（患者级聚合后 AUROC/AUPRC ± CI） |

**两路分类**指：

1. **DINO 图像分类**（任务标签 `LNM_CN01` 或 `FTCPTC`）  
2. **PyRadiomics → AutoGluon 表格分类**（同任务键）

**大路由器**：稿面 LLM/agent 或实现中等价的 **证据融合/选模**（`ThyroidCascadeAgent/pipeline` 中 seg 选 mask、cls 与 `radiomics_judge` 投票等）；**恶性任务须换任务特异 checkpoint**，不能用默认 `config.yaml` 里 **BM** 的 `radiomics_judge` 路径。

### 3.2 每个恶性任务 · 五折里训什么？（LNM 与 FTC 对称）

**FTC/PTC** 与 LNM 相同栈：仅换任务键 `FTCPTC`、数据 manifest（`FTCPTC_ZJH8K_FangDai_packed`）、外测集 FangDai（E4）。

在 **每一折、每一个任务** 内，仅用 **该折训练折** 样本：

| # | 组件 | 类型 | 标签 / 任务键 | 折内是否重训 |
|---|------|------|---------------|--------------|
| 1 | **DINO 分割** | 图像 U-Net 支 | 结节/病灶 mask 监督 | **是**（每折一版） |
| 2 | **DINO 分类** | 图像二分类头 | `LNM_CN01` 或 `FTCPTC` | **是**（每折一版） |
| 3 | **AutoGluon** | 表格 | 同左（radiomics 特征） | **是**（每折一版） |
| — | **路由器** | 规则 / LLM | 固定推理协议 | **否**（五折共用；变的是各支输入） |

**验证折**：用该折训好的三支 + 固定路由，在验证折患者上出 **OOF 概率** → 五折拼接 → 患者级 AUROC/AUPRC + bootstrap CI（替换原 20 例 val 的 ±）。

**外测 E2 / E4**：在 **该任务全开发集** 上再各训 **一套** 三支（LNM：4753 → C2；FTC：ZJH 开发池 → FangDai）。

### 3.2.1 模型数量怎么数？（避免和五折乘法搞混）

按 **逻辑角色**（分割 DINO、分类 DINO 分开计），**一个任务、训满一轮**（例如外测前的那套最终权重）：

| 任务 | DINO 分割 | DINO 分类 | AutoGluon |
|------|-----------|-----------|-----------|
| LNM | 1 | 1 | 1 |
| FTC/PTC | 1 | 1 | 1 |
| **两任务合计（一套最终模型）** | **2** | **2** | **2** |

→ 常说的 **「4 个 DINO + 2 个 AutoGluon」** = **两任务各 2 个 DINO（seg + cls）+ 各 1 个 AG**，**指的是外测用的各 1 套最终权重**（E2+E4 各训一轮，共两轮「四套 DINO + 两套 AG」若严格分开 LNM/FTC 各训一次）。

**五折 OOF（E1+E3）会乘 5**：每个任务 **每折** 仍要重训上述三支 → 单任务 **5 折 ≈ 10 次 DINO 训练 + 5 次 AG**（若 seg/cls **分开训**；联合 multitask 则每折 **1 次 DINO run + 1 次 AG**）。两任务五折都做完，训练 **次数** 约为：

| 模式 | 每任务 5 折 | LNM+FTC 五折合计（训练 run 次数） |
|------|-------------|-----------------------------------|
| DINO **分开** seg/cls | 10 DINO + 5 AG | **20 DINO + 10 AG** |
| DINO **联合** seg+cls | 5 DINO + 5 AG | **10 DINO + 10 AG** |

外测 **再** 各训一套：分开训 → **+4 DINO + 2 AG**；联合 → **+2 DINO + 2 AG**。

> **实现备注**：`Malignant_Cls_Model/train_single_binary_with_mask.py` 在 **单次 run** 里联合优化 **seg + cls**（`DINOv3_S_UNet_MULTITASK`）。若投稿实现是 **一个 checkpoint 两路输出**，五折可以是 **每折 1 次联合训练**，在文档里记为「逻辑两支 DINO（分割头 + 分类头）、物理一个权重文件」；若历史上是 **分割与分类分开训的两个 DINO 权重**，则五折为 **每折 2 次 DINO 训练 + 1 次 AutoGluon**。编排脚本须与 **实际投稿 checkpoint 结构** 一致，并在 `methods_snapshot.json` 写明。

### 3.3 代码落点（与 BM 级联无关）

| 能力 | 目录 |
|------|------|
| **DINO multitask 专家（本期优先）** | `dino_unet_multitask/Malignant_Cls_Model/`：**训练**用现有 `train_single_binary_with_mask.py`；**B9 五折**在 **`Malignant_Cls_Model/b9/`** 新建编排（见该目录 `README.md`） |
| AutoGluon + PyRadiomics | `pyradiomics_train/binary_class/`（下一阶段） |
| 端到端推理 / 路由 | `ThyroidCascadeAgent/pipeline/`（DINO+AG 就绪后） |

**Multitask 计数**：LNM、FTC 各 **1 个**联合 seg+cls checkpoint（共 **2 个 DINO 专家**），不是每任务分割/分类各一个独立网络。

**不做**：用 BM 五分割 + 三分类专家池直接当恶性训练栈。

### 3.5 实施阶段（当前：只做 DINO）

| 阶段 | 内容 | 产出 |
|------|------|------|
| **D0** | `b9/packed_io` + 折分 + 调 `train_single_binary_with_mask` | `runs/b9_dino_lnm_cv/`、`b9_dino_ftcptc_cv/` |
| **D1** | 全量 multitask + C2/FangDai **图像支**外测 | 供后续与 AG 融合 |
| **D2** | 每折/全量 AutoGluon + Cascade config | E1–E4 全栈 OOF / S5 |

### 3.4 工作量粗估

| 组件 | 代码 | 算力 |
|------|------|------|
| 折分 + OOF + 患者 bootstrap | 小（1–2 人天） | 低 |
| **2 任务 × 5 折 × 三支** | 中（编排 2–4 人天） | **很大**（见 §3.2.1） |
| 恶性专用 pipeline config + 外测 | 中 | 中 |
| LLNM-Net / Tiger | 0 | 0 |

---

## 4. 推荐执行顺序（LNM + FTC 本期）

```text
Phase 0  两 packed 包各自 fold_indices.json（seed=42；LNM 与 Tiger/LLNM B9 同折约定）
Phase 1  LNM：E1 五折（三支/折）→ OOF；FTC：E3 五折 → OOF
Phase 2  LNM：E2 全量三支 → C2；FTC：E4 全量三支 → FangDai
Phase 3  B9_ThyroidXAgent_LNM结论.md + B9_ThyroidXAgent_FTC结论.md；S5 灰底两列
```

---

## 5. 交付物

| 文件 | 内容 |
|------|------|
| `runs/b9_txagent_lnm_cv/cv_summary.json` | OOF 患者/图像 AUROC、AUPRC、95% CI（**全栈最终分**） |
| `runs/b9_txagent_lnm_cv/oof_predictions.json` | 患者 ID、折号、概率、标签 |
| `runs/b9_txagent_lnm_cv/fold_*/` | 该折 DINO seg/cls（或联合 ckpt）、AG 目录、训练 config |
| `runs/b9_txagent_lnm_external/summary.json` | C2 患者级外测 |
| `runs/b9_txagent_ftcptc_cv/*`、`b9_txagent_ftcptc_external/*` | E3/E4（结构同 LNM） |
| `methods_snapshot.json` | (a)(b)(c)：增强、GLA、掩膜来源、路由规则、DINO 联合/分开训 |

---

## 6. 与专家 B9 的关系

| | LLNM-Net / Tiger | ThyroidXAgent B9 |
|---|------------------|------------------|
| 折分 | 同 packed | **同 patient_id 折** |
| S5 行 | 专家行 | **灰底 ThyroidXAgent** |
| 训练内容 | 单网络 | **DINO 分割 + DINO 分类 + AutoGluon + 路由** |

---

## 7. 风险

| 风险 | 缓解 |
|------|------|
| 联合训 vs 分开训与旧稿 checkpoint 不一致 | Phase 0 对齐历史权重结构；Methods 如实写 |
| 固定全数据掩膜做 radiomics | 折内用 **该折 DINO seg** 生成 mask，避免泄漏 |
| Cascade 仅有 BM `radiomics_judge` | 新建 `config_b9_lnm.yaml` 指向 LNM AutoGluon |
| 算力 | 可先 1 折冒烟再 5 折满跑 |

---

## 8. 决策记录

| 项 | 选择 | 日期 |
|----|------|------|
| S5 定义 | **ThyroidXAgent 1 seg + 2 cls + 路由** | 2026-10-23 |
| LNM 五折三支 | **DINO 分割 + DINO 分类 + AutoGluon / 折** | 2026-10-23 |
| DINO 联合 vs 分开 checkpoint | **联合 multitask**（`train_single_binary_with_mask`） | 2026-10-23 |
| DINO B9 代码位置 | **`Malignant_Cls_Model/b9/`** 编排，不重写训练主脚本 | 2026-10-23 |
| FTC E3/E4 本期 | **是**（与 LNM 同期） | 2026-10-23 |
| R2.12 E5 / F7 | 待定 | |

---

*版本：v1.4 · 2026-10-23 · §3.5 DINO 先行；`Malignant_Cls_Model/b9/README.md`*
