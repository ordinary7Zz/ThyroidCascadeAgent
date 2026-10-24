#!/usr/bin/env python3
"""从 B8 abstention_eval.json 绘制 risk–coverage 曲线（单队列或多队列合图）。"""

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

from pipeline.revision.b8.plot_abstention import plot_risk_coverage_curve, plot_risk_coverage_vs_abstention

DEFAULT_COHORTS = [
    "tn3k",
    "tn5k",
    "thyroidxl",
    "zjh8k",
    "ddti_cls",
]

COHORT_LABELS = {
    "tn3k": "TN3K",
    "tn5k": "TN5K",
    "thyroidxl": "ThyroidXL",
    "zjh8k": "ZJH-8K",
    "ddti_cls": "DDTI-cls",
    "rjh7k": "RJH-7K",
    "ddti_seg": "DDTI-seg",
    "pktn": "PKTN",
    "sample": "sample",
}


def _load_curve(eval_path: Path) -> list[dict]:
    with open(eval_path, encoding="utf-8") as f:
        data = json.load(f)
    return list(data.get("risk_coverage") or [])


def _operating_point(eval_path: Path) -> tuple[int, int, float]:
    with open(eval_path, encoding="utf-8") as f:
        data = json.load(f)
    n_total = int(data.get("n_total") or 0)
    n_flagged = int(data.get("n_flagged") or 0)
    rate = n_flagged / n_total if n_total else 0.0
    return n_flagged, n_total, rate


def plot_multi_panel(
    cohort_curves: dict[str, list[dict]],
    out_path: Path,
    *,
    x_axis: str,
    mark_operating: bool,
    operating: dict[str, float],
) -> Path | None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return None

    if not cohort_curves:
        return None

    n = len(cohort_curves)
    ncols = min(3, n)
    nrows = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 3.5 * nrows), squeeze=False)

    for idx, (cohort, curve) in enumerate(sorted(cohort_curves.items())):
        ax = axes[idx // ncols][idx % ncols]
        label = COHORT_LABELS.get(cohort, cohort)
        if x_axis == "abstention":
            xs, ys = [], []
            for pt in curve:
                acc = pt.get("retained_accuracy")
                if acc is None or "abstention_rate" not in pt:
                    continue
                xs.append(float(pt["abstention_rate"]))
                ys.append(float(acc))
            ax.plot(xs, ys, "-", linewidth=1.2)
            xlab = "Abstention rate"
            if mark_operating and cohort in operating:
                ar = operating[cohort]
                if xs:
                    j = min(range(len(xs)), key=lambda i: abs(xs[i] - ar))
                    ax.scatter([xs[j]], [ys[j]], s=40, zorder=5, color="C1")
        else:
            xs, ys = [], []
            for pt in curve:
                acc = pt.get("retained_accuracy")
                if acc is None:
                    continue
                xs.append(float(pt["coverage"]))
                ys.append(float(acc))
            ax.plot(xs, ys, "-", linewidth=1.2)
            xlab = "Coverage"
            if mark_operating and cohort in operating and xs:
                cov = 1.0 - operating[cohort]
                j = min(range(len(xs)), key=lambda i: abs(xs[i] - cov))
                ax.scatter([xs[j]], [ys[j]], s=40, zorder=5, color="C1")

        ax.set_title(label, fontsize=10)
        ax.set_xlabel(xlab, fontsize=9)
        ax.set_ylabel("Retained accuracy", fontsize=9)
        ax.set_xlim(0, 1.02)
        ax.grid(True, alpha=0.3)

    for j in range(n, nrows * ncols):
        axes[j // ncols][j % ncols].set_visible(False)

    fig.suptitle("Risk–coverage (classification, retained subset)", fontsize=11)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="B8 risk–coverage 图")
    parser.add_argument(
        "--cohorts-root",
        type=Path,
        default=Path("output/b8/cohorts"),
        help="含 <cohort>/abstention_eval.json 的目录",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("output/b8/figures"),
        help="输出 PNG 目录",
    )
    parser.add_argument(
        "--cohorts",
        type=str,
        default=",".join(DEFAULT_COHORTS),
        help="逗号分隔队列名；默认主 BM 外测队列",
    )
    parser.add_argument(
        "--x-axis",
        choices=["coverage", "abstention"],
        default="coverage",
        help="横轴：覆盖率或送复核率",
    )
    parser.add_argument(
        "--mark-operating-point",
        action="store_true",
        help="在曲线上标出固定 validation 阈值对应工作点",
    )
    parser.add_argument(
        "--combined",
        action="store_true",
        help="额外输出多队列合图 risk_coverage_panels.png",
    )
    args = parser.parse_args()

    cohorts = [c.strip() for c in args.cohorts.split(",") if c.strip()]
    args.out_dir.mkdir(parents=True, exist_ok=True)

    cohort_curves: dict[str, list[dict]] = {}
    operating: dict[str, float] = {}

    for cohort in cohorts:
        eval_path = args.cohorts_root / cohort / "abstention_eval.json"
        if not eval_path.is_file():
            print(f"跳过 {cohort}: 无 {eval_path}")
            continue
        curve = _load_curve(eval_path)
        if not curve:
            print(f"跳过 {cohort}: risk_coverage 为空（无 BM 标签）")
            continue
        cohort_curves[cohort] = curve
        _, _, rate = _operating_point(eval_path)
        operating[cohort] = rate

        label = COHORT_LABELS.get(cohort, cohort)
        stem = f"risk_coverage_{cohort}"
        if args.x_axis == "abstention":
            out = args.out_dir / f"{stem}_vs_abstention.png"
            fig = plot_risk_coverage_vs_abstention(
                curve,
                out,
                title=f"{label}: risk–coverage",
                label=label,
                mark_abstention_rate=rate if args.mark_operating_point else None,
            )
        else:
            out = args.out_dir / f"{stem}.png"
            fig = plot_risk_coverage_curve(
                curve,
                out,
                title=f"{label}: risk–coverage",
                label=label,
                mark_coverage=(1.0 - rate) if args.mark_operating_point else None,
            )
        if fig:
            print(f"✓ {fig}")
        else:
            print(f"未生成 {cohort}（需要 matplotlib）")

    if args.combined and cohort_curves:
        panel_out = args.out_dir / "risk_coverage_panels.png"
        fig = plot_multi_panel(
            cohort_curves,
            panel_out,
            x_axis=args.x_axis,
            mark_operating=args.mark_operating_point,
            operating=operating,
        )
        if fig:
            print(f"✓ {fig}")


if __name__ == "__main__":
    main()
