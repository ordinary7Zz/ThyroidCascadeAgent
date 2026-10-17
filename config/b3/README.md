# B3 路由消融配置

每个测试队列一个 YAML：`config/b3/<cohort_id>.yaml`。

| 文件 | 队列 | B3 task | Phase 1–2 参考 |
|------|------|---------|----------------|
| `sample.yaml` | 开发集 10 例 | both | `config/config_test.yaml` |
| `tn3k.yaml` | TN3K test | both | `config/config_TN3K.yaml` |
| `tn5k.yaml` | TN5K test | both | `config/config_TN5K.yaml` |
| `thyroidxl.yaml` | ThyroidXL test | both | `config/config_ThyroidXL.yaml` |
| `zjh8k.yaml` | ZJH-8K | both | `config/config_ZJH-8K.yaml` |
| `rjh7k.yaml` | RJH-7K（无 BM 标签） | both | `config/config_RJH-7K.yaml` |
| `ddti_seg.yaml` | DDTI `all_seg` | **seg** | 独立 `output/DDTI_seg/pipeline_run` |
| `ddti_cls.yaml` | DDTI_Classification `all/` | **cls** | 独立 `output/DDTI_cls/pipeline_run` |
| `pktn.yaml` | PKTN test（仅 mask） | **seg** | 独立 `output/PKTN/pipeline_run` |
| `nhc_misd_tus.yaml` | NHC-MISD-TUS | both | 数据不在本机时可跳过 |

- **模板**：`sample.yaml`；同步：`python scripts/generate_ablation_configs.py`
- **专家池**：`sample.yaml` 模板为 **5 个分割 DINO-UNet**（不含 Cine-Clip）+ **4 个分类 DINO multitask**；各队列 yaml 由模板生成。换池后须重跑 Phase 1–2 写满 `shared_intermediate`。
- **波次 1**：`run_b3_batch.py --preset wave1` 或 `./scripts/run_b3_wave1_all_cohorts.sh`

```bash
python scripts/run_b3_batch.py --config config/b3/ddti_seg.yaml --preset wave1 --force-phase3 --summarize --task seg
python scripts/run_b3_batch.py --config config/b3/ddti_cls.yaml --preset wave1 --force-phase3 --summarize --task cls
python scripts/run_b3_batch.py --config config/b3/pktn.yaml --preset wave1 --force-phase3 --summarize --task seg

# Phase 1–2 多专家缓存（串行 run_pipeline）：
./scripts/run_pipeline_all_cohorts.sh --exclude tn3k   # 已在跑可跳过

# B3 波次 1（须先有 shared_intermediate）：
./scripts/run_b3_wave1_all_cohorts.sh
```
