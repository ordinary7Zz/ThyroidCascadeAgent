#!/usr/bin/env python3
"""B10: build Supplementary baseline training protocol table from b2_exports manifests."""

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

import json
from pathlib import Path

import repo_path
REPO = repo_path.find_repo_root()
EXPORTS = REPO.parent / "b2_exports"
OUT_DIR = REPO / "docs/revision/b10/tables"

# Training protocol narrative (see docs/revision/b10/B10_基线训练协议总结.md)
DEV_SEG = (
    "OpenThyroid stacked seg development: dataset_4 "
    "(TN3K + ThyroidXL + PKTN + TN5K); train under "
    "train_val_test/Superimposed_experiment/dataset_4/train"
)
DEV_CLS = (
    "OpenThyroid stacked cls development: dataset_3 "
    "(TN3K + ThyroidXL + TN5K); "
    "train_val_test/Superimposed_multitask/dataset_3_cls/train "
    "(ResNet-50 / DINO multitask: dataset_3 with JSON, same image count)"
)

UPSTREAM: dict[tuple[str, str], str] = {
    ("TransUNet", "segmentation"): "ImageNet-21k ViT-B/16 (TransUNet default)",
    ("MedSAM2", "segmentation"): "SAM2.1 Hiera pretrained",
    ("MedSegX", "segmentation"): "SAM ViT-B + MedSegX thyroid adapter",
    ("UltraFedFM", "segmentation"): "MAE / federated FM pretrained + dataset_4 finetune",
    ("RepViT", "classification"): "ImageNet-pretrained RepViT; full fine-tune on dataset_3",
    ("LSNet", "classification"): "ImageNet-pretrained LSNet; full fine-tune on dataset_3",
    ("UltraFedFM", "classification"): "ViT backbone pretrained + dataset_3_cls finetune",
    ("BiomedCLIP", "classification"): "OpenCLIP BiomedCLIP + dataset_3_cls head finetune",
    ("MedSigLIP", "classification"): "Google MedSigLIP + partial finetune on dataset_3_cls",
    ("ResNet-50", "classification"): "ImageNet ResNet-50 + dataset_3 finetune",
}

THYROIDXAGENT_ROWS = [
    {
        "model": "ThyroidXAgent (segmentation router)",
        "task": "segmentation",
        "protocol": "full_finetune",
        "upstream_pretraining": "DINOv3 backbone (ImageNet-scale pretrain); full fine-tune on dataset_4",
        "thyroid_development_set": DEV_SEG
        + "; full merge also uses Superimposed_experiment/dataset_4/images",
        "model_selection_split": "dataset_4 internal train/val (publisher splits)",
        "checkpoint_for_tables": "Segmentation_Agent / dino_unet dataset_4 weights (see config)",
        "inference_input": "US image → routed expert mask",
        "notes": "Table S6 progressive stacks reported separately; S3 uses full-stack checkpoint",
        "in_s3_s4_baseline_export": False,
    },
    {
        "model": "ThyroidXAgent (classification router)",
        "task": "classification",
        "protocol": "full_finetune",
        "upstream_pretraining": "DINOv3 backbone (ImageNet-scale pretrain); full multitask fine-tune on dataset_3",
        "thyroid_development_set": DEV_CLS,
        "model_selection_split": "dataset_3 train/val",
        "checkpoint_for_tables": "infer_dinov3_unet_multitask / Classification_Agent weights",
        "inference_input": "Routed mask + image (pipeline config)",
        "notes": "Same stacked cls data as supervised baselines for fair comparison",
        "in_s3_s4_baseline_export": False,
    },
]

VLM_ROWS = [
    {
        "model": "MedGemma",
        "task": "classification",
        "protocol": "finetune",
        "upstream_pretraining": "Public MedGemma; fine-tuned on dataset_3",
        "thyroid_development_set": DEV_CLS,
        "model_selection_split": "dataset_3 train/val",
        "checkpoint_for_tables": "vllms / finetune scripts on dataset_3",
        "inference_input": "image only",
        "notes": "Open-weight VLM fine-tuned on thyroid cls development",
        "in_s3_s4_baseline_export": False,
    },
    {
        "model": "Qwen3-VL",
        "task": "classification",
        "protocol": "finetune",
        "upstream_pretraining": "Public Qwen3-VL; fine-tuned on dataset_3",
        "thyroid_development_set": DEV_CLS,
        "model_selection_split": "dataset_3 train/val",
        "checkpoint_for_tables": "vllms / finetune scripts on dataset_3",
        "inference_input": "image only",
        "notes": "Open-weight VLM fine-tuned on thyroid cls development",
        "in_s3_s4_baseline_export": False,
    },
    {
        "model": "GPT-5 / Gemini",
        "task": "classification",
        "protocol": "zero_shot_or_api",
        "upstream_pretraining": "Vendor API; not trained on thyroid development sets",
        "thyroid_development_set": "None",
        "model_selection_split": "N/A",
        "checkpoint_for_tables": "API with fixed prompts",
        "inference_input": "image + fixed text prompt",
        "notes": "Closed API models; no dataset_3 E2E training",
        "in_s3_s4_baseline_export": False,
    },
]


def load_export_rows() -> list[dict]:
    rows: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for manifest_path in sorted(EXPORTS.glob("*/*/manifest.json")):
        if "_example" in manifest_path.parts:
            continue
        m = json.loads(manifest_path.read_text(encoding="utf-8"))
        model = m.get("model_id", manifest_path.parent.parent.name)
        task = m.get("task", "")
        key = (model, task)
        if key in seen:
            continue
        seen.add(key)
        dev = DEV_SEG if task == "segmentation" else DEV_CLS
        inf = m.get("inference_input", "")
        if task == "segmentation":
            inf_note = "US image + GT box/mask for expert (gt_mask)" if inf == "gt_mask" else inf
        else:
            inf_note = "US image (image_only)" if inf == "image_only" else inf
        rows.append(
            {
                "model": model,
                "task": task,
                "protocol": "full_finetune_on_stacked_dev",
                "upstream_pretraining": UPSTREAM.get(key, "Public pretrained + thyroid finetune"),
                "thyroid_development_set": dev,
                "model_selection_split": "Publisher train/val within stacked dev (per model script)",
                "checkpoint_for_tables": m.get("checkpoint", ""),
                "inference_input": inf_note,
                "notes": f"Exported eval: my_Thyroid_Infer; metrics in b2_exports/{model}/",
                "in_s3_s4_baseline_export": True,
                "manifest_example": str(manifest_path),
            }
        )
    return rows


def to_markdown(rows: list[dict]) -> str:
    cols = [
        "model",
        "task",
        "protocol",
        "upstream_pretraining",
        "thyroid_development_set",
        "checkpoint_for_tables",
        "inference_input",
    ]
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    lines = [
        "# Supplementary Table S[X] — Baseline training and inference protocol (B10)",
        "",
        "Supervised rows match **Table S3/S4** exports (`b2_exports`, 2026-10-21). "
        "External test cohorts are not used for development finetuning.",
        "",
        header,
        sep,
    ]
    for r in rows:
        lines.append("| " + " | ".join(str(r.get(c, "")).replace("|", "\\|") for c in cols) + " |")
    return "\n".join(lines) + "\n"


def main() -> None:
    supervised = load_export_rows()
    all_rows = supervised + THYROIDXAGENT_ROWS + VLM_ROWS
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_from": str(EXPORTS),
        "n_supervised_models": len(supervised),
        "rows": all_rows,
    }
    json_path = OUT_DIR / "baseline_training_protocol.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path = OUT_DIR / "baseline_training_protocol.md"
    md_path.write_text(to_markdown(all_rows), encoding="utf-8")
    print(f"Wrote {len(all_rows)} rows -> {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()

import importlib.util
from pathlib import Path


