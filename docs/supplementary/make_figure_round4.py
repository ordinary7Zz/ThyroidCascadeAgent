import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

OUT = Path(__file__).resolve().parents[1] / (sys.argv[1] if len(sys.argv) > 1 else "outputs_round5")
plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none", "pdf.fonttype": 42})
MM = 1 / 25.4
W = 166.0
FS = 7.0
LINE = FS / 72 * 25.4 * 1.22
GREY, PURPLE, INK = "#d9d9d9", "#7a3e9d", "#111111"

SUMS = {
    "train cls": ([4633, 3500, 9441], 17574), "train seg": ([4633, 3500, 703, 9441], 18277),
    "val cls": ([100, 500, 100], 700), "val seg": ([100, 500, 150, 100], 850),
    "int cls": ([614, 1000, 2090], 3704), "int seg": ([614, 1000, 150, 2090], 3854),
    "ext cls": ([349, 6807, 4999], 12155), "ext nodule seg": ([637, 7288, 6807, 6384], 21116),
    "ext all": ([637, 7288, 6807, 8721], 23453), "all seven": ([5347, 5000, 11631, 1003, 637, 7288, 7958], 38864),
    "dev+test": ([18277, 850, 3854, 637, 7288, 7958], 38864), "zjh": ([6807, 1151], 7958), "with nhc": ([38864, 8721], 47585),
}
for k, (parts, total) in SUMS.items():
    assert sum(parts) == total, (k, sum(parts), total)

ROWS = [
    ("Training", "Classification and Segmentation\nTraining set\nn = 18,277 images",
     ("Classification (n = 17,574)", ["TN3K (n = 4,633)", "TN5K (n = 3,500)", "ThyroidXL (n = 9,441)"]),
     ("Segmentation (n = 18,277)", ["TN3K (n = 4,633)", "TN5K (n = 3,500)", "PKTN (n = 703)", "ThyroidXL (n = 9,441)"]),
     ("LNM & PTC subtype\nZJH-8K malignant\nprimary lesions\nn = 3,227 images", "solid")),
    ("Validation", "Classification and Segmentation\nValidation set: checkpoint selection, routing and referral thresholds\nn = 850 images",
     ("Classification (n = 700)", ["TN3K (n = 100)", "TN5K (n = 500)", "ThyroidXL (n = 100)"]),
     ("Segmentation (n = 850)", ["TN3K (n = 100)", "TN5K (n = 500)", "PKTN (n = 150)", "ThyroidXL (n = 100)"]),
     ("LNM & PTC subtype\nFive-fold cross-validation\nwithin the training pool;\nno separate validation set", "solid")),
    ("Internal test", "Classification and Segmentation\nTest splits of the development cohorts\nn = 3,854 images",
     ("Classification (n = 3,704)", ["TN3K (n = 614)", "TN5K (n = 1,000)", "ThyroidXL (n = 2,090)"]),
     ("Segmentation (n = 3,854)", ["TN3K (n = 614)", "TN5K (n = 1,000)", "PKTN (n = 150)", "ThyroidXL (n = 2,090)"]),
     ("LNM & PTC subtype\nZJH-8K malignant hold-out\n(20% of patients)\nn = 801 images", "solid")),
    ("External test", "Classification and Segmentation\nIndependent external cohorts\nn = 23,453 images\n1,151 ZJH-8K images identical to TN3K training images excluded",
     ("Classification (n = 12,155)", ["DDTI (n = 349)", "ZJH-8K (n = 6,807)", "NHC-MISD-TUS (n = 4,999)"]),
     ("Segmentation (n = 21,116)", ["DDTI (n = 637)", "RJH-7K (n = 7,288)", "ZJH-8K (n = 6,807)", "NHC-MISD-TUS nodule (n = 6,384)", "NHC-MISD-TUS gland (n = 8,721)"]),
     ("ZJH-8K dual role\nSame images: external test\nfor classification and\nsegmentation; malignant\nlesions split for LNM &\nPTC subtype (3,227 / 801)", "dual")),
]
SIDE = ("Datasets (total images)\n"
        "TN3K 5,347 · TN5K 5,000 · ThyroidXL 11,631 · PKTN 1,003 · DDTI 637 · RJH-7K 7,288\n"
        "ZJH-8K 7,958 · NHC-MISD-TUS 8,721 (35 centres)\n"
        "Seven cohorts: 38,864 images; with NHC-MISD-TUS: 47,585")
texts = []


def box(ax, x0, y0, w, h, txt, fc="white", ec=INK, ls="-", lw=0.7, align="center"):
    ax.add_patch(Rectangle((x0, y0), w, h, fc=fc, ec=ec, ls=ls, lw=lw, zorder=2))
    lines = txt.split("\n")
    y = y0 + h / 2 - (len(lines) - 1) * LINE / 2
    for i, l in enumerate(lines):
        x = x0 + w / 2 if align == "center" else x0 + 1.8
        t = ax.text(x, y + i * LINE, l, ha=align, va="center", fontsize=FS, weight="bold" if i == 0 else "normal", color=INK, zorder=3)
        texts.append((t, w))


def hbox(txt):
    return txt.count("\n") * LINE + LINE + 3.0


def bullets(ax, x0, y0, w, title, items):
    rows = [(title, True)] + [(("• " + it) if not it.startswith("  ") else ("   " + it.strip()), False) for it in items]
    h = len(rows) * LINE + 3.0
    ax.add_patch(Rectangle((x0, y0), w, h, fc="white", ec=INK, lw=0.7, zorder=2))
    for i, (l, b) in enumerate(rows):
        t = ax.text(x0 + 1.6, y0 + 1.5 + LINE * (i + 0.5), l, ha="left", va="center", fontsize=FS, weight="bold" if b else "normal", color=INK, zorder=3)
        texts.append((t, w))
    return h


def arrow(ax, x0, y0, x1, y1):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=0.7, mutation_scale=6, shrinkA=0, shrinkB=0), zorder=1)


def line(ax, xs, ys, **kw):
    ax.plot(xs, ys, color=kw.pop("color", INK), lw=kw.pop("lw", 0.7), zorder=1, solid_capstyle="butt", **kw)


def layout():
    """每行的高度：左侧（标题 + LNM 框）与右侧（汇总框 + 子框）取大者。"""
    out = []
    for head, summ, cls, seg, (mal, kind) in ROWS:
        left = 8.5 + 4 + hbox(mal)
        right = hbox(summ) + 7 + max(len(cls[1]) + 1, len(seg[1]) + 1) * LINE + 3.0
        out.append(max(left, right))
    return out


def main():
    if OUT.exists() and any(OUT.iterdir()):
        sys.exit("output dir not empty; refuse to overwrite")
    OUT.mkdir(exist_ok=True)
    heights = layout()
    top = 28.0
    gap = 6.0
    H = top + sum(heights) + gap * (len(ROWS) - 1) + 3.0
    fig = plt.figure(figsize=(W * MM, H * MM))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.axis("off")
    # 顶部
    box(ax, 1.0, 3.0, 36.0, 9.0, "Image Analysis")
    sh = hbox(SIDE)
    box(ax, 44.0, 1.5, W - 45.0, sh, SIDE, align="left")
    arrow(ax, 37.0, 7.5, 44.0, 7.5)
    trunk_x = 4.5
    lx0, lx1 = 9.0, 49.0           # 左侧：标题与 LNM 框
    rx0, rx1 = 54.0, W - 1.0       # 右侧：汇总框与子框
    cw = (rx1 - rx0 - 2.0) / 2
    y = top
    ys_head = []
    lnm_boxes = []
    for (head, summ, cls, seg, (mal, kind)), h in zip(ROWS, heights):
        # 标题框
        hh = 8.5
        box(ax, lx0, y, lx1 - lx0, hh, head, fc=GREY)
        ys_head.append(y + hh / 2)
        arrow(ax, trunk_x, y + hh / 2, lx0, y + hh / 2)
        # LNM 或双重用途框
        mh = hbox(mal)
        my = y + hh + 4
        if kind == "dual":
            box(ax, lx0, my, lx1 - lx0, mh, mal, ec=PURPLE, ls=(0, (4, 2)), lw=0.9)
        else:
            arrow(ax, (lx0 + lx1) / 2, y + hh, (lx0 + lx1) / 2, my)
            box(ax, lx0, my, lx1 - lx0, mh, mal)
        lnm_boxes.append((my, mh))
        # 汇总框
        sh2 = hbox(summ)
        box(ax, rx0, y, rx1 - rx0, sh2, summ)
        arrow(ax, lx1, y + hh / 2, rx0, y + hh / 2)
        # 子框
        cy = y + sh2 + 7
        bus = y + sh2 + 3.5
        mid = (rx0 + rx1) / 2
        line(ax, [mid, mid], [y + sh2, bus])
        c1, c2 = rx0 + cw / 2, rx0 + cw + 2.0 + cw / 2
        line(ax, [c1, c2], [bus, bus])
        arrow(ax, c1, bus, c1, cy)
        arrow(ax, c2, bus, c2, cy)
        bullets(ax, rx0, cy, cw, *cls)
        bullets(ax, rx0 + cw + 2.0, cy, cw, *seg)
        y += h + gap
    # 主干
    line(ax, [trunk_x, trunk_x], [12.0, ys_head[-1]])
    line(ax, [1.0 + 18.0, 1.0 + 18.0], [12.0, 12.0])
    line(ax, [trunk_x, 19.0], [12.0, 12.0])
    # 双重用途框与上一行 LNM 框之间的紫色虚线
    (iy, ih), (dy, dh) = lnm_boxes[2], lnm_boxes[3]
    xm = (lx0 + lx1) / 2
    line(ax, [xm, xm], [iy + ih, dy], color=PURPLE, lw=0.9, ls=(0, (4, 2)))
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    over = [(t.get_text(), round(t.get_window_extent(r).width / fig.dpi * 25.4, 1), round(w, 1)) for t, w in texts
            if t.get_window_extent(r).width / fig.dpi * 25.4 > w - 2.4]
    for ext in ("png", "pdf", "svg"):
        fig.savefig(OUT / f"image_analysis_dataflow.{ext}", dpi=300)
    print(f"size {W:.0f} x {H:.1f} mm | sums checked: {len(SUMS)} | text overflow: {over or 'none'}")


if __name__ == "__main__":
    main()
