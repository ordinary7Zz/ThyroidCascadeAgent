# 补充数据流图 — 设计计划（B12 + S9，对应 R1.4 / R3.3 / G2）

> **图源文件**：[`DATAFLOW_FIGURE.mmd`](DATAFLOW_FIGURE.mmd)（Mermaid，可用 [mermaid.live](https://mermaid.live) 或 VS Code 插件导出 SVG/PDF）。  
> **占位符 `[B1]` / `[S9]`** 须在定稿前由数据审计与报告负责人填入患者级互斥结论、模板库精确划分。

---

## 1. 图的目标与受众

审稿人需要一眼看出：

1. **每个组件**（分割专家池、分类专家池、AutoGluon radiomics、LLM 路由器、报告模板库、LNM/FTC 头）**用了哪些数据做 train / val / threshold / test**。
2. **ZJH-8K** 在「外测分割/分类」与「恶性子集开发 LNM/FTC」上的 **双重角色** 被显式分开，避免误解为泄漏。
3. **验证集 850 张** 与 **SMU-HMC 400 患者测试** 等 **患者级留出** 与图像级 test 不混为一谈。
4. **操作阈值** 标在 **Validation** 或 **Fixed hyperparameter**，测试集箭头旁写 **evaluate only**。

建议作为 **Supplementary Figure S[X]**（全宽两页或单页双栏），正文 Methods 4.1 引用一次；与 **Fig. 1a**（资源总览）分工：Fig. 1 = 队列地图；本图 = **组件 × 划分**。

---

## 2. 推荐版面（单图五带）

自上而下或从左到右 **五条泳道**，统一图例放在底部。

| 泳道 | 标题 | 负责人 | 内容 |
|------|------|--------|------|
| **A** | Data pools & splits | B1 + 稿面 S1 | 队列方块 + train/val/test 数字（来自 Table S1） |
| **B** | Image: seg / cls / radiomics | B12 | 训练箭头 + 推理五阶段 + 测试队列 |
| **C** | Report generation | S9 | SMU-HMC / KMVE / ZJH-TS / TNVideo + 两套模板库 |
| **D** | Malignant-lesion tasks | B9 + B12 | ZJH-8K 恶性、LymphUs、Dai 外测 |
| **E** | Private multicentre test | G3 + B7 | NHC-MISD-TUS（35 中心，仅测试） |

**视觉编码（定稿时统一）**

| 样式 | 含义 |
|------|------|
| 实心蓝框 | Training / fitting |
| 实心橙框 | Validation（选专家、拟合路由/拒答阈） |
| 实心绿框 | Test / external evaluation only |
| 虚线框 | 与另一任务 **共享同一批图像**（须在旁注说明） |
| 红色 ⊘ | 明确 **禁止** 进入训练（外部队列） |
| 细字标签 | 阈值名 + 数值 +「fitted on val」|

---

## 3. 泳道 A — 数据池（稿面数字，待 B1 核对患者级）

### 图像分割 + 良恶性分类（OpenThyroidDB 七队列）

| 队列 | Train | Val | Test | 备注 |
|------|-------|-----|------|------|
| TN3K | 4,633 img | 100 | 614 | 内部分割+分类 |
| TN5K | 3,500 | 500 | 1,000 | |
| ThyroidXL | 9,441 | 100 | 2,090 | |
| PKTN | 703 | 150 | 150 | 仅分割 |
| DDTI | — | — | 637 seg / 349 cls | 外部，⊘ train |
| RJH-7K | — | — | 7,288 seg | 外部，⊘ train |
| ZJH-8K | — | — | 7,958 | 外部测试；**恶性 4,756 另见泳道 D** |
| **合计** | **18,277** | **850** | **19,737** | Methods 2.1 |

**堆叠训练集**：多队列 train 合并 → 最大堆叠 **18,277** → 训练 `all_datasets` 等专家（Supp. Fig. expert pool）。

**统一 Val 850**：用于 **best_single**、**learned router**、**B8 abstention/calibration**（仅 val fit）。

### 报告（四队列，泳道 C 展开）

| 队列 | 开发/训练用途 | 验证 | 测试 |
|------|----------------|------|------|
| SMU-HMC | 除 400 患者外 → 组件开发；**7,147** 报告 → 模板库 A | — | **400 患者 / 5,984 图** |
| KMVE | train **1,719** + 模板库 B 构建 | **246** | **492** |
| ZJH-TS | ⊘ | ⊘ | **150** 报告（外院） |
| TNVideo | ⊘ | ⊘ | **148** 检查（读者研究，**145** 有标签） |

`[S9]`：两模板库是否重叠患者、KMVE train 与 template 是否同一子集，须在图旁脚注。

### 私有外测

| NHC-MISD-TUS | ⊘ train | ⊘ val | **8,721 cases / 35 centres** test |

---

## 4. 泳道 B — 图像分析组件数据流

### 训练阶段（箭头从泳道 A 的 Train/Stack 出发）

```
Stacked train (~18,277) ──► Seg expert pool (all_datasets, TN3K, TN5K, ThyroidXL, PKTN checkpoints)
Stacked train ──► Cls expert pool (multitask UNets, 同架构不同数据)
dataset_3 GT masks (17,774 img) ──► PyRadiomics features ──► AutoGluon Tabular (fit, 600s, 8-fold, val=AUTOGLUON internal CV)
```

- **无** radiomics 前 CCA（与代码一致）；专家内部 0.5 / ≥50 px / closing 标在 **expert inference** 小框，不连到 AutoGluon。

### 验证阶段（从 Val 850）

| 组件 | 在 Val 850 上做什么 |
|------|---------------------|
| best_single seg/cls | 选最优单专家（Dice / AUROC） |
| Learned router | 拟合 `learned_router_*.joblib` |
| B8 | `abstention_thresholds.json`、可选温度缩放 |
| LLM 路由（主文 S4） | **建议**：与投稿一致时在 **独立 val 协议** 上标出；NHC 无 LLM 配置单独虚线 |

### 测试阶段（箭头到泳道 A 各 Test 框 + NHC）

**推理链**（与 `pipeline/cascade.py` 一致，画在 B 泳道右侧竖条）：

1. Phase 1：Seg experts → masks  
2. Phase 2：Cls experts → probs  
3. Phase 3：Router → **selected_masks**（+ optional RadiomicsJudge 信号）  
4. Phase 4：PyRadiomics(selected) → AutoGluon  
5. Phase 5：Consensus / Path B (+ LLM if S4) → label  

每个 **Test 队列** 一根箭头进入该竖条，出口写 **Table S3/S4 metrics**。

### 主文指标聚合（角注框）

- 五队列分类 test：**unweighted mean** AUROC 0.9001 / AUPRC 0.8705  
- 可选：sample-weighted 0.9228 / 0.9533  

---

## 5. 泳道 C — 报告生成（S9）

```
SMU-HMC (excl. 400-pt test) ──► 报告组件 / 工具训练
SMU-HMC 7,147 QC reports ──► Template library A (BM25 retrieval)
KMVE train 1,719 ──► Template library B (+ 与 train 关系 [S9 标注])

Case evidence (from image branch or priors) ──► Planner/Executor ──► Slot fill + clause assembly ──► Report R

Test:
  SMU-HMC 400 patients ──► eval (Table S14)
  KMVE test 492 ──► eval
  ZJH-TS 150 ──► external eval
  TNVideo 148 ──► reader study (not necessarily same metric table)
```

**勿画**「图像 test 集直接进模板库」除非 S3 审计证明无泄漏；若有患者 ID 去重，在 Template library 旁画 **S3 audit** 盾牌图标。

---

## 6. 泳道 D — 恶性病灶任务（与 ZJH-8K 交叉）

用 **虚线双色框** 包住 ZJH-8K malignant **4,756 images**：

| 用途 | 划分 |
|------|------|
| Seg/Cls **external test** | 7,958 全量 test（含良性） |
| LNM / subtype **development** | 4,756 malignant；**183 img / 20 cases val** |
| LNM train 增强 | + LymphUs **C1 180** → 合计 **4,753**（稿面数字以 B9 定稿为准） |
| LNM **external test** | LymphUs **C2 158** |
| FTC/PTC **external test** | Dai **200** |

FTC/PTC 训练标签定义旁注 **[F7 / 病理确认]**。

---

## 7. 泳道 E — NHC

- 输入：仅 **test** 箭头接图像推理链（**无 LLM** 或单独子图，与 `nhc_no_llm_primary.yaml` 一致）。  
- 输出：中心级 Dice/AUROC（S11–S12）、B7 异质性。  
- G3：中心元数据表 → 挂在 NHC 框下方。

---

## 8. 制图工作流（建议）

| 步骤 | 工具 | 产出 |
|------|------|------|
| 1 | 编辑 `DATAFLOW_FIGURE.mmd` | 逻辑定稿 |
| 2 | mermaid.live → SVG | 矢量底稿 |
| 3 | Figma / Illustrator / BioRender | 统一字体、色盲友好、加 ⊘ 与脚注 |
| 4 | B1 填 `[B1]` 脚注 | 患者互斥声明 |
| 5 | S9 填模板库箭头 | 与 S3 表一致 |
| 6 | 全文 cross-ref | Supp. Fig. S[X], Methods 4.1 |

**不要**在一张图里画清每一个超参数；阈值列表用 **Supp. Table S[Y]**，主图只标 **类别**（Val-fit vs fixed）。

---

## 9. 本仓库尚不能自动完成的部分

- 患者级互斥的最终措辞（B1）  
- 模板库与测试集 MinHash 结论（S3）在图上的脚注  
- NHC 35 中心是否等于 35 家医院（G3）  
- 主文 LLM 路由 val 协议与 850 张是否同一集合的 **最终 Methods 表述**

以上在 `DATAFLOW_FIGURE.mmd` 中以 `%% TODO` 或 `[B1]` 保留。
