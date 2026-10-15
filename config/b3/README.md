# B3 路由消融配置

每个测试队列一个 YAML：`config/b3/<cohort_id>.yaml`。

| 文件 | 队列 | Phase 1–2 参考 |
|------|------|----------------|
| `sample.yaml` | 开发集 10 例 | `config/config_test.yaml` |
| `tn3k.yaml` | TN3K test | `config/config_TN3K.yaml` |
| `tn5k.yaml` | TN5K test | `config/config_TN5K.yaml` |
| `thyroidxl.yaml` | ThyroidXL test | `config/config_ThyroidXL.yaml` |
| `zjh8k.yaml` | ZJH-8K | `config/config_ZJH-8K.yaml` |
| `rjh7k.yaml` | RJH-7K | `config/config_RJH-7K.yaml` |
| `ddti.yaml` | DDTI（路径见文件内注释） | `config/config_DDTI.yaml` |
| `nhc_misd_tus.yaml` | NHC-MISD-TUS（**路径占位，需改**） | 待补 |

- **模板**：以 `sample.yaml` 为准；其余由 `python scripts/generate_ablation_configs.py` 生成或同步。
- **专家池**：当前与 sample 同为 2 seg + 2 cls；正式投稿前请与 `config/config_<队列>.yaml` 的 Table S3/S4 池对齐。
- **波次 1（无 learned/llm）**：`routing_modes` 仅含 6 种静态策略；或 `run_b3_batch.py --preset wave1`。

```bash
python scripts/run_b3_batch.py --config config/b3/zjh8k.yaml --preset wave1 --force-phase3 --summarize
```
