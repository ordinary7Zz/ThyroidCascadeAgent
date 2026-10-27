# NHC 示例数据（10 图）— 配置与运行顺序

目的：在 `output/b7/nhc_prepared_smoke` 上跑通返修各任务**输出结构**（数值仅作样板）。  
索引：`config/revision/nhc_sample/manifest.yaml`

**NHC 模型范围**（必读）：[`MODEL_POLICY_ZH.md`](./MODEL_POLICY_ZH.md) — 仅本地专家 + `my_Thyroid_Infer/config.yaml` 九模型；**不**跑 GPT/Gemini/Qwen 等 LLM API。

GPU 环境见 `docs/revision/b7/NHC_GPU_AND_WEIGHTS_ZH.md`。

## 0. 预处理 + Cascade + B7（若尚未完成）

```bash
bash scripts/revision/b7/run_b7_sample_canonical.sh
```

## 1. B3（静态策略 + learned 推理，无 LLM）

配置：`config/revision/b3/nhc_prepared_sample.yaml`  
依赖：`output/b7/nhc_cascade_sample/intermediate`（与 Cascade 模型列表一致）  
learned：`pipeline.ablation.learned_router` 指向**开发队列**已拟合 joblib（不在 NHC 上 `fit_learned_router`）。

```bash
python scripts/revision/b3/run_b3_static_bundle.py \
  --config config/revision/b3/nhc_prepared_sample.yaml

python scripts/revision/b3/run_learned_b3.py \
  --config config/revision/b3/nhc_prepared_sample.yaml \
  --shared-intermediate output/b7/nhc_cascade_sample/intermediate \
  --output-dir output/ablation/b3/nhc_prepared_sample/learned \
  --force-phase3 --device cpu
```

产出：`output/ablation/b3/nhc_prepared_sample/{soft_voting,majority,...,learned}/`

## 2. B4 L1（单专家，无 LLM）

配置：`config/revision/b4/l1/nhc_prepared_sample.yaml`

```bash
python scripts/revision/b4/run_l1_cohort.py --cohort nhc_prepared_sample --fresh
```

产出：`output/ablation/b4/l1/nhc_prepared_sample/run1/`、`artifacts/b4_l1_nhc_prepared_sample.json`

汇总表（L1/L2 + Path B 结构；NHC 无 llm 时 L3/B-c 会告警缺行）：

```bash
python scripts/revision/b4/build_b4_tables.py \
  --config config/revision/b4/nhc_prepared_sample.yaml
```

产出：`output/ablation/b4/nhc_prepared_sample/b4_component_table.csv`、`b4_pathb_radiomics_table.csv`、`b4_build_report.json`

## 3. B8（OpenThyroid validation 冻结阈值 → NHC eval）

配置：`config/revision/b8/nhc_prepared_sample.yaml`  
阈值：`output/b8/fit/abstention_thresholds.json`（**不在 NHC 上定阈**）

```bash
python scripts/revision/b8/run_calibration_abstention.py --eval \
  --thresholds output/b8/fit/abstention_thresholds.json \
  --test-results output/b7/nhc_cascade_sample/results.json \
  --out output/b8/nhc_prepared_sample/eval_formal \
  --rule-subset nhc
```

产出：`output/b8/nhc_prepared_sample/eval_formal/`

## 4. B2（患者簇 = patient_id）

配置：`config/revision/b2/nhc_prepared_sample.yaml`  
簇映射：`config/revision/b2/nhc_prepared_sample.cluster_map.json`

```bash
python scripts/revision/b2/run_b2_cluster_metrics.py \
  --task both \
  --results output/b7/nhc_cascade_sample/results.json \
  --pipeline-dir output/b7/nhc_cascade_sample \
  --gt-mask-dir output/b7/nhc_prepared_smoke/nodule_masks \
  --cluster-map config/revision/b2/nhc_prepared_sample.cluster_map.json \
  --patient-level \
  --out output/b2/nhc_prepared_sample
```

## 5. 九模型 infer（my_Thyroid_Infer）

配置：`config/revision/infer/nhc_prepared_sample.yaml`（权重路径相对 **my_Thyroid_Infer** 根目录）

```bash
cd ../my_Thyroid_Infer
python run_all.py --config ../ThyroidCascadeAgent/config/revision/infer/nhc_prepared_sample.yaml \
  --tasks gland nodule binary tirads
```

产出：`my_Thyroid_Infer/results/nhc_prepared_sample/`
