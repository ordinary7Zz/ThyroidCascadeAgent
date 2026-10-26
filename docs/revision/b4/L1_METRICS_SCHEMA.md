# B4 L1 单专家指标 JSON 规范

> **B4 总进度与 L1/L2 数字表**：[B4_STATUS_ZH.md](./B4_STATUS_ZH.md)  
> **消费者**：`pipeline/revision/b4/b4_summary.py`（`l1_metrics` 路径）  
> **生产者**：`scripts/revision/b4/ingest_l1_metrics.py` 或外仓手写后 `--patch-json` 合并

## 实验定义（L1）

- **一个**在完整堆叠 segmentation/classification development 上训练的 DINO 专家（与稿中「多专家池」成员同架构，但 **只保留一个 checkpoint**）。
- 外测：**该专家直连输出**，无专家池融合、**无 LLM**、无 B3 八种路由。
- **不定义** Path A/B 多模型分歧；`classification_path_b` **默认省略**（若填写仅用于特殊敏感性分析，需在 Methods 说明）。

## 顶层字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `dataset_id` | 是 | 与 `config/revision/b4/<id>.yaml` 一致，如 `tn3k`、`zjh8k` |
| `schema_version` | 建议 | 当前为 `1` |
| `layer` | 建议 | 固定 `"L1"` |
| `description` | 可选 | 人类可读一句 |
| `note` | 可选 | 占位/修订说明 |
| `provenance` | 强烈建议 | 训练与评测可追溯（见下） |
| `segmentation` | 与 cls 二选一至少一项 | 分割外测 |
| `classification` | 与 seg 二选一至少一项 | 良恶性外测（**全测试集**） |
| `classification_path_b` | 否 | L1 通常不写 |

### `provenance` 建议键

```json
{
  "training": "stacked dataset_3 / dataset_4（与 Table S3/S4 开发集一致）",
  "seg_checkpoint": "path or weight id",
  "cls_checkpoint": "path or weight id",
  "eval_run_dir": "output/ablation/l1/tn3k/run1",
  "eval_protocol": "single expert mask + single cls head; no routing",
  "bootstrap": "image-level 1000 resamples seed=42（与 evaluate_pipeline 一致；定稿前可换 B2 cluster）"
}
```

## `segmentation` 块（`b4_summary` 读取）

| 键 | 类型 | 说明 |
|----|------|------|
| `dice_mean` | float | 0–1，与稿中 Dice 一致（非百分比） |
| `dice_ci_lower` / `dice_ci_upper` | float | 95% CI |
| `hd95_mean` | float | mm |
| `hd95_ci_lower` / `hd95_ci_upper` | float | 可选；汇总表目前主要用 `hd95_mean` |

掩膜来源：单专家预测 mask（或写入 `intermediate/selected_masks.npz` 后走 `evaluate_pipeline`）。

## `classification` 块

| 键 | 类型 | 说明 |
|----|------|------|
| `n` | int | 有标签的图像数 |
| `auroc` / `auprc` | float | 点估计 |
| `auroc_ci_lower` / `auroc_ci_upper` | float | 95% CI |
| `auprc_ci_lower` / `auprc_ci_upper` | float | 95% CI |
| `accuracy` | float | 可选 |

分数定义与 `pipeline/evaluate.py` 一致：`score_malignant = p(恶性)`（由 `final_label` + `final_confidence` 推出）。

## 外仓 / my_Thyroid_Infer 对接流程

1. 在堆叠 development 上训好 **一个** seg + **一个** cls 专家。  
2. 对外测队列推理，得到与 cascade 兼容的 `results.json`（每例至少 `image_name`、`true_label`、`final_label`、`final_confidence`）及分割 mask（建议目录结构同 `run_pipeline` 输出）。  
3. 在本仓库执行：

```bash
python scripts/revision/b4/ingest_l1_metrics.py \
  --dataset-id zjh8k \
  --config config/revision/b3/zjh8k.yaml \
  --pipeline-dir /path/to/l1/zjh8k \
  --provenance-json docs/revision/b4/examples/l1_provenance_zjh8k.json \
  --out artifacts/b4_l1_zjh8k.json
```

4. 将 `config/revision/b4/zjh8k.yaml` 的 `l1_metrics` 改为 `artifacts/b4_l1_zjh8k.json`（或保持 generate 默认路径但 **覆盖** placeholder 文件内容）。  
5. `python scripts/revision/b4/build_b4_tables.py --config config/revision/b4/zjh8k.yaml`

## 与 L2/L3 的指标口径

| 层 | 数据来源 | LLM |
|----|----------|-----|
| L1 | 本 JSON | 否 |
| L2 | B3 `soft_voting/b3_metrics.json` | 否 |
| L3 | B3 `llm/b3_metrics.json` | 是 |

定稿前若 B2 cluster bootstrap 重算 CI，应对 L1 重新 `ingest`（或外仓按同一 cluster 脚本出 CI 后 `--patch-json` 覆盖 `segmentation`/`classification` 中的 CI 字段）。

## 最小合法示例

```json
{
  "schema_version": 1,
  "dataset_id": "tn3k",
  "layer": "L1",
  "segmentation": {
    "dice_mean": 0.84,
    "dice_ci_lower": 0.82,
    "dice_ci_upper": 0.86,
    "hd95_mean": 10.2
  },
  "classification": {
    "n": 614,
    "auroc": 0.81,
    "auroc_ci_lower": 0.77,
    "auroc_ci_upper": 0.85,
    "auprc": 0.72
  }
}
```
