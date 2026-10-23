# B6　路由器透明性与可复现性（Router transparency）

> 对应审稿意见：**R2.9**  
> 范围：**ThyroidCascadeAgent**；专家模型不重训。  
> 原文要求：*Router transparency: full prompt, LLM name/version, decoding parameters, JSON schema; repeat routing [5] times per case and report selection agreement and metric variance, stratified by how close the candidates were; at least 10 structured routing records.*

---

## 审稿要求解读（三条）

| # | 要求 | 要回答的问题 |
|---|------|----------------|
| 1 | **规格公开** | 路由器用了什么 prompt、什么模型、什么解码参数、输出 JSON 长什么样？能否复现？ |
| 2 | **5× 稳定性** | 同一病例、同一组候选，重复路由 5 次，选的专家/类别是否一致？Dice/AUROC 会抖多少？**候选很接近** vs **差距大**时是否不同？ |
| 3 | **≥10 条结构化记录** | 每条决策能否对照「输入数字 ↔ LLM 输出 ↔ 对错」，而非只看 `reasoning` 散文？ |

**注意（与 Cascade 行为一致）**

- 分类 **一致短路**（独立模型 top_class 一致）→ **不调用 LLM**，重复 5 次必然 100% 一致 → **稳定性分析仅针对「曾调用 LLM」子集**，或单独报告 deterministic 比例。
- 默认 `enable_agent: false` 时无 LLM 路由 → B6 实验需 **`enable_agent: true`**（分割/分类按返修实验配置），或单独跑稳定性子集。
- **5× 重复**指 **重跑路由（Phase 3/5 或 Agent）**，在 **复用 `intermediate/seg`、`intermediate/cls` 缓存** 的前提下进行，不重跑全部分割/分类模型。

---

## 实施顺序

```
① 规格文档（可从代码导出，可不跑 GPU）
        ↓
② routing_log.jsonl（全 pipeline 带审计，含非 LLM 路径）
        ↓
③ run_routing_stability.py（分歧/LLM 子集，5× 路由 + 分层统计）
        ↓
④ 从日志筛选 ≥10 条 → 补充表 + 回复 R2.9 段落
```

---

## 代码修改计划

### A. 配置（`config/config.yaml` 及 `config_test.yaml`）

```yaml
pipeline:
  log_routing: true
  routing_log_path: null          # null → {output_dir}/routing_log.jsonl
  routing_log_include_prompts: false  # true：每条存完整 system/user（体积大，仅调试或样例）

segmentation:
  agent:
    enable_agent: true            # B6 稳定性实验配置；日常可 false

classification:
  agent:
    enable_agent: true            # Path B 才进 LLM；Path A 仍记日志但 llm_invoked=false
```

### B. 新建 `shared/routing_log.py`

| 职责 |
|------|
| `RoutingLogger(path, enabled)` |
| `log(record: dict)` → append JSONL，UTF-8，`flush` |
| 可选：`redact()` 确保无患者可识别信息 |

**不在此模块调用 LLM**，只写盘。

### C. `segmentation/agent.py` — `select_best_mask`

| 修改点 |
|--------|
| `__init__` 增加 `routing_logger: Optional[RoutingLogger] = None` |
| 参数增加 `image_name: Optional[str] = None`（由 `cascade` 传入） |
| 在 **每条出口** 调用 `_emit_routing_log(...)`：`enable_agent=False` → fallback；LLM 成功；LLM 失败 → fallback |

**建议单条记录字段**

| 字段 | 说明 |
|------|------|
| `image_name`, `task`=`seg` | |
| `path`, `classification_anchor`, `classification_consensus` | A/B、锚点 |
| `llm_invoked`, `method` | `llm` / `static_fallback` / `ensemble` |
| `disagreement_tier` | `easy` / `close`（见下「分层规则」） |
| `candidates_summary` | 每专家：name, mask_area, mean_conf, agreement 等 |
| `judge_summary` | radiomics 裁判摘要（若有） |
| `llm_model`, `temperature`, `max_tokens` | 来自 `LLMClient` |
| `selected_model`, `confidence`, `reasoning`, `parse_ok`, `error` | |
| `prompts` | 仅当 `routing_log_include_prompts` 或首条样例 |

**`disagreement_tier`（分层规则，稳定性表用同一套）**

- 分割示例：取 `average_agreement` 最高与次高差值 Δ；Δ &gt; 阈值（如 0.1）→ `easy`，否则 → `close`。  
- 或：top-2 专家 agreement 均 &gt; 0.85 → `easy`。阈值在 Methods 写死并在验证集不用于调参（仅分层标签）。

### D. `classification/agent.py`

| 位置 | 日志 |
|------|------|
| `select_best_model` | unanimous / soft_voting / LLM / fallback（`run_cls.py` 路径） |
| `resolve_path_b` → `_resolve_path_b_with_llm` | `task=cls_path_b`，含 indie + autogluon + seg 摘要 |
| `resolve_path_b` 降级软投票 | `llm_invoked=false`, `method=path_b_softvote` |

字段与分割类似；`candidates_summary` 含各模型 `top_class`, `top_confidence`, `entropy`, `margin`（能从 `ClsModelOutput` / metadata 取的都写入）。

### E. `pipeline/cascade.py`

| 修改点 |
|--------|
| `CascadePipeline.__init__` 接收 `routing_logger`，注入 `seg_agent` / `cls_agent` |
| Phase 3：`select_best_mask(..., image_name=img_name)` |
| Phase 5：Path A `_make_anchor_classification_decision` **也写一条** `task=cls_path_a`, `llm_invoked=false`, `method=classification_consensus` |
| Path B：`resolve_path_b` 已有 agent 内日志即可 |

### F. `run_pipeline.py` / `run_seg.py` / `run_cls.py`

- 读 `pipeline.log_routing`，创建 `RoutingLogger(output_dir / "routing_log.jsonl")`  
- 构造 Agent 时传入 `routing_logger`

### G. 新建仓库根目录 `run_routing_stability.py`（非 `scripts/` 下）

**输入**

- `--config`（`enable_agent=true`）  
- 已有 `intermediate/` 缓存的 `output_dir`，或先跑 Phase 1–2  
- `--repeats 5`  
- `--max_cases` / `--only_path_b` / `--only_llm_seg` 等筛选  

**流程**

1. 加载每张图的 seg/cls 缓存与标签（可选）。  
2. 判定该 case 是否纳入（例如：分类无共识 **或** 分割 `enable_agent` 会调 LLM）。  
3. 对纳入 case：循环 `repeats` 次调用 **仅路由**（与 Phase 3/5 相同输入）。  
4. 记录每次 `selected_model` / `selected_class`；若有 GT，算每次 Dice（分割）或是否正确（分类）。  
5. 输出 `stability_summary.json` + 可选 `stability_per_case.jsonl`。

**输出统计（按 `disagreement_tier` 分层）**

| 指标 | 定义 |
|------|------|
| Selection agreement | 5 次选中同一专家（或同一类）的比例；可报 case-level mean |
| Metric variance | 5 次 Dice 或 0/1 正确的 std / range |
| Fleiss κ | 可选，多类别选择时 |

### H. 新建 `scripts/revision/b6/export_router_spec.py`（可选，与 A① 二选一）

- 导出 `SegmentationAgent.system_prompt`、分类 single/multi/Path B 的 prompt 模板  
- 写入 `docs/supplementary/router_spec.md`：模型名、temperature、max_tokens、JSON 字段说明  
- **不依赖 GPU**

### I. 明确不修改

- 各 `*_model.py` 权重与推理  
- Phase 1–2 npz/json **缓存格式**（除非缺字段且无法从现有 json 推导）  
- `LLMClient` 核心重试逻辑（仅可读 `model_name` / `temperature` 写日志）

---

## 期望输出（交付物）

### 1. Supplementary Note（或 Supp. Methods S[X]）— 对应原文第 1 条

| 内容 | 来源 |
|------|------|
| 分割：完整 system prompt + user 模板说明（含锚点/无锚点两版） | `segmentation/agent.py` + export 脚本 |
| 分类：standalone 与 **Path B** 的 prompt（两套不同） | `classification/agent.py` |
| LLM **名称与版本**（分割 / 分类各一） | `config.yaml` + 实际 API `model` 字段 |
| Decoding：`temperature`, `max_tokens`（及若有的 `top_p`） | `LLMClient` + config |
| JSON schema | 代码中要求的 key + 解析失败 → `_fallback_selection` / soft vote |
| 1–2 个 **真实完整 prompt 样例**（匿名图） | `routing_log_include_prompts` 或手工从日志摘 |

### 2. Supplementary Table — 稳定性（原文第 2 条）

| 列/行建议 |
|-----------|
| 总体 + 分层 `easy` / `close` |
| N cases（仅 LLM 路由子集） |
| Mean selection agreement（%） |
| Mean Dice std 或 AUROC/accuracy std（有 GT 时） |
| 脚注：重复次数、temperature、子集定义、未对 Path A 一致短路做 5× |

**图**：可选条形图（分层一致率），非硬性。

### 3. Supplementary Table — ≥10 条结构化路由记录（原文第 3 条）

| 列建议 |
|--------|
| Case ID（匿名） |
| Task（seg / cls_path_b / cls_path_a 等） |
| Trigger（为何进/不进 LLM） |
| 候选摘要（2–3 个关键专家一行或缩略 JSON） |
| Selected + confidence |
| Reasoning（一句） |
| Correct?（若有标签） |
| 5-run agreement（若该条在稳定性子集中） |

**选取原则（representative）**：明显赢家、胶着、错例、5 次不一致、不同数据集各若干。

### 4. 仓库内产物（可复现）

| 路径 | 说明 |
|------|------|
| `output/.../routing_log.jsonl` | 全量或子集运行 |
| `output/.../stability_summary.json` | 5× 汇总 |
| `docs/supplementary/router_spec.md` | 可选，与 Supp. 同步 |

### 5. 正文

- 至多 **1–2 句** 指向 Supp. Note S[X] 与 Supp. Table S[Y–Z]；不必改 Results 主叙事。

---

## 验收 checklist

- [ ] Supp. 中 prompt / 模型版本 / 解码参数 / JSON 与 **当前代码一致**（改 prompt 须同步改 Supp.）
- [ ] 5× 实验 **仅**在调用 LLM 的 case 上报告（或明确分层报告短路 case）
- [ ] 稳定性表含 **`disagreement_tier` 分层**
- [ ] ≥10 条记录含 **候选输入 + 输出**，不仅 reasoning
- [ ] 无患者身份信息；case ID 匿名
- [ ] `enable_agent=true` 的实验配置与论文声称的 LLM 路由一致

---

## 工作量粗估

| 项 | 体感 |
|----|------|
| `routing_log` + Agent/Cascade 挂钩 | 1–2 天 |
| `run_routing_stability.py` + 汇总 | 1–2 天 |
| 导出 Supp. + 挑 10 条 + 稳定性表 | 0.5–1 天（写作） |
| API 成本 | 仅 LLM 子集 × 5；用 `max_cases` 控制 |

---

## 与 B5 的关系

- B6 的 `routing_log.jsonl` 与 `metadata_mode`（B5）共用；**先做 B6 日志**，B5 多配置重跑时不必再加一套审计。
- B5 的 Δ 性能与 B6 的稳定性 **不同表**；日志字段预留 `metadata_mode`（默认 `full`）。

---

## 已实现（代码）

| 路径 | 说明 |
|------|------|
| `shared/routing_log.py` | `RoutingLogger`、分层与候选摘要 |
| `segmentation/agent.py` / `classification/agent.py` | 路由日志与 `image_name` |
| `pipeline/cascade.py` | Phase 3/5 传参；Path A / 静态 mask / 静态 Path B 日志 |
| `run_pipeline.py` / `run_seg.py` / `run_cls.py` | `pipeline.log_routing` |
| `run_routing_stability.py` + `pipeline/routing_stability.py` | 5× 重复与 `stability_summary.json` |
| `scripts/revision/b6/export_router_spec.py` | 导出 Supp. prompt 规格 |

配置：`pipeline.log_routing: true` 开启 `routing_log.jsonl`。

---

*文档版本：对齐 `REVISION_B5_B6_B8_B11_PLAN.md` 中 B6 节及 R2.9 英文原文。*
