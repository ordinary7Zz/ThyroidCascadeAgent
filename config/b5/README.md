# B5 路由元数据消融

- 计划：`docs/REVISION_B5_PLAN.md`
- **数据路径**：已对齐 `scripts/build_all_test_for_llm.sh` 产出的 `*_for_llm_malignancy` 子集（约 250 张；PKTN 为全量 150）。
- **任务开关**：`ddti_seg` / `pktn` / `rjh7k` 仅分割；`ddti_cls` 仅分类；其余 `both`。
- **未建 for_llm 子集**：`sample.yaml`、`nhc_misd_tus.yaml` 仍指向全量测试路径。

```bash
python scripts/revision/b5/run_b5_batch.py --config config/b5/tn3k.yaml --force-phase3 --skip-full
```

- 汇总：`python scripts/revision/b5/build_b5_tables.py --root output/ablation/b5`

`metadata_mode`：`full` | `drop_device` | `drop_source` | `drop_both` | `quality_only`
