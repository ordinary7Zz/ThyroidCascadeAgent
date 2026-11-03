# 恶性子任务重跑编排（ZJH hold-out + Dai）

与回信 `tab_malig_oof` / `tab_malig_ext` / `tab_ftcptc_ext_dai` 对齐。

## 数据前提

1. TN3K dHash H=0 剔除后，对患者 hold-out（seed 42）：
   ```bash
   python scripts/revision/b9/split_zjh_malignant_train_test.py
   ```
2. 开发/OOF 仅用 **`zjh_train.json`**（3227 图，517 例）；外测 **`zjh_test.json`**（801 图，130 例）。
3. LNM 与 FTC 共用同一批 patient_id（见 `docs/revision/b9/zjh_malignant_patient_split.json`）。

`Malignant_Cls_Model/b9/task_specs.py` 默认 manifest 已改为 `manifests/zjh_train.json`。

## 环境

```bash
cd ThyroidCascadeAgent
export CUDA_VISIBLE_DEVICES=0
export RUN_TAG=zjh20261101
# 可选: source scripts/revision/b9/env_malig_b9.sh
```

## 按模型一键脚本（`scripts/revision/b9/models/`）

每个 `run_<model>.sh` **按同一顺序**执行：

| 步骤        | 内容                                                                                                | 例外                                           |
| ----------- | --------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| **1** | 全量 `zjh_train` 训练 → **ZJH hold-out** 评测（LNM + FTC 两任务，若模型只做 LNM 则仅 LNM） | —                                             |
| **2** | **FTC/PTC** 在 **FangDai** 外测（复用步骤 1 的 FTC 权重，`--skip_train`）             | LLNM 无 FTC；ThyroidXAgent / GPT / Gemini 见下 |
| **3** | **五折 OOF**（LNM + FTC，共用 `01_export_shared_folds.sh`）                                 | **MedGemma、Qwen3 跳过**                 |

| 脚本                                                         | 说明                                                  |
| ------------------------------------------------------------ | ----------------------------------------------------- |
| `run_repvit.sh` / `run_lsnet.sh` / `run_ultrafedfm.sh` | 步骤 1–3                                             |
| `run_medgemma.sh` / `run_qwen3.sh`                       | 步骤 1–2                                             |
| `run_llnm_net.sh`                                          | 步骤 **1 + 3**（LNM 全量 + hold-out eval + 五折 OOF）；已有 my_run 全量（220/158）或 OOF（220 图）时自动跳过对应部分（`SKIP_IF_LLNM_*`）；`SKIP_OOF=1` 仅刷 step1 |
| `run_tiger_model.sh`                                       | 步骤 1–3（FTC；Tiger ResNet 流水线）                 |
| `run_thyroidxagent.sh`                                     | 步骤 **1 + 3**（DINO 全量外测 + 五折 OOF）；已有 `external_summary.json` / my_run OOF（220·532 图）时自动跳过对应步骤（`SKIP_IF_TX_*`）；`SKIP_TX_OOF=1` 仅刷外测；全栈 Cascade 仍待补 |
| `run_gpt5.sh` / `run_gemini.sh`                          | API 占位（无本地训练 / 无 OOF）                       |
| `run_all_models.sh`                                        | `MODELS="repvit lsnet"` 过滤批量跑                  |

输出根目录：`docs/revision/b9/runs/models_${RUN_TAG}/`（见 `_lib.sh` 中 `OUT_ROOT`）。

### 默认训练 epoch（每次 `fit`）

在 `env_malig_b9.sh` 中定义，各 `run_<model>.sh` 通过 `_lib.sh` 生效：

| 脚本                                                         | 默认 epoch/次 | 环境变量                                                                                                                                                                                                      |
| ------------------------------------------------------------ | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `run_repvit.sh` / `run_lsnet.sh` / `run_ultrafedfm.sh` | **10**  | `BASELINE_EPOCHS`；RepViT/LSNet：`Classification_Models/{RepViT,lsnet}/scripts/mytrain_{LNMCN01,FTCPTC}.sh`；UltraFedFM：`UltraFedFM/scripts/my_class_pretrain_{LNMCN01,FTCPTC}.sh`（LNM、FTC 均为 10） |
| `run_medgemma.sh` / `run_qwen3.sh`                       | **3**   | `VLM_EPOCHS`（与 `medgemma_thyroid_binary_train.py` / `qwen3_vl_thyroid_binary_train.py` 默认一致）                                                                                                     |
| `run_llnm_net.sh`                                          | **30**  | `EPOCHS` 或 `SPECIALIST_EPOCHS`（全量 + OOF 各折）                                                                                                                                                        |
| `run_tiger_model.sh`                                       | **30**  | `NUM_EPOCHS` 或 `SPECIALIST_EPOCHS`（全量 ResNet + OOF 各折）                                                                                                                                             |
| `run_thyroidxagent.sh`                                     | **30**  | `EPOCHS` / `SPECIALIST_EPOCHS`（全量外测 1 次/任务；OOF 另加 5 折×2 任务） |

### 各模型运行命令

在仓库根目录 `ThyroidCascadeAgent` 下执行（先设置 `CUDA_VISIBLE_DEVICES`、`RUN_TAG`）：

```bash
# CNN / ViT 基线（步骤 1–3）
bash scripts/revision/b9/models/run_repvit.sh
bash scripts/revision/b9/models/run_lsnet.sh
bash scripts/revision/b9/models/run_ultrafedfm.sh

# VLM 基线（步骤 1–2，不做五折 OOF）
bash scripts/revision/b9/models/run_medgemma.sh
bash scripts/revision/b9/models/run_qwen3.sh

# 专用模型
bash scripts/revision/b9/models/run_llnm_net.sh
# 全量已训完、只补 eval + OOF（会自动跳过 30-epoch 重训）：
# bash scripts/revision/b9/models/run_llnm_net.sh
# 清掉旧 OOF（3227 图 cv_config）后重跑五折：
# rm -rf docs/revision/b9/runs/models_${RUN_TAG}/llnm_net/lnm/oof
# SKIP_IF_LLNM_OOF=0 bash scripts/revision/b9/models/run_llnm_net.sh
bash scripts/revision/b9/models/run_tiger_model.sh
# ThyroidXAgent：DINO 全量外测 + 五折 OOF（已有结果则跳过，避免重复全量训练）
bash scripts/revision/b9/models/run_thyroidxagent.sh
# 仅补 OOF（外测已存在）：
# SKIP_IF_TX_FULL=1 bash scripts/revision/b9/models/run_thyroidxagent.sh
# 仅刷外测、不做 OOF：
# SKIP_TX_OOF=1 bash scripts/revision/b9/models/run_thyroidxagent.sh
# 强制重跑全量外测：
# SKIP_IF_TX_FULL=0 bash scripts/revision/b9/models/run_thyroidxagent.sh

# 闭源 API 占位（无本地训练 / 无 OOF）
bash scripts/revision/b9/models/run_gpt5.sh
bash scripts/revision/b9/models/run_gemini.sh

# 批量（默认全部模型；可过滤）
bash scripts/revision/b9/models/run_all_models.sh
MODELS="repvit lsnet" bash scripts/revision/b9/models/run_all_models.sh
```

## 底层分步脚本（`scripts/revision/b9/`）

| 脚本                              | 作用                                                           |
| --------------------------------- | -------------------------------------------------------------- |
| `env_malig_b9.sh`               | 路径与 manifest 环境变量                                       |
| `01_export_shared_folds.sh`     | 导出 RepViT 系共用五折（OOF 前自动调用）                       |
| `02_run_baselines_oof.sh`       | 旧版：仅 RepViT / LSNet / UltraFedFM 五折 OOF                  |
| `03_run_dino_multitask_oof.sh`  | ThyroidXAgent DINO 五折 OOF                                    |
| `08_run_dino_full_external.sh`  | DINO 全量 `zjh_train` → `zjh_test`（FTC 含 Dai）；`dino_unet_multitask/.../run_full_external.py` |
| `04_run_llnm_zjh_b9.sh`         | LLNM 五折 + 全量 + zjh_test（与 `run_llnm_net.sh` 等价编排） |
| `05_run_tiger_ftc_b9.sh`        | Tiger FTC 五折 OOF                                             |
| `06_run_tiger_ftc_external.sh`  | Tiger 全量外测；`EXTERNAL_STEP=zjh\|dai\|both`                 |
| `run_baseline_full_external.py` | CNN/ViT/VLM 全量 + ZJH + 可选 Dai                              |
| `run_all_malig_rerun.sh`        | 旧版串联（默认 01+02）                                         |

## 仍缺 / 待补

- **ThyroidXAgent 全栈**（DINO + AutoGluon + 路由）外测：见 `B9_ThyroidXAgent_补充实验计划.md`；回信 **`tab_malig_ext`  interim** 用 `08_run_dino_full_external.sh` 的 DINO 专家结果（表注需说明非全栈融合）。
- **GPT / Gemini**：API 评测脚本。
- 跑完后将 metrics 写入 LaTeX 表并去掉 `\rpending`。
