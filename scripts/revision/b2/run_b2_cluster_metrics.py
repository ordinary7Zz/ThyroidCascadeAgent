#!/usr/bin/env python3
"""B2: cluster-bootstrap CIs (classification and/or segmentation)."""

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
from collections import defaultdict
from pathlib import Path
from typing import Optional

import numpy as np

import repo_path
_REPO = repo_path.find_repo_root()
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from shared.image_io import ImageIO


def _label_to_binary(label) -> Optional[int]:
    if isinstance(label, (int, float)):
        return int(label)
    if isinstance(label, str):
        if label in ("恶性", "malignant", "M", "1", "1.0"):
            return 1
        if label in ("良性", "benign", "B", "0", "0.0"):
            return 0
    return None


def _score_malignant(r: dict) -> Optional[float]:
    if "true_label" not in r or "final_label" not in r:
        return None
    pred_label = r["final_label"]
    confidence = float(r.get("final_confidence", 0.5))
    pred_binary = _label_to_binary(pred_label) if isinstance(pred_label, str) else pred_label
    if pred_binary is None:
        return None
    return confidence if pred_binary == 1 else 1.0 - confidence


def _rows_from_results(results: list[dict], cluster_map: dict[str, str] | None) -> list[dict]:
    rows = []
    for r in results:
        true_binary = _label_to_binary(r.get("true_label"))
        score = _score_malignant(r)
        if true_binary is None or score is None:
            continue
        img = r.get("image_name", "")
        cid = (cluster_map or {}).get(img, img)
        rows.append(
            {
                "image_name": img,
                "cluster_id": cid,
                "y_true": true_binary,
                "y_score": score,
            }
        )
    return rows


def _aggregate_patient_level(rows: list[dict]) -> list[dict]:
    by: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by[row["cluster_id"]].append(row)
    out = []
    for cid, group in by.items():
        y_true = max(x["y_true"] for x in group)
        y_score = float(np.mean([x["y_score"] for x in group]))
        out.append({"cluster_id": cid, "y_true": y_true, "y_score": y_score, "n_images": len(group)})
    return out


def _cluster_bootstrap_auc(
    rows: list[dict],
    n_bootstrap: int = 1000,
    seed: int = 42,
    use_patient_aggregate: bool = False,
) -> tuple[float, float, float, int]:
    from sklearn.metrics import roc_auc_score

    if use_patient_aggregate:
        units = _aggregate_patient_level(rows)
        cluster_key = "cluster_id"
    else:
        units = rows
        cluster_key = "cluster_id"

    if len(units) < 2:
        return float("nan"), float("nan"), float("nan"), len(units)

    y_true = np.array([u["y_true"] for u in units])
    y_score = np.array([u["y_score"] for u in units])
    if len(set(y_true)) < 2:
        return float("nan"), float("nan"), float("nan"), len(units)

    point = float(roc_auc_score(y_true, y_score))

    if use_patient_aggregate:
        clusters = units
    else:
        by_c: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            by_c[row[cluster_key]].append(row)
        clusters = [{"cluster_id": c, "rows": rs} for c, rs in by_c.items()]

    rng = np.random.RandomState(seed)
    n_c = len(clusters)
    boot = []
    for _ in range(n_bootstrap):
        idx = rng.randint(0, n_c, size=n_c)
        if use_patient_aggregate:
            sample_units = [clusters[i] for i in idx]
            yt = np.array([u["y_true"] for u in sample_units])
            ys = np.array([u["y_score"] for u in sample_units])
        else:
            pooled = []
            for i in idx:
                pooled.extend(clusters[i]["rows"])
            yt = np.array([x["y_true"] for x in pooled])
            ys = np.array([x["y_score"] for x in pooled])
        if len(set(yt)) < 2:
            continue
        try:
            boot.append(roc_auc_score(yt, ys))
        except ValueError:
            continue

    if not boot:
        return point, float("nan"), float("nan"), n_c

    boot = np.array(boot)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return point, float(lo), float(hi), n_c


def _cluster_bootstrap_auprc(
    rows: list[dict],
    n_bootstrap: int = 1000,
    seed: int = 42,
    use_patient_aggregate: bool = False,
) -> tuple[float, float, float]:
    from sklearn.metrics import average_precision_score

    if use_patient_aggregate:
        units = _aggregate_patient_level(rows)
    else:
        units = rows

    y_true = np.array([u["y_true"] for u in units])
    y_score = np.array([u["y_score"] for u in units])
    if len(units) < 2 or len(set(y_true)) < 2:
        return float("nan"), float("nan"), float("nan")

    point = float(average_precision_score(y_true, y_score))

    if use_patient_aggregate:
        clusters = units
    else:
        by_c: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            by_c[row["cluster_id"]].append(row)
        clusters = [{"cluster_id": c, "rows": rs} for c, rs in by_c.items()]

    rng = np.random.RandomState(seed)
    n_c = len(clusters)
    boot = []
    for _ in range(n_bootstrap):
        idx = rng.randint(0, n_c, size=n_c)
        if use_patient_aggregate:
            sample_units = [clusters[i] for i in idx]
            yt = np.array([u["y_true"] for u in sample_units])
            ys = np.array([u["y_score"] for u in sample_units])
        else:
            pooled = []
            for i in idx:
                pooled.extend(clusters[i]["rows"])
            yt = np.array([x["y_true"] for x in pooled])
            ys = np.array([x["y_score"] for x in pooled])
        if len(set(yt)) < 2:
            continue
        try:
            boot.append(average_precision_score(yt, ys))
        except ValueError:
            continue

    if not boot:
        return point, float("nan"), float("nan")

    boot = np.array(boot)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return point, float(lo), float(hi)


def _compute_dice(pred_mask: np.ndarray, gt_mask: np.ndarray) -> float:
    pred = pred_mask.astype(bool)
    gt = gt_mask.astype(bool)
    intersection = np.logical_and(pred, gt).sum()
    union = pred.sum() + gt.sum()
    if union == 0:
        return 1.0 if intersection == 0 else 0.0
    return float((2.0 * intersection) / union)


def _cluster_bootstrap_mean(
    rows: list[dict],
    value_key: str,
    n_bootstrap: int,
    seed: int,
    per_cluster_aggregate: bool = False,
) -> tuple[float, float, float, int]:
    if not rows:
        return float("nan"), float("nan"), float("nan"), 0

    by_c: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        by_c[row["cluster_id"]].append(float(row[value_key]))

    if per_cluster_aggregate:
        units = [{"cluster_id": c, "value": float(np.mean(vs))} for c, vs in by_c.items()]
        point = float(np.mean([u["value"] for u in units]))
        clusters = units
    else:
        point = float(np.mean([row[value_key] for row in rows]))
        clusters = [{"cluster_id": c, "values": vs} for c, vs in by_c.items()]

    rng = np.random.RandomState(seed)
    n_c = len(clusters)
    boot = []
    for _ in range(n_bootstrap):
        idx = rng.randint(0, n_c, size=n_c)
        if per_cluster_aggregate:
            boot.append(float(np.mean([clusters[i]["value"] for i in idx])))
        else:
            vals: list[float] = []
            for i in idx:
                vals.extend(clusters[i]["values"])
            boot.append(float(np.mean(vals)))

    boot_arr = np.array(boot)
    lo, hi = np.percentile(boot_arr, [2.5, 97.5])
    return point, float(lo), float(hi), n_c


def _seg_rows(
    pipeline_dir: Path,
    gt_mask_dir: Path,
    cluster_map: dict[str, str] | None,
) -> list[dict]:
    npz_path = pipeline_dir / "intermediate" / "selected_masks.npz"
    if not npz_path.exists():
        raise FileNotFoundError(f"Missing {npz_path}")

    data = np.load(str(npz_path), allow_pickle=True)
    image_names = list(data["image_names"])
    masks = list(data["selected_masks"])
    io = ImageIO()
    gt_dir = Path(gt_mask_dir)
    gt_stem_map = {p.stem: p for p in gt_dir.iterdir() if p.is_file()}

    rows = []
    for img_name, pred in zip(image_names, masks):
        stem = Path(img_name).stem
        gt_path = gt_stem_map.get(stem)
        if gt_path is None or not gt_path.exists():
            continue
        gt = io.binarize_mask(io.load_mask(gt_path))
        dice = _compute_dice(pred.astype(bool), gt)
        cid = (cluster_map or {}).get(img_name, img_name)
        rows.append({"image_name": img_name, "cluster_id": cid, "dice": dice})
    return rows


def build_classification_report(
    results: list[dict],
    cluster_map: dict[str, str] | None,
    n_bootstrap: int,
    seed: int,
    patient_level: bool,
) -> dict:
    rows = _rows_from_results(results, cluster_map)
    if not rows:
        return {"skipped": True, "reason": "no classification labels in results (seg-only run?)"}

    n_clusters = len({r["cluster_id"] for r in rows})
    auc_img, auc_lo, auc_hi, _ = _cluster_bootstrap_auc(rows, n_bootstrap, seed, False)
    auprc_img, auprc_lo, auprc_hi = _cluster_bootstrap_auprc(rows, n_bootstrap, seed, False)

    out: dict = {
        "task": "classification",
        "n_images": len(rows),
        "n_clusters": n_clusters,
        "image_level_cluster_bootstrap": {
            "auroc": {"mean": auc_img, "ci_lower": auc_lo, "ci_upper": auc_hi},
            "auprc": {"mean": auprc_img, "ci_lower": auprc_lo, "ci_upper": auprc_hi},
        },
    }

    if patient_level and cluster_map and n_clusters < len(rows):
        patients = _aggregate_patient_level(rows)
        pt_auc, pt_lo, pt_hi, _ = _cluster_bootstrap_auc(rows, n_bootstrap, seed, True)
        pt_auprc, pt_auprc_lo, pt_auprc_hi = _cluster_bootstrap_auprc(rows, n_bootstrap, seed, True)
        out["patient_level"] = {
            "n_patients": len(patients),
            "auroc": {"mean": pt_auc, "ci_lower": pt_lo, "ci_upper": pt_hi},
            "auprc": {"mean": pt_auprc, "ci_lower": pt_auprc_lo, "ci_upper": pt_auprc_hi},
        }
    return out


def build_segmentation_report(
    pipeline_dir: Path,
    gt_mask_dir: Path,
    cluster_map: dict[str, str] | None,
    n_bootstrap: int,
    seed: int,
    patient_level: bool,
) -> dict:
    rows = _seg_rows(pipeline_dir, gt_mask_dir, cluster_map)
    return build_segmentation_report_from_dice_rows(
        rows, cluster_map, n_bootstrap, seed, patient_level
    )


def build_segmentation_report_from_dice_rows(
    rows: list[dict],
    cluster_map: dict[str, str] | None,
    n_bootstrap: int,
    seed: int,
    patient_level: bool,
) -> dict:
    if not rows:
        return {"skipped": True, "reason": "no segmentation dice rows"}

    n_clusters = len({r["cluster_id"] for r in rows})
    d_mean, d_lo, d_hi, _ = _cluster_bootstrap_mean(rows, "dice", n_bootstrap, seed, False)
    out: dict = {
        "task": "segmentation",
        "n_images": len(rows),
        "n_clusters": n_clusters,
        "image_level_cluster_bootstrap": {
            "dice": {"mean": d_mean, "ci_lower": d_lo, "ci_upper": d_hi},
        },
    }
    if patient_level and cluster_map and n_clusters < len(rows):
        pd_mean, pd_lo, pd_hi, _ = _cluster_bootstrap_mean(rows, "dice", n_bootstrap, seed, True)
        out["patient_level"] = {
            "n_patients": n_clusters,
            "dice": {"mean": pd_mean, "ci_lower": pd_lo, "ci_upper": pd_hi},
        }
    return out


def load_exclude_images(path: Path) -> set[str]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict) and "images" in data:
            items = data["images"]
        else:
            raise ValueError(f"Unsupported exclude JSON shape: {path}")
        return {str(x).strip() for x in items if str(x).strip()}

    names: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        names.add(line)
    return names


def image_is_excluded(image_name: str, exclude: set[str]) -> bool:
    if not exclude:
        return False
    if image_name in exclude:
        return True
    base = Path(image_name).name
    return base in exclude


def filter_classification_results(results: list[dict], exclude: set[str]) -> list[dict]:
    if not exclude:
        return results
    return [r for r in results if not image_is_excluded(r.get("image_name", ""), exclude)]


def filter_dice_rows(rows: list[dict], exclude: set[str]) -> list[dict]:
    if not exclude:
        return rows
    return [r for r in rows if not image_is_excluded(r.get("image_name", ""), exclude)]


def classification_results_from_jsonl(records: list[dict]) -> list[dict]:
    """Convert b2_exports classification jsonl to pipeline-like results list."""
    results = []
    for rec in records:
        score = float(rec["score_malignant"])
        pred = 1 if score >= 0.5 else 0
        results.append(
            {
                "image_name": rec["image_name"],
                "true_label": int(rec["y_true"]),
                "final_label": "恶性" if pred == 1 else "良性",
                "final_confidence": score if pred == 1 else 1.0 - score,
            }
        )
    return results


def seg_dice_rows_from_jsonl(
    records: list[dict], cluster_map: dict[str, str] | None
) -> list[dict]:
    rows = []
    for rec in records:
        img = rec["image_name"]
        cid = (cluster_map or {}).get(img, img)
        rows.append({"image_name": img, "cluster_id": cid, "dice": float(rec["dice"])})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="B2 cluster-bootstrap metrics.")
    parser.add_argument("--task", choices=("classification", "segmentation", "both"), default="classification")
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--pipeline-dir", type=Path, default=None, help="Required for segmentation (selected_masks.npz)")
    parser.add_argument("--gt-mask-dir", type=Path, default=None, help="Required for segmentation")
    parser.add_argument("--cluster-map", type=Path, default=None, help="JSON filename->cluster_id; omit for 1 image = 1 cluster")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--patient-level", action="store_true")
    parser.add_argument(
        "--exclude-images",
        type=Path,
        default=None,
        help="Text (one image_name per line) or JSON list / manifest with 'images' key",
    )
    args = parser.parse_args()

    results = json.loads(args.results.read_text(encoding="utf-8"))
    exclude: set[str] = set()
    if args.exclude_images:
        exclude = load_exclude_images(args.exclude_images)
        n_before = len(results)
        results = filter_classification_results(results, exclude)
        print(f"exclude-images: {len(exclude)} listed, classification rows {n_before} -> {len(results)}")
    cluster_map = None
    if args.cluster_map and args.cluster_map.exists():
        cluster_map = json.loads(args.cluster_map.read_text(encoding="utf-8"))

    pipeline_dir = args.pipeline_dir or args.results.parent
    out: dict = {
        "results": str(args.results),
        "cluster_map": str(args.cluster_map) if args.cluster_map else None,
        "bootstrap": {"n": args.n_bootstrap, "seed": args.seed},
    }
    if exclude:
        out["exclusion"] = {
            "exclude_images": str(args.exclude_images),
            "n_listed": len(exclude),
            "criterion": "image_name in exclude list (sensitivity analysis)",
        }

    if args.task in ("classification", "both"):
        out["classification"] = build_classification_report(
            results, cluster_map, args.n_bootstrap, args.seed, args.patient_level
        )
    if args.task in ("segmentation", "both"):
        if args.gt_mask_dir is None:
            raise SystemExit("--gt-mask-dir required for segmentation")
        if exclude:
            rows = _seg_rows(pipeline_dir, args.gt_mask_dir, cluster_map)
            n_before = len(rows)
            rows = filter_dice_rows(rows, exclude)
            print(f"exclude-images: segmentation dice rows {n_before} -> {len(rows)}")
            out["segmentation"] = build_segmentation_report_from_dice_rows(
                rows, cluster_map, args.n_bootstrap, args.seed, args.patient_level
            )
        else:
            out["segmentation"] = build_segmentation_report(
                pipeline_dir, args.gt_mask_dir, cluster_map, args.n_bootstrap, args.seed, args.patient_level
            )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
