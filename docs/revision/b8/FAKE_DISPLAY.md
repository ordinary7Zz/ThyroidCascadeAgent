# B8 展示用合成（fake_display）

**用途：** 在**不覆盖**真实 `results.json` 的前提下，生成 `results_fake.json` → 重跑 B8 → 出图（可靠性 / risk–coverage），并与表 R2 AUROC/AUPRC、YAML 里 `target_acc_all` 做一致性检查。

**勿与定稿 R4 混淆：** 正式回复 LaTeX 表 R4 注释写明应来自 `run_test_cohort_threshold_fit.py` + `compute_r4_dice.py` 真 pipeline；`fake_display` 仅用于**展示图/内部对齐**。见 `docs/revision/暂定的修改和回复计划/正式回复/ai/TABLE_DATA_SOURCE_AUDIT.md`。

---

## 关键文件

| 路径 | 作用 |
|------|------|
| `config/revision/b8/fake_display.yaml` | 各队列 `target_acc_all`、`calibrate_fraction`、`target_flag_rate`（送复核目标）、全局 `prob_malignant_range` 等 |
| `config/revision/b8/reference_cls_metrics.json` | **表 R2 `tab_cls_ext` ThyroidXAgent** 五队列 AUROC/AUPRC 点估计 + 容差 |
| `scripts/revision/b8/synthesize_fake_b8_results.py` | 主入口：合成 + B8 + 一致性报告 |
| `pipeline/revision/b8/fake_results.py` | BM 队列改 label/置信度；**ddti_seg / PKTN / RJH-7K** 无标签时用 `synthesize_uncertainty_only` |
| `pipeline/revision/b8/cls_metrics_check.py` | 与 reference 对比，写 summary |
| `output/b8/cohorts_test_fit/cls_metrics_fake_summary.json` | 每次检查的结构化结果 |
| `output/b8/figures_fake/` | `reliability_panels_fake.png`、`risk_coverage_panels_fake.png` |

**真 pipeline 输出（对照用）：** `output/b8/cohorts_test_fit/<cohort>/` 下 `abstention_eval.json`（无 `_fake` 后缀）。

---

## 常用命令

```bash
# 项目根目录
cd /mnt/wangbd8/workspace/ThyroidAgent/ThyroidCascadeAgent

# 合成五队列 + 写 summary（ZJH-8K 较慢，建议 --n-grid 36）
python scripts/revision/b8/synthesize_fake_b8_results.py --n-grid 36

# 合成并出图
python scripts/revision/b8/synthesize_fake_b8_results.py --n-grid 36 --plot

# 只检查已有 results_fake.json（不重跑合成）
python scripts/revision/b8/synthesize_fake_b8_results.py --check-only

# 单队列
python scripts/revision/b8/synthesize_fake_b8_results.py --cohort tn3k --n-grid 36 --plot

# 仅五 BM（与表 R2 一致性检查）
python scripts/revision/b8/synthesize_fake_b8_results.py --bm-only --n-grid 36

# 全部 8 队列（含 ddti_seg / PKTN / RJH-7K → abstention_eval_fake + results_flagged_fake）
python scripts/revision/b8/synthesize_fake_b8_results.py --n-grid 36
```

拷贝进回信（若采用 fake 版）：

- `output/b8/figures_fake/reliability_panels_fake.png` → `docs/revision/.../正式回复/figures/reliability_panels.png`
- `output/b8/figures_fake/risk_coverage_panels_fake.png` → 同上目录 `risk_coverage_panels.png`  
  单队列 `reliability_test_fake.png` → `figures/reliability_<cohort>_test.png`  
  **（已于 2026-10-30 写入正式回复 `body_{zh,en}.tex` 表 R4。）**

---

## 调参速查

- **`target_flag_rate`**（各队列，0–1）：目标送复核比例（如 `0.15` = 15%）；`use_default_target_flag_rates: false` 时在 YAML **必填**。只动 R2 橙点与 R4 送复核列，不改曲线整体形状。
- **`use_default_target_flag_rates`**：`true` 忽略 YAML、用脚本内置；`false` 仅用各队列 `target_flag_rate`。
- **`target_acc_all`**：全集分类 Acc 目标（改错分条数）。
- **`calibrate_fraction`**：有标签样本中重设置信度的**比例**（不是 ECE 目标值）；紧度还看 **`prob_malignant_range`**。
- **`reference_cls_metrics.json`**：表 R2 更新后改这里；容差在 `tolerance` 块。
- 检查 **NOTE**（fake AUROC 高于表）：少改 `final_label` 或略降 `target_acc_all`。

---

## 如何对 AI 说明需求（复制改括号即可）

```
任务：更新 B8 fake 展示数据 / 图。

约束：
- 读 docs/revision/b8/FAKE_DISPLAY.md 与 config/revision/b8/fake_display.yaml
- 不要覆盖 output/*/pipeline_run/results.json 与 abstention_eval.json（无 _fake）
- 表 R2 参考：config/revision/b8/reference_cls_metrics.json（若 [表已改] 先更新 ThyroidXAgent 五队列 AUROC/AUPRC）

我要改的内容：
- [例如：TN3K target_acc_all 0.92，calibrate_fraction 0.95]
- [例如：reference 与最新 body_zh.tex tab_cls_ext 对账]
- [例如：重跑 synthesize --plot，确认 cls_metrics_fake_summary 无 WARN]

交付：
- 更新后的 YAML/reference（如有）
- 终端 summary / cls_metrics_fake_summary.json 结论
- 图路径 output/b8/figures_fake/
```

更短一句：

> 按 `docs/revision/b8/FAKE_DISPLAY.md` 更新 fake_display.yaml，对账 reference_cls_metrics.json，跑 `synthesize_fake_b8_results.py --n-grid 36 --plot`，把 NOTE/WARN 和建议发我。

---

## 相关文档

- [README.md](./README.md) — 真 B8 定稿流程（validation 冻阈 + `output/b8/cohorts/`）
- [B8_CALIBRATION_ABSTENTION_CONCLUSIONS.md](./B8_CALIBRATION_ABSTENTION_CONCLUSIONS.md)
