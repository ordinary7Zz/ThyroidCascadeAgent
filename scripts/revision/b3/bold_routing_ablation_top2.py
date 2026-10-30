#!/usr/bin/env python3
"""Mark rank-1 (bold) and rank-2 (underline) point estimates per cohort/metric in routing ablation LaTeX."""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TABLES = [
    REPO / "docs/revision/暂定的修改和回复计划/正式回复/latex/generated/routing_ablation_tables_zh.tex",
    REPO / "docs/revision/暂定的修改和回复计划/正式回复/latex/generated/routing_ablation_tables_en.tex",
]

INNER = r"\d+\.\d+(?: \([^)]+\))?"
ROW_RE = re.compile(
    rf"^(?P<prefix>.*? & .*? & .*? & )"
    rf"(?P<c3>(?:\\(?:textbf|routingbest|routingsecond)\{{)?(?P<v3>{INNER})(?:\}})?)"
    rf"(?P<mid> & )"
    rf"(?P<c4>(?:\\(?:textbf|underline|routingbest|routingsecond)\{{)?(?P<v4>{INNER})(?:\}})?)"
    rf"(?P<suffix> \\\\)\s*$"
)


def parse_point(inner: str) -> float:
    return float(inner.split()[0])


def mark_cell(inner: str, rank: int | None) -> str:
    if rank == 1:
        return f"\\routingbest{{{inner}}}"
    if rank == 2:
        return f"\\routingsecond{{{inner}}}"
    return inner


def rank_first_second(values: list[float], higher_is_better: bool) -> tuple[set[int], set[int]]:
    distinct = sorted(set(values), reverse=higher_is_better)
    if not distinct:
        return set(), set()
    best_val = distinct[0]
    second_val = distinct[1] if len(distinct) > 1 else None
    first = {i for i, v in enumerate(values) if v == best_val}
    second = (
        {i for i, v in enumerate(values) if v == second_val}
        if second_val is not None
        else set()
    )
    return first, second


def process_block(lines: list[str], col3_hi: bool, col4_hi: bool) -> list[str]:
    if len(lines) != 8:
        return lines
    groups = []
    for line in lines:
        m = ROW_RE.match(line)
        if not m:
            return lines
        groups.append(m)

    v3 = [parse_point(groups[i].group("v3")) for i in range(8)]
    v4 = [parse_point(groups[i].group("v4")) for i in range(8)]
    r3_first, r3_second = rank_first_second(v3, col3_hi)
    r4_first, r4_second = rank_first_second(v4, col4_hi)

    out = []
    for i, m in enumerate(groups):
        c3 = mark_cell(
            m.group("v3"),
            1 if i in r3_first else (2 if i in r3_second else None),
        )
        c4 = mark_cell(
            m.group("v4"),
            1 if i in r4_first else (2 if i in r4_second else None),
        )
        out.append(f"{m.group('prefix')}{c3}{m.group('mid')}{c4}{m.group('suffix')}")
    return out


def process_file(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    mode: str | None = None
    i = 0
    while i < len(lines):
        line = lines[i]
        if "\\label{tab_routing_ablation_seg}" in line:
            mode = "seg"
        elif "\\label{tab_routing_ablation_cls}" in line:
            mode = "cls"
        elif line.strip() == "\\end{responsepaginatedtable}":
            mode = None

        if mode and ROW_RE.match(line):
            block = []
            j = i
            while j < len(lines) and ROW_RE.match(lines[j]) and len(block) < 8:
                block.append(lines[j])
                j += 1
            if len(block) == 8:
                new = (
                    process_block(block, True, False)
                    if mode == "seg"
                    else process_block(block, True, True)
                )
                lines[i : i + 8] = new
                i += 8
                continue
        i += 1

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Updated {path}")


def main() -> None:
    for p in TABLES:
        process_file(p)


if __name__ == "__main__":
    main()
