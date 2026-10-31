#!/usr/bin/env python3
"""生成 config/for_llm/<cohort>.yaml：策略 7 LLM 路由 + test_for_llm_malignancy 数据路径。"""

from __future__ import annotations

import repo_path

repo_path.install()

from pathlib import Path

ROOT = repo_path.find_repo_root()
OUT_DIR = ROOT / "config" / "for_llm"
DATA = Path("/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test")

DEFAULT_LLM = "deepseek-v4-pro-0813"


def _sub(
    rel: str,
    *,
    images_dir: str = "images",
    masks_dir: str = "masks",
    label_name: str | None = None,
) -> dict:
    base = DATA / rel / "test_for_llm_malignancy"
    return {
        "image_input": base / images_dir,
        "gt_mask_dir": base / masks_dir if masks_dir else None,
        "label_file": base / label_name if label_name else None,
    }


COHORTS: list[dict] = [
    {
        "name": "tn3k",
        "run_segmentation": True,
        "run_classification": True,
        **_sub("TN3K", label_name="TN3K_test_label.json"),
    },
    {
        "name": "tn5k",
        "run_segmentation": True,
        "run_classification": True,
        **_sub("TN5K", label_name="TN5K_test_label.json"),
    },
    {
        "name": "thyroidxl",
        "run_segmentation": True,
        "run_classification": True,
        **_sub("ThyroidXL", label_name="ThyroidXL_test_label.json"),
    },
    {
        "name": "zjh8k",
        "run_segmentation": True,
        "run_classification": True,
        **_sub("ZJH-8K", label_name="ZJH-8K_BM_labels.json"),
    },
    {
        "name": "pktn",
        "run_segmentation": True,
        "run_classification": True,
        **_sub("PKTN", label_name="PKTN_test_label.json"),
    },
    {
        "name": "rjh7k",
        "run_segmentation": True,
        "run_classification": False,
        **_sub("RJH-7K", images_dir="image", masks_dir="mask", label_name=None),
    },
    {
        "name": "ddti_seg",
        "run_segmentation": True,
        "run_classification": False,
        **_sub("DDTI/all_seg", label_name=None),
    },
    {
        "name": "ddti_cls",
        "run_segmentation": False,
        "run_classification": True,
        **_sub(
            "DDTI_Classification/all",
            images_dir="images_processed",
            masks_dir="",
            label_name="DDTI_Classification_test_label.json",
        ),
    },
]


def _bool_yaml(v: bool) -> str:
    return "true" if v else "false"


def render(cohort: dict) -> str:
    name = cohort["name"]
    out_run = f"output/for_llm/{name}/pipeline_run"
    label = cohort.get("label_file")
    label_line = f"    label_file: {label}" if label else "    label_file: ''"
    mask = cohort.get("gt_mask_dir")
    if mask:
        mask_line = f"    gt_mask_dir: {mask}"
    else:
        mask_line = "    gt_mask_dir: ''"

    return f"""# 策略 7（LLM 全系统路由，metadata_mode=full）— 专家选择占比 / routing_log
# 数据：.../test_for_llm_malignancy（先 bash scripts/build_all_test_for_llm.sh 或 build_test_for_llm.py --out ...）
# 用法:
#   export DASHSCOPE_API_KEY=...
#   python run_pipeline.py --config config/for_llm/{name}.yaml --device cuda
#
shared:
  agent_llm:
    api_key_env: DASHSCOPE_API_KEY
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    model_name: {DEFAULT_LLM}
    temperature: 0.3
    max_tokens: 2048
    enable_thinking: false
segmentation:
  models:
  - type: dinov3_unet
    name: all_datasets
    model_path: ../Segmentation_Agent/weights/all_datasets/dino_unet_train_all_datasets_epoch_40.pth
    input_size:
    - 224
    - 224
    threshold: 0.5
  - type: dinov3_unet
    name: TN3K
    model_path: ../Segmentation_Agent/weights/TN3K/dino_unet_train_TN3K_epoch_50.pth
    input_size:
    - 224
    - 224
    threshold: 0.5
  - type: dinov3_unet
    name: ThyroidXL
    model_path: ../Segmentation_Agent/weights/ThyroidXL/dino_unet_train_ThyroidXL_epoch_50.pth
    input_size:
    - 224
    - 224
    threshold: 0.5
  - type: dinov3_unet
    name: PKTN_comprehensive
    model_path: ../Segmentation_Agent/weights/PKTN_comprehensive/dino_unet_train_PKTN_comprehensive_epoch_50.pth
    input_size:
    - 224
    - 224
    threshold: 0.5
  - type: dinov3_unet
    name: TN5K
    model_path: ../Segmentation_Agent/weights/TN5K/dino_unet_train_TN5K_epoch_50.pth
    input_size:
    - 224
    - 224
    threshold: 0.5
  agent:
    enable_agent: true
    routing_mode: llm
    brief_routing_prompt: true
    include_disagreement_metrics_in_prompt: true
    metadata_mode: full
    pre_filter:
      cosine_threshold: 0.8
      prob_outlier_threshold: 0.4
      min_keep: 1
    ensemble:
      enabled: true
      top_k: 1
      method: weighted_average
      threshold: 0.5
classification:
  models:
  - type: dinov3_unet_multitask
    name: all_datasets
    model_path: ../Classification_Agent/weights/all_datasets/dino_unet_train_all_datasets_epoch_40.pth
    use_tirads: false
  - type: dinov3_unet_multitask
    name: TN3K
    model_path: ../Classification_Agent/weights/TN3K/dino_unet_train_multitask_TN3K_epoch_50.pth
    use_tirads: false
  - type: dinov3_unet_multitask
    name: TN5K
    model_path: ../Classification_Agent/weights/TN5K/dino_unet_train_multitask_TN5K_epoch_50.pth
    use_tirads: false
  - type: dinov3_unet_multitask
    name: ThyroidXL
    model_path: ../Classification_Agent/weights/ThyroidXL/dino_unet_train_multitask_ThyroidXL_epoch_50.pth
    use_tirads: false
  agent:
    enable_agent: true
    routing_mode: llm
    brief_routing_prompt: true
    metadata_mode: full
    top_k: 5
    consensus_min_confidence: 0.6
radiomics_judge:
  enabled: true
  model_dir: ../Classification_Agent/weights/dataset_3/autogluon_model_20260106_215755
  top_k_features: 5
  radiomics_params: null
pipeline:
  preload_workers: 4
  stop_after_phase2: false
  run_segmentation: {_bool_yaml(cohort["run_segmentation"])}
  run_classification: {_bool_yaml(cohort["run_classification"])}
  data:
    image_input: {cohort["image_input"]}
{mask_line}
{label_line}
    label_key: malignancy
    device_info:
    - GE Logiq E9
    - GE S7
    start_index: 0
    max_images: null
  log_routing: true
  routing_log_include_prompts: false
  output:
    output_dir: {out_run}
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for cohort in COHORTS:
        path = OUT_DIR / f"{cohort['name']}.yaml"
        path.write_text(render(cohort), encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")
    print("done.")


if __name__ == "__main__":
    main()
