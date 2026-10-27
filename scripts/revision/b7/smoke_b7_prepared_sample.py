#!/usr/bin/env python3
"""用 run_nhc_prepare 产出目录模拟 pipeline 输出，供 B7 冒烟（无需 GPU）。预测 mask = GT。"""

from __future__ import annotations

import importlib.util
import json
import shutil
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


__revision_bootstrap()

import numpy as np

import repo_path

repo_path.install()

from pipeline.cascade import CascadePipeline
from shared.image_io import ImageIO


def build_smoke_pipeline_run(prepared_dir: Path, pipeline_out: Path) -> None:
    prepared_dir = prepared_dir.resolve()
    pipeline_out = pipeline_out.resolve()
    pipeline_out.mkdir(parents=True, exist_ok=True)
    (pipeline_out / "intermediate").mkdir(exist_ok=True)

    labels = json.loads((prepared_dir / "labels.json").read_text(encoding="utf-8"))
    io = ImageIO()
    image_names: list[str] = []
    selected_masks: list[np.ndarray] = []
    results: list[dict] = []

    for row in labels:
        fn = row["filename"]
        nodule_path = prepared_dir / "nodule_masks" / fn
        if not nodule_path.is_file():
            continue
        mask = io.binarize_mask(io.load_mask(nodule_path))
        image_names.append(fn)
        selected_masks.append(mask)
        mal = row.get("malignancy", -1)
        conf = 0.85 if mal == 1 else 0.15 if mal == 0 else 0.5
        rec = {
            "image_name": fn,
            "true_label": mal,
            "final_label": mal if mal in (0, 1) else 0,
            "final_confidence": conf,
        }
        if row.get("center_id"):
            rec["center_id"] = row["center_id"]
        results.append(rec)

    seg_decisions = [
        {
            "img_name": fn,
            "consensus": True,
            "anchor_class": None,
            "selected_model": "smoke",
            "confidence": 0.9,
            "reasoning": "smoke",
            "path": None,
            "method": "smoke",
            "all_predictions": [],
            "seg_agreement": {
                "num_seg_models": 1,
                "seg_min_pairwise_iou": 1.0,
                "seg_mean_pairwise_iou": 1.0,
                "seg_volume_cv": 0.0,
            },
        }
        for fn in image_names
    ]
    CascadePipeline._save_selected_masks_npz(
        pipeline_out / "intermediate" / "selected_masks.npz",
        image_names,
        selected_masks,
        seg_decisions,
    )
    (pipeline_out / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    pred_gland = pipeline_out / "gland_pred_smoke"
    if pred_gland.exists():
        shutil.rmtree(pred_gland)
    shutil.copytree(prepared_dir / "gland_masks", pred_gland)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prepared-dir",
        type=Path,
        default=Path("output/b7/nhc_prepared_smoke"),
    )
    parser.add_argument(
        "--pipeline-out",
        type=Path,
        default=Path("output/b7/smoke_pipeline_run"),
    )
    args = parser.parse_args()
    if not (args.prepared_dir / "labels.json").is_file():
        raise SystemExit(f"缺少 labels.json: {args.prepared_dir}")
    build_smoke_pipeline_run(args.prepared_dir, args.pipeline_out)
    print(f"✓ 冒烟 pipeline 输出: {args.pipeline_out} ({len(list(json.loads((args.pipeline_out / 'results.json').read_text())))} 条)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
