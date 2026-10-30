#!/usr/bin/env python3
"""生成 config/revision/b6/<cohort>.yaml，结构与 config/revision/b6/sample_stability.yaml 一致。"""

from __future__ import annotations

import importlib.util
from pathlib import Path

def __revision_bootstrap() -> None:
    p = Path(__file__).resolve()
    for d in [p.parent, *p.parents]:
        if d.name == "revision" and (d / "_path_setup.py").is_file():
            spec = importlib.util.spec_from_file_location("_rev_path_setup", d / "_path_setup.py")
            mod = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(mod)
            mod.bootstrap(__file__)
            return
    raise RuntimeError(f"revision _path_setup.py not found above {__file__}")

__revision_bootstrap()

import importlib.util
from pathlib import Path

from pathlib import Path

import repo_path
ROOT = repo_path.find_repo_root()
OUT_DIR = ROOT / "config" / "revision" / "b6"
DATA = Path("/mnt/wangbd8/workspace/DataSets/ThyroidAgent")

COHORTS: list[dict] = [
    {
        "name": "tn3k",
        "task": "both",
        "run_segmentation": True,
        "run_classification": True,
        "image_input": DATA / "train_val_test/TN3K/test_for_llm_malignancy/images",
        "gt_mask_dir": DATA / "train_val_test/TN3K/test_for_llm_malignancy/masks",
        "label_file": DATA / "train_val_test/TN3K/test_for_llm_malignancy/TN3K_test_label.json",
    },
    {
        "name": "tn5k",
        "task": "both",
        "run_segmentation": True,
        "run_classification": True,
        "image_input": DATA / "train_val_test/TN5K/test_for_llm_malignancy/images",
        "gt_mask_dir": DATA / "train_val_test/TN5K/test_for_llm_malignancy/masks",
        "label_file": DATA / "train_val_test/TN5K/test_for_llm_malignancy/TN5K_test_label.json",
    },
    {
        "name": "thyroidxl",
        "task": "both",
        "run_segmentation": True,
        "run_classification": True,
        "image_input": DATA / "train_val_test/ThyroidXL/test_for_llm_malignancy/images",
        "gt_mask_dir": DATA / "train_val_test/ThyroidXL/test_for_llm_malignancy/masks",
        "label_file": DATA
        / "train_val_test/ThyroidXL/test_for_llm_malignancy/ThyroidXL_test_label.json",
    },
    {
        "name": "pktn",
        "task": "seg",
        "run_segmentation": True,
        "run_classification": False,
        "image_input": DATA / "train_val_test/PKTN/test_for_llm_malignancy/images",
        "gt_mask_dir": DATA / "train_val_test/PKTN/test_for_llm_malignancy/masks",
        "label_file": DATA / "train_val_test/PKTN/test_for_llm_malignancy/PKTN_test_label.json",
    },
    {
        "name": "zjh8k",
        "task": "both",
        "run_segmentation": True,
        "run_classification": True,
        "llm_model_name": "qwen3.8-27b",
        "image_input": DATA / "train_val_test/ZJH-8K_for_llm_malignancy/images",
        "gt_mask_dir": DATA / "train_val_test/ZJH-8K_for_llm_malignancy/masks",
        "label_file": DATA / "train_val_test/ZJH-8K_for_llm_malignancy/ZJH-8K_BM_labels.json",
    },
    {
        "name": "rjh7k",
        "task": "seg",
        "run_segmentation": True,
        "run_classification": False,
        "image_input": DATA / "augtrain_PNG_for_llm_malignancy/image",
        "gt_mask_dir": DATA / "augtrain_PNG_for_llm_malignancy/mask",
        "label_file": None,
    },
    {
        "name": "ddti_seg",
        "task": "seg",
        "run_segmentation": True,
        "run_classification": False,
        "image_input": DATA / "train_val_test/DDTI/all_seg_for_llm_malignancy/images",
        "gt_mask_dir": DATA / "train_val_test/DDTI/all_seg_for_llm_malignancy/masks",
        "label_file": None,
    },
    {
        "name": "ddti_cls",
        "task": "cls",
        "run_segmentation": False,
        "run_classification": True,
        "llm_model_name": "qwen3.8-max",
        "image_input": DATA
        / "train_val_test/DDTI_Classification/all_for_llm_malignancy/images_processed",
        "gt_mask_dir": None,
        "label_file": DATA
        / "train_val_test/DDTI_Classification/all_for_llm_malignancy/DDTI_Classification_test_label.json",
    },
]

DEFAULT_LLM_MODEL = "deepseek-v4-pro-0813"


def _bool_yaml(v: bool) -> str:
    return "true" if v else "false"


def render(cohort: dict) -> str:
    name = cohort["name"]
    llm_model = cohort.get("llm_model_name", DEFAULT_LLM_MODEL)
    out_run = f"output/b6/{name}/pipeline_run"
    inter = f"{out_run}/intermediate"
    label = cohort.get("label_file")
    label_line = f"    label_file: {label}" if label else "    label_file: ''"
    mask = cohort.get("gt_mask_dir")
    mask_line = f"    gt_mask_dir: {mask}" if mask else "    gt_mask_dir: ''"

    return f"""# B6 路由稳定性（5× LLM 重复）；数据为 test_for_llm 子集（非全量 test）。
# 构建子集: bash scripts/build_all_test_for_llm.sh
# 用法:
#   export DASHSCOPE_API_KEY=...
#   python run_pipeline.py --config config/revision/b6/{name}.yaml --device cuda
#   python run_routing_stability.py \\
#     --config config/revision/b6/{name}.yaml \\
#     --output-dir {out_run} \\
#     --repeats 5 --device cuda
#
# 结构对齐 config/revision/b6/sample_stability.yaml；勿用于 B3 波次 1 static bundle。
shared:
  agent_llm:
    api_key_env: DASHSCOPE_API_KEY
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    model_name: {llm_model}
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
    top_k: 5
    consensus_min_confidence: 0.6
radiomics_judge:
  enabled: true
  model_dir: ../Classification_Agent/weights/dataset_3/autogluon_model_20260106_215755
  top_k_features: 5
  radiomics_params: null
pipeline:
  preload_workers: 4
  stop_after_phase2: true
  run_segmentation: {_bool_yaml(cohort["run_segmentation"])}
  run_classification: {_bool_yaml(cohort["run_classification"])}
  ablation:
    routing_modes:
    - soft_voting
    - majority
    - max_confidence
    - static_rule
    - best_single
    - oracle
    shared_intermediate: {inter}
    output_root: output/ablation/b6/{name}
    force_phase3: true
    summarize: true
    task: {cohort["task"]}
    learned_router:
      seg_artifact: artifacts/learned_router_seg.joblib
      cls_artifact: artifacts/learned_router_cls.joblib
      allow_missing_artifact: true
      write_random_artifact: false
      params:
        C: 0.1
        max_iter: 200
        random_state: 42
        random_init: true
        random_coef_scale: 0.05
    best_single_seg: all_datasets
    best_single_cls: all_datasets
    val_list: null
  data:
    image_input: {cohort["image_input"]}
{mask_line}
{label_line}
    label_key: malignancy
    device_info:
    - GE Logiq E9
    - GE S7
    stability_sample:
      n: 10
      seed: 42
      mode: random
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
