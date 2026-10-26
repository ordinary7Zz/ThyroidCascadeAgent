# B6 返修交付物（路由器透明性与稳定性）

| 文件 | 说明 |
|------|------|
| [**B6_ROUTING_STABILITY_CONCLUSIONS.md**](./B6_ROUTING_STABILITY_CONCLUSIONS.md) | **主结论文档**（当前填 **sample** 试点数值；换队列时改文内「数据卡」与表格） |
| [REVIEWER_RESPONSE_SNIPPETS_B6.md](./REVIEWER_RESPONSE_SNIPPETS_B6.md) | R2.9 回复段落草稿（与主文档数字一致） |

**规格与审计（与队列无关，一般不需随换数而改）：**

- `docs/supplementary/router_spec.md`（prompt / 模型 / 解码 / JSON）
- 各 cohort 的 `output/<队列>/pipeline_run/routing_log.jsonl`（结构化记录 ≥10 条）

**稳定性跑数：**

```bash
export DASHSCOPE_API_KEY=...
python run_routing_stability.py \
  --config config/revision/b6/sample_stability.yaml \
  --output-dir output/<队列>/pipeline_run \
  --repeats 5 --max-cases <N> --device cuda
```

产物：`output/<队列>/pipeline_run/stability_summary.json`。

实施规格：`docs/REVISION_B6_PLAN.md`；命令索引：`docs/RUN_REVISION_COMMANDS.md` §5。
