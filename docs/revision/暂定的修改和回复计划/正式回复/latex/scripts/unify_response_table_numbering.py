#!/usr/bin/env python3
"""Shift response tables R4..R15 -> R3..R14; remove manuscript Table S* from the response letter."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated"
PATHS = [
    GENERATED / "body_zh.tex",
    GENERATED / "body_en.tex",
    GENERATED / "routing_ablation_tables_zh.tex",
    GENERATED / "routing_ablation_tables_en.tex",
    ROOT / "reviewer_response.sty",
]


def shift_table_numbers(text: str) -> str:
    """Close the R3 gap: old R4..R15 become R3..R14."""
    text = text.replace("R14--R15", "§R14R15§")
    text = text.replace("R13--R15", "§R13R15§")  # if any
    for old in range(15, 3, -1):
        new = old - 1
        text = text.replace(f"tab:R{old}b", f"§LBL{old}b§")
        text = text.replace(f"tab:R{old}", f"§LBL{old}§")
        text = text.replace(f"Table R{old} (continued)", f"§CAP{old}c§")
        text = text.replace(f"表 R{old}（续）", f"§CAP{old}c§")
        text = text.replace(f"Table R{old}", f"§CAP{old}§")
        text = text.replace(f"表 R{old}", f"§CAP{old}§")
        text = text.replace(f"Tables R{old}", f"§CAPS{old}§")
        text = text.replace(f"表 R{old}", f"§CAP{old}§")  # idempotent
    text = text.replace("§R14R15§", "R13--R14")
    text = text.replace("§R13R15§", "R13--R14")
    for old in range(15, 3, -1):
        new = old - 1
        text = text.replace(f"§LBL{old}b§", f"tab:R{new}b")
        text = text.replace(f"§LBL{old}§", f"tab:R{new}")
        text = text.replace(f"§CAP{old}c§", f"Table R{new} (continued)" if "§CAP" not in f"§CAP{old}c§" else "")
        # bilingual captions
        text = text.replace(f"§CAP{old}c§", f"__CAP{new}c__")
        text = text.replace(f"§CAP{old}§", f"__CAP{new}__")
        text = text.replace(f"§CAPS{old}§", f"Tables R{new}")
    # Fix caption placeholders (zh/en mixed in file)
    for new in range(3, 15):
        text = text.replace(f"__CAP{new}c__", f"表 R{new}（续）")  # zh files
        text = text.replace(f"__CAP{new}__", f"表 R{new}")  # zh - en fixed below
    # English files use Table R* — re-run shift on en with Table prefix only
    return text


def shift_table_numbers_en_fix(text: str) -> str:
    """After generic shift, restore English 'Table' captions where we wrote 表."""
    if "Response to Reviewer" not in text and "Reviewer 1" not in text:
        return text
    for n in range(3, 15):
        text = text.replace(f"表 R{n}（续）", f"Table R{n} (continued)")
        text = text.replace(f"表 R{n}", f"Table R{n}")
    return text


def strip_s_refs(text: str, is_zh: bool) -> str:
    text = text.replace("\\hypertarget{tab:R3}{}\n", "")
    text = re.sub(
        r"Supplementary Table S\d+[a-z]?\s*---\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"Supplementary Table S\d+[a-z]?\s*\([^)]*\)\s*---\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    if is_zh:
        text = text.replace(
            "版式与 $\\pm$ 报告方式与投稿 Supplementary Table~S4 一致",
            "版式与 $\\pm$ 报告方式与投稿稿分类外测补充表一致",
        )
        text = text.replace(
            "版式与 $\\pm$ 报告方式与投稿 Supplementary Table~S3 一致",
            "版式与 $\\pm$ 报告方式与投稿稿分割外测补充表一致",
        )
        text = re.sub(r"版式同投稿 Table S5", "版式同投稿稿恶性子任务外测表", text)
        text = re.sub(r"与投稿 Table S5 一致", "与投稿稿恶性子任务表一致", text)
    else:
        text = text.replace(
            "Layout and $\\pm$ reporting match the submitted Supplementary Table~S4",
            "Layout and $\\pm$ reporting match the submitted manuscript classification supplement",
        )
        text = text.replace(
            "Layout and $\\pm$ reporting match the submitted Supplementary Table~S3",
            "Layout and $\\pm$ reporting match the submitted manuscript segmentation supplement",
        )

    # After renumber: S3->R3, S4->R2, S5->R7, S6->manuscript stacking
    pairs = [
        ("Tables S3/S4", "Tables R3 and R2"),
        ("Table S3/S4", "Tables R3 and R2"),
        ("Tables S3--S4", "Tables R2 and R3"),
        ("Table S3--S4", "Tables R2 and R3"),
        ("Table S3--S5", "Tables R2, R3, and R7"),
        ("Supplementary Table S4", "Table R2"),
        ("Supplementary Table S3", "Table R3"),
        ("Supplementary Table S5", "Table R7"),
        ("Table S5b", "Table R7 (continued)"),
        ("Table S5a", "Table R7"),
        ("Table S5", "Table R7"),
        ("Tables S5", "Table R7"),
        ("Table S4", "Table R2"),
        ("Table S3", "Table R3"),
        ("Table S6", "the manuscript stepwise-stacking table"),
        ("表 S3/S4", "表 R3 与 R2"),
        ("表 S3--S5", "表 R2、R3 与 R7"),
        ("表 S4", "表 R2"),
        ("表 S3", "表 R3"),
        ("表 S6", "修订稿逐级叠加表"),
        ("（S5a）", "（OOF）"),
        ("（S5b）", "（外测）"),
        ("(S5a)", "(OOF)"),
        ("(S5b)", "(external test)"),
        ("(Table S4 protocol)", "(Table R2 protocol)"),
        ("（与 Table S4 协议一致）", "（与表 R2 协议一致）"),
        ("Table S4-aligned", "Table R2-aligned"),
        ("Table S4 protocol", "Table R2 protocol"),
        ("five Table S4 cohorts", "five Table R2 cohorts"),
        ("image-level Table S4", "image-level Table R2"),
        ("did not match Supplementary Table S4", "did not match Table R2"),
        ("与 Supplementary Table S4 不一致", "与 表 R2 不一致"),
        ("Table S4 五队列", "表 R2 五队列"),
        ("主文 Table S4", "表 R2"),
        ("Table S4 的", "表 R2 的"),
        ("与 Table S4 ", "与表 R2 "),
        ("与 Table S3", "与表 R3"),
        ("for Table S3/S4 ", "for Tables R3/R2 "),
        ("Table S3/S4 ", "Tables R3/R2 "),
        ("Table S3 summaries", "Table R3 summaries"),
        ("分割 Table S3", "分割表 R3"),
        ("Table S3 汇总", "表 R3 汇总"),
        ("完整 Table S3", "完整分割外测（表 R3）"),
        ("full Table S3", "full segmentation results (Table R3)"),
        ("Full Table S5 is", "Malignant-subtask results are in"),
        ("完整 Table S5", "恶性子任务完整结果（表 R7）"),
        ("while Table S5 shows", "while the submitted manuscript Table S5 shows"),
        ("而 Table S5 显示", "而送审稿 Table S5 显示"),
        ("submitted Supplementary Table S5 OOF layout", "submitted malignant-subtask OOF layout"),
        ("投稿 Supplementary Table S5 OOF", "投稿稿恶性子任务 OOF"),
        ("Table S5 narrative", "Table R7 narrative"),
        ("Table S5 protocol", "Table R7 protocol"),
        ("Table S5 wording", "Table R7 wording"),
        ("Table S5 叙事", "表 R7 叙事"),
        ("Table S5 协议", "表 R7 协议"),
        ("Table S5 用语", "表 R7 用语"),
        ("in Table S6", "in the manuscript stepwise-stacking table"),
        ("Table S6 ", "修订稿逐级叠加表 "),
        ("discussed with Table S6", "discussed with the manuscript stepwise-stacking results"),
        ("在 Table S6", "在修订稿逐级叠加"),
        ("Table S6 separately", "in the manuscript separately"),
        ("Table S6 逐级", "修订稿逐级"),
        ("Table R2 (Supplementary Table S4, AUROC/AUPRC), and Table R3 (Supplementary Table S3, segmentation Dice/HD95)", "Table R2 (classification, AUROC/AUPRC) and Table R3 (segmentation, Dice/HD95)"),
        ("表 R2（Supplementary Table S4，AUROC/AUPRC）、表 R3（Supplementary Table S3，分割 Dice/HD95）", "表 R2（良恶性分类，AUROC/AUPRC）、表 R3（结节分割，Dice/HD95）"),
        ("Table R7 (Supplementary Table S5a/S5b)", "Table R7 (malignant-subtask OOF and external tests)"),
        ("表 R7（Supplementary Table S5a/S5b）", "表 R7（恶性子任务 OOF 与外测）"),
        ("与 表 R1--R4 对齐", "与 表 R1--R3 对齐"),
        ("Table R1--R4", "Tables R1--R3"),
        ("表 R1--R4", "表 R1--R3"),
        ("Table R8（S5a）", "Table R7 (OOF)"),
        ("表 R8（S5a）", "表 R7（OOF）"),
        (" (S5b)", " (external test)"),
    ]
    for a, b in pairs:
        text = text.replace(a, b)

    text = text.replace("labels \\textbf{R1--R15}", "labels \\textbf{R1--R14}")
    text = text.replace("编号 \\textbf{R1--R15}", "编号 \\textbf{R1--R14}")
    text = re.sub(
        r"Entries aligned with revised Supplementary Tables S3--S5 retain the manuscript table numbers\.",
        "Tables and figures use response-letter labels \\textbf{R1--R14} and \\textbf{Figures R1--R2} only.",
        text,
    )
    text = re.sub(
        r"与修订稿 Supplementary Tables S3--S5 对齐者保留原表号。",
        "表图编号仅使用本信 \\textbf{R1--R14}、\\textbf{图 R1--R2}，不复用稿件补充表序号。",
        text,
    )
    return text


def main() -> None:
    for path in PATHS:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        is_zh = "body_zh" in path.name or "tables_zh" in path.name or "responseappendixzh" in text
        text = shift_table_numbers(text)
        if path.name == "body_en.tex" or path.name == "routing_ablation_tables_en.tex":
            text = shift_table_numbers_en_fix(text)
        if path.suffix == ".sty":
            is_zh = True  # both langs in sty
        text = strip_s_refs(text, is_zh=is_zh or "zh" in path.name)
        path.write_text(text, encoding="utf-8")
        print("updated", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
