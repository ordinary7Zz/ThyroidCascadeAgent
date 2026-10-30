#!/usr/bin/env python3
"""Copy metric columns from routing_ablation_tables_en.tex to _zh.tex (same row order)."""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
EN = REPO / "docs/revision/暂定的修改和回复计划/正式回复/latex/generated/routing_ablation_tables_en.tex"
ZH = REPO / "docs/revision/暂定的修改和回复计划/正式回复/latex/generated/routing_ablation_tables_zh.tex"

INNER = r"\d+\.\d+(?: \([^)]+\))?"
ROW_RE = re.compile(
    rf"^(?P<prefix>.*? & .*? & .*? & )"
    rf"(?P<c3>(?:\\(?:textbf|routingbest|routingsecond)\{{)?(?P<v3>{INNER})(?:\}})?)"
    rf"(?P<mid> & )"
    rf"(?P<c4>(?:\\(?:textbf|underline|routingbest|routingsecond)\{{)?(?P<v4>{INNER})(?:\}})?)"
    rf"(?P<suffix> \\\\)\s*$"
)


def is_data_row(line: str) -> bool:
    return bool(ROW_RE.match(line))


def sync() -> None:
    en_lines = EN.read_text(encoding="utf-8").splitlines()
    zh_lines = ZH.read_text(encoding="utf-8").splitlines()
    en_idx = [i for i, ln in enumerate(en_lines) if is_data_row(ln)]
    zh_idx = [i for i, ln in enumerate(zh_lines) if is_data_row(ln)]
    if len(en_idx) != len(zh_idx):
        raise RuntimeError(f"Row count mismatch: en={len(en_idx)} zh={len(zh_idx)}")
    for ei, zi in zip(en_idx, zh_idx):
        em = ROW_RE.match(en_lines[ei])
        zm = ROW_RE.match(zh_lines[zi])
        if not em or not zm:
            raise RuntimeError(f"Parse failed en@{ei+1} or zh@{zi+1}")
        zh_lines[zi] = (
            f"{zm.group('prefix')}{em.group('v3')}{zm.group('mid')}"
            f"{em.group('v4')}{zm.group('suffix')}"
        )
    ZH.write_text("\n".join(zh_lines) + "\n", encoding="utf-8")
    print(f"Synced {len(en_idx)} data rows: {EN.name} -> {ZH.name}")


if __name__ == "__main__":
    sync()
