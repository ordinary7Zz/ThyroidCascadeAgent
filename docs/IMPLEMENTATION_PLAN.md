# ThyroidCascadeAgent 修改实施计划

> 根据 `目标.md` 讨论确定的 4 步流程重新组织 Pipeline 和 Agent。

## 新流程

```
Step 1: 跑 3 个独立分类模型 → 判断共识（无 LLM）
   ├─ 共识 → Path A（分类锚点已定）
   └─ 无共识 → Path B（分类待定）

Step 2: 跑 5 个分割模型 + Radiomics 裁判 + quality_evaluator

Step 3: 分割 Agent 选 mask
   ├─ agent_enabled=true → LLM（含/不含分类锚点 prompt）
   └─ agent_enabled=false → 静态规则（锚点过滤 + average_agreement 排序）

Step 4: 分类裁决
   ├─ Path A → 直接输出锚点
   └─ Path B → 多数派 vs AutoGluon 比较 → LLM 或静态规则
```

## 修改清单

### 1. `classification/model_registry.py`（~15 行，前置依赖）

- 新增 `get_independent_models()` → 返回 `requires_mask=False` 的模型
- 新增 `get_mask_dependent_models()` → 返回 `requires_mask=True` 的模型

### 2. `config/config.yaml`（~3 行）

- 新增 `classification.agent.consensus_min_confidence: 0.6`

### 3. `segmentation/agent.py`（~50 行）

- `SegAgentDecision` 增加 `classification_anchor: str | None`, `path: str` 字段
- `select_best_mask()` 增加 `classification_anchor` 参数
- `format_predictions_for_agent()` 增加锚点字段和 prompt 结构
- `_generate_system_prompt()` 动态追加锚点/无锚点指令

### 4. `classification/agent.py`（~100 行）

- 新增 `resolve_path_b(indie_preds, autogluon_pred, seg_decision)` → 规则裁决
- 新增 `_resolve_path_b_with_llm(...)` → LLM 裁决（全新 prompt）
- 新增 Path B 专用 system prompt 和 user prompt 构造

### 5. `pipeline/cascade.py`（~200 行，核心重构）

- `run_single()` 重写为 Step 1→2→3→4 流程
- 新增 `_get_independent_classification_predictions()`
- 新增 `_check_classification_consensus()`
- 新增 `_make_anchor_classification_decision()`
- 新增 `_run_autogluon_classification()`
- 新增 `_select_mask_static()`（agent_enabled=false 时）
- 新增 `_resolve_classification_path_b()`（agent_enabled=false 时规则裁决）

### 6. `run_pipeline.py`（~0 行，外部接口不变）

## 不改动的文件

- 所有模型子类（`segmentation/*_model.py`, `classification/*_model.py`）
- `radiomics_judge/`、`shared/`、`run_seg.py`、`run_cls.py`
- `segmentation/model_registry.py`（接口不变）
- `segmentation/quality_evaluator.py`、`segmentation/metrics.py`

## 关键设计决策

| 决策 | 选择 |
|---|---|
| AutoGluon 在分类阶段的身份 | 不参与独立模型投票，作为参照，最终 Path B 时可能与多数派比较 |
| 共识判定标准 | top_class 一致 AND min(confidence) > 0.6 |
| 无 LLM 时的分割 tiebreaker | average_agreement（模型间 IoU 一致性，不依赖 mahalanobis） |
| Path B 分类不确定性处理 | 都不可靠时输出多数派 + "low" 置信度 |
| Agent 可配置 | `classification.agent.enable_agent` 控制是否调 LLM |
