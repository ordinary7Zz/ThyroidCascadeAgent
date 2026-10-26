# B4 组件消融配置

每个队列一个 YAML：`config/revision/b4/<cohort_id>.yaml`。`b3_root` 指向同队列的 B3 输出目录。

| 文件 | 对应 B3 配置 |
|------|----------------|
| `sample.yaml` | `config/revision/b3/sample.yaml` → `output/ablation/b3/sample` |
| `zjh8k.yaml` | `config/revision/b3/zjh8k.yaml` → `output/ablation/b3/zjh8k` |
| … | 其余 cohort 同名 |

- **L1**：`artifacts/b4_l1_<cohort>.json`（`ingest_l1_metrics.py`）；占位文件 `*_placeholder.json` 仅开发用。
- **L2/L3**：分别读 B3 的 `soft_voting`、`llm` 目录下的 `b3_metrics.json`（无 `llm` 时 L3 行会缺/告警）。
- **Path B 附录**：`pathb.b_a` / `b_b` / `b_c`；**B-b** 默认目录 `output/ablation/b4/<cohort>/path_b_autogluon`（与 `run_b4_pathb_appendix.py --output-dir` 一致）。

### L1 写入

见 `docs/revision/b4/L1_METRICS_SCHEMA.md`。

```bash
python scripts/revision/b4/ingest_l1_metrics.py \
  --dataset-id zjh8k \
  --config config/revision/b3/zjh8k.yaml \
  --pipeline-dir output/ablation/l1/zjh8k/run1 \
  --out artifacts/b4_l1_zjh8k.json
```

### 汇总主表

```bash
python scripts/revision/b4/build_b4_tables.py --config config/revision/b4/zjh8k.yaml
```

重新生成全部 B4（及 B3 数据段）：`python scripts/generate_ablation_configs.py`（会写入 `b_b_metrics_dir`）。
