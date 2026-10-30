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

DEFAULT_COHORTS = ["tn3k", "tn5k", "thyroidxl", "zjh8k", "ddti_cls"]
COHORT_LABELS = {
    "tn3k": "TN3K",
    "tn5k": "TN5K",
    "thyroidxl": "ThyroidXL",
    "zjh8k": "ZJH-8K",
    "ddti_cls": "DDTI",
}


def plot_combined(
    cohorts_root: Path,
    cohorts: list[str],
    out_path: Path,
    *,
    calibration_json_name: str = "calibration_test.json",
) -> Path | None:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return None

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
        cal_path = cohorts_root / cohort / calibration_json_name
        if not cal_path.is_file():
            continue
        cal = json.loads(cal_path.read_text(encoding="utf-8"))
        bins = cal.get("bins") or []
        ax = axes[idx // ncols][idx % ncols]
        label = COHORT_LABELS.get(cohort, cohort)
        _draw_bins_on_ax(ax, bins, title=label)

    for j in range(len(cohorts), nrows * ncols):
        axes[j // ncols][j % ncols].set_visible(False)

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def _scatter_sizes(counts: list[int], *, min_pt: float = 48.0, max_pt: float = 220.0) -> list[float]:
    """合图子图较小：用 sqrt(count) 缩放，避免小队列看不见、大队列单点过大。"""
    import math

    out: list[float] = []
    for c in counts:
        s = math.sqrt(max(c, 1)) * 11.0
        out.append(min(max_pt, max(min_pt, s)))
    return out


def _draw_bins_on_ax(ax, bins: list, *, title: str) -> None:
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

    ax.plot([0, 1], [0, 1], "k--", label="Perfect calibration", linewidth=1)
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
    ax.set_xlabel("Mean predicted P(malignant)", fontsize=8)
    ax.set_ylabel("Fraction malignant", fontsize=8)
    ax.set_title(title, fontsize=9)
    ax.legend(loc="lower right", fontsize=6)
    ax.grid(True, alpha=0.25)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohorts-root", type=Path, default=Path("output/b8/cohorts_test_fit"))
    parser.add_argument("--calibration-json", default="calibration_test.json")
    parser.add_argument("--out", type=Path, default=Path("output/b8/figures/reliability_panels.png"))
    parser.add_argument("--cohorts", default=",".join(DEFAULT_COHORTS))
    args = parser.parse_args()
    cohorts = [c.strip() for c in args.cohorts.split(",") if c.strip()]
    p = plot_combined(
        args.cohorts_root,
        cohorts,
        args.out,
        calibration_json_name=args.calibration_json,
    )
    if p:
        print(f"✓ {p}")


if __name__ == "__main__":
    main()
