# B6 配置（`test_for_llm_malignancy` 子集）

满足 **R2.9**：`routing_log.jsonl` + `run_routing_stability.py`（5× LLM 路由重复）。  
数据路径对齐 `scripts/build_all_test_for_llm.sh`（约 ≤250 张），**不用全量 test**。  
**YAML 字段与 `sample_stability.yaml` 同构**（含 `pipeline.ablation` 块）；仅 `data` 路径与 `output/b6/<cohort>/` 不同。

**LLM 路由（各 cohort 统一）**：`shared.agent_llm.model_name` = **`deepseek-v4-pro-0813`**（DashScope compatible API，`DASHSCOPE_API_KEY`；`temperature=0.3`，**`max_tokens=2048`**（路由 JSON；若日志出现 `finish_reason=length` 可再增大），与 B5 主队列可分开调参）。

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

**Intermediate 在哪？** B6 脚本默认只认 `output/b6/<cohort>/pipeline_run/intermediate/`。主外测 pipeline 的 Phase 1–2 往往在 **别的路径**（与 B3 共用），例如：

| cohort | 已有 Phase 1–2（本机典型路径） | for_llm 250 张是否在其中 |
|--------|-------------------------------|---------------------------|
| thyroidxl | `output/ThyroidXL/pipeline_run/intermediate` | 是（250/250） |
| zjh8k | `output/ZJH-8K/pipeline_run/intermediate` | 是（250/250） |
| ddti_cls | `output/DDTI_cls/pipeline_run/intermediate`（**仅 cls**，无 seg） | cls 250/250 |
| tn3k / tn5k | `output/b6/tn3k|tn5k/...` 或 `output/TN3K|TN5K/...` | B6 下多为 250 行 npz |

若 `run_b6_stability_*.sh` 报「缺少 intermediate」，可先链到主缓存（不复制大文件）：

```bash
bash scripts/revision/b6/link_b6_intermediate_from_main.sh
```

然后再跑 `run_b6_stability_remaining.sh`（写 manifest + 5× LLM）。

| **ZJH-8K 等大队列** | symlink 到全量 `intermediate` 时，稳定性脚本 **只 mmap 加载 manifest 内 10 张**（`pipeline/revision/b6/cache_subset.py`）。旧版曾一次性载入 ~9×4GB npz 导致 **Killed（内存 OOM）**；**换 CUDA 设备无效**。 |

`sample_stability.yaml`：仅 10 例本地调试，不参与上表批量。

## 前置：构建 for_llm 子集

```bash
bash scripts/build_all_test_for_llm.sh
# LABEL_KEY=malignancy（默认）
```

若某目录不存在，先跑上式再执行 pipeline。

## 推荐流程（**仅 10 例 LLM**，默认已写入 yaml）

各 cohort 默认：`stop_after_phase2: true` + `pipeline.data.stability_sample`（`n=10`, `seed=42`, `mode=random`）。

```bash
export DASHSCOPE_API_KEY=...

COHORT=tn5k
OUT=output/b6/${COHORT}/pipeline_run

# 1) 仅 Phase 1–2：对 stability_sample 的 10 张做专家推理（无 LLM）
python run_pipeline.py --config config/revision/b6/${COHORT}.yaml --device cuda --stop-after-phase2

# 2) 5× 稳定性：同一 10 张（读 stability_case_manifest.json）仅重复 LLM 路由
python run_routing_stability.py \
  --config config/revision/b6/${COHORT}.yaml \
  --output-dir "$OUT" \
  --repeats 5 --device cuda

# 批跑剩余队列（若曾误跑 250 张，先 FORCE_REFRESH=1）
bash scripts/revision/b6/run_b6_stability_remaining.sh

# 3) 规格导出（无 GPU）
python scripts/revision/b6/export_router_spec.py --config config/revision/b6/${COHORT}.yaml
```

## 重新生成 YAML

修改 `scripts/revision/b6/generate_b6_configs.py` 后：

```bash
python scripts/revision/b6/generate_b6_configs.py
```

计划：`docs/REVISION_B6_PLAN.md`；结论文档：`docs/revision/b6/`.
