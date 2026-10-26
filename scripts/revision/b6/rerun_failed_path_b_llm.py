#!/usr/bin/env python3
"""补跑 B6 / pipeline 中 Path B 分类 LLM 失败（如 Access denied 后 softvote 降级）的病例。

复用 output-dir 下 intermediate 与 selected_masks，仅重新调用 resolve_path_b，
更新 results.json，并替换 routing_log.jsonl 中对应 image 的旧 cls_path_b 行。

用法:
  export DASHSCOPE_API_KEY=...
  python scripts/revision/b6/rerun_failed_path_b_llm.py \\
    --config config/revision/b6/tn3k.yaml \\
    --output-dir output/b6/tn3k/pipeline_run
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
from datetime import datetime, timezone
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

import yaml

from classification import LLMClassificationAgent
from classification.base_model import ClsModelOutput
from pipeline import CascadePipeline
from shared.center_manifest import load_center_lookup
from radiomics_judge import RadiomicsJudge
from segmentation import SegmentationAgent, SegmentationQualityEvaluator
from shared.image_io import ImageIO
from shared.llm_client import build_llm_client
from shared.routing_log import build_routing_logger_from_config


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def failed_path_b_images(routing_log: Path) -> list[str]:
    """曾 Path B LLM 失败（softvote + error）的 image_name 列表。"""
    failed: list[str] = []
    seen: set[str] = set()
    with routing_log.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("task") != "cls_path_b":
                continue
            if r.get("method") == "path_b_softvote" and r.get("error"):
                name = r.get("image_name")
                if name and name not in seen:
                    seen.add(name)
                    failed.append(name)
    return failed


def load_labels(label_file: Path | None, label_key: str) -> dict[str, object]:
    if not label_file or not label_file.is_file():
        return {}
    with label_file.open(encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, dict):
        return {Path(k).stem: v for k, v in raw.items()}
    if isinstance(raw, list):
        out: dict[str, object] = {}
        for item in raw:
            fname = item.get("filename", "")
            if fname:
                out[Path(fname).stem] = item.get(label_key)
        return out
    return {}


def load_indie_preds(
    img_name: str,
    cls_model_configs: list[dict],
    cls_cache_dir: Path,
) -> list[ClsModelOutput]:
    preds: list[ClsModelOutput] = []
    for model_cfg in cls_model_configs:
        model_name = model_cfg.get("name", "")
        cache_path = cls_cache_dir / f"{model_name}.json"
        with cache_path.open(encoding="utf-8") as f:
            data = json.load(f)
        pred_dict = data["results"][img_name]
        preds.append(
            ClsModelOutput(
                model_name=pred_dict["model_name"],
                predictions=pred_dict["predictions"],
                top_class=pred_dict["top_class"],
                top_confidence=pred_dict["top_confidence"],
                requires_mask=pred_dict["requires_mask"],
                metadata=pred_dict.get("metadata", {}),
            )
        )
    return preds


def strip_cls_path_b_lines(routing_log: Path, image_names: set[str], backup: Path) -> int:
    if not routing_log.is_file():
        return 0
    shutil.copy2(routing_log, backup)
    kept: list[str] = []
    removed = 0
    with routing_log.open(encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            r = json.loads(s)
            if r.get("image_name") in image_names and r.get("task") == "cls_path_b":
                removed += 1
                continue
            kept.append(s)
    with routing_log.open("w", encoding="utf-8") as f:
        for s in kept:
            f.write(s + "\n")
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description="补跑 Path B 分类 LLM 失败病例")
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--images-file",
        help="可选：每行一个 image_name；默认从 routing_log 解析 path_b_softvote+error",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-eval", action="store_true", help="不刷新 metrics / comparison")
    args = parser.parse_args()

    config = load_config(args.config)
    out = Path(args.output_dir)
    routing_log = out / "routing_log.jsonl"
    results_path = out / "results.json"
    inter = out / "intermediate"
    cls_cache_dir = inter / "cls"

    if args.images_file:
        targets = [
            ln.strip()
            for ln in Path(args.images_file).read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
    else:
        targets = failed_path_b_images(routing_log)

    print(f"待补跑 Path B LLM: {len(targets)} 例")
    if not targets:
        print("无失败病例，退出")
        return 0
    if args.dry_run:
        for name in targets[:20]:
            print(f"  {name}")
        if len(targets) > 20:
            print(f"  ... 共 {len(targets)} 例")
        return 0

    llm_cfg = config["shared"]["agent_llm"]
    api_key = os.getenv(llm_cfg.get("api_key_env", "DASHSCOPE_API_KEY"), "").strip()
    if not api_key:
        print("✗ 未设置 API key")
        return 1

    pipe_cfg = config.get("pipeline", {})
    data_cfg = pipe_cfg.get("data", {})
    seg_cfg = config.get("segmentation", {})
    cls_cfg = config.get("classification", {})
    judge_cfg = config.get("radiomics_judge", {})

    target_set = set(targets)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = routing_log.with_suffix(f".jsonl.bak.{ts}")
    removed = strip_cls_path_b_lines(routing_log, target_set, backup)
    print(f"已备份 routing_log → {backup.name}，移除旧 cls_path_b 行: {removed}")

    shutil.copy2(results_path, results_path.with_suffix(f".json.bak.{ts}"))

    llm_client = build_llm_client(llm_cfg, api_key)
    judge = None
    if judge_cfg.get("enabled", False):
        judge = RadiomicsJudge(
            model_dir=judge_cfg["model_dir"],
            top_k_features=judge_cfg.get("top_k_features", 5),
            shap_reference_path=judge_cfg.get("shap_reference_path"),
            radiomics_params=judge_cfg.get("radiomics_params"),
        )

    routing_logger = build_routing_logger_from_config(config, out)
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
    pipeline = CascadePipeline(
        seg_agent=seg_agent,
        cls_agent=cls_agent,
        seg_registry=None,
        cls_registry=None,
        image_io=ImageIO(),
        config=config,
        device="cuda",
    )

    sel_names, sel_masks, seg_decisions = CascadePipeline._load_selected_masks_npz(
        inter / "selected_masks.npz"
    )
    sel_map: dict[str, dict] = {}
    for i, name in enumerate(sel_names):
        d = seg_decisions[i]
        sel_map[name] = {
            "mask": sel_masks[i],
            "decision": d,
            "consensus": d["consensus"],
            "anchor_class": d["anchor_class"],
        }

    autogluon_results: dict = {}
    ag_path = inter / "autogluon.json"
    if ag_path.is_file():
        with ag_path.open(encoding="utf-8") as f:
            autogluon_results = json.load(f)

    labels = load_labels(
        Path(data_cfg["label_file"]) if data_cfg.get("label_file") else None,
        data_cfg.get("label_key", "malignancy"),
    )
    center_lookup = load_center_lookup(pipe_cfg.get("center_manifest"))
    cls_model_configs = cls_cfg.get("models", [])
    voting_weights = pipeline._get_voting_weights()

    with results_path.open(encoding="utf-8") as f:
        results: list[dict] = json.load(f)
    by_name = {r["image_name"]: i for i, r in enumerate(results) if r.get("image_name")}

    from segmentation.agent import SegAgentDecision

    for idx, img_name in enumerate(targets):
        if img_name not in sel_map:
            print(f"  ✗ {img_name}: 无 selected_masks")
            continue
        if img_name not in by_name:
            print(f"  ✗ {img_name}: 不在 results.json")
            continue
        sel_info = sel_map[img_name]
        if sel_info["consensus"]:
            print(f"  ⏭ {img_name}: 已有分类共识，跳过")
            continue

        indie_preds = load_indie_preds(img_name, cls_model_configs, cls_cache_dir)
        seg_d = sel_info["decision"]
        seg_stub = SegAgentDecision(
            selected_model=seg_d["selected_model"],
            selected_mask=sel_info["mask"],
            confidence=seg_d["confidence"],
            reasoning=seg_d["reasoning"],
            all_predictions=seg_d["all_predictions"],
            classification_anchor=sel_info["anchor_class"],
            path=seg_d.get("path", "B"),
        )
        ag_dict = autogluon_results.get(img_name)
        autogluon_pred = None
        if ag_dict:
            autogluon_pred = ClsModelOutput(
                model_name=ag_dict["model_name"],
                predictions=ag_dict["predictions"],
                top_class=ag_dict["top_class"],
                top_confidence=ag_dict["top_confidence"],
                requires_mask=ag_dict["requires_mask"],
                metadata=ag_dict.get("metadata", {}),
            )

        cls_decision = cls_agent.resolve_path_b(
            indie_preds,
            autogluon_pred,
            seg_stub,
            voting_weights=voting_weights,
            image_name=img_name,
        )

        final_label = pipeline._label_to_binary(cls_decision.selected_class)
        if final_label is None:
            final_label = cls_decision.selected_class

        ri = by_name[img_name]
        old = results[ri]
        result = {
            "path": "B",
            "classification_consensus": False,
            "cls_decision": cls_decision.to_dict(),
            "final_label": final_label,
            "final_confidence": cls_decision.confidence,
            "image_name": img_name,
            "seg_decision": seg_d,
            "selected_mask_shape": old.get("selected_mask_shape")
            or list(sel_info["mask"].shape),
            "selected_mask_area": old.get("selected_mask_area")
            or int(sel_info["mask"].sum()),
        }
        img_stem = Path(img_name).stem
        if img_stem in labels:
            result["true_label"] = labels[img_stem]
        if "uncertainty" in old:
            result["uncertainty"] = old["uncertainty"]

        pipeline._enrich_result_record(
            result,
            img_name=img_name,
            indie_preds=indie_preds,
            seg_decision_dict=seg_d,
            consensus=False,
            final_confidence=float(result["final_confidence"]),
            llm_used_seg=True,
            llm_used_cls=True,
            center_lookup=center_lookup,
        )
        results[ri] = result
        status = "OK" if cls_decision.method == "path_b_llm" else f"降级({cls_decision.method})"
        print(f"  [{idx + 1}/{len(targets)}] {img_name}: {status}")

        if (idx + 1) % 10 == 0:
            with results_path.open("w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

    with results_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    ok = sum(
        1
        for name in targets
        if name in by_name
        and results[by_name[name]].get("cls_decision", {}).get("method") == "path_b_llm"
    )
    still_fail = len(targets) - ok
    print(f"\n完成: path_b_llm 成功 {ok}/{len(targets)}，仍降级/失败 {still_fail}")

    if args.skip_eval:
        return 0 if still_fail == 0 else 2

    from pipeline.evaluate import evaluate_pipeline
    from pipeline.compare_models import compare_models

    evaluate_pipeline(
        results,
        out,
        image_io=ImageIO(),
        gt_mask_dir=data_cfg.get("gt_mask_dir"),
    )
    if data_cfg.get("gt_mask_dir") and data_cfg.get("label_file"):
        compare_models(
            output_dir=str(out),
            gt_mask_dir=data_cfg["gt_mask_dir"],
            label_file=data_cfg["label_file"],
            label_key=data_cfg.get("label_key", "malignancy"),
        )
    return 0 if still_fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
