# NHC 数据集：允许运行的模型范围

## 禁止（数据安全 / 算力）

- **不得**在 NHC 私有数据上调用任何 **云端大模型 API**（含 GPT、Gemini、Claude 等闭源，以及 **Qwen 等开源大模型的在线/兼容 API 路由**）。
- **不得**在 NHC 上跑 **策略 7（LLM 全系统路由）**、`seg_agent` / `cls_agent`（依赖 LLM 的后处理）、B4 **L3** 级联 Agent。
- 保存 NHC 的机器 **不支持闭源模型**；开源 LLM 亦 **不接入** NHC 流水线。

## 允许

### 1. 九模型本地推理（稿面 S7–S12 / 多架构对比的主来源）

**唯一模型清单与权重路径**：`my_Thyroid_Infer/config.yaml`（`weights` + `pretrained`）。

示例配置（数据指向 `output/b7/nhc_prepared_smoke`）：

- `config/revision/infer/nhc_prepared_sample.yaml`

运行仅基础任务（**不要**加 `seg_agent` / `cls_agent`）：

```bash
cd my_Thyroid_Infer
python run_all.py --config ../ThyroidCascadeAgent/config/revision/infer/nhc_prepared_sample.yaml \
  --tasks gland nodule binary tirads
```

### 2. ThyroidCascadeAgent 本地专家（无 LLM）

用于 **B7 级联协议**、**B3 静态路由**、**B4 L1** 等时：

- 所有 yaml 中 **`segmentation.agent.enable_agent: false`**、**`classification.agent.enable_agent: false`**
- **`radiomics_judge`**：本地 AutoGluon（与主文一致，非 LLM）
- 专家权重为仓库内 **Segmentation_Agent / Classification_Agent** 的 **DINO  checkpoint**（`nhc_no_llm_primary.yaml` / `nhc_prepared_sample.yaml`），**不是** GPT/Qwen。

这与九模型 infer **并行**：级联表用 Cascade 输出；九模型列用 `my_Thyroid_Infer` 输出。

## 配置检查清单

| 检查项 | NHC 示例配置 |
|--------|----------------|
| `enable_agent: false` | b3 / b4 / cascade yaml 已设 |
| 不设置 `DASHSCOPE_API_KEY` 亦可跑 | 是（无 LLM 阶段） |
| 九模型路径 | `config/revision/infer/nhc_prepared_sample.yaml` |
| 不含 `routing_mode: llm` / 策略 7 | 是 |
| B3 策略 6 learned | **仅推理**（`run_learned_b3.py` + 开发队列 joblib）；**不在 NHC fit** |
