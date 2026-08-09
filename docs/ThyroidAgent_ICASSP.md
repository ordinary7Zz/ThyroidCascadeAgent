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

\begin{table*}[t]
    \centering
    \caption{Cross-dataset generalization for thyroid nodule segmentation. Dice coefficient (\%) and 95th-percentile Hausdorff distance (HD95, mm) are reported with 95\% confidence intervals.}
    \label{tab:table1_seg_blocks}
    \scriptsize
    \setlength{\tabcolsep}{3pt}
    \renewcommand{\arraystretch}{1.15}
    \begin{tabular}{lccccccc}
        \toprule
        \textbf{Model} & \textbf{TN3K} & \textbf{ThyroidXL} & \textbf{PKTN} & \textbf{TN5K} & \textbf{DDTI} & \textbf{ZJH-8K} & \textbf{RJH-7K} \\
        \midrule
        \multicolumn{8}{l}{\textit{Dice (\%) $\uparrow$}} \\
        \midrule
        TransUNet~\cite{chen2024transunet}
        & \makecell{81.8 \\ {\tiny [80.2, 83.5]}}
        & \makecell{85.8 \\ {\tiny [85.2, 86.3]}}
        & \makecell{76.9 \\ {\tiny [73.3, 80.5]}}
        & \makecell{78.5 \\ {\tiny [77.0, 80.1]}}
        & \makecell{76.6 \\ {\tiny [75.0, 78.2]}}
        & \makecell{80.7 \\ {\tiny [79.8, 81.7]}}
        & \makecell{84.8 \\ {\tiny [84.5, 85.2]}} \\
        MedSegX~\cite{zhang2025generalist}
        & \makecell{83.9 \\ {\tiny [83.1, 84.7]}}
        & \makecell{80.0 \\ {\tiny [79.6, 80.3]}}
        & \makecell{80.6 \\ {\tiny [80.2, 81.1]}}
        & \makecell{83.1 \\ {\tiny [82.6, 83.6]}}
        & \makecell{75.1 \\ {\tiny [73.4, 76.8]}}
        & \makecell{84.1 \\ {\tiny [83.7, 84.5]}}
        & \makecell{85.4 \\ {\tiny [85.2, 85.6]}} \\
        MedSAM2~\cite{ma2025medsam2}
        & \makecell{84.5 \\ {\tiny [83.5, 85.5]}}
        & \makecell{86.9 \\ {\tiny [86.6, 87.3]}}
        & \makecell{\textbf{83.5} \\ {\tiny [80.9, 86.1]}}
        & \makecell{83.0 \\ {\tiny [81.7, 84.3]}}
        & \makecell{84.7 \\ {\tiny [83.5, 86.0]}}
        & \makecell{86.3 \\ {\tiny [85.6, 87.0]}}
        & \makecell{90.7 \\ {\tiny [90.5, 90.9]}} \\
        UltraFedFM~\cite{jiang2025pretraining}
        & \makecell{81.2 \\ {\tiny [79.7, 82.6]}}
        & \makecell{84.7 \\ {\tiny [84.2, 85.2]}}
        & \makecell{75.3 \\ {\tiny [74.2, 76.4]}}
        & \makecell{77.1 \\ {\tiny [75.8, 78.5]}}
        & \makecell{75.6 \\ {\tiny [73.9, 77.2]}}
        & \makecell{80.6 \\ {\tiny [79.8, 81.5]}}
        & \makecell{83.1 \\ {\tiny [82.8, 83.4]}} \\
        \rowcolor{lightgray}
        \textbf{ThyroidAgent}
        & \makecell{\textbf{85.3} \\ {\tiny [84.0, 86.6]}}
        & \makecell{\textbf{87.6} \\ {\tiny [87.1, 88.0]}}
        & \makecell{83.0 \\ {\tiny [80.9, 85.1]}}
        & \makecell{\textbf{83.3} \\ {\tiny [81.9, 84.6]}}
        & \makecell{\textbf{85.6} \\ {\tiny [84.6, 86.7]}}
        & \makecell{\textbf{94.3} \\ {\tiny [93.9, 94.7]}}
        & \makecell{\textbf{91.5} \\ {\tiny [91.3, 91.6]}} \\
        \midrule
        \multicolumn{8}{l}{\textit{HD95 (mm) $\downarrow$}} \\
        \midrule
        TransUNet~\cite{chen2024transunet}
        & \makecell{27.3 \\ {\tiny [21.8, 32.8]}}
        & \makecell{22.4 \\ {\tiny [21.1, 23.8]}}
        & \makecell{26.9 \\ {\tiny [17.2, 36.5]}}
        & \makecell{22.3 \\ {\tiny [18.9, 25.8]}}
        & \makecell{17.1 \\ {\tiny [15.6, 18.7]}}
        & \makecell{18.4 \\ {\tiny [17.6, 19.1]}}
        & \makecell{18.8 \\ {\tiny [18.1, 19.6]}} \\
        MedSegX~\cite{zhang2025generalist}
        & \makecell{11.0 \\ {\tiny [10.3, 11.6]}}
        & \makecell{11.1 \\ {\tiny [10.8, 11.4]}}
        & \makecell{10.8 \\ {\tiny [10.1, 11.5]}}
        & \makecell{11.8 \\ {\tiny [11.0, 12.5]}}
        & \makecell{18.4 \\ {\tiny [16.7, 20.0]}}
        & \makecell{11.0 \\ {\tiny [10.6, 11.3]}}
        & \makecell{9.4 \\ {\tiny [9.2, 9.6]}} \\
        MedSAM2~\cite{ma2025medsam2}
        & \makecell{11.5 \\ {\tiny [10.0, 13.0]}}
        & \makecell{5.5 \\ {\tiny [5.0, 5.9]}}
        & \makecell{10.6 \\ {\tiny [6.9, 14.2]}}
        & \makecell{10.9 \\ {\tiny [9.8, 12.1]}}
        & \makecell{10.1 \\ {\tiny [8.9, 11.3]}}
        & \makecell{6.8 \\ {\tiny [6.2, 7.4]}}
        & \makecell{2.9 \\ {\tiny [2.8, 3.1]}} \\
        UltraFedFM~\cite{jiang2025pretraining}
        & \makecell{15.0 \\ {\tiny [12.9, 17.1]}}
        & \makecell{8.1 \\ {\tiny [7.5, 8.7]}}
        & \makecell{16.1 \\ {\tiny [14.4, 17.8]}}
        & \makecell{15.0 \\ {\tiny [13.3, 16.6]}}
        & \makecell{18.1 \\ {\tiny [16.7, 19.6]}}
        & \makecell{8.7 \\ {\tiny [7.9, 9.5]}}
        & \makecell{9.1 \\ {\tiny [8.7, 9.4]}} \\
        \rowcolor{lightgray}
        \textbf{ThyroidAgent}
        & \makecell{\textbf{10.3} \\ {\tiny [8.6, 12.0]}}
        & \makecell{\textbf{5.4} \\ {\tiny [4.9, 6.0]}}
        & \makecell{\textbf{9.0} \\ {\tiny [5.4, 12.6]}}
        & \makecell{\textbf{10.1} \\ {\tiny [8.9, 11.4]}}
        & \makecell{\textbf{9.2} \\ {\tiny [8.2, 10.3]}}
        & \makecell{\textbf{2.3} \\ {\tiny [1.9, 2.6]}}
        & \makecell{\textbf{1.9} \\ {\tiny [1.8, 2.0]}} \\
        \bottomrule
    \end{tabular}
\end{table*}

\section{Experiments}
\label{sec:experiment}
We evaluate on a consolidated thyroid ultrasound benchmark assembled from TN3K~\cite{gong2021multi}, TN5K~\cite{zhang2025tn5000}, DDTI~\cite{pedraza2015open}, ThyroidXL~\cite{duong2025thyroidxl}, PKTN~\cite{sun2025clip}, ZJH-8K, and RJH-7K, spanning heterogeneous acquisition protocols and device settings. Patient-level 0.7/0.15/0.15 splits are used where applicable, and stacked training sets are formed by merging training portions across datasets (up to 26,074 images). Segmentation is evaluated with Dice (\%) and HD95 (mm); classification with AUROC and AUPRC. Baselines include TransUNet~\cite{chen2024transunet}, MedSegX~\cite{zhang2025generalist}, MedSAM2~\cite{ma2025medsam2}, UltraFedFM~\cite{jiang2025pretraining}, LSNet~\cite{wang2025lsnet}, RepViT~\cite{wang2023repvit}, ResNet50~\cite{he2016deep}, Qwen3-VL-8B-Instruct~\cite{bai2025qwen3}, MedGemma-4B~\cite{sellergren2025medgemma}, GPT-5~\cite{openai2025gpt5systemcard}, and Gemini-2.5-Pro~\cite{comanici_gemini_2025}. Open-source VLMs are adapted with LoRA fine-tuning; GPT-5 and Gemini-2.5-Pro use prompt-only API inference. All models are trained with AdamW (lr $1e{-}4$, batch 12, 50 epochs) on 3$\times$48\,GB NVIDIA RTX A6000 GPUs.

\section{Results}
\label{sec:results}
\subsection{Main Results}
Segmentation performance is evaluated using Dice (\%) and HD95 (mm). Table~\ref{tab:table1_seg_blocks} compares ThyroidAgent against four methods: TransUNet~\cite{chen2024transunet}, MedSegX~\cite{zhang2025generalist}, MedSAM2~\cite{ma2025medsam2}, and UltraFedFM~\cite{jiang2025pretraining}. ThyroidAgent achieves the best Dice on 6 of 7 datasets and the best HD95 on all 7 datasets. On ZJH-8K, ThyroidAgent reaches 94.3\% Dice, outperforming the second-best (MedSAM2, 86.3\%) by 8.0 points. On PKTN, ThyroidAgent (83.0\%) slightly underperforms MedSAM2 (83.5\%), likely because PKTN's clip-based low-quality images produce mask predictions with lower inter-model variance, reducing the discriminative power of the feature-consistency-based judge.
\begin{table*}[b]
    \centering
    \caption{Cross-dataset generalization for benign-malignant thyroid nodule classification. AUROC and AUPRC are reported with 95\% confidence intervals. PKTN is excluded as it lacks malignancy labels.}
    \label{tab:table2_cls_blocks2}
    \scriptsize
    \setlength{\tabcolsep}{4pt}
    \renewcommand{\arraystretch}{1.15}
    \begin{tabular}{lccccc}
        \toprule
        \textbf{Method} & \textbf{TN3K} & \textbf{ThyroidXL} & \textbf{TN5K} & \textbf{DDTI} & \textbf{ZJH-8K} \\
        \midrule
        \multicolumn{6}{l}{\textit{AUROC $\uparrow$}} \\
        \midrule
        ResNet-50~\cite{he2016deep}
        & \makecell{0.767 \\ {\tiny [0.728, 0.807]}}
        & \makecell{0.904 \\ {\tiny [0.893, 0.916]}}
        & \makecell{0.932 \\ {\tiny [0.915, 0.949]}}
        & \makecell{0.670 \\ {\tiny [0.586, 0.755]}}
        & \makecell{0.670 \\ {\tiny [0.586, 0.755]}} \\
        RepViT~\cite{wang2023repvit}
        & \makecell{0.556 \\ {\tiny [0.509, 0.602]}}
        & \makecell{0.777 \\ {\tiny [0.759, 0.796]}}
        & \makecell{0.660 \\ {\tiny [0.623, 0.698]}}
        & \makecell{0.616 \\ {\tiny [0.536, 0.697]}}
        & \makecell{0.854 \\ {\tiny [0.835, 0.872]}} \\
        LSNet~\cite{wang2025lsnet}
        & \makecell{0.810 \\ {\tiny [0.776, 0.843]}}
        & \makecell{0.918 \\ {\tiny [0.906, 0.929]}}
        & \makecell{0.909 \\ {\tiny [0.889, 0.929]}}
        & \makecell{0.758 \\ {\tiny [0.692, 0.824]}}
        & \makecell{0.863 \\ {\tiny [0.843, 0.883]}} \\
        UltraFedFM~\cite{jiang2025pretraining}
        & \makecell{0.846 \\ {\tiny [0.776, 0.916]}}
        & \makecell{0.924 \\ {\tiny [0.914, 0.934]}}
        & \makecell{0.930 \\ {\tiny [0.912, 0.947]}}
        & \makecell{0.752 \\ {\tiny [0.581, 0.923]}}
        & \makecell{0.912 \\ {\tiny [0.898, 0.925]}} \\
        MedGemma~\cite{sellergren2025medgemma}
        & \makecell{0.849 \\ {\tiny [0.819, 0.880]}}
        & \makecell{0.937 \\ {\tiny [0.928, 0.947]}}
        & \makecell{0.944 \\ {\tiny [0.929, 0.960]}}
        & \makecell{\textbf{0.826} \\ {\tiny [0.761, 0.890]}}
        & \makecell{0.898 \\ {\tiny [0.881, 0.914]}} \\
        Qwen3-VL-8B~\cite{bai2025qwen3}
        & \makecell{0.824 \\ {\tiny [0.791, 0.856]}}
        & \makecell{0.905 \\ {\tiny [0.894, 0.917]}}
        & \makecell{0.921 \\ {\tiny [0.903, 0.940]}}
        & \makecell{0.736 \\ {\tiny [0.667, 0.805]}}
        & \makecell{0.866 \\ {\tiny [0.847, 0.885]}} \\
        GPT-5~\cite{openai2025gpt5systemcard}
        & \makecell{0.692 \\ {\tiny [0.650, 0.735]}}
        & \makecell{0.706 \\ {\tiny [0.659, 0.753]}}
        & \makecell{0.774 \\ {\tiny [0.674, 0.873]}}
        & \makecell{0.635 \\ {\tiny [0.543, 0.726]}}
        & \makecell{0.611 \\ {\tiny [0.559, 0.662]}} \\
        Gemini-2.5-Pro~\cite{comanici_gemini_2025}
        & \makecell{0.659 \\ {\tiny [0.613, 0.704]}}
        & \makecell{0.625 \\ {\tiny [0.561, 0.689]}}
        & \makecell{0.687 \\ {\tiny [0.618, 0.756]}}
        & \makecell{0.616 \\ {\tiny [0.485, 0.746]}}
        & \makecell{0.649 \\ {\tiny [0.598, 0.701]}} \\
        \rowcolor{lightgray}
        \textbf{ThyroidAgent}
        & \makecell{\textbf{0.869} \\ {\tiny [0.834, 0.904]}}
        & \makecell{\textbf{0.968} \\ {\tiny [0.961, 0.974]}}
        & \makecell{\textbf{0.947} \\ {\tiny [0.932, 0.963]}}
        & \makecell{0.799 \\ {\tiny [0.725, 0.873]}}
        & \makecell{\textbf{0.918} \\ {\tiny [0.901, 0.934]}} \\
        \midrule
        \multicolumn{6}{l}{\textit{AUPRC $\uparrow$}} \\
        \midrule
        ResNet-50~\cite{he2016deep}
        & \makecell{0.688 \\ {\tiny [0.625, 0.751]}}
        & \makecell{0.888 \\ {\tiny [0.871, 0.906]}}
        & \makecell{0.967 \\ {\tiny [0.941, 0.994]}}
        & \makecell{0.376 \\ {\tiny [0.258, 0.493]}}
        & \makecell{0.276 \\ {\tiny [0.159, 0.392]}} \\
        RepViT~\cite{wang2023repvit}
        & \makecell{0.428 \\ {\tiny [0.375, 0.480]}}
        & \makecell{0.716 \\ {\tiny [0.688, 0.744]}}
        & \makecell{0.840 \\ {\tiny [0.819, 0.862]}}
        & \makecell{0.392 \\ {\tiny [0.299, 0.486]}}
        & \makecell{0.949 \\ {\tiny [0.941, 0.956]}} \\
        LSNet~\cite{wang2025lsnet}
        & \makecell{0.758 \\ {\tiny [0.713, 0.803]}}
        & \makecell{0.904 \\ {\tiny [0.890, 0.918]}}
        & \makecell{0.955 \\ {\tiny [0.942, 0.968]}}
        & \makecell{0.418 \\ {\tiny [0.277, 0.559]}}
        & \makecell{0.945 \\ {\tiny [0.934, 0.956]}} \\
        UltraFedFM~\cite{jiang2025pretraining}
        & \makecell{0.853 \\ {\tiny [0.825, 0.881]}}
        & \makecell{0.935 \\ {\tiny [0.924, 0.947]}}
        & \makecell{0.842 \\ {\tiny [0.800, 0.884]}}
        & \makecell{0.449 \\ {\tiny [0.303, 0.594]}}
        & \makecell{0.967 \\ {\tiny [0.959, 0.975]}} \\
        MedGemma~\cite{sellergren2025medgemma}
        & \makecell{0.805 \\ {\tiny [0.762, 0.848]}}
        & \makecell{0.920 \\ {\tiny [0.906, 0.934]}}
        & \makecell{0.975 \\ {\tiny [0.966, 0.983]}}
        & \makecell{0.554 \\ {\tiny [0.387, 0.720]}}
        & \makecell{0.959 \\ {\tiny [0.949, 0.968]}} \\
        Qwen3-VL-8B~\cite{bai2025qwen3}
        & \makecell{0.762 \\ {\tiny [0.711, 0.813]}}
        & \makecell{0.879 \\ {\tiny [0.841, 0.917]}}
        & \makecell{0.964 \\ {\tiny [0.953, 0.974]}}
        & \makecell{0.411 \\ {\tiny [0.270, 0.553]}}
        & \makecell{0.950 \\ {\tiny [0.940, 0.959]}} \\
        GPT-5~\cite{openai2025gpt5systemcard}
        & \makecell{0.663 \\ {\tiny [0.599, 0.726]}}
        & \makecell{0.624 \\ {\tiny [0.557, 0.690]}}
        & \makecell{0.892 \\ {\tiny [0.860, 0.924]}}
        & \makecell{0.358 \\ {\tiny [0.249, 0.467]}}
        & \makecell{0.831 \\ {\tiny [0.793, 0.869]}} \\
        Gemini-2.5-Pro~\cite{comanici_gemini_2025}
        & \makecell{0.621 \\ {\tiny [0.562, 0.679]}}
        & \makecell{0.491 \\ {\tiny [0.407, 0.576]}}
        & \makecell{0.846 \\ {\tiny [0.802, 0.891]}}
        & \makecell{0.392 \\ {\tiny [0.240, 0.545]}}
        & \makecell{0.840 \\ {\tiny [0.804, 0.876]}} \\
        \rowcolor{lightgray}
        \textbf{ThyroidAgent}
        & \makecell{\textbf{0.855} \\ {\tiny [0.795, 0.914]}}
        & \makecell{\textbf{0.965} \\ {\tiny [0.958, 0.973]}}
        & \makecell{\textbf{0.975} \\ {\tiny [0.966, 0.984]}}
        & \makecell{\textbf{0.586} \\ {\tiny [0.448, 0.724]}}
        & \makecell{\textbf{0.971} \\ {\tiny [0.971, 0.972]}} \\
        \bottomrule
    \end{tabular}
\end{table*}
For malignancy classification, we evaluate AUROC and AUPRC. Table~\ref{tab:table2_cls_blocks2} compares ThyroidAgent with general-purpose classifiers (LSNet~\cite{wang2025lsnet}, RepViT~\cite{wang2023repvit}, ResNet50~\cite{he2016deep}), an ultrasound-specific model (UltraFedFM~\cite{jiang2025pretraining}), and vision-language models (Qwen3-VL-8B-Instruct~\cite{bai2025qwen3}, MedGemma-4B~\cite{sellergren2025medgemma}, GPT-5~\cite{openai2025gpt5systemcard}, Gemini-2.5-Pro~\cite{comanici_gemini_2025}). PKTN is excluded from classification evaluation as it lacks malignancy labels. ThyroidAgent achieves the best AUROC on 4 of 5 datasets and the best AUPRC on all 5 datasets. On ThyroidXL, ThyroidAgent reaches 0.968 AUROC, outperforming the second-best (MedGemma, 0.937) by 0.031. On DDTI, ThyroidAgent (0.799) underperforms MedGemma (0.826) in AUROC but surpasses it in AUPRC (0.586 vs 0.554), suggesting more stable precision-recall trade-offs on small, class-imbalanced datasets. GPT-5 and Gemini-2.5-Pro perform poorly across all datasets (mean AUROC 0.684 and 0.647, respectively), confirming that prompt-only inference without task-specific adaptation is insufficient for thyroid malignancy assessment.

\begin{figure}[t]
    \centering
    \includegraphics[width=\columnwidth]{figures/Fig3.pdf}
    \caption{Analysis of agentic aggregation.
    (a) Cls vote consistency distribution across models.
    (b) Distribution of Seg disagreement scores (Area-CV).
    (c) Cls performance across Seg Dice-score bins.}
    \label{fig:system_analysis}
\end{figure}

\subsection{Effectiveness of Dual-Path Cascade Routing}
\label{sec:effectiveness}
The rationale for using dual-path cascade routing is supported by the fact that multi-model outputs are not trivially redundant. Both segmentation and classification experts exhibit non-negligible disagreement across samples, as illustrated by the Area-CV distribution (median = 0.057, 90th percentile = 0.250) in Fig.~\ref{fig:system_analysis}(b) and the vote-consistency pie in Fig.~\ref{fig:system_analysis}(a). This indicates that no single model consistently performs across all images, which motivates the consensus-based path split and radiomics-judge-driven selection.

Fig.~\ref{fig:system_analysis}(c) further shows that ThyroidAgent outperforms heuristics such as selecting the most confident expert or majority voting, especially in the Dice-score range of [0.6, 0.8], where radiomics features improve contour and texture characterization. The performance gap narrows in the [0.8, 1.0] range as segmentation quality improves and expert predictions converge.

\begin{figure}[t]
    \centering
    \includegraphics[width=\columnwidth]{figures/Fig4.pdf}
    \caption{Interpretability analysis of classification and segmentation evidence.}
    \label{fig:interpretability_analysis}
\end{figure}

\subsection{Interpretability Analysis}
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
