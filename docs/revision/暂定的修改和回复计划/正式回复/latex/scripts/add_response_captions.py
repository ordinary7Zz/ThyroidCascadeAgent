#!/usr/bin/env python3
"""Add standard \\caption/\\label and tablenotes to response-letter floats."""
import re
from pathlib import Path

LATEX = Path(__file__).resolve().parents[1]
GENERATED = LATEX / "generated"


def appendix_split(text: str) -> tuple[str, str]:
    for marker in (
        r"\begin{center}{\Large\bfseries 回复信支撑图表",
        r"\begin{center}{\Large\bfseries Supporting Figures and Tables",
    ):
        idx = text.find(marker)
        if idx != -1:
            return text[:idx], text[idx:]
    return text, ""


def convert_appendix_header(appendix: str, lang: str) -> str:
    if lang == "zh":
        appendix = re.sub(
            r"\\begin\{center\}\{\\Large\\bfseries 回复信支撑图表[^}]*\}\\end\{center\}\s*\\vspace\{0\.6em\}",
            r"\\responseappendixzh\n\\vspace{0.35em}",
            appendix,
            count=1,
        )
    else:
        appendix = re.sub(
            r"\\begin\{center\}\{\\Large\\bfseries Supporting Figures and Tables for This Response\}\\end\{center\}\s*\\vspace\{0\.6em\}",
            r"\\responseappendix\n\\vspace{0.35em}",
            appendix,
            count=1,
        )
    return appendix


def label_key(kind: str, body: str) -> str:
    m = re.search(r"\bR(\d+)\b", body)
    if m and kind in ("Table", "表", "Figure", "图"):
        prefix = "tab" if kind in ("Table", "表") else "fig"
        return f"{prefix}:R{m.group(1)}"
    m = re.search(r"Appendix (A\d+)", body)
    if m:
        return f"app:{m.group(1)}"
    return ""


def merge_table_r4(appendix: str, lang: str) -> str:
    """One float for Dice + HD95 with a single caption."""
    if lang == "zh":
        pat = (
            r"\\reviewersection\{表 R4\. Supplementary Table S3 --- 跨数据集结节分割\}\s*"
            r"表注：[^\n]+\s*\\par\s*"
            r"\\textbf\{Dice（\\% ↑）\}\s*\\par\s*"
            r"\\begin\{responsetable\}"
        )
        cap = "表 R4. Supplementary Table S3 — 跨数据集结节分割"
        note = (
            "\\textbf{Dice} 为 \\textbf{\\%}（$\\uparrow$），\\textbf{HD95} 为 \\textbf{mm}（$\\downarrow$）；"
            "数值为点估计 \\textbf{±} 95\\% CI 半宽（cluster bootstrap，1000 次，seed=42，图像级）。"
        )
        sub_dice = "\\textbf{Dice（\\% $\\uparrow$）}"
        sub_hd = "\\textbf{HD95（mm $\\downarrow$）}"
    else:
        pat = (
            r"\\reviewersection\{Table R4\. Supplementary Table S3 --- Cross-dataset nodule segmentation\}\s*"
            r"Note: [^\n]+\s*\\par\s*"
            r"\\textbf\{Dice \(\\% \$\\uparrow\$\)\}\s*\\par\s*"
            r"\\begin\{responsetable\}"
        )
        cap = "Table R4. Supplementary Table S3 — Cross-dataset nodule segmentation"
        note = (
            "\\textbf{Dice} in \\textbf{\\%} ($\\uparrow$), \\textbf{HD95} in \\textbf{mm} ($\\downarrow$); "
            "point estimate $\\pm$ half-width of 95\\% CI (cluster bootstrap, 1000 resamples, seed=42, image-level)."
        )
        sub_dice = "\\textbf{Dice (\\% $\\uparrow$)}"
        sub_hd = "\\textbf{HD95 (mm $\\downarrow$)}"

    if not re.search(pat, appendix):
        return appendix

    appendix = re.sub(
        pat,
        (
            "\\begin{responsetable}\n"
            f"\\caption{{{cap}}}\n"
            "\\label{tab:R4}\n"
            f"\\responsetablenote{{{note}}}\n"
            f"{sub_dice}\n"
            "\\par\\vspace{0.35em}\n"
        ),
        appendix,
        count=1,
    )
    # Remove second float wrapper around HD95 block
    appendix = re.sub(
        r"\\end\{responsetable\}\s*\n\s*\\textbf\{HD95[^}]+\}\s*\\par\s*\\begin\{responsetable\}",
        f"\\par\\vspace{0.65em}\n{sub_hd}\n\\par\\vspace{0.35em}\n",
        appendix,
        count=1,
    )
    return appendix


def process_appendix(appendix: str, lang: str) -> str:
    appendix = convert_appendix_header(appendix, lang)
    appendix = merge_table_r4(appendix, lang)

    lines = appendix.splitlines(keepends=True)
    out: list[str] = []
    pending_caption: str | None = None
    pending_label: str | None = None

    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(
            r"^\\reviewersection\{(?P<kind>表|图|Table|Figure|Appendix) (?P<body>[^}]+)\}\s*$",
            line.strip(),
        )
        if m:
            kind, body = m.group("kind"), m.group("body")
            if kind == "Appendix":
                out.append(f"\\subsection*{{Appendix {body}}}\n")
                if body.startswith("A"):
                    out.append(f"\\label{{app:{body.split('.')[0].replace(' ', '')}}}\n")
                pending_caption = None
                pending_label = None
            else:
                pending_caption = f"{kind} {body}" if kind in ("表", "图") else f"{kind} {body}"
                # normalise en Table/Figure prefix already in body
                pending_label = label_key(kind, body)
            i += 1
            continue

        if line.strip() == r"\begin{responsetable}":
            out.append(line)
            if pending_caption:
                out.append(f"\\caption{{{pending_caption}}}\n")
                if pending_label:
                    out.append(f"\\label{{{pending_label}}}\n")
                pending_caption = None
                pending_label = None
            i += 1
            continue

        if line.strip() in (r"\begin{figure}", r"\begin{responsefigure}"):
            out.append(r"\begin{responsefigure}" + "\n")
            if pending_caption:
                out.append(f"\\caption{{{pending_caption}}}\n")
                if pending_label:
                    out.append(f"\\label{{{pending_label}}}\n")
                pending_caption = None
                pending_label = None
            i += 1
            continue

        if line.strip() == r"\end{figure}":
            out.append(r"\end{responsefigure}" + "\n")
            i += 1
            continue

        # Drop redundant \caption* when we already injected caption
        if line.strip().startswith(r"\caption*{") and pending_caption is None:
            # keep if no caption yet — convert star to regular
            out.append(line.replace(r"\caption*{", r"\caption{", 1))
            i += 1
            continue

        out.append(line)
        i += 1

    text = "".join(out)
    text = attach_trailing_table_notes(text)
    text = collapse_duplicate_cluster_bootstrap_notes(text, lang)
    return text


def attach_trailing_table_notes(text: str) -> str:
    """Move prose immediately after \\end{responsetable} into tablenotes."""

    def repl(m: re.Match) -> str:
        note = m.group(1).strip()
        if not note or note.startswith("\\") or note.startswith("%"):
            return m.group(0)
        # skip panel sub-headers already inside merged R4
        if note.startswith("\\textbf{") and ("Dice" in note or "HD95" in note):
            return m.group(0)
        note_one = " ".join(note.split())
        return f"\\responsetablenote{{{note_one}}}\n\\end{{responsetable}}\n"

    return re.sub(
        r"\\end\{responsetable\}\s*\n+((?:[^\n\\%].+\n)+?)(?=\n\\(?:reviewersection|subsection|responseappendix|begin\{))",
        repl,
        text,
        flags=re.MULTILINE,
    )


def collapse_duplicate_cluster_bootstrap_notes(text: str, lang: str) -> str:
    zh = "均为 cluster-bootstrap 95\\% CI（1000 次，seed 42）。"
    en = "Cluster-bootstrap 95\\% CIs (1000 resamples, seed 42)."
    note = zh if lang == "zh" else en
    # If standalone after table, fold into tablenotes (already handled). Remove duplicate orphan lines between tables.
    text = re.sub(
        rf"\n{re.escape(note)}\s*\\par\s*(?=\\reviewersection|\\begin{{responsetable}})",
        "\n",
        text,
    )
    # Append to Table R3 float if missing
    if note not in text:
        return text
    return text


def process_file(path: Path, lang: str) -> None:
    text = path.read_text(encoding="utf-8")
    head, appendix = appendix_split(text)
    if not appendix:
        print(f"skip {path.name}: no appendix")
        return
    appendix = process_appendix(appendix, lang)
    path.write_text(head + appendix, encoding="utf-8")
    print(f"updated {path.name}")


def main():
    process_file(GENERATED / "body_zh.tex", "zh")
    process_file(GENERATED / "body_en.tex", "en")


if __name__ == "__main__":
    main()
