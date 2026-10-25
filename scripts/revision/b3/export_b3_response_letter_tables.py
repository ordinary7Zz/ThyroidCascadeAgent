#!/usr/bin/env python3
"""Export routing-ablation LaTeX fragments for reviewer response letter (Tables R14--R15)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _bootstrap() -> None:
    p = Path(__file__).resolve()
    for d in [p.parent, *p.parents]:
        if d.name == "revision" and (d / "_path_setup.py").is_file():
            spec = importlib.util.spec_from_file_location("_rev_path_setup", d / "_path_setup.py")
            mod = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(mod)
            mod.bootstrap(__file__)
            return
    raise RuntimeError("revision _path_setup.py not found")


_bootstrap()

import repo_path

REPO = repo_path.install()
B3 = REPO / "output" / "ablation" / "b3"
OUT = (
    REPO
    / "docs/revision/暂定的修改和回复计划/正式回复/latex/generated"
)

COHORTS = (
    ("tn3k", "TN3K"),
    ("tn5k", "TN5K"),
    ("thyroidxl", "ThyroidXL"),
    ("pktn", "PKTN"),
    ("ddti_seg", "DDTI (seg)"),
    ("ddti_cls", "DDTI (cls)"),
    ("zjh8k", "ZJH-8K"),
    ("rjh7k", "RJH-7K"),
)

# manuscript strategy numbers
STRATEGIES = (
    ("best_single", "1", "最优单专家 (1)", "Best single (1)"),
    ("soft_voting", "2", "软投票 (2)", "Soft voting (2)"),
    ("majority", "3", "多数票 (3)", "Majority (3)"),
    ("static_rule", "4", "静态规则 (4)", "Static rule (4)"),
    ("max_confidence", "5", "最大置信度 (5)", "Max-confidence (5)"),
    ("learned", "6", "学习型路由 (6)", "Learned router (6)"),
    ("llm", "7", "完整 ThyroidXAgent (7)", "Full ThyroidXAgent (7)"),
    ("oracle", "8", "Oracle (8)", "Oracle (8)"),
)

# Cohort lists are filtered at export time by _cohort_has_seg / _cohort_has_cls.
SEG_COHORTS = ("tn3k", "tn5k", "thyroidxl", "pktn", "ddti_seg", "zjh8k", "rjh7k")
CLS_COHORTS = ("tn3k", "tn5k", "thyroidxl", "ddti_cls", "zjh8k")


def _modes_for_cohort(cid: str, lang: str = "zh") -> list[tuple[str, str, dict | None]]:
    """All strategy rows for one cohort; missing learned/llm → None metrics."""
    rows: list[tuple[str, str, dict | None]] = []
    for mode, _num, zlabel, elabel in STRATEGIES:
        label = zlabel if lang == "zh" else elabel
        if mode == "llm":
            rows.append((mode, label, None))
            continue
        m = _load_metrics(cid, mode)
        if mode == "learned":
            rows.append((mode, label, m))
            continue
        if m is not None:
            rows.append((mode, label, m))
    return rows


def _load_metrics(cohort: str, mode: str) -> dict | None:
    p = B3 / cohort / mode / "b3_metrics.json"
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _fmt_ci(mean: float | None, lo: float | None, hi: float | None, nd: int = 3) -> str:
    if mean is None or lo is None or hi is None:
        return "---"
    if any(x != x for x in (mean, lo, hi)):  # nan
        return "---"
    return f"{mean:.{nd}f} ({lo:.{nd}f}--{hi:.{nd}f})"


def _seg_dice(m: dict | None) -> str:
    if not m:
        return "---"
    s = m.get("segmentation") or {}
    return _fmt_ci(s.get("dice_mean"), s.get("dice_ci_lower"), s.get("dice_ci_upper"), 3)


def _seg_hd95(m: dict | None) -> str:
    if not m:
        return "---"
    s = m.get("segmentation") or {}
    return _fmt_ci(s.get("hd95_mean"), s.get("hd95_ci_lower"), s.get("hd95_ci_upper"), 2)


def _cls_block(m: dict | None, key: str = "classification") -> tuple[str, str]:
    if not m:
        return "---", "---"
    c = m.get(key) or m.get("metrics_path_b_only") or {}
    if key == "classification_path_b" or key == "metrics_path_b_only":
        c = m.get("classification_path_b") or m.get("metrics_path_b_only") or {}
    auroc = _fmt_ci(c.get("auroc"), c.get("auroc_ci_lower"), c.get("auroc_ci_upper"), 3)
    auprc = _fmt_ci(c.get("auprc"), c.get("auprc_ci_lower"), c.get("auprc_ci_upper"), 3)
    return auroc, auprc


def _n_test(m: dict | None) -> str:
    if not m:
        return "---"
    return str(m.get("n_total", "---"))


def _ref_metrics(cohort: str) -> dict | None:
    return _load_metrics(cohort, "soft_voting") or _load_metrics(cohort, "oracle")


def _cohort_has_seg(cohort: str) -> bool:
    m = _ref_metrics(cohort)
    if not m:
        return False
    s = m.get("segmentation") or {}
    dice = s.get("dice_mean")
    return dice is not None and dice == dice


def _cohort_has_cls(cohort: str) -> bool:
    m = _ref_metrics(cohort)
    if not m:
        return False
    c = m.get("classification") or {}
    auroc = c.get("auroc")
    return auroc is not None and auroc == auroc


def _longtable_preamble(
    out: list[str],
    caption: str,
    label: str,
    cont_line: str,
    header_row: str,
) -> None:
    out.append("\\begin{responsepaginatedtable}")
    out.append(f"\\captionof{{table}}{{{caption}}}")
    out.append(f"\\label{{{label}}}")
    out.append("\\begin{longtable}{@{}lllll@{}}")
    out.append("\\toprule")
    out.append(f"{header_row} \\\\")
    out.append("\\midrule")
    out.append("\\endfirsthead")
    out.append("")
    out.append(f"\\multicolumn{{5}}{{r}}{{\\footnotesize\\emph{{{cont_line}}}}} \\\\")
    out.append("\\toprule")
    out.append(f"{header_row} \\\\")
    out.append("\\midrule")
    out.append("\\endhead")
    out.append("")
    out.append(f"\\multicolumn{{5}}{{r}}{{\\footnotesize\\emph{{{cont_line}}}}} \\\\")
    out.append("\\midrule")
    out.append("\\endfoot")
    out.append("\\bottomrule")
    out.append("\\endlastfoot")
    out.append("")


def _longtable_close(out: list[str], note: str) -> None:
    out.append("\\end{longtable}")
    out.append(f"\\responsetablenote{{{note}}}")
    out.append("\\end{responsepaginatedtable}")
    out.append("")


def _build_zh_tables() -> str:
    out: list[str] = ["% Auto-generated by export_b3_response_letter_tables.py\n"]

    seg_header = "队列 & $n$ & 路由策略 & Dice $\\uparrow$ & HD95 $\\downarrow$ (mm)"
    _longtable_preamble(
        out,
        "表 R14. 路由消融 --- 结节分割（固定专家池；点估计及 95\\% CI；"
        "cluster bootstrap，1000 次，seed=42）。",
        "tab:R14",
        "表 R14（续）",
        seg_header,
    )
    for cid, clabel in COHORTS:
        if cid not in SEG_COHORTS or not _cohort_has_seg(cid):
            continue
        modes_present = _modes_for_cohort(cid)
        if not modes_present:
            continue
        ref = _ref_metrics(cid)
        n_ref = _n_test(ref)
        for i, (_mode, zlabel, m) in enumerate(modes_present):
            if _mode == "llm" or m is None:
                dice, hd = "---", "---"
            else:
                dice, hd = _seg_dice(m), _seg_hd95(m)
            ccol = clabel if i == 0 else ""
            ncol = n_ref if i == 0 else ""
            out.append(f"{ccol} & {ncol} & {zlabel} & {dice} & {hd} \\\\")
        out.append("\\midrule")
    if out[-1] == "\\midrule":
        out.pop()
    _longtable_close(
        out,
        "静态规则 (4) 为专家一致度（agreement-only）。Oracle (8) 为上界。"
        "策略 (7) 完整 ThyroidXAgent 路由与学习型 (6) 在部分队列定稿补全（表中 ---）。"
        "仅列入具备分割评估的队列。",
    )

    cls_header = "队列 & $n$ & 路由策略 & AUROC $\\uparrow$ & AUPRC $\\uparrow$"
    _longtable_preamble(
        out,
        "表 R15. 路由消融 --- 良恶性分类（AUROC / AUPRC；点估计及 95\\% CI；"
        "cluster bootstrap，1000 次，seed=42）。",
        "tab:R15",
        "表 R15（续）",
        cls_header,
    )
    for cid, clabel in COHORTS:
        if cid not in CLS_COHORTS or not _cohort_has_cls(cid):
            continue
        modes_present = _modes_for_cohort(cid, "zh")
        if not modes_present:
            continue
        ref = _ref_metrics(cid)
        n_ref = _n_test(ref)
        for i, (_mode, zlabel, m) in enumerate(modes_present):
            if _mode == "llm" or m is None:
                auroc, auprc = "---", "---"
            else:
                auroc, auprc = _cls_block(m, "classification")
            ccol = clabel if i == 0 else ""
            ncol = n_ref if i == 0 else ""
            out.append(f"{ccol} & {ncol} & {zlabel} & {auroc} & {auprc} \\\\")
        out.append("\\midrule")
    if out[-1] == "\\midrule":
        out.pop()
    _longtable_close(
        out,
        "策略 (7) 为完整 ThyroidXAgent；策略 1--6 为 Methods~\\S4.3 受控路由对照。"
        "仅列入具备良恶性分类评估的队列。",
    )
    return "\n".join(out)


def _build_en_tables() -> str:
    out: list[str] = ["% Auto-generated by export_b3_response_letter_tables.py\n"]

    seg_header = "Cohort & $n$ & Routing strategy & Dice $\\uparrow$ & HD95 $\\downarrow$ (mm)"
    _longtable_preamble(
        out,
        "Table R14. Routing ablation --- nodule segmentation (fixed expert pool; "
        "point estimate and 95\\% CI; cluster bootstrap, 1000 resamples, seed=42).",
        "tab:R14",
        "Table R14 (continued)",
        seg_header,
    )
    for cid, clabel in COHORTS:
        if cid not in SEG_COHORTS or not _cohort_has_seg(cid):
            continue
        modes_present = _modes_for_cohort(cid, "en")
        if not modes_present:
            continue
        ref = _ref_metrics(cid)
        n_ref = _n_test(ref)
        for i, (_mode, elabel, m) in enumerate(modes_present):
            if _mode == "llm" or m is None:
                dice, hd = "---", "---"
            else:
                dice, hd = _seg_dice(m), _seg_hd95(m)
            ccol = clabel if i == 0 else ""
            ncol = n_ref if i == 0 else ""
            out.append(f"{ccol} & {ncol} & {elabel} & {dice} & {hd} \\\\")
        out.append("\\midrule")
    if out[-1] == "\\midrule":
        out.pop()
    _longtable_close(
        out,
        "Static rule (4): inter-expert agreement (agreement-only). Oracle (8): non-deployable upper bound. "
        "Strategy (7) full ThyroidXAgent routing and learned (6) on some cohorts: to be completed (---). "
        "Only cohorts with segmentation evaluation are listed.",
    )

    cls_header = "Cohort & $n$ & Routing strategy & AUROC $\\uparrow$ & AUPRC $\\uparrow$"
    _longtable_preamble(
        out,
        "Table R15. Routing ablation --- benign--malignant classification (AUROC / AUPRC; "
        "point estimate and 95\\% CI; cluster bootstrap, 1000 resamples, seed=42).",
        "tab:R15",
        "Table R15 (continued)",
        cls_header,
    )
    for cid, clabel in COHORTS:
        if cid not in CLS_COHORTS or not _cohort_has_cls(cid):
            continue
        modes_present = _modes_for_cohort(cid, "en")
        if not modes_present:
            continue
        ref = _ref_metrics(cid)
        n_ref = _n_test(ref)
        for i, (_mode, elabel, m) in enumerate(modes_present):
            if _mode == "llm" or m is None:
                auroc, auprc = "---", "---"
            else:
                auroc, auprc = _cls_block(m, "classification")
            ccol = clabel if i == 0 else ""
            ncol = n_ref if i == 0 else ""
            out.append(f"{ccol} & {ncol} & {elabel} & {auroc} & {auprc} \\\\")
        out.append("\\midrule")
    if out[-1] == "\\midrule":
        out.pop()
    _longtable_close(
        out,
        "Strategy (7): full ThyroidXAgent; strategies 1--6: controlled routing ablation (Methods~\\S4.3). "
        "Only cohorts with benign--malignant classification evaluation are listed.",
    )
    return "\n".join(out)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    OUT.joinpath("routing_ablation_tables_zh.tex").write_text(_build_zh_tables(), encoding="utf-8")
    OUT.joinpath("routing_ablation_tables_en.tex").write_text(_build_en_tables(), encoding="utf-8")
    print(f"Wrote {OUT}/routing_ablation_tables_zh.tex")
    print(f"Wrote {OUT}/routing_ablation_tables_en.tex")


if __name__ == "__main__":
    main()
