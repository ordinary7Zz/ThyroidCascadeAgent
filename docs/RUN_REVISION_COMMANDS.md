# 返修实验执行命令（Runbook）

**脚本总索引（按 B1–B12 归类、推荐入口）**：[`scripts/README_REVISION.md`](../scripts/README_REVISION.md) · **Pipeline 模块**：[`pipeline/README.md`](../pipeline/README.md) · **逻辑目录**：[`scripts/revision/README.md`](../scripts/revision/README.md)

按 **任务编号（B1、B2、…）** 分节收录可复制命令与推荐顺序；新任务在文末追加新节即可。各任务 **契约与交付物** 见对应 `docs/REVISION_*_PLAN.md`。

| 节 | 任务 | 计划文档 | 状态 |
|----|------|----------|------|
| §1 | 共享地基 | — | 已写 |
| §2 | B3 路由消融 | `REVISION_B3_B4_PLAN.md` | 已写 |
| §3 | B4 组件消融 | `REVISION_B3_B4_PLAN.md` | 已写 |
| §4 | B5 元数据消融 | `REVISION_B5_PLAN.md` | 已写 |
| §5 | B6 路由器透明性 | `REVISION_B6_PLAN.md` | 已写 |
| — | B7 / B8 / … | `REVISION_B7_B8_PLAN.md` 等 | 待追加 |

配置目录：`config/b3/`、`config/b4/`、`config/b5/`（后续任务可增 `config/b7/` 等）。

---

## 0. 环境与变量

```bash
cd /mnt/wangbd8/workspace/ThyroidAgent/ThyroidCascadeAgent

export DASHSCOPE_API_KEY='…'          # B3 波次 2 / B5 / B6 稳定性需要
export PYTHON=python3
export DEVICE=cuda                    # learned 可用 cpu
# 可选：export REPO_ROOT=$PWD
```

---

## 1. 共享地基（多任务共用）

### 1.1 LLM 子集（B5 默认路径；B3 仍可用全量 test）

```bash
bash scripts/build_all_test_for_llm.sh
# 或：LABEL_KEY=malignancy bash scripts/build_all_test_for_llm.sh
```

说明见 `scripts/README_test_for_llm.md`。`sample`、`nhc_misd_tus` 未包含在批量脚本中。

### 1.2 Phase 1–2：写满各队列 `shared_intermediate`

与 B3 默认队列一致（不含 NHC）：

```bash
./scripts/run_pipeline_all_cohorts.sh
./scripts/run_pipeline_all_cohorts.sh --exclude tn3k          # 已在跑可跳过
./scripts/run_pipeline_all_cohorts.sh --from ddti_seg --continue-on-error
```

单队列：

```bash
python run_pipeline.py --config config/b3/tn3k.yaml --device cuda
```

日志：`output/_pipeline_batch_logs/`。完成标准见脚本内 `phase12_complete`（`intermediate/seg/*.npz`、`intermediate/cls/*.json` 齐全）。

### 1.3 B3 策略 1：`best_single`（验证集选专家）

```bash
python scripts/revision/b3/fit_best_single_expert.py \
  --config config/b3/tn3k.yaml \
  --intermediate "$(python -c "import yaml; c=yaml.safe_load(open('config/b3/tn3k.yaml')); print(c['pipeline']['ablation']['shared_intermediate'])")" \
  --out artifacts/best_single_tn3k.json
```

`run_routing_ablation` 默认会读 `artifacts/best_single.json`；多队列可 `--best-single-artifact` 指定。

### 1.4 默认队列与 ablation task

| `cohort_id` | B3 `task` | 备注 |
|-------------|-----------|------|
| `tn3k`, `tn5k`, `thyroidxl`, `zjh8k`, `sample` | `both` | |
| `rjh7k` | `both`（无 BM 标签时分类指标受限） | |
| `ddti_seg`, `pktn` | `seg` | 无分类标签，不做 cls 消融 |
| `ddti_cls` | `cls` | 无 mask，不做 seg 消融 |
| `nhc_misd_tus` | `both` | 数据/政策按需；B5 计划含 NHC |

B5 同名 yaml 在 `config/b5/`；`rjh7k` / `ddti_*` / `pktn` 的 `run_classification` / `task` 与上表一致。

---

## 2. B3　八种路由策略（波次 0–3）

**输出根目录**（默认）：`output/ablation/b3/<cohort_id>/<routing_mode>/`  
**汇总表**：`output/ablation/b3/<cohort_id>/_summary/b3_routing_table.csv`（`--summarize` 或 `python -m pipeline.ablation_summary --root …`）  
**论文/回复用结论表**（波次 1 部分队列）：[`docs/revision/b3/B3_WAVE1_RESULTS.md`](revision/b3/B3_WAVE1_RESULTS.md)

### 2.1 波次 1：六种非 LLM + Oracle（推荐 static bundle）

全队列串行：

```bash
./scripts/revision/b3/run_b3_wave1_all_cohorts.sh
./scripts/revision/b3/run_b3_wave1_all_cohorts.sh --exclude tn3k --skip-complete
./scripts/revision/b3/run_b3_wave1_all_cohorts.sh --include-nhc
```

单队列：

```bash
python scripts/revision/b3/run_b3_batch.py \
  --config config/b3/tn3k.yaml \
  --preset wave1 \
  --force-phase3 \
  --summarize \
  --task both
```

仅分割 / 仅分类：

```bash
python scripts/revision/b3/run_b3_batch.py --config config/b3/ddti_seg.yaml --preset wave1 --force-phase3 --summarize --task seg
python scripts/revision/b3/run_b3_batch.py --config config/b3/ddti_cls.yaml --preset wave1 --force-phase3 --summarize --task cls
```

`wave1` 含：`soft_voting`, `majority`, `max_confidence`, `static_rule`, `best_single`, `oracle`。

**与 B2 对齐的 cluster-bootstrap CI**（不重跑路由，只刷新 `b3_metrics.json` / `_summary`）：

```bash
python scripts/revision/b3/recompute_b3_cluster_ci.py --config config/b3/tn3k.yaml --summarize
python scripts/revision/b3/recompute_b3_cluster_ci.py --all-wave1 --summarize
# 大队列日志：output/ablation/b3/_batch_logs/recompute_cluster_ci_all.log
```

无 patient map 的队列（TN3K/TN5K/DDTI/PKTN/RJH 等）**一图一簇**，CI 与旧图像级 bootstrap **一致**；**ZJH-8K / ThyroidXL** 使用 `docs/revision/b2/cluster_maps/*.json`，CI 会略宽。`eval_merged_b3_cohort.py` 与新跑 learned 的 eval 默认已走同一口径。

**大队列（ZJH-8K / RJH-7K）**：`static_rule` 默认 **inter-expert agreement**（无 radiomics judge），与 fast5 同属 npz 轻量扫图。可一次 `--preset wave1`，或仍拆两趟仅为 **内存/断点** 方便：

```bash
# 一次波次 1（推荐，static_rule 不再单独拖慢）
python scripts/revision/b3/run_b3_batch.py --config config/b3/zjh8k.yaml \
  --preset wave1 --force-phase3 --summarize --device cpu \
  2>&1 | tee output/ablation/b3/_batch_logs/zjh8k_wave1.log

# 或拆两趟（可选）
# --modes soft_voting,majority,max_confidence,best_single,oracle,static_rule
```

完整静态级联（含 Radiomics 裁判）仅在做对照时开启：`pipeline.ablation.static_rule_use_radiomics_judge: true`。

监视：`./scripts/revision/b3/zjh/watch_b3_bundle_progress.sh zjh8k 30`（读 `.bundle_progress.json`）。

对拍（每策略单独子进程，较慢）：

```bash
python scripts/revision/b3/run_b3_batch.py --config config/b3/sample.yaml --preset wave1 --force-phase3 --legacy-subprocess
```

### 2.2 波次 2：策略 7 `llm`（勿用 static bundle）

须设 `DASHSCOPE_API_KEY`。`run_routing_ablation` 会在 `routing_mode=llm` 时自动 `enable_agent=true`。配置中建议 `pipeline.log_routing: true`（B6 日志）。

```bash
python scripts/run_routing_ablation.py \
  --config config/b3/tn3k.yaml \
  --routing-mode llm \
  --task both \
  --shared-intermediate output/TN3K/pipeline_run/intermediate \
  --output-dir output/ablation/b3/tn3k/llm \
  --force-phase3 \
  --device cuda
```

`shared-intermediate` / `output-dir` 以各 yaml 的 `pipeline.ablation` 为准（勿硬编码路径时可从 config 读取）。

### 2.3 波次 3：策略 6 `learned`

每队列在 `config/b3/<cohort>.yaml` 配好 `val_list`、`val_data`（valid 的 mask/label）、`val_intermediate`（valid 的 Phase 1–2），以及 **每队列独立** `learned_router.*_artifact`（如 `artifacts/b3/tn3k/`）。

生成 `val_list`：

```bash
python scripts/revision/b3/export_val_list.py \
  --image-dir /mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/TN3K/valid/images \
  --out config/revision/b3/val_lists/tn3k.json
```

**一键（valid fit → test infer → eval）：**

| 队列 | val intermediate | n | 脚本 |
|------|------------------|---|------|
| TN3K | `output/validation/_parts/tn3k/intermediate` | 100 | `bash scripts/revision/b3/run_learned_tn3k.sh` |
| TN5K | `output/validation/_parts/tn5k/intermediate` | 525 | `bash scripts/revision/b3/run_learned_tn5k.sh` |
| ThyroidXL | `output/validation/_parts/thyroidxl/intermediate` | 100 | `bash scripts/revision/b3/run_learned_thyroidxl.sh` |

`output/validation/_parts/` 另有 **pktn**（无 TN3K 式双 split 时需单独配 val）。

或分步（fit 用 valid intermediate + `val_data`；推理用 **test** intermediate）：

```bash
python scripts/revision/b3/fit_learned_router.py --config config/b3/tn3k.yaml
# 默认读 ablation.val_intermediate；也可 --intermediate output/validation/_parts/tn3k/intermediate

python scripts/revision/b3/run_learned_b3.py \
  --config config/b3/tn3k.yaml \
  --shared-intermediate output/TN3K/pipeline_run/intermediate \
  --output-dir output/ablation/b3/tn3k/learned \
  --force-phase3 \
  --device cpu

python scripts/revision/b3/eval_merged_b3_cohort.py \
  --config config/b3/tn3k.yaml \
  --root output/ablation/b3/tn3k \
  --modes learned
```

`sample` 调试：`val_list` 见 `config/revision/b3/val_lists/sample.json`（7/10 图），fit 与 infer 共用 `output/sample/pipeline_run/intermediate`。

### 2.4 单次消融（任意 mode）

```bash
python scripts/run_routing_ablation.py \
  --config config/b3/sample.yaml \
  --routing-mode static_rule \
  --task both \
  --shared-intermediate output/sample/pipeline_run/intermediate \
  --output-dir output/ablation/b3/sample/static_rule \
  --force-phase3
```

异构 seg/cls：

```bash
python scripts/run_routing_ablation.py \
  --routing-mode-seg llm \
  --routing-mode-cls soft_voting \
  ...
```

---

## 3. B4　组件消融（L1–L3 + Path B 附录）

**配置**：`config/b4/<cohort>.yaml`（`pipeline.ablation_b4` 指向 B3 的 `soft_voting` / `llm` 等目录）。

### 3.1 L2 / L3

- **L2**：B3 `soft_voting` 的 `results.json` / `b3_metrics.json`（跑完波次 1 即有）。
- **L3**：B3 `llm` 目录（跑完波次 2）。
- **L1**：单专家评测结果 JSON → `artifacts/b4_l1_<cohort>_placeholder.json`（正式队列替换为真实 `results_single_expert.json`）。

### 3.2 Path B 附录 B-b（无 LLM，含 AutoGluon）

```bash
python scripts/revision/b4/run_b4_pathb_appendix.py \
  --config config/b3/sample.yaml \
  --shared-intermediate output/sample/pipeline_run/intermediate \
  --output-dir output/ablation/b4/sample/path_b_autogluon \
  --seg-mode soft_voting \
  --force-phase3
```

与 L3 对齐时 `--seg-mode llm`（使用与 L3 相同的 mask 协议，见脚本注释与 `REVISION_B3_B4_PLAN.md` §5.1.2）。B-a / B-c 分别对应 B3 `soft_voting`（Path B cls）与 B3 `llm`。

### 3.3 汇总主表

```bash
python scripts/revision/b4/build_b4_tables.py --config config/b4/tn3k.yaml
# 或：--output-dir output/ablation/b4/tn3k
```

产物：`b4_component_table.csv`、`b4_pathb_radiomics_table.csv` 等（见 `pipeline/b4_summary.py`）。

### 3.4 S4 校验（可选）

`run_pipeline.py` + 投稿等价配置，输出目录如 `output/ablation/b4/<cohort>/s4_replica/`；应与 L3 **同 manifest、同指标**（见 B4 计划 §5.3）。

---

## 4. B5　路由元数据消融（固定 `llm`，五种 `metadata_mode`）

**配置**：`config/b5/<cohort>.yaml`  
**输出**：`output/ablation/b5/<cohort>/<metadata_mode>/`

`metadata_mode`：`full` | `drop_device` | `drop_source` | `drop_both` | `quality_only`

```bash
python scripts/revision/b5/run_b5_batch.py \
  --config config/b5/tn3k.yaml \
  --force-phase3 \
  --skip-full
```

- `--skip-full`：`full` 复用 B3 `output/ablation/b3/<cohort>/llm`，省 API。
- 子集 mode：`--modes drop_device quality_only`

**注意**：B5 图像列表为 for_llm 子集时，`shared_intermediate` 须对**同一批图像**跑过 Phase 1–2（或单独 pipeline_run），否则 Phase 3 索引会对不齐。见 `config/b5/README.md`。

### 4.1 汇总与选择偏差

```bash
python scripts/revision/b5/build_b5_tables.py --root output/ablation/b5
```

热图 / 互信息（需 `routing_log.jsonl`）：

```bash
python pipeline/analyze_routing_bias.py \
  --log output/ablation/b5/tn3k/drop_both/routing_log.jsonl \
  --labels /path/to/labels.json \
  --centre-key centre \
  --out output/ablation/b5/tn3k/drop_both/routing_bias.json \
  --heatmap output/ablation/b5/tn3k/drop_both/centre_expert_heatmap.png
```

---

## 5. B6　路由器透明性与稳定性

### 5.1 规格导出（无 GPU）

```bash
python scripts/revision/b6/export_router_spec.py \
  --config config/b3/sample.yaml \
  --out docs/supplementary/router_spec.md
```

### 5.2 全 pipeline 路由日志

在对应 config 中：

```yaml
pipeline:
  log_routing: true
  routing_log_include_prompts: false   # 样例审计可 true
```

跑 `run_pipeline.py` 或 `run_routing_ablation.py`（`llm`）后得到 `{output_dir}/routing_log.jsonl`。

### 5.3 5× 稳定性（复用 intermediate，仅重复 LLM 路由）

配置中分割/分类 `agent.enable_agent: true`（或仅用 B3/B5 的 llm 跑数 config）。

```bash
python run_routing_stability.py \
  --config config/b3/sample.yaml \
  --output-dir output/sample/pipeline_run \
  --repeats 5 \
  --max-cases 50 \
  --device cuda
```

产物：`stability_summary.json`（及可选 per-case jsonl）。分析仅针对 **曾调用 LLM** 的子集；Path A 一致短路不做 5×。

---

## 6. 推荐端到端顺序（单 cohort 示例 `tn3k`）

```bash
# 1) 地基
python run_pipeline.py --config config/b3/tn3k.yaml --device cuda
python scripts/revision/b3/fit_best_single_expert.py --config config/b3/tn3k.yaml --intermediate <yaml.shared_intermediate>

# 2) B3
python scripts/revision/b3/run_b3_batch.py --config config/b3/tn3k.yaml --preset wave1 --force-phase3 --summarize
python scripts/run_routing_ablation.py --config config/b3/tn3k.yaml --routing-mode llm \
  --task both --shared-intermediate <intermediate> --output-dir output/ablation/b3/tn3k/llm --force-phase3
python scripts/revision/b3/fit_learned_router.py --config config/b3/tn3k.yaml --intermediate <intermediate>
python scripts/revision/b3/run_learned_b3.py --config config/b3/tn3k.yaml --shared-intermediate <intermediate> \
  --output-dir output/ablation/b3/tn3k/learned --force-phase3 --device cpu

# 3) B4
python scripts/revision/b4/run_b4_pathb_appendix.py --config config/b3/tn3k.yaml --shared-intermediate <intermediate> \
  --output-dir output/ablation/b4/tn3k/path_b_autogluon --seg-mode llm --force-phase3
python scripts/revision/b4/build_b4_tables.py --config config/b4/tn3k.yaml

# 4) B5（for_llm 路径 + 对齐的 intermediate）
python scripts/revision/b5/run_b5_batch.py --config config/b5/tn3k.yaml --force-phase3 --skip-full
python scripts/revision/b5/build_b5_tables.py --root output/ablation/b5

# 5) B6（可与波次 2 同次 llm 跑数一并出 log；稳定性单独跑）
python scripts/revision/b6/export_router_spec.py --config config/b3/tn3k.yaml
python run_routing_stability.py --config config/b3/tn3k.yaml --output-dir <pipeline_output_dir> --repeats 5
```

全队列批量：**§1.2** → **`./scripts/revision/b3/run_b3_wave1_all_cohorts.sh`** → 各 cohort 波次 2/3/B5/B4 按需调度。

---

## 7. 配置同步

从模板重生成 B3/B4/B5 yaml（会覆盖手改路径，慎用）：

```bash
python scripts/generate_ablation_configs.py
```

---

## 8. 待追加任务（占位）

- **B7**（中心异质性 / meta）：命令见 `docs/REVISION_B7_B8_PLAN.md`，实现后在此节补全。
- **B8** 及后续：同上。

---

*路径以各 `config/b3|b4|b5/<cohort>.yaml` 为准；与仓库脚本同步维护本 Runbook。*
