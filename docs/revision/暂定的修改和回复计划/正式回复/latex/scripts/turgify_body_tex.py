#!/usr/bin/env python3
"""TURG-like structure: comment headings, reviewer blocks, fix ZH comment envs."""
import re
from pathlib import Path

GENERATED = Path(__file__).resolve().parents[1] / "generated"


def strip_title_preamble(text: str) -> str:
    text = re.sub(
        r"\\begin\{center\}\{\\Large\\bfseries[^}]+\}\\end\{center\}\s*"
        r"\\vspace\{0\.6em\}\s*"
        r"(?:Manuscript:|手稿：)[^\n]*\n\\par\s*",
        "",
        text,
        count=1,
    )
    return text


def remove_hrules(text: str) -> str:
    return text.replace("\\bigskip\\hrule\\bigskip\n", "")


def fix_zh_broken_comments(text: str) -> str:
    # ** placeholder inside empty reviewercomment + text outside
    pattern = re.compile(
        r"\\begin\{reviewercomment\}\s*\*\*\s*\\par\s*\\end\{reviewercomment\}\s*"
        r"(.*?)\s*\\par\s*\\begin\{authorresponse\}",
        re.DOTALL,
    )
    text = pattern.sub(
        r"\\begin{reviewercomment}\n\1\n\\end{reviewercomment}\n\\begin{authorresponse}",
        text,
    )
    # R2.21 editor block without reviewercomment
    text = text.replace(
        "\\reviewersection{审稿人 2 --- 意见 21（R2.21）}\n"
        "\\textbf{审稿意见（编辑部原文，无分条）：}\n\\par\n"
        "基于 AutoGluon 的放射组学分支描述不足。\n\\par\n"
        "\\begin{authorresponse}",
        "\\reviewersection{审稿人 2，意见 21（R2.21）}\n"
        "\\begin{reviewercomment}\n"
        "基于 AutoGluon 的放射组学分支描述不足。\n"
        "\\end{reviewercomment}\n\\begin{authorresponse}",
    )
    return text


def normalize_section_title(title: str, lang: str) -> str:
    if lang == "en":
        title = title.replace(" --- ", ", ")
        title = re.sub(r"^Reviewer (\d+), General remark", r"Reviewer \1, General remark", title)
        return title
    title = title.replace(" --- ", "，")
    return title


def insert_reviewer_blocks(text: str, lang: str) -> str:
    if lang == "en":
        block_tpl = "\\responsetoreviewer{{Response to Reviewer {n}}}\n"
        pat = re.compile(r"\\reviewersection\{(Reviewer (\d+)[^}]+)\}")
    else:
        block_tpl = "\\responsetoreviewer{{对审稿人 {n} 的回复}}\n"
        pat = re.compile(r"\\reviewersection\{(审稿人 (\d+)[^}]+)\}")

    last_n = None
    out = []
    pos = 0
    for m in pat.finditer(text):
        n = m.group(2)
        if n != last_n:
            out.append(text[pos : m.start()])
            out.append(block_tpl.format(n=n))
            last_n = n
        else:
            out.append(text[pos : m.start()])
        inner = normalize_section_title(m.group(1), lang)
        out.append(f"\\reviewersection{{{inner}}}")
        pos = m.end()
    out.append(text[pos:])
    return "".join(out)


def process(path: Path, lang: str) -> None:
    text = path.read_text(encoding="utf-8")
    text = strip_title_preamble(text)
    text = remove_hrules(text)
    if lang == "zh":
        text = fix_zh_broken_comments(text)
    text = insert_reviewer_blocks(text, lang)
    path.write_text(text, encoding="utf-8")
    print(f"Updated {path.name}")


def main() -> None:
    process(GENERATED / "body_en.tex", "en")
    process(GENERATED / "body_zh.tex", "zh")


if __name__ == "__main__":
    main()
