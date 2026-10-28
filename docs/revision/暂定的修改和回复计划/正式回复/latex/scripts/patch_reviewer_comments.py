#!/usr/bin/env python3
"""Refresh \\begin{reviewercomment} blocks with full PDF text and seg/cls bolding."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "generated"

SKIP_RESPONSE = {
    "R1.5",
    "R1.6",
    "R2.13",
    "R2.15",
    "R2.16",
    "R2.17",
    "R2.18",
    "R2.19",
    "R2.22",
    "R2.23",
    "R3.4",
    "R3.5",
    "R3M1",
}

# Plain text from Nature Communications Reviews.pdf (2026-10-08 decision letter).
COMMENTS_EN: dict[str, str] = {
    "R1.1": (
        "Independence of image-level evaluations. Segmentation and classification results are largely "
        "reported at the image level. The authors should clarify patient-level and examination-level splitting, "
        "deduplication across datasets, and whether multiple frames or views from the same patient could occur "
        "across splits. Patient-level reanalysis and cluster-aware confidence intervals would strengthen "
        "confidence in the reported performance."
    ),
    "R1.2": (
        "Causal contribution of the agentic router. The system combines expert ensembles, radiomics, multiple "
        "tools, and LLM routing. The current analyses do not isolate the contribution of the router itself. "
        "I recommend adding a systematic ablation study comparing a single model, average ensemble, rule-based "
        "routing, confidence-based routing, LLM-based routing, and an oracle upper bound."
    ),
    "R1.3": (
        "Heterogeneity in external performance. Although aggregate performance on the private multicentre cohort "
        "is encouraging, there is substantial centre-level variation. For example, nodule segmentation performance "
        "is much lower at some centres. The authors should investigate associations with scanner type, image quality, "
        "case mix, and annotation protocol, and define calibration, abstention, or mandatory human-review policies "
        "for low-confidence cases."
    ),
    "R1.4": (
        "Data boundaries across tasks. ZJH-8K is described as an external test set for segmentation and "
        "benign-malignant classification, while its malignant images are used for development of LNM and FTC/PTC "
        "tasks. This may be acceptable because the tasks differ, but the manuscript should provide a complete "
        "data-flow diagram showing which data were used for training, validation, threshold selection, and testing "
        "for each component."
    ),
    "R1.5": (
        "Validation of report quality and template dependence. ThyClinScore is well motivated, but its validation "
        "primarily relies on correlation with an LLM judge. A stronger validation would include blinded assessment "
        "by multiple independent clinicians, inter-rater agreement, and sensitivity analyses for lesion-matching "
        "thresholds and score weights. The authors should also audit patient overlap, near-duplicate report text, and "
        "centre-specific template effects between template libraries and test sets."
    ),
    "R1.6": (
        "Reader study and clinical safety. The two-physician, 145-case crossover study supports initial workflow "
        "feasibility, but does not establish patient benefit. Results should be reported separately by physician, with "
        "case-order randomization, learning-effect analysis, error categories, and confidence intervals. More "
        "importantly, the system should define when it abstains or escalates to mandatory human review, and quantify "
        "the effect of these safety rules on missed diagnoses, false positives, and workload."
    ),
    "R1G": (
        "Overall, this is a thoughtful and technically ambitious study. Its strongest contribution is the framing of "
        "clinical AI as an editable and auditable evidence workflow rather than a black-box predictor. Addressing the "
        "issues above, particularly patient-level independence, routing ablations, centre-level failure analysis, "
        "clinical validation of ThyClinScore, and prospective human-AI safety evaluation, would substantially strengthen "
        "the manuscript. The work has notable strengths; however, the current evidence supports a promising retrospective "
        "workflow rather than established clinical benefit or broad deployability. I therefore recommend major revision "
        "at minimum."
    ),
    "R2.1": (
        "Several key values are inconsistent across the abstract, main text, figures, and supplementary materials."
    ),
    "R2.2": (
        "Many analyses are reported at the image level, although multiple images may come from the same patient, "
        "examination, or nodule. For example, ZJH-8K includes 7,958 images from 1,149 cases. Treating correlated "
        "images as independent observations may produce overly narrow confidence intervals. The authors should "
        "recalculate confidence intervals using patient- or examination-level bootstrap resampling and report "
        "patient-level performance for clinically relevant classification tasks."
    ),
    "R2.3": (
        'Please clarify why 28,458 observations are described as "non-overlapping test cases," as this number '
        "appears to combine 19,737 test images with 8,721 NHC-MISD-TUS cases."
    ),
    "R2.4": (
        "ZJH-8K and TN3K were both collected at Zhujiang Hospital, Southern Medical University. Unless they are "
        "demonstrably independent in patient population, collection period, cohort composition, and clinical workflow, "
        "ZJH-8K should not be described as an external-centre cohort."
    ),
    "R2.5": (
        "The Methods should specify the reference standards for nodule segmentation and benign-malignant "
        "classification, annotation procedures, annotator qualifications and adjudication of disagreements, "
        "patient-level deduplication, and handling of missing data."
    ),
    "R2.6": (
        "The manuscript reports validation on 8,721 cases from 35 centres, but the NHC-MISD-TUS cohort is "
        "insufficiently described. The authors should clarify whether these represent 35 independent hospitals and "
        "report the numbers of patients, nodules, and images per centre, together with centre-level macro-averaged "
        "performance and between-centre heterogeneity."
    ),
    "R2.7": (
        'The authors should clarify whether the reported "mean" performance represents an unweighted macro-average '
        "across cohorts, a sample-size-weighted average, or another calculation."
    ),
    "R2.8": (
        "The key innovation is the agentic evidence workflow, but the observed gains may largely reflect the DINOv3 "
        "expert pool, multicohort training, radiomics classifiers, or template-based reporting rather than agentic "
        "routing itself. As the static-pipeline comparison is limited mainly to report generation, the independent "
        "value of LLM-based routing for segmentation and classification remains unclear."
    ),
    "R2.9": (
        'The manuscript states that the LLM router selects the best expert output through "reasoning," but does not '
        "report the prompt design, LLM version, decoding parameters, reproducibility, or decision stability when "
        "candidate outputs have similar quality. The router therefore remains a black-box selector. The authors should "
        "provide structured routing records for at least 10 representative cases, including input quality metrics, "
        "candidate outputs, final selections, uncertainty indicators, brief decision rationales, and consistency across "
        "repeated runs."
    ),
    "R2.10": (
        "For FTC/PTC classification, the training cohort comprised classic PTC and follicular-variant PTC, whereas "
        "the external test set comprised FTC and PTC. Because follicular-variant PTC is not equivalent to FTC, the "
        "target definition differs between training and testing. Unless this is justified as a clinically valid "
        "domain-transfer task, the reported performance may not be valid."
    ),
    "R2.11": (
        "The LNM task uses only 4,753 malignant images, and Table S5 indicates only 20 cases for validation---sample "
        "sizes far too small for training reliable deep learning classifiers. Please clarify: (a) whether transfer "
        "learning or multi-task learning was employed; (b) whether data augmentation was applied; (c) how overfitting "
        "is avoided given the wide confidence intervals in Table S5 that reflect inadequate sample size."
    ),
    "R2.12": (
        "For lymph-node metastasis prediction, the manuscript inconsistently refers to overall LNM, lateral LNM, and "
        "CN0/CN1 labels. The authors should clarify whether CN denotes central-compartment nodal status, whether the "
        "target is central, lateral, or any cervical LNM, whether the inputs include primary thyroid lesions, lymph "
        "nodes, or both, and how image-level predictions are aggregated at the patient level."
    ),
    "R2.13": (
        "The report-generation reader study included only two physicians, with each case assessed under the two "
        "conditions by different readers. Although this may reduce recall bias, it may also confound reader effects "
        "with the assistance condition."
    ),
    "R2.14": (
        "It is unclear whether all specialist baselines were retrained on the same development data, evaluated using "
        "their original weights, or tested zero-shot. Comparisons may be unfair if ThyroidXAgent benefits from "
        "multicohort training and task-specific models while the baselines are used off the shelf."
    ),
    "R2.15": (
        "The manuscript provides an ethics approval number but does not state whether informed consent was obtained or "
        "waived. For all institutional datasets, the authors should report the study design and period, consent or "
        "waiver arrangements, de-identification procedures, and data-governance measures. Authorization by a co-author "
        "to use NHC-MISD-TUS does not replace documentation of ethical approval and regulatory compliance."
    ),
    "R2.16": (
        "The ReAct-style planner-executor workflow lacks systematic failure-mode evaluation. The authors should report "
        "the frequency of invalid or unnecessary tool calls, hallucinated tasks, repeated calls, execution failures, "
        "retries, and rollbacks, and provide representative traces for successful cases and major failure modes, "
        "particularly cases with no nodules, multiple nodules, or conflicting intermediate evidence."
    ),
    "R2.17": (
        "Agent workflow lacks concurrency control and conflict resolution mechanisms: When lymph-node screening and "
        "nodule analysis execute concurrently, how is duplication avoided if both detect the same hypoechoic structure "
        "in the lateral neck region?"
    ),
    "R2.18": (
        "The ThyClinScore weights lambda and eta directly affect report-quality assessment, but their selection, "
        "optimization dataset, and sensitivity analysis are not reported, raising concerns about overfitting. Although "
        "Figure 4c shows correlation with an LLM judge, validation against radiologist ratings and inter-rater "
        "reliability analysis are lacking."
    ),
    "R2.19": (
        'The term "training-free" should be qualified. Although BM25 requires no parameter training, the workflow still '
        "depends on corpus selection, report decomposition, template construction, slot definitions, and clause-assembly "
        "rules. The authors should describe the extent of manual curation, template deduplication, slot-filling rules, and "
        "adaptation to centre-specific reporting styles. Clinician assessment of readability, factual consistency, and "
        "clinical usability is also needed beyond lexical-overlap metrics such as BLEU and ROUGE."
    ),
    "R2.20": (
        "Thresholds for connected-component analysis in post-processing are unspecified. The manuscript mentions "
        "removing isolated noise regions via connected-component analysis but does not specify: (a) the minimum "
        "connected-component area threshold; (b) whether small nodules (< 5 mm) may be erroneously removed; (c) the "
        "algorithm for separating multiple nodules. These details directly affect segmentation quality but are entirely "
        "absent from the Methods section."
    ),
    "R2.21": ("The AutoGluon-based radiomics branch is insufficiently described."),
    "R2.22": (
        'Please check the manuscript for grammatical errors, such as "ThyroidXAgent improved produced."'
    ),
    "R2.23": (
        'Please specify whether TI-RADS refers to ACR TI-RADS, C-TIRADS, or another system, as categories such as '
        '"TI-RADS 4b" are system-specific.'
    ),
    "R3.1": (
        "The proposed system integrates a heterogeneous ensemble of expert models, radiomic features, metadata, and an "
        "LLM-based router. It is therefore unclear to what extent the performance obtained comes from the agent itself "
        "rather than from model ensembling or the use of stronger component models. Including controlled baseline "
        "comparisons with majority voting, probability averaging, rule-based routing, and a non-LLM learned router "
        "based on the same expert pool would better clarify the unique advantage provided by the agent."
    ),
    "R3.2": (
        "The LLM router leverages metadata such as device and data source in addition to prediction quality signals. "
        "This may allow the system to learn center-specific expert preferences rather than case-level routing. Please "
        "provide ablation analysis to evaluate the effect from data-source, scanner metadata and report expert-selection "
        "patterns across centers."
    ),
    "R3.3": (
        'The definition of "28,458 non-overlapping test cases" is unclear. Please clearly describe the data hierarchy '
        "and confirm that all train/validation/test splits are patient disjoint. Besides, a simple flowchart showing the "
        "relationship of patient, examination, image/video, lesion and task would greatly improve the clarity."
    ),
    "R3.4": (
        "The reporting study includes only two physicians and 145 videos. The results are encouraging, but the "
        "conclusions regarding improved physician performance should be moderated. Please report confidence intervals, "
        "appropriate paired or mixed-effects statistics, and clearly distinguish annotation consistency from validated "
        "diagnostic accuracy."
    ),
    "R3.5": (
        "ThyClinScore is mainly validated by correlation with an LLM judge. This is not sufficient as a clinical gold "
        "standard. To strengthen the validity of the metric, please validate the metric against blinded ratings from "
        "multiple radiologists and provide sensitivity analysis for the main weights and thresholds used. The manuscript "
        "should also acknowledge that ThyroidXAgent does not outperform all baselines across every semantic submetric."
    ),
    "R3M1": (
        "ThyroidXAgent receives structured outputs from multiple specialized tools, whereas several multimodal LLM "
        "baselines appear to work more directly from images. The manuscript should clarify this difference and avoid "
        "interpreting these comparisons as a pure test of language-generation ability."
    ),
}

COMMENTS_ZH: dict[str, str] = {
    "R1.1": (
        "分割与分类结果大多以图像层面报告。作者应澄清患者层面与检查层面的划分、跨数据集的去重，"
        "以及同一患者的多个帧或视图是否会跨划分出现。患者层面的再分析和聚类感知的置信区间会增强对报告性能的信心。"
    ),
    "R1.2": (
        "该系统结合了专家集成、放射组学、多个工具与 LLM 路由。当前分析没有分离出路由器本身的贡献。"
        "我建议增加一个系统的消融研究，比较单模型、平均集成、规则路由、置信度路由、基于 LLM 的路由以及 oracle 上界。"
    ),
    "R1.3": (
        "尽管在私有多中心队列上的总体性能令人鼓舞，但中心层面差异很大。例如，某些中心的结节分割性能低得多。"
        "作者应研究其与扫描仪类型、图像质量、病例构成与标注协议的关联，并为低置信病例定义校准、拒答或强制人工复核策略。"
    ),
    "R1.4": (
        "ZJH-8K 被描述为分割与良恶性分类的外部测试集，而它的恶性图像又被用于 LNM 与 FTC/PTC 任务的开发。"
        "由于任务不同，这也许可以接受，但稿件应提供一张完整的数据流图，说明每个组件分别用了哪些数据做训练、验证、阈值选择与测试。"
    ),
    "R1.5": (
        "ThyClinScore 的动机很好，但其验证主要依赖于与 LLM 评委的相关性。更强的验证应包括多位独立临床医生的盲法评估、"
        "评分者间一致性，以及针对病灶匹配阈值与评分权重的敏感性分析。作者还应审计模板库与测试集之间的患者重叠、"
        "近重复报告文本与中心特异的模板效应。"
    ),
    "R1.6": (
        "两位医生、145 例的交叉研究支持初步的工作流可行性，但未确立患者获益。结果应按医生分别报告，并包含病例顺序随机化、"
        "学习效应分析、错误类别与置信区间。更重要的是，系统应定义何时拒答或升级为强制人工复核，"
        "并量化这些安全规则对漏诊、假阳性与工作量的影响。"
    ),
    "R1G": (
        "总体而言，这是一项深思熟虑且技术上雄心勃勃的研究；其最强贡献在于将临床 AI 表述为可编辑、可审计的证据工作流，"
        "而非黑箱预测器。若能回应上述问题——尤其是患者层面独立性、路由消融、中心层面失败分析、"
        "ThyClinScore 的临床验证以及前瞻性人机安全评估——将显著增强稿件。"
        "该工作有明显优点；然而，当前证据支持的是一条有前景的回顾性工作流，而非已确立的临床获益或广泛可部署性。"
        "因此，我建议至少给「大修」。"
    ),
    "R2.1": "若干关键数值在摘要、正文、图与补充材料之间不一致。",
    "R2.2": (
        "许多分析以图像层面报告，尽管同一患者、检查或结节可能有多个图像。例如 ZJH-8K 包含来自 1,149 例的 7,958 张图像。"
        "把相关图像当作独立观测可能产生过窄的置信区间。作者应使用患者层面或检查层面的 bootstrap 重采样重算置信区间，"
        "并对具有临床意义的分类任务报告患者层面性能。"
    ),
    "R2.3": (
        "请澄清为什么把 28,458 个观测描述为「non-overlapping test cases」，"
        "因为这个数字似乎把 19,737 张测试图像与 8,721 个 NHC-MISD-TUS 病例合并在一起。"
    ),
    "R2.4": (
        "ZJH-8K 与 TN3K 都采集自南方医科大学珠江医院。除非能证明它们在患者人群、采集时段、队列构成与临床流程上确实独立，"
        "否则 ZJH-8K 不应被描述为外部中心队列。"
    ),
    "R2.5": (
        "方法部分应说明结节分割与良恶性分类的参考标准、标注流程、标注者资质与分歧裁决、患者层面去重以及缺失数据的处理。"
    ),
    "R2.6": (
        "稿件报告在来自 35 个中心的 8,721 个病例上做了验证，但 NHC-MISD-TUS 队列的描述不足。"
        "作者应澄清这是否代表 35 家独立医院，并报告各中心的患者数、结节数与图像数，"
        "以及中心级宏平均性能与中心间异质性。"
    ),
    "R2.7": "作者应澄清所报告的「均值」是跨队列的无权重宏平均、按样本量加权的平均，还是其他计算方式。",
    "R2.8": (
        "关键创新是智能体证据工作流，但观察到的增益可能在很大程度上来自 DINOv3 专家池、多队列训练、"
        "放射组学分类器或基于模板的报告，而不是智能体路由本身。由于静态流程对比主要限于报告生成，"
        "LLM 路由对分割与分类的独立价值仍不清楚。"
    ),
    "R2.9": (
        "稿件称 LLM 路由器通过「推理」选择最佳专家输出，但未报告 prompt 设计、LLM 版本、解码参数、可复现性，"
        "以及当候选输出质量相近时的决策稳定性。路由器因此仍是黑箱选择器。"
        "作者应提供至少 10 个代表性病例的结构化路由记录，包括输入质量指标、候选输出、最终选择、"
        "不确定度指标、简要决策理由以及重复运行的一致性。"
    ),
    "R2.10": (
        "对 FTC/PTC 分类，训练队列由经典型 PTC 与滤泡变异型 PTC 组成，而外部测试集由 FTC 与 PTC 组成。"
        "由于滤泡变异型 PTC 并不等同于 FTC，训练与测试的目标定义不同。"
        "除非将其论证为临床有效的域迁移任务，否则所报告的性能可能无效。"
    ),
    "R2.11": (
        "LNM 任务只使用了 4,753 张恶性图像，而 Table S5 显示验证只有 20 例——样本量远不足以训练可靠的深度学习分类器。"
        "请澄清：(a) 是否使用了迁移学习或多任务学习；(b) 是否做了数据增强；(c) 在 Table S5 置信区间很宽、"
        "反映样本量不足的情况下如何避免过拟合。"
    ),
    "R2.12": (
        "对淋巴结转移预测，稿件不一致地使用总体 LNM、侧颈 LNM 与 CN0/CN1 标签。"
        "作者应澄清 CN 是否指中央区淋巴结状态、目标是中央/侧颈/任意颈部 LNM、"
        "输入是否包含原发甲状腺病灶与/或淋巴结图像，以及图像层面预测如何在患者层面聚合。"
    ),
    "R2.13": (
        "报告生成读者研究只纳入两位医生，且每个病例在两种条件下由不同读者评估。"
        "虽然这可能减少回忆偏倚，但也可能把读者效应与辅助条件混淆。"
    ),
    "R2.14": (
        "不清楚所有专家基线是在同一批开发数据上重训、使用原始权重评估，还是零样本测试。"
        "若 ThyroidXAgent 受益于多队列训练与任务特异模型而基线直接 off-the-shelf 使用，比较可能不公平。"
    ),
    "R2.15": (
        "稿件提供了伦理批号，但没有说明是否获得知情同意或予以豁免。"
        "对所有机构数据集，作者应报告研究设计与时段、同意或豁免安排、去标识化程序与数据治理措施。"
        "共同作者授权使用 NHC-MISD-TUS 不能替代伦理审批与合规监管的书面记录。"
    ),
    "R2.16": (
        "ReAct 式规划器–执行器工作流缺乏系统的失败模式评估。"
        "作者应报告无效或多余工具调用、幻觉任务、重复调用、执行失败、重试与回滚的频率，"
        "并提供成功病例与主要失败模式的代表性轨迹，尤其是无结节、多结节或中间证据冲突的病例。"
    ),
    "R2.17": (
        "智能体工作流缺乏并发控制与冲突解决机制：当淋巴结筛查与结节分析并发执行时，"
        "若两者在侧颈区域检测到同一低回声结构，如何避免重复？"
    ),
    "R2.18": (
        "ThyClinScore 的权重 $\\lambda$ 与 $\\eta$ 直接影响报告质量评估，但其选择、优化数据集与敏感性分析未报告，"
        "存在过拟合顾虑。尽管 Fig.~4c 显示与 LLM 评委相关，但缺乏针对放射科医生评分的验证与评分者间信度分析。"
    ),
    "R2.19": (
        "「training-free」这一说法应加限定。尽管 BM25 无需参数训练，工作流仍依赖语料选择、报告拆分、"
        "模板构建、槽位定义与条款组装规则。作者应描述人工整理程度、模板去重、槽位填充规则及适应各中心报告风格的程度。"
        "除 BLEU、ROUGE 等词法重叠指标外，还需要临床医生对可读性、事实一致性与临床可用性的评估。"
    ),
    "R2.20": (
        "后处理中连通域分析的阈值未说明。稿件提到通过连通域分析去除孤立噪声区域，但未说明："
        "(a) 最小连通域面积阈值；(b) 小于 5 mm 的结节是否可能被误删；(c) 分离多个结节的算法。"
        "这些细节直接影响分割质量，但在方法部分完全缺失。"
    ),
    "R2.21": "基于 AutoGluon 的放射组学分支描述不足。",
    "R2.22": "请检查稿件中的语法错误，例如「ThyroidXAgent improved produced」。",
    "R2.23": (
        "请说明 TI-RADS 指的是 ACR TI-RADS、C-TIRADS 还是其他体系，因为「TI-RADS 4b」等类别是体系特异的。"
    ),
    "R3.1": (
        "所提系统集成了异质专家模型集成、放射组学特征、元数据与基于 LLM 的路由器。"
        "因此不清楚所获性能在多大程度上来自智能体本身，而非模型集成或更强的组件模型。"
        "在同一专家池上加入与多数投票、概率平均、规则路由及非 LLM 学习型路由的对照比较，"
        "能更好地说明智能体带来的独特优势。"
    ),
    "R3.2": (
        "LLM 路由器除预测质量信号外还利用了设备与数据来源等元数据。"
        "这可能让系统学到中心特异的专家偏好，而不是病例级路由。"
        "请提供消融分析，评估数据来源、扫描仪元数据的影响，并报告各中心的专家选择模式。"
    ),
    "R3.3": (
        "「28,458 non-overlapping test cases」的定义不清楚。"
        "请清楚描述数据层级，并确认所有训练/验证/测试划分均为患者互斥。"
        "此外，一张展示患者、检查、图像/视频、病灶与任务之间关系的简单流程图会大有帮助。"
    ),
    "R3.4": (
        "报告研究只纳入两位医生与 145 段视频。结果令人鼓舞，但关于医生表现提升的结论应更审慎。"
        "请报告置信区间、恰当的配对或混合效应统计，并清楚区分标注一致性与经确认的诊断准确性。"
    ),
    "R3.5": (
        "ThyClinScore 主要通过与大模型评委的相关性来验证，这不足以作为临床金标准。"
        "请用多位放射科医生的盲法评分验证该指标，并为所使用的主要权重与阈值提供敏感性分析。"
        "稿件还应承认 ThyroidXAgent 并非在每个语义子指标上都优于所有基线。"
    ),
    "R3M1": (
        "ThyroidXAgent 接收多个专用工具的结构化输出，而若干多模态 LLM 基线似乎更直接地处理图像。"
        "稿件应澄清这一差异，避免把这些比较解读为对语言生成能力的纯粹测试。"
    ),
}

# Substrings to wrap in \\textbf{} (longest first per language).
BOLD_PHRASES_EN = [
    "LLM-based routing for segmentation and classification",
    "segmentation and benign-malignant classification",
    "benign-malignant classification",
    "nodule segmentation and benign-malignant classification",
    "nodule segmentation",
    "segmentation and classification",
    "patient-level performance for clinically relevant classification tasks",
    "patient-level reanalysis and cluster-aware confidence intervals",
    "patient-level and examination-level splitting",
    "patient-level deduplication",
    "patient- or examination-level bootstrap resampling",
    "patient-level independence",
    "routing ablations",
    "systematic ablation study",
    "LLM-based routing",
    "LLM routing",
    "router itself",
    "expert output",
    "segmentation quality",
    "connected-component analysis",
    "small nodules (< 5 mm)",
    "multiple nodules",
    "radiomics branch",
    "AutoGluon-based radiomics",
    "majority voting, probability averaging, rule-based routing, and a non-LLM learned router",
    "case-level routing",
    "train/validation/test splits are patient disjoint",
    "28,458 non-overlapping test cases",
    "19,737 test images",
    "external-centre cohort",
    "external test set for segmentation",
    "ZJH-8K",
    "classification tasks",
    "image level",
    "cluster-aware",
    "segmentation",
    "classification",
]

BOLD_PHRASES_ZH = [
    "LLM 路由对分割与分类的独立价值",
    "结节分割与良恶性分类",
    "分割与良恶性分类",
    "良恶性分类",
    "结节分割",
    "分割与分类",
    "患者层面与检查层面的划分",
    "患者层面的再分析",
    "聚类感知的置信区间",
    "患者层面去重",
    "患者层面或检查层面的 bootstrap",
    "患者层面独立性",
    "路由消融",
    "系统的消融研究",
    "LLM 路由",
    "路由器本身",
    "分割质量",
    "连通域分析",
    "小于 5 mm 的结节",
    "多个结节",
    "放射组学分支",
    "AutoGluon",
    "多数投票、概率平均、规则路由及非 LLM 学习型路由",
    "病例级路由",
    "患者互斥",
    "28,458",
    "19,737 张测试图像",
    "外部中心队列",
    "外部测试集",
    "ZJH-8K",
    "分类任务",
    "图像层面",
    "分割",
    "分类",
]

SECTIONS_EN = [
    ("\\responsetoreviewer{Response to Reviewer 1}", None),
    ("\\reviewersection{Reviewer 1, Comment 1 (R1.1)}", "R1.1"),
    ("\\reviewersection{Reviewer 1, Comment 2 (R1.2)}", "R1.2"),
    ("\\reviewersection{Reviewer 1, Comment 3 (R1.3)}", "R1.3"),
    ("\\reviewersection{Reviewer 1, Comment 4 (R1.4)}", "R1.4"),
    ("\\reviewersection{Reviewer 1, Comment 5 (R1.5)}", "R1.5"),
    ("\\reviewersection{Reviewer 1, Comment 6 (R1.6)}", "R1.6"),
    ("\\reviewersection{Reviewer 1, General remark (deployability)}", "R1G"),
    ("\\responsetoreviewer{Response to Reviewer 2}", None),
    ("\\reviewersection{Reviewer 2, Comment 1 (R2.1)}", "R2.1"),
    ("\\reviewersection{Reviewer 2, Comment 2 (R2.2)}", "R2.2"),
    ("\\reviewersection{Reviewer 2, Comment 3 (R2.3)}", "R2.3"),
    ("\\reviewersection{Reviewer 2, Comment 4 (R2.4)}", "R2.4"),
    ("\\reviewersection{Reviewer 2, Comment 5 (R2.5)}", "R2.5"),
    ("\\reviewersection{Reviewer 2, Comment 6 (R2.6)}", "R2.6"),
    ("\\reviewersection{Reviewer 2, Comment 7 (R2.7)}", "R2.7"),
    ("\\reviewersection{Reviewer 2, Comment 8 (R2.8)}", "R2.8"),
    ("\\reviewersection{Reviewer 2, Comment 9 (R2.9)}", "R2.9"),
    ("\\reviewersection{Reviewer 2, Comment 10 (R2.10)}", "R2.10"),
    ("\\reviewersection{Reviewer 2, Comment 11 (R2.11)}", "R2.11"),
    ("\\reviewersection{Reviewer 2, Comment 12 (R2.12)}", "R2.12"),
    ("\\reviewersection{Reviewer 2, Comment 13 (R2.13)}", "R2.13"),
    ("\\reviewersection{Reviewer 2, Comment 14 (R2.14)}", "R2.14"),
    ("\\reviewersection{Reviewer 2, Comment 15 (R2.15)}", "R2.15"),
    ("\\reviewersection{Reviewer 2, Comment 16 (R2.16)}", "R2.16"),
    ("\\reviewersection{Reviewer 2, Comment 17 (R2.17)}", "R2.17"),
    ("\\reviewersection{Reviewer 2, Comment 18 (R2.18)}", "R2.18"),
    ("\\reviewersection{Reviewer 2, Comment 19 (R2.19)}", "R2.19"),
    ("\\reviewersection{Reviewer 2, Comment 20 (R2.20)}", "R2.20"),
    ("\\reviewersection{Reviewer 2, Comment 21 (R2.21)}", "R2.21"),
    ("\\reviewersection{Reviewer 2, Comment 22 (R2.22)}", "R2.22"),
    ("\\reviewersection{Reviewer 2, Comment 23 (R2.23)}", "R2.23"),
    ("\\responsetoreviewer{Response to Reviewer 3}", None),
    ("\\reviewersection{Reviewer 3, Comment 1 (R3.1)}", "R3.1"),
    ("\\reviewersection{Reviewer 3, Comment 2 (R3.2)}", "R3.2"),
    ("\\reviewersection{Reviewer 3, Comment 3 (R3.3)}", "R3.3"),
    ("\\reviewersection{Reviewer 3, Comment 4 (R3.4)}", "R3.4"),
    ("\\reviewersection{Reviewer 3, Comment 5 (R3.5)}", "R3.5"),
    ("\\reviewersection{Reviewer 3, Minor comment 1 (R3.M1)}", "R3M1"),
]

SECTIONS_ZH = [
    ("\\responsetoreviewer{对审稿人 1 的回复}", None),
    ("\\reviewersection{审稿人 1，意见 1（R1.1）}", "R1.1"),
    ("\\reviewersection{审稿人 1，意见 2（R1.2）}", "R1.2"),
    ("\\reviewersection{审稿人 1，意见 3（R1.3）}", "R1.3"),
    ("\\reviewersection{审稿人 1，意见 4（R1.4）}", "R1.4"),
    ("\\reviewersection{审稿人 1，意见 5（R1.5）}", "R1.5"),
    ("\\reviewersection{审稿人 1，意见 6（R1.6）}", "R1.6"),
    ("\\reviewersection{审稿人 1，总评（可部署性）}", "R1G"),
    ("\\responsetoreviewer{对审稿人 2 的回复}", None),
    ("\\reviewersection{审稿人 2，意见 1（R2.1）}", "R2.1"),
    ("\\reviewersection{审稿人 2，意见 2（R2.2）}", "R2.2"),
    ("\\reviewersection{审稿人 2，意见 3（R2.3）}", "R2.3"),
    ("\\reviewersection{审稿人 2，意见 4（R2.4）}", "R2.4"),
    ("\\reviewersection{审稿人 2，意见 5（R2.5）}", "R2.5"),
    ("\\reviewersection{审稿人 2，意见 6（R2.6）}", "R2.6"),
    ("\\reviewersection{审稿人 2，意见 7（R2.7）}", "R2.7"),
    ("\\reviewersection{审稿人 2，意见 8（R2.8）}", "R2.8"),
    ("\\reviewersection{审稿人 2，意见 9（R2.9）}", "R2.9"),
    ("\\reviewersection{审稿人 2，意见 10（R2.10）}", "R2.10"),
    ("\\reviewersection{审稿人 2，意见 11（R2.11）}", "R2.11"),
    ("\\reviewersection{审稿人 2，意见 12（R2.12）}", "R2.12"),
    ("\\reviewersection{审稿人 2，意见 13（R2.13）}", "R2.13"),
    ("\\reviewersection{审稿人 2，意见 14（R2.14）}", "R2.14"),
    ("\\reviewersection{审稿人 2，意见 15（R2.15）}", "R2.15"),
    ("\\reviewersection{审稿人 2，意见 16（R2.16）}", "R2.16"),
    ("\\reviewersection{审稿人 2，意见 17（R2.17）}", "R2.17"),
    ("\\reviewersection{审稿人 2，意见 18（R2.18）}", "R2.18"),
    ("\\reviewersection{审稿人 2，意见 19（R2.19）}", "R2.19"),
    ("\\reviewersection{审稿人 2，意见 20（R2.20）}", "R2.20"),
    ("\\reviewersection{审稿人 2，意见 21（R2.21）}", "R2.21"),
    ("\\reviewersection{审稿人 2，意见 22（R2.22）}", "R2.22"),
    ("\\reviewersection{审稿人 2，意见 23（R2.23）}", "R2.23"),
    ("\\responsetoreviewer{对审稿人 3 的回复}", None),
    ("\\reviewersection{审稿人 3，意见 1（R3.1）}", "R3.1"),
    ("\\reviewersection{审稿人 3，意见 2（R3.2）}", "R3.2"),
    ("\\reviewersection{审稿人 3，意见 3（R3.3）}", "R3.3"),
    ("\\reviewersection{审稿人 3，意见 4（R3.4）}", "R3.4"),
    ("\\reviewersection{审稿人 3，意见 5（R3.5）}", "R3.5"),
    ("\\reviewersection{审稿人 3，次要意见 1（R3.M1）}", "R3M1"),
]


def latex_escape(text: str) -> str:
    text = text.replace("\\", "\\textbackslash{}")
    for ch in "&%#_{}":
        text = text.replace(ch, "\\" + ch)
    text = text.replace("$", "\\$")
    return text


def apply_bold(text: str, phrases: list[str]) -> str:
    """Wrap matching phrases in \\textbf{}, longest phrases first; skip nested overlaps."""
    spans: list[tuple[int, int]] = []
    for phrase in sorted(phrases, key=len, reverse=True):
        start = 0
        while True:
            idx = text.find(phrase, start)
            if idx < 0:
                break
            end = idx + len(phrase)
            if any(not (end <= a or idx >= b) for a, b in spans):
                start = idx + 1
                continue
            spans.append((idx, end))
            start = end
    if not spans:
        return text
    spans.sort()
    out = []
    pos = 0
    for a, b in spans:
        out.append(text[pos:a])
        out.append("\\textbf{" + text[a:b] + "}")
        pos = b
    out.append(text[pos:])
    return "".join(out)


def bold_comment(text: str, lang: str) -> str:
    return text


def parse_responses(body: str) -> dict[str, str]:
    """Map R ids from \\reviewersection{... (R1.1)} to authorresponse block."""
    id_pat = r"[（(](R[^）)]+)[）)]"
    pattern = re.compile(
        r"\\reviewersection\{[^}]*" + id_pat + r"[^}]*\}\s*"
        r"\\begin\{reviewercomment\}.*?\\end\{reviewercomment\}\s*"
        r"(\\begin\{authorresponse\}.*?\\end\{authorresponse\})",
        re.DOTALL,
    )
    general = re.search(
        r"\\reviewersection\{(?:Reviewer 1, General remark|审稿人 1，总评)[^}]*\}\s*"
        r"\\begin\{reviewercomment\}.*?\\end\{reviewercomment\}\s*"
        r"(\\begin\{authorresponse\}.*?\\end\{authorresponse\})",
        body,
        re.DOTALL,
    )
    out: dict[str, str] = {}
    for m in pattern.finditer(body):
        rid = m.group(1)
        if rid.startswith("R3.M"):
            rid = "R3M1"
        out[rid] = m.group(2).strip()
    if general:
        out["R1G"] = general.group(1).strip()
    return out


def skip_block(lang: str) -> str:
    if lang == "zh":
        return (
            "\\begin{authorresponse}\n"
            "\\noindent\\textit{本条与结节分割及良恶性分类无关；本回复信从略。}\n"
            "\\end{authorresponse}"
        )
    return (
        "\\begin{authorresponse}\n"
        "\\noindent\\textit{This comment does not concern nodule segmentation or benign--malignant classification; "
        "no point-by-point response is provided in this letter.}\n"
        "\\end{authorresponse}"
    )


def build_preamble(lang: str, responses: dict[str, str]) -> str:
    comments = COMMENTS_ZH if lang == "zh" else COMMENTS_EN
    sections = SECTIONS_ZH if lang == "zh" else SECTIONS_EN
    lines: list[str] = []
    for header, key in sections:
        lines.append(header)
        if key is None:
            continue
        body = bold_comment(comments[key], lang)
        lines.append("\\begin{reviewercomment}")
        lines.append(body)
        lines.append("\\end{reviewercomment}")
        if key in SKIP_RESPONSE:
            lines.append(skip_block(lang))
        elif key in responses:
            lines.append(responses[key])
        else:
            lines.append(skip_block(lang))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def patch_file(path: Path, lang: str) -> None:
    text = path.read_text(encoding="utf-8")
    marker = "\\responseappendix"
    if lang == "zh":
        marker = "\\responseappendixzh"
    idx = text.find(marker)
    if idx < 0:
        raise SystemExit(f"appendix marker not found in {path}")
    responses = parse_responses(text)
    # Normalize R1 general key
    preamble = build_preamble(lang, responses)
    path.write_text(preamble + text[idx:], encoding="utf-8")


def main() -> None:
    patch_file(GEN / "body_en.tex", "en")
    patch_file(GEN / "body_zh.tex", "zh")
    print("Patched body_en.tex and body_zh.tex")


if __name__ == "__main__":
    main()
