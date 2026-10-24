#!/usr/bin/env python3
"""
B6 路由稳定性：在已有 intermediate 缓存上对 LLM 路由重复 N 次。

用法:
  python run_routing_stability.py --config config/config.yaml \\
    --output-dir output/shared_output/pipeline_run --repeats 5 --max-cases 50

要求: output-dir 下已有 intermediate/seg 与 intermediate/cls（先跑 Phase 1–2 或完整 pipeline）。
分割/分类 agent 须 enable_agent: true，且配置 DASHSCOPE_API_KEY。
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import yaml

from shared.image_io import ImageIO
from shared.llm_client import LLMClient
from shared.routing_log import build_routing_logger_from_config
from segmentation import SegmentationQualityEvaluator, SegmentationAgent
from classification import LLMClassificationAgent
from pipeline.cascade import CascadePipeline
from pipeline.revision.b6.routing_stability import run_stability_from_caches
from radiomics_judge import RadiomicsJudge


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="B6 routing stability (repeat LLM routing)")
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--output-dir", required=True, help="含 intermediate/ 的 pipeline 输出目录")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--max-cases", type=int, default=None)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    config = load_config(args.config)
    llm_cfg = config["shared"]["agent_llm"]
    seg_cfg = config["segmentation"]
    cls_cfg = config["classification"]
    pipe_cfg = config.get("pipeline", {})
    data_cfg = pipe_cfg.get("data", {})
    judge_cfg = config.get("radiomics_judge", {})

    enable_seg_agent = seg_cfg.get("agent", {}).get("enable_agent", False)
    enable_cls_agent = cls_cfg.get("agent", {}).get("enable_agent", False)
    if not enable_seg_agent and not enable_cls_agent:
        print("⚠️ segmentation/classification enable_agent 均为 false，无 LLM 可重复")
        return

    out = Path(args.output_dir)
    inter = out / "intermediate"
    print("=" * 60)
    print("B6 路由稳定性（复用 intermediate 缓存，仅重复 LLM 路由）")
    print("=" * 60)
    print(f"  config:      {args.config}")
    print(f"  output-dir:  {out.resolve()}")
    print(f"  repeats:     {args.repeats}")
    print(f"  max-cases:   {args.max_cases if args.max_cases is not None else 'all'}")
    print(f"  seg LLM:     {enable_seg_agent}")
    print(f"  cls LLM:     {enable_cls_agent}")
    print(f"  LLM model:   {llm_cfg.get('model_name')} (T={llm_cfg.get('temperature')})")

    api_key = os.getenv(llm_cfg["api_key_env"], "")
    if not api_key:
        print(f"⚠️ 警告: 环境变量 {llm_cfg['api_key_env']} 未设置，LLM 调用将失败")
    llm_client = LLMClient(
        api_key=api_key,
        base_url=llm_cfg["base_url"],
        model_name=llm_cfg["model_name"],
        temperature=llm_cfg["temperature"],
        max_tokens=llm_cfg["max_tokens"],
    )

    judge = None
    if judge_cfg.get("enabled", False):
        print("  加载 Radiomics 裁判...")
        judge = RadiomicsJudge(
            model_dir=judge_cfg["model_dir"],
            top_k_features=judge_cfg.get("top_k_features", 5),
            shap_reference_path=judge_cfg.get("shap_reference_path"),
            radiomics_params=judge_cfg.get("radiomics_params"),
        )
        print("  ✓ Radiomics 裁判已加载")
    else:
        print("  Radiomics 裁判: 未启用")

    routing_logger = build_routing_logger_from_config(config, out)
    if routing_logger.enabled:
        print(f"  routing_log: {routing_logger.path} (append)")
    else:
        print("  routing_log: 关闭 (pipeline.log_routing=false)")

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

    image_dir = Path(data_cfg["image_input"])
    exts = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
    image_paths = sorted(
        [f for f in image_dir.iterdir() if f.suffix.lower() in exts],
        key=lambda x: x.name,
    )
    img_names = [p.name for p in image_paths]
    print(f"  图像目录:    {image_dir} ({len(image_paths)} 张)")
    print(f"  seg 缓存:    {inter / 'seg'}")
    print(f"  cls 缓存:    {inter / 'cls'}")
    print("")

    summary = run_stability_from_caches(
        image_io=ImageIO(),
        seg_agent=seg_agent,
        cls_agent=cls_agent,
        image_paths=image_paths,
        img_names=img_names,
        seg_model_configs=seg_cfg.get("models", []),
        cls_model_configs=cls_cfg.get("models", []),
        seg_cache_dir=inter / "seg",
        cls_cache_dir=inter / "cls",
        load_seg_npz=CascadePipeline._load_seg_npz,
        load_cls_json=CascadePipeline._load_cls_json,
        check_classification_consensus=CascadePipeline._check_classification_consensus,
        consensus_threshold=cls_cfg.get("agent", {}).get("consensus_min_confidence", 0.6),
        enable_seg_agent=enable_seg_agent,
        enable_cls_agent=enable_cls_agent,
        device_info=data_cfg.get("device_info"),
        gt_mask_dir=data_cfg.get("gt_mask_dir"),
        repeats=args.repeats,
        max_cases=args.max_cases,
        output_path=out / "stability_summary.json",
    )

    print("")
    print("=" * 60)
    print("稳定性汇总（不含 per_case）")
    print("=" * 60)
    print(json_dumps_safe(summary))
    print(f"\n✓ 已写入 {out / 'stability_summary.json'}")


def json_dumps_safe(obj):
    import json
    return json.dumps(
        {k: v for k, v in obj.items() if k != "per_case"},
        ensure_ascii=False,
        indent=2,
    )


if __name__ == "__main__":
    main()
