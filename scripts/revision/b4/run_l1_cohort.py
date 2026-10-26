#!/usr/bin/env python3
"""B4 L1：本仓库 run_pipeline（单 all_datasets 专家）+ ingest_l1_metrics。

示例:
  python scripts/revision/b4/run_l1_cohort.py --cohort sample --max-images 5
  python scripts/revision/b4/run_l1_cohort.py --cohort tn3k
  python scripts/revision/b4/run_l1_cohort.py --config config/revision/b4/l1/tn3k.yaml --skip-pipeline  # 仅 ingest
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
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
import shutil

import repo_path
import yaml

ROOT = repo_path.install()


def _load_config(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _dataset_id(cfg: dict, fallback: str) -> str:
    b4 = (cfg.get("pipeline") or {}).get("ablation_b4") or {}
    return b4.get("dataset_id") or fallback


def _output_dir(cfg: dict) -> Path:
    out = (cfg.get("pipeline") or {}).get("output", {}).get("output_dir")
    if not out:
        raise ValueError("config 缺少 pipeline.output.output_dir")
    return Path(out)


def _write_provenance(cohort_id: str, pipeline_dir: Path, cfg_path: Path) -> Path:
    prov = {
        "training": "stacked OpenThyroid dataset_3 (cls) / dataset_4 (seg); all_datasets joint DINO",
        "seg_checkpoint": "../Segmentation_Agent/weights/all_datasets/dino_unet_train_all_datasets_epoch_40.pth",
        "cls_checkpoint": "../Classification_Agent/weights/all_datasets/dino_unet_train_all_datasets_epoch_40.pth",
        "eval_run_dir": str(pipeline_dir),
        "eval_config": str(cfg_path),
        "eval_protocol": "run_pipeline.py; single seg+cls; enable_agent=false; radiomics_judge=false",
        "bootstrap": "evaluate_pipeline image-level n=1000 seed=42",
    }
    path = pipeline_dir / "l1_provenance.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(prov, f, ensure_ascii=False, indent=2)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="B4 L1 单专家 pipeline + ingest")
    parser.add_argument("--cohort", default=None, help="config/revision/b4/l1/<cohort>.yaml")
    parser.add_argument("--config", default=None, help="显式 L1 配置路径")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--max-images", type=int, default=None, help="覆盖 pipeline.data.max_images（冒烟）")
    parser.add_argument("--skip-pipeline", action="store_true")
    parser.add_argument("--skip-ingest", action="store_true")
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="删除 pipeline.output.output_dir 后全量重跑（避免 --max-images 残留缓存）",
    )
    parser.add_argument(
        "--artifacts-out",
        default=None,
        help="默认 artifacts/b4_l1_<cohort>.json",
    )
    args = parser.parse_args()

    if args.config:
        cfg_path = Path(args.config)
        cohort = args.cohort or cfg_path.stem
    elif args.cohort:
        cohort = args.cohort
        cfg_path = ROOT / "config" / "revision" / "b4" / "l1" / f"{cohort}.yaml"
    else:
        parser.error("须指定 --cohort 或 --config")

    if not cfg_path.is_file():
        print(f"缺少 {cfg_path}，请先: python scripts/generate_ablation_configs.py", file=sys.stderr)
        sys.exit(1)

    cfg = _load_config(cfg_path)
    dataset_id = _dataset_id(cfg, cohort)
    pipeline_dir = _output_dir(cfg)
    artifacts_out = Path(args.artifacts_out or ROOT / "artifacts" / f"b4_l1_{dataset_id}.json")

    config_for_run = cfg_path
    tmp_cfg: Path | None = None
    if args.max_images is not None:
        cfg = dict(cfg)
        pipe = cfg.setdefault("pipeline", {})
        data = pipe.setdefault("data", {})
        data["max_images"] = args.max_images
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", prefix=f"l1_{cohort}_", delete=False, encoding="utf-8"
        )
        yaml.dump(cfg, tmp, allow_unicode=True, sort_keys=False, default_flow_style=False)
        tmp.close()
        tmp_cfg = Path(tmp.name)
        config_for_run = tmp_cfg

    try:
        if args.fresh and pipeline_dir.exists():
            print(f"✓ --fresh: 删除 {pipeline_dir}")
            shutil.rmtree(pipeline_dir)

        if not args.skip_pipeline:
            cmd = [
                sys.executable,
                str(ROOT / "run_pipeline.py"),
                "--config",
                str(config_for_run),
                "--device",
                args.device,
            ]
            print("→", " ".join(cmd))
            subprocess.run(cmd, cwd=str(ROOT), check=True)
            _write_provenance(dataset_id, pipeline_dir, cfg_path)

        if not args.skip_ingest:
            prov = pipeline_dir / "l1_provenance.json"
            ingest = [
                sys.executable,
                str(ROOT / "scripts" / "revision" / "b4" / "ingest_l1_metrics.py"),
                "--dataset-id",
                dataset_id,
                "--config",
                str(cfg_path),
                "--pipeline-dir",
                str(pipeline_dir),
                "--out",
                str(artifacts_out),
            ]
            if prov.is_file():
                ingest.extend(["--provenance-json", str(prov)])
            print("→", " ".join(ingest))
            subprocess.run(ingest, cwd=str(ROOT), check=True)

        print(f"\n✓ L1 完成: {pipeline_dir}")
        print(f"  指标: {artifacts_out}")
        print(f"  汇总: python scripts/revision/b4/build_b4_tables.py --config config/revision/b4/{dataset_id}.yaml")
    finally:
        if tmp_cfg and tmp_cfg.is_file():
            tmp_cfg.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
