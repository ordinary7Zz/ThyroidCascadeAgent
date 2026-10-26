#!/usr/bin/env python3
"""对已完成的 B3 mode 目录：用 B2 口径 cluster bootstrap 重算 b3_metrics.json 中的 CI。

不重跑路由；只读 results.json + intermediate/selected_masks.npz。

  python scripts/revision/b3/recompute_b3_cluster_ci.py --config config/revision/b3/tn3k.yaml
  python scripts/revision/b3/recompute_b3_cluster_ci.py --all-wave1 --summarize
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
from pipeline.revision.b3.cluster_ci import (
    cohort_id_from_config_path,
    evaluate_metrics_cluster,
    patch_b3_classification_from_cluster,
)

WAVE1_COHORTS = (
    "tn3k",
    "tn5k",
    "thyroidxl",
    "pktn",
    "ddti_seg",
    "ddti_cls",
    "zjh8k",
    "rjh7k",
)
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


def recompute_cohort(cfg_path: Path, root: Path, modes: tuple[str, ...], summarize: bool) -> None:
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    data_cfg = cfg.get("pipeline", {}).get("data", {}) or {}
    gt_mask_dir = data_cfg.get("gt_mask_dir")
    if not gt_mask_dir:
        raise SystemExit(f"{cfg_path}: pipeline.data.gt_mask_dir 缺失")
    ab = cfg.get("pipeline", {}).get("ablation", {}) or {}
    default_task = ab.get("task") or "both"
    cohort_id = cohort_id_from_config_path(cfg_path)

    if not root.is_absolute():
        root = ROOT / root

    for mode in modes:
        mode_dir = root / mode
        results_path = mode_dir / "results.json"
        if not results_path.is_file():
            print(f"跳过 {cohort_id}/{mode}: 无 results.json", file=sys.stderr)
            continue
        results = _load_results(results_path)
        meta_path = mode_dir / "ablation_run.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else {}
        seg_mode = meta.get("seg_mode") or meta.get("routing_mode_seg") or mode
        cls_mode = meta.get("cls_mode") or meta.get("routing_mode_cls") or mode
        task = meta.get("task") or default_task

        metrics, boot_meta = evaluate_metrics_cluster(
            results, mode_dir, gt_mask_dir, cohort_id
        )
        cls_all, cls_pb = patch_b3_classification_from_cluster(results, cohort_id)
        b3 = build_b3_metrics(
            results,
            metrics,
            routing_mode=mode,
            task=task,
            seg_mode=seg_mode,
            cls_mode=cls_mode,
        )
        if cls_all:
            b3["classification"] = cls_all
        if cls_pb:
            b3["classification_path_b"] = cls_pb
            b3["metrics_path_b_only"] = cls_pb
        b3["bootstrap"] = boot_meta
        save_b3_metrics(mode_dir, b3)
        print(f"✓ {cohort_id}/{mode} cluster CI (seg clusters={boot_meta.get('n_clusters_segmentation')})")

    if summarize and modes:
        ref = root / modes[0] / "intermediate_manifest.json"
        cmd = [
            sys.executable,
            "-m",
            "pipeline.revision.b3.ablation_summary",
            "--root",
            str(root),
        ]
        if ref.is_file():
            cmd.extend(["--reference-manifest", str(ref)])
        subprocess.check_call(cmd, cwd=str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="B3 metrics: 重算 cluster-bootstrap CI")
    parser.add_argument("--config", type=Path, help="config/revision/b3/<cohort>.yaml")
    parser.add_argument("--root", type=Path, help="默认 output/ablation/b3/<cohort>")
    parser.add_argument("--modes", default=",".join(WAVE1_MODES))
    parser.add_argument("--all-wave1", action="store_true", help="重算 WAVE1_COHORTS")
    parser.add_argument("--summarize", action="store_true", help="各 cohort 后跑 ablation_summary")
    args = parser.parse_args()

    modes = tuple(m.strip() for m in args.modes.split(",") if m.strip())

    if args.all_wave1:
        for cid in WAVE1_COHORTS:
            cfg = ROOT / "config" / "b3" / f"{cid}.yaml"
            if not cfg.is_file():
                print(f"跳过 {cid}: 无 {cfg}", file=sys.stderr)
                continue
            root = args.root or (ROOT / "output" / "ablation" / "b3" / cid)
            recompute_cohort(cfg, root, modes, args.summarize)
        return 0

    if not args.config:
        parser.error("需要 --config 或 --all-wave1")
    cfg_path = args.config if args.config.is_absolute() else ROOT / args.config
    cohort_id = cohort_id_from_config_path(cfg_path)
    root = args.root or (ROOT / "output" / "ablation" / "b3" / cohort_id)
    recompute_cohort(cfg_path, root, modes, args.summarize)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
