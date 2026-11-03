"""Parse docs/per_center_tables.tex (Supp. S7–S12) ThyroidXAgent column."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from pipeline.revision.b7.supplement_center_meta import CenterEstimate, se_from_ci


LABELS = {
    "gland": "tab:gland_dice",
    "gland_hd95": "tab:gland_hd95",
    "nodule": "tab:nodule_dice",
    "nodule_hd95": "tab:nodule_hd95",
    "binary": "tab:binary_auroc",
    "binary_auprc": "tab:binary_auprc",
}


@dataclass
class ParsedTable:
    overall_n: int
    overall_point: Optional[float]
    overall_lo: Optional[float]
    overall_hi: Optional[float]
    centers: dict[str, CenterEstimate]


def _parse_n(raw: str) -> Optional[int]:
    s = raw.strip().replace(",", "").replace("{,}", ",").replace(" ", "")
    s = re.sub(r"[^\d]", "", s)
    if not s:
        return None
    return int(s)


def _parse_metric_cell(cell: str, *, is_percent: bool) -> tuple[Optional[float], Optional[float], Optional[float]]:
    if not cell or "--" in cell.strip():
        return None, None, None
    cleaned = re.sub(r"\\textbf\{([^}]*)\}", r"\1", cell.strip())
    m = re.search(
        r"([\d.]+)\s*\\textsubscript\s*\{\s*\(\s*([\d.,]+)\s*,\s*([\d.,]+)\s*\)\s*\}",
        cleaned,
    )
    if not m:
        m2 = re.search(r"([\d.]+)", cleaned)
        if not m2:
            return None, None, None
        v = float(m2.group(1))
        if is_percent:
            v /= 100.0
        return v, None, None
    pt, lo, hi = float(m.group(1)), float(m.group(2)), float(m.group(3))
    if is_percent:
        pt, lo, hi = pt / 100.0, lo / 100.0, hi / 100.0
    return pt, lo, hi


def _extract_table_block(tex: str, label: str) -> str:
    pat = re.compile(rf"\\label\{{{re.escape(label)}\}}(.*?)\\end{{table}}", re.DOTALL)
    m = pat.search(tex)
    if not m:
        raise ValueError(f"label not found: {label}")
    return m.group(1)


def parse_table(tex: str, label: str, *, is_percent: bool) -> ParsedTable:
    block = _extract_table_block(tex, label)
    centers: dict[str, CenterEstimate] = {}
    overall_n = 0
    overall_pt = overall_lo = overall_hi = None

    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith("%") or "&" not in line:
            continue
        if "\\midrule" in line or "\\toprule" in line or "\\bottomrule" in line:
            continue
        parts = [p.strip() for p in line.split("&")]
        if len(parts) < 3:
            continue
        center_raw = parts[0]
        if center_raw.startswith("\\textit{Overall}"):
            n = _parse_n(parts[1])
            pt, lo, hi = _parse_metric_cell(parts[2], is_percent=is_percent)
            if n is not None:
                overall_n = n
            overall_pt, overall_lo, overall_hi = pt, lo, hi
            continue
        if not center_raw.startswith("THYB"):
            continue
        center_id = center_raw.replace("\\_", "_")
        n = _parse_n(parts[1])
        if n is None or n <= 0:
            continue
        pt, lo, hi = _parse_metric_cell(parts[2], is_percent=is_percent)
        if pt is None:
            continue
        se = se_from_ci(lo, hi) if lo is not None and hi is not None else None
        centers[center_id] = CenterEstimate(center_id=center_id, n=n, point=pt, se=se)

    return ParsedTable(
        overall_n=overall_n,
        overall_point=overall_pt,
        overall_lo=overall_lo,
        overall_hi=overall_hi,
        centers=centers,
    )


def parse_per_center_tex(path) -> dict[str, ParsedTable]:
    text = path.read_text(encoding="utf-8")
    return {
        "gland": parse_table(text, LABELS["gland"], is_percent=True),
        "gland_hd95": parse_table(text, LABELS["gland_hd95"], is_percent=False),
        "nodule": parse_table(text, LABELS["nodule"], is_percent=True),
        "nodule_hd95": parse_table(text, LABELS["nodule_hd95"], is_percent=False),
        "binary": parse_table(text, LABELS["binary"], is_percent=False),
        "binary_auprc": parse_table(text, LABELS["binary_auprc"], is_percent=False),
    }
