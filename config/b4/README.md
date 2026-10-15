# B4 组件消融配置

每个队列一个 YAML：`config/b4/<cohort_id>.yaml`。`b3_root` 指向同队列的 B3 输出目录。

| 文件 | 对应 B3 配置 |
|------|----------------|
| `sample.yaml` | `config/b3/sample.yaml` → `output/ablation/b3/sample` |
| `zjh8k.yaml` | `config/b3/zjh8k.yaml` → `output/ablation/b3/zjh8k` |
| … | 其余 cohort 同名 |

- **L1**：`artifacts/b4_l1_<cohort>_placeholder.json`（占位，正式单专家评测后替换）。
- **L2/L3**：分别读 B3 的 `soft_voting`、`llm` 目录下的 `b3_metrics.json`（无 `llm` 时 L3 行会缺/告警）。
- **Path B 附录**：`pathb.b_a` / `b_b` / `b_c` 对应 B3 子目录名。

```bash
python scripts/build_b4_tables.py --config config/b4/zjh8k.yaml
```

重新生成全部 B4（及 B3 数据段）：`python scripts/generate_ablation_configs.py`
