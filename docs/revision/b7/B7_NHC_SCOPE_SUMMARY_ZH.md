# B7 / NHC 返修结论摘要

**最后更新**：2026-10-26  
**范围**：NHC-MISD-TUS 在返修中的实验补全清单、元数据清单，及与 B2–B8 分工。

---

## 1. 审稿对应（B7 包内）

| 编号 | B7 负责 | 不归 B7 |
|------|---------|---------|
| **R2.6** | 队列与中心定义、描述表、中心级分割/分类表现、中心间异质性（I² 等） | — |
| **R1.3** | 中心间差异的承认、解释、个案（如 THYB_S_ZJ24、全腺体 Dice 偏低）；可选 meta 回归 | **校准 / 拒答 / 送复核** → **B8**（主表五 BM 外测；NHC 可另做 eval） |

---

## 2. 需要补充的实验（总表）

说明：**「重训」** = 重新训练模型；**「重跑 pipeline」** = 在 NHC 测试集上推理 + evaluate（可与 B3/B5/B8 **共用** `results.json`）；**「仅后处理」** = 已有逐图结果时只聚合统计。

### 2.1 B7 本体（R1.3 异质性 + R2.6 性能/异质性）

| 序号 | 内容 | 类型 | 是否重训 | 依赖 |
|------|------|------|----------|------|
| E7-1 | NHC 测试集 **逐图** 分割/分类指标（Dice、HD95、AUROC、AUPRC 等）+ **`center_id`** | 重跑 pipeline 或 **仅 evaluate**（若已有预测/GT 缓存） | 否 | `labels.json`、掩膜路径、与投稿一致的推理配置 |
| E7-2 | 按中心聚合 + **中心间 I²、τ²**（及可选 Q 统计） | 仅后处理 | 否 | E7-1 产出；`run_b7_analysis.py` |
| E7-3 | **中心内**变异（各中心内图像级指标的组内方差；I² 公式中的 within-center 分量） | 仅后处理 | 否 | 同上，必须 **图像级** 列表，不能只有 S7–S12 每中心一个点 |
| E7-4 | 可选：**meta 回归**（dice ~ 扫描仪/恶性比例/结节大小/质量代理等） | 后处理 + 协变量 | 否 | E7-1 + **§3 元数据** |
| E7-5 | 修订 **S7–S12**：小样本中心 **not estimable**、与 E7-1 对账 | 制表 | 否 | E7-1 或确认稿面表与现网结果一致 |
| E7-6 | 稿内 **九模型** NHC 对比（Fig. 2h、S7–S12 多模型列） | **一般不重跑** | 否 | 若需对账且缺存档，才在 NHC 上按原协议重跑各 baseline |

**若无存档的 `results.json` / `per_image_*.jsonl`**：E7-1～E7-3 **无法**从 `ThyroidXAgent.md` 单独完成，必须在可访问 NHC 的环境 **重跑 pipeline（或 evaluate）**；这不等于重训，但等于 **重新产生分析用输出**。

### 2.2 与 B7 同批 NHC 工作流、审稿常一并要求的实验（非 B7 任务号，但共享数据）

| 任务 | 序号 | 内容 | NHC | 重训？ | 审稿 |
|------|------|------|-----|--------|------|
| **B3** | E3-1 | 八策略路由消融（1–6、8；**7** 对齐主文全系统时可不重跑） | **要** | 否 | R1.2、R3.1 |
| **B5** | E5-1 | `metadata_mode=full` 全量 + **`routing_log`** → 中心×专家热图 | **要（至少）** | 否 | R3.2 |
| **B5** | E5-2 | 五 mode 性能 Δ（`full→quality_only` 等） | 可选在 NHC 全做；可主要在公开队列 | 否 | R3.2 |
| **B8** | E8-1 | 用 **已定 validation 阈值** 在 NHC 上 eval：**ECE、Brier、送复核比例**（建议按中心） | **建议** | 否 | R1.3（校准段） |
| **B2** | E2-1 | 簇 bootstrap **95% CI**、患者级分类（若有 ID） | **条件** | 否 | R1.1、R2.2 |
| **B4** | E4-1 | L1/L2/L3 组件消融 | 可选 | 否 | R2.8 |
| **B6** | — | 路由 prompt / 5× 稳定性 | **可不补 NHC** | — | R2.9 |

**共用建议**：在 NHC 上优先跑通 **`nhc_no_llm_primary.yaml`（或稿面主系统协议）** 的 `pipeline_run` → 同一 `results.json` 供 **B7、B8、B3 中间结果、B5（若与 B3 llm 分轨则另目录）**。

### 2.3 明确不需要在 NHC 上补的

- **B10** 基线公平性重训（针对 S3/S4 监督基线，非 NHC 专表）。
- **B6** 在 NHC 上重复 5× 路由（审稿未强制）。
- **B8 定阈**：在 OpenThyroid **validation** 完成即可，NHC 只 **应用阈值 eval**，不重定阈。

---

## 3. 需要补充的元数据

### 3.1 治理与稿面叙述（**G3**，R2.6 / R2.15）

| 字段 / 内容 | 用途 | 负责 |
|-------------|------|------|
| 35 个「中心」是否为 **独立参与医院**及关系说明 | Methods / Results 文字 | G3 + 共作者 |
| NHC **伦理 / DUA / 去标识化** 可写进稿的表述 | Data availability、R2.15 | G3、F9 |
| 队列级：**8,721** 的单位定义（病例 vs 图像）、与 **19,737** 测试图分层（配合 R2.3） | §2.1、数据流图 | G2/B12 |

### 3.2 中心描述表（R2.6 补充表，与 B7 绑定）

**每中心一行**（`center_id` 与 S7–S12、pipeline 一致，如 `THYB_S_ZJ24`）：

| 字段 | 必填 | 来源 |
|------|------|------|
| `center_id` | 是 | labels / manifest |
| **患者数** | 是（R2.6） | G3 或 labels 聚合 |
| **结节数** | 是 | G3 或 labels 聚合 |
| **图像数** | 是 | `build_nhc_center_table.py` 或 G3 |
| **扫描仪**（厂商/型号或类别） | 是 | G3 CSV |
| **标签可用性**（分割 / 良恶性 / 全腺体等） | 是 | G3 + labels |
| 可选：`province`、`hospital`、标注协议简述 | 建议 | G3 CSV（`build_nhc_center_table.py` 可 merge） |

脚本默认从 **labels** 还可导出：`n_labeled`、`n_malignant`、`malignant_ratio`（中心级构成，供 meta 回归）。

### 3.3 图像级 join 用 manifest（B7 / B8 / B3 共用）

见 `docs/supplementary/nhc_center_schema.md`：

| 字段 | 必填 |
|------|------|
| `stem` 或 `image_name` | 是 |
| `center_id` / `centre_id` | 是 |

或在 **labels.json** 每条含 `center_id`（及良恶性、掩膜路径等）。

### 3.4 可选（meta 回归、B7-4）

| 字段 | 层级 |
|------|------|
| 结节大小 / ROI 占比 | 图像（可由 GT 掩膜计算） |
| 图像质量代理（分辨率、对比度等） | 图像 |
| `patient_id` | 患者（**若有** → 触发 B2；无则 Methods 披露一图一簇） |
| 扫描仪 | 中心或图像（G3） |

### 3.5 当前仓库缺口（2026-10-26）

- NHC **本地数据路径 / `labels.json`** 未就绪（B1 审计 TBD）。
- **`imgs_sup/per_center_tables.tex`** 未入库，无法仅从 `ThyroidXAgent.md` 复算 I²。
- **G3 CSV** 需院方/孔老师侧提供后 `--g3-csv` 合并。

---

## 4. B7 交付物（实验 + 元数据 → 稿面）

| 交付 | 输入 |
|------|------|
| 新/修订 **Supp. 中心描述表** | §3.2 + §3.3 |
| **I²、τ²**（分割/分类分任务报告） | E7-1～E7-3 |
| 可选 Supp. Fig.（中心性能分布、meta 回归） | E7-4 |
| Results 段落（极差、ZJ24、全腺体 vs 结节） | E7-1 + 稿面 S7–S8 |
| 修订 S11/S12（not estimable） | E7-5 |
| 回复信 R2.6 + R1.3 异质性段 | 以上全部 |

---

## 5. 执行顺序（简）

1. **§3 元数据** + NHC 数据盘、`labels.json`、center manifest  
2. **E7-1**（或找回存档 `results.json`）→ **E7-2、E7-3**  
3. **§3.2 描述表**（`build_nhc_center_table.py`）  
4. 并行：**E3-1 B3**、**E5-1 B5**、**E8-1 B8**、条件 **E2-1 B2**  
5. 改稿、对账 S7–S12、回复信  

---

## 6. 仓库入口

| 路径 | 说明 |
|------|------|
| `config/revision/nhc_no_llm_primary.yaml` | B7/B8 冻结 no-LLM 协议示例 |
| `scripts/revision/b7/build_nhc_center_table.py` | 中心描述表 |
| `scripts/revision/b7/run_b7_analysis.py` | 按中心聚合 + I² |
| `docs/revision/暂定的修改和回复计划/B_DELIVERABLES_CHECKLIST_ZH.md` § B7 | 清单状态 |

**版式说明**：NHC 可不进正文 Table S3/S4；B3/B7/B8 等 NHC 结果可放 **Supp. 专节 + 回复信**，与 OpenThyroid 主表并列叙述。
