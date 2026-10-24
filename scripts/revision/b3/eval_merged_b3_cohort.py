#!/usr/bin/env python3
"""合并后的 B3 全队列：对每 mode 目录跑 evaluate_pipeline → b3_metrics.json，可选 ablation_summary。

  python scripts/revision/b3/eval_merged_b3_cohort.py \\
    --config config/b3/zjh8k.yaml \\
    --root output/ablation/b3/zjh8k

  python scripts/revision/b3/eval_merged_b3_cohort.py \\
    --config config/b3/rjh7k.yaml \\
    --root output/ablation/b3/rjh7k
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
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

import repo_path
import yaml

ROOT = repo_path.install()

from pipeline.revision.b3.ablation_metrics import build_b3_metrics, save_b3_metrics
from pipeline.evaluate import evaluate_pipeline
from shared.image_io import ImageIO

WAVE1_MODES = (
    "soft_voting",
    "majority",
    "max_confidence",
    "best_single",
    "oracle",
    "static_rule",
)


def _load_results(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return data.get("results", data)


def main() -> int:
    parser = argparse.ArgumentParser(description="合并 B3 目录后生成 b3_metrics.json")
    parser.add_argument("--config", required=True, help="config/b3/<cohort>.yaml")
    parser.add_argument("--root", required=True, help="合并输出根目录，含各 mode 子目录")
    parser.add_argument(
        "--modes",
        default=",".join(WAVE1_MODES),
        help="逗号分隔 mode 名",
    )
    parser.add_argument("--summarize", action="store_true", default=True)
    parser.add_argument("--no-summarize", action="store_false", dest="summarize")
    args = parser.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = ROOT / cfg_path
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    data_cfg = cfg.get("pipeline", {}).get("data", {}) or {}
    gt_mask_dir = data_cfg.get("gt_mask_dir")
    ab = cfg.get("pipeline", {}).get("ablation", {}) or {}
    default_task = ab.get("task") or "both"

    out_root = Path(args.root)
    if not out_root.is_absolute():
        out_root = ROOT / out_root

    modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    image_io = ImageIO()

    for mode in modes:
        mode_dir = out_root / mode
        results_path = mode_dir / "results.json"
        if not results_path.is_file():
            print(f"跳过 {mode}: 无 {results_path}", file=sys.stderr)
            continue
        results = _load_results(results_path)
        meta_path = mode_dir / "ablation_run.json"
        if meta_path.is_file():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        else:
            meta = {}
        seg_mode = meta.get("seg_mode") or meta.get("routing_mode_seg") or mode
        cls_mode = meta.get("cls_mode") or meta.get("routing_mode_cls") or mode
        task = meta.get("task") or default_task

        print(f"\n>>> 评估 {mode} (n={len(results)}, task={task})")
        metrics = evaluate_pipeline(
            results,
            str(mode_dir),
            image_io=image_io,
            gt_mask_dir=gt_mask_dir,
        )
        b3 = build_b3_metrics(
            results,
            metrics,
            routing_mode=mode,
            task=task,
            seg_mode=seg_mode,
            cls_mode=cls_mode,
        )
        save_b3_metrics(mode_dir, b3)
        print(f"  ✓ {mode_dir / 'b3_metrics.json'}")

    if args.summarize:
        ref = out_root / modes[0] / "intermediate_manifest.json"
        cmd = [
            sys.executable,
            "-m",
            "pipeline.revision.b3.ablation_summary",
            "--root",
            str(out_root),
        ]
        if ref.is_file():
            cmd.extend(["--reference-manifest", str(ref)])
        print("\n汇总:", " ".join(cmd))
        subprocess.check_call(cmd, cwd=str(ROOT))

    print(f"\n完成: {out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
