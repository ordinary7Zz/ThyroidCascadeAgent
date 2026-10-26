# B6　路由器透明性与 5× 稳定性结论

> **审稿意见**：R2.9（router transparency；每例重复路由 5 次；报告选择一致率与指标波动，并按候选接近程度分层；≥10 条结构化路由记录）  
> **状态**：**试点结论**（sample，`n=10`）；主队列数值待 `stability_summary.json` 产出后替换下文「数据卡」与 §3 表格。

---

## 1. 数据卡（换数据集时 **优先改本节**）

| 字段 | 当前值（sample 试点） | 替换为 |
|------|----------------------|--------|
| 队列 / cohort | `sample` | 如 `TN3K`、`TN5K` … |
| 图像数 `n_cases` | **10** | `stability_summary.json` → `n_cases` |
| 重复次数 `repeats` | **5** | 同上 → `repeats`（建议保持 5 与稿面一致） |
| 汇总一致率 | **0.92**（92%） | `mean_selection_agreement` |
| 分层 `close` 例数 / 均值 | **10** 例，均值 **0.92** | `by_disagreement_tier.close` |
| 分层 `easy` 例数 / 均值 | **0** 例（本批未出现） | `by_disagreement_tier.easy`（若有） |
| 配置 | `config/revision/b6/sample_stability.yaml` | 复制为 `config/revision/b6/<cohort>_stability.yaml` 并改 `data` / `shared_intermediate` |
| 稳定性 JSON | `output/sample/pipeline_run/stability_summary.json` | `output/<cohort>/pipeline_run/stability_summary.json` |
| 路由审计日志 | `output/sample/pipeline_run/routing_log.jsonl` | 同目录 `routing_log.jsonl` |
| LLM（稳定性配置） | qwen3.7-flash，`temperature=0.3`，`max_tokens=768` | 与 config 中 `shared.agent_llm` 一致 |

**分层定义（与代码一致，换数时不必改文案）：** 分割侧 `disagreement_tier`：各候选 `average_agreement` 排序后，top-1 与 top-2 差值 ≤ **0.10** → `close`，否则 `easy`（`shared/routing_log.py`）。

---

## 2. 三条审稿要求的对应关系

### 2.1 规格公开（可复现）

- 补充材料：**`docs/supplementary/router_spec.md`**（完整 prompt 模板、模型名、解码参数、输出 JSON 字段）。
- 可由 `python scripts/revision/b6/export_router_spec.py` 从当前 config 再导出（改模型后重导一次即可）。

### 2.2 5× 路由稳定性（本文件 §3 数字）

- 在 **复用 Phase 1–2 `intermediate/`** 的前提下，对每张图重复调用 LLM **分割路由** `repeats` 次；分类仅在 **无共识（Path B）** 时再重复 Path B 分类 LLM。
- **Path A 分类共识** 不重复 5× 分类（确定性短路）；稳定性分析中的 `selection_agreement` 在多数 Path A 病例上 **等于分割侧** `seg_selection_agreement`。

### 2.3 ≥10 条结构化路由记录

- **`routing_log.jsonl`**：每条含 `candidates_summary`、`judge_summary`（若启用）、`llm_invoked`、`selected_model` / `selected_class`、`reasoning`、`disagreement_tier` 等。
- sample 试点日志约 **75** 行（含多次 pipeline / 消融跑数）；撰稿时 **筛选 ≥10 例** 制表即可，其中建议包含不稳定例 **0002.jpg**、**0003.jpg**（与 §3.2 一致）。

---

## 3. 定量结论（sample，`n=10`，`repeats=5`）

### 3.1 总体

- **平均选择一致率**：**92%**（`mean_selection_agreement = 0.92`）。
- **分层**：本批 **10/10** 为 **`close`**（候选 agreement 差距小），**无 `easy` 层**；故分层表仅报告 close 层均值 0.92，**尚不能在本次试点内对比 easy vs close**（扩大 `max_cases` 或换队列后若出现 `easy`，补一行即可）。
- **分割 / 分类 Agent**：均为 `enable_agent: true`（与 B6 稳定性实验设定一致）。

### 3.2 病例级摘要（不稳定例用于回复举例）

| 图像 | Path | tier | 5× 分割专家（摘要） | `seg` 一致率 | Dice 波动（有 GT） |
|------|------|------|---------------------|--------------|-------------------|
| 0002.jpg | A | close | TN3K / ThyroidXL 混选 | **60%** | range ≈ 0.062，std ≈ 0.031 |
| 0003.jpg | B | close | all_datasets / PKTN 混选 | **60%** | range ≈ 0.119 |
| 0003.jpg | B | — | 分类 5×：1×良性、4×恶性 | **cls 80%** | — |
| 其余 8 例 | 多为 A | close | 单一专家 5/5 | **100%** | Dice std = 0 |

### 3.3 一句话结论（中文，可进正文 / 回复）

在 **sample** 子集（10 例、每例 5 次 LLM 分割路由、候选均为 close-tier）下，路由器 **平均选择一致率为 92%**；**8/10** 病例五次选择完全相同，**2/10**（胶着分割或 Path B）一致率为 **60%**，且与 **Dice 在重复间的波动**（最大 range 约 **0.12**）相对应。路由器完整规格与结构化决策日志见补充材料；队列级分层稳定性将在主实验 cohort 上按相同协议扩展。

### 3.4 一句话结论（英文草稿）

On the **sample** subset (*n* = 10, five repeated LLM segmentation routing calls per case, all cases labelled **close** by inter-expert agreement), mean selection agreement was **92%** (8/10 cases fully stable; 2/10 at **60%** with measurable Dice variability across repeats). Full router specifications and structured routing logs are provided in the Supplementary Information.

---

## 4. 换队列时除数字外还可能要改什么？

| 只换数值即可 | 建议同步检查 |
|--------------|----------------|
| §1 数据卡、`mean_selection_agreement`、`by_disagreement_tier` | `n_cases` 是否与稿面「子集 / 全量」表述一致 |
| §3.1 总体句中的比例、例数 | 是否出现 **`easy` 层**（需补分层对比句） |
| §3.2 不稳定例表格 | **逐例行**需从新区 `per_case` 重选 1–2 个低一致率例替换 0002/0003 |
| §3.3–3.4 一句话 | cohort 名称、*n*、是否「全 close」 |

**不必改**：分层阈值 0.10、R2.9 三条结构、`router_spec.md`（除非换 LLM 型号或 prompt）。

---

## 5. 产物路径清单（sample）

```
output/sample/pipeline_run/stability_summary.json   # 5× 汇总
output/sample/pipeline_run/routing_log.jsonl      # 结构化审计
docs/supplementary/router_spec.md                   # 透明性
config/revision/b6/sample_stability.yaml                     # 稳定性实验 config
```

---

*文档版本：2026-10-21；数值来源 `stability_summary.json`（sample，`max_cases=10`）。*
