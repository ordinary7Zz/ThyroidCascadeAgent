# `config/for_llm` — 策略 7 LLM 路由（专家选择占比）

外测队列 **分割 / 分类** LLM 专家占比表（`expert_selection_tables_*.tex`）所需推理配置。  
`pipeline.data` 一律指向各队列下的 **`test_for_llm_malignancy`**（约 250 例；PKTN 为全量 150）。

## 生成 / 更新 YAML

```bash
python scripts/generate_for_llm_configs.py
```

## 前置：构建子集

```bash
bash scripts/build_all_test_for_llm.sh
```

`build_test_for_llm.py` 默认输出名可能是 `*_for_llm_malignancy`（如 `ZJH-8K_for_llm_malignancy`、`all_seg_for_llm_malignancy`）。若与下表路径不一致，请用 `--out .../test_for_llm_malignancy` 重建，或将已有子集目录 **符号链接 / 复制** 到本 README 所列 `test_for_llm_malignancy` 路径。

| 配置文件 | 子集根目录（`test_for_llm_malignancy` 的父路径） | 任务 |
|----------|--------------------------------------------------|------|
| `tn3k.yaml` | `train_val_test/TN3K/` | 分割 + 分类 |
| `tn5k.yaml` | `train_val_test/TN5K/` | 分割 + 分类 |
| `thyroidxl.yaml` | `train_val_test/ThyroidXL/` | 分割 + 分类 |
| `zjh8k.yaml` | `train_val_test/ZJH-8K/` | 分割 + 分类 |
| `pktn.yaml` | `train_val_test/PKTN/` | 分割 + 分类 |
| `rjh7k.yaml` | `train_val_test/RJH-7K/`（`image`/`mask` 子目录） | 仅分割 |
| `ddti_seg.yaml` | `train_val_test/DDTI/all_seg/` | 仅分割 |
| `ddti_cls.yaml` | `train_val_test/DDTI_Classification/all/`（`images_processed`） | 仅分类 |

回信表 **DDTI** 一行：分割用 `ddti_seg.yaml`，分类用 `ddti_cls.yaml`。

## 跑推理

```bash
export DASHSCOPE_API_KEY=...
python run_pipeline.py --config config/for_llm/tn5k.yaml --device cuda
```

输出：`output/for_llm/<cohort>/pipeline_run/`（含 `routing_log.jsonl`，用于统计专家占比）。
