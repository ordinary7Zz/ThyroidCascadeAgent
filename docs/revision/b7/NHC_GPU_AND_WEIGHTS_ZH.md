# NHC 实验：GPU 环境与权重说明

## GPU / Conda

与仓库根目录 `待做.md` 一致，在跑 **GPU 推理**前执行：

```bash
export CUDA_VISIBLE_DEVICES=1   # 按需改卡号
source ~/miniconda3/bin/activate
conda activate /mnt/wangbd8/workspace/envs/thyroid_infer
```

返修 **Cascade 主 pipeline**（`run_pipeline.py`）与 **九模型 infer**（`my_Thyroid_Infer`）均建议使用该环境。

---

## NHC 模型合规（禁 LLM API）

NHC 机器**不跑**闭源大模型（GPT、Gemini 等），**不接入** Qwen 等开源 LLM 的 API（数据安全）。  
允许：

- **九模型**：仅以 `my_Thyroid_Infer/config.yaml` 为准 → `config/revision/infer/nhc_prepared_sample.yaml`
- **级联 / B3 / B4 L1**：`enable_agent: false`，本地 DINO + 本地 AutoGluon 裁判

详见 `docs/revision/nhc_sample/MODEL_POLICY_ZH.md`。

## 两套权重体系（勿混用路径）

| 用途 | 配置文件 | 权重位置 |
|------|----------|----------|
| **稿面级联 Agent**（B7 正式 `results.json`） | `config/revision/nhc_no_llm_primary.yaml` | `ThyroidAgent/Segmentation_Agent/weights/…`、`Classification_Agent/weights/…`（相对 ThyroidCascadeAgent 的 `../`） |
| **九模型独立推理**（消融/对账、与 S7–S12 九模型列） | `my_Thyroid_Infer/config.yaml` 的 `weights:` / `pretrained:` | 相对 `my_Thyroid_Infer/` 根目录，如 `./infer_dinov3_unet/checkpoints/Nodule/…` |

`my_Thyroid_Infer/config.yaml` 还定义：

- `prepare.input_dir` / `prepare.output_dir` / `prepare.roi_checkpoint` — 原始 NHC → `processed/`
- `device: cuda`、`use_dino_mask_for_cls: nodule/dinov3_unet` 等推理行为

B7 **中心异质性**脚本消费的是 **Cascade** 输出的 `results.json` + `labels.json`（含 `center_id`）。九模型结果需单独汇总，不能自动替代 Cascade 的 B7 表。

---

## 推荐工作流（示例 → 全量）

### 1. 预处理（ThyroidCascadeAgent，可无 GPU）

```bash
cd ThyroidCascadeAgent
PYTHONPATH=. python scripts/revision/b7/run_nhc_prepare.py \
  --input_dir /path/to/甲状腺私有数据/新建文件夹 \
  --output_dir output/b7/nhc_prepared_smoke \
  --skip_roi
```

全量 NHC 可换 `--output_dir`；需 ROI 时设 `THYROID_INFER_ROOT=../my_Thyroid_Infer` 并提供 `--checkpoint`（权重见 infer `config.yaml` 的 `prepare.roi_checkpoint`）。

### 2a. Cascade 真推理（B7 主路径）

```bash
conda activate /mnt/wangbd8/workspace/envs/thyroid_infer
cd ThyroidCascadeAgent

# 示例 2 张图
python run_pipeline.py --config config/revision/nhc_prepared_sample.yaml

# 全量（数据盘就绪后）
python run_pipeline.py --config config/revision/nhc_no_llm_primary.yaml
```

### 2b. 九模型 infer（可选，非 B7 默认可用输入）

```bash
conda activate /mnt/wangbd8/workspace/envs/thyroid_infer
cd ../my_Thyroid_Infer

# 仅用已预处理数据推理（权重见 config.yaml）
python pipeline.py --skip_prepare --skip_roi \
  --processed_dir /path/to/ThyroidCascadeAgent/output/b7/nhc_prepared_smoke
```

`pipeline.py` 会把 `processed/` 写入 `datasets/processed/config.yaml` 并调用 `run_all.py`。

### 3. B7 分析

```bash
cd ThyroidCascadeAgent
python scripts/revision/b8/backfill_results_metadata.py \
  --output-dir output/b7/nhc_cascade_sample \
  --label-file output/b7/nhc_prepared_smoke/labels.json

python scripts/revision/b7/run_b7_analysis.py --re-evaluate \
  --output-dir output/b7/nhc_cascade_sample \
  --label-file output/b7/nhc_prepared_smoke/labels.json \
  --gt-gland-mask-dir output/b7/nhc_prepared_smoke/gland_masks \
  --gland-pred-mask-dir <cascade 输出的腺体预测目录，若有>
```

无 GPU 时可用 `scripts/revision/b7/smoke_b7_prepared_sample.py` 做 B7 链冒烟。

---

## 路径检查

```bash
# Cascade 分割权重（示例）
ls ../Segmentation_Agent/weights/all_datasets/dino_unet_train_all_datasets_epoch_40.pth

# Infer 结节 DINO（示例）
ls ../my_Thyroid_Infer/infer_dinov3_unet/checkpoints/Nodule/dino_unet_train_dataset_4_epoch_50.pth
```
