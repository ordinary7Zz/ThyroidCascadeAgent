% Template for ICASSP-2026 paper; to be used with:
%          spconf.sty  - ICASSP/ICIP LaTeX style file, and
%          IEEEbib.bst - IEEE bibliography style file.
% --------------------------------------------------------------------------
\documentclass{article}
\usepackage{spconf,amsmath,amssymb,graphicx,hyperref}
\usepackage{algorithm}
\usepackage{algpseudocode}
\usepackage{multirow}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{makecell}
\usepackage{adjustbox}
\usepackage[table,xcdraw]{xcolor}

\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}
\newcolumntype{Y}{>{\centering\arraybackslash}X}

% Title.
% ------
\title{Explainable Agent-Based Framework for Thyroid Ultrasound Diagnosis}
%
\name{Author(s) Name(s)\thanks{Thanks to XYZ agency for funding.}}
\address{Author Affiliation(s)}

\begin{document}
%\ninept
%
\maketitle
%
\begin{abstract}
We propose ThyroidAgent, an explainable agent-based framework for thyroid nodule ultrasound diagnosis that coordinates segmentation and classification experts through dual-path routing driven by classification consensus and a GT-trained radiomics judge. Unlike static pipelines, ThyroidAgent runs heterogeneous experts in parallel and routes each case through a consensus shortcut or a dispute-resolution path based on whether independent classifiers agree. A radiomics classifier trained on ground-truth masks serves as a dual-purpose judge, evaluating segmentation quality via inter-model feature consistency while providing an independent malignancy signal that is integrated with all expert predictions by an LLM arbiter in the dispute-resolution path. An LLM arbiter, operating within this radiomics-coupled framework, performs case-level segmentation selection and arbitrates the hardest classification disputes. Each routing decision is transparent and grounded in structured evidence, enabling case-level explainability through SHAP-interpretable radiomics features.
Experiments on five datasets demonstrate that ThyroidAgent outperforms static baselines, achieving a mean Dice of 86.1\% and mean AUROC of 0.896, confirming more reliable and context-aware clinical deployment.
\end{abstract}
%
\begin{keywords}
Ultrasound, Thyroid Nodule, Segmentation, Malignancy Classification, Cascade Inference
\end{keywords}
%
\section{Introduction}
\label{sec:intro}

\begin{figure}[t]
    \centering
    \includegraphics[width=\columnwidth]{figures/Fig1.pdf}
    \caption{Overview of the ThyroidAgent framework. While traditional systems use fixed pipelines, ThyroidAgent routes each case through a consensus shortcut or a dispute-resolution path based on classification consensus, with a GT-trained radiomics judge providing segmentation quality assessment and an independent malignancy signal.}
    \label{fig:ThyroidAgent}
\end{figure}

Deep learning has substantially improved thyroid ultrasound analysis in both nodule segmentation~\cite{gong2021multi,dong2024ultrasound,haribabu2025mlrt} and malignancy classification~\cite{gong_acl_2022,sujini2025automated,das2024deep}. However, these tasks are typically developed and evaluated in isolation, leading to fixed pipelines that cannot jointly exploit segmentation-derived structural evidence and classification confidence. Prior attempts at task coupling—such as shared encoders with task-specific heads~\cite{he2023joint,rhanoui2025multi,wu2023multi}, ROI-based feature extraction~\cite{kang2022thyroid}, or thyroid-region priors~\cite{gong2021multi,gong_thyroid_2023}—offer limited cross-task interaction. Radiomics-assisted methods~\cite{park2021combining} and expert-routing medical VLMs~\cite{she2026echovlm,bai2025qwen3,sellergren2025medgemma} each address only part of the challenge: the former lack dynamic mask-quality control, while the latter, including EchoVLM~\cite{she2026echovlm}, build monolithic VLMs rather than case-level cascade coordination over external experts.

We propose \textit{ThyroidAgent}, an explainable agent-based framework that routes each case through a dual-path cascade driven by classification consensus and a GT-trained radiomics judge (Fig.~\ref{fig:ThyroidAgent}). When independent classifiers agree, a consensus shortcut uses their label as an anchor to guide segmentation selection; when they disagree, a dispute-resolution path invokes a radiomics classifier—trained on ground-truth masks—that simultaneously evaluates segmentation quality via inter-model feature consistency and provides an independent malignancy signal. The judge's prediction is then integrated with all independent classifier outputs by an LLM arbiter, ensuring ROI-level radiomics evidence directly contributes to the final classification. Motivated by the reasoning capability of LLMs~\cite{dong_survey_2022,bai2025qwen3,sellergren2025medgemma}, we further employ an LLM as a decision module within this radiomics-coupled framework. Unlike prior work that uses LLMs to independently select experts for each task, ThyroidAgent's LLM operates within the bidirectional coupling: classification consensus guides segmentation selection, while the radiomics judge's malignancy prediction feeds back into classification arbitration. The LLM is invoked for segmentation selection and the hardest classification disputes. Connected-component analysis (CCA) is available as an optional mask-refinement step for ensemble mode, independent of the routing policy.

The key contributions are:
\textbf{1. Explainable dual-path routing.} ThyroidAgent replaces static pipelines with transparent, case-level routing driven by classification consensus, enabling explainable decisions under heterogeneous acquisition conditions.
\textbf{2. GT-trained radiomics judge.} An AutoGluon classifier trained on GT-mask radiomics serves as a dual-purpose judge for segmentation quality assessment and independent malignancy prediction, driving pre-filtering, mask selection, and classification reconciliation.
\textbf{3. Unified benchmark.} We consolidate multiple datasets with aligned annotations, enabling systematic cross-dataset evaluation under heterogeneous acquisition conditions.

\begin{figure}[t]
    \centering
    \includegraphics[width=\columnwidth]{figures/Fig2.pdf}
    \caption{Detailed workflow of the ThyroidAgent system, showing the cascade inference process with parallel expert inference, classification-consensus-driven path splitting, GT-trained radiomics judging, LLM-guided segmentation selection, and rule-based reconciliation with LLM arbitration.}
    \label{fig:WorkFlow}
\end{figure}

\section{Method}
\label{sec:method}

\subsection{Expert Pool}
\label{sec:dinov3_models}
The expert pool combines multiple DINOv3-based variants with heterogeneous architectures to improve robustness under cross-dataset variability. The DINOv3 variants share a common backbone with task-specific lightweight heads~\cite{simeoni2025dinov3} and are trained on stacked datasets with varying input resolutions (128, 224, 448) and dilation settings. The pool also incorporates heterogeneous architectures covering complementary inductive biases for both segmentation and classification. Segmentation experts use a U-Net-style decoder with skip fusion, optimized by a boundary-aware weighted BCE+IoU loss $\mathcal{L}_{\mathrm{seg}}$. Classification experts use global pooling followed by an attention-based head, trained with a generalized logit-adjustment (GLA) loss to alleviate class imbalance. The core weight and logit adjustment are:
\begin{equation}
\begin{aligned}
w &= 1 + 5 \cdot \left| \operatorname{AvgPool}_{31}(y) - y \right|,\\
z'_b &= z_b + \tau \left( \log p_{\text{pos}} - \log p_{\text{neg}} \right),
\end{aligned}
\label{eq:losses}
\end{equation}
where $y$ is the segmentation target, $\operatorname{AvgPool}_{31}(\cdot)$ emphasizes boundary pixels, $z_b$ is the original logit, $p_{\text{pos}}$/$p_{\text{neg}}$ are empirical class priors, and $\tau$ is the adjustment coefficient. The logit adjustment is a constant offset applied to all samples independent of their label, which is the sigmoid-equivalent of softmax logit adjustment for binary classification.

\subsection{GT-Trained Radiomics Judge}
\label{sec:radiomics_judge}
A key component of ThyroidAgent is a \emph{GT-trained radiomics judge}: an AutoGluon tabular classifier trained on radiomics features extracted from ground-truth masks. Unlike mask-guided radiomics descriptors used in prior work solely as classification evidence, this judge serves a dual purpose---it simultaneously assesses segmentation quality and provides an independent malignancy signal for each predicted mask. Given an image $x$ and a mask $M$, we extract a 2D PyRadiomics feature vector $f = \phi(x, M)$ covering shape2D and texture families. Representative formulations include:
\begin{equation}
\begin{aligned}
A = \sum_{x=1}^{H} \sum_{y=1}^{W} \mathbb{I} \left[ M(x,y) = 1 \right], \\
\mathrm{Energy} = \sum_{i=1}^{N_g} \sum_{j=1}^{N_g} P(i,j)^2,
\end{aligned}
\end{equation}
where $A$ denotes the ROI area, $M(x,y) \in \{0,1\}$ is the binary ROI mask at spatial coordinate $(x,y)$, $\mathbb{I}[\cdot]$ is the indicator function, $H \times W$ is the mask resolution, $\mathrm{Energy}$ is the gray-level co-occurrence matrix (GLCM) energy, $P(i,j)$ is the normalized GLCM entry associated with gray levels $i$ and $j$, and $N_g$ is the number of discretized gray levels used in radiomics quantization. The judge $g_\theta$ is trained on $\{(f_i, y_i)\}_{i=1}^{N}$ where $f_i = \phi(x_i, M_i^{\mathrm{GT}})$ are features extracted from ground-truth masks and $y_i$ is the malignancy label. At inference time, for each predicted mask $M_k$, the judge outputs a malignancy probability $p_{\mathrm{judge}}^{(k)} = g_\theta(\phi(x, M_k))$ and a confidence $c_{\mathrm{judge}}^{(k)} = \max(p_{\mathrm{judge}}^{(k)}, 1-p_{\mathrm{judge}}^{(k)})$. The intuition is that a more accurate mask yields radiomics features closer to those of other plausible predictions, producing more consistent classification outputs. Together, $\{p_{\mathrm{judge}}^{(k)}, c_{\mathrm{judge}}^{(k)}\}$ form the judge evidence that drives pre-filtering, segmentation selection, and classification reconciliation in the cascade.

\begin{algorithm}[t]
\caption{ThyroidAgent cascade inference}
\label{alg:thyroidagent_inference}
\begin{algorithmic}[1]
\Require Image $x$; seg experts $\mathcal{E}_{seg}$; cls experts $\mathcal{E}_{cls}$; radiomics judge $g_\theta$
\Ensure Final mask $\hat{M}$, label $\hat{y}$

\Statex \textbf{Phase 1--2: Parallel expert inference}
\State $\{M_k\}_{k=1}^{K} \gets \mathrm{RunSeg}(\mathcal{E}_{seg}, x)$
\State $\{p_m\}_{m=1}^{M} \gets \mathrm{RunCls}(\mathcal{E}_{cls}, x)$ \Comment{mask-free}

\Statex \textbf{Phase 3: Consensus check \& path split}
\State consensus $\gets \big[\arg\max_m p_m \text{ all equal}\big]$
\If{consensus}
  \State $a \gets$ consensus class \Comment{classification anchor}
  \State $\hat{k} \gets \mathrm{SegSelect}(\{M_k\}, g_\theta, a)$ \Comment{LLM-guided, anchor-coupled}
  \State $\hat{M} \gets M_{\hat{k}}$; $\hat{y} \gets a$
  \State \Return $\hat{M}, \hat{y}$ \Comment{Path A: shortcut}
\EndIf

\Statex \textbf{Phase 4: Pre-filter \& mask selection (Path B)}
\State $\{M_k\} \gets \mathrm{PreFilter}(\{M_k\}, g_\theta)$ \Comment{outlier removal}
\State $\hat{k} \gets \mathrm{SegSelect}(\{M_k\}, g_\theta, \mathrm{None})$ \Comment{LLM-guided}
\State $\hat{M} \gets M_{\hat{k}}$

\Statex \textbf{Phase 5: Classification reconciliation}
\State $p_{\mathrm{rad}} \gets g_\theta\big(\phi(x, \hat{M})\big)$ \Comment{AutoGluon on selected mask}
\State $\hat{y} \gets \mathrm{LLMArbitrate}(\{p_m\}, p_{\mathrm{rad}}, \hat{M})$ \Comment{LLM with all evidence}
\State \Return $\hat{M}, \hat{y}$
\end{algorithmic}
\end{algorithm}

In Algorithm~\ref{alg:thyroidagent_inference}, $\mathrm{PreFilter}(\cdot)$, $\mathrm{SegSelect}(\cdot)$, and the reconciliation policy are defined in Eq.~\eqref{eq:prefilter_cos}--\eqref{eq:reconcile}. Connected-component analysis (CCA)~\cite{liu2025shapekit} is available as an optional mask-refinement step. The LLM uses low-temperature decoding (temperature 0.3, bounded output length) with a strict JSON decision schema; it receives structured evidence summaries—including morphology, inter-model agreement, radiomics judge predictions, and classification confidence—rather than raw image pixels. When the LLM is unavailable, $\mathrm{SegSelect}$ falls back to selecting the mask with the highest inter-model IoU agreement, and $\mathrm{LLMArbitrate}$ falls back to weighted soft-voting over all predictions including $p_{\mathrm{rad}}$.

\subsection{Cascade Inference with Dual-Path Routing}

\textbf{Pre-filtering.} Given $K$ candidate masks, the pre-filter applies two independent outlier rules based on the radiomics judge outputs. First, masks whose feature vector $f_k$ has a maximum cosine similarity to any other candidate below a threshold $\tau_{\cos}$ are flagged as feature outliers:
\begin{equation}
\max_{j \neq k} \cos(f_k, f_j) < \tau_{\cos}.
\label{eq:prefilter_cos}
\end{equation}
Second, masks whose judge malignancy probability deviates from the median by more than a threshold $\tau_{\mathrm{prob}}$ are flagged as probability outliers:
\begin{equation}
\big| p_{\mathrm{judge}}^{(k)} - \tilde{p} \big| > \tau_{\mathrm{prob}},
\label{eq:prefilter_prob}
\end{equation}
where $\tilde{p}$ is the median judge probability. Flagged masks are removed, subject to a safety floor of $\max(3, K/2)$ retained models; if removal would violate the floor, all filters are canceled. We use $\tau_{\cos}=0.8$ and $\tau_{\mathrm{prob}}=0.4$.

\textbf{Segmentation selection.} The selector first applies an anchor-consistency filter (Path~A only): masks whose judge prediction strongly contradicts the classification anchor $a$ are excluded, i.e., removed when $c_{\mathrm{judge}}^{(k)} > 0.6$ and $|\hat{y}_{\mathrm{judge}}^{(k)} - a| > 0.4$. An LLM then selects the best mask from the surviving candidates by integrating structured evidence including inter-model IoU agreement,
\begin{equation}
a_{\mathrm{agree}}^{(k)} = \frac{1}{K-1}\sum_{j \neq k} \mathrm{IoU}(M_k, M_j),
\label{eq:segsel}
\end{equation}
morphology metrics, radiomics judge predictions, and the classification anchor (Path~A only). If the filter removes all masks, the anchor constraint is relaxed and selection proceeds from the full candidate set.

\textbf{Classification reconciliation.} Given the selected mask $\hat{M}$, the judge produces $p_{\mathrm{rad}} = g_\theta(\phi(x, \hat{M}))$. An LLM arbiter receives all expert predictions—including the $M$ independent classifiers $\{p_m\}$ and the radiomics judge $p_{\mathrm{rad}}$—along with the segmentation selection rationale, and produces the final classification:
\begin{equation}
\hat{y} = \mathrm{LLMArbitrate}\big(\{p_m\}_{m=1}^{M},\; p_{\mathrm{rad}},\; \hat{M}\big),
\label{eq:reconcile}
\end{equation}
where the LLM integrates structured evidence from all sources, including individual expert predictions and confidences, the radiomics judge's malignancy probability, and the segmentation selection reasoning. This design ensures the ROI-level radiomics signal directly contributes to the final decision, making Path~B complementary to Path~A's consensus shortcut.

\begin{table}[t]
    \centering
    \caption{Segmentation performance (Dice, \%) across 5 datasets with 95\% confidence intervals.}
    \label{tab:table1_seg_blocks}
    \footnotesize
    \setlength{\tabcolsep}{4pt}
    \renewcommand{\arraystretch}{1.15}
    \begin{tabular}{@{}lccccc@{}}
        \toprule
        \textbf{Method} & \textbf{TN3K} & \textbf{DDTI} & \textbf{ThyroidXL} & \textbf{PKTN} & \textbf{TN5K} \\
        \midrule
        TransUNet~\cite{chen2024transunet}
        & \makecell{81.84 \\ {\tiny [80.22, 83.46]}}
        & \makecell{76.58 \\ {\tiny [74.96, 78.20]}}
        & \makecell{85.75 \\ {\tiny [85.18, 86.32]}}
        & \makecell{76.89 \\ {\tiny [73.33, 80.45]}}
        & \makecell{78.54 \\ {\tiny [77.03, 80.05]}} \\
        MedSegX~\cite{zhang2025generalist}
        & \makecell{83.93 \\ {\tiny [83.14, 84.72]}}
        & \makecell{85.40 \\ {\tiny [85.22, 85.58]}}
        & \makecell{79.98 \\ {\tiny [79.62, 80.34]}}
        & \makecell{80.63 \\ {\tiny [80.21, 81.05]}}
        & \makecell{83.10 \\ {\tiny [82.62, 83.58]}} \\
        MedSAM2~\cite{ma2025medsam2}
        & \makecell{84.47 \\ {\tiny [83.45, 85.49]}}
        & \makecell{90.72 \\ {\tiny [90.51, 90.93]}}
        & \makecell{86.94 \\ {\tiny [86.58, 87.30]}}
        & \makecell{\textbf{83.46} \\ {\tiny [80.86, 86.06]}}
        & \makecell{83.03 \\ {\tiny [81.74, 84.32]}} \\
        UltraFedFM~\cite{jiang2025pretraining}
        & \makecell{81.18 \\ {\tiny [79.72, 82.64]}}
        & \makecell{83.10 \\ {\tiny [82.77, 83.43]}}
        & \makecell{84.70 \\ {\tiny [84.17, 85.23]}}
        & \makecell{75.31 \\ {\tiny [74.19, 76.43]}}
        & \makecell{77.13 \\ {\tiny [75.75, 78.51]}} \\
        \midrule
        \textbf{ThyroidAgent}
        & \makecell{\textbf{85.28} \\ {\tiny [84.00, 86.56]}}
        & \makecell{\textbf{91.46} \\ {\tiny [91.32, 91.60]}}
        & \makecell{\textbf{87.58} \\ {\tiny [87.14, 88.02]}}
        & \makecell{82.99 \\ {\tiny [80.89, 85.09]}}
        & \makecell{\textbf{83.26} \\ {\tiny [81.92, 84.60]}} \\
        \bottomrule
    \end{tabular}
\end{table}

\section{Results}
\label{sec:results}
We evaluate on a consolidated thyroid ultrasound benchmark assembled from TN3K~\cite{gong2021multi}, TN5K~\cite{zhang2025tn5000}, DDTI~\cite{pedraza2015open}, ThyroidXL~\cite{duong2025thyroidxl}, and PKTN~\cite{sun2025clip}, spanning heterogeneous acquisition protocols and device settings. Patient-level 0.7/0.15/0.15 splits are used where applicable, and stacked training sets are formed by merging training portions across datasets (up to 26,074 images). Baselines include TransUNet~\cite{chen2024transunet}, MedSegX~\cite{zhang2025generalist}, MedSAM2~\cite{ma2025medsam2}, UltraFedFM~\cite{jiang2025pretraining}, MedSigLIP~\cite{sellergren2025medgemma,zhai2023siglip}, BiomedCLIP~\cite{zhang2023biomedclip}, LSNet~\cite{wang2025lsnet}, RepViT~\cite{wang2023repvit}, ResNet50~\cite{he2016deep}, Qwen3-VL-8B-Instruct~\cite{bai2025qwen3}, MedGemma-4B~\cite{sellergren2025medgemma}, and GPT-5.1~\cite{openai2025gpt5systemcard}. Open-source VLMs are adapted with LoRA fine-tuning; GPT-5.1 uses prompt-only API inference. All models are trained with AdamW (lr $1e{-}4$, batch 12, 50 epochs) on 3$\times$48\,GB NVIDIA RTX A6000 GPUs.

\subsection{Main Results}
Segmentation performance is evaluated using Dice (\%). Table~\ref{tab:table1_seg_blocks} compares ThyroidAgent against three categories of methods: general-purpose segmenters (MedSegX~\cite{zhang2025generalist}, MedSAM2~\cite{ma2025medsam2}), a specialized ultrasound model (UltraFedFM~\cite{jiang2025pretraining}), and a recent advanced transformer-based approach (TransUNet~\cite{chen2024transunet}). ThyroidAgent achieves the best Dice on 4 of 5 datasets, with the largest gain on DDTI (+0.74 over MedSAM2, 91.46 vs 90.72). On PKTN, ThyroidAgent (82.99) slightly underperforms MedSAM2 (83.46), likely because PKTN's clip-based low-quality images produce mask predictions with lower inter-model variance, reducing the discriminative power of the feature-consistency-based judge.
\begin{table}[b]
    \centering
    \caption{Classification performance (AUROC) across 4 datasets with 95\% confidence intervals.}
    \label{tab:table2_cls_blocks2}
    \footnotesize
    \setlength{\tabcolsep}{4pt}
    \renewcommand{\arraystretch}{1.15}
    \begin{tabular}{@{}lcccc@{}}
        \toprule
        \textbf{Method} & \textbf{TN3K} & \textbf{DDTI} & \textbf{ThyroidXL} & \textbf{TN5K} \\
        \midrule
        MedSigLIP~\cite{sellergren2025medgemma,zhai2023siglip}
        & \makecell{0.831 \\ {\tiny ---}}
        & \makecell{0.798 \\ {\tiny ---}}
        & \makecell{0.924 \\ {\tiny ---}}
        & \makecell{0.941 \\ {\tiny ---}} \\
        BiomedCLIP~\cite{zhang2023biomedclip}
        & \makecell{0.798 \\ {\tiny ---}}
        & \makecell{0.762 \\ {\tiny ---}}
        & \makecell{0.905 \\ {\tiny ---}}
        & \makecell{0.928 \\ {\tiny ---}} \\
        ResNet-50~\cite{he2016deep}
        & \makecell{0.767 \\ {\tiny [0.728, 0.807]}}
        & \makecell{0.670 \\ {\tiny [0.586, 0.755]}}
        & \makecell{0.904 \\ {\tiny [0.893, 0.916]}}
        & \makecell{0.932 \\ {\tiny [0.915, 0.949]}} \\
        RepViT~\cite{wang2023repvit}
        & \makecell{0.556 \\ {\tiny [0.509, 0.602]}}
        & \makecell{0.616 \\ {\tiny [0.536, 0.697]}}
        & \makecell{0.777 \\ {\tiny [0.759, 0.796]}}
        & \makecell{0.660 \\ {\tiny [0.623, 0.698]}} \\
        LSNet~\cite{wang2025lsnet}
        & \makecell{0.810 \\ {\tiny [0.776, 0.843]}}
        & \makecell{0.758 \\ {\tiny [0.692, 0.824]}}
        & \makecell{0.918 \\ {\tiny [0.906, 0.929]}}
        & \makecell{0.909 \\ {\tiny [0.889, 0.929]}} \\
        UltraFedFM~\cite{jiang2025pretraining}
        & \makecell{0.846 \\ {\tiny [0.776, 0.916]}}
        & \makecell{0.752 \\ {\tiny [0.581, 0.923]}}
        & \makecell{0.924 \\ {\tiny [0.914, 0.934]}}
        & \makecell{0.930 \\ {\tiny [0.912, 0.947]}} \\
        MedGemma~\cite{sellergren2025medgemma}
        & \makecell{0.849 \\ {\tiny [0.819, 0.880]}}
        & \makecell{0.826 \\ {\tiny [0.761, 0.890]}}
        & \makecell{0.937 \\ {\tiny [0.928, 0.947]}}
        & \makecell{0.944 \\ {\tiny [0.929, 0.960]}} \\
        Qwen3-VL-8B~\cite{bai2025qwen3}
        & \makecell{0.824 \\ {\tiny [0.791, 0.856]}}
        & \makecell{0.736 \\ {\tiny [0.667, 0.805]}}
        & \makecell{0.905 \\ {\tiny [0.894, 0.917]}}
        & \makecell{0.921 \\ {\tiny [0.903, 0.940]}} \\
        GPT-5.1~\cite{openai2025gpt5systemcard}
        & \makecell{0.692 \\ {\tiny [0.650, 0.735]}}
        & \makecell{0.635 \\ {\tiny [0.543, 0.726]}}
        & \makecell{0.706 \\ {\tiny [0.659, 0.753]}}
        & \makecell{0.774 \\ {\tiny [0.674, 0.873]}} \\
        \midrule
        \textbf{ThyroidAgent}
        & \makecell{\textbf{0.869} \\ {\tiny [0.834, 0.904]}}
        & \makecell{0.799 \\ {\tiny [0.725, 0.873]}}
        & \makecell{\textbf{0.968} \\ {\tiny [0.961, 0.974]}}
        & \makecell{\textbf{0.947} \\ {\tiny [0.932, 0.963]}} \\
        \bottomrule
    \end{tabular}
\end{table}
For malignancy classification, we evaluate AUROC. Table~\ref{tab:table2_cls_blocks2} compares ThyroidAgent with four categories of methods: medical vision-language models (MedSigLIP~\cite{sellergren2025medgemma,zhai2023siglip}, BiomedCLIP~\cite{zhang2023biomedclip}), ultrasound-specific models (UltraFedFM~\cite{jiang2025pretraining}), general-purpose classifiers (LSNet~\cite{wang2025lsnet}, RepViT~\cite{wang2023repvit}, ResNet50~\cite{he2016deep}), and vision-language models (Qwen3-VL-8B-Instruct~\cite{bai2025qwen3}, MedGemma-4B~\cite{sellergren2025medgemma}, GPT-5.1~\cite{openai2025gpt5systemcard}). PKTN is excluded from classification evaluation as it lacks malignancy labels. ThyroidAgent achieves the best AUROC on 3 of 4 datasets, with the largest gain on ThyroidXL (+0.031 over MedGemma, 0.968 vs 0.937). On DDTI, ThyroidAgent (0.799) underperforms MedGemma (0.826), possibly because DDTI's smaller training set limits the diversity of the expert pool. GPT-5.1 performs poorly across all datasets (mean AUROC 0.702), confirming that prompt-only inference without task-specific adaptation is insufficient for thyroid malignancy assessment.

\begin{figure}[t]
    \centering
    \includegraphics[width=\columnwidth]{figures/Fig3.pdf}
    \caption{Analysis of agentic aggregation.
    (a) Cls vote consistency distribution across models.
    (b) Distribution of Seg disagreement scores (Area-CV).
    (c) Cls performance across Seg Dice-score bins.}
    \label{fig:system_analysis}
\end{figure}

\subsection{System Analysis}
\label{sec:effectiveness}
The rationale for using dual-path cascade routing is supported by the fact that multi-model outputs are not trivially redundant. Both segmentation and classification experts exhibit non-negligible disagreement across samples, as illustrated by the Area-CV distribution (median = 0.057, 90th percentile = 0.250) in Fig.~\ref{fig:system_analysis}(b) and the vote-consistency pie in Fig.~\ref{fig:system_analysis}(a). This indicates that no single model consistently performs across all images, which motivates the consensus-based path split and radiomics-judge-driven selection. Fig.~\ref{fig:system_analysis}(c) further shows that ThyroidAgent outperforms heuristics such as selecting the most confident expert or majority voting, especially in the Dice-score range of [0.6, 0.8], where radiomics features improve contour and texture characterization.

\begin{figure}[t]
    \centering
    \includegraphics[width=\columnwidth]{figures/Fig4.pdf}
    \caption{Interpretability analysis of classification and segmentation evidence.}
    \label{fig:interpretability_analysis}
\end{figure}

Fig.~\ref{fig:interpretability_analysis}(a) shows the global SHAP feature importance of the radiomics judge. Shape descriptors dominate the prediction: \emph{Sphericity} and \emph{Elongation} are the top-2 contributors, followed by \emph{Perimeter}, \emph{LRHGLE}, and \emph{SRLGLE}, confirming that malignancy cues are primarily morphological rather than textural. Fig.~\ref{fig:interpretability_analysis}(b) decomposes a single malignant prediction into feature-level contributions, showing how these descriptors collectively shift the base value to the final decision. Fig.~\ref{fig:interpretability_analysis}(c) compares selected masks with ground truth across cases with varying judge confidence, demonstrating that the judge assigns higher confidence to masks whose radiomics features stay consistent with the consensus of plausible predictions.

\section{Conclusion}
\label{sec:conclusion}
We proposed ThyroidAgent, an explainable agent-based framework that dynamically integrates segmentation and classification for thyroid ultrasound diagnosis. By routing each case through a consensus shortcut or a radiomics-coupled dispute-resolution path, the framework adapts to case-level difficulty while maintaining interpretability. The GT-trained radiomics judge bridges the two tasks---classification consensus guides segmentation selection, while the judge's malignancy prediction informs classification arbitration---enabling robust performance across heterogeneous datasets. Together with a consolidated multi-source benchmark, ThyroidAgent demonstrates improved robustness, interpretability, and generalization for clinical deployment. Future work will focus on expanding the benchmark and exploring additional modalities.

% References should be produced using the bibtex program from suitable
% BiBTeX files (here: strings, refs, manuals). The IEEEbib.bst bibliography
% style file from IEEE produces unsorted bibliography list.
% -------------------------------------------------------------------------
\bibliographystyle{IEEEbib}
\bibliography{ref}

\end{document}
