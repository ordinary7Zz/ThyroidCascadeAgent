#!/usr/bin/env python3
"""Optional one-way import: Markdown drafts → latex/generated/body_*.tex.

The project now edits TeX directly; running this overwrites body_*.tex. Use only
if you intentionally re-import from REVIEWER_RESPONSE_DRAFT_*.md.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SPECIAL = str.maketrans(
    {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
)


def escape_latex(text: str, allow_math: bool = False) -> str:
    """Escape LaTeX special characters; preserve existing backslash commands."""
    if not text:
        return ""
    parts: list[str] = []
    i = 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text) and text[i + 1].isalpha():
            j = i + 1
            while j < len(text) and text[j].isalpha():
                j += 1
            parts.append(text[i:j])
            i = j
            continue
        parts.append(text[i].translate(SPECIAL))
        i += 1
    return "".join(parts)


def inline_md_to_latex(line: str, _depth: int = 0) -> str:
    """Bold, italic, code, links (non-recursive regex on long lines)."""
    if _depth > 8:
        return line.translate(SPECIAL)

    s = line

    def link_repl(m: re.Match[str]) -> str:
        label = inline_md_to_latex(m.group(1), _depth + 1)
        url = m.group(2).replace("_", r"\_")
        return rf"\href{{{url}}}{{{label}}}"

    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link_repl, s)

    def code_repl(m: re.Match[str]) -> str:
        inner = m.group(1).translate(SPECIAL)
        return rf"\texttt{{{inner}}}"

    s = re.sub(r"`([^`]+)`", code_repl, s)

    def bold_repl(m: re.Match[str]) -> str:
        inner = inline_md_to_latex(m.group(1), _depth + 1)
        return rf"\textbf{{{inner}}}"

    s = re.sub(r"\*\*([^*]+)\*\*", bold_repl, s)

    def italic_repl(m: re.Match[str]) -> str:
        inner = inline_md_to_latex(m.group(1), _depth + 1)
        return rf"\textit{{{inner}}}"

    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", italic_repl, s)

    return _escape_plain_latex(s)


def _escape_plain_latex(s: str) -> str:
    """Escape characters outside LaTeX commands and {...} groups."""
    out: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        if s[i] == "\\":
            j = i + 1
            while j < n and s[j].isalpha():
                j += 1
            if j < n and s[j] == "{":
                depth = 1
                k = j + 1
                while k < n and depth:
                    if s[k] == "{":
                        depth += 1
                    elif s[k] == "}":
                        depth -= 1
                    k += 1
                out.append(s[i:k])
                i = k
                continue
            out.append(s[i:j])
            i = j
            continue
        if s[i] == "{":
            depth = 1
            j = i + 1
            while j < n and depth:
                if s[j] == "{":
                    depth += 1
                elif s[j] == "}":
                    depth -= 1
                j += 1
            out.append(s[i:j])
            i = j
            continue
        out.append(s[i].translate(SPECIAL))
        i += 1
    return "".join(out)


def is_table_row(line: str) -> bool:
    t = line.strip()
    return t.startswith("|") and t.endswith("|")


def is_table_sep(line: str) -> bool:
    t = line.strip()
    if not is_table_row(t):
        return False
    inner = t.strip("|").replace(" ", "")
    return bool(re.fullmatch(r"[\|\-:]+", inner.replace("|", ""))) or all(
        re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) for c in t.strip("|").split("|")
    )


def parse_table_row(line: str) -> list[str]:
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return cells


def table_to_latex(rows: list[list[str]], caption: str | None = None) -> str:
    if not rows:
        return ""
    ncol = max(len(r) for r in rows)
    colspec = "l" * ncol
    if ncol >= 5:
        colspec = "l" + "c" * (ncol - 1)

    lines = [
        r"\begin{responsetable}",
        r"\begin{adjustbox}{max width=\textwidth}",
        rf"\begin{{tabular}}{{{colspec}}}",
        r"\toprule",
    ]
    for i, row in enumerate(rows):
        while len(row) < ncol:
            row.append("")
        cells = [inline_md_to_latex(c) for c in row]
        lines.append(" & ".join(cells) + r" \\")
        if i == 0:
            lines.append(r"\midrule")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{adjustbox}"])
    if caption:
        lines.append(rf"\caption*{{{inline_md_to_latex(caption)}}}")
    lines.append(r"\end{responsetable}")
    return "\n".join(lines) + "\n"


def md_to_latex_body(md_text: str) -> str:
    # Em dash confuses some CJK fonts under XeLaTeX; use LaTeX em-dash command.
    md_text = md_text.replace("\u2014", "---")
    lines = md_text.splitlines()
    out: list[str] = []
    i = 0
    in_ul = False
    in_code = False
    code_buf: list[str] = []
    pending_table_caption: str | None = None

    def close_ul():
        nonlocal in_ul
        if in_ul:
            out.append(r"\end{itemize}")
            in_ul = False

    while i < len(lines):
        line = lines[i]
        raw = line.rstrip()

        if raw.strip() == "---":
            close_ul()
            out.append(r"\bigskip\hrule\bigskip")
            i += 1
            continue

        if raw.startswith("```"):
            close_ul()
            if in_code:
                out.append(r"\begin{promptverbatim}")
                out.extend(code_buf)
                out.append(r"\end{promptverbatim}")
                code_buf = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue

        if in_code:
            code_buf.append(line)
            i += 1
            continue

        if not raw.strip():
            close_ul()
            i += 1
            continue

        if is_table_row(raw):
            close_ul()
            table_rows: list[list[str]] = []
            while i < len(lines) and is_table_row(lines[i].strip()):
                row_line = lines[i].strip()
                if not is_table_sep(row_line):
                    table_rows.append(parse_table_row(row_line))
                i += 1
            out.append(table_to_latex(table_rows, pending_table_caption))
            pending_table_caption = None
            continue

        img = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", raw.strip())
        if img:
            close_ul()
            alt, path = img.group(1), img.group(2)
            path_tex = path.replace("\\", "/")
            if path_tex.startswith("figures/"):
                path_tex = path_tex[len("figures/") :]
            out.append(r"\begin{figure}[htbp]")
            out.append(r"\centering")
            out.append(rf"\includegraphics[width=0.92\textwidth]{{{path_tex}}}")
            if alt:
                out.append(rf"\caption*{{{inline_md_to_latex(alt)}}}")
            out.append(r"\end{figure}")
            i += 1
            continue

        if raw.startswith("# "):
            close_ul()
            title = inline_md_to_latex(raw[2:].strip())
            out.append(rf"\begin{{center}}{{\Large\bfseries {title}}}\end{{center}}")
            out.append(r"\vspace{0.6em}")
            i += 1
            continue

        if raw.startswith("## "):
            close_ul()
            title = inline_md_to_latex(raw[3:].strip())
            out.append(rf"\reviewersection{{{title}}}")
            i += 1
            continue

        if raw.startswith("#### "):
            close_ul()
            title = inline_md_to_latex(raw[5:].strip())
            out.append(rf"\reviewersubtitle{{{title}}}")
            i += 1
            continue

        if raw.startswith("**审稿意见：**") or raw.startswith("**Reviewer comment:**"):
            close_ul()
            rest = raw.split("：", 1)[-1].split(":", 1)[-1].strip()
            out.append(r"\begin{reviewercomment}")
            if rest:
                out.append(inline_md_to_latex(rest))
                out.append(r"\par")
                i += 1
            else:
                i += 1
                while i < len(lines) and lines[i].strip() and not lines[i].startswith("**"):
                    out.append(inline_md_to_latex(lines[i].strip()))
                    out.append(r"\par")
                    i += 1
            out.append(r"\end{reviewercomment}")
            continue

        if raw.startswith("**回复：**") or raw.startswith("**Response:**"):
            close_ul()
            out.append(r"\begin{authorresponse}")
            i += 1
            continue

        if raw.startswith("**支撑材料：**") or raw.startswith("**Supporting material:**"):
            close_ul()
            out.append(inline_md_to_latex(raw))
            out.append(r"\par")
            i += 1
            continue

        if raw.startswith("**支撑图表**") or raw.startswith("**Supporting tables and figures**"):
            close_ul()
            if out and out[-1] == r"\begin{authorresponse}":
                out.append(r"\end{authorresponse}")
            elif r"\begin{authorresponse}" in out and r"\end{authorresponse}" not in "".join(out[-20:]):
                out.append(r"\end{authorresponse}")
            out.append(r"\begin{supportingblock}")
            i += 1
            continue

        if raw.startswith("# 回复信支撑图表") or raw.startswith("# Supporting Figures and Tables"):
            close_ul()
            if out and out[-1] == r"\begin{authorresponse}":
                out.append(r"\end{authorresponse}")
            out.append(r"\section{Supporting figures and tables}")
            i += 1
            continue

        if raw.startswith("- "):
            if not in_ul:
                if out and out[-1] == r"\begin{authorresponse}":
                    pass
                out.append(r"\begin{itemize}")
                in_ul = True
            item = inline_md_to_latex(raw[2:].strip())
            out.append(rf"\item {item}")
            i += 1
            continue

        if raw.startswith("**") and raw.endswith("**") and raw.count("**") == 2:
            close_ul()
            out.append(inline_md_to_latex(raw))
            out.append(r"\par")
            i += 1
            continue

        close_ul()
        if out and out[-1] == r"\begin{authorresponse}":
            pass
        elif out and out[-1] == r"\begin{supportingblock}":
            pending_table_caption = raw.strip()
        else:
            out.append(inline_md_to_latex(raw))
            out.append(r"\par")

        i += 1

    close_ul()
    if out and out[-1] == r"\begin{authorresponse}":
        out.append(r"\end{authorresponse}")
    if out and out[-1] == r"\begin{supportingblock}":
        out.append(r"\end{supportingblock}")

    # Close dangling environments
    text = "\n".join(out)
    for env in ("authorresponse", "supportingblock", "reviewercomment"):
        opens = text.count(rf"\begin{{{env}}}")
        closes = text.count(rf"\end{{{env}}}")
        for _ in range(opens - closes):
            text += f"\n\\end{{{env}}}"
    return text + "\n"


def build_main_tex(body: str, lang: str, title: str) -> str:
    if lang == "zh":
        doc_class = r"\documentclass[11pt,a4paper]{ctexart}"
        fonts = r"""
\setCJKmainfont{WenQuanYi Micro Hei}
\setCJKsansfont{WenQuanYi Micro Hei}
\setCJKmonofont{WenQuanYi Micro Hei Mono}
"""
        comment_label = r"\renewcommand{\ReviewerCommentLabel}{审稿意见：}"
        response_label = r"\renewcommand{\ResponseLabel}{回复：}"
        supporting_label = r"\renewcommand{\SupportingLabel}{支撑图表}"
    else:
        doc_class = r"\documentclass[11pt,a4paper]{article}"
        fonts = r"\setmainfont{TeX Gyre Termes}"
        comment_label = response_label = supporting_label = ""

    return f"""{doc_class}
\\usepackage{{reviewer_response}}
{fonts}
{comment_label}
{response_label}
{supporting_label}

\\title{{{escape_latex(title)}}}
\\date{{}}

\\begin{{document}}
\\maketitle
\\tableofcontents
\\bigskip

{body}

\\end{{document}}
"""


def convert_file(md_path: Path, out_body: Path, out_main: Path | None, lang: str) -> None:
    md_text = md_path.read_text(encoding="utf-8")
    body = md_to_latex_body(md_text)
    out_body.parent.mkdir(parents=True, exist_ok=True)
    out_body.write_text(body, encoding="utf-8")

    if out_main:
        first_line = md_text.splitlines()[0].lstrip("# ").strip() if md_text else "Response"
        main = build_main_tex(
            rf"\input{{{out_body.name}}}",
            lang=lang,
            title=first_line,
        )
        # Use relative input from main tex directory
        main = main.replace(
            rf"\input{{{out_body.name}}}",
            rf"\input{{generated/{out_body.name}}}",
        )
        out_main.write_text(main, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert reviewer response MD to LaTeX")
    parser.add_argument(
        "--base",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="正式回复 directory",
    )
    args = parser.parse_args()
    base = args.base
    latex_dir = base / "latex"

    pairs = [
        (base / "REVIEWER_RESPONSE_DRAFT_EN.md", "body_en.tex", "REVIEWER_RESPONSE_EN.tex", "en"),
        (base / "REVIEWER_RESPONSE_DRAFT_ZH.md", "body_zh.tex", "REVIEWER_RESPONSE_ZH.tex", "zh"),
    ]
    for md_path, body_name, main_name, lang in pairs:
        if not md_path.exists():
            print(f"Missing {md_path}", file=sys.stderr)
            return 1
        convert_file(
            md_path,
            latex_dir / "generated" / body_name,
            latex_dir / main_name,
            lang,
        )
        print(f"Wrote {latex_dir / main_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
