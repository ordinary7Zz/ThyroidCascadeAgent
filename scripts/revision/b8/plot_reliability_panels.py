#!/usr/bin/env python3
"""多队列可靠性分箱合图（读 calibration_test*.json）。"""

from __future__ import annotations

import importlib.util
import json
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

repo_path.install()

from pipeline.revision.b8.plot_export import save_figure_notext_svg

DEFAULT_COHORTS = ["tn3k", "tn5k", "thyroidxl", "zjh8k", "ddti_cls"]
COHORT_LABELS = {
    "tn3k": "TN3K",
    "tn5k": "TN5K",
    "thyroidxl": "ThyroidXL",
    "zjh8k": "ZJH-8K",
    "ddti_cls": "DDTI",
}

NOTEXT_FIGSIZE = (4.2, 3.6)


def _load_bins(cohorts_root: Path, cohort: str, calibration_json_name: str) -> list | None:
    cal_path = cohorts_root / cohort / calibration_json_name
    if not cal_path.is_file():
        return None
    cal = json.loads(cal_path.read_text(encoding="utf-8"))
    return list(cal.get("bins") or [])


def _scatter_sizes(counts: list[int], *, min_pt: float = 48.0, max_pt: float = 220.0) -> list[float]:
    """合图子图较小：用 sqrt(count) 缩放，避免小队列看不见、大队列单点过大。"""
    import math

    out: list[float] = []
    for c in counts:
        s = math.sqrt(max(c, 1)) * 11.0
        out.append(min(max_pt, max(min_pt, s)))
    return out


def _draw_bins_on_ax(
    ax,
    bins: list,
    *,
    with_text: bool = True,
    cohort_label: str = "",
    legend_glyphs_only: bool = False,
) -> None:
    """与 pipeline.revision.b8.plot_calibration.plot_reliability_diagram 同口径。"""
    confs: list[float] = []
    accs: list[float] = []
    counts: list[int] = []
    for b in bins:
        if not b.get("count"):
            continue
        ac = b.get("avg_confidence")
        aa = b.get("avg_accuracy")
        if ac is None or aa is None:
            continue
        confs.append(float(ac))
        accs.append(float(aa))
        counts.append(int(b["count"]))

    need_legend_label = with_text or legend_glyphs_only
    ax.plot(
        [0, 1],
        [0, 1],
        "k--",
        linewidth=1,
        label="Perfect calibration" if need_legend_label else None,
    )
    if confs:
        sizes = _scatter_sizes(counts)
        ax.scatter(
            confs,
            accs,
            s=sizes,
            alpha=0.82,
            c="C0",
            edgecolors="white",
            linewidths=0.8,
        )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    if with_text:
        ax.set_xlabel("Mean predicted P(malignant)", fontsize=8)
        ax.set_ylabel("Fraction malignant", fontsize=8)
        if cohort_label:
            ax.set_title(cohort_label, fontsize=9)
        ax.legend(loc="lower right", fontsize=6)
    elif legend_glyphs_only:
        ax.legend(loc="lower right", fontsize=6, frameon=True, handlelength=2.2)
    ax.grid(True, alpha=0.25)


def save_reliability_notext_svg(
    bins: list,
    out_svg: Path,
    *,
    figsize: tuple[float, float] = NOTEXT_FIGSIZE,
) -> Path | None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return None

    if not bins:
        return None

    fig, ax = plt.subplots(figsize=figsize)
    _draw_bins_on_ax(ax, bins, with_text=False, legend_glyphs_only=True)
    fig.tight_layout()
    save_figure_notext_svg(fig, out_svg, keep_legend=True)
    plt.close(fig)
    return out_svg


def export_cohort_reliability(
    cohort: str,
    bins: list,
    *,
    out_dir: Path,
    svg_dir: Path | None,
) -> tuple[Path | None, Path | None]:
    """带标注 PNG + 无文字 SVG（与合图子格同口径）。"""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return None, None

    label = COHORT_LABELS.get(cohort, cohort)
    png_path = out_dir / f"reliability_{cohort}.png"

    fig, ax = plt.subplots(figsize=(5.0, 4.5))
    _draw_bins_on_ax(ax, bins, with_text=True, cohort_label=f"{label}: reliability")
    fig.tight_layout()
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(png_path, dpi=150)
    plt.close(fig)

    svg_path: Path | None = None
    if svg_dir is not None:
        svg_path = save_reliability_notext_svg(bins, svg_dir / f"reliability_{cohort}_notext.svg")
    return png_path, svg_path


def plot_combined(
    cohort_bins: dict[str, list],
    out_path: Path,
) -> Path | None:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return None

    if not cohort_bins:
        return None

    cohorts = list(cohort_bins.keys())
    n = len(cohorts)
    ncols = 3
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(4.2 * ncols, 3.6 * nrows))
    if nrows == 1 and ncols == 1:
        axes = np.array([[axes]])
    elif nrows == 1:
        axes = np.array([axes])
    elif ncols == 1:
        axes = np.array([[a] for a in axes])

    for idx, cohort in enumerate(cohorts):
        ax = axes[idx // ncols][idx % ncols]
        label = COHORT_LABELS.get(cohort, cohort)
        _draw_bins_on_ax(ax, cohort_bins[cohort], with_text=True, cohort_label=label)

    for j in range(n, nrows * ncols):
        axes[j // ncols][j % ncols].set_visible(False)

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="B8 可靠性：每队列输出带文字 PNG，并默认额外输出无文字 SVG。",
    )
    parser.add_argument(
        "--cohorts-root",
        type=Path,
        default=Path("output/b8/cohorts_test_fit"),
        help="含 <cohort>/calibration_test*.json 的目录",
    )
    parser.add_argument(
        "--calibration-json",
        default="calibration_test.json",
        help="各 cohort 目录下的校准 JSON",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("output/b8/figures"),
        help="带文字单队列 PNG 输出目录",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="多队列合图 PNG（默认 <out-dir>/reliability_panels.png）",
    )
    parser.add_argument("--cohorts", default=",".join(DEFAULT_COHORTS))
    parser.add_argument(
        "--no-notext-svg",
        action="store_true",
        help="不输出无文字 SVG（默认写入 <out-dir>/svg_notext/）",
    )
    parser.add_argument(
        "--notext-svg-dir",
        type=Path,
        default=None,
        help="无文字 SVG 目录（默认 <out-dir>/svg_notext）",
    )
    args = parser.parse_args()

    cohorts = [c.strip() for c in args.cohorts.split(",") if c.strip()]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    panel_out = args.out or (args.out_dir / "reliability_panels.png")

    svg_dir: Path | None = None
    if not args.no_notext_svg:
        svg_dir = args.notext_svg_dir or (args.out_dir / "svg_notext")
        svg_dir.mkdir(parents=True, exist_ok=True)

    cohort_bins: dict[str, list] = {}
    for cohort in cohorts:
        bins = _load_bins(args.cohorts_root, cohort, args.calibration_json)
        if bins is None:
            print(f"跳过 {cohort}: 无 {args.cohorts_root / cohort / args.calibration_json}")
            continue
        if not bins:
            print(f"跳过 {cohort}: bins 为空")
            continue
        cohort_bins[cohort] = bins

        png_path, svg_path = export_cohort_reliability(
            cohort,
            bins,
            out_dir=args.out_dir,
            svg_dir=svg_dir,
        )
        if png_path:
            print(f"✓ PNG {png_path}")
        if svg_path:
            print(f"✓ SVG {svg_path}")

    if cohort_bins:
        p = plot_combined(cohort_bins, panel_out)
        if p:
            print(f"✓ 合图 {p}")


if __name__ == "__main__":
    main()