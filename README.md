# ThyroidCascadeAgent

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

## 返修 B3（路由消融，波次 0–1）

1. 先跑满共享 `intermediate`（Phase 1–2），例如 `python run_pipeline.py --config config/config_test.yaml`。
2. **一次性跑波次 1 多个策略**（推荐）：

```bash
conda activate /mnt/wangbd8/workspace/envs/thyroid_infer
# 方式 A：在 config/ablation_b3.yaml 的 pipeline.ablation 里配置 routing_modes 后：
python scripts/run_b3_batch.py --config config/ablation_b3.yaml
# 默认 static bundle：一次扫图输出 config 中全部静态策略（见 pipeline/static_b3_bundle.py）
# 旧行为（每策略子进程）：--legacy-subprocess

# 方式 B：命令行覆盖
python scripts/run_b3_batch.py \
  --config config/ablation_b3.yaml \
  --shared-intermediate output/sample/pipeline_run/intermediate \
  --output-root output/ablation/b3/sample \
  --modes soft_voting,static_rule,oracle \
  --force-phase3 --summarize
```

**seg / cls 可分开**（一次运行内）：

```yaml
routing_modes:
  - name: my_mix
    seg: static_rule
    cls: soft_voting
```

或单次：`python scripts/run_routing_ablation.py ... --routing-mode-seg static_rule --routing-mode-cls soft_voting`

CLI 批量简写：`--modes soft_voting,static_rule:soft_voting`（`seg:cls`）。

3. 单策略：

```bash
python scripts/run_routing_ablation.py \
  --config config/ablation_b3.yaml \
  --routing-mode soft_voting \
  --task both \
  --shared-intermediate output/sample/pipeline_run/intermediate \
  --output-dir output/ablation/b3/sample/soft_voting \
  --force-phase3
```

4. （可选）val 上选 best_single 专家：

```bash
python scripts/fit_best_single_expert.py \
  --config config/ablation_b3.yaml \
  --intermediate output/sample/pipeline_run/intermediate
```

5. 离线分割梯子（不调 cascade）：`python scripts/eval_seg_routing_offline.py --intermediate output/sample/pipeline_run/intermediate`

6. 汇总（若未用 `--summarize`）：

```bash
python -m pipeline.ablation_summary --root output/ablation/b3/sample \
  --reference-manifest output/ablation/b3/sample/soft_voting/intermediate_manifest.json \
  --paired soft_voting,static_rule
```

详见 `docs/REVISION_B3_B4_PLAN.md`。
