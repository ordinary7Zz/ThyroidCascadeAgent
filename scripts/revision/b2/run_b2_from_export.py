#!/usr/bin/env python3
"""B2 metrics from b2_exports/<model>/<cohort>/predictions.jsonl (+ manifest.json)."""

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

import argparse
import json
import sys

import repo_path

_REPO = repo_path.find_repo_root()
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

# Load sibling module without package prefix
_spec = importlib.util.spec_from_file_location(
    "run_b2_cluster_metrics", _REPO / "scripts" / "revision" / "b2" / "run_b2_cluster_metrics.py"
)
_b2 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_b2)

WORKSPACE_ROOT = _REPO.parent
DEFAULT_EXPORTS_ROOT = WORKSPACE_ROOT / "b2_exports"
MAP_DIR = _REPO / "docs/revision/b2/cluster_maps"
TABLE_DIR = _REPO / "docs/revision/b2/tables"

COHORT_CLUSTER_MAP: dict[str, str] = {
    "thyroidxl": "thyroidxl_test.json",
    "zjh8k": "zjh8k.json",
}
PATIENT_LEVEL_COHORTS = frozenset({"thyroidxl", "zjh8k"})


def base_cohort_id(cohort_id: str) -> str:
    """Map export dir id → cohorts.yaml key (cluster maps, patient-level flags)."""
    for suffix in ("_seg_nodule", "_cls_bm", "_seg", "_cls"):
        if cohort_id.endswith(suffix):
            return cohort_id[: -len(suffix)]
    return cohort_id


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def resolve_cluster_map(cohort_id: str, manifest: dict) -> dict[str, str] | None:
    if manifest.get("cluster_map_file"):
        p = Path(manifest["cluster_map_file"])
        if not p.is_absolute():
            p = _REPO / p
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    fname = COHORT_CLUSTER_MAP.get(cohort_id)
    if fname:
        p = MAP_DIR / fname
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    return None


def process_export_dir(
    export_dir: Path,
    n_bootstrap: int,
    seed: int,
    out_path: Path | None,
    exclude_images: Path | None = None,
) -> dict:
    manifest_path = export_dir / "manifest.json"
    pred_path = export_dir / "predictions.jsonl"
    if not pred_path.exists():
        raise FileNotFoundError(f"Missing {pred_path}")

    manifest = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    parts = export_dir.parts
    cohort_id = manifest.get("cohort_id") or (parts[-1] if len(parts) >= 1 else "unknown")
    model_id = manifest.get("model_id") or (parts[-2] if len(parts) >= 2 else "unknown")
    task = manifest.get("task", "").lower()

    records = load_jsonl(pred_path)
    exclude: set[str] = set()
    if exclude_images is not None:
        exclude = _b2.load_exclude_images(exclude_images)
        n_before = len(records)
        records = [
            r
            for r in records
            if not _b2.image_is_excluded(str(r.get("image_name", "")), exclude)
        ]
        print(f"exclude-images: {len(exclude)} listed, records {n_before} -> {len(records)}")

    cohort_base = base_cohort_id(str(cohort_id))
    cluster_map = resolve_cluster_map(cohort_base, manifest)
    patient_level = bool(manifest.get("patient_level")) or cohort_base in PATIENT_LEVEL_COHORTS

    if not task:
        if records and "score_malignant" in records[0]:
            task = "classification"
        elif records and "dice" in records[0]:
            task = "segmentation"
        else:
            raise ValueError(f"Cannot infer task for {export_dir}; set manifest.task")

    out: dict = {
        "source": "b2_exports",
        "export_dir": str(export_dir),
        "model_id": model_id,
        "cohort_id": cohort_id,
        "manifest": str(manifest_path) if manifest_path.exists() else None,
        "predictions": str(pred_path),
        "n_records": len(records),
        "cluster_map": (
            str(MAP_DIR / COHORT_CLUSTER_MAP[cohort_base])
            if cohort_base in COHORT_CLUSTER_MAP
            else None
        ),
        "bootstrap": {"n": n_bootstrap, "seed": seed},
    }
    if exclude:
        out["exclusion"] = {
            "exclude_images": str(exclude_images),
            "n_listed": len(exclude),
            "criterion": "image_name in exclude list (sensitivity analysis)",
        }

    if task == "classification":
        results = _b2.classification_results_from_jsonl(records)
        out["classification"] = _b2.build_classification_report(
            results, cluster_map, n_bootstrap, seed, patient_level
        )
    elif task == "segmentation":
        if "dice" in records[0]:
            rows = _b2.seg_dice_rows_from_jsonl(records, cluster_map)
            out["segmentation"] = _b2.build_segmentation_report_from_dice_rows(
                rows, cluster_map, n_bootstrap, seed, patient_level
            )
        else:
            raise NotImplementedError(
                "Segmentation export must include 'dice' per line, or use pipeline selected_masks path"
            )
    else:
        raise ValueError(f"Unknown task: {task}")

    if out_path is None:
        TABLE_DIR.mkdir(parents=True, exist_ok=True)
        safe_model = str(model_id).replace("/", "_")
        if exclude:
            out_path = TABLE_DIR / f"baseline_{safe_model}_{cohort_id}_b2_excl_train_dup.json"
        else:
            out_path = TABLE_DIR / f"baseline_{safe_model}_{cohort_id}_b2.json"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["output"] = str(out_path)
    return out


def scan_exports_root(root: Path) -> list[Path]:
    found: list[Path] = []
    if not root.exists():
        return found
    for model_dir in sorted(root.iterdir()):
        if not model_dir.is_dir() or model_dir.name.startswith(("_", ".")):
            continue
        for cohort_dir in sorted(model_dir.iterdir()):
            if cohort_dir.is_dir() and (cohort_dir / "predictions.jsonl").exists():
                found.append(cohort_dir)
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description="B2 from b2_exports predictions.jsonl")
    parser.add_argument(
        "--export-dir",
        type=Path,
        help="Single export dir: b2_exports/<model>/<cohort>/",
    )
    parser.add_argument(
        "--exports-root",
        type=Path,
        default=None,
        help=f"Scan all cohorts under root (default: {DEFAULT_EXPORTS_ROOT})",
    )
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--scan-all", action="store_true", help="Process every */*/predictions.jsonl under exports-root")
    parser.add_argument(
        "--exclude-images",
        type=Path,
        default=None,
        help="ZJH sensitivity: manifest/txt of image_name to drop before metrics",
    )
    parser.add_argument(
        "--cohort-substr",
        type=str,
        default=None,
        help="With --scan-all: only export dirs whose cohort folder name contains this substring",
    )
    args = parser.parse_args()

    nb = int(__import__("os").environ.get("B2_N_BOOTSTRAP", str(args.n_bootstrap)))
    seed = int(__import__("os").environ.get("B2_SEED", str(args.seed)))

    if args.scan_all or (args.export_dir is None and not args.exports_root):
        root = args.exports_root or DEFAULT_EXPORTS_ROOT
        dirs = scan_exports_root(root)
        if args.cohort_substr:
            dirs = [d for d in dirs if args.cohort_substr in d.name]
        if not dirs:
            print(f"No exports found under {root}")
            print("See ThyroidAgent/b2_exports/README.md")
            sys.exit(0)
        TABLE_DIR.mkdir(parents=True, exist_ok=True)
        if not args.exclude_images:
            for stale in TABLE_DIR.glob("baseline_*_b2.json"):
                if "_excl_train_dup" not in stale.name:
                    stale.unlink()
        index = []
        for d in dirs:
            print(f"-------- {d.relative_to(root)} --------")
            summary = process_export_dir(d, nb, seed, None, args.exclude_images)
            print(f"Wrote {summary['output']}")
            index.append(
                {
                    "model_id": summary["model_id"],
                    "cohort_id": summary["cohort_id"],
                    "output": summary["output"],
                    "n_records": summary["n_records"],
                }
            )
        idx_name = "BASELINES_INDEX_excl_train_dup.json" if args.exclude_images else "BASELINES_INDEX.json"
        idx_path = TABLE_DIR / idx_name
        idx_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nIndex: {idx_path} ({len(index)} exports)")
        return

    if args.export_dir is None:
        parser.error("Provide --export-dir or --scan-all")

    summary = process_export_dir(args.export_dir, nb, seed, args.out, args.exclude_images)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\nWrote {summary['output']}")


if __name__ == "__main__":
    main()

