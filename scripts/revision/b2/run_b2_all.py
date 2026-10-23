#!/usr/bin/env python3
"""One-shot B2: read docs/revision/b2/cohort_tasks.yaml and run per-cohort tasks."""

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
import subprocess
import sys
from pathlib import Path

import yaml

import repo_path
ROOT = repo_path.find_repo_root()


def main() -> None:
    manifest = ROOT / "docs/revision/b2/cohort_tasks.yaml"
    cfg = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    data_root = Path(cfg.get("data_root", "/mnt/wangbd8/workspace/DataSets/ThyroidAgent"))
    table_dir = ROOT / "docs/revision/b2/tables"
    map_dir = ROOT / "docs/revision/b2/cluster_maps"
    b1_dir = ROOT / "docs/revision/b1/tables"
    nb = int(__import__("os").environ.get("B2_N_BOOTSTRAP", "1000"))
    seed = int(__import__("os").environ.get("B2_SEED", "42"))

    print("========== [1/3] Cluster maps (ZJH + ThyroidXL) ==========")
    subprocess.check_call(
        [sys.executable, str(ROOT / "scripts/revision/b2/build_cluster_maps.py"), "--out-dir", str(map_dir)],
        cwd=ROOT,
    )

    table_dir.mkdir(parents=True, exist_ok=True)
    b1_dir.mkdir(parents=True, exist_ok=True)

    print("\n========== [2/3] B2 per cohort (task-aware) ==========")
    for cohort in cfg["cohorts"]:
        name = cohort["name"]
        tasks = cohort["tasks"]
        results = ROOT / cohort["results"]
        if not results.exists():
            print(f"SKIP {name}: missing {results}")
            continue

        cluster_map_path = cohort.get("cluster_map")
        cluster_map = ROOT / cluster_map_path if cluster_map_path else None
        patient_level = bool(cohort.get("patient_level", False))
        pipeline_dir = ROOT / cohort["pipeline_dir"] if cohort.get("pipeline_dir") else results.parent
        gt_rel = cohort.get("gt_mask_dir")
        gt_mask_dir = (data_root / gt_rel) if gt_rel else None

        out_path = table_dir / f"{name}_b2.json"
        cmd = [
            sys.executable,
            str(ROOT / "scripts/revision/b2/run_b2_cluster_metrics.py"),
            "--results",
            str(results),
            "--out",
            str(out_path),
            "--n-bootstrap",
            str(nb),
            "--seed",
            str(seed),
        ]
        if cluster_map and cluster_map.exists():
            cmd.extend(["--cluster-map", str(cluster_map)])
        if patient_level:
            cmd.append("--patient-level")

        if "classification" in tasks and "segmentation" in tasks:
            cmd.extend(["--task", "both"])
            if gt_mask_dir is None:
                print(f"SKIP {name}: both tasks but no gt_mask_dir")
                continue
            cmd.extend(["--pipeline-dir", str(pipeline_dir), "--gt-mask-dir", str(gt_mask_dir)])
        elif "classification" in tasks:
            cmd.extend(["--task", "classification"])
        elif "segmentation" in tasks:
            cmd.extend(["--task", "segmentation", "--pipeline-dir", str(pipeline_dir)])
            if gt_mask_dir is None:
                print(f"SKIP {name}: segmentation but no gt_mask_dir")
                continue
            cmd.extend(["--gt-mask-dir", str(gt_mask_dir)])
        else:
            print(f"SKIP {name}: no tasks listed")
            continue

        print(f"-------- {name} tasks={tasks} --------")
        subprocess.check_call(cmd, cwd=ROOT)

    print("\n========== [3/3] B1 train vs test overlap ==========")
    subprocess.check_call(
        [
            sys.executable,
            str(ROOT / "scripts/revision/b1/audit_train_test_overlap.py"),
            "--out",
            str(b1_dir / "train_test_overlap.json"),
        ],
        cwd=ROOT,
    )

    print("\nDone.")
    print(f"  Tables: {table_dir}/")
    print(f"  Manifest: {manifest}")


if __name__ == "__main__":
    main()

import importlib.util
from pathlib import Path


