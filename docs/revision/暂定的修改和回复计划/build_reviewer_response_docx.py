#!/usr/bin/env python3
"""Generate draft point-by-point response docx with embedded figures/tables cited in replies.

Response wording: edit REVIEWER_RESPONSE_DRAFT_EN.md / REVIEWER_RESPONSE_DRAFT_ZH.md (source of truth).
Run this script only when you need an updated REVIEWER_RESPONSE_DRAFT.docx; exhibits stay in EXHIBIT_FNS here.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from docx import Document
from docx.enum.text import WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

SCRIPT_DIR = Path(__file__).resolve().parent
REPO = SCRIPT_DIR.parents[2]
OUT = SCRIPT_DIR / "REVIEWER_RESPONSE_DRAFT.docx"
RESPONSE_MD = {
    "en": SCRIPT_DIR / "REVIEWER_RESPONSE_DRAFT_EN.md",
    "zh": SCRIPT_DIR / "REVIEWER_RESPONSE_DRAFT_ZH.md",
}

B9_LNM_CV = (
    REPO.parent
    / "dino_unet_multitask/Malignant_Cls_Model/b9/runs/lnm_cv/cv_summary.json"
)
B9_FTC_CV = (
    REPO.parent
    / "dino_unet_multitask/Malignant_Cls_Model/b9/runs/ftcptc_cv/cv_summary.json"
)

_MERMAID_FAILED = False

UI = {
    "en": {
        "original_lbl": "Reviewer comment (verbatim, decision letter): ",
        "response_lbl": "Response:",
        "support_lbl": "Supporting figures and tables (draft revision material; not yet in marked-up manuscript):",
        "doc_title": "Response to Reviewers (Draft with embedded figures/tables)",
        "doc_intro": (
            "Manuscript: ThyroidXAgent (Nature Communications — major revision). "
            "This is an initial response draft before formal tracked-changes markup in ThyroidXAgent.md. "
            "Structure per point: (1) bold line = our section label (Reviewer N, Comment M, R ID) — not the reviewer text; "
            "(2) verbatim reviewer comment; (3) author response; (4) embedded draft figures/tables. "
            "At submission, figures/tables move to the manuscript or SI; the letter then cites numbers and page/line only."
        ),
        "deferred_h": "Deferred comments (not in this draft)",
        "body_font": "Times New Roman",
    },
    "zh": {
        "original_lbl": "审稿意见（原文，摘自返修意见稿）：",
        "response_lbl": "回复：",
        "support_lbl": "支撑性图表与表格（修订草稿，尚未写入带痕迹稿）：",
        "doc_title": "审稿意见回复（中文草稿，含嵌入图表）",
        "doc_intro": (
            "稿件：ThyroidXAgent（Nature Communications 大修）。"
            "本文为正式修改稿之前的回复初稿。"
            "每条结构：（1）加粗行仅为小节标题（审稿人序号 + R 编号），不是审稿原文；"
            "（2）审稿意见原文；（3）作者回复；（4）嵌入的草稿图表。"
            "投稿时图表迁入正文/补充材料；回复信仅引用编号与页码行号。"
        ),
        "deferred_h": "本稿暂未回复的意见",
        "body_font": "宋体",
    },
}


def _t(en: str, zh: str, lang: str) -> str:
    return zh if lang == "zh" else en


# Verbatim reviewer text (zh from docs/ThyroidXAgent_返修计划与回复_中文.md; en aligned with Nature Communications Reviews)
REVIEWER_ORIGINAL: dict[str, dict[str, str]] = {
    "R1.1": {
        "en": (
            "Segmentation and classification results are largely reported at the image level. "
            "The authors should clarify patient- and examination-level splits, cross-dataset deduplication, "
            "and whether multiple frames or views from the same patient appear across splits. "
            "Patient-level re-analysis and cluster-aware confidence intervals would strengthen confidence in the reported performance."
        ),
        "zh": (
            "分割与分类结果大多以图像层面报告。作者应澄清患者层面与检查层面的划分、跨数据集的去重，"
            "以及同一患者的多个帧或视图是否会跨划分出现。患者层面的再分析和聚类感知的置信区间会增强对报告性能的信心。"
        ),
    },
    "R1.3": {
        "en": (
            "Although overall performance on the private multi-center cohort is encouraging, performance varies substantially across centers "
            "(e.g., much lower nodule segmentation at some centers). The authors should examine associations with scanner type, image quality, "
            "case mix, and annotation protocols, and define calibration, abstention, or mandatory human review for low-confidence cases."
        ),
        "zh": (
            "尽管在私有多中心队列上的总体性能令人鼓舞，但中心层面差异很大。例如，某些中心的结节分割性能低得多。"
            "作者应研究其与扫描仪类型、图像质量、病例构成与标注协议的关联，并为低置信病例定义校准、拒答或强制人工复核策略。"
        ),
    },
    "R1.4": {
        "en": (
            "ZJH-8K is described as an external test set for segmentation and benign–malignant classification, while its malignant images "
            "are also used to develop LNM and FTC/PTC tasks. The manuscript should provide a complete data-flow diagram showing, for each component, "
            "which data were used for training, validation, threshold selection, and testing."
        ),
        "zh": (
            "ZJH-8K 被描述为分割与良恶性分类的外部测试集，而它的恶性图像又被用于 LNM 与 FTC/PTC 任务的开发。"
            "由于任务不同，这也许可以接受，但稿件应提供一张完整的数据流图，说明每个组件分别用了哪些数据做训练、验证、阈值选择与测试。"
        ),
    },
    "R1.deploy": {
        "en": (
            "The work has clear strengths; however, the current evidence supports a promising retrospective workflow rather than "
            "established clinical benefit or broad deployability. I therefore recommend major revision at minimum."
        ),
        "zh": (
            "该工作有明显优点……然而，当前证据支持的是一条有前景的回顾性工作流，而非已确立的临床获益或广泛可部署性。因此，我建议至少给「大修」。"
        ),
    },
    "R2.1": {
        "en": "Several key numbers are inconsistent across the abstract, main text, figures, and supplementary materials.",
        "zh": "若干关键数值在摘要、正文、图与补充材料之间不一致。",
    },
    "R2.2": {
        "en": (
            "Many analyses are reported at the image level although the same patient, examination, or nodule may have multiple images "
            "(e.g., ZJH-8K contains 7,958 images from 1,149 patients). Treating correlated images as independent may yield overly narrow "
            "confidence intervals. The authors should use patient- or examination-level bootstrap resampling and report patient-level "
            "performance for clinically meaningful classification tasks."
        ),
        "zh": (
            "许多分析以图像层面报告，尽管同一患者、检查或结节可能有多个图像。例如 ZJH-8K 包含来自 1,149 例的 7,958 张图像。"
            "把相关图像当作独立观测可能产生过窄的置信区间。作者应使用患者层面或检查层面的 bootstrap 重采样重算置信区间，"
            "并对具有临床意义的分类任务报告患者层面性能。"
        ),
    },
    "R2.3": {
        "en": (
            "Please clarify why 28,458 observations are described as \"non-overlapping test cases\", as this number appears to combine "
            "19,737 test images with 8,721 NHC-MISD-TUS cases."
        ),
        "zh": (
            "请澄清为什么把 28,458 个观测描述为「non-overlapping test cases」，因为这个数字似乎把 19,737 张测试图像与 8,721 个 NHC-MISD-TUS 病例合并在一起。"
        ),
    },
    "R2.4": {
        "en": (
            "ZJH-8K and TN3K were both collected at Nanfang Hospital, Southern Medical University. Unless patient populations, acquisition periods, "
            "cohort composition, and clinical workflows are demonstrably independent, ZJH-8K should not be described as an external center cohort."
        ),
        "zh": (
            "ZJH-8K 与 TN3K 都采集自南方医科大学珠江医院。除非能证明它们在患者人群、采集时段、队列构成与临床流程上确实独立，"
            "否则 ZJH-8K 不应被描述为外部中心队列。"
        ),
    },
    "R2.7": {
        "en": (
            "The authors should clarify whether reported \"means\" are unweighted macro-averages across cohorts, sample-size-weighted averages, or another scheme."
        ),
        "zh": "作者应澄清所报告的「均值」是跨队列的无权重宏平均、按样本量加权的平均，还是其他计算方式。",
    },
    "R2.9": {
        "en": (
            "The manuscript states that the LLM router \"reasons\" to select the best expert output but does not report prompt design, LLM version, "
            "decoding parameters, reproducibility, or decision stability when candidate quality is similar. "
            "The authors should provide structured routing records for at least ten representative cases."
        ),
        "zh": (
            "稿件称 LLM 路由器通过「推理」选择最佳专家输出，但未报告 prompt 设计、LLM 版本、解码参数、可复现性，"
            "以及当候选输出质量相近时的决策稳定性。……作者应提供至少 10 个代表性病例的结构化路由记录……"
        ),
    },
    "R2.10": {
        "en": (
            "For FTC/PTC classification, the training cohort consists of classic PTC versus follicular-variant PTC, whereas the external test set "
            "uses FTC versus PTC. Follicular-variant PTC is not histologic FTC; training and testing therefore target different definitions."
        ),
        "zh": (
            "对 FTC/PTC 分类，训练队列由经典型 PTC 与滤泡变异型 PTC 组成，而外部测试集由 FTC 与 PTC 组成。"
            "由于滤泡变异型 PTC 并不等同于 FTC，训练与测试的目标定义不同。……"
        ),
    },
    "R2.11": {
        "en": (
            "The LNM task used only 4,753 malignant images, while Table S5 shows validation with only 20 cases. "
            "Please clarify: (a) whether transfer or multitask learning was used; (b) data augmentation; (c) how overfitting was mitigated."
        ),
        "zh": (
            "LNM 任务只使用了 4,753 张恶性图像，而 Table S5 显示验证只有 20 例……"
            "请澄清：(a) 是否使用了迁移学习或多任务学习；(b) 是否做了数据增强；(c) 如何避免过拟合……"
        ),
    },
    "R2.12": {
        "en": (
            "For lymph-node metastasis prediction, the manuscript inconsistently uses overall LNM, lateral LNM, and CN0/CN1 labels, "
            "including primary thyroid lesions on ZJH-8K versus lymph-node images on LymphUs."
        ),
        "zh": "对淋巴结转移预测，稿件不一致地使用总体 LNM、侧颈 LNM 与 CN0/CN1 标签。……",
    },
    "R2.14": {
        "en": (
            "It is unclear whether all expert baselines were retrained on the same development data, evaluated with original weights, or tested zero-shot."
        ),
        "zh": "不清楚所有专家基线是在同一批开发数据上重训、使用原始权重评估，还是零样本测试。……",
    },
    "R2.20": {
        "en": (
            "Thresholds for connected-component post-processing are not specified, including: "
            "(a) minimum component area; (b) whether nodules <5 mm may be removed; (c) how multiple nodules are separated."
        ),
        "zh": (
            "后处理中连通域分析的阈值未说明。……(a) 最小连通域面积阈值；(b) 小于 5 mm 的结节是否可能被误删；(c) 分离多个结节的算法。"
        ),
    },
    "R2.21": {
        "en": "The AutoGluon-based radiomics branch is insufficiently described.",
        "zh": "基于 AutoGluon 的放射组学分支描述不足。",
    },
    "R3.3": {
        "en": (
            "The definition of \"28,458 non-overlapping test cases\" is unclear. Please describe the data hierarchy clearly, confirm patient-disjoint "
            "train/validation/test splits where applicable, and provide a simple flowchart relating patients, examinations, images/videos, lesions, and tasks."
        ),
        "zh": (
            "「28,458 non-overlapping test cases」的定义不清楚。请清楚描述数据层级，并确认所有训练/验证/测试划分都是患者互斥的。"
            "此外，一张展示患者、检查、图像/视频、病灶与任务之间关系的简单流程图会大有帮助。"
        ),
    },
}


def _attach_rid(sections: list, rids: list) -> list:
    """Append reviewer ID as 5th element to each block tuple."""
    out = []
    for (sec_title, blocks), sec_rids in zip(sections, rids):
        new_blocks = []
        for block, rid in zip(blocks, sec_rids):
            title, summary, bullets, exhibits = block
            new_blocks.append((title, summary, bullets, exhibits, rid))
        out.append((sec_title, new_blocks))
    return out


RESPONSE_MD = {
    "en": SCRIPT_DIR / "REVIEWER_RESPONSE_DRAFT_EN.md",
    "zh": SCRIPT_DIR / "REVIEWER_RESPONSE_DRAFT_ZH.md",
}

_REVIEWER_SECTION_TITLES = {
    "en": ["Reviewer 1", "Reviewer 2", "Reviewer 3"],
    "zh": ["审稿人 1", "审稿人 2", "审稿人 3"],
}


def _parse_subsection_body(chunk: str, name: str) -> str:
    m = re.search(rf"### {re.escape(name)}\s*\n(.*?)(?=\n### |\Z)", chunk, re.DOTALL)
    return (m.group(1).strip() if m else "")


def _parse_subsection_first(chunk: str, names: tuple[str, ...]) -> str:
    for name in names:
        body = _parse_subsection_body(chunk, name)
        if body:
            return body
    return ""


_MD_DEFERRED_HEADERS = frozenset({"Deferred", "暂缓回复"})
_MD_TITLE_HEADERS = ("Title", "小节标题")
_MD_REVIEWER_HEADERS = ("Reviewer comment", "审稿意见（原文）")
_MD_RESPONSE_HEADERS = ("Response", "回复")
_MD_EXHIBITS_HEADERS = ("Exhibits", "嵌入图表")
_MD_EXHIBITS_NONE = frozenset({"(none)", "（无）", "none"})


def _parse_response_md(text: str) -> tuple[list[str], dict[str, dict]]:
    """Parse REVIEWER_RESPONSE_DRAFT_*.md → deferred bullets and per-rid blocks."""
    deferred: list[str] = []
    by_rid: dict[str, dict] = {}
    for chunk in re.split(r"\n(?=## )", text):
        chunk = chunk.strip()
        if not chunk.startswith("## "):
            continue
        head, rest = chunk.split("\n", 1)
        label = head[3:].strip()
        if label in _MD_DEFERRED_HEADERS:
            for line in rest.splitlines():
                line = line.strip()
                if line.startswith("- "):
                    deferred.append(line[2:].strip())
            continue
        if not label.startswith("R"):
            continue
        rid = label
        title = _parse_subsection_first(rest, _MD_TITLE_HEADERS)
        reviewer_comment = _parse_subsection_first(rest, _MD_REVIEWER_HEADERS)
        response = _parse_subsection_first(rest, _MD_RESPONSE_HEADERS)
        bullets = [ln[2:].strip() for ln in response.splitlines() if ln.strip().startswith("- ")]
        ex_raw = _parse_subsection_first(rest, _MD_EXHIBITS_HEADERS).strip()
        if not ex_raw or ex_raw.lower() in _MD_EXHIBITS_NONE:
            exhibits: list[str] = []
        else:
            exhibits = [x.strip() for x in ex_raw.replace("\n", ",").split(",") if x.strip()]
        by_rid[rid] = {
            "title": title,
            "reviewer_comment": reviewer_comment,
            "bullets": bullets,
            "exhibits": exhibits,
        }
    return deferred, by_rid


def _set_normal_font(doc: Document, font_name: str):
    style = doc.styles["Normal"]
    style.font.name = font_name
    style._element.rPr.rFonts.set(qn("w:eastAsia"), font_name)


def _load_json(path: Path) -> dict | list | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _sanitize_submission_text(text: str) -> str:
    """Strip internal task codes, repo paths, and forbidden stem narrative from submission-facing text."""
    if not text:
        return text
    forbidden = [
        r"不再以文件名\s*stem[^。；\n]*",
        r"不再以[^。；\n]*stem[^。；\n]*独立[^。；\n]*",
        r"[Ww]e no longer[^.\n]*filename stem[^.\n]*",
        r"\bnot filename stems\b",
        r"filename stem[^。；\n]*独立",
        r"stem\s*无重叠[^。；\n]*",
        r"勿用\s*stem[^。；\n]*",
    ]
    for pat in forbidden:
        text = re.sub(pat, "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*\(B\d+\)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(?:B|F|E|G)\d{1,2}\b", "", text)
    text = re.sub(r"\bB\d+(?:\s*/\s*B\d+)+\b", "", text)
    text = re.sub(r"docs/revision/b\d+/", "", text, flags=re.IGNORECASE)
    text = re.sub(r"output/b\d+/", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bb\d+/tables/", "", text, flags=re.IGNORECASE)
    text = re.sub(r"config/b\d+/", "config/", text, flags=re.IGNORECASE)
    text = text.replace("需要确认.md", "临床合作定稿材料")
    text = text.replace("ThyroidCascadeAgent", "ThyroidXAgent")
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"（\s*）", "", text)
    text = re.sub(r"\(\s*\)", "", text)
    return text.strip()


def add_bullet_with_optional_bold(doc: Document, text: str):
    """List bullet; ``**segment**`` → Word bold (Markdown is not rendered in docx)."""
    text = _sanitize_submission_text(text)
    p = doc.add_paragraph(style="List Bullet")
    parts = re.split(r"\*\*(.+?)\*\*", text)
    for i, part in enumerate(parts):
        if not part:
            continue
        run = p.add_run(part)
        if i % 2 == 1:
            run.bold = True


def add_table(doc: Document, caption: str, headers: list[str], rows: list[list[str]]):
    caption = _sanitize_submission_text(caption)
    headers = [_sanitize_submission_text(h) for h in headers]
    rows = [[_sanitize_submission_text(str(c)) for c in row] for row in rows]
    p = doc.add_paragraph()
    r = p.add_run(caption)
    r.bold = True
    r.font.size = Pt(10)
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    for j, h in enumerate(headers):
        table.rows[0].cells[j].text = h
    for i, row in enumerate(rows):
        for j, cell in enumerate(row):
            table.rows[i + 1].cells[j].text = str(cell)
    doc.add_paragraph()


def add_image(doc: Document, caption: str, path: Path, width_in: float = 6.0):
    caption = _sanitize_submission_text(caption)
    p = doc.add_paragraph()
    r = p.add_run(caption)
    r.bold = True
    r.font.size = Pt(10)
    if path.is_file():
        doc.add_picture(str(path), width=Inches(width_in))
    else:
        doc.add_paragraph(f"[Image not found: {path}]")
    doc.add_paragraph()


def parse_md_pipe_table(md_path: Path, max_cols: int | None = None) -> tuple[list[str], list[list[str]]]:
    lines = [ln.strip() for ln in md_path.read_text(encoding="utf-8").splitlines() if ln.strip().startswith("|")]
    if len(lines) < 2:
        return [], []
    headers = [c.strip() for c in lines[0].split("|")[1:-1]]
    if max_cols:
        headers = headers[:max_cols]
    rows = []
    for ln in lines[2:]:
        cells = [c.strip() for c in ln.split("|")[1:-1]]
        if max_cols:
            cells = cells[:max_cols]
        if len(cells) == len(headers):
            rows.append([_sanitize_submission_text(c) for c in cells])
    return [_sanitize_submission_text(h) for h in headers], rows


def ensure_dataflow_png() -> Path:
    global _MERMAID_FAILED
    mmd = REPO / "docs/revision/b11_b12/DATAFLOW_FIGURE.mmd"
    out = SCRIPT_DIR / "_embed_dataflow_figure.png"
    if out.is_file() and out.stat().st_mtime >= mmd.stat().st_mtime:
        return out
    if not mmd.is_file() or _MERMAID_FAILED:
        return out
    try:
        subprocess.run(
            [
                "npx",
                "-y",
                "@mermaid-js/mermaid-cli",
                "-i",
                str(mmd),
                "-o",
                str(out),
                "-b",
                "white",
                "-w",
                "1400",
            ],
            check=True,
            capture_output=True,
            timeout=120,
            cwd=str(mmd.parent),
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        _MERMAID_FAILED = True
        print(f"Warning: mermaid export failed ({e}); dataflow image may be missing.")
    return out


# --- Exhibit builders (referenced in responses) ---

_COHORT_PAIR_LABELS: dict[str, tuple[tuple[str, str], tuple[str, str]]] = {
    "TN3K_splits_vs_ZJH-8K": (
        ("TN3K (train+val+test)", "TN3K（官方 train+val+test）"),
        ("ZJH-8K", "ZJH-8K"),
    ),
    "TN3K_test_vs_ZJH-8K": (
        ("TN3K (test)", "TN3K（test）"),
        ("ZJH-8K", "ZJH-8K"),
    ),
    "TN5K_splits_vs_ZJH-8K": (
        ("TN5K (train+val+test)", "TN5K（train+val+test）"),
        ("ZJH-8K", "ZJH-8K"),
    ),
    "ThyroidXL_splits_vs_ZJH-8K": (
        ("ThyroidXL (train+val+test)", "ThyroidXL（train+val+test）"),
        ("ZJH-8K", "ZJH-8K"),
    ),
    "TN3K_splits_vs_TN5K_splits": (
        ("TN3K (train+val+test)", "TN3K（train+val+test）"),
        ("TN5K (train+val+test)", "TN5K（train+val+test）"),
    ),
    "TN3K_splits_vs_ThyroidXL_splits": (
        ("TN3K (train+val+test)", "TN3K（train+val+test）"),
        ("ThyroidXL (train+val+test)", "ThyroidXL（train+val+test）"),
    ),
    "TN5K_test_vs_TN5K_train": (
        ("TN5K (test)", "TN5K（test）"),
        ("TN5K (train)", "TN5K（train）"),
    ),
    "DDTI_test_vs_PKTN_test": (
        ("DDTI (test)", "DDTI（test）"),
        ("PKTN (test)", "PKTN（test）"),
    ),
}


def _near_dup_rows(data: dict, keys: list[str], lang: str = "en") -> list[list[str]]:
    comps = data.get("comparisons", {})
    rows: list[list[str]] = []
    for key in keys:
        block = comps.get(key)
        if not block:
            continue
        labels = _COHORT_PAIR_LABELS.get(key)
        if labels:
            left = labels[0][0] if lang == "en" else labels[0][1]
            right = labels[1][0] if lang == "en" else labels[1][1]
        else:
            left = block.get("left_dir", "")
            right = block.get("right_dir", "")
            if "/" in str(left):
                left = Path(str(left)).name or str(left)
            if "/" in str(right):
                right = Path(str(right)).name or str(right)
        rows.append(
            [
                str(left),
                str(right),
                str(block.get("left_n", "")),
                str(block.get("right_n", "")),
                str(block.get("pair_count", "")),
                str(block.get("exact_hamming_0", "")),
                str(block.get("near_only", "")),
            ]
        )
    return rows


# Cohort-vs-cohort (R1.1); excludes stacked-train vs test leakage screen.
CROSS_COHORT_NEAR_DUP_ORDER = [
    "TN3K_splits_vs_ZJH-8K",
    "TN3K_test_vs_ZJH-8K",
    "TN5K_splits_vs_ZJH-8K",
    "ThyroidXL_splits_vs_ZJH-8K",
    "TN3K_splits_vs_TN5K_splits",
    "TN3K_splits_vs_ThyroidXL_splits",
    "TN5K_test_vs_TN5K_train",
    "DDTI_test_vs_PKTN_test",
]

TRAIN_TEST_NEAR_DUP_ORDER = [
    "stacked_train_vs_TN3K_test",
    "stacked_train_vs_TN5K_test",
    "stacked_train_vs_ThyroidXL_test",
    "stacked_train_vs_ZJH-8K",
    "stacked_train_vs_DDTI_test",
    "stacked_train_vs_PKTN_test",
]

_NEAR_DUP_TABLE_HEADERS = (
    ["Cohort A", "Cohort B", "n (A)", "n (B)", "Pairs (H≤5)", "H=0", "Near-only (1–5)"],
    ["队列 A", "队列 B", "n (A)", "n (B)", "配对数 (H≤5)", "H=0", "仅近重复 (1–5)"],
)


def exhibit_near_dup_cohort(doc: Document, lang: str = "en"):
    data = _load_json(REPO / "docs/revision/b1/tables/near_duplicates.json")
    if not data:
        return
    rows = _near_dup_rows(data, CROSS_COHORT_NEAR_DUP_ORDER, lang)
    if not rows:
        return
    add_table(
        doc,
        _t(
            "Table (draft Supp.): dHash cross-cohort near-duplicate screening (Hamming ≤ 5)",
            "表（拟补材料）：dHash 跨基础队列近重复筛查（Hamming ≤ 5）",
            lang,
        ),
        _t(_NEAR_DUP_TABLE_HEADERS[0], _NEAR_DUP_TABLE_HEADERS[1], lang),
        rows,
    )
    note = _t(
        "Each row compares two source cohorts (not the merged development stack). "
        "Patient-level overlap where IDs exist is reported separately in Methods.",
        "每行对比两个来源队列（非合并后的开发堆叠集）。具备患者 ID 的队列在 Methods 中另述患者层面重叠。",
        lang,
    )
    doc.add_paragraph(note)


def exhibit_near_dup_train_test(doc: Document, lang: str = "en"):
    data = _load_json(REPO / "docs/revision/b1/tables/near_duplicates.json")
    if not data:
        return
    rows = _near_dup_rows(data, TRAIN_TEST_NEAR_DUP_ORDER, lang)
    if not rows:
        return
    stack_lbl = _t(
        "OpenThyroid stacked train (dataset_3 + dataset_4)",
        "OpenThyroid 堆叠训练集（dataset_3 + dataset_4）",
        lang,
    )
    test_labels = {
        "stacked_train_vs_TN3K_test": ("TN3K (test)", "TN3K（test）"),
        "stacked_train_vs_TN5K_test": ("TN5K (test)", "TN5K（test）"),
        "stacked_train_vs_ThyroidXL_test": ("ThyroidXL (test)", "ThyroidXL（test）"),
        "stacked_train_vs_ZJH-8K": ("ZJH-8K", "ZJH-8K"),
        "stacked_train_vs_DDTI_test": ("DDTI (test)", "DDTI（test）"),
        "stacked_train_vs_PKTN_test": ("PKTN (test)", "PKTN（test）"),
    }
    out_rows: list[list[str]] = []
    for key in TRAIN_TEST_NEAR_DUP_ORDER:
        block = data.get("comparisons", {}).get(key)
        if not block:
            continue
        t_en, t_zh = test_labels.get(key, (key, key))
        test_lbl = t_en if lang == "en" else t_zh
        out_rows.append(
            [
                stack_lbl,
                test_lbl,
                str(block.get("left_n", "")),
                str(block.get("right_n", "")),
                str(block.get("pair_count", "")),
                str(block.get("exact_hamming_0", "")),
                str(block.get("near_only", "")),
            ]
        )
    rows = out_rows
    add_table(
        doc,
        _t(
            "Table (draft Supp.): dHash stacked development train vs held-out test cohorts",
            "表（拟补材料）：堆叠开发训练集 vs 外测队列 dHash 筛查（训练–测试泄漏风险）",
            lang,
        ),
        _t(_NEAR_DUP_TABLE_HEADERS[0], _NEAR_DUP_TABLE_HEADERS[1], lang),
        rows,
    )


def exhibit_near_dup(doc: Document, lang: str = "en"):
    """Legacy alias: cross-cohort table only."""
    exhibit_near_dup_cohort(doc, lang)


def exhibit_zjh_sensitivity(doc: Document, lang: str = "en"):
    full = _load_json(REPO / "docs/revision/b2/tables/zjh8k_b2.json")
    excl = _load_json(REPO / "docs/revision/b2/tables/zjh8k_b2_excl_train_dup.json")
    if not full or not excl:
        return
    def fmt_cls(d, level="image_level_cluster_bootstrap"):
        c = d["classification"][level]["auroc"]
        return f"{c['mean']:.3f} ({c['ci_lower']:.3f}–{c['ci_upper']:.3f})"

    rows = [
        [
            "ZJH-8K full",
            str(full["classification"]["n_images"]),
            fmt_cls(full),
            f"{full['classification']['patient_level']['auroc']['mean']:.3f}",
            f"{full['segmentation']['image_level_cluster_bootstrap']['dice']['mean']:.3f}",
        ],
        [
            "ZJH-8K excl. train dHash H=0 (992 images)",
            str(excl["classification"]["n_images"]),
            fmt_cls(excl),
            f"{excl['classification']['patient_level']['auroc']['mean']:.3f}",
            f"{excl['segmentation']['image_level_cluster_bootstrap']['dice']['mean']:.3f}",
        ],
    ]
    add_table(
        doc,
        _t(
            "Table (draft Supp.): ZJH-8K sensitivity — full vs excl. train-matched dHash H=0",
            "表（拟补材料）：ZJH-8K 全量 vs 剔除与堆叠训练 dHash H=0 匹配图",
            lang,
        ),
        _t(
            ["Setting", "n images", "Cls AUROC (95% CI)", "Patient AUROC", "Seg Dice"],
            ["设定", "图像数", "分类 AUROC（95% CI）", "患者级 AUROC", "分割 Dice"],
            lang,
        ),
        rows,
    )


# Table S4 layout (matches manuscript tab:cls_performance): methods × five test cohorts.
S4_COHORT_SPECS: list[tuple[str, str, str]] = [
    ("TN3K", "tn3k_cls_bm", "tn3k_b2.json"),
    ("ThyroidXL", "thyroidxl_cls_bm", "thyroidxl_b2.json"),
    ("TN5K", "tn5k_cls_bm", "tn5k_b2.json"),
    ("DDTI", "ddti_cls_cls_bm", "ddti_cls_b2.json"),
    ("ZJH-8K", "zjh8k_cls_bm", "zjh8k_b2.json"),
]
S4_SUPERVISED_MODELS = [
    "ResNet-50",
    "RepViT",
    "LSNet",
    "UltraFedFM",
    "MedSigLIP",
    "BiomedCLIP",
    "ThyroidXAgent",
]


def _baseline_cls_index() -> dict[tuple[str, str], Path]:
    index = _load_json(REPO / "docs/revision/b2/tables/BASELINES_INDEX.json")
    if not index:
        return {}
    out: dict[tuple[str, str], Path] = {}
    for entry in index:
        cid = entry.get("cohort_id", "")
        if "cls_bm" not in cid:
            continue
        out[(entry["model_id"], cid)] = Path(entry["output"])
    return out


def _cls_metric_cell(data: dict | None, metric: str) -> str:
    if not data:
        return "—"
    m = data["classification"]["image_level_cluster_bootstrap"][metric]
    return f"{m['mean']:.4f} ({m['ci_lower']:.4f}–{m['ci_upper']:.4f})"


def _s4_classification_rows(metric: str) -> list[list[str]]:
    b2_dir = REPO / "docs/revision/b2/tables"
    bl = _baseline_cls_index()
    rows: list[list[str]] = []
    for model in S4_SUPERVISED_MODELS:
        row = [model]
        for _col, cohort_id, agent_json in S4_COHORT_SPECS:
            if model == "ThyroidXAgent":
                data = _load_json(b2_dir / agent_json)
            else:
                data = _load_json(bl.get((model, cohort_id)))
            row.append(_cls_metric_cell(data, metric))
        rows.append(row)
    return rows


def exhibit_table_s4_full(doc: Document, lang: str = "en"):
    """Full revision Table S4 (supervised classifiers + ThyroidXAgent), same layout as the manuscript."""
    headers = _t(
        ["Method", "TN3K", "ThyroidXL", "TN5K", "DDTI", "ZJH-8K"],
        ["方法", "TN3K", "ThyroidXL", "TN5K", "DDTI", "ZJH-8K"],
        lang,
    )
    note = _t(
        "Cluster-bootstrap 95% CIs (1000 resamples, seed 42). "
        "Vision-language model rows in the submitted Table S4 are unchanged in layout and will be updated in the final supplement.",
        "均为 cluster-bootstrap 95% CI（1000 次，seed 42）。"
        "投稿版 Table S4 中的视觉-语言模型行版式不变，正式补表中将同步更新其 CI。",
        lang,
    )
    for metric, title_en, title_zh in [
        ("auroc", "AUROC", "AUROC"),
        ("auprc", "AUPRC", "AUPRC"),
    ]:
        rows = _s4_classification_rows(metric)
        if not rows:
            continue
        add_table(
            doc,
            _t(
                f"Table (draft Table S4 — {title_en}): Cross-dataset benign–malignant classification",
                f"表（草稿 Table S4 — {title_zh}）：跨数据集良恶性分类",
                lang,
            ),
            headers,
            rows,
        )
    doc.add_paragraph(note)


def exhibit_table_s4_macro(doc: Document, lang: str = "en"):
    add_table(
        doc,
        _t(
            "Table (draft for R2.1/R2.7): Macro-averaged BM classification means across five Table S4 cohorts "
            "(two rows: AUROC and AUPRC; not five cohort rows)",
            "表（R2.1/R2.7 用）：五个 Table S4 外测队列的良恶性分类汇总均值（两行分别为 AUROC、AUPRC；"
            "不是五个队列各占一行）",
            lang,
        ),
        _t(
            ["Metric", "Unweighted macro mean", "Weighted by test image count"],
            ["指标", "等权宏平均", "按测试图像数加权"],
            lang,
        ),
        [
            ["AUROC", "0.9001", "0.9228"],
            ["AUPRC", "0.8705", "0.9533"],
        ],
    )


def exhibit_table_s5_b9(doc: Document, lang: str = "en"):
    rows = []
    for label_en, label_zh, path in [
        ("LNM (ThyroidXAgent OOF)", "LNM（ThyroidXAgent OOF）", B9_LNM_CV),
        ("FTC/PTC (ThyroidXAgent OOF)", "FTC/PTC（ThyroidXAgent OOF）", B9_FTC_CV),
    ]:
        label = label_zh if lang == "zh" else label_en
        d = _load_json(path)
        if not d:
            rows.append([label, "—", "—", "—", "—", "—"])
            continue
        oof = d.get("oof_patient_level", {})
        ci = d.get("oof_patient_ci", {})
        rows.append(
            [
                label,
                str(int(oof.get("n", 0))),
                f"{oof.get('AUROC', 0):.3f}",
                f"{ci.get('AUROC', ['', ''])[0]:.3f}–{ci.get('AUROC', ['', ''])[1]:.3f}",
                f"{oof.get('AUPRC', 0):.3f}",
                f"{ci.get('AUPRC', ['', ''])[0]:.3f}–{ci.get('AUPRC', ['', ''])[1]:.3f}",
            ]
        )
    add_table(
        doc,
        _t(
            "Table (draft Table S5): ThyroidXAgent LNM/FTC rows (interim DINO OOF)",
            "表（草稿 Table S5）：ThyroidXAgent 恶性子任务行（ interim DINO OOF，全栈融合后可能更新）",
            lang,
        ),
        _t(
            ["Task", "n clusters", "AUROC", "95% CI", "AUPRC", "95% CI"],
            ["任务", "簇数 n", "AUROC", "95% CI", "AUPRC", "95% CI"],
            lang,
        ),
        rows,
    )


def exhibit_b8(doc: Document, lang: str = "en"):
    val_cal = REPO / "output/b8/fit_q95/calibration_val.json"
    cal = _load_json(val_cal)
    if cal:
        add_table(
            doc,
            _t("Table (draft Supp.): Validation calibration", "表（拟补材料）：验证集校准", lang),
            _t(["n", "ECE", "Brier"], ["n", "ECE", "Brier"], lang),
            [[str(cal.get("n", "")), f"{cal.get('ece', 0):.4f}", f"{cal.get('brier', 0):.4f}"]],
        )
    add_image(
        doc,
        _t(
            "Figure (draft Supp.): Validation reliability diagram",
            "图（拟补材料）：验证集可靠性图",
            lang,
        ),
        REPO / "output/b8/fit_q95/reliability_val.png",
        width_in=5.5,
    )
    cohorts = ["tn3k", "tn5k", "thyroidxl", "zjh8k", "ddti_cls"]
    rows = []
    for c in cohorts:
        ev = _load_json(REPO / f"output/b8/cohorts_q95/{c}/abstention_eval.json")
        if not ev:
            continue
        cal = ev.get("calibration", {})
        rows.append(
            [
                c,
                str(ev.get("n_total", "")),
                f"{cal.get('ece', 0):.4f}",
                f"{cal.get('brier', 0):.4f}",
                f"{100 * ev.get('n_flagged', 0) / max(ev.get('n_total', 1), 1):.1f}%",
                str(ev.get("by_center", {}).get("unknown", {}).get("retained_accuracy", "")),
            ]
        )
    add_table(
        doc,
        _t(
            "Table (draft Supp.): Test calibration & abstention (q=0.95 on validation)",
            "表（拟补材料）：外测校准与送复核（验证集 95 分位定阈）",
            lang,
        ),
        _t(
            ["Cohort", "n", "ECE", "Brier", "Flagged %", "Retained accuracy"],
            ["队列", "n", "ECE", "Brier", "送复核%", "保留子集准确率"],
            lang,
        ),
        rows,
    )
    add_image(
        doc,
        _t("Figure (draft Supp.): Risk–coverage panels", "图（拟补材料）：风险–覆盖率曲线", lang),
        REPO / "output/b8/figures/risk_coverage_panels.png",
        width_in=6.2,
    )


def exhibit_dataflow(doc: Document, lang: str = "en"):
    png = ensure_dataflow_png()
    if png.is_file():
        add_image(
            doc,
            _t("Figure (draft Supp.): Image-arm data flow", "图（拟补材料）：图像侧数据流", lang),
            png,
            width_in=6.5,
        )
    else:
        add_table(
            doc,
            _t(
                "Table (draft Supp.): Image-arm data flow (text; export Mermaid when available)",
                "表（拟补材料）：图像侧数据流文字版（待导出 Mermaid 图）",
                lang,
            ),
            _t(["Stage", "Data / threshold"], ["阶段", "数据 / 阈值"], lang),
            _t(
                [
                    ["Stacked training", "Multi-cohort merge (~18k) → DINO-UNet experts"],
                    ["Validation (850)", "Expert selection, routing, abstention thresholds (no test tuning)"],
                    ["AutoGluon radiomics", "dataset_3, GT masks, 17,774 rows"],
                    ["Generic test", "TN3K, TN5K, ThyroidXL, DDTI, ZJH-8K, RJH-7K, NHC"],
                    ["LNM / FTC-PTC", "ZJH malignant + LymphUs; external LymphUs C2 / FangDai"],
                    ["ZJH-8K role", "BM/seg test; experts not trained on ZJH; LNM/FTC dev subset only"],
                ],
                [
                    ["堆叠训练", "多队列合并（约 1.8 万图）→ DINO-UNet 等专家"],
                    ["验证集（850 张）", "专家选择、路由拟合、拒答/送复核阈值（外测不调参）"],
                    ["AutoGluon 放射组学", "dataset_3、GT mask、17,774 训练样本"],
                    ["通用外测", "TN3K、TN5K、ThyroidXL、DDTI、ZJH-8K、RJH-7K、NHC 等"],
                    ["LNM / FTC-PTC", "ZJH 恶性子集 + LymphUs；外测 LymphUs C2 / FangDai"],
                    ["ZJH-8K 角色", "良恶性/分割外测；专家未在 ZJH 训练；恶性子集仅用于 LNM/FTC 开发"],
                ],
                lang,
            ),
        )


def exhibit_b10_protocol(doc: Document, lang: str = "en"):
    md = REPO / "docs/revision/b10/tables/baseline_training_protocol.md"
    headers, rows = parse_md_pipe_table(md, max_cols=4)
    if headers:
        add_table(
            doc,
            _t(
                "Table (draft Supp. S[X]): Baseline training protocol (first four columns)",
                "表（拟补材料 S[X]）：基线训练协议（前四列）",
                lang,
            ),
            headers,
            rows,
        )


def exhibit_r2_20(doc: Document, lang: str = "en"):
    md = REPO / "docs/revision/b11_b12/tables/R2_20_SUMMARY.md"
    headers, rows = parse_md_pipe_table(md)
    if headers:
        add_table(
            doc,
            _t(
                "Table (draft Supp.): R2.20(b) nodules <5 mm — pipeline failures",
                "表（拟补材料）：R2.20(b) <5 mm 结节 — 流水线失败统计",
                lang,
            ),
            headers,
            rows,
        )


def exhibit_radiomics(doc: Document, lang: str = "en"):
    md = REPO / "docs/reproducibility_radiomics.md"
    if not md.is_file():
        return
    text = md.read_text(encoding="utf-8")
    # Pull key parameter lines into a small table
    rows = []
    for pat, label in [
        (r"pyradiomics[^\n]*?(\d+\.\d+\.\d+)", "PyRadiomics version"),
        (r"AutoGluon[^\n]*?(\d+\.\d+\.\d+)", "AutoGluon version"),
        (r"best_quality", "Preset"),
        (r"8-fold|8 fold", "Bagging folds"),
        (r"600\s*s", "Time limit"),
    ]:
        m = re.search(pat, text, re.I)
        if m:
            rows.append([label, m.group(0)[:80]])
    if rows:
        add_table(
            doc,
            _t(
                "Table (draft): Radiomics branch summary",
                "表（草稿）：放射组学分支要点",
                lang,
            ),
            _t(["Item", "Value"], ["项", "值"], lang),
            rows,
        )
    add_image(
        doc,
        _t("Figure (draft Supp.): TN3K test reliability diagram", "图（拟补材料）：TN3K 外测可靠性图", lang),
        REPO / "output/b8/cohorts_q95/tn3k/reliability_test.png",
        width_in=5.0,
    )


def exhibit_b6(doc: Document, lang: str = "en"):
    stab = _load_json(REPO / "output/sample/pipeline_run/stability_summary.json")
    if stab:
        per = stab.get("per_case", [])
        rows = []
        for c in per[:12]:
            rows.append(
                [
                    c.get("image_name", ""),
                    c.get("disagreement_tier", ""),
                    f"{100 * c.get('selection_agreement', 0):.0f}%",
                    f"{100 * c.get('seg_selection_agreement', 0):.0f}%",
                ]
            )
        add_table(
            doc,
            _t(
                "Table (draft Supp.): 5× routing stability (sample n=10)",
                "表（拟补材料）：5 次重复路由稳定性（sample，n=10）",
                lang,
            ),
            _t(
                ["Case", "Tier", "Selection agreement", "Seg selection agreement"],
                ["病例", "分层", "选择一致率", "分割路由一致率"],
                lang,
            ),
            rows,
        )
    log_path = REPO / "output/sample/pipeline_run/routing_log.jsonl"
    if log_path.is_file():
        rows = []
        for i, line in enumerate(log_path.read_text(encoding="utf-8").splitlines()):
            if i >= 10:
                break
            rec = json.loads(line)
            rows.append(
                [
                    rec.get("image_name", rec.get("case_id", ""))[:40],
                    str(rec.get("selected_model", ""))[:30],
                    str(rec.get("llm_invoked", ""))[:10],
                    (rec.get("reasoning", "") or "")[:80],
                ]
            )
        add_table(
            doc,
            _t(
                "Table (draft Supp.): Routing log excerpts (first 10)",
                "表（拟补材料）：结构化 routing log 摘录（前 10 条）",
                lang,
            ),
            _t(
                ["Case", "Selected", "LLM?", "Reason (truncated)"],
                ["病例", "选中专家", "调用 LLM", "理由（截断）"],
                lang,
            ),
            rows,
        )
    spec = REPO / "docs/supplementary/router_spec.md"
    if spec.is_file():
        excerpt = _sanitize_submission_text(
            "\n".join(spec.read_text(encoding="utf-8").splitlines()[:25])
        )
        p = doc.add_paragraph()
        p.add_run(
            _t(
                "Appendix excerpt: supplementary router specification (first 25 lines)",
                "附录摘录：补充材料路由规格（前 25 行）",
                lang,
            )
        ).bold = True
        doc.add_paragraph(excerpt)


EXHIBIT_FNS = {
    "near_dup": exhibit_near_dup,
    "near_dup_cohort": exhibit_near_dup_cohort,
    "near_dup_train_test": exhibit_near_dup_train_test,
    "zjh_sensitivity": exhibit_zjh_sensitivity,
    "table_s4_macro": exhibit_table_s4_macro,
    "table_s4_full": exhibit_table_s4_full,
    "table_s5_b9": exhibit_table_s5_b9,
    "b8": exhibit_b8,
    "dataflow": exhibit_dataflow,
    "b10_protocol": exhibit_b10_protocol,
    "r2_20": exhibit_r2_20,
    "radiomics": exhibit_radiomics,
    "b6": exhibit_b6,
}


# Legacy fallback when REVIEWER_RESPONSE_DRAFT_{EN,ZH}.md is absent. Prefer editing those MD files.
# (title, summary, bullets, exhibit_ids) — rid attached below
SECTIONS_RAW = [
    (
        "Reviewer 1",
        [
            (
                "Reviewer 1 — Comment 1 (R1.1)",
                "Segmentation and classification results are largely reported at the image level. "
                "The authors should clarify patient- and examination-level splits, cross-dataset deduplication, "
                "and whether multiple frames from the same patient appear across splits. Patient-level re-analysis "
                "and cluster-aware confidence intervals would strengthen confidence in the reported performance.",
                [
                    "We thank the reviewer for this important point. We revised our statistical reporting as follows.",
                    "Independence and near-duplicates. We screened **between source cohorts** using perceptual hashing "
                    "(dHash, Hamming ≤ 5; see embedded cross-cohort table). TN3K (official train+val+test) and ZJH-8K share "
                    "**1156** H=0 image pairs; TN3K test and ZJH-8K share **2** H=0 pairs. "
                    "A separate stacked-development-train vs held-out-test screen (R2.4) quantifies train–test leakage risk. "
                    "Cluster definitions. Where patient IDs are available (ZJH-8K, ThyroidXL), we use patient-level clusters; "
                    "for cohorts without IDs, we use one image per cluster. Bootstrap CIs (1000 resamples, seed 42) are cluster-aware.",
                    "Patient-level classification. For ZJH-8K and ThyroidXL we report patient-level AUROC/AUPRC after aggregating "
                    "image probabilities (arithmetic mean within patient).",
                    "Cluster-bootstrap confidence intervals. We recomputed 95% CIs using 1000 cluster bootstrap resamples "
                    "(seed 42). The embedded tables reproduce revised **Table S4** in full manuscript layout "
                    "(all supervised classifiers and ThyroidXAgent × five test cohorts; AUROC and AUPRC blocks). "
                    "Table S3 (segmentation) is updated similarly in the supplement (Methods §4.6). "
                    "DDTI classification uses n=349 labeled images.",
                    "Sensitivity analysis. For ZJH-8K we additionally report results excluding 992 images matched to stacked training by dHash "
                    "(see embedded supplementary table below).",
                ],
                ["near_dup_cohort", "zjh_sensitivity", "table_s4_full"],
            ),
            (
                "Reviewer 1 — Comment 3 (R1.3)",
                "Performance varies substantially across centers. The authors should examine associations with scanner type, "
                "image quality, and case mix, and define calibration, abstention, or mandatory review for low-confidence cases.",
                [
                    "We agree that center heterogeneity matters. Center-level meta-analyses for NHC-MISD-TUS (Reviewer 2, Comment 6) "
                    "will be reported separately when center metadata are finalized (see our response to Reviewer 2, Comment 6). "
                    "Here we address calibration and abstention for the five benign–malignant classification test cohorts with pathology labels.",
                    "We fixed abstention thresholds on the OpenThyroid validation merge (n=875 images, same non-LLM inference protocol as testing), "
                    "using vote entropy, top-2 margin, and minimum pairwise segmentation IoU among experts. Thresholds are the 95th percentile "
                    "of each score on validation (no test-set tuning).",
                    "On the labeled validation subset we report pooled ECE and Brier (see embedded table and reliability figure).",
                    "On TN3K, TN5K, ThyroidXL, ZJH-8K, and DDTI_cls test sets we report ECE, Brier, abstention rates (~43–48% flagged), "
                    "and risk–coverage curves (embedded below).",
                ],
                ["b8"],
            ),
            (
                "Reviewer 1 — Comment 4 (R1.4)",
                "ZJH-8K is used as an external test set for segmentation and benign–malignant classification, while malignant images "
                "are also used to develop LNM and FTC/PTC tasks. A complete data-flow diagram should show train/validation/threshold/test "
                "for each component.",
                [
                    "We agree. Segmentation and generic benign–malignant experts were not trained on ZJH-8K. The malignant subset of ZJH-8K "
                    "is used only for task-specific LNM and FTC/PTC development, with external testing on LymphUs Center 2 and FangDai, respectively.",
                    "We provide the image-arm data-flow figure below (to be numbered Supplementary Figure S-X in the revision).",
                ],
                ["dataflow"],
            ),
            (
                "Reviewer 1 — General remark (deployability)",
                "The evidence supports a promising retrospective workflow rather than established clinical benefit or broad deployability.",
                [
                    "We softened deployability claims throughout the manuscript and emphasize retrospective evaluation, "
                    "revised statistical reporting (data auditing and cluster-bootstrap confidence intervals), and explicit limitations. "
                    "Code release improvements are described in the Data and Code Availability statement.",
                ],
                [],
            ),
        ],
    ),
    (
        "Reviewer 2",
        [
            (
                "Reviewer 2 — Comment 1 (R2.1)",
                "Several key numbers are inconsistent across abstract, main text, figures, and supplements.",
                [
                    "We apologize and thank the reviewer. We reconciled all numbers against source exports.",
                    "Benign–malignant classification means (abstract, §2.2): corrected to unweighted macro-averages over five Table S4 cohorts "
                    "(embedded table). Figure 3b axis labels were swapped and are corrected to match Table S5.",
                    "LNM training pool size corrected to 4,936 images (4,756 ZJH-8K malignant + 180 LymphUs Center 1); five-fold CV uses 4,753 images "
                    "in the combined development manifest (Table S5 excerpt below).",
                ],
                ["table_s4_macro", "table_s5_b9"],
            ),
            (
                "Reviewer 2 — Comment 2 (R2.2)",
                "Treating correlated images as independent may yield overly narrow CIs. Patient- or examination-level bootstrap and patient-level "
                "performance for clinically meaningful classification tasks are requested.",
                [
                    "We agree. All segmentation and classification confidence intervals in Tables S3–S5 now use cluster bootstrap "
                    "(1000 resamples, seed 42). Patient-level classification metrics are reported for ZJH-8K and ThyroidXL as in R1.1 "
                    "(ZJH example embedded below).",
                ],
                ["zjh_sensitivity"],
            ),
            (
                "Reviewer 2 — Comment 3 (R2.3)",
                "Clarify what the 28,458 observations represent.",
                [
                    "The reviewer is correct: 28,458 sums 19,737 test images from seven segmentation/classification cohorts and 8,721 NHC-MISD-TUS cases. "
                    "We replaced this phrase with stratified counts; the image-arm data-flow figure (below) summarizes splits.",
                ],
                ["dataflow"],
            ),
            (
                "Reviewer 2 — Comment 4 (R2.4)",
                "Unless independence is demonstrated, ZJH-8K should not be described as an external center cohort.",
                [
                    "dHash cross-cohort screening found **1156** H=0 pairs between TN3K (train+val+test) and ZJH-8K, and **2** H=0 pairs between TN3K test and ZJH-8K "
                    "(embedded cross-cohort table under R1.1). Primary results retain full ZJH-8K with a sensitivity analysis excluding images matched to "
                    "stacked development training (embedded table). Train–test leakage counts are in the supplementary table below.",
                ],
                ["near_dup_train_test", "zjh_sensitivity"],
            ),
            (
                "Reviewer 2 — Comment 7 (R2.7)",
                "Clarify whether reported means are unweighted macro-averages, sample-size-weighted averages, or other.",
                [
                    "All cross-cohort “means” for benign–malignant classification are unweighted macro-averages over five Table S4 test cohorts. "
                    "Corrected values and per-cohort point estimates are in the embedded tables below.",
                ],
                ["table_s4_macro"],
            ),
            (
                "Reviewer 2 — Comment 9 (R2.9)",
                "The manuscript does not report prompt design, LLM version, decoding parameters, reproducibility, or stability when candidate quality is similar.",
                [
                    "We provide router specifications, structured routing logs, and five-repeat stability results in the embedded tables and excerpt below.",
                ],
                ["b6"],
            ),
            (
                "Reviewer 2 — Comment 10 (R2.10)",
                "Training uses classic PTC vs follicular-variant PTC while external testing uses PTC vs FTC; definitions differ.",
                [
                    "We describe FangDai evaluation as exploratory domain shift. Internal five-fold OOF for ThyroidXAgent is in the embedded Table S5 excerpt "
                    "(interim DINO multitask OOF; full-stack fusion may update numbers). FangDai external results will follow development-set retraining.",
                ],
                ["table_s5_b9"],
            ),
            (
                "Reviewer 2 — Comment 11 (R2.11)",
                "LNM used 4,753 malignant images with only 20 validation cases; questions on transfer learning, augmentation, and overfitting.",
                [
                    "We replaced the 20-case hold-out with patient-level stratified five-fold CV (4,753 images, 882 clusters; seed 42). "
                    "Out-of-fold metrics with cluster-bootstrap CIs are in the embedded Table S5 excerpt.",
                ],
                ["table_s5_b9"],
            ),
            (
                "Reviewer 2 — Comment 12 (R2.12)",
                "Inconsistent use of overall LNM, lateral LNM, and CN0/CN1 labels; ZJH primary lesions vs LymphUs lymph-node images.",
                [
                    "We harmonized terminology and clustering rules (ZJH by year/name; LymphUs Center 1 one image per cluster). "
                    "Clinical definitions will be finalized with co-authors; statistical protocol matches Table S5 below.",
                ],
                ["table_s5_b9"],
            ),
            (
                "Reviewer 2 — Comment 14 (R2.14)",
                "Unclear whether baselines were retrained on the same development data, used original weights, or were zero-shot.",
                [
                    "We added Supplementary Table S[X] documenting baseline training and inference protocols (excerpt embedded below).",
                ],
                ["b10_protocol"],
            ),
            (
                "Reviewer 2 — Comment 20 (R2.20)",
                "Thresholds for connected-component analysis are unspecified; impact on nodules <5 mm and multi-nodule separation.",
                [
                    "Methods now state ≥50 px components inside experts; reported Dice and radiomics use the same selected mask. "
                    "Small-nodule statistics are in the embedded table (mm_per_pixel=0.1 sensitivity assumption).",
                ],
                ["r2_20"],
            ),
            (
                "Reviewer 2 — Comment 21 (R2.21)",
                "Insufficient detail on the radiomics tabular branch.",
                [
                    "We expanded Methods §4.3 and the Supplementary radiomics specification; key parameters and an example reliability figure are embedded below.",
                ],
                ["radiomics"],
            ),
        ],
    ),
    (
        "Reviewer 3",
        [
            (
                "Reviewer 3 — Comment 3 (R3.3)",
                "Clarify data hierarchy and the claim of 40 datasets.",
                [
                    "We aligned this response with R2.3 and R1.4 using the embedded data-flow figure and cross-cohort dHash table (R1.1).",
                ],
                ["dataflow", "near_dup_cohort"],
            ),
        ],
    ),
]

SECTIONS_ZH_RAW = [
    (
        "审稿人 1",
        [
            (
                "审稿人 1 — 意见 1（R1.1）",
                "分割与分类多在图像层面报告。应澄清患者/检查层面划分、跨数据集去重、同一患者多帧是否跨划分出现；"
                "建议做患者层面再分析与聚类感知的置信区间。",
                [
                    "感谢审稿人。我们已按下列方式修订统计报告。",
                    "独立性与近重复：对**各来源基础队列之间**做感知哈希（dHash，Hamming ≤ 5）筛查（见下方跨队列表，非堆叠训练集口径）。"
                    "TN3K（官方 train+val+test）与 ZJH-8K：H=0 **1156** 对；TN3K **test** 与 ZJH-8K：H=0 **2** 对。"
                    "堆叠开发训练 vs 外测的泄漏风险筛查见 R2.4 及对应补充表。",
                    "聚类定义：ZJH-8K、ThyroidXL 使用可复现 patient ID；无 ID 队列 **一图一簇**。Bootstrap **1000** 次、**seed=42**，CI 为 cluster-aware。",
                    "患者级分类：ZJH-8K、ThyroidXL 对图像概率 **簇内/患者内算术平均** 后报告 AUROC/AUPRC。",
                    "聚类 bootstrap 置信区间：均用 **1000** 次聚类 bootstrap（**seed=42**）重算 **95% CI**。"
                    "下方嵌入表为修订稿 **Table S4** 的完整版式（**7** 个方法 × **5** 个外测队列，含 AUROC 与 AUPRC 两块），"
                    "与正文补充表结构一致；**Table S3**（分割）在补充材料中同样更新。**DDTI** 分类外测 **n=349**。",
                    "ZJH-8K 敏感性：剔除与堆叠训练 dHash H=0 匹配的 **992** 张图后重算（不重训），见下方表。",
                ],
                ["near_dup_cohort", "zjh_sensitivity", "table_s4_full"],
            ),
            (
                "审稿人 1 — 意见 3（R1.3）",
                "中心间差异大；应分析扫描仪、图像质量、病例构成，并定义校准、拒答或强制人工复核策略。",
                [
                    "我们同意中心异质性重要。NHC-MISD-TUS 中心级分析（审稿人 2 意见 6）待中心元数据齐备后单独报告（见对审稿人 2 意见 6 的回复）。"
                    "此处就五个有良恶性病理标签的外测队列报告校准与送复核策略。",
                    "在 OpenThyroid **validation** 合并集（**n=875**，与非 LLM 测试协议一致）上，以投票熵、top-2 margin、分割专家最小 pairwise IoU "
                    "定义不确定度，各指标取 **95 分位数** 定阈（**不在测试集调参**）。",
                    "有标签 validation 子集 pooled **ECE≈0.088**、**Brier≈0.078**（见下图表）。",
                    "TN3K、TN5K、ThyroidXL、ZJH-8K、DDTI_cls 外测报告 ECE/Brier、送复核比例（约 **43–48%**）及 risk–coverage 曲线（见下方）。",
                ],
                ["b8"],
            ),
            (
                "审稿人 1 — 意见 4（R1.4）",
                "ZJH-8K 既作分割/良恶性外测，又用于 LNM/FTC 开发；需完整数据流图标明各组件 train/val/阈值/test。",
                [
                    "分割与通用良恶性专家 **未在 ZJH-8K 训练**；ZJH 恶性子集仅用于 LNM/FTC 任务开发，"
                    "外测分别为 LymphUs C2 与 FangDai。图像侧数据流见下方图/表（正式稿拟为补充图 S-X）。",
                ],
                ["dataflow"],
            ),
            (
                "审稿人 1 — 总评（可部署性）",
                "证据支持的是有前景的回顾性工作流，而非已确立的临床获益或广泛可部署性。",
                [
                    "我们已在全稿弱化可部署性表述，强调回顾性评估、修订后的统计报告（数据审计与 cluster-bootstrap 置信区间）及明确局限性；"
                    "代码可用性见数据与代码可用性声明。",
                ],
                [],
            ),
        ],
    ),
    (
        "审稿人 2",
        [
            (
                "审稿人 2 — 意见 1（R2.1）",
                "摘要、正文、图与补充材料间存在关键数字不一致。",
                [
                    "我们致歉并已按源结果逐项核对。",
                    "良恶性分类「均值」（摘要、§2.2）：更正为 Table S4 **五队列等权宏平均** AUROC **0.9001**、AUPRC **0.8705**（见下表）；"
                    "加权均值 AUROC **0.9228**、AUPRC **0.9533**。",
                    "Fig.3b：AUROC/AUPRC 轴标签标反，已与 Table S5 对齐。",
                    "LNM 训练池更正为 **4936** 图（4756 ZJH 恶性 + 180 LymphUs C1）；五折 CV 合并 manifest **4753** 图（见 Table S5 摘录）。",
                ],
                ["table_s4_macro", "table_s5_b9"],
            ),
            (
                "审稿人 2 — 意见 2（R2.2）",
                "将相关图像当作独立观测可能导致 CI 过窄；建议患者/检查 bootstrap 及患者级分类性能。",
                [
                    "我们同意。Tables S3–S5 等 CI 均改为 cluster bootstrap（1000，seed 42）。"
                    "ZJH-8K、ThyroidXL 患者级分类见 R1.1；ZJH 示例见下表。",
                ],
                ["zjh_sensitivity"],
            ),
            (
                "审稿人 2 — 意见 3（R2.3）",
                "请澄清 28,458 所指层级。",
                [
                    "审稿人正确：28,458 = 七个分割/分类队列 **19,737** 张测试图 + NHC **8,721** 例之和；"
                    "称「cases」不准确且未含报告生成与恶性子任务测试。已改为分层计数，见数据流图/表。",
                ],
                ["dataflow"],
            ),
            (
                "审稿人 2 — 意见 4（R2.4）",
                "除非证明独立，不宜将 ZJH-8K 描述为外部中心队列。",
                [
                    "跨队列 dHash（R1.1 表）：TN3K（train+val+test）与 ZJH-8K **1156** 对 H=0；TN3K **test** 与 ZJH 仅 **2** 对 H=0。"
                    "主结果保留全量 ZJH-8K，并补充剔除与堆叠开发训练 dHash 匹配图的敏感性分析（下表）。"
                    "堆叠训练 vs 外测泄漏筛查见下表；患者级重叠在补充材料或 Limitations 中说明。",
                ],
                ["near_dup_train_test", "zjh_sensitivity"],
            ),
            (
                "审稿人 2 — 意见 7（R2.7）",
                "请澄清均值为宏平均、加权平均或其他。",
                [
                    "跨五个 Table S4 外测队列的「均值」均为 **等权宏平均**；更正数字与分队列点估计见下表。",
                ],
                ["table_s4_macro"],
            ),
            (
                "审稿人 2 — 意见 9（R2.9）",
                "未报告 prompt、LLM 版本、解码参数、可复现性及候选接近时的决策稳定性。",
                [
                    "补充材料提供 router 完整规格、结构化 routing_log，并在固定专家输出下对 **10** 例每例 **5** 次重复路由："
                    "平均选择一致率 **92%**（8/10 全稳，2/10 为 60%，close 层）。见下表与 router_spec 摘录。",
                ],
                ["b6"],
            ),
            (
                "审稿人 2 — 意见 10（R2.10）",
                "训练为 cPTC vs FVPTC，外测为 PTC vs FTC，定义不一致。",
                [
                    "我们承认 FVPTC≠组织学 FTC，将 FangDai 外测表述为 **探索性域迁移**，与主结论区分。",
                    "ThyroidXAgent 内部验证：ZJH **4756** 图、**722** 簇、五折 OOF（下表；interim DINO OOF，全栈融合后可能更新）。"
                    "FangDai（n=199）ThyroidXAgent 外测将在全开发集重训后更新；组织学 FTC 与训练标签不一致之处在 Limitations 中与临床合作者说明。",
                ],
                ["table_s5_b9"],
            ),
            (
                "审稿人 2 — 意见 11（R2.11）",
                "LNM 仅 4753 图、20 例验证；询问迁移学习、增强与过拟合。",
                [
                    "训练规模更正为 **4936** 图；将 20 例 val 改为 **882** 簇上 **患者级分层五折 OOF**（seed 42），cluster bootstrap 95% CI。"
                    "Table S5 ThyroidXAgent LNM：AUROC **0.718（0.678–0.754）**，AUPRC **0.598（0.536–0.655）**（下表）。"
                    "LymphUs C2（n=158）全栈外测将在开发集重训与评估完成后更新 Table S5。",
                ],
                ["table_s5_b9"],
            ),
            (
                "审稿人 2 — 意见 12（R2.12）",
                "LNM、侧颈 LNM、CN0/CN1 用法不一致；ZJH 原发灶图 vs LymphUs 淋巴结图。",
                [
                    "我们统一标签键与聚类规则（ZJH：**年/姓名**；LymphUs C1：**一图一簇**）；簇内概率平均与 R2.11 一致。"
                    "临床定义句待与病理/临床合作者定稿；统计协议见 Table S5。",
                ],
                ["table_s5_b9"],
            ),
            (
                "审稿人 2 — 意见 14（R2.14）",
                "不清楚基线是否同数据重训、用原始权重或零样本。",
                [
                    "新增补充表 S[X] 记录基线训练与推理协议（下表为摘录）。"
                    "监督分割/分类基线均在 OpenThyroid 堆叠开发集（dataset_4 / dataset_3）微调；VLM 等单独说明；外测仅用于 test。",
                ],
                ["b10_protocol"],
            ),
            (
                "审稿人 2 — 意见 20（R2.20）",
                "连通域阈值未说明；<5 mm 结节与多结节分离。",
                [
                    "Methods 已更正：报告 Dice 与 radiomics **共用 selected mask**；专家内部 ≥**50** 像素连通域、5×5 闭运算；**单图单 ROI**。"
                    "<5 mm 统计见下表（**mm_per_pixel=0.1** 敏感性假设；M 为整条流水线失败，非 radiomics 前删除）。",
                ],
                ["r2_20"],
            ),
            (
                "审稿人 2 — 意见 21（R2.21）",
                "放射组学表格分支描述不足。",
                [
                    "已扩充 Methods §4.3 与补充材料中的放射组学规范；要点表与示例外测可靠性图见下方。",
                ],
                ["radiomics"],
            ),
        ],
    ),
    (
        "审稿人 3",
        [
            (
                "审稿人 3 — 意见 3（R3.3）",
                "请澄清数据层级及 40 datasets 表述。",
                [
                    "与 R2.3、R1.4 合并回应：见下方数据流与 R1.1 跨队列 dHash 表；「40 datasets」在修订稿中定义或改为明示列表。",
                ],
                ["dataflow", "near_dup_cohort"],
            ),
        ],
    ),
]

COMMENT_RIDS = [
    ["R1.1", "R1.3", "R1.4", "R1.deploy"],
    [
        "R2.1",
        "R2.2",
        "R2.3",
        "R2.4",
        "R2.7",
        "R2.9",
        "R2.10",
        "R2.11",
        "R2.12",
        "R2.14",
        "R2.20",
        "R2.21",
    ],
    ["R3.3"],
]

SECTIONS = _attach_rid(SECTIONS_RAW, COMMENT_RIDS)
SECTIONS_ZH = _attach_rid(SECTIONS_ZH_RAW, COMMENT_RIDS)

DEFERRED = {
    "en": [
        "R1.2, R2.8, R3.1 — routing and component ablations (pending supplementary experiments).",
        "R1.5–R1.6, R2.13, R2.16–R2.19, R3.4–R3.5 — report generation and reader studies.",
        "R2.5 — reference standards and annotation protocols. R2.6 — NHC-MISD-TUS center-level analyses.",
        "R2.15, R2.22–R2.23, R2 code — ethics, language, TI-RADS, code release.",
        "R3.2 — routing metadata ablation.",
    ],
    "zh": [
        "R1.2、R2.8、R3.1 — 路由与组件消融（补充实验进行中）。",
        "R1.5–6、R2.13、R2.16–19、R3.4–5 — 报告生成与读者研究（Shiyu / Fei Chen）。",
        "R2.5 — 参考标准与标注协议。R2.6 — NHC-MISD-TUS 中心级分析。",
        "R2.15、R2.22–23、R2 代码 — 伦理、语言、TI-RADS、代码发布。",
        "R3.2 — 路由元数据消融。",
    ],
}


def _sections_from_md(lang: str) -> tuple[list, list[str]]:
    path = RESPONSE_MD[lang]
    if not path.is_file():
        raise FileNotFoundError(path)
    deferred, by_rid = _parse_response_md(path.read_text(encoding="utf-8"))
    sections = []
    for sec_title, sec_rids in zip(_REVIEWER_SECTION_TITLES[lang], COMMENT_RIDS):
        blocks = []
        for rid in sec_rids:
            if rid not in by_rid:
                raise KeyError(f"Missing ## {rid} in {path.name}")
            rec = by_rid[rid]
            blocks.append(
                (rec["title"], "", rec["bullets"], rec["exhibits"], rid, rec.get("reviewer_comment", ""))
            )
        sections.append((sec_title, blocks))
    return sections, deferred


def _load_sections_and_deferred(lang: str) -> tuple[list, list[str]]:
    path = RESPONSE_MD[lang]
    if path.is_file():
        return _sections_from_md(lang)
    return (SECTIONS if lang == "en" else SECTIONS_ZH), DEFERRED[lang]


def add_comment_block(
    doc,
    title,
    summary,
    bullets,
    exhibit_ids: list[str],
    lang: str,
    rid: str,
    reviewer_comment: str = "",
):
    ui = UI[lang]
    p = doc.add_paragraph()
    run = p.add_run(title)
    run.bold = True
    run.font.size = Pt(11)
    sub = doc.add_paragraph()
    sub_run = sub.add_run(_t("(Section label only — full reviewer text below.)", "（仅为小节编号，完整审稿意见见下。）", lang))
    sub_run.italic = True
    sub_run.font.size = Pt(9)
    orig = (reviewer_comment or "").strip() or REVIEWER_ORIGINAL.get(rid, {}).get(lang, "")
    if orig:
        o = doc.add_paragraph()
        o_run = o.add_run(ui["original_lbl"])
        o_run.bold = True
        body = doc.add_paragraph(orig)
        body.paragraph_format.left_indent = Inches(0.25)
    r = doc.add_paragraph()
    r_run = r.add_run(ui["response_lbl"])
    r_run.bold = True
    for b in bullets:
        add_bullet_with_optional_bold(doc, b)
    if exhibit_ids:
        doc.add_paragraph()
        h = doc.add_paragraph()
        h.add_run(ui["support_lbl"]).bold = True
        for eid in exhibit_ids:
            fn = EXHIBIT_FNS.get(eid)
            if fn:
                fn(doc, lang)


def append_response_language(doc: Document, lang: str, sections, deferred: list[str] | None = None):
    ui = UI[lang]
    deferred = deferred if deferred is not None else DEFERRED[lang]
    _set_normal_font(doc, ui["body_font"])
    style = doc.styles["Normal"]
    style.font.size = Pt(11)
    style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE

    doc.add_heading(ui["doc_title"], level=0)
    doc.add_paragraph(ui["doc_intro"])

    for section_title, blocks in sections:
        doc.add_heading(section_title, level=1)
        for block in blocks:
            reviewer_comment = ""
            if len(block) == 6:
                title, summary, bullets, exhibit_ids, rid, reviewer_comment = block
            else:
                title, summary, bullets, exhibit_ids, rid = block
            add_comment_block(
                doc, title, summary, bullets, exhibit_ids, lang, rid, reviewer_comment
            )

    doc.add_heading(ui["deferred_h"], level=1)
    for d in deferred:
        doc.add_paragraph(_sanitize_submission_text(d), style="List Bullet")


_FORBIDDEN_IN_OUTPUT = [
    re.compile(r"不再以文件名"),
    re.compile(r"stem\s*无重叠", re.I),
    re.compile(r"not filename stems", re.I),
    re.compile(r"no longer.*filename stem", re.I),
    re.compile(r"\bB\d{1,2}\b"),
    re.compile(r"\bF\d{1,2}\b"),
    re.compile(r"\bE\d{1,2}\b"),
    re.compile(r"\bG\d{1,2}\b"),
    re.compile(r"docs/revision/b\d", re.I),
    re.compile(r"需要确认\.md"),
]


def _assert_submission_clean(docx_path: Path) -> None:
    import zipfile
    from xml.sax.saxutils import unescape

    with zipfile.ZipFile(docx_path) as zf:
        xml = "".join(
            zf.read(n).decode("utf-8", errors="replace")
            for n in zf.namelist()
            if n.startswith("word/") and n.endswith(".xml")
        )
    text = unescape(re.sub(r"<[^>]+>", "", xml))
    # Allow metric tokens that look like internal codes (e.g. thyroid E2E train, lesion F1).
    text_for_codes = re.sub(r"E2E", "E2E_TRAIN", text, flags=re.I)
    text_for_codes = re.sub(r"(?<![A-Za-z])F1(?![A-Za-z0-9])", "F1_METRIC", text_for_codes)
    hits: list[str] = []
    for pat in _FORBIDDEN_IN_OUTPUT:
        if pat.search(text if "E2" not in pat.pattern else text_for_codes):
            m = pat.search(text if "E2" not in pat.pattern else text_for_codes)
            if m:
                i = m.start()
                hits.append(f"{pat.pattern}: …{text_for_codes[max(0, i - 40) : i + 60]}…")
    if hits:
        raise SystemExit("Submission docx failed cleanliness check:\n" + "\n".join(hits[:12]))


def main():
    sections_en, deferred_en = _load_sections_and_deferred("en")
    sections_zh, deferred_zh = _load_sections_and_deferred("zh")
    doc = Document()
    append_response_language(doc, "en", sections_en, deferred_en)
    doc.add_page_break()
    append_response_language(doc, "zh", sections_zh, deferred_zh)
    doc.save(OUT)
    _assert_submission_clean(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
