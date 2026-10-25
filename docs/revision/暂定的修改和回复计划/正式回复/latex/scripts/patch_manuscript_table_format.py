#!/usr/bin/env python3
"""Reformat response-letter Tables R2/R4 (S4/S3) to match ThyroidXAgent.md supplementary layout."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "generated"


def cell_pm(s: str) -> str:
    s = s.strip()
    bold = "\\textbf{" in s
    inner = s
    if bold:
        inner = re.search(r"\\textbf\{([^}]+)\}", s).group(1)
    m = re.search(r"([\d.]+)\s*\(([\d.]+)[–-]([\d.]+)\)", inner.replace(" ", ""))
    if not m:
        return s
    pt, lo, hi = map(float, m.groups())
    hw = (hi - lo) / 2
    body = f"{pt:.4f} $\\pm$ {hw:.4f}"
    return f"\\textbf{{{body}}}" if bold else body


def extract_table(tex: str, label: str) -> list[str]:
    pat = rf"\\label\{{tab:{label}\}}.*?\\begin{{tabular}}.*?\\midrule\n(.*?)\\bottomrule"
    m = re.search(pat, tex, re.S)
    if not m:
        return []
    return [ln.strip() for ln in m.group(1).strip().split("\n") if ln.strip()]


def build_s4(tex: str, cap: str, model_col: str, note: str) -> str:
    rows_au = extract_table(tex, "R2")
    rows_ap = extract_table(tex, "R3")
    au_data, ap_data, methods = [], [], []
    for r in rows_au:
        parts = [p.strip() for p in r.split("&")]
        methods.append(parts[0])
        au_data.append([cell_pm(p) for p in parts[1:]])
    for r in rows_ap:
        parts = [p.strip() for p in r.split("&")]
        ap_data.append([cell_pm(p) for p in parts[1:]])
    cohorts = ["TN3K", "ThyroidXL", "TN5K", "DDTI", "ZJH-8K"]
    hdr = " & ".join([f"\\textbf{{{model_col}}}"] + [f"\\textbf{{{c}}}" for c in cohorts]) + " \\\\"
    lines = [
        "\\begin{manuscriptresponsetable}",
        f"\\caption{{{cap}}}",
        "\\label{tab:R2}",
        "\\hypertarget{tab:R3}{}",
        "\\begin{adjustbox}{max width=\\textwidth}",
        "\\begin{tabular}{lccccc}",
        "\\toprule",
        hdr,
        "\\midrule",
        "\\multicolumn{6}{l}{\\textit{AUROC $\\uparrow$}} \\\\",
        "\\midrule",
    ]
    for i, meth in enumerate(methods):
        if "ThyroidXAgent" in meth:
            lines.append("\\responserowagent")
        lines.append(" & ".join([meth] + au_data[i]) + " \\\\")
    lines += [
        "\\midrule",
        "\\multicolumn{6}{l}{\\textit{AUPRC $\\uparrow$}} \\\\",
        "\\midrule",
    ]
    for i, meth in enumerate(methods):
        if "ThyroidXAgent" in meth:
            lines.append("\\responserowagent")
        lines.append(" & ".join([meth] + ap_data[i]) + " \\\\")
    lines += [
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{adjustbox}",
        f"\\responsetablenote{{{note}}}",
        "\\end{manuscriptresponsetable}",
    ]
    return "\n".join(lines)


def dice_pm_cell(s: str) -> str:
    s = s.strip()
    bold = "\\textbf" in s
    inner = re.search(r"\\textbf\{([^}]+)\}", s)
    text = inner.group(1) if inner else s
    m = re.search(r"([\d.]+)\s*±\s*([\d.]+)", text)
    if not m:
        return s
    a, b = m.groups()
    body = f"{a} $\\pm$ {b}"
    return f"\\textbf{{{body}}}" if bold else body


def build_s3(tex: str, cap: str, model_col: str, note: str) -> str:
    r4_block = re.search(r"\\label\{tab:R4\}(.*?)\\end\{responsetable\}", tex, re.S)
    if not r4_block:
        r4_block = re.search(
            r"\\label\{tab:R4\}(.*?)\\end\{manuscriptresponsetable\}", tex, re.S
        )
    block = r4_block.group(1)

    def rows_from_part(part: str) -> list[str]:
        m = re.search(r"\\midrule\n(.*?)\\bottomrule", part, re.S)
        return [ln.strip() for ln in m.group(1).strip().split("\n") if ln.strip()]

    parts = re.split(r"\\begin\{adjustbox\}", block)

    def parse_seg_rows(rows: list[str]):
        out = []
        for r in rows:
            cells = [p.strip() for p in r.split("&")]
            name = cells[0].replace("TransUNet", "TransUnet")
            vals = [dice_pm_cell(p) for p in cells[1:]]
            out.append((name, vals))
        return out

    dice_rows = parse_seg_rows(rows_from_part(parts[1]))
    hd_rows = parse_seg_rows(rows_from_part(parts[2]))
    cohorts = ["TN3K", "ThyroidXL", "PKTN", "TN5K", "DDTI", "ZJH-8K", "RJH-7K"]
    hdr = " & ".join([f"\\textbf{{{model_col}}}"] + [f"\\textbf{{{c}}}" for c in cohorts]) + " \\\\"
    lines = [
        "\\begin{manuscriptresponsetable}",
        f"\\caption{{{cap}}}",
        "\\label{tab:R4}",
        "\\begin{adjustbox}{max width=\\textwidth}",
        "\\begin{tabular}{lccccccc}",
        "\\toprule",
        hdr,
        "\\midrule",
        "\\multicolumn{8}{l}{\\textit{Dice (\\%) $\\uparrow$}} \\\\",
        "\\midrule",
    ]
    for name, vals in dice_rows:
        if "ThyroidXAgent" in name:
            lines.append("\\responserowagent")
        lines.append(name + " & " + " & ".join(vals) + " \\\\")
    lines += [
        "\\midrule",
        "\\multicolumn{8}{l}{\\textit{HD95 (mm) $\\downarrow$}} \\\\",
        "\\midrule",
    ]
    for name, vals in hd_rows:
        if "ThyroidXAgent" in name:
            lines.append("\\responserowagent")
        lines.append(name + " & " + " & ".join(vals) + " \\\\")
    lines += [
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{adjustbox}",
        f"\\responsetablenote{{{note}}}",
        "\\end{manuscriptresponsetable}",
    ]
    return "\n".join(lines)


def patch_file(path: Path, lang: str) -> None:
    tex = path.read_text()
    if lang == "zh":
        s4_cap = (
            "表 R2. Supplementary Table S4 --- 跨数据集良恶性甲状腺结节分类。"
            "报告受试者工作特征曲线下面积（AUROC）与精确率--召回率曲线下面积（AUPRC），附 95\\% 置信区间。"
        )
        s4_note = (
            "版式与 $\\pm$ 报告方式与投稿 Supplementary Table~S4 一致；"
            "数值为 cluster bootstrap（1000 次，seed=42）重算。"
        )
        s3_cap = (
            "表 R4. Supplementary Table S3 --- 跨数据集甲状腺结节分割。"
            "报告 Dice 系数与 95 百分位 Hausdorff 距离（HD95），附 95\\% 置信区间。"
        )
        s3_note = (
            "版式与 $\\pm$ 报告方式与投稿 Supplementary Table~S3 一致；"
            "数值为 cluster bootstrap（1000 次，seed=42，图像级）重算。"
        )
        model_s4, model_s3 = "方法", "模型"
        r2_anchor = "表 R2."
        r3_anchor = "表 R3."
        r4_anchor = "表 R4."
    else:
        s4_cap = (
            "Table R2. Supplementary Table S4 --- Cross-dataset generalization for "
            "benign-malignant thyroid nodule classification. Area under the receiver "
            "operating characteristic curve (AUROC) and area under the precision-recall "
            "curve (AUPRC) are reported with 95\\% confidence intervals."
        )
        s4_note = (
            "Layout and $\\pm$ reporting match the submitted Supplementary Table~S4; "
            "values recomputed with cluster bootstrap (1000 resamples, seed~42)."
        )
        s3_cap = (
            "Table R4. Supplementary Table S3 --- Cross-dataset generalization for "
            "thyroid nodule segmentation. Dice coefficient and 95th-percentile "
            "Hausdorff distance (HD95) are reported with 95\\% confidence intervals."
        )
        s3_note = (
            "Layout and $\\pm$ reporting match the submitted Supplementary Table~S3; "
            "values recomputed with cluster bootstrap (1000 resamples, seed~42, image-level)."
        )
        model_s4, model_s3 = "Method", "Model"
        r2_anchor = "Table R2."
        r3_anchor = "Table R3."
        r4_anchor = "Table R4."

    s4 = build_s4(tex, s4_cap, model_s4, s4_note)
    s3 = build_s3(tex, s3_cap, model_s3, s3_note)

    i2 = tex.find(f"\\caption{{{r2_anchor}")
    if i2 < 0:
        raise SystemExit(f"R2 not found in {path}")
    j2 = tex.find("\\end{responsetable}", i2)
    i3 = tex.find(f"\\caption{{{r3_anchor}", j2)
    j3 = tex.find("\\end{responsetable}", i3)
    start = tex.rfind("\\begin{responsetable}", 0, i2)
    tex = tex[:start] + s4 + "\n\n" + tex[j3 + len("\\end{responsetable}") :]

    i4 = tex.find(f"\\caption{{{r4_anchor}")
    start4 = tex.rfind("\\begin{responsetable}", 0, i4)
    j4 = tex.find("\\end{responsetable}", i4)
    tex = tex[:start4] + s3 + "\n\n" + tex[j4 + len("\\end{responsetable}") :]

    for a, b in [
        ("表 R2–R3", "表 R2"),
        ("Tables R2–R3", "Table R2"),
        ("表 R2–R4", "表 R2 与 R4"),
        ("Tables R2–R4", "Tables R2 and R4"),
        ("\\textbf{表 R2–R3}", "\\textbf{表 R2}"),
        ("\\textbf{Tables R2–R3}", "\\textbf{Table R2}"),
    ]:
        tex = tex.replace(a, b)

    path.write_text(tex)
    print("patched", path.name)


def main() -> None:
    patch_file(GEN / "body_zh.tex", "zh")
    patch_file(GEN / "body_en.tex", "en")


if __name__ == "__main__":
    main()
