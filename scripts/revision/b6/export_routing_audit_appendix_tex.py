#!/usr/bin/env python3
"""Export de-identified routing-log exemplars for reviewer-response Appendix A1-3."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def _latex_escape(s: str) -> str:
    s = str(s)
    repl = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for a, b in repl.items():
        s = s.replace(a, b)
    return s


EXPERT_EN = {
    "all_datasets": "Multi-cohort joint",
    "TN3K": "TN3K-specific",
    "TN5K": "TN5K-specific",
    "ThyroidXL": "ThyroidXL-specific",
    "PKTN_comprehensive": "PKTN-specific",
    "RJH-7K": "RJH-specific",
    "ZJH-8K": "ZJH-specific",
}

EXPERT_ZH = {
    "all_datasets": "多队列联合",
    "TN3K": "TN3K 专用",
    "TN5K": "TN5K 专用",
    "ThyroidXL": "ThyroidXL 专用",
    "PKTN_comprehensive": "PKTN 专用",
    "RJH-7K": "RJH 专用",
    "ZJH-8K": "ZJH 专用",
}


def _expert(name: str | None, lang: str) -> str:
    if not name:
        return "---"
    m = EXPERT_EN if lang == "en" else EXPERT_ZH
    return m.get(name, name.replace("_", " "))


def _tier(tier: str | None, lang: str) -> str:
    if tier == "close":
        return "Similar" if lang == "en" else "相近"
    if tier == "easy":
        return "Easy" if lang == "en" else "易区分"
    return tier or "---"


def _task_label(task: str | None, lang: str) -> str:
    if task == "seg":
        return "Segmentation routing" if lang == "en" else "分割路由"
    if task == "cls_path_a":
        return "Classification routing" if lang == "en" else "分类路由"
    if task == "cls_path_b":
        return "Classification routing" if lang == "en" else "分类路由"
    return task or "---"


def _mode_label(method: str | None, lang: str) -> str:
    m = method or ""
    if lang == "en":
        return {
            "llm_single": "LLM mask selection",
            "path_b_llm": "LLM arbitration",
            "classification_consensus": "Deterministic consensus",
            "path_b_softvote": "Weighted soft vote (LLM unavailable)",
            "llm_fallback": "Rule fallback (LLM parse/API failure)",
        }.get(m, m)
    return {
        "llm_single": "LLM 选 mask",
        "path_b_llm": "LLM 裁决",
        "classification_consensus": "确定性共识",
        "path_b_softvote": "加权软投票（LLM 不可用）",
        "llm_fallback": "规则回退（LLM 解析/API 失败）",
    }.get(m, m)


def _outcome(r: dict, lang: str) -> str:
    if r.get("task") == "seg":
        return _expert(r.get("selected_model"), lang)
    if r.get("task") == "cls_path_b":
        cls = r.get("selected_class") or "---"
        if lang == "zh" and cls in ("良性", "恶性"):
            return cls
        if lang == "en":
            if cls == "良性":
                return "Benign"
            if cls == "恶性":
                return "Malignant"
        return _latex_escape(cls)
    if r.get("task") == "cls_path_a":
        cls = r.get("selected_class") or "---"
        if lang == "en":
            if cls == "良性":
                return "Benign (consensus)"
            if cls == "恶性":
                return "Malignant (consensus)"
        return f"{cls}（共识）" if lang == "zh" else _latex_escape(cls)
    return "---"


def _candidates_sketch(r: dict, lang: str) -> str:
    cs = r.get("candidates_summary") or []
    if not cs:
        return "---"
    if cs and "top_class" in cs[0] and r.get("task") in ("cls_path_b", "cls_path_a"):
        parts = []
        for c in cs[:3]:
            cls = c.get("top_class", "?")
            conf = c.get("top_confidence")
            if lang == "en":
                cls = {"良性": "Benign", "恶性": "Malignant"}.get(cls, cls)
            if conf is not None:
                parts.append(f"{cls} ({float(conf):.2f})")
            else:
                parts.append(str(cls))
        head = f"{len(cs)} classifiers" if lang == "en" else f"{len(cs)} 个分类器"
        return head + ": " + ", ".join(parts)
    n = len(cs)
    ranked = sorted(
        cs,
        key=lambda x: float(x.get("average_agreement") or 0),
        reverse=True,
    )
    top = ranked[:2]
    parts = []
    for c in top:
        name = c.get("model_name", "?")
        short = _expert(name, lang)
        agr = c.get("average_agreement")
        if agr is not None:
            parts.append(f"{short} ({float(agr):.2f})")
        else:
            parts.append(short)
    head = f"{n} candidates" if lang == "en" else f"{n} 个候选"
    return head + "; " + ", ".join(parts)


def _reasoning_cell(r: dict, lang: str) -> str:
    raw = str(r.get("reasoning") or "").strip()
    if raw == "-":
        return "`--'" if lang == "en" else "占位 ``-''"
    if len(raw) > 48:
        raw = raw[:45] + "…"
    if lang == "en" and raw != "-":
        # Keep programmatic Chinese fallbacks readable in EN table as transliteration-lite
        if "独立分类模型一致" in raw:
            return "Programmatic consensus note"
        if "降级" in raw or "软投票" in raw:
            return "Programmatic fallback note"
    return _latex_escape(raw)


def _load_records(path: Path, max_primary: int = 520) -> tuple[list[dict], list[dict]]:
    """Primary deduped rows (main pass) + all rows (for rare fallbacks)."""
    primary: list[dict] = []
    all_rows: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for i, line in enumerate(path.open()):
        r = json.loads(line)
        all_rows.append(r)
        if i >= max_primary:
            continue
        key = (r.get("image_name") or "", r.get("task") or "")
        if key in seen:
            continue
        seen.add(key)
        primary.append(r)
    return primary, all_rows


def _order_rows_for_display(
    hero: dict | None,
    seg_llm: list[dict],
    path_b: list[dict],
    consensus: list[dict],
    softvote: list[dict],
    llm_fallback: list[dict],
    n: int = 12,
) -> list[dict]:
    """Interleave seg vs classification-side rows; Rec-07 = hero segmentation row."""
    segs_other = [r for r in seg_llm if hero is None or id(r) != id(hero)]
    seg_tail = list(llm_fallback)

    ordered: list[dict] = []
    si = pi = 0
    # First block: alternate classification-side (path B LLM) and segmentation LLM
    while len(ordered) < 6 and (pi < len(path_b) or si < len(segs_other)):
        if pi < len(path_b) and (len(ordered) % 2 == 0 or si >= len(segs_other)):
            ordered.append(path_b[pi])
            pi += 1
        elif si < len(segs_other):
            ordered.append(segs_other[si])
            si += 1
        elif pi < len(path_b):
            ordered.append(path_b[pi])
            pi += 1
        else:
            break

    if hero:
        ordered.insert(min(6, len(ordered)), hero)

    while pi < len(path_b):
        ordered.append(path_b[pi])
        pi += 1
    while si < len(segs_other):
        ordered.append(segs_other[si])
        si += 1

    for r in consensus:
        if len(ordered) >= n:
            break
        ordered.append(r)
    for r in softvote:
        if len(ordered) >= n:
            break
        ordered.append(r)
    for r in seg_tail:
        if len(ordered) >= n:
            break
        ordered.append(r)

    seen: set[int] = set()
    deduped: list[dict] = []
    for r in ordered:
        if id(r) in seen:
            continue
        seen.add(id(r))
        deduped.append(r)

    if hero:
        deduped = [r for r in deduped if id(r) != id(hero)]
        deduped.insert(min(6, len(deduped)), hero)

    return deduped[:n]


def _pick_exemplars(primary: list[dict], all_rows: list[dict], n: int = 12) -> list[dict]:
    used: set[int] = set()

    def grab(pool: list[dict], k: int) -> list[dict]:
        got: list[dict] = []
        for r in pool:
            if id(r) in used:
                continue
            used.add(id(r))
            got.append(r)
            if len(got) >= k:
                break
        return got

    seg_pool = [
        r
        for r in primary
        if r.get("task") == "seg" and r.get("method") == "llm_single"
    ]
    path_b_pool = [
        r
        for r in primary
        if r.get("task") == "cls_path_b" and r.get("method") == "path_b_llm"
    ]
    consensus_pool = [r for r in primary if r.get("task") == "cls_path_a"]
    softvote_pool = [r for r in all_rows if r.get("method") == "path_b_softvote"]
    fallback_pool = [r for r in all_rows if r.get("method") == "llm_fallback"]

    hero = next((r for r in seg_pool if r.get("selected_model") == "all_datasets"), None)
    if hero:
        used.add(id(hero))

    seg_llm: list[dict] = []
    if hero:
        seg_llm.append(hero)
    for r in seg_pool:
        if id(r) in used:
            continue
        if (
            hero
            and r.get("selected_model") == "all_datasets"
            and id(r) != id(hero)
        ):
            continue
        used.add(id(r))
        seg_llm.append(r)
        if len(seg_llm) >= 4:
            break
    if not hero and seg_llm:
        hero = seg_llm[0]

    path_b = grab(path_b_pool, 5)
    # 4 seg LLM + 5 path_b_llm + 1 consensus + 1 softvote + 1 llm_fallback = 12
    consensus = grab(consensus_pool, 1)
    softvote = grab(softvote_pool, 1)
    llm_fallback = grab(fallback_pool, 1)

    return _order_rows_for_display(
        hero, seg_llm, path_b, consensus, softvote, llm_fallback, n=n
    )


def _render_table(rows: list[dict], lang: str) -> str:
    if lang == "en":
        cap = (
            "Table A1-3. De-identified structured routing-record exemplars "
            "(TN3K external testing; fields aligned with Table A1-2)"
        )
        note = (
            r"\par\smallskip\noindent\footnotesize Exemplars are balanced across segmentation "
            r"LLM routing and classification routing (LLM-invoked routes, deterministic "
            r"consensus, soft vote, and rule fallback). On this TN3K primary pass, segmentation LLM "
            r"routes were all ``similar'' tier (top-two candidate agreement gap "
            r"$\leq 0.10$)."
        )
        hdr = (
            r"\textbf{Rec.} & \textbf{Task} & \textbf{Tier} & \textbf{LLM} & "
            r"\textbf{Decision mode} & \textbf{Outcome} & \textbf{Conf.} & "
            r"\textbf{Candidate sketch} \\"
        )
    else:
        cap = "表 A1-3. 去标识化结构化路由记录样例（TN3K 外测；字段与表 A1-2 对齐）"
        note = (
            r"\par\smallskip\noindent\footnotesize 样例行在分割 LLM 路由与分类路由"
            r"（调用 LLM、确定性共识、软投票与规则回退）之间均衡选取。"
            r"本 TN3K 主评估中，分割 LLM 路由的相近度分层均为「相近」"
            r"（最优与次优候选 agreement 差 $\leq 0.10$）。"
        )
        hdr = (
            r"\textbf{编号} & \textbf{任务} & \textbf{分层} & \textbf{LLM} & "
            r"\textbf{决策方式} & \textbf{结果} & \textbf{置信度} & "
            r"\textbf{候选摘要} \\"
        )

    lines = [
        r"\begin{responseinlinetable}",
        rf"\responseinlinetablecaption{{{cap}}}",
        r"\label{tab_A1_audit_exemplars}",
        r"\begin{adjustbox}{max width=\textwidth}",
        r"\footnotesize",
        r"\begin{tabular}{llllllccp{0.30\textwidth}}",
        r"\toprule",
        hdr,
        r"\midrule",
    ]
    for i, r in enumerate(rows, start=1):
        rec = f"Rec-{i:02d}"
        if i == 7:
            rec = r"\textbf{Rec-07}"  # narrative anchor in appendix text
        llm = "Yes" if r.get("llm_invoked") else "No"
        if lang == "zh":
            llm = "是" if r.get("llm_invoked") else "否"
        conf = r.get("confidence")
        conf_s = f"{float(conf):.2f}" if conf is not None else "---"
        lines.append(
            " & ".join(
                [
                    rec,
                    _latex_escape(_task_label(r.get("task"), lang)),
                    _latex_escape(_tier(r.get("disagreement_tier"), lang)),
                    llm,
                    _latex_escape(_mode_label(r.get("method"), lang)),
                    _latex_escape(_outcome(r, lang)),
                    conf_s,
                    _latex_escape(_candidates_sketch(r, lang)),
                ]
            )
            + r" \\"
        )
    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{adjustbox}",
        r"\end{responseinlinetable}",
        note,
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log",
        default="output/b6/tn3k/pipeline_run/routing_log.jsonl",
    )
    parser.add_argument(
        "--out-en",
        default="docs/revision/暂定的修改和回复计划/正式回复/latex/generated/routing_audit_appendix_en.tex",
    )
    parser.add_argument(
        "--out-zh",
        default="docs/revision/暂定的修改和回复计划/正式回复/latex/generated/routing_audit_appendix_zh.tex",
    )
    parser.add_argument("-n", type=int, default=12)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[3]
    log_path = root / args.log
    primary, all_rows = _load_records(log_path)
    picked = _pick_exemplars(primary, all_rows, n=args.n)
    if len(picked) < 10:
        raise SystemExit(f"Only picked {len(picked)} exemplars (need >=10)")

    out_en = root / args.out_en
    out_zh = root / args.out_zh
    out_en.parent.mkdir(parents=True, exist_ok=True)
    out_en.write_text(_render_table(picked, "en"), encoding="utf-8")
    out_zh.write_text(_render_table(picked, "zh"), encoding="utf-8")
    print(f"Wrote {len(picked)} exemplars -> {out_en.name}, {out_zh.name}")


if __name__ == "__main__":
    main()
