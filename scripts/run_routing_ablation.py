#!/usr/bin/env python3
"""B3 路由消融：在共享 intermediate 上切换 routing_mode，重跑 Phase 3–5（波次 0–1）。

与 ``run_pipeline.py`` 同级能力，但面向消融目录约定；实现依赖 ``pipeline/``，不反向被 cascade 引用。

示例（sample 队列，共享地基 + 静态规则）:
  python scripts/run_routing_ablation.py \\
    --config config/revision/b3/sample.yaml \\
    --routing-mode static_rule \\
    --task both \\
    --shared-intermediate output/sample/pipeline_run/intermediate \\
    --output-dir output/ablation/b3/sample/static_rule \\
    --force-phase3
"""

from __future__ import annotations


import argparse
import os
from pathlib import Path

import repo_path
import yaml

ROOT = repo_path.install()

from classification.agent import LLMClassificationAgent
from pipeline import CascadePipeline
from pipeline.revision.b3.ablation_metrics import build_b3_metrics, save_b3_metrics
from pipeline.evaluate import evaluate_pipeline
from pipeline.revision.b3.intermediate_manifest import write_intermediate_manifest
from pipeline.revision.b3.routing_ablation import prepare_ablation_run
from pipeline.revision.b3.routing_methods import write_routing_methods_report
from radiomics_judge import RadiomicsJudge
from segmentation.agent import SegmentationAgent
from segmentation.quality_evaluator import SegmentationQualityEvaluator
from shared.image_io import ImageIO
from shared.llm_client import build_llm_client
from shared.routing_log import build_routing_logger_from_config
from shared.routing_modes import get_cls_routing_mode, get_seg_routing_mode


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="B3 routing ablation (wave 0–1)")
    parser.add_argument("--config", default="config/revision/b3/sample.yaml")
    parser.add_argument(
        "--routing-mode",
        default=None,
        help="seg 与 cls 使用同一策略（与 --routing-mode-seg/cls 二选一）",
    )
    parser.add_argument("--routing-mode-seg", default=None, help="仅覆盖分割 Phase 3")
    parser.add_argument("--routing-mode-cls", default=None, help="仅覆盖分类 Path B")
    parser.add_argument("--task", choices=("seg", "cls", "both"), default="both")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--shared-intermediate",
        required=True,
        help="已有 Phase 1–2 产物的 intermediate 目录（含 seg/ cls）",
    )
    parser.add_argument("--force-phase3", action="store_true")
    parser.add_argument(
        "--metadata-mode",
        default=None,
        help="B5：full | drop_device | drop_source | drop_both | quality_only",
    )
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--start-index", type=int, default=None, help="覆盖 pipeline.data.start_index")
    parser.add_argument("--max-images", type=int, default=None, help="覆盖 pipeline.data.max_images")
    parser.add_argument("--skip-eval", action="store_true")
    parser.add_argument(
        "--best-single-artifact",
        default=None,
        help="fit_best_single_expert.py 产出的 JSON（routing_mode=best_single 时使用）",
    )
    args = parser.parse_args()

    if not args.routing_mode and not args.routing_mode_seg and not args.routing_mode_cls:
        parser.error("须指定 --routing-mode 或 --routing-mode-seg / --routing-mode-cls")
    if args.routing_mode and (args.routing_mode_seg or args.routing_mode_cls):
        parser.error("--routing-mode 与 --routing-mode-seg/cls 不要同时使用")

    base_config = load_config(args.config)
    artifact = Path(args.best_single_artifact) if args.best_single_artifact else None
    if artifact is None:
        default_art = ROOT / "artifacts" / "best_single.json"
        if default_art.is_file():
            artifact = default_art
    cfg = prepare_ablation_run(
        base_config,
        Path(args.output_dir),
        shared_intermediate=Path(args.shared_intermediate),
        routing_mode=args.routing_mode,
        routing_mode_seg=args.routing_mode_seg,
        routing_mode_cls=args.routing_mode_cls,
        metadata_mode=args.metadata_mode,
        task=args.task,
        force_phase3=args.force_phase3,
        best_single_artifact=artifact,
    )
    if args.start_index is not None:
        cfg.setdefault("pipeline", {}).setdefault("data", {})["start_index"] = args.start_index
    if args.max_images is not None:
        cfg.setdefault("pipeline", {}).setdefault("data", {})["max_images"] = args.max_images

    llm_cfg = cfg["shared"]["agent_llm"]
    seg_cfg = cfg["segmentation"]
    cls_cfg = cfg["classification"]
    judge_cfg = cfg.get("radiomics_judge", {})
    pipe_cfg = cfg.get("pipeline", {})
    data_cfg = pipe_cfg.get("data", {})

    seg_mode = get_seg_routing_mode(cfg)
    cls_mode = get_cls_routing_mode(cfg)
    need_llm = seg_mode == "llm" or cls_mode == "llm"

    if need_llm:
        api_key = os.getenv(llm_cfg["api_key_env"], "")
        llm_client = build_llm_client(llm_cfg, api_key)
    else:
        llm_client = None
        print("✓ 非 LLM 模式，跳过 LLM 客户端")

    judge = None
    if judge_cfg.get("enabled", False) and pipe_cfg.get("run_segmentation", True):
        try:
            judge = RadiomicsJudge(
                model_dir=judge_cfg["model_dir"],
                top_k_features=judge_cfg.get("top_k_features", 5),
                shap_reference_path=judge_cfg.get("shap_reference_path"),
                radiomics_params=judge_cfg.get("radiomics_params"),
            )
        except Exception as e:
            print(f"⚠️ Radiomics 裁判加载失败: {e}")

    output_dir = Path(args.output_dir)
    routing_logger = build_routing_logger_from_config(cfg, output_dir)

    seg_agent = SegmentationAgent(
        llm_client=llm_client,
        quality_evaluator=SegmentationQualityEvaluator(),
        radiomics_judge=judge,
        config=seg_cfg.get("agent", {}),
        routing_logger=routing_logger,
    )
    cls_agent = LLMClassificationAgent(
        llm_client=llm_client,
        config=cls_cfg.get("agent", {}),
        routing_logger=routing_logger,
    )

    if args.task == "seg":
        cfg.setdefault("pipeline", {})["run_classification"] = False
    elif args.task == "cls":
        cfg.setdefault("pipeline", {})["run_segmentation"] = False

    pipeline = CascadePipeline(
        seg_agent=seg_agent,
        cls_agent=cls_agent,
        image_io=ImageIO(),
        config=cfg,
        device=args.device,
    )

    results = pipeline.run_batch(
        image_dir=data_cfg["image_input"],
        output_dir=str(output_dir),
        gt_mask_dir=data_cfg.get("gt_mask_dir"),
        label_file=data_cfg.get("label_file"),
        label_key=data_cfg.get("label_key", "malignancy"),
        input_device_info=data_cfg.get("device_info"),
        input_data_info=data_cfg.get("input_data_info"),
        start_index=data_cfg.get("start_index", 0),
        max_images=data_cfg.get("max_images"),
        force_phase3=args.force_phase3,
    )

    write_intermediate_manifest(output_dir / "intermediate", output_dir / "intermediate_manifest.json")
    write_routing_methods_report(output_dir, results)

    metrics = {}
    if not args.skip_eval:
        metrics = evaluate_pipeline(
            results,
            str(output_dir),
            image_io=ImageIO(),
            gt_mask_dir=data_cfg.get("gt_mask_dir"),
        )
        run_label = seg_mode if seg_mode == cls_mode else f"{seg_mode}__{cls_mode}"
        meta_mode = seg_cfg.get("agent", {}).get("metadata_mode")
        b3 = build_b3_metrics(
            results,
            metrics,
            routing_mode=run_label,
            task=args.task,
            seg_mode=seg_mode,
            cls_mode=cls_mode,
            metadata_mode=meta_mode,
        )
        save_b3_metrics(output_dir, b3)
        print(f"✓ b3_metrics.json 已写入 {output_dir}")

    run_label = seg_mode if seg_mode == cls_mode else f"{seg_mode}__{cls_mode}"
    print(f"完成: {len(results)} 张, seg={seg_mode}, cls={cls_mode}, task={args.task}")


if __name__ == "__main__":
    main()
