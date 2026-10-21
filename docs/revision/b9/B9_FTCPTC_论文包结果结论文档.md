# B9（FTC/PTC 分类）实验结论 — `FTCPTC_ZJH8K_FangDai_packed`

> **数值来源**：`export_results/ftcptc_paper_external/*`、`new_code/runs/b9_paper_cv/cv_summary.json`（2026-10-21 核验）。  
> CSV 过滤子集见：`B9_FTCPTC_filtered数据集结论.md`。

**数据包**：`Classifaction_Data/FTCPTC_ZJH8K_FangDai_packed`  
**运行 ID**：`b9_paper_cv`、`Thyroid_PTC_vs_FTC_paper_20261020_233453`、`ftcptc_paper_external`

---

## 1. 返修交付对照

| 返修项 | 状态 | 证据 |
|--------|------|------|
| **R2.11** 患者级 5 折 CV（4756 池） | **已完成** | `b9_paper_cv/cv_summary.json`、`oof_predictions.json` |
| **R2.12** FangDai 外测与 ZJH 训练分离 | **已完成** | `export_results/ftcptc_paper_external/` |

| 与稿内 | 稿内 | 本包 |
|--------|------|------|
| ZJH CV / 开发池 | 4,756 | 4,756（`zjh_dev_all.json`） |
| ZJH 固定 val | 183 | 183（单次训练用，非 B9 OOF 协议） |
| 外部 test | ~200 | **199** FangDai |

---

## 2. 数据划分

| 角色 | 图像数 | Manifest |
|------|--------|----------|
| ZJH 训练（单次） | 4,573 | `zjh_train.json` |
| ZJH 验证（单次） | 183 | `zjh_val.json` |
| ZJH 开发池（B9） | 4,756 | `zjh_dev_all.json` |
| FangDai 外测 | 199 | `fangdai_external_test.json` |

物化（单次训练）：`dataset_json_ftcptc_paper/`。

---

## 3. 模型与训练配置（ResNet18）

| 项目 | B9 五折 CV | 单次 + FangDai 外测 |
|------|------------|---------------------|
| 脚本 | `run_b9_paper_cv.sh` | `run_ftcptc_paper_pipeline.sh` |
| 优化 | `lr=1e-5`，`batch=8`，`epochs=50` | 同左 |
| 划分 / 选模 | `n_splits=5`，`seed=42`，患者分层 | val **V** 最大 → epoch **11** |
| OOF / 阈值 | 末轮 epoch 049 + OOF Youden ≈ **0.978** | val 183 Youden → **0.0447** |
| CI | bootstrap 1000，95%，`seed=42` | 同左 |
| 预训练 | `pretrained/resnet18-f37072fd.pth`（以训练日志为准） | 同左 |

---

## 4. 患者级 5 折交叉验证（R2.11）

**输入**：`zjh_dev_all.json` 全量 **4756** 张；约 **722** 患者（折内 val 患者约 144–145/折）。

**归档**：`new_code/runs/b9_paper_cv/cv_summary.json`、`oof_predictions.json`、`fold_{0..4}/`。

### 4.1 各折验证集（折末 checkpoint 推理）

| Fold | Val 图像 | Val 患者 | 患者级 AUROC | 图像级 AUROC |
|------|----------|----------|--------------|--------------|
| 0 | 962 | 145 | 0.435 | 0.481 |
| 1 | 884 | 145 | 0.569 | 0.607 |
| 2 | 1105 | 144 | 0.346 | 0.399 |
| 3 | 903 | 144 | 0.493 | 0.477 |
| 4 | 902 | 144 | 0.463 | 0.418 |

### 4.2 合并 OOF（4756 张）

| 级别 | AUROC | AUPRC | Acc | F1 | 95% CI（AUROC） |
|------|-------|-------|-----|-----|-----------------|
| **患者级** | **0.462** | 0.080 | 0.907 | 0.000 | **[0.404, 0.525]** |
| 图像级 | 0.470 | 0.083 | 0.906 | 0.000 | [0.445, 0.497] |

OOF 阈值（Youden）：≈ **0.978**。患者分数：同 `patient_id` 下概率 **算术平均**。

> **解读注意**：OOF 在 Youden 阈值下 **Recall/F1≈0**（多数预测为负类），与极高阈值一致；AUROC 仍反映排序能力。折间差异大（fold 1 相对最高）。各折使用 **epoch 049** 权重，非 valid 最优 checkpoint（见 §8）。

---

## 5. 单次训练 + FangDai 外部 test（R2.12）

**来源**：`export_results/ftcptc_paper_external/fangdai_external_test_metrics.txt`

| 项目 | 值 |
|------|-----|
| 权重 | `epoch_011_..._V0.581_T0.649.pth` |
| 阈值 | 0.0447（183 张 val） |

### 5.1 图像级（*n*=199）

| 指标 | 值 | 95% CI |
|------|-----|--------|
| **AUROC** | **0.650** | [0.577, 0.723] |
| AUPRC | 0.635 | [0.546, 0.735] |
| F1 | 0.471 | [0.376, 0.557] |

### 5.2 患者级外测

Manifest 病例 ID 过粗，导出中患者级 AUROC **不可解释**；**外测主报图像级**。

---

## 6. 结论陈述（回复草稿）

1. **ZJH 4756 图**上患者分层 **5 折 CV**：OOF **患者级 AUROC 0.46**（95% CI **0.40–0.53**）；图像级 **0.47**（0.45–0.50）。  
2. **FangDai 199 图**外测（ZJH train/val 训练、val 定阈）：**图像级 AUROC 0.65**（0.58–0.72）。  
3. 同一数据包上 **CV 与外测表现不一致**（外测优于 OOF 排序），需结合选模协议（OOF 末 epoch vs 外测 valid-best epoch）、类别不平衡与是否全程 ImageNet 预训练作讨论（§8）。  
4. 外测 *n*=**199**。

---

## 7. 复现命令

```bash
cd /mnt/wangbd8/workspace/ThyroidAgent/Tiger-Model
export PACK=/mnt/wangbd8/workspace/DataSets/ThyroidAgent/Classifaction_Data/FTCPTC_ZJH8K_FangDai_packed

CUDA_VISIBLE_DEVICES=0 PACK="$PACK" OUTPUT_DIR=./new_code/runs/b9_paper_cv \
  bash new_code/run_b9_paper_cv.sh

SKIP_DATA=1 CUDA_VISIBLE_DEVICES=0 PACK="$PACK" \
  bash new_code/run_ftcptc_paper_pipeline.sh
```

---

## 8. 产物路径与局限

| 类型 | 路径 |
|------|------|
| B9 CV | `new_code/runs/b9_paper_cv/cv_summary.json` |
| B9 OOF | `new_code/runs/b9_paper_cv/oof_predictions.json` |
| 外测 | `export_results/ftcptc_paper_external/` |

| # | 局限 |
|---|------|
| 1 | B9 OOF 使用各折 **最后一 epoch**，非 valid 最优权重。 |
| 2 | OOF Youden 阈值极高，分类指标（Prec/Recall/F1）在 OOF 上接近退化；主报 **AUROC + CI**。 |
| 3 | 若部分折训练曾随机初始化 ImageNet，需对照日志后决定是否重跑。 |

---

*文档版本：v2.0 · B9 + 外测均已有 `cv_summary` / metrics 文件支撑*
