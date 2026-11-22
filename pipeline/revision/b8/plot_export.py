"""Export matplotlib panels as text-free SVG for manual layout (Illustrator / Inkscape)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure


# 无字 SVG 图例占位宽度（排版软件里手补说明）
LEGEND_LABEL_BLANK = "\u2003" * 12


def strip_axes_text(ax: "Axes", *, keep_legend: bool = False) -> None:
    """Remove titles, axis labels, tick labels, and legends; keep data artists."""
    ax.set_title("")
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(
        axis="both",
        which="both",
        labelbottom=False,
        labelleft=False,
        labelright=False,
        labeltop=False,
    )
    for lbl in (*ax.get_xticklabels(), *ax.get_yticklabels()):
        lbl.set_visible(False)
    leg = ax.get_legend()
    if leg is None:
        return
    if keep_legend:
        for txt in leg.get_texts():
            txt.set_text(LEGEND_LABEL_BLANK)
        return
    leg.remove()


def save_figure_notext_svg(
    fig: "Figure",
    out_path: Path,
    *,
    dpi: int = 150,
    keep_legend: bool = False,
) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    for ax in fig.axes:
        strip_axes_text(ax, keep_legend=keep_legend)
    fig.suptitle("")
    fig.savefig(
        out_path,
        format="svg",
        bbox_inches="tight",
        pad_inches=0.02,
        dpi=dpi,
        transparent=False,
    )
    return out_path
