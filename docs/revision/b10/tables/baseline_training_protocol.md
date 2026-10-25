# Supplementary Table S[X] — Baseline training and inference protocol

Supervised rows match **Table S3/S4** exports (`b2_exports`, 2026-10-21). External test cohorts are not used for development fine-tuning.

**Table notes**

1. **dataset_3 (classification development):** stacked training split from TN3K + ThyroidXL + TN5K (`train_val_test/Superimposed_multitask/dataset_3_cls/train`; image count matches multitask `dataset_3` JSON).
2. **dataset_4 (segmentation development):** stacked training split from TN3K + ThyroidXL + PKTN + TN5K (`train_val_test/Superimposed_experiment/dataset_4/train`).
3. **Supervised protocol (default):** full fine-tuning on the indicated stacked development set from publicly available upstream weights; best validation checkpoint used for all external tests in Tables S3/S4 (checkpoint paths are recorded in the analysis manifest, not shown here).
4. **Segmentation baselines at test:** image plus GT box/mask prompt (`gt_mask` protocol), consistent with Table S3.
5. **Classification baselines at test:** image-level input only.
6. **ThyroidXAgent:** same stacked development data as supervised baselines for full-stack Table S3/S4 results; progressive stacking ablations (Table S6) reported separately.
7. **Vision–language models:** no thyroid end-to-end training on dataset_3; vendor or public weights; API or frozen inference with fixed prompts.

| Model | Task | Development set | Upstream pretraining | Test-time inference |
| --- | --- | --- | --- | --- |
| BiomedCLIP | Classification | dataset_3 | OpenCLIP BiomedCLIP; head fine-tuned on dataset_3_cls | US image only |
| LSNet | Classification | dataset_3 | ImageNet-pretrained LSNet | US image only |
| MedSAM2 | Segmentation | dataset_4 | SAM 2.1 Hiera | US image + GT box/mask (`gt_mask`) |
| MedSegX | Segmentation | dataset_4 | SAM ViT-B + MedSegX thyroid adapter | US image + GT box/mask (`gt_mask`) |
| MedSigLIP | Classification | dataset_3 | Google MedSigLIP; partial fine-tune on dataset_3_cls | US image only |
| RepViT | Classification | dataset_3 | ImageNet-pretrained RepViT | US image only |
| ResNet-50 | Classification | dataset_3 | ImageNet ResNet-50; fine-tuned on dataset_3 | US image only |
| TransUNet | Segmentation | dataset_4 | ImageNet-21k ViT-B/16 (TransUNet default) | US image + GT box/mask (`gt_mask`) |
| UltraFedFM | Classification | dataset_3 | ViT backbone + dataset_3_cls fine-tune | US image only |
| UltraFedFM | Segmentation | dataset_4 | MAE / federated FM + dataset_4 fine-tune | US image + GT box/mask (`gt_mask`) |
| ThyroidXAgent (segmentation router) | Segmentation | dataset_4 | DINOv3-UNet (ImageNet-scale backbone) | US image → LLM-routed expert mask |
| ThyroidXAgent (classification router) | Classification | dataset_3 | DINOv3 multitask backbone (fine-tuned on dataset_3) | Routed mask + image (pipeline) |
| GPT-5 / Gemini / MedGemma / Qwen3-VL (if in S4) | Classification | — (not finetuned) | Vendor / public VLM weights | Image ± fixed text prompt (zero-shot or API) |
