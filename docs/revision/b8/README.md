# B8　校准与拒答（返修）

| 文件 | 说明 |
|------|------|
| [B8_CALIBRATION_ABSTENTION_CONCLUSIONS.md](./B8_CALIBRATION_ABSTENTION_CONCLUSIONS.md) | 结论文档（当前为 **smoke** 数值；定稿后替换 §1 数据卡与 §3–§4 表格） |
| [FAKE_DISPLAY.md](./FAKE_DISPLAY.md) | **展示用** `results_fake` / 出图 / 与表 R2 一致性检查（非定稿 R4 默认来源） |
| `docs/REVISION_B7_B8_PLAN.md` | 任务契约与交付物 |

**定稿时**：跑 `run_openthyroid_validation_b8.sh` + `run_b8_all_cohorts.sh`，从 `output/b8/fit/` 与 `output/b8/cohorts/` 更新结论文档中的数字即可；方法与 §2、§5 模板通常不变。

**Risk–coverage 图**（读 `cohorts/*/abstention_eval.json`）：

```bash
export PYTHON=/mnt/wangbd8/workspace/envs/thyroid_infer/bin/python
python scripts/revision/b8/plot_risk_coverage.py --mark-operating-point --combined
# 输出：output/b8/figures/risk_coverage_<cohort>.png、risk_coverage_panels.png
```
