#!/usr/bin/env python3
"""B7：NHC 中心级性能、中心内/中心间异质性、可选全腺体与 meta 回归。"""

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

import repo_path

repo_path.install()

from pipeline.evaluate import evaluate_pipeline
from pipeline.revision.b7.gland_metrics import compute_gland_per_image, write_gland_jsonl
from pipeline.revision.b7.nhc_config import load_nhc_data_paths
from pipeline.revision.b7.per_image_enrich import enrich_output_dir_jsonl
from pipeline.revision.b7.report import build_b7_report
from shared.center_manifest import load_center_lookup, summarize_centers_from_labels
from shared.image_io import ImageIO
from shared.revision_paths import B7_DEFAULT_OUT, NHC_PRIMARY_OUTPUT_DIR, NHC_REVISION_CONFIG


def _load_descriptive(label_file: Path | None, g3_csv: Path | None) -> dict | None:
    if label_file is None or not label_file.is_file():
        return None
    summary = summarize_centers_from_labels(str(label_file))
    if g3_csv and g3_csv.is_file():
        import csv

        with open(g3_csv, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                cid = row.get("center_id") or row.get("centre_id")
                if not cid:
                    continue
                block = summary["centers"].setdefault(cid, {"n_images": 0})
                for k in (
                    "n_patients",
                    "n_nodules",
                    "scanner",
                    "scanner_vendor",
                    "hospital",
                    "province",
                    "seg_label",
                    "bm_label",
                    "gland_label",
                ):
                    if row.get(k) not in (None, ""):
                        block[k] = row[k]
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="B7 NHC 中心级异质性汇总")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=NHC_PRIMARY_OUTPUT_DIR,
        help="含 results.json 的 pipeline 输出",
    )
    parser.add_argument("--config", type=Path, default=NHC_REVISION_CONFIG)
    parser.add_argument("--gt-mask-dir", type=Path, default=None)
    parser.add_argument("--label-file", type=Path, default=None)
    parser.add_argument("--center-manifest", type=Path, default=None)
    parser.add_argument("--g3-csv", type=Path, default=None, help="G3 中心元数据 CSV")
    parser.add_argument("--gt-gland-mask-dir", type=Path, default=None)
    parser.add_argument("--gland-pred-mask-dir", type=Path, default=None)
    parser.add_argument("--re-evaluate", action="store_true", help="先跑 evaluate 生成结节/分类 jsonl")
    parser.add_argument(
        "--compute-gland",
        action="store_true",
        help="若提供腺体 GT/预测 mask 目录则写 per_image_gland_metrics.jsonl",
    )
    parser.add_argument(
        "--meta-covariates",
        type=str,
        default="malignant_ratio_center",
        help="逗号分隔的 meta 回归协变量键（图像行上字段）",
    )
    parser.add_argument("--out", type=Path, default=B7_DEFAULT_OUT)
    args = parser.parse_args()

    paths = load_nhc_data_paths(args.config)
    if args.gt_mask_dir is None and paths.get("gt_mask_dir"):
        args.gt_mask_dir = Path(paths["gt_mask_dir"])
    if args.label_file is None and paths.get("label_file"):
        args.label_file = Path(paths["label_file"])
    if args.center_manifest is None and paths.get("center_manifest"):
        args.center_manifest = Path(paths["center_manifest"])
    if args.gt_gland_mask_dir is None and paths.get("gt_gland_mask_dir"):
        args.gt_gland_mask_dir = Path(paths["gt_gland_mask_dir"])
    if args.gland_pred_mask_dir is None and paths.get("gland_pred_mask_dir"):
        args.gland_pred_mask_dir = Path(paths["gland_pred_mask_dir"])

    args.out.mkdir(parents=True, exist_ok=True)
    results_path = args.output_dir / "results.json"
    if not results_path.is_file():
        raise SystemExit(f"缺少 {results_path}")

    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    manifest_lookup = load_center_lookup(str(args.center_manifest) if args.center_manifest else None)

    if args.re_evaluate:
        evaluate_pipeline(
            results,
            str(args.output_dir),
            image_io=ImageIO(),
            gt_mask_dir=str(args.gt_mask_dir) if args.gt_mask_dir else None,
        )

    enriched = enrich_output_dir_jsonl(
        args.output_dir,
        results=results,
        manifest_lookup=manifest_lookup,
    )
    if enriched:
        print(f"✓ 已补写 center_id: {enriched}")

    do_gland = args.compute_gland or (
        args.gt_gland_mask_dir
        and args.gland_pred_mask_dir
        and args.gt_gland_mask_dir.is_dir()
        and args.gland_pred_mask_dir.is_dir()
    )
    if do_gland:
        stems = [Path(r.get("image_name", "")).stem for r in results if r.get("image_name")]
        gland_rows = compute_gland_per_image(
            gt_gland_dir=args.gt_gland_mask_dir,
            pred_gland_dir=args.gland_pred_mask_dir,
            image_stems=stems,
        )
        gpath = write_gland_jsonl(args.output_dir, gland_rows)
        enrich_output_dir_jsonl(args.output_dir, results=results, manifest_lookup=manifest_lookup)
        print(f"✓ 全腺体逐图: {gpath} ({len(gland_rows)} 条)")

    descriptive = _load_descriptive(
        args.label_file if args.label_file and args.label_file.is_file() else None,
        args.g3_csv,
    )
    cov_keys = [k.strip() for k in args.meta_covariates.split(",") if k.strip()]
    report = build_b7_report(
        args.output_dir,
        results=results,
        center_descriptive=descriptive,
        meta_covariate_keys=cov_keys,
    )

    report_path = args.out / "b7_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"✓ B7 报告: {report_path}")

    hetero = report.get("heterogeneity") or {}
    for key, block in hetero.items():
        if block and block.get("i2_percent") is not None:
            print(f"  {key} I² ≈ {block['i2_percent']:.1f}%, τ² ≈ {block.get('tau2')}")

    legacy_path = args.out / "center_metrics.json"
    with open(legacy_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "n_centers": report["center_performance"]["n_centers"],
                "macro_mean_dice": report["center_performance"].get("macro_mean_dice"),
                "macro_mean_auroc": report["center_performance"].get("macro_mean_auroc"),
                "centers": report["center_performance"]["centers"],
                "heterogeneity": hetero,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"✓ 兼容汇总: {legacy_path}")


if __name__ == "__main__":
    main()
