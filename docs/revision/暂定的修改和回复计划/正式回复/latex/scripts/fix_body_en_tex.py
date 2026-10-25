#!/usr/bin/env python3
"""Clean up body_en.tex: structure fixes + English appendix labels."""
import re
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "generated" / "body_en.tex"

REPLACEMENTS = [
    (
        "Tables and figures cited in the point-by-point responses above.；编号 \\textbf{R1–R13}、\\textbf{图 R1–R2} 与正文交叉引用一致。与修订稿 Supplementary Tables S3–S5 等同者保留原表号。",
        "Tables and figures cited in the point-by-point responses above. Labels \\textbf{R1--R13} and \\textbf{Figures R1--R2} match in-text cross-references. Entries aligned with revised Supplementary Tables S3--S5 retain the original table numbers.",
    ),
    ("\\reviewersection{Table R1. dHash 跨基础队列近重复筛查（Hamming ≤ 5）}", "\\reviewersection{Table R1. dHash cross-cohort near-duplicate screening (Hamming $\\leq$ 5)}"),
    ("TN3K（train+val+test）", "TN3K (train+val+test)"),
    ("TN3K（test）", "TN3K (test)"),
    ("方法 &", "Method &"),
    ("Note: \\textbf{Dice} 为 \\textbf{\\%}（↑），\\textbf{HD95} 为 \\textbf{mm}（↓）；数值为点估计 \\textbf{±} 95\\% CI 半宽（cluster bootstrap，1000 次，seed=42，图像级）。",
     "Note: \\textbf{Dice} in \\textbf{\\%} ($\\uparrow$), \\textbf{HD95} in \\textbf{mm} ($\\downarrow$); point estimate $\\pm$ half-width of 95\\% CI (cluster bootstrap, 1000 resamples, seed=42, image-level)."),
    ("\\textbf{Dice（\\% ↑）}", "\\textbf{Dice (\\% $\\uparrow$)}"),
    ("\\textbf{HD95（mm ↓）}", "\\textbf{HD95 (mm $\\downarrow$)}"),
    (
        "\\reviewersection{Table R5. External-test calibration and referral（各 test 队列自身分位定阈，送复核约 5\\%–15\\%）}",
        "\\reviewersection{Table R5. External-test calibration and referral (per-cohort percentile thresholds; referral $\\approx$ 5\\%--15\\%)}",
    ),
    ("队列 & n &", "Cohort & $n$ &"),
    (
        "\\reviewersection{Figure R1. External-test reliability diagrams（五队列拼接；各队列自身分位定阈）}",
        "\\reviewersection{Figure R1. External-test reliability diagrams (five cohorts; per-cohort thresholds)}",
    ),
    ("\\caption*{External-test reliability diagrams（TN3K、TN5K、ThyroidXL、ZJH-8K、DDTI）}",
     "\\caption*{External-test reliability diagrams (TN3K, TN5K, ThyroidXL, ZJH-8K, DDTI)}"),
    ("\\caption*{Risk–coverage曲线合图（五个外测队列；标点为各队列工作点）}",
     "\\caption*{Risk--coverage curves (five external cohorts; markers = operating points)}"),
    ("阶段 & 数据 / 阈值 \\\\", "Stage & Data / threshold \\\\"),
    ("模型开发训练 & TN3K、TN5K、ThyroidXL、PKTN 等公开队列合并（约 1.8 万图）→ DINO-UNet 等专家 \\\\",
     "Model development training & Merged public cohorts (TN3K, TN5K, ThyroidXL, PKTN; $\\sim$18k images) $\\rightarrow$ DINO-UNet experts \\\\"),
    ("验证集（850 张） & 专家选择、路由、拒答阈值（外测不调参） \\\\",
     "Validation set (850 images) & Expert selection, routing, abstention thresholds (no tuning on external tests) \\\\"),
    ("AutoGluon 放射组学 & dataset\\_3、GT mask、17,774 训练样本 \\\\",
     "AutoGluon radiomics & dataset\\_3, GT masks, 17,774 training samples \\\\"),
    ("通用外测 & TN3K、TN5K、ThyroidXL、DDTI、ZJH-8K、RJH-7K、NHC 等 \\\\",
     "Generic external test & TN3K, TN5K, ThyroidXL, DDTI, ZJH-8K, RJH-7K, NHC, etc. \\\\"),
    ("LNM / FTC-PTC & ZJH 恶性子集 + LymphUs；外测 LymphUs C2 / FangDai \\\\",
     "LNM / FTC--PTC & ZJH malignant subset + LymphUs; external LymphUs C2 / FangDai \\\\"),
    ("ZJH-8K 角色 & 良恶性/分割外测；专家未在 ZJH 训练；恶性子集仅用于 LNM/FTC 开发 \\\\",
     "ZJH-8K role & Benign--malignant / segmentation external test; experts not trained on ZJH; malignant subset for LNM/FTC development only \\\\"),
    (
        "\\reviewersection{Table R7. Five-cohort malignancy summary means（两行：AUROC / AUPRC）}",
        "\\reviewersection{Table R7. Five-cohort malignancy summary means (AUROC / AUPRC)}",
    ),
    ("指标 & Unweighted macro mean", "Metric & Unweighted macro mean"),
    (
        "\\textbf{表 S5a --- Independent external test}（五折 OOF 定稿开发流程后，于\\textbf{全开发集}训练模型后的单次外测；数值 ± 半宽与投稿 Supplementary Table S5 中对应专家单元格一致）",
        "\\textbf{Table S5a --- Independent external test.} After finalising the five-fold OOF development protocol, models were trained on the \\textbf{full development set} and evaluated once externally; values are $\\pm$ half-width of 95\\% CI and match the corresponding expert cells in the submitted Supplementary Table S5.",
    ),
    (
        "表注：\\textbf{LNM}：LymphUs \\textbf{Center 2}（\\textbf{n=158}）。\\textbf{FTC/PTC}：FangDai 等公开外测集（\\textbf{n≈200}）。仅报告 \\textbf{ThyroidXAgent}、\\textbf{LLNM-Net}（LNM）、\\textbf{Tiger-Model}（FTC/PTC）；与正文主结果一致。",
        "Note: \\textbf{LNM}: LymphUs \\textbf{Center 2} (\\textbf{$n$=158}). \\textbf{FTC/PTC}: FangDai public external set (\\textbf{$n\\approx$200}). Only \\textbf{ThyroidXAgent}, \\textbf{LLNM-Net} (LNM), and \\textbf{Tiger-Model} (FTC/PTC) are shown, consistent with main-text results.",
    ),
    (
        "\\textbf{表 S5b --- Development set: patient/cluster-stratified 5-fold OOF}（cluster bootstrap 95\\% CI，1000 次，seed=42；簇内图像概率算术平均后计算指标）",
        "\\textbf{Table S5b --- Development set: patient/cluster-stratified five-fold OOF} (cluster-bootstrap 95\\% CI, 1000 resamples, seed=42; metrics after arithmetic mean of image probabilities within cluster).",
    ),
    (
        "表注：替代原 \\textbf{20 例}固定验证。\\textbf{LNM}：合并开发 \\textbf{4753} 图、\\textbf{882} 簇。\\textbf{FTC/PTC}：ZJH 恶性开发 \\textbf{4756} 图、\\textbf{722} 簇。\\textbf{ThyroidXAgent}、\\textbf{LLNM-Net}、\\textbf{Tiger-Model} 同折 OOF（种子 42）。\\textbf{RepViT} 至 \\textbf{Gemini-2.5-Pro} 与投稿 Table S5 一致（未按五折 OOF 重跑）。--- 表示该任务未评估。",
        "Note: Replaces the original \\textbf{20-case} hold-out. \\textbf{LNM}: \\textbf{4753} development images, \\textbf{882} clusters. \\textbf{FTC/PTC}: ZJH malignant development \\textbf{4756} images, \\textbf{722} clusters. \\textbf{ThyroidXAgent}, \\textbf{LLNM-Net}, and \\textbf{Tiger-Model} share the same OOF folds (seed 42). \\textbf{RepViT} through \\textbf{Gemini-2.5-Pro} match the submitted Table S5 (not re-run with five-fold OOF). ``---'' = task not evaluated.",
    ),
    (
        "\\reviewersection{Table R9. Malignancy: image-level vs patient-level（ThyroidXAgent，ZJH-8K 与 ThyroidXL）}",
        "\\reviewersection{Table R9. Malignancy: image-level vs patient-level (ThyroidXAgent, ZJH-8K and ThyroidXL)}",
    ),
    (
        "Cluster-bootstrap 95\\% CI（1000 次，seed=42）。患者级：簇内恶性概率算术平均，标签组内 max。",
        "Cluster-bootstrap 95\\% CI (1000 resamples, seed=42). Patient-level: arithmetic mean of malignancy probability within cluster; label = within-cluster max.",
    ),
    ("队列 & 报告层级 &", "Cohort & Level &"),
    ("ZJH-8K & 图像 & 7958 图 / 1146 簇 &", "ZJH-8K & Image & 7958 images / 1146 clusters &"),
    ("ZJH-8K & 患者 &", "ZJH-8K & Patient &"),
    ("ThyroidXL & 图像 & 2090 图 / 739 簇 &", "ThyroidXL & Image & 2090 images / 739 clusters &"),
    ("ThyroidXL & 患者 &", "ThyroidXL & Patient &"),
    (
        "\\reviewersection{Table R10. Segmentation: within-patient mean Dice（ThyroidXAgent，补充）}",
        "\\reviewersection{Table R10. Segmentation: within-patient mean Dice (ThyroidXAgent, supplement)}",
    ),
    ("队列 & n 患者 & Dice（患者级） &", "Cohort & $n$ patients & Dice (patient-level) &"),
    (
        "\\reviewersection{Table R11. Routing stability（TN3K 稳定性子集，5 次重复）}",
        "\\reviewersection{Table R11. Routing stability (TN3K stability subset, five repeats)}",
    ),
    ("病例 & Tier & 5 Choice agreement (5 runs) \\\\", "Case & Tier & Choice agreement (5 runs) \\\\"),
    (
        "Reasoning must cite specific confidence values. (Deployed labels use Chinese strings 良性/恶性.)",
        "Reasoning must cite specific confidence values. (Deployed labels use Chinese strings \\textit{良性}/\\textit{恶性}.)",
    ),
    (
        '\\texttt{\\{"selected\\_class": "良性|恶性", "confidence": 0.0–1.0, "reasoning": "..."\\}}',
        '\\texttt{\\{"selected\\_class": "benign|malignant (Chinese labels in production)", "confidence": 0.0--1.0, "reasoning": "..."\\}}',
    ),
    ("\\textbf{表注}", "\\textbf{Table notes}"),
    (
        "1. \\textbf{dataset\\_3（分类开发）}：TN3K + ThyroidXL + TN5K 堆叠训练划分（与 OpenThyroid 公开 multitask 分类开发集一致）。",
        "1. \\textbf{dataset\\_3 (classification development):} TN3K + ThyroidXL + TN5K stacked training split (OpenThyroid public multitask classification development set).",
    ),
    (
        "2. \\textbf{dataset\\_4（分割开发）}：TN3K + ThyroidXL + PKTN + TN5K 堆叠训练划分（与 OpenThyroid 公开分割开发集一致）。",
        "2. \\textbf{dataset\\_4 (segmentation development):} TN3K + ThyroidXL + PKTN + TN5K stacked training split (OpenThyroid public segmentation development set).",
    ),
    (
        "3. \\textbf{监督基线默认协议}：在对应堆叠开发集上\\textbf{全量微调}（自公开上游预训练权重出发），取验证集最佳权重用于 Table S3/S4 全部外测；\\textbf{非}甲状腺零样本或仅用原始权重评估。",
        "3. \\textbf{Supervised baseline protocol:} full fine-tuning on the stacked development set from public upstream weights; best validation checkpoint for all Table S3/S4 external tests---\\textbf{not} thyroid zero-shot or frozen upstream weights only.",
    ),
    (
        "4. \\textbf{分割基线外测}：图像 + \\textbf{GT box/mask} 提示（\\texttt{gt\\_mask} 协议），与 Table S3 一致。",
        "4. \\textbf{Segmentation external test:} image + \\textbf{GT box/mask} prompt (\\texttt{gt\\_mask} protocol), consistent with Table S3.",
    ),
    ("5. \\textbf{分类基线外测}：仅超声图像输入。", "5. \\textbf{Classification external test:} ultrasound image only."),
    (
        "6. \\textbf{ThyroidXAgent}：满堆叠 S3/S4 结果与上表使用相同堆叠开发数据；\\textbf{Table S6} 逐级叠加消融另报。",
        "6. \\textbf{ThyroidXAgent:} full-stack S3/S4 results use the same stacked development data; progressive ablations in \\textbf{Table S6} separately.",
    ),
    (
        "7. \\textbf{视觉–语言模型}：未在 dataset\\_3 端到端训练；厂商/公开权重；API 或冻结推理 + 固定 prompt。",
        "7. \\textbf{Vision--language models:} not end-to-end trained on dataset\\_3; vendor/public weights; API or frozen inference with fixed prompts.",
    ),
    (
        "8. 监督行与 \\textbf{Table S3/S4} 出表模型一致；ZJH-8K、DDTI 等外测队列\\textbf{不参与}开发微调。",
        "8. Supervised rows match models in \\textbf{Tables S3/S4}; external cohorts (ZJH-8K, DDTI, etc.) \\textbf{do not} enter development fine-tuning.",
    ),
    ("模型 & 任务 & 甲状腺开发集 & 上游预训练 & 外测推理输入 \\\\", "Model & Task & Thyroid development set & Upstream pretraining & External inference input \\\\"),
    ("BiomedCLIP & 分类 & dataset\\_3 & OpenCLIP BiomedCLIP；在 dataset\\_3\\_cls 上微调分类头 & 仅图像 \\\\",
     "BiomedCLIP & Classification & dataset\\_3 & OpenCLIP BiomedCLIP; classification head fine-tuned on dataset\\_3\\_cls & Image only \\\\"),
    ("LSNet & 分类 & dataset\\_3 & ImageNet 预训练 LSNet & 仅图像 \\\\",
     "LSNet & Classification & dataset\\_3 & ImageNet-pretrained LSNet & Image only \\\\"),
    ("MedSAM2 & 分割 & dataset\\_4 & SAM 2.1 Hiera & 图像 + GT box/mask（\\texttt{gt\\_mask}） \\\\",
     "MedSAM2 & Segmentation & dataset\\_4 & SAM 2.1 Hiera & Image + GT box/mask (\\texttt{gt\\_mask}) \\\\"),
    ("MedSegX & 分割 & dataset\\_4 & SAM ViT-B + MedSegX 甲状腺适配器 & 图像 + GT box/mask（\\texttt{gt\\_mask}） \\\\",
     "MedSegX & Segmentation & dataset\\_4 & SAM ViT-B + MedSegX thyroid adapter & Image + GT box/mask (\\texttt{gt\\_mask}) \\\\"),
    ("MedSigLIP & 分类 & dataset\\_3 & Google MedSigLIP；在 dataset\\_3\\_cls 上部分微调 & 仅图像 \\\\",
     "MedSigLIP & Classification & dataset\\_3 & Google MedSigLIP; partial fine-tune on dataset\\_3\\_cls & Image only \\\\"),
    ("RepViT & 分类 & dataset\\_3 & ImageNet 预训练 RepViT & 仅图像 \\\\",
     "RepViT & Classification & dataset\\_3 & ImageNet-pretrained RepViT & Image only \\\\"),
    ("ResNet-50 & 分类 & dataset\\_3 & ImageNet ResNet-50；dataset\\_3 微调 & 仅图像 \\\\",
     "ResNet-50 & Classification & dataset\\_3 & ImageNet ResNet-50; fine-tuned on dataset\\_3 & Image only \\\\"),
    ("TransUNet & 分割 & dataset\\_4 & ImageNet-21k ViT-B/16（TransUNet 默认） & 图像 + GT box/mask（\\texttt{gt\\_mask}） \\\\",
     "TransUNet & Segmentation & dataset\\_4 & ImageNet-21k ViT-B/16 (TransUNet default) & Image + GT box/mask (\\texttt{gt\\_mask}) \\\\"),
    ("UltraFedFM & 分类 & dataset\\_3 & ViT 骨干 + dataset\\_3\\_cls 微调 & 仅图像 \\\\",
     "UltraFedFM & Classification & dataset\\_3 & ViT backbone + dataset\\_3\\_cls fine-tune & Image only \\\\"),
    ("UltraFedFM & 分割 & dataset\\_4 & MAE / 联邦 FM + dataset\\_4 微调 & 图像 + GT box/mask（\\texttt{gt\\_mask}） \\\\",
     "UltraFedFM & Segmentation & dataset\\_4 & MAE / federated FM + dataset\\_4 fine-tune & Image + GT box/mask (\\texttt{gt\\_mask}) \\\\"),
    ("ThyroidXAgent（分割路由） & 分割 & dataset\\_4 & DINOv3-UNet（ImageNet 级骨干） & 图像 → LLM 路由后的专家 mask \\\\",
     "ThyroidXAgent (seg. router) & Segmentation & dataset\\_4 & DINOv3-UNet (ImageNet-scale backbone) & Image $\\rightarrow$ LLM-routed expert mask \\\\"),
    ("ThyroidXAgent（分类路由） & 分类 & dataset\\_3 & DINOv3 多任务骨干（dataset\\_3 微调） & 路由 mask + 图像（pipeline） \\\\",
     "ThyroidXAgent (cls. router) & Classification & dataset\\_3 & DINOv3 multitask backbone (dataset\\_3 fine-tune) & Routed mask + image (pipeline) \\\\"),
    ("GPT-5 / Gemini / MedGemma / Qwen3-VL（若见于 S4） & 分类 & ---（未微调） & 厂商/公开 VLM 权重 & 图像 ± 固定文本 prompt（零样本或 API） \\\\",
     "GPT-5 / Gemini / MedGemma / Qwen3-VL (if in S4) & Classification & --- (not fine-tuned) & Vendor/public VLM weights & Image $\\pm$ fixed text prompt (zero-shot or API) \\\\"),
    ("队列 & n 匹配 & <5.0 mm (N) & 失败 (M) & 小结节子集 mean Dice & GT 等价径 <50 px \\\\",
     "Cohort & $n$ matched & <5.0 mm ($N$) & Failures ($M$) & Mean Dice (small-nodule subset) & GT equiv.\\ diameter <50 px \\\\"),
    (
        "\\item The image-arm data-flow figure is \\textbf{to be supplied}; the tabular summary is in \\textbf{Table R6} summarizes splits in the interim.",
        "\\item The image-arm data-flow figure is \\textbf{to be supplied}; the interim tabular summary is in \\textbf{Table R6}.",
    ),
    (
        "(\\textbf{Table R7} at the end of this letter), in addition to image-level Table S4.",
        "(\\textbf{Tables R9} and \\textbf{R10} at the end of this letter), in addition to image-level Table S4.",
    ),
]


def fix_reviewer_comments(text: str) -> str:
    pat = re.compile(
        r"\\begin\{reviewercomment\}\s*\*\*\s*\\par\s*\\end\{reviewercomment\}\s*"
        r"(.*?)\s*\\par\s*\\begin\{authorresponse\}",
        re.DOTALL,
    )

    def repl(m):
        comment = m.group(1).strip()
        return (
            "\\begin{reviewercomment}\n"
            + comment
            + "\n\\end{reviewercomment}\n"
            "\\begin{authorresponse}"
        )

    return pat.sub(repl, text)


def fix_r221(text: str) -> str:
    old = (
        "\\reviewersection{Reviewer 2 --- Comment 21 (R2.21)}\n"
        "\\textbf{Reviewer comment (editorial text; no sub-bullets):}\n"
        "\\par\n"
        "The AutoGluon-based radiomics branch is insufficiently described.\n"
        "\\par\n"
        "\\begin{authorresponse}"
    )
    new = (
        "\\reviewersection{Reviewer 2 --- Comment 21 (R2.21)}\n"
        "\\begin{reviewercomment}\n"
        "The AutoGluon-based radiomics branch is insufficiently described.\n"
        "(Editorial comment; no sub-bullets.)\n"
        "\\end{reviewercomment}\n"
        "\\begin{authorresponse}"
    )
    return text.replace(old, new)


def balance_authorresponse(text: str) -> str:
    # Remove trailing spurious \end{authorresponse}
    lines = text.splitlines()
    while lines and lines[-1].strip() == r"\end{authorresponse}":
        lines.pop()
    text = "\n".join(lines) + "\n"

    # Close authorresponse before each section break if still open
    parts = re.split(r"(\\bigskip\\hrule\\bigskip)", text)
    out = []
    for i, part in enumerate(parts):
        opens = part.count(r"\begin{authorresponse}")
        closes = part.count(r"\end{authorresponse}")
        if opens > closes:
            part = part.rstrip() + "\n\\end{authorresponse}\n"
        out.append(part)
    text = "".join(out)

    # Appendix should not be inside authorresponse: strip any open from first Supporting Figures
    marker = r"\begin{center}{\Large\bfseries Supporting Figures and Tables for This Response}"
    idx = text.find(marker)
    if idx != -1:
        before = text[:idx]
        after = text[idx:]
        # close any dangling opens in `before`
        opens = before.count(r"\begin{authorresponse}")
        closes = before.count(r"\end{authorresponse}")
        if opens > closes:
            before = before.rstrip() + "\n" + (r"\end{authorresponse}\n" * (opens - closes))
        # remove any authorresponse env tokens from appendix
        after = after.replace(r"\begin{authorresponse}", "")
        after = after.replace(r"\end{authorresponse}", "")
        text = before + after

    return text


def main():
    text = PATH.read_text(encoding="utf-8")
    text = fix_reviewer_comments(text)
    text = fix_r221(text)
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    text = balance_authorresponse(text)
    PATH.write_text(text, encoding="utf-8")
    # report remaining CJK
    import re as _re

    cjk = _re.findall(r"[\u4e00-\u9fff]+", text)
    print(f"Wrote {PATH}; remaining CJK segments: {len(cjk)}")
    if cjk:
        print("Sample:", ", ".join(sorted(set(cjk))[:20]))


if __name__ == "__main__":
    main()
