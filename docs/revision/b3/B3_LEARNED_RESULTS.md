# B3 路由消融 — 策略 6（学习型路由 / learned）

> **用途**：回应 **R1.2、R2.8、R3.1** 中「学习型路由」一行；与波次 1 静态策略（`B3_WAVE1_RESULTS.md`）并列。  
> **原始数据**：`output/ablation/b3/<cohort>/learned/b3_metrics.json`；本目录 `tables/b3_learned_*.csv` 由 `scripts/export_b3_learned_tables.py` 导出。  
> **回复信 LaTeX 表**：手改 `docs/revision/.../latex/generated/routing_ablation_tables_{zh,en}.tex`（R13–R14，含策略 6 列）；数字对照本页与 `tables/b3_learned_*.csv`。  
> **生成说明**（冻结于 **2026-10-26**）：验证集拟合 **多项逻辑回归**（`fit_learned_router.py`）；测试集推理为 **static bundle 快速路径**（`run_learned_b3.py`，`phase3_expert_judge=false`）。**95% CI** 与波次 1 相同：**cluster bootstrap**（1000 次，seed=42）。ZJH-8K / ThyroidXL 使用 B2 cluster map；其余队列一图一簇。  
> **表内数值**：Dice / AUROC / AUPRC / HD95 与回复信 R14–R15 一致，均为 **比例制四位小数**（Dice 0.8452 = 84.52%，非稿面 Table S3 的百分数 85.28）。

---

## 1. 覆盖范围

| 队列 | *n*（测试） | 任务 | learned 状态 | Val intermediate（拟合） |
|------|------------|------|--------------|---------------------------|
| **TN3K** | 614 | seg + cls | ✅ | `output/validation/_parts/tn3k`（及 config `val_list`） |
| **TN5K** | 1,000 | seg + cls | ✅ | `output/validation/_parts/tn5k` |
| **ThyroidXL** | 2,090 | seg + cls | ✅ | `output/validation/_parts/thyroidxl` |
| **PKTN** | 150 | **seg only** | ✅ | `output/validation/_parts/pktn` |
| **DDTI (seg)** | 637 | **seg only** | ✅ | `output/validation/_parts/ddti_seg` |
| **DDTI (cls)** | 349 | **cls only** | ✅ | `output/validation/_parts/ddti_cls` |
| **ZJH-8K** | 7,958 | seg + cls | ✅ | `b3_reinfer/chunk_07`（holdout fit） |
| **RJH-7K** | 7,288 | **seg only** | ✅ | `b3_reinfer/chunk_07`（holdout fit） |
| NHC-MISD-TUS | — | — | ⏳ 未跑 | 未纳入 wave3 |
| **策略 7（LLM）** | — | — | ✅ 稿面 Table S3/S4 | 见 [**B3_LLM_RESULTS.md**](./B3_LLM_RESULTS.md)（非 learned） |

队列元数据：`config/revision/b3/learned_wave3_cohorts.yaml`。批量：`scripts/revision/b3/run_learned_wave3_{standard,chunks}.sh`。

---

## 2. 表 A — 分割（学习型路由，全测试集）

**格式**：点估计 **(95% CI 下限–上限)**。CSV：`tables/b3_learned_segmentation.csv`。

| 队列 | Dice ↑ | HD95 ↓ (mm) |
|------|--------|-------------|
| TN3K (*n*=614) | 0.8452 (0.8315–0.8572) | 10.5189 (9.1745–12.2149) |
| TN5K (*n*=1,000) | 0.8309 (0.8168–0.8442) | 8.4157 (7.4267–9.4981) |
| ThyroidXL (*n*=2,090) | 0.8618 (0.8534–0.8689) | 6.5732 (5.9289–7.3309) |
| PKTN (*n*=150) | 0.8136 (0.7793–0.8411) | 9.8351 (7.0586–13.1820) |
| DDTI seg (*n*=637) | 0.8535 (0.8422–0.8635) | 8.7226 (7.7636–9.8345) |
| ZJH-8K (*n*=7,958) | 0.8392 (0.8323–0.8459) | 13.0973 (12.2670–13.8631) |
| RJH-7K (*n*=7,288) | 0.9086 (0.9063–0.9109) | 2.6545 (2.4865–2.8439) |

---

## 3. 表 B — 分类（学习型路由，全测试集）

CSV：`tables/b3_learned_classification_full.csv`。PKTN / RJH-7K / DDTI seg **无分类标签**，不列入本表。

| 队列 | AUROC ↑ | AUPRC ↑ |
|------|---------|---------|
| TN3K (*n*=614) | 0.8141 (0.7782–0.8479) | 0.7591 (0.7019–0.8114) |
| TN5K (*n*=1,000) | 0.9509 (0.9352–0.9643) | 0.9800 (0.9726–0.9865) |
| ThyroidXL (*n*=2,090) | 0.9158 (0.8980–0.9319) | 0.8994 (0.8733–0.9226) |
| DDTI cls (*n*=349) | 0.7506 (0.6700–0.8257) | 0.3166 (0.2155–0.4686) |
| ZJH-8K (*n*=7,958) | 0.9572 (0.9496–0.9646) | 0.9671 (0.9590–0.9746) |

---

## 4. 表 C — 分类 Path B 子集（学习型路由）

CSV：`tables/b3_learned_classification_path_b.csv`。

| 队列 | *n* Path B | AUROC ↑ |
|------|------------|---------|
| TN3K | 279 | 0.6766 (0.6146–0.7436) |
| TN5K | 404 | 0.8730 (0.8366–0.9086) |
| ThyroidXL | 921 | 0.7387 (0.7005–0.7779) |
| DDTI cls | 223 | 0.7575 (0.6783–0.8315) |
| ZJH-8K | 4,102 | 0.9200 (0.9061–0.9320) |

---

## 5. 与波次 1 的简要对照（便于写回复信）

1. **分割**：学习型路由在 TN3K/TN5K 上与 **软投票/最优单专家** 同量级（例如 TN5K learned Dice 0.831 vs 波次 1 最优单专家 0.830），明显优于 **最大置信度**（0.631）；仍低于 **Oracle**（0.878）。RJH-7K 上 learned Dice 0.909 接近院内大队列上静态策略水平，但队列间 **不可直接横比** 数据分布。
2. **分类**：TN3K learned 全量 AUROC 0.814，介于波次 1 软投票（0.828）与静态规则之间；TN5K learned 0.951 与静态策略并列高位；ZJH-8K learned 0.957 与波次 1 最优静态接近。DDTI cls 样本少、AUPRC 宽 CI，宜在正文强调 *n* 与外部验证语境。
3. **Path B**：学习型路由在 Path B 上 AUROC 仍低于全量（共识稀释消失后），与波次 1 模式一致；TN3K Path B learned 0.677 vs 全量 0.814。
4. **策略 7（LLM）** 见 [**B3_LLM_RESULTS.md**](./B3_LLM_RESULTS.md)（= 主文 Table S3/S4）；回复信 R14–R15 已与 learned 并列导出，勿与本表 learned 行混读。

---

## 6. 复现命令

```bash
# Val intermediate（DDTI 示例）
python run_pipeline.py --config config/revision/validation/ddti_seg.yaml --device cuda
python run_pipeline.py --config config/revision/validation/ddti_cls.yaml --device cuda

# 单 cohort
python scripts/revision/b3/run_learned_cohort.py \
  --manifest config/revision/b3/learned_wave3_cohorts.yaml \
  --cohort-meta tn5k --device cpu

# 批量（仅 DDTI）
COHORTS="ddti_seg ddti_cls" DEVICE=cpu bash scripts/revision/b3/run_learned_wave3_standard.sh

# 刷新本目录 CSV
python docs/revision/b3/scripts/export_b3_learned_tables.py

# 回复信 R13–R14：在 latex/generated/routing_ablation_tables_*.tex 中手改
```

**实现备注**：`ddti_cls` 等 **cls-only** val 无 `intermediate/seg` 时，`routing/learned_router.py` 从各专家 `cls/*.json` 的图像名交集对齐（2026-10-26 修复）。

---

## 7. 文件索引

| 文件 | 内容 |
|------|------|
| `tables/b3_learned_segmentation.csv` | 策略 6 分割 |
| `tables/b3_learned_classification_full.csv` | 策略 6 全量分类 |
| `tables/b3_learned_classification_path_b.csv` | 策略 6 Path B |
| `tables/b3_learned_cohort_meta.csv` | *n*、Path B 例数 |
| `B3_WAVE1_RESULTS.md` | 策略 1–5、8（静态 + Oracle） |
| `B3_LLM_RESULTS.md` | 策略 7（稿面 ThyroidXAgent） |
| `REVIEWER_RESPONSE_SNIPPETS_B3.md` | 回复信段落（含 learned + LLM 草稿） |
