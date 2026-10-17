# B7 / B8　NHC 异质性与校准·拒答（实施计划）

> **对应审稿意见**  
> - **B7**：R1.3（外部队列中心差异）、R2.6（NHC-MISD-TUS 描述与中心级结果）  
> - **B8**：R1.3（校准与低置信策略）、R1.6（拒答/强制复核与工作量，供 **F4** 临床安全叙事）  
>  
> **范围**：ThyroidCascadeAgent 以 **结节分割 + 良恶性分类** 为主；NHC **全腺体**分割（稿面 Table S7–S8、总体 Dice 59.28%）若本仓库无 GT/推理链，在 §3.4 单独标注数据来源，不与结节 pipeline 混为一谈。  
> **关联文档**：`docs/ThyroidXAgent_返修计划与回复_中文.md`（任务语义与回复草稿）、`docs/REVISION_B5_B6_B8_B11_PLAN.md`（B8 代码概要，本文件展开 B7 并统一验收）、`docs/REVISION_B3_B4_PLAN.md`（NHC 上 B3 跑数与 `intermediate/` 复用）。

---

## 1. 任务理解（是否对齐返修清单）

### 1.1 B7 在回答什么

审稿人认为：NHC-MISD-TUS 总体指标好看，但 **35 个中心之间差异极大**（例如结节 Dice 低至 45.53% 的 THYB_S_ZJ24；全腺体 Dice  pooled 仅 59.28%）。他们要求：

| 层次 | 要求 | 本任务含义 |
|------|------|------------|
| **描述** | 每个中心的患者数、结节数、图像数、扫描仪、标签可用性 | 补充表 + Methods/Results 文字（依赖 **G3** 中心元数据） |
| **汇总** | 中心级 **宏平均**性能；随机效应合并得到 **I²、τ²** | 不能只用 8,721 张图拼成的 micro 总体掩盖中心差异 |
| **解释** | Meta 回归：扫描仪、图像质量、病例构成、结节大小等与 Dice/AUROC 的关联 | 说明「差」是否与可观测协变量相关，而非空泛讨论 |
| **个案** | 剖析 THYB_S_ZJ24 与全腺体整体偏低 | Results 段落 + 可选补充图（失败模式、尺寸/质量分布） |

**不做的事（边界）**：B7 **不重训模型**、不改路由器；与 **B5**（元数据消融 / 专家选择热图）互补——B5 问「路由是否学中心偏好」，B7 问「各中心表现与临床/采集协变量」。

### 1.2 B8 在回答什么

同一审稿意见（R1.3）要求：**概率是否校准**、**何时拒答或强制人工复核**。R1.6 / F4 要求把规则 **量化**（覆盖率、剩余子集性能、漏诊/假阳性/工作量——临床侧由 Fei Chen 填数，工程侧提供 **阈值与标记结果**）。

| 层次 | 要求 | 本任务含义 |
|------|------|------------|
| **校准** | 可靠性图、ECE、Brier；分队列，NHC 可选分中心 | 分类为主；分割可用像素级 ECE（`segmentation/metrics.compute_ece`）作补充 |
| **拒答** | 专家分歧、分类熵、路由不确定标志等；**阈值仅在验证集确定** | 后处理策略，**不改权重**；测试集只报告曲线与固定工作点 |
| **交付 F4** | 各中心/队列 **送复核比例** + `abstention_thresholds.json` | F4 做临床叙述与错误分类统计时引用同一套规则 |

**不做的事（边界）**：不在测试集上调阈；不把拒答写成「已确立临床获益」；温度缩放若做，须写清 **仅验证集拟合**、测试集只报告 before/after（可选，非必须）。

### 1.3 B7 与 B8 的关系

```
NHC（及必要时其他测试队列）pipeline 跑完 → results.json + evaluate 指标
        │
        ├─ B7：按 center_id 聚合 + 元数据 join → 异质性表 / I² / meta 回归 / 个案
        │
        └─ B8：全队列校准 + 验证集定阈 → 测试集 risk–coverage + 各中心拒答率 → F4
```

两条线 **可并行**；**共同前提**是冻结的测试预测与 **G3** 提供的中心表。B8 的 **验证集**必须与 Methods 一致（见 §4.2），与 B7 用的测试集 **严格分离**。

---

## 2. 依赖与阻塞项

| 依赖 | 负责人 | 用途 |
|------|--------|------|
| **G3** NHC 中心清单与元数据（扫描仪、医院、去标识化字段） | Griffin / Prof. Kong | B7 描述表与 meta 回归协变量 |
| **G3** 或数据侧：`image_name` → `center_id` 映射 | 数据 | B7/B8 按中心汇总；可写在 `labels.json` 扩展字段或独立 `nhc_center_index.csv` |
| NHC **投稿配置** 的 `pipeline_run`（或 B3 策略 7 / S4 快照） | Baidong | 逐例 `results.json`、mask、分类概率 |
| **验证集** 图像列表（OpenThyroidDB 850 张或 Methods 写明之集合） | Baidong | B8 **仅在此集上**搜阈 / 拟合温度 |
| **B2** cluster bootstrap（若中心级 AUROC 要 CI） | Baidong | B7 表与稿面 CI 一致；可与 B7 脚本共用患者/检查聚类键 |
| **F4** 临床安全叙事 | Fei Chen | 消费 B8 的 `abstention_eval.json` 与阈值文件 |

**阻塞**：无 `center_id` 时，B7 只能做队列级、无法填 R2.6 中心表；B8 仍可先做 **全 NHC pooled** 校准与拒答，中心分层延后。

---

## 3. B7 实施计划

### 3.1 交付物清单（稿面）

| 交付物 | 形态 |
|--------|------|
| 补充表 S[X] | 35 中心：患者/结节/图像数、扫描仪、恶性标签可用性、结节/分类样本量 |
| 补充表 S7–S12 **修订** | 中心级 Dice/HD95/AUROC/AUPRC；单类或 n&lt;10 标 **not estimable**，不报 0.5/0.0（见返修 A7） |
| 补充表 S[X] | 随机效应汇总：I²、τ²（结节 Dice、分类 AUROC 等） |
| 补充表 / 图 | Meta 回归系数（扫描仪、质量、恶性比例、结节大小等） |
| Results 新段落 | THYB_S_ZJ24 + 全腺体 59.28% 讨论 |
| 回复 R1.3 / R2.6 | 引用上表数字 |

### 3.2 数据与字段约定

建议在仓库内固定一份 **中心索引**（不提交患者可识别信息）：

```text
docs/supplementary/nhc_center_schema.md   # 字段说明
data/manifests/nhc_center_index.csv       # 或仅路径写在 config（gitignore 大表）
```

| 字段 | 来源 | 说明 |
|------|------|------|
| `center_id` | G3 | 如 `THYB_S_ZJ24` |
| `image_name` / `stem` | `labels.json` 或文件名规则 | 与 `results.json` 对齐 |
| `patient_id` | 若有 | 中心内患者数、B2 聚类 |
| `scanner_vendor` / `model` | G3 或 DICOM 汇总 | meta 回归 |
| `nodule_size_mm` | GT mask 或标注 | 分布、回归协变量 |
| `malignancy` | `label_file` | 中心恶性比例 |

**Pipeline 可选小改（非必须）**：Phase 5 在 `results.json` 每例写入 `center_id`（从 manifest 查表），避免事后 join 失败。若 manifest 稳定，**离线 join 即可**，不必改 `cascade.py`。

### 3.3 代码与脚本（新建，不改推理逻辑）

| 模块 / 脚本 | 职责 |
|-------------|------|
| `scripts/build_nhc_center_table.py` | 读 manifest + G3 CSV → 补充表「描述」部分 |
| `pipeline/nhc_heterogeneity.py` | 读 `results.json` + GT → **逐图 Dice**；按中心聚合 mean/median；宏平均 |
| `pipeline/meta_regression.py` | 图像级或中心级因变量；混合效应 / 标准 meta-reg（实现选用 `statsmodels` 或 `rpy2`，文档写明） |
| `scripts/run_b7_analysis.py` | CLI：指定 `output-dir`、`manifest`、`task=seg|cls|both` → `output/b7/center_metrics.json`、LaTeX/CSV |
| `scripts/plot_b7_figures.py` | 中心森林图、协变量散点、ZJ24 子集直方图（可选） |

**质量协变量（与回复草稿一致）**：分辨率、对比度、ROI 占图比例——可在 `shared/image_io` 或脚本内对灰度图批量计算，写入 `per_image_covariates.parquet` 供回归。

### 3.4 全腺体分割（Table S7–S8）

- 若 **ThyroidCascadeAgent 当前仅评估结节 mask**（`gt_mask_dir` 为结节 GT），则 **全腺体 Dice 59.28%** 来自：
  - 已有稿面/补充表生成脚本（可能在 MedXAgent 主仓或其它评测目录），或  
  - 单独的全腺体 GT 目录 + 一次性评测脚本。  
- B7 文档与回复中 **明确两条任务线**：结节（本仓库 pipeline）与全腺体（标注任务不同）。个案讨论可引用 S7–S8 **已有逐中心数**，本仓库负责 **结节侧** 的 meta 回归与 ZJ24 结节剖析；全腺体侧重 **描述 + 与 MedSAM2 等基线对比**（若需重算，单独排期，不塞进 B8）。

### 3.5 B7 实施顺序

```
① 收 G3 元数据 + 定 center_id 映射规则
        ↓
② build_nhc_center_table.py → 描述表草稿
        ↓
③ 确认 NHC pipeline 结果路径（与 B3/S4 一致配置）
        ↓
④ nhc_heterogeneity.py：逐中心结节 Dice / 分类 AUROC（+ B2 聚类 CI 若就绪）
        ↓
⑤ 随机效应 I²、τ² + meta 回归
        ↓
⑥ ZJ24 与低性能中心：尺寸/质量/扫描仪分布 + 可视化
        ↓
⑦ 填稿 + 回复占位符
```

### 3.6 B7 验收标准

- [ ] 35 中心描述表与 G3 一致，且与 8,721 图像计数可对账  
- [ ] 中心级性能为 **宏平均** 或逐中心一行，与「28,458」类 micro 混算方式在 Methods 中区分  
- [ ] 无法估计 AUROC 的中心已标 NE，不进入宏平均  
- [ ] Meta 回归与个案结论在回复 R1.3 中有对应数字占位  
- [ ] 复现：`run_b7_analysis.py` + manifest 路径可在 README 或本文件 §6 一键命令复现表结构（数值依赖本地数据）

---

## 4. B8 实施计划

> B8 代码概要曾见于 `docs/REVISION_B5_B6_B8_B11_PLAN.md`；此处合并为与 B7 联动的完整规格。

### 4.1 交付物清单

| 交付物 | 形态 |
|--------|------|
| 图 | 可靠性图（分队列；NHC 可选 2–3 个代表性中心含 ZJ24） |
| 图 | Risk–coverage（分类 AUROC/准确率 vs 覆盖率；分割 Dice vs 覆盖率可选） |
| 补充表 | 各队列/中心 ECE、Brier；默认工作点：拒答率、保留子集 Dice/AUROC |
| 仓库 | `abstention_thresholds.json`（验证集导出） |
| 仓库 | `calibration.json`、`abstention_eval.json`（测试集评估） |
| Methods | 一句：阈值仅验证集、测试未调参、未重训 |
| **F4** | 同上 JSON + 逐例 `flagged_for_review: bool` 列表 |

### 4.2 验证集与数据划分（必须写死）

| 用途 | 数据集 | 禁止 |
|------|--------|------|
| 搜拒答阈值、可选温度缩放 | Methods 4.1 的 **validation**（如 stacked 850 张）或单独 `val_list` 文件 | 不可用 NHC 测试集调阈 |
| 报告校准 / risk–coverage | 各 **测试** 队列（含 NHC） | 不在测试集上选「最优」阈 |

配置建议：

```yaml
pipeline:
  abstention:
    val_results: output/validation/pipeline_run/results.json   # 或 val_list + 单独跑 evaluate
    rules:
      - name: cls_vote_entropy
        op: gt
        field: vote_entropy
      - name: cls_margin_low
        op: lt
        field: margin_top2
      - name: seg_pairwise_iou_min
        op: lt
        field: seg_min_pairwise_iou
      - name: router_uncertain
        op: eq
        field: routing_uncertain_flag
        value: true
    combination: any   # any | k_of_n
    target: maximize_auroc_on_retained   # 或固定覆盖率工作点 0.9
```

### 4.3 代码修改（本仓库 **必须**）

| 项 | 文件 | 内容 |
|----|------|------|
| 分类拒答特征 | `pipeline/cascade.py` 或 `classification/agent.py` 旁路函数 | 从 `indie_preds` 计算并写入 `results.json`：`vote_entropy`, `margin_top2`, `num_models_same_class`, `min_indie_margin` |
| 分割分歧特征 | `pipeline/cascade.py` | 从 `intermediate/seg/*.npz` 或已有 quality 字段写：`seg_mean_pairwise_iou`, `seg_min_pairwise_iou`（与返修「专家 IoU &lt; t1」一致） |
| 路由不确定 | `segmentation/agent.py` / `classification/agent.py` | 解析 LLM JSON 中 `uncertain` / 低置信标志 → `routing_uncertain_flag`（无 LLM 时为 false） |
| 校准 | **新建** `pipeline/calibration.py` | 分类：ECE、Brier、reliability bins；`y_score` 用 `final_confidence` 与恶性方向一致化 |
| 拒答 | **新建** `pipeline/abstention.py` | 验证集 grid/分位搜阈 → `abstention_thresholds.json`；测试集应用 → risk–coverage |
| 分割 ECE | `pipeline/calibration.py` | 可选：对选中 mask 的概率图 + GT（需 Phase 1 存 prob map 或仅用分类 ECE 作主文） |
| CLI | **新建** `scripts/run_calibration_abstention.py` | 读 config + `results.json` → `figures/` + JSON |
| 测试 | `tests/test_abstention.py`, `tests/test_calibration.py` | 合成 20 例验证搜阈逻辑 |

**复用**：`segmentation/metrics.compute_ece`；`classification/agent.format_predictions_json` 内已有 `vote_entropy` 计算逻辑，应 **提取为共享函数** 供 Phase 5 写入 `results.json`（避免仅存在于 prompt JSON）。

### 4.4 拒答规则（与回复 R1.3 草稿对齐）

| 信号 | 字段 | 说明 |
|------|------|------|
| 专家分类分歧 | `vote_entropy` ↑ 或 `num_models_same_class` &lt; M/2 | 与 Path A/B 无关，一律从独立模型算 |
| 置信度边缘 | `margin_top2` &lt; t | 取独立模型概率 top1−top2 的最小值或均值 |
| 分割分歧 | `seg_min_pairwise_iou` &lt; t1 | 多专家 mask 两两 IoU 最小值 |
| 路由不确定 | `routing_uncertain_flag` | LLM 输出或解析失败降级策略需在 Methods 说明 |

组合：`any`（默认，与回复「专家分歧 **或** 熵 **或** 路由标志」一致）或 `k_of_n` 做敏感性（可放补充）。

### 4.5 B8 实施顺序

```
① 提取 vote_entropy / margin 等 → results.json（改 cascade + 小 refactor）
        ↓
② pipeline/calibration.py + 单元测试
        ↓
③ 验证集跑 pipeline → run_calibration_abstention.py --fit-thresholds
        ↓
④ 各测试队列（含 NHC）--apply-thresholds → 图 + 表
        ↓
⑤ 按 center_id join → 各中心拒答率（依赖 B7 manifest）
        ↓
⑥ 交付 F4 + Methods/Results 段落
```

### 4.6 B8 验收标准

- [ ] 阈值 JSON 仅含 `fitted_on: validation` 及样本量记录  
- [ ] 测试集重复运行阈值不变、指标可复现  
- [ ] 至少 1 个队列 reliability 图 + 1 条 risk–coverage 曲线入稿  
- [ ] NHC 各中心拒答率表（或与 B7 合并一表）  
- [ ] F4 可读取 `abstention_eval.json` 中的逐例标记

---

## 5. 推荐总排期（仅工程 + 分析，不含 GPU 全量重跑）

| 周 | B7 | B8 |
|----|----|----|
| W0 | 收 G3；定 manifest；确认 NHC `results` 路径 | 同左 |
| W1 | 描述表脚本；逐中心 Dice/AUROC 聚合 | `results.json` 字段 + `calibration.py` 骨架 |
| W2 | I² / meta 回归；ZJ24 个案 | `abstention.py` + 验证集定阈 |
| W3 | 制图、与稿面 S 表对账 | 测试集曲线 + 中心拒答率；交给 F4 |

**并行**：W1 起 B7 聚合与 B8 字段开发可同时进行；**汇合点**为 `center_id` manifest 与 NHC 测试 `results.json` 就绪。

---

## 6. 复现命令（占位，实现后替换为真实路径）

```bash
# B7：中心级指标（示例）
python scripts/run_b7_analysis.py \
  --results output/NHC-MISD-TUS/pipeline_run/results.json \
  --manifest data/manifests/nhc_center_index.csv \
  --gt-mask-dir /path/to/NHC-MISD-TUS/masks \
  --label-file /path/to/NHC-MISD-TUS/labels.json \
  --out output/b7/nhc

# B8：验证集定阈 + 测试集评估（示例）
python scripts/run_calibration_abstention.py \
  --config config/b3/nhc_misd_tus.yaml \
  --val-results output/validation/pipeline_run/results.json \
  --test-results output/NHC-MISD-TUS/pipeline_run/results.json \
  --out output/b8/nhc
```

---

## 7. 与返修回复的映射

| 回复要点 | B7 | B8 |
|----------|----|----|
| 中心差异大、ZJ24、全腺体 59.28% | 主责 | 可选：低性能中心子集校准 |
| Meta 回归（扫描仪、质量、构成、大小） | 主责 | — |
| I²、τ² | 主责 | — |
| 可靠性图、ECE、Brier | — | 主责 |
| 拒答/强制复核、risk–coverage | — | 主责 |
| 各中心送复核比例 | 可合并出表 | 主责（需 center_id） |
| F4 临床安全量化 | — | 输出 JSON |

---

## 8. 工作量粗估

| 任务 | 代码 | 实验/制表 |
|------|------|-----------|
| B7 | 中（新分析包，基本不改 cascade） | 中（依赖 G3 + 对账 S 表） |
| B8 | 中（cascade 补字段 + 两模块 + CLI） | 小～中（验证集 + 多队列测试） |

合计约 **5～10 个工作日**（熟悉仓库）；全腺体重评、B2 全表 CI 另计。

---

*文档版本：2026-10-15；与 `ThyroidXAgent_返修计划与回复_中文.md` B7/B8 及 R1.3 回复草稿对齐。*
