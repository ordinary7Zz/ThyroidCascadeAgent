#!/usr/bin/env python3
"""从 config/b3/sample.yaml 生成各队列的 config/b3/<cohort>.yaml 与 config/b4/<cohort>.yaml。"""

from __future__ import annotations

import repo_path

repo_path.install()

import json
from pathlib import Path

import yaml

ROOT = repo_path.find_repo_root()
CONFIG = ROOT / "config"
B3_DIR = CONFIG / "b3"
B4_DIR = CONFIG / "b4"
B5_DIR = CONFIG / "b5"
B3_TEMPLATE = B3_DIR / "sample.yaml"

B5_METADATA_MODES = (
    "full",
    "drop_device",
    "drop_source",
    "drop_both",
    "quality_only",
)

# 正式 B3 跑数前：将 segmentation/classification 与 config/config_<cohort>.yaml 全文对齐（Table S3/S4）。
_DATA = "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test"
_AUG = "/mnt/wangbd8/workspace/DataSets/ThyroidAgent"

# ablation_task: seg | cls | both；可选 run_segmentation / run_classification 覆盖 pipeline 开关
COHORTS: dict[str, dict] = {
    "sample": {
        "image_input": "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/sample/images",
        "gt_mask_dir": "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/sample/masks",
        "label_file": "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/sample/sample_test_label.json",
        "pipeline_run": "output/sample/pipeline_run",
    },
    "tn3k": {
        "image_input": "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/TN3K/test/images",
        "gt_mask_dir": "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/TN3K/test/masks",
        "label_file": "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/TN3K/test/TN3K_test_label.json",
        "pipeline_run": "output/TN3K/pipeline_run",
    },
    "tn5k": {
        "image_input": "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/TN5K/test/images",
        "gt_mask_dir": "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/TN5K/test/masks",
        "label_file": "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/TN5K/test/TN5K_test_label.json",
        "pipeline_run": "output/TN5K/pipeline_run",
    },
    "thyroidxl": {
        "image_input": "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/ThyroidXL/test/images",
        "gt_mask_dir": "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/ThyroidXL/test/masks",
        "label_file": "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/ThyroidXL/test/ThyroidXL_test_label.json",
        "pipeline_run": "output/ThyroidXL/pipeline_run",
    },
    "zjh8k": {
        "image_input": "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/ZJH-8K/images",
        "gt_mask_dir": "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/ZJH-8K/masks",
        "label_file": "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/ZJH-8K/ZJH-8K_BM_labels.json",
        "pipeline_run": "output/ZJH-8K/pipeline_run",
    },
    "rjh7k": {
        "image_input": f"{_AUG}/augtrain_PNG/image",
        "gt_mask_dir": f"{_AUG}/augtrain_PNG/mask",
        "label_file": "",
        "pipeline_run": "output/RJH-7K/pipeline_run",
        "ablation_task": "both",
    },
    "ddti_seg": {
        "image_input": f"{_DATA}/DDTI/all_seg/images",
        "gt_mask_dir": f"{_DATA}/DDTI/all_seg/masks",
        "label_file": "",
        "pipeline_run": "output/DDTI_seg/pipeline_run",
        "ablation_task": "seg",
    },
    "ddti_cls": {
        "image_input": f"{_DATA}/DDTI_Classification/all/images_processed",
        "gt_mask_dir": "",
        "label_file": f"{_DATA}/DDTI_Classification/all/DDTI_Classification_test_label.json",
        "pipeline_run": "output/DDTI_cls/pipeline_run",
        "ablation_task": "cls",
    },
    "pktn": {
        "image_input": f"{_DATA}/PKTN/test/images",
        "gt_mask_dir": f"{_DATA}/PKTN/test/masks",
        "label_file": "",
        "pipeline_run": "output/PKTN/pipeline_run",
        "ablation_task": "seg",
    },
    "nhc_misd_tus": {
        "image_input": "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/NHC-MISD-TUS/images",
        "gt_mask_dir": "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/NHC-MISD-TUS/masks",
        "label_file": "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/NHC-MISD-TUS/labels.json",
        "pipeline_run": "output/NHC-MISD-TUS/pipeline_run",
    },
}


def _load_b3_template() -> dict:
    with open(B3_TEMPLATE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_b3(cohort_id: str, paths: dict) -> dict:
    cfg = _load_b3_template()
    b3_root = f"output/ablation/b3/{cohort_id}"
    shared = f"{paths['pipeline_run']}/intermediate"
    pipe = cfg.setdefault("pipeline", {})
    ab = pipe.setdefault("ablation", {})
    ab["shared_intermediate"] = shared
    ab["output_root"] = b3_root
    ab["routing_modes"] = [
        "soft_voting",
        "majority",
        "max_confidence",
        "static_rule",
        "best_single",
        "oracle",
    ]
    ab.setdefault("static_rule_use_radiomics_judge", False)
    data = pipe.setdefault("data", {})
    data["image_input"] = paths["image_input"]
    data["gt_mask_dir"] = paths["gt_mask_dir"]
    data["label_file"] = paths["label_file"]
    data.setdefault("label_key", "malignancy")
    data.setdefault("device_info", ["GE Logiq E9", "GE S7"])
    data.setdefault("start_index", 0)
    data.setdefault("max_images", None)
    task = paths.get("ablation_task", "both")
    ab["task"] = task
    pipe["run_segmentation"] = paths.get(
        "run_segmentation", task in ("seg", "both")
    )
    pipe["run_classification"] = paths.get(
        "run_classification", task in ("cls", "both")
    )
    # run_pipeline.py 写入 intermediate 的目录须与 shared_intermediate 父路径一致
    pipe.setdefault("output", {})["output_dir"] = paths["pipeline_run"]
    return cfg


def build_b5(cohort_id: str, paths: dict) -> dict:
    cfg = build_b3(cohort_id, paths)
    b5_root = f"output/ablation/b5/{cohort_id}"
    pipe = cfg.setdefault("pipeline", {})
    ab = pipe.setdefault("ablation", {})
    ab["output_root"] = b5_root
    ab["dataset_id"] = cohort_id
    ab["metadata_modes"] = list(B5_METADATA_MODES)
    ab["routing_modes"] = ["llm"]
    ab["force_phase3"] = True
    data = pipe.setdefault("data", {})
    data.setdefault(
        "input_data_info",
        {"dataset_name": cohort_id, "split": "test"},
    )
    seg_agent = cfg.setdefault("segmentation", {}).setdefault("agent", {})
    cls_agent = cfg.setdefault("classification", {}).setdefault("agent", {})
    seg_agent["routing_mode"] = "llm"
    seg_agent["enable_agent"] = True
    seg_agent["metadata_mode"] = "full"
    cls_agent["routing_mode"] = "llm"
    cls_agent["enable_agent"] = True
    cls_agent["metadata_mode"] = "full"
    pipe.setdefault("output", {})["output_dir"] = f"{b5_root}/placeholder"
    return cfg


def build_b4(cohort_id: str, paths: dict) -> dict:
    b3_root = f"output/ablation/b3/{cohort_id}"
    return {
        "pipeline": {
            "ablation_b4": {
                "dataset_id": cohort_id,
                "b3_root": b3_root,
                "l2_b3_mode": "soft_voting",
                "l3_b3_mode": "llm",
                "s4_replica_b3_mode": "llm",
                "l1_metrics": f"artifacts/b4_l1_{cohort_id}_placeholder.json",
                "reference_manifest": f"{b3_root}/soft_voting/intermediate_manifest.json",
                "pathb": {
                    "b_a_b3_mode": "soft_voting",
                    "b_b_b3_mode": "path_b_autogluon",
                    "b_b_metrics_dir": None,
                    "b_c_b3_mode": "llm",
                },
            },
            "output": {"output_dir": f"output/ablation/b4/{cohort_id}"},
        }
    }


def write_l1_placeholder(cohort_id: str) -> None:
    path = ROOT / "artifacts" / f"b4_l1_{cohort_id}_placeholder.json"
    if path.is_file():
        return
    doc = {
        "note": "L1 占位：正式实验替换为单专家全队列评测 JSON（见 fit / my_Thyroid_Infer）",
        "dataset_id": cohort_id,
        "segmentation": {
            "dice_mean": None,
            "dice_ci_lower": None,
            "dice_ci_upper": None,
            "hd95_mean": None,
        },
        "classification": {
            "n": None,
            "accuracy": None,
            "auroc": None,
            "auroc_ci_lower": None,
            "auroc_ci_upper": None,
            "auprc": None,
        },
        "classification_path_b": {"n": None, "accuracy": None},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main() -> None:
    header = (
        "# 由 scripts/generate_ablation_configs.py 生成；可手改 data 路径。\n"
        "# 波次 1：run_b3_batch.py --preset wave1（不含 learned/llm）。\n"
        "# Phase 1–2 请先：python run_pipeline.py --config config/config_<队列>.yaml\n"
    )
    b4_header = (
        "# B4 汇总；L3/B-c 需 B3 llm 目录存在后再 build_b4_tables.py。\n"
    )
    b5_header = (
        "# B5 元数据消融；须先有 pipeline_run/intermediate。批量: scripts/revision/b5/run_b5_batch.py\n"
        "# full 可与 B3 llm 复用: run_b5_batch.py --skip-full\n"
    )
    B3_DIR.mkdir(parents=True, exist_ok=True)
    B4_DIR.mkdir(parents=True, exist_ok=True)
    B5_DIR.mkdir(parents=True, exist_ok=True)
    for cohort_id, paths in COHORTS.items():
        b3_path = B3_DIR / f"{cohort_id}.yaml"
        b4_path = B4_DIR / f"{cohort_id}.yaml"
        b5_path = B5_DIR / f"{cohort_id}.yaml"
        b3_doc = build_b3(cohort_id, paths)
        b4_doc = build_b4(cohort_id, paths)
        b5_doc = build_b5(cohort_id, paths)
        with open(b3_path, "w", encoding="utf-8") as f:
            f.write(header)
            yaml.dump(b3_doc, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        with open(b4_path, "w", encoding="utf-8") as f:
            f.write(b4_header)
            yaml.dump(b4_doc, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        with open(b5_path, "w", encoding="utf-8") as f:
            f.write(b5_header)
            yaml.dump(b5_doc, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        write_l1_placeholder(cohort_id)
        print(f"wrote {b3_path.name} {b4_path.name} {b5_path.name}")


if __name__ == "__main__":
    main()

import importlib.util
from pathlib import Path


