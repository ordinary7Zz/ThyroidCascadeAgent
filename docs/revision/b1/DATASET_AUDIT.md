# B1 数据集审计表（草稿）

> **目的**：支撑 R1.1 / R2.2 / R3.3（患者或检查 ID、划分互斥、跨库近重复）。  
> **状态**：本地数据已核对项填实；待 F6 / 官方说明项标 **TBD**。  
> **勿改**：`docs/ThyroidXAgent_返修计划与回复_中文.md`；回复素材可摘本表。

**数据根目录**：`/mnt/wangbd8/workspace/DataSets/ThyroidAgent/`  
**工程内划分与标签**：`train_val_test/`（见 `docs/revision/b10/B10_基线训练协议总结.md`）

---

## 1. 总表（按稿内主要队列）

| 队列 | 角色（稿内） | 本地路径 | 测试图像数 | 公开 patient/case ID | 划分来源 | 患者级互斥（发布划分） | 近重复 / 同院备注 |
|------|--------------|----------|------------|----------------------|----------|------------------------|-------------------|
| TN3K | 内部 train/val/test | `train_val_test/TN3K/` | 614 | **无**（`filename` + 标签） | 原发布 train/val/test | **TBD**（公开包未附 patient ID） | 与 ZJH-8K 同院（珠江医院）；**F6** 院内 ID 查重叠 |
| TN5K | 内部 | `train_val_test/TN5K/` | 1000 | **无** | 原发布 + `ImageSets` | **TBD** | 原始 `Annotations/*.xml` 为 VOC 框，无 patient 字段 |
| ThyroidXL | 内部 | `train_val_test/ThyroidXL/` | 2090 | **有**（患者键 = 文件名首段 `00000058` 等；见官方 `ThyroidXL/train/train_annotations.json`） | 原发布 | **TBD**（官方称 739 test patients） | 测试文件名本地加前缀 `ThyroidXL_test_`（解析时需剥除） |
| PKTN | 内部（分割） | `train_val_test/PKTN/` | 150 | **无** | 项目划分 | **TBD** | — |
| DDTI | 外部 test（分割） | `train_val_test/DDTI/test/` | 见 masks | **无** | 外部仅 test | — | — |
| DDTI_Classification（**cls，主评估**） | 外部 test（分类） | `train_val_test/DDTI_Classification/all/images_processed` + `all/DDTI_Classification_test_label.json` | **349** | **无** | 标签 JSON 与 pipeline/B2 一致 | 一图一簇 | `test/images` 为更小子目录（~53 图），**主表不用** |
| RJH-7K | 外部 test（分割） | `train_val_test/RJH-7K/` 等 | **TBD** | **无** | 外部 | — | — |
| ZJH-8K | 外部 test | `train_val_test/ZJH-8K/` | 7958 | **有**（`ZJH-8K_labels.json.patient_map.json` → `P0001`…；文件名 `姓名_01_…` 或匿名 `P0091_01_…`） | 机构队列，全量作 test | 稿内 1,149 **患者** vs 本地 map **1146** 患者：**F6 对齐** | 与 TN3K 同院；重叠筛查见 §3 |
| NHC-MISD-TUS | 外部 test | **本地缺失** | — | **TBD** | — | — | 配置见 `config/b3/nhc_misd_tus.yaml` |
| SMU-HMC 等报告队列 | 报告侧 | 非 `train_val_test` 主表 | — | 稿内称 400 例 **患者级** test | 稿内 Methods | 已声明患者留出 | 与 B12/S9 数据流图联动 |

**Bootstrap 聚类键（B2 口径草案）**

| 队列 | Cluster bootstrap 键 | 患者级分类主表 |
|------|----------------------|----------------|
| ZJH-8K | `patient_id`（见 `scripts/revision/b2/build_cluster_maps.py`） | **必报** |
| ThyroidXL | `patient_id`（文件名解析，test **739** 簇 / **2090** 图） | **必报** |
| 其余 OpenThyroid 图像 test | **无 patient ID**：每张图视为独立 cluster（或仅图级 bootstrap + B1 披露） | 仅图像级 |
| B9 LNM 等子任务 | 已有患者簇（见 `docs/revision/b9/`） | 与 B2 统一 seed/次数 |

---

## 2. 有 ID 队列：证据与计数（本机 2026-10-21）

### ZJH-8K

| 项 | 值 |
|----|-----|
| 标签 | `train_val_test/ZJH-8K/ZJH-8K_BM_labels.json`（pipeline：`config/config_ZJH-8K.yaml`） |
| 患者映射 | `train_val_test/ZJH-8K/ZJH-8K_labels.json.patient_map.json`（**1146** 条 姓名→`Pxxxx`） |
| 图像 | `train_val_test/ZJH-8K/images/`（**7958**） |
| 主结果缓存 | `output/ZJH-8K/pipeline_run/results.json`（**7958** 条，`image_name` 多为中文姓名前缀） |
| 稿面患者数 | **1149** → 与 1146 差异需在 Methods 说明（去标识、排除例等） |

### ThyroidXL

| 项 | 值 |
|----|-----|
| 官方说明 | `ThyroidXL/README.md`：test **739** patients，**2094** images（官方）；本地 test **2090** 图 |
| 患者级标注结构 | `ThyroidXL/train/train_annotations.json` → `info["00000058"].images[]` |
| 本地 test 标签 | `train_val_test/ThyroidXL/test/ThyroidXL_test_label.json`（list，**2090**） |
| 患者 ID 规则 | 去掉可选前缀 `ThyroidXL_test_` 后，取 stem 的**第一段**（如 `00000126`） |
| 主结果缓存 | `output/ThyroidXL/pipeline_run/results.json`（**2090**） |

---

## 3. 无 ID 队列：Methods 可写句式（英文草稿）

- *For cohorts without publicly released patient identifiers (TN3K, TN5K, DDTI, PKTN, RJH-7K, …), we used the publishers’ image-level splits and resampled **one cluster per image** for bootstrap confidence intervals, and we report **image-level** classification metrics unless otherwise noted.*
- *We screened near-duplicate images using 64-bit difference hashing (Hamming ≤ 5). Stacked training vs. ZJH-8K: **995** exact (H = 0) and **128** near-only pairs; TN3K official splits vs. ZJH-8K: **1156** exact pairs; TN3K test vs. ZJH: **2** exact pairs (*see* `tables/near_duplicates.json`). Filename stem overlap was **not** used as evidence of independence (incompatible naming across cohorts). Spot-checked pairs: [**TBD**]. Patient-level overlap: institutional IDs (**F6**, optional).*

---

## 4. 训练 vs 外测（**以 dHash 为准**）

| 检查项 | 状态 |
|--------|------|
| 堆叠 train vs 各外测 **dHash 近重复** | **已完成**（`tables/near_duplicates.json`）；稿面主结论见 **B1_结论与回复素材 §2.2** |
| TN3K splits vs ZJH-8K | **1156** H=0 对（同院图级交叉） |
| stem 重叠（`train_test_overlap.json`） | 均为 0；**不作 B1 主结论**（跨库命名无鉴别力） |
| ThyroidXL / TN3K / TN5K 仅用各自 **train** 进堆叠 | 与 B10 叙述一致；**内容重复**以 dHash 表为准（如 TN5K test **38** H=0 vs train） |
| ZJH 全量为 test | 与 `config_ZJH-8K` 一致 |

整合结论见 **`docs/revision/b1/B1_结论与回复素材.md`**。

---

## 5. 待办（B1 关单）

- [ ] **F6**：TN3K↔ZJH 院内患者重叠、ZJH 1149 vs 1146、采集时段/设备  
- [ ] 近重复：人工 spot check + 可选全量配对 Supp.  
- [x] dHash 流水线（`scripts/revision/b1/audit_near_duplicates.py`）  
- [ ] ~~stem 互斥作为稿面结论~~（仅保留 JSON 作管线记录）  
- [ ] NHC 数据同步后补一行  
- [ ] 将定稿表同步到 Methods 4.1 / 补充表 S[X]（稿面）

---

## 6. 相关路径速查

```
train_val_test/TN3K/test/          # 614
train_val_test/TN5K/test/        # 1000
train_val_test/ThyroidXL/test/   # 2090, ThyroidXL_test_label.json
train_val_test/ZJH-8K/           # 7958 images, ZJH-8K_BM_labels.json
TN5K/.../Annotations/            # 原始 VOC，无 patient
ThyroidXL/train/train_annotations.json
output/<COHORT>/pipeline_run/results.json
output/<COHORT>/pipeline_run/metrics.json   # 当前为图像级 bootstrap CI
```
