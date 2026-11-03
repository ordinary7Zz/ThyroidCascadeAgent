#!/usr/bin/env python3
"""
从 my_Thyroid_Infer `analyze_center_performance.py` 导出的 CSV（与 Supp. S7–S12 同真源）
计算 R2.6 表：中心性能 macro/pooled、meta I²/τ²，并可选 patch `nhc_b7_tables_{zh,en}.tex`。

用法:
  # 1) 在含「私有数据集结果」的机器上导出 CSV（与稿面 S 表一致）:
  cd my_Thyroid_Infer
  python analyze_center_performance.py \\
    --results_dir results/私有数据集结果/results \\
    --output_csv /path/to/ThyroidCascadeAgent/docs/revision/b7/data/per_by_center_manuscript.csv

  # 2) 或直接从稿面 per-center TeX 解析（与 S 表同列 ThyroidXAgent）:
  python scripts/revision/b7/render_nhc_b7_tables_from_supplement.py \\
    --tex docs/per_center_tables.tex --apply

  # 3) 生成汇总并写回信 TeX（仅替换 % BEGIN/END AUTO 块）:
  cd ThyroidCascadeAgent
  python scripts/revision/b7/render_nhc_b7_tables_from_supplement.py \\
    --csv docs/revision/b7/data/per_by_center_manuscript.csv --apply
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from typing import Optional
from collections import defaultdict
from pathlib import Path

SCRIPT = Path(__file__).resolve()
REPO = SCRIPT.parents[3]
sys.path.insert(0, str(REPO))

from pipeline.revision.b7.parse_per_center_tex import parse_per_center_tex  # noqa: E402
from pipeline.revision.b7.supplement_center_meta import (  # noqa: E402
    CenterEstimate,
    cochrane_q_i2_tau2,
    fmt_auroc,
    fmt_hd95,
    fmt_pct,
    parse_ci_field,
    pooled_weighted_mean,
    se_from_ci,
    unweighted_macro,
)

DEFAULT_CSV = REPO / "docs/revision/b7/data/per_by_center_manuscript.csv"
DEFAULT_TEX = REPO / "docs/per_center_tables.tex"
ARTIFACT_JSON = REPO / "docs/revision/b7/artifacts/nhc_supplement_b7_summary.json"
TEX_ZH = REPO / "docs/revision/暂定的修改和回复计划/正式回复/latex/generated/nhc_b7_tables_zh.tex"
TEX_EN = REPO / "docs/revision/暂定的修改和回复计划/正式回复/latex/generated/nhc_b7_tables_en.tex"

# 与稿面 S7–S12 / Fig.2h ThyroidXAgent 列一致（见 my_plot_images/饼图/plot_global.py）
MODELS = {
    "gland": "dinov3_unet",
    "nodule": "dinov3_unet",
    "binary": "dinov3_unet_multitask",
}


def _bootstrap() -> None:
    p = SCRIPT
    for d in [p.parent, *p.parents]:
        if d.name == "revision" and (d / "_path_setup.py").is_file():
            import importlib.util

            spec = importlib.util.spec_from_file_location("_rev_path_setup", d / "_path_setup.py")
            mod = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(mod)
            mod.bootstrap(__file__)
            return


def read_analyze_csv(path: Path) -> dict[tuple[str, str, str], dict]:
    """task, model, center -> {n, dice or auroc field}"""
    out: dict[tuple[str, str, str], dict] = {}
    section = None
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if line.startswith("=== 分割任务"):
                section = "seg"
                continue
            if line.startswith("=== 分类任务"):
                section = "cls"
                continue
            if not line or line.startswith("task,"):
                continue
            row = next(csv.reader([line]))
            if len(row) < 5:
                continue
            task, model, center, n_s = row[0], row[1], row[2], row[3]
            if center.strip() == "全局":
                continue
            try:
                n = int(n_s)
            except ValueError:
                continue
            if section == "seg":
                dice_s = row[4] if len(row) > 4 else ""
                pt, lo, hi = parse_ci_field(dice_s)
                if pt is None:
                    continue
                se = se_from_ci(lo, hi) if lo is not None and hi is not None else None
                out[(task, model, center)] = {
                    "n": n,
                    "point": pt,
                    "se": se,
                    "field": "dice",
                }
            elif section == "cls" and task == "binary":
                auroc_s = row[4] if len(row) > 4 else ""
                pt, lo, hi = parse_ci_field(auroc_s)
                if pt is None:
                    continue
                se = se_from_ci(lo, hi) if lo is not None and hi is not None else None
                out[(task, model, center)] = {
                    "n": n,
                    "point": pt,
                    "se": se,
                    "field": "auroc",
                }
    return out


def center_id_sort_key(cid: str) -> str:
    return cid


def build_summary(rows: dict[tuple[str, str, str], dict]) -> dict:
    by_task_center: dict[str, dict[str, CenterEstimate]] = defaultdict(dict)

    for task_key, model in MODELS.items():
        task = "gland" if task_key == "gland" else ("nodule" if task_key == "nodule" else "binary")
        for (t, m, center), block in rows.items():
            if t != task or m != model:
                continue
            if not center.startswith("THYB_S_"):
                continue
            by_task_center[task_key][center] = CenterEstimate(
                center_id=center,
                n=block["n"],
                point=block["point"],
                se=block.get("se"),
            )

    perf_rows = []
    all_centers = sorted(
        set(by_task_center["gland"]) | set(by_task_center["nodule"]) | set(by_task_center["binary"]),
        key=center_id_sort_key,
    )
    for cid in all_centers:
        g = by_task_center["gland"].get(cid)
        nod = by_task_center["nodule"].get(cid)
        cls = by_task_center["binary"].get(cid)
        n_img = max((x.n for x in (g, nod, cls) if x), default=0)
        perf_rows.append(
            {
                "center_id": cid,
                "n_images_max_task": n_img,
                "gland_dice": g.point if g else None,
                "nodule_dice": nod.point if nod else None,
                "auroc": cls.point if cls else None,
                "auroc_estimable": cls is not None and cls.point is not None,
            }
        )

    def block(task_key: str, label: str):
        est = list(by_task_center[task_key].values())
        total_n = sum(e.n for e in est)
        macro = unweighted_macro(est)
        pooled = pooled_weighted_mean(est)
        meta = cochrane_q_i2_tau2(est)
        return {
            "label": label,
            "n_centers": meta["n_groups"],
            "n_images": total_n,
            "macro_mean": macro,
            "pooled_weighted": pooled,
            "heterogeneity": meta,
        }

    summary = {
        "source": "Supp. S7–S12 / analyze_center_performance CSV",
        "models": MODELS,
        "performance_rows": perf_rows,
        "gland": block("gland", "Gland Dice"),
        "nodule": block("nodule", "Nodule Dice"),
        "binary": block("binary", "BM AUROC"),
    }
    return summary


def build_summary_from_tex(parsed: dict) -> dict:
    """parsed from parse_per_center_tex."""
    by_task_center = {
        "gland": parsed["gland"].centers,
        "gland_hd95": parsed["gland_hd95"].centers,
        "nodule": parsed["nodule"].centers,
        "nodule_hd95": parsed["nodule_hd95"].centers,
        "binary": parsed["binary"].centers,
        "binary_auprc": parsed["binary_auprc"].centers,
    }

    perf_rows = []
    all_centers = sorted(
        set(by_task_center["gland"])
        | set(by_task_center["gland_hd95"])
        | set(by_task_center["nodule"])
        | set(by_task_center["nodule_hd95"])
        | set(by_task_center["binary"])
        | set(by_task_center["binary_auprc"]),
        key=center_id_sort_key,
    )
    for cid in all_centers:
        g = by_task_center["gland"].get(cid)
        g_h = by_task_center["gland_hd95"].get(cid)
        nod = by_task_center["nodule"].get(cid)
        nod_h = by_task_center["nodule_hd95"].get(cid)
        cls = by_task_center["binary"].get(cid)
        ap = by_task_center["binary_auprc"].get(cid)
        n_gland = g.n if g else None
        n_nodule = nod.n if nod else None
        n_binary = cls.n if cls else None
        perf_rows.append(
            {
                "center_id": cid,
                "n_gland": n_gland,
                "n_nodule": n_nodule,
                "n_binary": n_binary,
                "n_images_max_task": n_gland
                if n_gland
                else max((x for x in (n_nodule, n_binary) if x), default=0),
                "gland_dice": g.point if g else None,
                "gland_hd95": g_h.point if g_h else None,
                "nodule_dice": nod.point if nod else None,
                "nodule_hd95": nod_h.point if nod_h else None,
                "auroc": cls.point if cls else None,
                "auroc_estimable": cls is not None and cls.point is not None,
                "auprc": ap.point if ap else None,
                "auprc_estimable": ap is not None and ap.point is not None,
            }
        )

    def block(task_key: str, label: str):
        table = parsed[task_key]
        est = list(by_task_center[task_key].values())
        macro = unweighted_macro(est)
        pooled = (
            table.overall_point
            if table.overall_point is not None
            else pooled_weighted_mean(est)
        )
        meta = cochrane_q_i2_tau2(est)
        n_images = table.overall_n if table.overall_n else sum(e.n for e in est)
        return {
            "label": label,
            "n_centers": meta["n_groups"],
            "n_images": n_images,
            "macro_mean": macro,
            "pooled_weighted": pooled,
            "heterogeneity": meta,
        }

    summary = {
        "source": f"Supp. S7–S12 / {DEFAULT_TEX.relative_to(REPO)}",
        "models": {"gland": "ThyroidXAgent", "nodule": "ThyroidXAgent", "binary": "ThyroidXAgent"},
        "performance_rows": perf_rows,
        "gland": block("gland", "Gland Dice"),
        "gland_hd95": block("gland_hd95", "Gland HD95"),
        "nodule": block("nodule", "Nodule Dice"),
        "nodule_hd95": block("nodule_hd95", "Nodule HD95"),
        "binary": block("binary", "BM AUROC"),
        "binary_auprc": block("binary_auprc", "BM AUPRC"),
    }
    return summary


def _tex_escape_center(cid: str) -> str:
    return cid.replace("_", "\\_")


def fmt_n_cell(n: Optional[int]) -> str:
    if n is None or n <= 0:
        return "---"
    return str(n)


def render_performance_rows(summary: dict, *, lang: str) -> str:
    lines = []
    for r in summary["performance_rows"]:
        cid = _tex_escape_center(r["center_id"])
        ng = fmt_n_cell(r.get("n_gland"))
        nn = fmt_n_cell(r.get("n_nodule"))
        nb = fmt_n_cell(r.get("n_binary"))
        g = fmt_pct(r["gland_dice"]) if r["gland_dice"] is not None else "---"
        g_h = fmt_hd95(r.get("gland_hd95"))
        nod = fmt_pct(r["nodule_dice"]) if r["nodule_dice"] is not None else "---"
        nod_h = fmt_hd95(r.get("nodule_hd95"))
        au = fmt_auroc(r["auroc"]) if r.get("auroc_estimable") else "NE"
        ap = fmt_auroc(r["auprc"]) if r.get("auprc_estimable") else "NE"
        lines.append(
            f"{cid} & {ng} & {nn} & {nb} & {g} & {g_h} & {nod} & {nod_h} & {au} & {ap} \\\\"
        )

    gl = summary["gland"]
    gl_h = summary.get("gland_hd95") or {}
    nod = summary["nodule"]
    nod_h = summary.get("nodule_hd95") or {}
    bi = summary["binary"]
    bi_p = summary.get("binary_auprc") or {}
    n_g, n_n, n_b = gl["n_images"], nod["n_images"], bi["n_images"]
    if lang == "zh":
        lines.append(
            f"\\textbf{{Overall 池化}} & \\textbf{{{n_g}}} & \\textbf{{{n_n}}} & \\textbf{{{n_b}}} & "
            f"\\textbf{{{fmt_pct(gl['pooled_weighted'])}}} & \\textbf{{{fmt_hd95(gl_h.get('pooled_weighted'))}}} & "
            f"\\textbf{{{fmt_pct(nod['pooled_weighted'])}}} & \\textbf{{{fmt_hd95(nod_h.get('pooled_weighted'))}}} & "
            f"\\textbf{{{fmt_auroc(bi['pooled_weighted'])}}} & \\textbf{{{fmt_auroc(bi_p.get('pooled_weighted'))}}} \\\\"
        )
        lines.append(
            f"\\textbf{{跨中心等权宏平均}} & --- & --- & --- & "
            f"\\textbf{{{fmt_pct(gl['macro_mean'])}}} & \\textbf{{{fmt_hd95(gl_h.get('macro_mean'))}}} & "
            f"\\textbf{{{fmt_pct(nod['macro_mean'])}}} & \\textbf{{{fmt_hd95(nod_h.get('macro_mean'))}}} & "
            f"\\textbf{{{fmt_auroc(bi['macro_mean'])}}} & \\textbf{{{fmt_auroc(bi_p.get('macro_mean'))}}} \\\\"
        )
    else:
        lines.append(
            f"\\textbf{{Overall pooled}} & \\textbf{{{n_g}}} & \\textbf{{{n_n}}} & \\textbf{{{n_b}}} & "
            f"\\textbf{{{fmt_pct(gl['pooled_weighted'])}}} & \\textbf{{{fmt_hd95(gl_h.get('pooled_weighted'))}}} & "
            f"\\textbf{{{fmt_pct(nod['pooled_weighted'])}}} & \\textbf{{{fmt_hd95(nod_h.get('pooled_weighted'))}}} & "
            f"\\textbf{{{fmt_auroc(bi['pooled_weighted'])}}} & \\textbf{{{fmt_auroc(bi_p.get('pooled_weighted'))}}} \\\\"
        )
        lines.append(
            f"\\textbf{{Unweighted macro}} & --- & --- & --- & "
            f"\\textbf{{{fmt_pct(gl['macro_mean'])}}} & \\textbf{{{fmt_hd95(gl_h.get('macro_mean'))}}} & "
            f"\\textbf{{{fmt_pct(nod['macro_mean'])}}} & \\textbf{{{fmt_hd95(nod_h.get('macro_mean'))}}} & "
            f"\\textbf{{{fmt_auroc(bi['macro_mean'])}}} & \\textbf{{{fmt_auroc(bi_p.get('macro_mean'))}}} \\\\"
        )
    return "\n".join(lines)


def render_descriptive_image_rows(summary: dict) -> str:
    """仅图像数（来自 S 表 n）；患者/结节/扫描仪仍 \\rpending。"""
    by_center: dict[str, int] = {}
    for r in summary["performance_rows"]:
        by_center[r["center_id"]] = r["n_images_max_task"]
    total = sum(by_center.values())
    lines = []
    for cid in sorted(by_center, key=center_id_sort_key):
        n = by_center[cid]
        lines.append(
            f"{_tex_escape_center(cid)} & \\rpendingzh{{院方确认}} & \\rpendingzh{{院方确认}} & {n} & "
            f"\\rpendingzh{{院方确认}} & 是 & \\rpendingzh{{标签可用性}} \\\\"
        )
    lines.append(
        f"\\textbf{{合计（{len(by_center)} 中心）}} & --- & --- & \\textbf{{{total}}} & --- & --- & --- \\\\"
    )
    return "\n".join(lines)


def render_descriptive_image_rows_en(summary: dict) -> str:
    by_center: dict[str, int] = {}
    for r in summary["performance_rows"]:
        by_center[r["center_id"]] = r["n_images_max_task"]
    total = sum(by_center.values())
    lines = []
    for cid in sorted(by_center, key=center_id_sort_key):
        n = by_center[cid]
        lines.append(
            f"{_tex_escape_center(cid)} & \\rpending{{data steward}} & \\rpending{{data steward}} & {n} & "
            f"\\rpending{{data steward}} & Yes & \\rpending{{label availability}} \\\\"
        )
    lines.append(
        f"\\textbf{{Total ({len(by_center)} centers)}} & --- & --- & \\textbf{{{total}}} & --- & --- & --- \\\\"
    )
    return "\n".join(lines)


def render_heterogeneity_rows(summary: dict, *, lang: str) -> str:
    def one_row(name_zh: str, name_en: str, key: str, metric_col: str):
        b = summary[key]
        h = b["heterogeneity"]
        macro = b["macro_mean"]
        pooled = b["pooled_weighted"]
        i2 = h.get("i2_percent")
        tau2 = h.get("tau2")
        i2_s = f"{i2:.1f}" if i2 is not None else "---"
        tau2_s = f"{tau2:.3f}" if tau2 is not None else "---"
        if metric_col == "dice":
            pooled_macro = f"{fmt_pct(pooled)} / {fmt_pct(macro)}"
        else:
            pooled_macro = f"{fmt_auroc(pooled)} / {fmt_auroc(macro)}"
        label = name_zh if lang == "zh" else name_en
        return (
            f"{label} & {metric_col} $\\uparrow$ & {h['n_groups']} & {b['n_images']} & "
            f"{pooled_macro} & {i2_s} & {tau2_s} \\\\"
        )

    lines = [
        one_row("结节分割", "Nodule segmentation", "nodule", "Dice"),
        one_row("良恶性分类", "Benign--malignant", "binary", "AUROC"),
        one_row("全腺体分割", "Gland segmentation", "gland", "Dice"),
    ]
    return "\n".join(lines)


def patch_auto_block(tex_path: Path, marker: str, new_body: str) -> None:
    text = tex_path.read_text(encoding="utf-8")
    begin = f"% BEGIN AUTO {marker}"
    end = f"% END AUTO {marker}"
    i = text.find(begin)
    if i == -1:
        raise SystemExit(f"{tex_path}: missing marker {begin}")
    j = text.find(end, i)
    if j == -1:
        raise SystemExit(f"{tex_path}: missing marker {end}")
    new_text = text[: i + len(begin)] + "\n" + new_body + "\n" + text[j:]
    tex_path.write_text(new_text, encoding="utf-8")


def maybe_run_analyze(results_dir: Path, out_csv: Path) -> None:
    infer_script = REPO.parent / "my_Thyroid_Infer" / "analyze_center_performance.py"
    if not infer_script.is_file():
        raise SystemExit(f"缺少 {infer_script}")
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sys.executable,
            str(infer_script),
            "--results_dir",
            str(results_dir),
            "--output_csv",
            str(out_csv),
        ],
        check=True,
    )


def main() -> None:
    _bootstrap()
    parser = argparse.ArgumentParser(description="S7–S12 → NHC B7 回信表")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument(
        "--tex",
        type=Path,
        default=DEFAULT_TEX,
        help="Supp. per-center 表 TeX（默认 docs/per_center_tables.tex）；存在则优先于 CSV",
    )
    parser.add_argument("--results-dir", type=Path, default=None, help="若提供则先跑 analyze_center_performance")
    parser.add_argument("--apply", action="store_true", help="写 nhc_b7_tables_zh/en.tex 的 AUTO 块")
    parser.add_argument("--json-out", type=Path, default=ARTIFACT_JSON)
    args = parser.parse_args()

    if args.results_dir:
        maybe_run_analyze(args.results_dir, args.csv)

    if args.tex.is_file():
        parsed = parse_per_center_tex(args.tex)
        summary = build_summary_from_tex(parsed)
    elif args.csv.is_file():
        rows = read_analyze_csv(args.csv)
        summary = build_summary(rows)
    else:
        raise SystemExit(
            f"缺少数据源：{args.tex} 或 {args.csv}\n"
            "请提供 docs/per_center_tables.tex，或从 my_Thyroid_Infer 导出 CSV。"
        )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.json_out, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"✓ {args.json_out}")
    print(
        f"  centers={summary['nodule']['n_centers']}  n_images(nodule)={summary['nodule']['n_images']}  "
        f"nodule macro Dice={fmt_pct(summary['nodule']['macro_mean'])}%  "
        f"I2={summary['nodule']['heterogeneity'].get('i2_percent')}"
    )

    if args.apply:
        patch_auto_block(TEX_ZH, "tab_nhc_center_descriptive rows", render_descriptive_image_rows(summary))
        patch_auto_block(TEX_EN, "tab_nhc_center_descriptive rows", render_descriptive_image_rows_en(summary))
        patch_auto_block(TEX_ZH, "tab_nhc_center_performance rows", render_performance_rows(summary, lang="zh"))
        patch_auto_block(TEX_EN, "tab_nhc_center_performance rows", render_performance_rows(summary, lang="en"))
        patch_auto_block(TEX_ZH, "tab_nhc_heterogeneity rows", render_heterogeneity_rows(summary, lang="zh"))
        patch_auto_block(TEX_EN, "tab_nhc_heterogeneity rows", render_heterogeneity_rows(summary, lang="en"))
        print(f"✓ patched {TEX_ZH.name} / {TEX_EN.name}")


if __name__ == "__main__":
    main()
