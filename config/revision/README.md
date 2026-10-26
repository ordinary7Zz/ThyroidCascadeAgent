# 返修实验配置（B 任务）

审稿返修相关 YAML 统一放在本目录；主 pipeline / 投稿队列配置仍在 `config/config_<队列>.yaml` 与 `config/config.yaml`。

| 子目录 | 任务 | 说明 |
|--------|------|------|
| `b3/` | B3 路由消融 | 各 cohort `*.yaml`；`learned_wave3_cohorts.yaml`；`val_lists/`；Phase 1–2 辅助 `pipeline_*_b3.yaml` |
| `b4/` | B4 分层汇总 | `*.yaml` 指向 B3 产物；`l1/` 单专家 L1 跑数 |
| `b5/` | B5 元数据消融 | LLM 路由 + `metadata_mode` |
| `b6/` | B6 稳定性 / 主 LLM pipeline | `test_for_llm_malignancy` 等 |
| `validation/` | 验证集 Phase 1–2 | learned 拟合、B8 定阈等共用 |
| `nhc_no_llm_primary.yaml` | NHC 无 LLM 主协议 | B7/B8 等 |

生成 B3/B4/B5/L1 模板：

```bash
python scripts/generate_ablation_configs.py
```

生成 B6：

```bash
python scripts/revision/b6/generate_b6_configs.py
```
