# B5　路由元数据消融（实现计划）

> **对应审稿意见**：R3.2（Reviewer 3 Major 2：元数据与中心特异偏好）  
> **负责人（稿面）**：Baidong  
> **主交付物**：补充表（5 种 metadata 配置 × 测试集性能）+ 补充图（中心 × 专家选择热图）+ 回复信中的 Δ 与中心–专家关联统计  
> **关联文档**：`docs/ThyroidXAgent_返修计划与回复_中文.md`（A4 B5）、`docs/REVISION_B3_B4_PLAN.md`（实验契约）、`docs/REVISION_B5_B6_B8_B11_PLAN.md`（B5/B6 摘要）、`docs/REVISION_B6_PLAN.md`（`routing_log.jsonl`）

---

## 1. 任务一句话

在 **与 B3 波次 2（`routing_mode=llm`）完全相同的专家池与 intermediate** 上，只改变 LLM 路由器 **可见的元数据字段**，回答：

> 路由是靠 **病例级质量/分歧信号**，还是靠 **数据来源、扫描仪等设备元数据**（乃至隐性的中心偏好）？

**B5 不是**再跑八种路由策略（那是 B3）；**B5 是**在 **固定 LLM 路由** 下做 **五种输入消融**，并做 **选择模式** 分析。

---

## 2. 前置条件与依赖

| 依赖 | 状态 / 要求 |
|------|-------------|
| **B3 共享地基** | 各 `dataset_id` 已有 `pipeline_run/intermediate`（Phase 1–2 专家输出）；与 B3 使用 **同一 manifest**（`intermediate_manifest.json`） |
| **B3 波次 2 基线** | `routing_mode_seg=llm`、`routing_mode_cls=llm`，Path B 与投稿 S4 一致（含 Phase 4 AutoGluon + LLM 全信号）。`metadata_mode=full` 的指标 **可与 B3 的 `llm` 目录复用**，避免重复调 API |
| **B6 路由日志** | `pipeline.log_routing: true` → `routing_log.jsonl`（**已实现**）。B5 全量跑数时 **必须开启**，供热图与样例审计 |
| **B2 cluster bootstrap** | 投稿前主表 CI 须与 B2 一致；开发期可先用 `pipeline/evaluate.py` 图像级 bootstrap，定稿前重算 |
| **B7** | 中心级 I²、meta 回归等 **不在 B5**；B5 只报告 **专家选择频率 + 简单关联统计**（互信息等） |

**建议顺序**：B6 已就绪 → 实现 B5 的 `metadata_mode` 屏蔽逻辑 → 小队列试跑（`sample`）→ 全队列 5 mode × LLM 重跑 Phase 3–5 → 汇总表与热图。

---

## 3. 实验契约（与 B3 对齐，仅多一维 `metadata_mode`）

以下在 B5 全部运行中 **冻结**（与 `REVISION_B3_B4_PLAN.md` §3 一致）：

| 项 | B5 约定 |
|----|---------|
| 专家池 | 与 Table S3/S4 / `config/b3/<cohort>.yaml` 一致 |
| Intermediate | **只读链接** `pipeline.ablation.shared_intermediate`；**不重跑** Phase 1–2 |
| 路由策略 | **固定** `seg=llm`、`cls=llm`（`enable_agent=true`） |
| 一致短路 | 分类 Path A（全模型 `top_class` 一致）**不调 LLM** → 与现网一致；热图与互信息 **仅统计实际调用 LLM 的记录**（`llm_invoked=true`），并在补充中注明分母 |
| 输出目录 | **每个 `metadata_mode` 独立 `output_dir`**（推荐），或同一目录 + `--force-phase3`；禁止复用上一 mode 的 `selected_masks.npz` / `results.json` |
| 测试覆盖 | 与 B3 相同的全测试队列，**含 NHC-MISD-TUS** |
| 唯一变量 | `segmentation.agent.metadata_mode` 与 `classification.agent.metadata_mode`（两侧 **同值**） |
| LLM 超参 | 与 B3 波次 2 / `shared.agent_llm` 一致；**五种 mode 共用同一 temperature 等**，避免把解码随机性当成元数据效应 |

---

## 4. 五种 `metadata_mode`（语义与字段级规范）

配置取值：`full` | `drop_device` | `drop_source` | `drop_both` | `quality_only`。

实现时建议集中在一个模块（如 `shared/metadata_prompt.py`）做 **纯函数** 变换，seg/cls agent 共用，并附 **单元测试**（给定 fixture JSON → 期望字段存在/缺失）。

### 4.1 分割（`segmentation/agent.py`）

LLM 输入由三部分组成：**user 前缀行**（设备/数据）、**JSON `format_predictions_for_agent`**、**system**（`brief_routing_prompt` 时较短）。

| 信号 | 典型位置 | full | drop_device | drop_source | drop_both | quality_only |
|------|----------|------|-------------|-------------|-----------|----------------|
| 输入设备行 `**输入设备**` | user 前缀 | ✓ | ✗ | ✓ | ✗ | ✗ |
| 输入数据行 `**输入数据**` / `input_data_info` | user + JSON 顶栏 | ✓ | ✓ | ✗ | ✗ | ✗ |
| 专家 `training_devices` | 每模型 JSON | ✓ | ✗ | ✓ | ✗ | ✗ |
| 专家 `dataset_size`（来自 `dataset_info`） | 每模型 JSON | ✓ | ✓ | ✗ | ✗ | ✗ |
| 掩膜质量 `mask_statistics` | 每模型 JSON | ✓ | ✓ | ✓ | ✓ | ✓ |
| 组内分歧 `group_uncertainty` / `disagreement` | JSON | ✓ | ✓ | ✓ | ✓ | ✓ |
| `agreement_with_others` | 每模型 JSON | ✓ | ✓ | ✓ | ✓ | ✓（可选保留） |
| `mean_confidence` | 每模型 JSON | ✓ | ✓ | ✓ | ✓ | ✓ |
| `radiomics_judge`（含 `top_features`） | 每模型 JSON | ✓ | ✓ | ✓ | ✓ | **仅** `malignant_prob` + `confidence`（去掉 `top_features`） |
| `classification_anchor` 长文案 | JSON | brief 下为短字段 | 同左 | 同左 | 同左 | **仅** `class` 或 null（去掉 `source`/`usage` 叙事） |

`model_name` 在五种 mode 下 **均保留**（否则无法输出 `selected_model`）；审稿关切的是 **中心可识别元数据**，不是匿名化专家名。

### 4.2 分类（`classification/agent.py`）

| 信号 | 典型位置 | full | drop_device | drop_source | drop_both | quality_only |
|------|----------|------|-------------|-------------|-----------|----------------|
| user 行 `输入设备: …` | user 前缀 | ✓ | ✗ | ✓ | ✗ | ✗ |
| `predictions[].metadata.training_devices` | JSON | ✓ | ✗ | ✓ | ✗ | ✗ |
| `predictions[].metadata.dataset_size` | JSON | ✓ | ✓ | ✗ | ✗ | ✗ |
| `top_class` / `top_confidence` / `class_probabilities` | JSON | ✓ | ✓ | ✓ | ✓ | ✓ |
| `entropy` / `margin_top2` / `num_models_same_class` | JSON | ✓ | ✓ | ✓ | ✓ | ✓ |
| `top_confidence_calibrated` | JSON | ✓ | ✓ | ✓ | ✓ | ✓ |
| 顶层 `vote_entropy` | JSON | ✓ | ✓ | ✓ | ✓ | ✓ |
| system 中「设备匹配」等规则句 | system | brief 时已弱化 | 若仍引用设备，在 non-brief 下按 mode **裁剪 system 附录** | 同左 | 同左 | 使用 `brief_routing_prompt: true` 或 mode 专用短 system |

**现状缺口（须在 B5 中补齐）**：

1. `metadata_mode` 仅写入配置与 `routing_log`，**未**改变 prompt 内容。  
2. `input_data_info` 在 `run_pipeline` / `run_routing_ablation` 中 **未从 `pipeline.data` 注入**；分割侧 `data_text` 在缺省时常为空对象。B5 实施时需定义 **每队列 `input_data_info` 构造规则**（见 §7.2）。

### 4.3 `drop_both` vs `quality_only`（论文叙事）

- **`drop_both`**：审稿人点名的两类元数据（来源 + 设备）去掉，**其余路由上下文保留** → 回答「去掉这两类后性能变多少」。  
- **`quality_only`**：在同样不泄露来源/设备的前提下，**尽量只留质量与分歧标量** → 与 `full` 的 Δ 作为「元数据整体贡献」主对比；回复草稿 R3.2 中的 **[X]/[Y]** 建议用 **`full → quality_only`**。

---

## 5. 代码现状与目标架构

```
config/b5/<cohort>.yaml
        │
        ▼
scripts/revision/b5/run_b5_batch.py  ──►  scripts/run_routing_ablation.py  (+ --metadata-mode)
        │                              │
        │                              ├── link_shared_intermediate (同 B3)
        │                              ├── routing_mode=llm (两侧)
        │                              └── CascadePipeline.run_batch (Phase 3–5)
        │
        ▼
output/ablation/b5/<cohort>/<metadata_mode>/
        ├── results.json
        ├── b3_metrics.json  (或 b5_metrics.json，字段增加 metadata_mode)
        ├── routing_log.jsonl
        └── intermediate_manifest.json

scripts/revision/b5/build_b5_tables.py  ──►  artifacts/b5_summary.csv / .json
pipeline/analyze_routing_bias.py  ──►  figures/b5_centre_expert_heatmap.png + mi.json
```

### 5.1 待新建 / 待修改文件

| 优先级 | 文件 | 动作 |
|--------|------|------|
| P0 | `shared/metadata_prompt.py` | 五种 mode 的字段过滤；seg JSON / cls JSON / user 前缀行 |
| P0 | `segmentation/agent.py` | `format_predictions_for_agent`、`select_best_mask`（LLM 路径）调用过滤 |
| P0 | `classification/agent.py` | `format_predictions_json` / `_build_compact_prediction_dicts`、`select_best_model` 调用过滤 |
| P0 | `pipeline/routing_ablation.py` | `apply_metadata_mode_to_config`；`prepare_ablation_run` 接受 `metadata_mode` |
| P0 | `scripts/run_routing_ablation.py` | CLI `--metadata-mode`；metrics 写入 `metadata_mode` |
| P1 | `scripts/generate_ablation_configs.py` | 生成 `config/b5/<cohort>.yaml`（`output_root: output/ablation/b5/...`，固定 llm） |
| P1 | `scripts/revision/b5/run_b5_batch.py` | 8 队列 × 5 mode；可选 `--skip-full`（复用 B3 `llm`） |
| P1 | `pipeline/analyze_routing_bias.py` | 热图 + 互信息 |
| P1 | `scripts/revision/b5/build_b5_tables.py` | 宽表 + Δ 列 |
| P2 | `pipeline/ablation_metrics.py` | `build_b5_metrics` 或在 `build_b3_metrics` 增加 `metadata_mode` 字段 |
| P2 | `tests/test_metadata_prompt.py` | 五种 mode 快照测试 |
| P2 | `docs/supplementary/router_spec.md` | 增补「元数据消融」字段表（可脚本导出） |

**明确不做**：新路由策略、重训专家、改 Phase 4 协议、改 B3 八种策略表结构。

---

## 6. 跑数流程（操作手册草案）

### 6.1 一次性准备

```bash
# 各队列 Phase 1–2（若尚未有 intermediate）
python run_pipeline.py --config config/config_<队列>.yaml

# 生成 B5 配置（实现 generate_ablation_configs 后）
python scripts/generate_ablation_configs.py   # 增加 --b5 或默认同时写 b5/
```

### 6.2 单队列、单 mode（调试）

```bash
python scripts/run_routing_ablation.py \
  --config config/b5/sample.yaml \
  --routing-mode llm \
  --metadata-mode drop_device \
  --task both \
  --shared-intermediate output/sample/pipeline_run/intermediate \
  --output-dir output/ablation/b5/sample/drop_device \
  --force-phase3
```

（`--metadata-mode` 为计划 CLI；实现前须先完成 §5.1 P0。）

### 6.3 批量

```bash
python scripts/revision/b5/run_b5_batch.py --config config/b5/sample.yaml
# 或全队列：
for c in sample tn3k tn5k thyroidxl zjh8k rjh7k ddti nhc_misd_tus; do
  python scripts/revision/b5/run_b5_batch.py --config config/b5/$c.yaml
done
```

**API 与成本**：仅 **Path B 且 LLM 被调用** 的病例消耗 token；全测试集 × 4 个新 mode（若 `full` 复用 B3）仍可能很大。建议：

- 开发： `pipeline.data.max_images` 截断 + `sample` 队列；  
- 生产：串行 `--jobs 1`，夜间批跑；日志落盘便于断点续跑（按 `output_dir` 检查 `results.json` 是否完整）。

### 6.4 汇总与分析

```bash
python scripts/revision/b5/build_b5_tables.py --root output/ablation/b5
python pipeline/analyze_routing_bias.py \
  --log output/ablation/b5/nhc_misd_tus/full/routing_log.jsonl \
  --labels <NHC labels 路径> \
  --centre-key <字段名> \
  --out figures/b5_nhc_centre_expert.png
```

---

## 7. 中心标签与 `input_data_info`（数据契约）

### 7.1 热图的分组键 `centre_id`

| 队列 | 建议分组键 | 来源 |
|------|------------|------|
| NHC-MISD-TUS | 中心 ID（如 `THYB_S_*`） | `labels.json` 列表项中的中心字段（实现时读一条样本确定键名，写入 `config/b5/nhc_misd_tus.yaml` 的 `pipeline.ablation.centre_key`） |
| 单中心队列（TN3K、ZJH-8K 等） | 常数 `dataset_id` | 配置中的 `dataset_id`；热图退化为单列，互信息为 0 或省略，在补充中说明 |
| 多源混合 | `dataset_id` 或标签内医院字段 | 与稿面「各中心」表述一致即可 |

`analyze_routing_bias.py` 通过 `image_name` stem join 标签；`routing_log.jsonl` 可增加可选字段 `centre_id`（pipeline 写入，便于复现）。

### 7.2 `input_data_info` 构造（使 `drop_source` 有意义）

在 `config/b5/<cohort>.yaml` 的 `pipeline.data` 中增加例如：

```yaml
pipeline:
  data:
    device_info: ["GE Logiq E9", "GE S7"]
    input_data_info:
      dataset_name: "TN3K"
      cohort: "test"
```

对 NHC，宜 **按图** 注入中心（在 `cascade.run_batch` 循环内从 labels 条目合并到 `input_data_info`），避免全队列写死单一来源。此为 B5 的 **小改动**：`run_batch` 接受 per-image `input_data_info` 或在加载 labels 时保留完整条目。

---

## 8. 论文与回复信产出映射

| 稿面/回复 | 仓库产物 |
|-----------|----------|
| 补充表：5 mode × 队列 Dice/AUROC (+ CI) | `artifacts/b5_metrics_table.csv`（由 `build_b5_tables.py`） |
| 回复 [X][Y]：`full → quality_only` Δ | 同上表中的差分行或 `artifacts/b5_delta.json` |
| 补充图：中心 × 专家热图 | `figures/b5_*_heatmap.png`（至少 NHC **full**；可选 4 mode 分面） |
| 回复 [Z]：互信息 / 关联 | `artifacts/b5_mutual_information.json` |
| Methods 一句 | 引用 `docs/supplementary/router_spec.md` 元数据消融段 |

**叙事要点**（与 `ThyroidXAgent_返修计划与回复_中文.md` R3.2 草稿一致）：

- NHC 中心在开发期未见 → 无法在训练权重里背中心 ID；B5 检验的是 **推理时 prompt 元数据** 是否诱发中心级选择。  
- 若 `drop_both` 与 `full` 接近 → 设备/来源对指标影响有限。  
- 若热图显示某中心高度集中选某一专家 → 如实报告，并讨论与病例构成、扫描仪混杂的可能（深度分析可指向 B7）。

---

## 9. 测试与验收

### 9.1 自动化

- `tests/test_metadata_prompt.py`：五种 mode 下 seg/cls payload 无禁止字段（如 `drop_device` 无 `training_devices`）。  
- 可选：mock LLM，断言 `routing_log` 中 `metadata_mode` 与 prompt 一致（`routing_log_include_prompts: true` 仅样例跑）。

### 9.2 验收 checklist（B5 完成标准）

- [ ] 八种 `dataset_id`（与 B3 一致）均有 **5 种 mode** 的 `results.json` + `b3_metrics.json`（或 `b5_metrics.json`）。  
- [ ] `full` 与 B3 `llm` 跑在 **同一 intermediate manifest** 上，指标差异仅允许浮点/LLM 随机（若完全复用目录则差异为 0）。  
- [ ] NHC `full` 的 `routing_log.jsonl` 可生成 **中心 × 专家** 热图。  
- [ ] `build_b5_tables.py` 输出 `full → quality_only` 的 ΔDice、ΔAUROC，可填入回复信占位符。  
- [ ] 补充材料中注明：互信息/热图 **分母**（仅 `llm_invoked` 记录；seg/cls 分列或分 task）。

---

## 10. 风险与开放问题

| 风险 | 缓解 |
|------|------|
| `input_data_info` 长期为空 → `drop_source` 与 `drop_both` 在分割侧几乎无差别 | §7.2 按队列/按图注入；在计划验收前用 `routing_log_include_prompts: true` 抽查 3 例 |
| 分类侧从未传 `input_data_info` | B5 一并接入；`drop_source` 主要体现为去掉 `dataset_size` |
| LLM 成本 | 复用 `full`；非 NHC 可先完成再跑 NHC；`max_images` 开发 |
| 专家名本身可暗示训练数据 | 稿面如实写；`quality_only` 仍保留 `model_name`（工程必要）。若审稿追问，可在讨论中说明未改专家命名 |
| B2 未就绪 | 表内先标「图像级 bootstrap CI」；B2 完成后重跑 `evaluate` 汇总脚本即可 |

**待 Griffin / 数据侧确认**：

- NHC `labels.json` 中心字段正式键名与是否允许写入 `input_data_info`。  
- 各院内队列是否在标签中提供 **扫描仪型号**（若无，则 `drop_device` 主要依赖 `pipeline.data.device_info` 常量行）。

---

## 11. 实施排期（建议人日）

| 阶段 | 内容 | 估时 |
|------|------|------|
| A | `shared/metadata_prompt.py` + agent 接入 + 单测 | 1–2 d |
| B | `routing_ablation` / CLI + `config/b5` + `run_b5_batch` | 0.5–1 d |
| C | `input_data_info` per-image（cascade + labels 全条目缓存） | 0.5–1 d |
| D | `sample` 全 mode 试跑 + prompt 抽查 | 0.5 d |
| E | 全队列跑数（含 API 等待） | 2–5 d（视规模） |
| F | `analyze_routing_bias` + `build_b5_tables` + 图 | 1 d |

---

## 12. 文档维护

- B5 实现落地后：在根目录 `README.md` 增加一节「B5 元数据消融」链到本文与 `run_b5_batch.py`。  
- 若 `export_router_spec.py` 已导出 router 说明，增加 **Metadata ablation** 小节，与 §4 字段表同步。

---

*文档版本：2026-10-15；与仓库 B3/B4 已合并分支对齐。*

---

## 13. 实现状态（代码）

| 项 | 路径 | 状态 |
|----|------|------|
| 字段过滤 | `shared/metadata_prompt.py` | 已实现 |
| Agent 接入 | `segmentation/agent.py`, `classification/agent.py` | 已实现 |
| CLI | `scripts/run_routing_ablation.py --metadata-mode` | 已实现 |
| 批量 | `scripts/revision/b5/run_b5_batch.py` | 已实现 |
| 配置 | `config/b5/*.yaml`（`generate_ablation_configs.py`） | 已实现 |
| 汇总 | `scripts/revision/b5/build_b5_tables.py` | 已实现 |
| 偏倚分析 | `pipeline/analyze_routing_bias.py` | 已实现（热图需 matplotlib） |
| 单测 | `tests/test_metadata_prompt.py` | 已实现 |
| Path B LLM prompt | `resolve_path_b` 裁决 JSON | **未**做 metadata 消融（主文路由在 Phase 3 seg + Path B 前独立分类路由） |
