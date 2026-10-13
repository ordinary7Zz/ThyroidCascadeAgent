# ThyroidCascadeAgent

conda activate /mnt/wangbd8/workspace/envs/thyroid_infer

甲状腺超声级联推理系统：分割筛选 Agent → 分类筛选 Agent，以 GT-trained radiomics 模型作为分割质量裁判。

## 架构

```
shared/              共享层（IO、数据集信息、LLM 客户端、网络架构）
segmentation/        分割层（多模型预测 + 形态学评估 + LLM 选择）
classification/      分类层（多模型预测 + 校准 + soft voting + LLM 选择）
radiomics_judge/     GT-trained radiomics 裁判（评估 pred mask 可信度）
pipeline/            串联编排（分割筛选 → 分类筛选）
```

## 入口

- `run_seg.py` — 单独跑分割筛选
- `run_cls.py` — 单独跑分类筛选
- `run_pipeline.py` — 串联分割→分类

## 配置

`config/config.yaml` 统一配置，API key 从环境变量 `DASHSCOPE_API_KEY` 读取。

## 构建计划

详见 `docs/BUILD_PLAN.md`。

## 返修 B6（路由透明性）

- 配置：`pipeline.log_routing: true` → 输出目录下 `routing_log.jsonl`
- 规格导出：`python scripts/export_router_spec.py`
- 5× 稳定性（需 intermediate 缓存 + `enable_agent: true`）：`python run_routing_stability.py --output-dir <pipeline_out>`

详见 `docs/REVISION_B6_PLAN.md`。
