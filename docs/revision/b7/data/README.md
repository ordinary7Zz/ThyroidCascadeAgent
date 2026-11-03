# NHC 补充表 S7–S12 → 回信 `tab_nhc_*`

真源与稿面 **Supp. S7–S12** 相同：可直接解析 `docs/per_center_tables.tex`（ThyroidXAgent 列），或从 `my_Thyroid_Infer/analyze_center_performance.py` 读 `results/私有数据集结果/results` 导出 CSV。

## 1. 导出 CSV（在含完整私有外测结果的机器上）

```bash
cd /path/to/my_Thyroid_Infer
python analyze_center_performance.py \
  --results_dir results/私有数据集结果/results \
  --output_csv /path/to/ThyroidCascadeAgent/docs/revision/b7/data/per_by_center_manuscript.csv
```

也可把已有 `per_by_center_ci.csv`（饼图/Fig.2h 同源）中**按中心段**转为同格式，或从 `my_papers/.../data/per_by_center_ci.csv` 复制后跑 analyze 脚本重新导出长表。

## 2. 写入回信 TeX（只改 `% BEGIN/END AUTO` 块）

**推荐**（仓库已有 `docs/per_center_tables.tex` 时，默认优先 TeX）：

```bash
cd /path/to/ThyroidCascadeAgent
python scripts/revision/b7/render_nhc_b7_tables_from_supplement.py --apply
```

或显式指定 CSV：

```bash
python scripts/revision/b7/render_nhc_b7_tables_from_supplement.py \
  --csv docs/revision/b7/data/per_by_center_manuscript.csv \
  --apply
```

或一步（本机有 `results/私有数据集结果`）：

```bash
python scripts/revision/b7/render_nhc_b7_tables_from_supplement.py \
  --results-dir ../my_Thyroid_Infer/results/私有数据集结果/results \
  --apply
```

产出：

- `docs/revision/b7/artifacts/nhc_supplement_b7_summary.json`
- 更新 `latex/generated/nhc_b7_tables_{zh,en}.tex` 的三个 AUTO 块（**不**动表注里的 G3 `\rpending`、不动 `body_*.tex`）

## 3. 统计口径

| 列 | TeX 路径 | CSV 路径 |
|----|----------|----------|
| 全腺体 / 结节 Dice | Supp. 表 ThyroidXAgent 列 | `dinov3_unet` |
| 良恶性 AUROC | 同上 | `dinov3_unet_multitask` |

- **宏平均**：35 中心**等权**（R2.7 与跨队列 macro 一致）。
- **池化行**：TeX 路径使用 S 表 **Overall** 行（与稿面 59.28% / 82.31% / 0.819 一致）；CSV 路径为按中心 $n$ 加权均值。
- **$I^2$/$\tau^2$**：中心级 meta（非逐图 B7 `heterogeneity_i2_tau2`）。

## 4. 当前仓库状态

有 `docs/per_center_tables.tex` 时运行 `--apply` 即可填入中心性能与异质性 AUTO 块；无 TeX 且无 CSV 时 AUTO 块保持占位。
