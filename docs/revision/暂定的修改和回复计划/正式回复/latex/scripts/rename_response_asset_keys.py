#!/usr/bin/env python3
"""Rename tabR* / figR* keys to semantic tab_* / fig_* slugs."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated"

# Longest keys first
REPLACEMENTS = [
    ("tabR14", "tab_routing_ablation_cls"),
    ("tabR13", "tab_routing_ablation_seg"),
    ("tabR12", "tab_small_nodule_fail"),
    ("tabR11", "tab_baseline_protocol"),
    ("tabR10", "tab_routing_stability"),
    ("tabR7b", "tab_malig_ext"),
    ("tabR9", "tab_patient_seg"),
    ("tabR8", "tab_patient_cls"),
    ("tabR7", "tab_malig_oof"),
    ("tabR6", "tab_cls_macro_mean"),
    ("tabR5", "tab_dataflow"),
    ("tabR4", "tab_calib_referral"),
    ("tabR3", "tab_seg_ext"),
    ("tabR2", "tab_cls_ext"),
    ("tabR1", "tab_dhash"),
    ("figR2", "fig_risk_coverage"),
    ("figR1", "fig_reliability"),
]

FILES = [
    GENERATED / "body_en.tex",
    GENERATED / "body_zh.tex",
    GENERATED / "routing_ablation_tables_en.tex",
    GENERATED / "routing_ablation_tables_zh.tex",
    ROOT / "README.md",
    ROOT / "scripts" / "migrate_response_asset_refs.py",
]


def main() -> None:
    for path in FILES:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for old, new in REPLACEMENTS:
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")
        print("renamed keys in", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
