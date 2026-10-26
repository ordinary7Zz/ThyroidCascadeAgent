# B5 任务理解

**最后更新**：2026-10-26

---

## 1. 一句话

在与 **B3 波次 2**（`routing_mode=llm`，专家池、Phase 1–2 intermediate、Path B / AutoGluon 与投稿 **S4** 一致）**完全相同**的系统上，**只改变 LLM 路由器 prompt 里可见的元数据**，检验路由是否依赖 **设备/数据来源**（及可识别的中心信号），还是主要依赖 **病例质量与专家分歧**。

---

## 2. 科学问题（对应 R3.2）

审稿人担心：未见中心（如 NHC 各子中心）是否在 **推理阶段** 通过 prompt 里的扫描仪、数据集名称等，诱发 **中心级专家偏好**。

B5 要给出的证据类型：

| 证据 | 含义 |
|------|------|
| **性能消融** | 去掉某类元数据后，Dice / AUROC 变多少（5 mode × 各外测队列） |
| **主对比** | **`full → quality_only`** 的 Δ（回复信 R3.2 占位 **[X]/[Y]** 建议用这一对） |
| **选择模式** | **`full`** 下 **中心 × 专家** 频数热图；**互信息** 等简单关联（深度异质性归 **B7**） |

叙事边界：

- NHC 中心在 **训练权重** 里不能「背中心 ID」；B5 测的是 **推理 prompt 元数据** 是否改变选择与指标。  
- 若 **`drop_both` ≈ `full`** → 设备/来源对指标影响有限。  
- 若热图显示某中心集中选某一专家 → 如实报告，并讨论与构成、扫描仪混杂的可能。

---

## 3. 与相邻 B 任务的边界

| 任务 | B5 与之关系 |
|------|-------------|
| **B3** | B3 比较 **八种路由策略**；B5 **固定** seg/cls 均为 **LLM**，只扫 **`metadata_mode`**。B3 的 **`llm` 行 = B5 的 `full`**（可复用目录，免重复 API）。 |
| **B4** | B4 是 **L1 单专家 → L2 软投票 → L3 LLM 全系统** 的组件表；L3 与 B5 `full` 同配置，但 B4 **不**做元数据消融。 |
| **B6** | B6 提供 **可审计** 的 `routing_log.jsonl`、prompt 规范、稳定性；B5 全量跑数 **必须** `log_routing: true`，热图与互信息读日志。 |
| **B7** | B7 做 **中心级 I²、meta 回归** 等；B5 **不做** 这些，只做专家选择频率 + 互信息等轻量统计。 |

**明确不做**：新路由策略、重训专家、改 Phase 4 协议、改 B3 八策略表结构。

---

## 4. 五种 `metadata_mode`

配置取值（seg/cls **同值**）：

`full` | `drop_device` | `drop_source` | `drop_both` | `quality_only`

| Mode | 意图（通俗） |
|------|----------------|
| **full** | 与投稿 S4 / B3 `llm` 一致，全部元数据可见 |
| **drop_device** | 去掉设备相关（输入设备行、专家 `training_devices` 等） |
| **drop_source** | 去掉数据来源相关（`input_data_info`、`dataset_size` 等） |
| **drop_both** | 设备 + 来源两类都去掉，其余路由上下文保留 |
| **quality_only** | 不泄露来源/设备，尽量只留质量与分歧标量（radiomics 等会裁剪） |

**始终保留**：`model_name`（否则无法输出 `selected_model`）。关切的是 **可识别中心/设备的元数据**，不是匿名化专家代号。

分割 / 分类各字段在五种 mode 下的开关表见 [`REVISION_B5_PLAN.md` §4](../../REVISION_B5_PLAN.md)。

### `drop_both` vs `quality_only`

- **`drop_both`**：对应审稿人点名的两类元数据去掉后的 **性能** 回答。  
- **`quality_only`**：在同样不泄露来源/设备的前提下，**极简质量信号**；与 `full` 的差分用于 **「元数据整体贡献」** 主叙事。

---

## 5. 实验契约（冻结项）

与 [`REVISION_B3_B4_PLAN.md`](../../REVISION_B3_B4_PLAN.md) §3 对齐，B5 额外只动 `metadata_mode`：

| 项 | 约定 |
|----|------|
| Intermediate | **只读** `pipeline.ablation.shared_intermediate`，**不重跑** Phase 1–2 |
| 路由 | `enable_agent=true`，`routing_mode_seg=llm`，`routing_mode_cls=llm` |
| Path A 短路 | 分类全模型 `top_class` 一致 → **不调 LLM**；热图/互信息 **分母 = `llm_invoked=true`** |
| 输出 | **每个 mode 独立 `output_dir`**，禁止混用上一 mode 的 `selected_masks.npz` / `results.json` |
| LLM 超参 | 五种 mode **共用** temperature 等（不把解码随机性当成元数据效应） |
| 数据子集 | 多数队列用 `*_for_llm_malignancy` 子集（见 `config/revision/b5/README.md`）；`sample` / NHC 配置不同 |

---

## 6. 稿面与仓库交付物

| 稿面/回复 | 仓库产物（目标） |
|-----------|------------------|
| 补充表：5 mode × 队列性能 | `artifacts/b5_metrics_table.csv`（`build_b5_tables.py`） |
| 回复 Δ：`full → quality_only` | 同上或 `artifacts/b5_delta.json` |
| 补充图：中心 × 专家热图 | `figures/b5_*_heatmap.png`（至少 NHC **`full`**） |
| 回复关联统计 | `artifacts/b5_mutual_information.json` |
| Methods 一句 | `docs/supplementary/router_spec.md` 元数据消融段 |

---

## 7. 已知工程边界

（摘自 `REVISION_B5_PLAN.md` §13，实施时以代码为准。）

- **Path B** 里 LLM 裁决 JSON **未**做 metadata 消融；主文路由叙事在 **Phase 3 分割路由 + Path B 前分类路由**。  
- **`input_data_info`**：若未按队列/按图注入，分割侧 **`drop_source` / `drop_both` 可能几乎无差别**；B5 跑数前需核对 `pipeline.data` 与 NHC 标签合并逻辑（§7.2 详规）。  
- **NHC**：`labels.json` 路径与中心字段键名需与数据盘一致，否则 L1/B3/B5 均会失败；热图依赖可用标签 join `routing_log`。
