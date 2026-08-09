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
\usepackage{adjustbox}
\usepackage[table,xcdraw]{xcolor}

\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}
\newcolumntype{Y}{>{\centering\arraybackslash}X}

% Title.
% ------
\title{Dual-Path Cascade Framework with GT-Trained Radiomics Judge for Thyroid Ultrasound Diagnosis}
%
\name{Author(s) Name(s)\thanks{Thanks to XYZ agency for funding.}}
\address{Author Affiliation(s)}

\begin{document}
%\ninept
%
\maketitle
%
\begin{abstract}
We propose ThyroidAgent, a cascade inference framework for thyroid nodule ultrasound diagnosis that coordinates segmentation and classification experts through dual-path routing driven by classification consensus and a GT-trained radiomics judge. Unlike static pipelines, ThyroidAgent runs heterogeneous experts in parallel and routes each case through a consensus shortcut or a dispute-resolution path based on whether independent classifiers agree. A radiomics classifier trained on ground-truth masks serves as a dual-purpose judge, evaluating segmentation quality via inter-model feature consistency while providing an independent malignancy signal that is incorporated as an additional weighted voter in the dispute-resolution path.
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
    \caption{Overview of the ThyroidAgent framework. While traditional systems use fixed pipelines, ThyroidAgent routes each case through a consensus shortcut or a dispute-resolution path, guided by a GT-trained radiomics judge that simultaneously assesses segmentation quality and provides an independent malignancy signal.}
    \label{fig:ThyroidAgent}
\end{figure}

Deep learning has substantially improved thyroid ultrasound analysis in both nodule segmentation~\cite{gong2021multi,dong2024ultrasound,haribabu2025mlrt} and malignancy classification~\cite{gong_acl_2022,sujini2025automated,das2024deep}. However, these tasks are typically developed and evaluated in isolation, leading to fixed pipelines that cannot jointly exploit segmentation-derived structural evidence and classification confidence. Prior attempts at task coupling—such as shared encoders with task-specific heads~\cite{he2023joint,rhanoui2025multi,wu2023multi}, ROI-based feature extraction~\cite{kang2022thyroid}, or thyroid-region priors~\cite{gong2021multi,gong_thyroid_2023}—offer limited cross-task interaction. Radiomics-assisted methods~\cite{park2021combining} and expert-routing medical VLMs~\cite{she2026echovlm,bai2025qwen3,sellergren2025medgemma} each address only part of the challenge: the former lack dynamic mask-quality control, while the latter, including EchoVLM~\cite{she2026echovlm}, build monolithic VLMs rather than case-level cascade coordination over external experts.

We propose \textit{ThyroidAgent}, a cascade inference framework that routes each case through a dual-path cascade driven by classification consensus and a GT-trained radiomics judge (Fig.~\ref{fig:ThyroidAgent}). When independent classifiers agree, a consensus shortcut uses their label as an anchor to guide segmentation selection; when they disagree, a dispute-resolution path invokes a radiomics classifier—trained on ground-truth masks—that simultaneously evaluates segmentation quality via inter-model feature consistency and provides an independent malignancy signal. The judge's prediction is then incorporated as an additional weighted voter alongside the independent classifiers, ensuring ROI-level radiomics evidence directly contributes to the final classification. Connected-component analysis (CCA) is available as an optional mask-refinement step for ensemble mode, independent of the routing policy.

The key contributions are:
\textbf{1. Dual-path cascade routing.} ThyroidAgent replaces static pipelines with dual-path routing driven by classification consensus, enabling case-level processing under heterogeneous acquisition conditions.
\textbf{2. GT-trained radiomics judge.} An AutoGluon classifier trained on GT-mask radiomics serves as a dual-purpose judge for segmentation quality assessment and independent malignancy prediction, driving pre-filtering, mask selection, and classification reconciliation.
\textbf{3. Unified benchmark.} We consolidate multiple datasets with aligned annotations, enabling systematic cross-dataset evaluation under heterogeneous acquisition conditions.

\begin{figure}[t]
    \centering
    \includegraphics[width=\columnwidth]{figures/Fig2.pdf}
    \caption{Detailed workflow of the ThyroidAgent system, showing the cascade inference process with parallel expert inference, classification-consensus-driven path splitting, GT-trained radiomics judging, and weighted-vote-based reconciliation.}
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

\subsubsection{GT-Trained Radiomics Judge}
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
\Ensure Final mask $\hat{M}$, label $\hat{y}$, confidence $\hat{p}$

\Statex \textbf{Phase 1--2: Parallel expert inference}
\State $\{M_k\}_{k=1}^{K} \gets \mathrm{RunSeg}(\mathcal{E}_{seg}, x)$
\State $\{p_m\}_{m=1}^{M} \gets \mathrm{RunCls}(\mathcal{E}_{cls}, x)$ \Comment{mask-free}

\Statex \textbf{Phase 3: Consensus check \& path split}
\State consensus $\gets \big[\arg\max_m p_m \text{ all equal}\big]$
\If{consensus}
  \State $a \gets$ consensus class \Comment{classification anchor}
  \State $\hat{k} \gets \mathrm{SegSelect}(\{M_k\}, g_\theta, a)$ \Comment{anchor-guided}
  \State $\hat{M} \gets M_{\hat{k}}$; $\hat{y} \gets a$
  \State \Return $\hat{M}, \hat{y}$ \Comment{Path A: shortcut}
\EndIf

\Statex \textbf{Phase 4: Pre-filter \& mask selection (Path B)}
\State $\{M_k\} \gets \mathrm{PreFilter}(\{M_k\}, g_\theta)$ \Comment{outlier removal}
\State $\hat{k} \gets \mathrm{SegSelect}(\{M_k\}, g_\theta, \mathrm{None})$
\State $\hat{M} \gets M_{\hat{k}}$

\Statex \textbf{Phase 5: Classification reconciliation}
\State $p_{\mathrm{rad}} \gets g_\theta\big(\phi(x, \hat{M})\big)$ \Comment{AutoGluon on selected mask}
\State $\hat{y} \gets \arg\max_{y} \big(\textstyle\sum_{m} w_m \, p_m(y) + w_{\mathrm{rad}} \, p_{\mathrm{rad}}(y)\big)$ \Comment{weighted vote}
\State \Return $\hat{M}, \hat{y}$
\end{algorithmic}
\end{algorithm}

In Algorithm~\ref{alg:thyroidagent_inference}, $\mathrm{PreFilter}(\cdot)$, $\mathrm{SegSelect}(\cdot)$, and the weighted voting policy are defined in Eq.~\eqref{eq:prefilter_cos}--\eqref{eq:reconcile}. Connected-component analysis (CCA)~\cite{liu2025shapekit} is available as an optional mask-refinement step for ensemble mode (when $K>1$ masks are combined); in the default single-selection mode ($K=1$), CCA is disabled.

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

\textbf{Segmentation selection.} The selector first applies an anchor-consistency filter (Path~A only): masks whose judge prediction strongly contradicts the classification anchor $a$ are excluded, i.e., removed when $c_{\mathrm{judge}}^{(k)} > 0.6$ and $|\hat{y}_{\mathrm{judge}}^{(k)} - a| > 0.4$. The surviving mask with the highest inter-model IoU agreement is then selected:
\begin{equation}
\hat{k} = \arg\max_{k} a_{\mathrm{agree}}^{(k)},
\label{eq:segsel}
\end{equation}
where $a_{\mathrm{agree}}^{(k)}$ is the average IoU between mask $k$ and all other candidates. If the filter removes all masks, the anchor constraint is relaxed and selection falls back to the full candidate set.

\textbf{Classification reconciliation.} Given the selected mask $\hat{M}$, the judge produces $p_{\mathrm{rad}} = g_\theta(\phi(x, \hat{M}))$. Rather than treating the judge as a separate arbitration signal, we incorporate it as an additional weighted voter alongside the $M$ independent classifiers:
\begin{equation}
\hat{y} = \arg\max_{y} \left( \sum_{m=1}^{M} w_m \, p_m(y) + w_{\mathrm{rad}} \, p_{\mathrm{rad}}(y) \right),
\label{eq:reconcile}
\end{equation}
where $w_m$ are the independent classifier weights (set to their validation AUROC) and $w_{\mathrm{rad}}$ is the judge weight (default $0.5$, reflecting its lower AUROC on hard samples). This design ensures the ROI-level radiomics signal directly contributes to the final decision, making Path~B complementary to Path~A's consensus shortcut.

\begin{table}[t]
    \centering
    \caption{Segmentation performance (Dice, \%) across 5 datasets.}
    \label{tab:table1_seg_blocks}
    \footnotesize
    \begin{tabular}{@{}l|ccccc@{}}
        \toprule
        \textbf{Method} & \textbf{TN3K} & \textbf{DDTI} & \textbf{ThyroidXL} & \textbf{PKTN} & \textbf{TN5K} \\
        \midrule
        TransUNet~\cite{chen2024transunet} & 81.84 & 76.58 & 85.75 & 76.89 & 78.54 \\
        MedSegX~\cite{zhang2025generalist} & 83.93 & 85.40 & 79.98 & 80.63 & 83.10 \\
        MedSAM2~\cite{ma2025medsam2} & 84.47 & 90.72 & 86.94 & \textbf{83.46} & 83.03 \\
        UltraFedFM~\cite{jiang2025pretraining} & 81.18 & 83.10 & 84.70 & 75.31 & 77.13 \\
        \midrule
        \rowcolor{lightgray}
        \textbf{ThyroidAgent} & \textbf{85.28} & \textbf{91.46} & \textbf{87.58} & 82.99 & \textbf{83.26}\\
        \bottomrule
    \end{tabular}
\end{table}

\section{Experiments}
\label{sec:experiment}
We evaluate on a consolidated thyroid ultrasound benchmark assembled from TN3K~\cite{gong2021multi}, TN5K~\cite{zhang2025tn5000}, DDTI~\cite{pedraza2015open}, ThyroidXL~\cite{duong2025thyroidxl}, and PKTN~\cite{sun2025clip}, spanning heterogeneous acquisition protocols and device settings. Patient-level 0.7/0.15/0.15 splits are used where applicable, and stacked training sets are formed by merging training portions across datasets (up to 26,074 images). Segmentation is evaluated with Dice (\%); classification with AUROC. Baselines include TransUNet~\cite{chen2024transunet}, MedSegX~\cite{zhang2025generalist}, MedSAM2~\cite{ma2025medsam2}, UltraFedFM~\cite{jiang2025pretraining}, MedSigLIP, BiomedCLIP, LSNet~\cite{wang2025lsnet}, RepViT~\cite{wang2023repvit}, ResNet50~\cite{he2016deep}, Qwen3-VL-8B-Instruct~\cite{bai2025qwen3}, MedGemma-4B~\cite{sellergren2025medgemma}, and GPT-5.1~\cite{openai2025gpt5systemcard}. Open-source VLMs are adapted with LoRA fine-tuning; GPT-5.1 uses prompt-only API inference. All models are trained with AdamW (lr $1e{-}4$, batch 12, 50 epochs) on 3$\times$48\,GB NVIDIA RTX A6000 GPUs.

\section{Results}
\label{sec:results}
\subsection{Main Results}
Segmentation performance is evaluated using Dice (\%). Table~\ref{tab:table1_seg_blocks} compares ThyroidAgent against three categories of methods: general-purpose segmenters (MedSegX~\cite{zhang2025generalist}, MedSAM2~\cite{ma2025medsam2}), a specialized ultrasound model (UltraFedFM~\cite{jiang2025pretraining}), and a recent advanced transformer-based approach (TransUNet~\cite{chen2024transunet}). ThyroidAgent achieves the best Dice on 4 of 5 datasets, with the largest gain on DDTI (+0.74 over MedSAM2, 91.46 vs 90.72). On PKTN, ThyroidAgent (82.99) slightly underperforms MedSAM2 (83.46), likely because PKTN's clip-based low-quality images produce mask predictions with lower inter-model variance, reducing the discriminative power of the feature-consistency-based judge.
\begin{table}[b]
    \centering
    \caption{Classification performance (AUROC) across 4 datasets.}
    \label{tab:table2_cls_blocks2}
    \footnotesize
    \begin{tabular}{@{}l|cccc@{}}
        \toprule
        \textbf{Method} & \textbf{TN3K} & \textbf{DDTI} & \textbf{ThyroidXL} & \textbf{TN5K} \\
        \midrule
        MedSigLIP & 0.831 & 0.798 & 0.924 & 0.941 \\
        BiomedCLIP & 0.798 & 0.762 & 0.905 & 0.928 \\
        ResNet-50~\cite{he2016deep} & 0.767 & 0.670 & 0.904 & 0.932 \\
        RepViT~\cite{wang2023repvit} & 0.556 & 0.616 & 0.777 & 0.660 \\
        LSNet~\cite{wang2025lsnet} & 0.810 & 0.758 & 0.918 & 0.909 \\
        UltraFedFM~\cite{jiang2025pretraining} & 0.846 & 0.752 & 0.924 & 0.930 \\
        MedGemma~\cite{sellergren2025medgemma} & 0.849 & 0.826 & 0.937 & 0.944 \\
        Qwen3-VL-8B~\cite{bai2025qwen3} & 0.824 & 0.736 & 0.905 & 0.921 \\
        GPT-5.1~\cite{openai2025gpt5systemcard} & 0.692 & 0.635 & 0.706 & 0.774 \\
        \midrule
        \rowcolor{lightgray}
        \textbf{ThyroidAgent} & \textbf{0.869} & 0.799 & \textbf{0.968} & \textbf{0.947}\\
        \bottomrule
    \end{tabular}
\end{table}
For malignancy classification, we evaluate AUROC. Table~\ref{tab:table2_cls_blocks2} compares ThyroidAgent with four categories of methods: medical vision-language models (MedSigLIP, BiomedCLIP), ultrasound-specific models (UltraFedFM~\cite{jiang2025pretraining}), general-purpose classifiers (LSNet~\cite{wang2025lsnet}, RepViT~\cite{wang2023repvit}, ResNet50~\cite{he2016deep}), and vision-language models (Qwen3-VL-8B-Instruct~\cite{bai2025qwen3}, MedGemma-4B~\cite{sellergren2025medgemma}, GPT-5.1~\cite{openai2025gpt5systemcard}). ThyroidAgent achieves the best AUROC on 3 of 4 datasets, with the largest gain on ThyroidXL (+0.031 over MedGemma, 0.968 vs 0.937). On DDTI, ThyroidAgent (0.799) underperforms MedGemma (0.826), possibly because DDTI's smaller training set limits the diversity of the expert pool. GPT-5.1 performs poorly across all datasets (mean AUROC 0.702), confirming that prompt-only inference without task-specific adaptation is insufficient for thyroid malignancy assessment.

\begin{figure}[t]
    \centering
    \includegraphics[width=\columnwidth]{figures/Fig3.pdf}
    \caption{Analysis of dual-path cascade routing.
    (a) Path A/B distribution and consensus ratio across datasets.
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
    \caption{Interpretability analysis of the GT-trained radiomics judge: (a) global SHAP feature importance, (b) case-level SHAP waterfall for a malignancy prediction, (c) segmentation mask comparison with judge confidence.}
    \label{fig:interpretability_analysis}
\end{figure}

\subsection{Interpretability Analysis}
Fig.~\ref{fig:interpretability_analysis}(a) shows the global SHAP feature importance of the radiomics judge. Shape descriptors dominate the prediction: \emph{Sphericity} and \emph{Elongation} are the top-2 contributors, followed by \emph{Perimeter}, \emph{LRHGLE}, and \emph{SRLGLE}, confirming that malignancy cues are primarily morphological rather than textural. Fig.~\ref{fig:interpretability_analysis}(b) decomposes a single malignant prediction into feature-level contributions, showing how these descriptors collectively shift the base value to the final decision. Fig.~\ref{fig:interpretability_analysis}(c) compares selected masks with ground truth across cases with varying judge confidence, demonstrating that the judge assigns higher confidence to masks whose radiomics features stay consistent with the consensus of plausible predictions.

\section{Conclusion}
\label{sec:conclusion}
We proposed ThyroidAgent, a cascade inference framework for thyroid ultrasound diagnosis that routes each case through a consensus shortcut or a dispute-resolution path guided by a GT-trained radiomics judge. By coupling classification consensus with segmentation selection and using a GT-trained radiomics classifier as a dual-purpose judge, ThyroidAgent improves robustness, interpretability, and generalization across heterogeneous datasets. Future work will explore prospective validation and additional modalities for clinical deployment.

% References should be produced using the bibtex program from suitable
% BiBTeX files (here: strings, refs, manuals). The IEEEbib.bst bibliography
% style file from IEEE produces unsorted bibliography list.
% -------------------------------------------------------------------------
\bibliographystyle{IEEEbib}
\bibliography{ref}

\end{document}
