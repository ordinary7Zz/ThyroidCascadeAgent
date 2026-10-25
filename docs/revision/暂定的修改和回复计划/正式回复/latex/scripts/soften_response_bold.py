#!/usr/bin/env python3
"""Reduce \\textbf{} inside authorresponse blocks (blue prose); keep section label only."""
import re
from pathlib import Path

GENERATED = Path(__file__).resolve().parents[1] / "generated"


def should_keep_bold(inner: str, lang: str) -> bool:
    s = inner.strip()
    if lang == "zh":
        return s.startswith("支撑材料")
    return s.startswith("Supporting material")


def strip_textbf_balanced(text: str, lang: str) -> str:
    marker = r"\textbf{"
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text.startswith(marker, i):
            j = i + len(marker)
            depth = 1
            start = j
            while j < n and depth:
                c = text[j]
                if c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                j += 1
            inner = text[start : j - 1]
            if should_keep_bold(inner, lang):
                out.append(text[i:j])
            else:
                out.append(inner)
            i = j
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def process_file(path: Path, lang: str) -> None:
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"(\\begin\{authorresponse\}|\\end\{authorresponse\})", text)
    out: list[str] = []
    in_response = False
    for part in parts:
        if part == r"\begin{authorresponse}":
            in_response = True
            out.append(part)
        elif part == r"\end{authorresponse}":
            in_response = False
            out.append(part)
        elif in_response:
            out.append(strip_textbf_balanced(part, lang))
        else:
            out.append(part)
    path.write_text("".join(out), encoding="utf-8")


def main() -> None:
    process_file(GENERATED / "body_zh.tex", "zh")
    process_file(GENERATED / "body_en.tex", "en")
    print("soften_response_bold: done")


if __name__ == "__main__":
    main()
