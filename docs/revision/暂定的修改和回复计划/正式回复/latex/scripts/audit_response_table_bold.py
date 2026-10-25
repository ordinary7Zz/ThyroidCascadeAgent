#!/usr/bin/env python3
"""Audit \\textbf on point estimates: bold = column-best per metric block (↑ max, ↓ min)."""
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

GENERATED = Path(__file__).resolve().parents[1] / "generated"

SECTION_SPECS = [
    (re.compile(r"\\textit\{AUROC", re.I), True),
    (re.compile(r"\\textit\{AUPRC", re.I), True),
    (re.compile(r"\\textit\{Dice", re.I), True),
    (re.compile(r"\\textit\{HD95", re.I), False),
]


def parse_point(cell: str) -> Optional[float]:
    cell = cell.strip()
    if not cell or cell in ("---", "—"):
        return None
    plain = cell.replace("\\textbf{", "").replace("}", "")
    m = re.search(r"([\d.]+)\s*(?:\\pm|\$\\pm\$|±)", plain)
    if not m:
        m = re.search(r"([\d.]+)", plain)
    return float(m.group(1)) if m else None


def parse_hw(cell: str) -> Tuple[Optional[float], Optional[float]]:
    plain = cell.replace("\\textbf{", "").replace("}", "")
    m = re.search(r"([\d.]+)\s*(?:\\pm|\$\\pm\$|±)\s*([\d.]+)", plain)
    if m:
        return float(m.group(1)), float(m.group(2))
    return parse_point(cell), None


def is_bold_cell(cell: str) -> bool:
    return "\\textbf{" in cell


def format_cell(val: float, hw: float, bold: bool) -> str:
    if val > 10:
        body = f"{val:.2f} $\\pm$ {hw:.2f}"
    else:
        body = f"{val:.4f} $\\pm$ {hw:.4f}"
    return f"\\textbf{{{body}}}" if bold else body


def audit_section_rows(rows: List[List[str]], higher_better: bool, table_id: str, sec_name: str) -> List[str]:
    """rows: list of cell lists (col0=model name)."""
    issues: List[str] = []
    if not rows:
        return issues
    ncols = max(len(r) for r in rows) - 1
    for col in range(1, ncols + 1):
        col_vals: List[Tuple[str, float, bool]] = []
        for r in rows:
            if col >= len(r):
                continue
            p = parse_point(r[col])
            if p is None:
                continue
            name = r[0].replace("\\textbf{", "").replace("}", "")
            col_vals.append((name, p, is_bold_cell(r[col])))
        if not col_vals:
            continue
        best = max(p for _, p, _ in col_vals) if higher_better else min(p for _, p, _ in col_vals)
        for name, p, bold in col_vals:
            want = abs(p - best) < 1e-6
            if bold != want:
                issues.append(
                    f"{table_id} [{sec_name}] {name} col {col}: {p} "
                    f"(bold={bold}, should={want}; col-best={best})"
                )
    return issues


def parse_data_rows(section: str) -> List[List[str]]:
    rows: List[List[str]] = []
    for ln in section.split("\n"):
        s = ln.strip()
        if "&" not in s or s.startswith("\\multicolumn"):
            continue
        if s.startswith("\\midrule") or s.startswith("\\toprule"):
            continue
        parts = [p.strip() for p in s.rstrip("\\").split("&")]
        if not parts[0] or parts[0] in ("Method", "Model", "方法", "模型"):
            continue
        if parts[0].startswith("\\multirow"):
            continue
        rows.append(parts)
    return rows


def audit_table_block(block: str, table_id: str) -> List[str]:
    issues: List[str] = []
    positions: List[Tuple[int, bool]] = []
    for pat, hb in SECTION_SPECS:
        for m in pat.finditer(block):
            positions.append((m.start(), hb))
    positions.sort(key=lambda x: x[0])
    if not positions:
        return [f"{table_id}: no metric sections found"]

    for idx, (start, hb) in enumerate(positions):
        end = positions[idx + 1][0] if idx + 1 < len(positions) else len(block)
        section = block[start:end]
        sec_name = re.search(r"\\textit\{([^}]+)\}", section)
        sec_label = sec_name.group(1)[:30] if sec_name else "?"
        rows = parse_data_rows(section)
        issues.extend(audit_section_rows(rows, hb, table_id, sec_label))
    return issues


def main() -> int:
    tables = ("R2", "R4", "R8", "R8b")
    exit_code = 0
    for name in ("body_en.tex", "body_zh.tex"):
        tex = (GENERATED / name).read_text(encoding="utf-8")
        print(f"=== {name} ===")
        for tid in tables:
            m = re.search(rf"\\label\{{tab:{tid}\}}(.*?)(?:\\end{{manuscriptresponsetable\}}|\\label\{{tab:)", tex, re.S)
            if not m:
                print(f"  {tid}: not found")
                continue
            iss = audit_table_block(m.group(1), tid)
            mism = [i for i in iss if "should=" in i]
            if mism:
                exit_code = 1
                print(f"  {tid}: {len(mism)} mismatch(es)")
                for line in mism[:15]:
                    print(f"    {line}")
                if len(mism) > 15:
                    print(f"    ... +{len(mism) - 15} more")
            else:
                print(f"  {tid}: OK (column-best bold)")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
