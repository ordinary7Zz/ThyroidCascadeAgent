#!/usr/bin/env python3
"""将 L1 单专家评测结果写入 artifacts/b4_l1_<cohort>.json（B4 主表 L1 行）。

用法 1 — 本仓库 pipeline 输出（results.json + selected_masks，与 evaluate_pipeline 一致）:
  python scripts/revision/b4/ingest_l1_metrics.py \\
    --dataset-id tn3k \\
    --config config/revision/b3/tn3k.yaml \\
    --pipeline-dir output/ablation/l1/tn3k/run1 \\
    --out artifacts/b4_l1_tn3k.json

用法 2 — 已有 metrics.json（外仓或手跑 evaluate）:
  python scripts/revision/b4/ingest_l1_metrics.py \\
    --dataset-id tn3k \\
    --metrics-json output/ablation/l1/tn3k/run1/metrics.json \\
    --results-json output/ablation/l1/tn3k/run1/results.json \\
    --out artifacts/b4_l1_tn3k.json

用法 3 — 合并手写块（外仓字段已对齐 schema）:
  python scripts/revision/b4/ingest_l1_metrics.py \\
    --dataset-id tn3k \\
    --patch-json docs/revision/b4/examples/l1_patch_tn3k.json \\
    --out artifacts/b4_l1_tn3k.json

字段说明: docs/revision/b4/L1_METRICS_SCHEMA.md
"""

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

import argparse
import json
import sys

import repo_path
import yaml

ROOT = repo_path.install()

from pipeline.evaluate import evaluate_pipeline
from pipeline.revision.b4.l1_metrics import (
    build_l1_document,
    build_l1_from_evaluate,
    save_l1_document,
    validate_l1_document,
)
from shared.image_io import ImageIO


def _load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_results(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    if isinstance(data, list):
        return data
    raise ValueError(f"无法解析 results: {path}")


def _gt_mask_dir_from_config(cfg: dict) -> str | None:
    data = (cfg.get("pipeline") or {}).get("data") or {}
    return data.get("gt_mask_dir")


def main() -> None:
    parser = argparse.ArgumentParser(description="B4 L1 指标写入 artifacts/b4_l1_<cohort>.json")
    parser.add_argument("--dataset-id", required=True, help="与 config/revision/b4/<id>.yaml 的 dataset_id 一致")
    parser.add_argument(
        "--out",
        default=None,
        help="输出路径（默认 artifacts/b4_l1_<dataset-id>.json）",
    )
    parser.add_argument("--config", default=None, help="B3/测试队列 yaml（取 gt_mask_dir）")
    parser.add_argument("--pipeline-dir", default=None, help="含 results.json 的 L1 跑数目录")
    parser.add_argument("--metrics-json", default=None, help="已有 evaluate metrics.json")
    parser.add_argument("--results-json", default=None, help="用于统计分类 n；默认 pipeline-dir/results.json")
    parser.add_argument("--patch-json", default=None, help="与 evaluate 结果合并的 L1 片段（provenance 等）")
    parser.add_argument("--provenance-json", default=None, help='如 {"seg_checkpoint":"...","cls_checkpoint":"..."}')
    parser.add_argument("--note", default=None)
    parser.add_argument("--validate-only", action="store_true", help="只校验 --out 或 patch 后不写盘")
    parser.add_argument("--quiet-eval", action="store_true", help="evaluate_pipeline 少打印")
    args = parser.parse_args()

    out_path = Path(args.out or ROOT / "artifacts" / f"b4_l1_{args.dataset_id}.json")

    provenance = None
    if args.provenance_json:
        with open(args.provenance_json, "r", encoding="utf-8") as f:
            provenance = json.load(f)

    patch: dict = {}
    if args.patch_json:
        with open(args.patch_json, "r", encoding="utf-8") as f:
            patch = json.load(f)

    doc: dict | None = None

    if args.pipeline_dir:
        pipe_dir = Path(args.pipeline_dir)
        results_path = pipe_dir / "results.json"
        if not results_path.is_file():
            parser.error(f"缺少 {results_path}")
        results = _load_results(results_path)
        cfg = _load_yaml(Path(args.config)) if args.config else {}
        gt_mask_dir = _gt_mask_dir_from_config(cfg) if cfg else None
        if not args.quiet_eval:
            metrics = evaluate_pipeline(
                results,
                str(pipe_dir),
                image_io=ImageIO(),
                gt_mask_dir=gt_mask_dir,
            )
        else:
            import io
            from contextlib import redirect_stdout

            with redirect_stdout(io.StringIO()):
                metrics = evaluate_pipeline(
                    results,
                    str(pipe_dir),
                    image_io=ImageIO(),
                    gt_mask_dir=gt_mask_dir,
                )
        if provenance is None and patch.get("provenance"):
            provenance = patch["provenance"]
        doc = build_l1_from_evaluate(
            dataset_id=args.dataset_id,
            evaluate_metrics=metrics,
            results=results,
            provenance=provenance,
            note=args.note or patch.get("note"),
        )
    elif args.metrics_json:
        with open(args.metrics_json, "r", encoding="utf-8") as f:
            metrics = json.load(f)
        results = None
        rpath = args.results_json
        if rpath:
            results = _load_results(Path(rpath))
        elif args.pipeline_dir:
            results = _load_results(Path(args.pipeline_dir) / "results.json")
        doc = build_l1_from_evaluate(
            dataset_id=args.dataset_id,
            evaluate_metrics=metrics,
            results=results,
            provenance=provenance or patch.get("provenance"),
            note=args.note or patch.get("note"),
        )
    elif args.patch_json:
        doc = build_l1_document(
            dataset_id=args.dataset_id,
            segmentation=patch.get("segmentation"),
            classification=patch.get("classification"),
            classification_path_b=patch.get("classification_path_b"),
            provenance=provenance or patch.get("provenance"),
            note=args.note or patch.get("note"),
        )
    else:
        parser.error("须指定 --pipeline-dir、--metrics-json 或 --patch-json 之一")

    if patch:
        if patch.get("note"):
            doc["note"] = patch["note"]
        if patch.get("provenance"):
            doc["provenance"] = {**(doc.get("provenance") or {}), **patch["provenance"]}
        for key in ("segmentation", "classification", "classification_path_b"):
            if patch.get(key):
                doc[key] = patch[key]

    errs = validate_l1_document(doc)
    if errs:
        print("校验失败:", "; ".join(errs), file=sys.stderr)
        sys.exit(1)

    if args.validate_only:
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        return

    save_l1_document(doc, out_path)
    print(f"✓ L1 指标已写入 {out_path}")
    print(f"  下一步: 确认 config/revision/b4/{args.dataset_id}.yaml 的 l1_metrics 指向该文件，然后")
    print(f"  python scripts/revision/b4/build_b4_tables.py --config config/revision/b4/{args.dataset_id}.yaml")


if __name__ == "__main__":
    main()
