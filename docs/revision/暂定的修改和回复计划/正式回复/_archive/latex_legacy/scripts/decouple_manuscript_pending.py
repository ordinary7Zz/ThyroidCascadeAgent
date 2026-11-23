#!/usr/bin/env python3
"""Remove non-essential revised-manuscript \\rpending from response letter bodies."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "generated"

MANUSCRIPT_MARKERS = (
    "修订稿",
    "Revised manuscript",
    "Revised Methods",
    "Revised Results",
    "revised Methods",
    "revised Results",
    "revised supplement",
    "修订稿",
    "Methods \\S",
    "Methods~\\S",
    "Discussion",
    "Limitations",
    "Abstract",
    "§2.",
    "§4.",
    "Data availability",
    "Data and Code",
    "主文修订",
    "稿面统一",
    "队列列表表述",
    "分层计数表述",
    "数据流图",
    "Dataflow figure",
    "dataflow figure",
    "Patient--examination",
    "患者—检查",
    "参考标准与标注",
    "Reference-standard",
    "Co-author",
    "合作者书面",
    "G3：",
    "optional:",
    "Optional:",
    "Limitations）",
    "Discussion（",
    "Discussion/Limitations",
    "正文措辞",
    "Results wording",
    "Results R3.2",
    "Results 短段",
    "Results paragraph",
    "五档元数据条件与 Results",
    "统稿",
    "patient-count wording",
    "supplement table (R2.5)",
    "补充表终稿",
    "annotation-protocol",
    "标注协议",
    "ZJH wording",
    "ZJH 定位",
    "连通域与 mask 表述",
    "connected-component",
    "radiomics/AutoGluon",
    "放射组学/AutoGluon 段落",
    "figur",
    "流程图",
    "40 datasets",
    "heterogeneity paragraph",
    "异质性段落",
    "可部署性措辞",
    "deployability",
    "智能体路由的贡献",
    "agentic routing",
    "aligned main text",
    "一致的正文表述",
    "与正文统计表述",
    "main-text statistics",
    "figure notes",
    "图注与",
    "摘要、§",
    "Abstract/\\S",
    "Methods 校准",
    "calibration/referral and Discussion",
    "Methods patient",
    "Methods/\\S2.4",
    "Methods §4.3 五档",
    "Methods §4.3 放射",
    "Methods §4.3 five metadata",
    "Methods will state",
    "将在 Methods",
    "Methods 将写明",
    "Methods 写明",
    "will be stated in Methods",
    "will be auditable in Methods",
    "will document",
    "will clarify",
    "will harmonize",
    "will soften",
    "将统一",
    "将改为",
    "将把",
    "将按队列在 Methods",
    "将弱化",
    "将在全稿",
    "将扩展至修订稿",
    "All 35 centers will appear in the revised",
    "Revised Results will discuss",
    "修订稿 Results 将",
    "完整 35 中心将扩展至修订稿",
    "病例/图像计数（替换送审稿",
    "替换送审稿",
    "叙事与 Discussion",
    "Discussion（R2.10）",
    "LNM 临床定义与病理",
    "Fig.~3",
    "Fig.3",
)


def should_drop_pending(inner: str) -> bool:
    if any(m in inner for m in MANUSCRIPT_MARKERS):
        return True
    # Drop pending that only points to letter tables already cited in same pending
    if re.search(r"tab_(cls|seg)_ext", inner) and "修订" in inner:
        return True
    if "tab_malig" in inner and ("Methods" in inner or "Discussion" in inner or "叙事" in inner):
        return True
    return False


def clean_tex(text: str) -> str:
    def repl_pending(m):
        inner = m.group(1)
        if should_drop_pending(inner):
            return ""
        return m.group(0)

    text = re.sub(r"\\rpendingzh\{([^}]*)\}", repl_pending, text)
    text = re.sub(r"\\rpending\{([^}]*)\}", repl_pending, text)

    # Remove empty \noindent\rpending-only lines
    text = re.sub(r"\n\\noindent\s*\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Prose: decouple manuscript forward refs
    subs = [
        (r"与修订稿 Table", "与投稿 Table"),
        (r"与修订稿 Table", "与投稿 Table"),
        ("修订稿 Table", "投稿 Table"),
        ("修订稿 Supplementary", "投稿补充材料"),
        ("修订稿 Results 将并列说明", "本回复 `tab_component_ablation_*` 已并列说明"),
        ("修订稿 Results 将讨论", "`tab_nhc_center_performance` / `tab_nhc_heterogeneity` 与投稿补充材料一致地讨论"),
        ("完整 35 中心将扩展至修订稿 Supp", "完整 35 中心将列入本回信 `tab_nhc_center_performance` 扩展版"),
        ("All 35 centers will appear in the revised supplement", "All 35 centers will be listed in an expanded `tab_nhc_center_performance` block in this letter"),
        ("Revised Results will discuss", "`tab_nhc_center_performance` / `tab_nhc_heterogeneity` discuss"),
        ("（\\textbf{当前为假设性占位}，NHC 定稿实验后替换）。\\rpendingzh{修订稿 Results 异质性段落[^}]*}", "（\\textbf{当前为假设性占位}，NHC 定稿实验后替换）。"),
        ("修订稿在 \\textbf{TN5K}", "本回复在 \\textbf{TN5K} 试点子集（\\rpendingzh{定稿 $n$=250；当前 `tab_metadata_ablation_*` 为 $n$=10}）"),
        ("The revised manuscript reports", "This letter reports"),
        ("Methods §4.3 将写入同等口径。", "同等口径见附录 A2。"),
        ("Methods \\S4.3 will state the same protocol.", "The same protocol is in Appendix A2."),
        ("将在 Methods 说明阈值拟合", "阈值拟合与评估划分见 \\responsetableref{tab_calib_referral} 及 \\responsefigureref{fig_reliability}、\\responsefigureref{fig_risk_coverage}"),
        ("Methods will state threshold fitting", "Threshold fitting and evaluation splits are in \\responsetableref{tab_calib_referral}, \\responsefigureref{fig_reliability}, and \\responsefigureref{fig_risk_coverage}"),
        ("送复核病例的临床处置边界在 Limitations 与讨论中说明。", "送复核病例的临床处置边界在本回复中作回顾性工作流说明（见上条）。"),
        ("clinical boundaries for flagged cases will be noted in Limitations/Discussion.", "clinical boundaries for flagged cases are described above as part of the retrospective workflow."),
        ("Methods 将写明：分类模型不一致时的 LLM 裁决输入\\textbf{未}纳入本次元数据消融；修订稿 Results 短段与", "分类模型不一致时的 LLM 裁决输入\\textbf{未}纳入本次元数据消融（\\responsetableref{tab_metadata_ablation_cls} 表注）；性能见"),
        ("Methods will state that LLM arbitration inputs used when classifiers disagree were \\textbf{not} included in this metadata ablation; the Results short paragraph will match", "LLM arbitration inputs when classifiers disagree were \\textbf{not} included in this metadata ablation (see \\responsetableref{tab_metadata_ablation_cls} note); performance is in"),
        ("\\responsetablenote{\\rpendingzh{\\responsetableref{tab_dataflow} 配套数据流图（患者—检查—图像—任务）}}", "\\responsetablenote{图像侧训练/验证/测试角色见表内列；患者—检查—图像—任务层级见本表文字说明。}"),
        ("队列组成与修订稿堆叠数据集配置表一致", "队列组成与投稿/OpenThyroid 堆叠开发集定义一致"),
        ("cohort composition per the revised manuscript stacked-dataset configuration table", "cohort composition per the submitted/OpenThyroid stacked development definition"),
        ("统计报告将按下列方式修订。", "统计报告口径如下（支撑表见本条末）。"),
        ("Our statistical reporting will be revised as follows.", "Our statistical reporting is summarized below (supporting tables at the end of this item)."),
        ("我们将在全稿弱化可部署性表述", "我们同意应弱化可部署性表述"),
        ("We will soften deployability claims throughout the manuscript", "We agree to soften deployability claims"),
        ("（与投稿 S4 一致）", "（与投稿补充材料 S4 路由设定一致）"),
        ("will be distinguished in the revised Methods", "is distinguished in \\responsetableref{tab_routing_ablation_seg} notes"),
        ("cluster-bootstrap CI 将在 Methods 写明", "cluster-bootstrap CI 见 \\responsetableref{tab_malig_oof} 表注"),
        ("with cluster-bootstrap CIs will be stated in Methods", "with cluster-bootstrap CIs are in \\responsetableref{tab_malig_oof} notes"),
        ("差异将在 Methods 说明", "差异说明见 \\responsetableref{tab_patient_cls} 与下文"),
        ("we will clarify mapping and exclusions in Methods", "we clarify mapping and exclusions in this response (\\responsetableref{tab_patient_cls})"),
        ("将改为分层叙述并删除误导性", "本回复已改为分层叙述并删除误导性"),
        ("将改为分层叙述", "本回复采用分层叙述"),
        ("无法从公开发布中完全核实患者互斥的队列在 Limitations 中如实说明", "无法从公开发布中完全核实患者互斥的队列在本回复中如实说明"),
        ("cohorts where patient disjointness cannot be fully verified from public releases are noted in Limitations", "such cohorts are noted in this response"),
        ("无 ID 外测队列在 Methods 中说明并按一图一簇处理", "无 ID 外测队列按一图一簇处理（见 R1.1、\\responsetableref{tab_cls_ext} 表注）"),
        ("item \\textbf{流程图}：.*?\\responsetableref{tab_dataflow}", "item \\textbf{数据流（表格式）}：\\responsetableref{tab_dataflow}"),
    ]
    for old, new in subs:
        if old.startswith("item "):
            text = re.sub(old, new, text, flags=re.DOTALL)
        else:
            text = text.replace(old, new)

    # R2.10 second bullet - rewrite future tense to letter refs
    text = text.replace(
        "将：（i）在 Methods 单列 FTC/PTC",
        "（i）FTC/PTC 标签定义与 Dai 等外测集一致（见 \\responsetableref{tab_malig_ext} 表注）；原稿 Methods 将单列",
    )
    text = text.replace(
        "We will: (i) define FTC/PTC labels explicitly in Methods",
        "(i) FTC/PTC labels align with the Dai \\textit{et al.} external test set (\\responsetableref{tab_malig_ext} notes); (i) originally in Methods we will define",
    )

    return text


def main():
    for name in ("body_zh.tex", "body_en.tex"):
        path = ROOT / name
        original = path.read_text(encoding="utf-8")
        cleaned = clean_tex(original)
        path.write_text(cleaned, encoding="utf-8")
        n_before = len(re.findall(r"\\rpending", original))
        n_after = len(re.findall(r"\\rpending", cleaned))
        print(f"{name}: rpending {n_before} -> {n_after}")


if __name__ == "__main__":
    main()
