# B3 路由消融 — 策略 7（LLM / 全系统 ThyroidXAgent）

> **用途**：B3 八策略表中的 **「完整 ThyroidXAgent (7)」** 行；与投稿主文 **Table S3（分割）**、**Table S4（分类）** 的 **ThyroidXAgent** 行一致，**非** `output/ablation/b3/*/llm/` 重跑。  
> **数据源**：`manuscript_llm_metrics.yaml`（自 `docs/ThyroidXAgent.md` 转录，冻结 **2026-10-26**）。  
> **CSV**：`python docs/revision/b3/scripts/export_b3_llm_tables.py` → `tables/b3_llm_*.csv`。  
> **策略 6（learned）** 为修订消融独立结果，见 [`B3_LEARNED_RESULTS.md`](./B3_LEARNED_RESULTS.md)；勿与本文档混读。

---

## 1. 口径说明

| 项 | 说明 |
|----|------|
| 与 B3 波次 1 / learned | 稿面全系统在主文专家池与评测协议下报告；修订静态/learned 在 **固定 Phase 1–2 intermediate** 上换路由。表内并列是为审稿人对比 **路由族**，非断言数值逐位相等。 |
| CI | 稿面表为 **mean ± 半宽**（caption 为 95% CI）；本目录统一为 **点估计 (下限–上限)**，四位小数（Dice/AUROC/AUPRC）；HD95 单位为 mm。 |
| Path B | 主文 Table S3/S4 **未**分列 Path B；B3 回复信 Path B 行仅适用于 **波次 1 / learned** 等消融跑数。 |
| NHC-MISD-TUS | 主文 Fig./补充有全系统结果；未纳入下表（与当前 B3 cohort 列表一致）；需入表时从稿面单独转录。 |

---

## 2. 表 A — 分割（策略 7，全测试集）

CSV：`tables/b3_llm_segmentation.csv`。来源：**Table S3** ThyroidXAgent 行。

| 队列 | Dice ↑ | HD95 ↓ (mm) |
|------|--------|-------------|
| TN3K (*n*=614) | 0.8528 (0.8400–0.8656) | 10.3100 (8.6100–12.0100) |
| ThyroidXL (*n*=2,090) | 0.8758 (0.8714–0.8802) | 5.4300 (4.9000–5.9600) |
| PKTN (*n*=150) | 0.8299 (0.8089–0.8509) | 9.0100 (5.4300–12.5900) |
| TN5K (*n*=1,000) | 0.8326 (0.8192–0.8460) | 10.1200 (8.8900–11.3500) |
| DDTI seg (*n*=637) | 0.8562 (0.8455–0.8669) | 9.2400 (8.1700–10.3100) |
| ZJH-8K (*n*=7,958) | 0.9430 (0.9392–0.9468) | 2.2500 (1.8600–2.6400) |
| RJH-7K (*n*=7,288) | 0.9146 (0.9132–0.9160) | 1.9200 (1.8400–2.0000) |

---

## 3. 表 B — 分类（策略 7，全测试集）

CSV：`tables/b3_llm_classification_full.csv`。来源：**Table S4** ThyroidXAgent 行。无 cls 的队列（PKTN、RJH-7K、DDTI seg）不列入。

| 队列 | AUROC ↑ | AUPRC ↑ |
|------|---------|---------|
| TN3K (*n*=614) | 0.8692 (0.8343–0.9041) | 0.8545 (0.7945–0.9145) |
| ThyroidXL (*n*=2,090) | 0.9676 (0.9610–0.9742) | 0.9653 (0.9575–0.9731) |
| TN5K (*n*=1,000) | 0.9472 (0.9320–0.9624) | 0.9752 (0.9663–0.9841) |
| DDTI cls (*n*=349) | 0.7991 (0.7250–0.8732) | 0.5863 (0.4483–0.7243) |
| ZJH-8K (*n*=7,958) | 0.9175 (0.9008–0.9342) | 0.9711 (0.9705–0.9717) |

---

## 4. 与策略 6（learned）对照（TN3K 分割 Dice 示例）

| 策略 | TN3K Dice | 含义 |
|------|-----------|------|
| **7 LLM（本文）** | **0.8528** | 稿面全系统 LLM 路由 |
| **6 learned** | 0.8452 | 修订消融：验证集 LR 路由 + bundle 推理 |

二者为 **不同策略**；learned 低于稿面 LLM 并不矛盾。

---

## 5. 复现与更新

```bash
# 刷新 CSV（改 yaml 后）
python docs/revision/b3/scripts/export_b3_llm_tables.py

# 回复信 LaTeX（策略 7 读 yaml）
# 回复信策略 7 列：手改 latex/generated/routing_ablation_tables_*.tex
```

若主文表数字修订，只改 `manuscript_llm_metrics.yaml` 并重新导出；**无需** API 重跑。

---

## 6. 文件索引

| 文件 | 内容 |
|------|------|
| `manuscript_llm_metrics.yaml` | 策略 7 机读指标 |
| `tables/b3_llm_segmentation.csv` | 分割 |
| `tables/b3_llm_classification_full.csv` | 全量分类 |
| `tables/b3_llm_cohort_meta.csv` | *n*、来源标记 |
| `B3_LEARNED_RESULTS.md` | 策略 6 |
| `B3_WAVE1_RESULTS.md` | 策略 1–5、8 |
