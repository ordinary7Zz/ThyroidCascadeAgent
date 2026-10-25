#!/usr/bin/env python3
"""Replace hardcoded Table R* / Figure R* with \\responsetableref / \\responsefigureref; normalize \\label keys."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated"
FILES = [
    GENERATED / "body_en.tex",
    GENERATED / "body_zh.tex",
    GENERATED / "routing_ablation_tables_en.tex",
    GENERATED / "routing_ablation_tables_zh.tex",
]


def normalize_labels(text: str) -> str:
    text = re.sub(r"\\label\{tab:R(\d+)b\}", r"\\label{tabR\1b}", text)
    text = re.sub(r"\\label\{tab:R(\d+)\}", r"\\label{tabR\1}", text)
    text = re.sub(r"\\label\{fig:R(\d+)\}", r"\\label{figR\1}", text)
    return text


def migrate_captions(text: str) -> str:
    text = re.sub(
        r"\\caption\{(Table R(\d+) \(continued\))\.\s*",
        r"\\caption{\\responsetabletitle{tabR\1b}{",
        text,
    )
    text = re.sub(
        r"\\caption\{(表 R(\d+)（续）)\.\s*",
        r"\\caption{\\responsetabletitle{tabR\1b}{",
        text,
    )
    text = re.sub(
        r"\\caption\{(Table R(\d+))\.\s*",
        r"\\caption{\\responsetabletitle{tabR\1}{",
        text,
    )
    text = re.sub(
        r"\\caption\{(表 R(\d+))\.\s*",
        r"\\caption{\\responsetabletitle{tabR\1}{",
        text,
    )
    text = re.sub(
        r"\\captionof\{table\}\{(表 R(\d+))\.\s*",
        r"\\captionof{table}{\\responsetabletitle{tabR\1}{",
        text,
    )
    text = re.sub(
        r"\\captionof\{table\}\{(Table R(\d+))\.\s*",
        r"\\captionof{table}{\\responsetabletitle{tabR\1}{",
        text,
    )
    # Close extra brace before \end{responsetable} / manuscript / longtable (caption ends with single })
    # Captions now: \caption{\responsetabletitle{tab_dhash}{TITLE}} — need one } before final }
    def close_title(m: re.Match) -> str:
        s = m.group(0)
        if s.rstrip().endswith("}}"):
            return s
        if s.rstrip().endswith("}"):
            return s[:-1] + "}}"
        return s

    text = re.sub(
        r"\\caption\{\\responsetabletitle\{tabR[^}]+\}\{[^}]*(?:\{[^}]*\}[^}]*)*\}",
        close_title,
        text,
        flags=re.DOTALL,
    )
    return text


def migrate_refs(text: str) -> str:
    if "\\responsetableref{" in text and "Table R1)" not in text:
        pass
    pairs = [
        (r"Table R7 \(continued\)", r"\\responsetableref{tab_malig_ext}"),
        (r"表 R7（续）", r"\\responsetableref{tab_malig_ext}"),
        (r"Tables R13--R14", r"\\responsetablerefrange{tab_routing_ablation_seg}{tab_routing_ablation_cls}"),
        (r"表 R13--R14", r"\\responsetablerefrange{tab_routing_ablation_seg}{tab_routing_ablation_cls}"),
        (r"Tables R8 and R9", r"\\responsetableref{tab_patient_cls} and \\responsetableref{tab_patient_seg}"),
        (r"Tables R6 and R2", r"\\responsetableref{tab_cls_macro_mean} and \\responsetableref{tab_cls_ext}"),
        (r"Tables R2 and R3", r"\\responsetableref{tab_cls_ext} and \\responsetableref{tab_seg_ext}"),
        (r"Tables R3 and R2", r"\\responsetableref{tab_seg_ext} and \\responsetableref{tab_cls_ext}"),
        (r"Tables R2, R3, and R7", r"\\responsetableref{tab_cls_ext}, \\responsetableref{tab_seg_ext}, and \\responsetableref{tab_malig_oof}"),
        (r"Figures R1--R2", r"\\responsefigurerefrange{fig_reliability}{fig_risk_coverage}"),
        (r"图 R1--R2", r"\\responsefigurerefrange{fig_reliability}{fig_risk_coverage}"),
        (r"Figure R1", r"\\responsefigureref{fig_reliability}"),
        (r"Figure R2", r"\\responsefigureref{fig_risk_coverage}"),
        (r"图 R1", r"\\responsefigureref{fig_reliability}"),
        (r"图 R2", r"\\responsefigureref{fig_risk_coverage}"),
        (r"Table R2-aligned", r"\\responsetableref{tab_cls_ext}-aligned"),
        (r"表 R8、表 R9", r"\\responsetableref{tab_patient_cls}、\\responsetableref{tab_patient_seg}"),
        (r"表 R6 与 表 R2", r"\\responsetableref{tab_cls_macro_mean} 与 \\responsetableref{tab_cls_ext}"),
        (r"表 R2 与 R4", r"\\responsetableref{tab_cls_ext} 与 \\responsetableref{tab_calib_referral}"),
        (r"表 R7 与 表 R7（续）", r"\\responsetableref{tab_malig_oof} 与 \\responsetableref{tab_malig_ext}"),
        (r"Table R7 and Table R7 \(continued\)", r"\\responsetableref{tab_malig_oof} and \\responsetableref{tab_malig_ext}"),
        (r"完整 Tables R3 and R2", r"\\responsetableref{tab_seg_ext} 与 \\responsetableref{tab_cls_ext}"),
    ]
    for a, b in pairs:
        text = text.replace(a, b)
    for n in range(14, 0, -1):
        text = re.sub(rf"\bTable R{n}\b", rf"\\responsetableref{{tabR{n}}}", text)
        text = re.sub(rf"表 R{n}", rf"\\responsetableref{{tabR{n}}}", text)
    # Fix double-wrapped
    text = text.replace("\\responsetableref{tabR", "\\responsetableref{tabR")
    text = re.sub(
        r"\\responsetableref\{tabR(\d+)\}\\responsetableref",
        r"\\responsetableref{tabR\1}",
        text,
    )
    return text


def fix_caption_braces(text: str) -> str:
    """Ensure \\caption{\\responsetabletitle{key}{title}} has closing double brace."""
    lines = text.splitlines()
    out = []
    for line in lines:
        if "\\caption{\\responsetabletitle{" in line and line.count("{") > line.count("}"):
            line = line + "}"
        if "\\captionof{table}{\\responsetabletitle{" in line and line.count("{") > line.count("}"):
            line = line + "}"
        out.append(line)
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def process(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = normalize_labels(text)
    text = migrate_captions(text)
    text = fix_caption_braces(text)
    text = migrate_refs(text)
    path.write_text(text, encoding="utf-8")
    print("migrated", path.relative_to(ROOT))


def main() -> None:
    for p in FILES:
        if p.exists():
            process(p)


if __name__ == "__main__":
    main()
