# B6 配置（`test_for_llm_malignancy` 子集）

满足 **R2.9**：`routing_log.jsonl` + `run_routing_stability.py`（5× LLM 路由重复）。  
数据路径对齐 `scripts/build_all_test_for_llm.sh`（约 ≤250 张），**不用全量 test**。  
**YAML 字段与 `sample_stability.yaml` 同构**（含 `pipeline.ablation` 块）；仅 `data` 路径与 `output/b6/<cohort>/` 不同。

| 配置文件 | 数据根目录 | seg / cls |
|----------|------------|-----------|
| `tn3k.yaml` | `.../TN3K/test_for_llm_malignancy` | both |
| `tn5k.yaml` | `.../TN5K/test_for_llm_malignancy` | both |
| `thyroidxl.yaml` | `.../ThyroidXL/test_for_llm_malignancy` | both |
| `zjh8k.yaml` | `.../ZJH-8K_for_llm_malignancy` | both |
| `pktn.yaml` | `.../PKTN/test_for_llm_malignancy` | seg only |
| `rjh7k.yaml` | `.../augtrain_PNG_for_llm_malignancy` | seg only |
| `ddti_seg.yaml` | `.../DDTI/all_seg_for_llm_malignancy` | seg only |
| `ddti_cls.yaml` | `.../DDTI_Classification/all_for_llm_malignancy` | cls only |

输出目录统一：`output/b6/<cohort>/pipeline_run/`（含 `intermediate/`、`routing_log.jsonl`、`stability_summary.json`）。

`sample_stability.yaml`：仅 10 例本地调试，不参与上表批量。

## 前置：构建 for_llm 子集

```bash
bash scripts/build_all_test_for_llm.sh
# LABEL_KEY=malignancy（默认）
```

若某目录不存在，先跑上式再执行 pipeline。

## 推荐流程

```bash
export DASHSCOPE_API_KEY=...

COHORT=tn3k
# 1) 完整 pipeline（Phase 1–5，写 log）；或先设 pipeline.stop_after_phase2: true 只跑 Phase 1–2
python run_pipeline.py --config config/revision/b6/${COHORT}.yaml --device cuda

# 2) 5× 稳定性（复用 intermediate，仅重复 LLM 路由）
python run_routing_stability.py \
  --config config/revision/b6/${COHORT}.yaml \
  --output-dir output/b6/${COHORT}/pipeline_run \
  --repeats 5 --device cuda

# 3) 规格导出（无 GPU）
python scripts/revision/b6/export_router_spec.py --config config/revision/b6/${COHORT}.yaml
```

## 重新生成 YAML

修改 `scripts/revision/b6/generate_b6_configs.py` 后：

```bash
python scripts/revision/b6/generate_b6_configs.py
```

计划：`docs/REVISION_B6_PLAN.md`；结论文档：`docs/revision/b6/`.
