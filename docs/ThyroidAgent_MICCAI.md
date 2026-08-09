% This is samplepaper.tex, a sample chapter demonstrating the
% LLNCS macro package for Springer Computer Science proceedings;
% Version 2.21 of 2022/01/12
%
\documentclass[runningheads]{llncs}
%
\usepackage[T1]{fontenc}
% T1 fonts will be used to generate the final print and online PDFs,
% so please use T1 fonts in your manuscript whenever possible.
% Other font encodings may result in incorrect characters.
%
\usepackage{graphicx,verbatim}
\usepackage{amsmath}
\usepackage{amsfonts}
\usepackage{algorithm}
\usepackage{algpseudocode}
\usepackage{multirow}
\usepackage{adjustbox}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{hyperref}
\usepackage{subcaption}
\usepackage{overpic}    % 核心：叠加标签到图片
\usepackage{graphicx}   % 加载图片（通常已加载）
\usepackage{caption}    % 图片标题（通常已加载）


\usepackage[table,xcdraw]{xcolor}
%\usepackage[section]{placeins}
\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}
\newcolumntype{Y}{>{\centering\arraybackslash}X} % 居中 X 列
% T1 fonts will be used to generate the final print and online PDFs,
% so please use T1 fonts in your manuscript whenever possible.
% Other font encondings may result in incorrect characters.
%
% Used for displaying a sample figure. If possible, figure files should
% be included in EPS format.
%
% If you use the hyperref package, please uncomment the following two lines
% to display URLs in blue roman font according to Springer's eBook style:
%\usepackage{color}
%\renewcommand\UrlFont{\color{blue}\rmfamily}
%\urlstyle{rm}
%

\begin{document}
%
% \title{Interpretable Thyroid Nodule Classification through Clinical Index Synthesis Based on Multi-Task Learning}
\title{Explainable Agent-Based Framework for Thyroid Ultrasound Diagnosis}
%
%\titlerunning{Abbreviated paper title}
% If the paper title is too long for the running head, you can set
% an abbreviated paper title here
%
\author{Anonymized Authors}  %% Added for anonymized MICCAI submission
\authorrunning{Anonymized Author et al.}
\institute{Anonymized Affiliations \\
    \email{email@anonymized.com}}
  
% \author{ID 1334}
% \institute{}
%
% \authorrunning{F. Author et al.}
% First names are abbreviated in the running head.
% If there are more than two authors, 'et al.' is used.
%
% \institute{Princeton University, Princeton NJ 08544, USA \and
% Springer Heidelberg, Tiergartenstr. 17, 69121 Heidelberg, Germany
% \email{lncs@springer.com}\\
% \url{http://www.springer.com/gp/computer-science/lncs} \and
% ABC Institute, Rupert-Karls-University Heidelberg, Heidelberg, Germany\\
% \email{\{abc,lncs\}@uni-heidelberg.de}}
%
\maketitle              % typeset the header of the contribution
%

\begin{abstract}
We propose ThyroidAgent, an agent-based framework for thyroid nodule ultrasound segmentation and classification. Unlike conventional approaches that rely on static pipelines, ThyroidAgent introduces a dynamic, policy-driven inference process, selecting model experts based on ultrasound image data and device context. By integrating segmentation and classification tasks, the framework enhances classification through segmentation-derived features. This multi-task workflow improves interpretability, robustness, and adaptability across diverse ultrasound conditions. 
% Additionally, we create a publicly available thyroid ultrasound dataset for joint segmentation and classification, exploring the impact of open-source data on model generalization. 
% 删除关于开源的描述
Additionally, we curate a consolidated multi-source benchmark with aligned segmentation and classification annotations, enabling systematic cross-dataset evaluation and analysis of data factors that affect generalization.
Experimental results show that ThyroidAgent outperforms static models, demonstrating its potential for more reliable, context-aware clinical deployment.

\keywords{Ultrasound \and Thyroid Nodule \and Segmentation \and Malignancy Classification \and Agentic AI}
\end{abstract}

\section{Introduction}
\begin{figure}[htbp]
    \centering
    \includegraphics[width=1.0\linewidth]{figures/ThyroidAgent.pdf}
    \caption{Overview of the ThyroidAgent framework. While traditional systems use fixed pipelines, ThyroidAgent dynamically selects expert models based on ultrasound images and metadata, integrating segmentation and classification for improved adaptability and robustness.}
    \label{fig:ThyroidAgent}
\end{figure}

% 添加了参考文献
Recent advances in deep learning have greatly improved automated thyroid ultrasound analysis, with substantial progress in both nodule segmentation and malignancy classification~\cite{das2024deep}. For segmentation, prior methods have explored CNN and transformer-based designs to improve boundary delineation and robustness in noisy ultrasound images~\cite{gong2021multi,dong2024ultrasound,haribabu2025mlrt}, while recent classification models have improved malignancy prediction under data imbalance and imaging variability~\cite{gong_acl_2022,sujini2025automated}. 
Nevertheless, these methods are typically developed and evaluated as separate components, leading to fixed task-specific pipelines. 
%Such a design limits the ability to jointly exploit segmentation-derived structural evidence and classification confidence, which is important for reliable thyroid ultrasound diagnosis in real-world settings.
% 修改当前及后续内容中一行内容很少的情况
This design limits the joint use of segmentation-derived structural evidence and classification confidence, which is crucial for reliable thyroid ultrasound diagnosis. %in real-world settings.


%Recent years have seen growing efforts to integrate segmentation and classification within a unified framework. 
% 承接上一段单任务框架的问题
% To address the limitations of task-specific pipelines, recent studies have integrated segmentation and classification into a unified framework. Several approaches use segmentation masks as Regions of Interest (ROIs) for feature extraction, enhancing classification by leveraging segmentation-derived structural evidence within multi-task learning settings \cite{kang2022thyroid,gong2021multi,gong_thyroid_2023}.
To address the limitations of task-specific pipelines, several studies have explored unified or multi-task formulations that couple nodule segmentation with malignancy classification~\cite{kang2022thyroid}. In parallel, thyroid-region priors have been incorporated via multi-task designs to improve nodule delineation under noisy ultrasound conditions~\cite{gong2021multi,gong_thyroid_2023}.
%However, these methods often focus primarily on simple concatenation of segmented regions to aid classification, without fully exploiting the potential of multi-task learning or utilizing complementary features for improved performance. 
%While these approaches have shown some success, they still rely heavily on fixed segmentation models that do not adapt dynamically to changing clinical scenarios. However, using segmentation masks as ROI inputs or concatenating segmentation outputs with classification models fails to fully leverage multi‑task learning, as these methods typically rely on shallow feature sharing, preventing effective optimization of both tasks \cite{he2023joint,rhanoui2025multi,wu2023multi}. More sophisticated mechanisms are needed to fully exploit task correlations and optimize cross-task feature interactions.
% 加入引用文献，增强说服力
Collectively, these efforts suggest that exploiting task relatedness can improve robustness and provide more interpretable ultrasound analysis.
However, many existing formulations adopt relatively simple task coupling (e.g., ROI-based feature extraction, output concatenation, or shared encoders with task-specific heads), which may yield limited cross-task interaction and hinder effective joint optimization~\cite{he2023joint,rhanoui2025multi,wu2023multi}.
More advanced mechanisms are needed to fully leverage task correlations and optimize feature interactions.

In this work, we propose \textit{ThyroidAgent}, an agent-based multi-task framework for thyroid ultrasound diagnosis that departs from conventional static pipelines by replacing fixed execution with context-aware expert orchestration (Fig.~\ref{fig:ThyroidAgent}). 
Instead of treating segmentation as an ROI-localization module, ThyroidAgent couples the predicted mask with the original ultrasound image to extract mask-guided radiomics descriptors, turning pixel-level delineations into interpretable morphology and texture evidence for improved malignancy classification.

Motivated by the recent progress of large language models (LLMs)~\cite{dong_survey_2022} in reasoning and decision support, we explore their use in thyroid ultrasound diagnosis as an evidence-aware decision module~\cite{bai2025qwen3,sellergren2025medgemma}. 
%Rather than replacing task-specific predictors, the LLM module receives structured evidence from multiple trained experts (e.g., predictions, confidence signals, segmentation-derived radiomics evidence, and contextual metadata) and performs sample-specific expert selection while producing interpretable decision rationales. Together, these designs establish a unified and adaptive framework that explicitly bridges segmentation, classification, and explainable evidence aggregation for thyroid ultrasound CAD.
The LLM module receives structured evidence from multiple trained experts and performs sample-specific expert selection while producing interpretable decision rationales. These designs establish a unified and adaptive framework that explicitly bridges segmentation, classification, and explainable evidence aggregation for thyroid ultrasound CAD.

The key contributions of our method are summarized as below:
\textbf{1. Dynamic agent-driven CAD paradigm.} 
    We propose \emph{ThyroidAgent}, a dynamic CAD framework that replaces the traditional static pipeline with an agent capable of reasoning over multimodal context metadata and adaptively selecting among segmentation and classification experts, enabling flexible and task-aware processing.
\textbf{2. Radiomics-augmented agent reasoning.} 
    We integrate radiomics and CCA-based feature toolkits into the agent loop, allowing the agent to exploit segmentation masks to extract quantitative descriptors and fuse them with model confidence signals, thereby improving decision reliability, interpretability, and expert-selection quality.
\textbf{3. Unified dataset consolidation and generalization analysis.} 
    %We construct a consolidated open-source thyroid ultrasound dataset with aligned segmentation and classification annotations, supporting cross-dataset evaluation. We further analyze how data factors influence generalization within the dynamic agent setting.
    We curate a consolidated benchmark by harmonizing segmentation and classification annotations across multiple datasets, enabling cross-dataset evaluation and analysis of data factors affecting generalization in the dynamic agent setting.


% 将图片格式改为pdf，小图标全部改为svg格式
\begin{figure}[htbp]
    \centering
    \includegraphics[width=1.0\linewidth]{figures/WorkFlow.pdf}
    \caption{Detailed workflow of the ThyroidAgent system, showing training and inference processes, including dynamic model selection, expert integration, and evidence-driven decision-making based on ultrasound images and metadata.}
    \label{fig:WorkFlow}
\end{figure}

\section{Method}
% 引用Fig2
Fig.~\ref{fig:WorkFlow} illustrates the ThyroidAgent framework, which consists of training and inference stages. During inference, the agent dynamically selects the most appropriate expert output based on contextual information and evidence signals, replacing static pipelines.
% 动机：动态选择单个简单模型的方式比训练一个复杂模型的性能更稳健；近两年来llm在多个领域得到广泛应用，利用llm的动态选择能力，同时也探索llm如何应用在甲状腺超声图像诊断领域
The agent-based framework overcomes the limitations of relying on a single complex model by dynamically selecting from multiple simpler expert models, improving flexibility and generalization across diverse datasets. Motivated by the recent advancements in large language models (LLMs), which excel in dynamic decision-making, we integrate their reasoning capabilities to perform expert selection and aggregation based on structured evidence. This dynamic orchestration allows ThyroidAgent to adapt to varying clinical scenarios and enhance decision-making in thyroid ultrasound diagnosis.

\subsection{Toolbox for Ultrasound Analysis}
%We define thyroid ultrasound analysis as a set of callable tools with standardized inputs and outputs, allowing the agent to compare expert models based on consistent evidence signals for reproducible results. The toolbox is designed to facilitate expert selection and enhance the accuracy of predictions through complementary components. 
We define thyroid ultrasound analysis as a collection of tools with standardized inputs and outputs, enabling the agent to compare expert models based on consistent evidence for reproducible results. The toolbox facilitates expert selection and improves prediction accuracy through complementary components.
% It includes: (i) a deep expert family for segmentation and classification, based on DINOv3 with varying training conditions, (ii) a radiomics tool for extracting complementary morphology and texture features, and (iii) reinforcement learning for optimizing connected component analysis (CCA) hyperparameters to refine segmentation mask quality.

\subsubsection{DINOv3-Based Expert Models}
\label{sec:dinov3_models}
Our models share a DINOv3-based backbone with task-specific lightweight heads~\cite{simeoni2025dinov3}. 
For segmentation, we adopt a U-Net-style decoder with skip fusion to output a dense nodule mask probability map, optimized by a weighted BCE+IoU loss $\mathcal{L}_{\mathrm{seg}}$. 
%For classification, the backbone features are summarized by global average/max pooling and passed to a compact attention-based classification head to produce malignancy probabilities. 
% 添加两个任务的损失函数说明
For classification, backbone features are summarized by global average and max pooling and fed into a compact attention-based head to output, trained with a GLA loss to alleviate class imbalance. 
The core weighting and logit adjustment used by $\mathcal{L}_{\mathrm{seg}}$ and GLA are:
\begin{equation}
\begin{aligned}
w &= 1 + 5 \cdot \left| \operatorname{AvgPool}_{31}(y) - y \right|,\\
z'_b &= z_b + \tau \left( y_b \log p_{\text{pos}} + (1-y_b)\log p_{\text{neg}} \right),
\end{aligned}
\label{eq:losses}
\end{equation}
where $\mathcal{L}_{\mathrm{bm}}$ is BCE-with-logits computed on the adjusted logits $z'_b$.

%Rather than designing increasingly complex single models, we construct a diverse expert pool to improve robustness under cross-dataset variability. 
% 引用databias论文，写明动机
In recent years, the issue of dataset bias has remained a critical challenge in the development of reliable machine learning models~\cite{torralba2011unbiased}. 
Despite the increasing diversity and scale of modern datasets, recent studies show that neural networks can still easily capture dataset-specific biases, which may hinder generalization across diverse real-world conditions~\cite{liu2024decade}. 
Motivated by these findings, our design adopts an agent-based paradigm to replace static pipelines with dynamic expert orchestration.
Specifically, the agent leverages ultrasound images together with contextual metadata to adaptively select or aggregate the most suitable segmentation and classification experts on a per-sample basis. This architecture is intended to explicitly mitigate cross-dataset and cross-device bias by avoiding reliance on a single fixed model whose behavior may be overly coupled to training data idiosyncrasies. 
As validated in Sec.~\ref{sec:effectiveness}, dynamic expert selection offers a practical and more stable, interpretable alternative to a single fixed model, improving robustness and generalization under heterogeneous clinical acquisition conditions via context-aware decision-making.

% Specifically, we train multiple models on stacked datasets with different input resolutions and dilation settings, and then use the agent to select or aggregate the most suitable expert model output for each case based on evidence signals.  
% This design is empirically validated in Sec.~\ref{sec:effectiveness} to provide more stable and interpretable performance than relying on a single fixed model to generalize across all imaging conditions.

\subsubsection{Radiomics Tool for Feature Extraction}
%Radiomics extracts interpretable features from an image and an ROI mask to complement deep learning predictions. We adopt a 2D PyRadiomics setup, enabling standard feature families such as shape2D and texture, consistent with our observation that morphology and texture features are dominant in predicting outcomes. We report representative formulations for these families:
Radiomics extracts interpretable features from images and ROI masks to complement deep learning predictions. Using a 2D PyRadiomics setup, we focus on feature families such as shape2D, which are dominant in predicting outcomes. Representative formulations include:
\begin{equation}
\begin{aligned}
A = \sum_{x=1}^{H} \sum_{y=1}^{W} \mathbb{I} \left[ M(x,y) = 1 \right], \\
\mathrm{Energy} = \sum_{i=1}^{N_g} \sum_{j=1}^{N_g} P(i,j)^2,
\end{aligned}
\end{equation}
%where $A$ denotes the ROI area, $M(x,y) \in {0,1}$ is the binary ROI mask, $\mathbb{I}[\cdot]$ is the indicator function, $H \times W$ is the mask resolution, $\mathrm{Energy}$ is the GLCM energy, $P(i,j)$ is the normalized gray-level co-occurrence matrix, and $N_g$ is the number of discretized gray levels.
where $A$ is the ROI area, $M(x,y) \in \{0,1\}$ is the binary ROI mask, $\mathrm{Energy}$ is the GLCM energy and $P(i,j)$ is the normalized gray-level co-occurrence matrix.

\subsubsection{RL for Connected Component Analysis}
We use reinforcement learning to optimize the hyperparameters of connected component analysis (CCA) applied to segmentation masks~\cite{liu2025shapekit}. 
%The agent, trained using the PPO algorithm, interacts with the segmentation outputs to adjust key CCA parameters, such as the number of connected components and the connectivity threshold, in order to improve the quality of the final masks.
% 添加ppo算法的参考文献
The agent is trained with Proximal Policy Optimization (PPO)~\cite{schulman2017proximal}, a stable on-policy method that updates the policy via a clipped objective, to adjust the number of connected components and the connectivity threshold in CCA and improve the final mask quality.


\begin{algorithm}[t]
\caption{ThyroidAgent inference process}
\label{alg:thyroidagent_inference}
\begin{algorithmic}[1]
\Require Image $x$, optional context $c$; expert pools $\mathcal{E}_{seg},\mathcal{E}_{cls}$; metadata registry $\mathcal{R}$
\Ensure Final mask $\hat{M}$, label $\hat{y}$ with confidence $\hat{p}$, decision log $\mathcal{L}$

\State $x' \gets \mathrm{Preprocess}(x)$; $\mathcal{L}\gets\emptyset$
\State $\{M_k,s_k\}_{k=1}^{K} \gets \mathrm{RunSeg}(\mathcal{E}_{seg},x',\mathcal{R})$ 
\State $E_{seg}\gets \mathrm{SegEvidence}(\{M_k,s_k\},c,\mathcal{R})$ 
\State $\hat{k}\gets \mathrm{PolicySelect}(E_{seg})$; $\hat{M}\gets M_{\hat{k}}$; $\mathcal{L}\gets\mathcal{L}\cup\{\hat{k},E_{seg}\}$
\State $r\gets \mathrm{PyRadiomics2D}(x',\hat{M})$ 
\State $\{p_m,\gamma_m\}_{m=1}^{M} \gets \mathrm{RunCls}(\mathcal{E}_{cls},x',\mathcal{R})$ 
\State $E_{cls}\gets \mathrm{ClsEvidence}(\{p_m,\gamma_m\},r,c,\mathcal{R})$ 
\State $\hat{m}\gets \mathrm{PolicySelect}(E_{cls})$; $\hat{y} \gets \mathbb{I}[p_{\hat{m}}\ge 0.5]$; $\hat{p}\gets p_{\hat{m}}$
\State $\mathcal{L}\gets\mathcal{L}\cup\{\hat{m},E_{cls}\}$; \Return $\hat{M},\hat{y},\hat{p},\mathcal{L}$
\end{algorithmic}
\end{algorithm}

% 把对图和算法的引用提到前面，在Method开始已经引用了Fig2，这里结合算法1，再简单介绍一下
\subsection{Agentic Inference Workflow}
%Fig.~\ref{fig:WorkFlow} summarizes ThyroidAgent as a policy-driven workflow with offline expert construction and online inference. In the offline stage, multiple segmentation and classification experts are trained from stacked datasets and organized into an experts zoo with a metadata registry. 
%In the online stage, a test ultrasound image is processed by multiple candidate experts, whose outputs are summarized as compact evidence signals and passed to ThyroidAgent for a strict JSON decision that drives expert selection or aggregation and final prediction. 
%As formalized in Algorithm~\ref{alg:thyroidagent_inference}, the process proceeds from segmentation-side candidate generation and evidence-based mask selection, to mask-guided radiomics extraction, and then to classification-side evidence construction and policy selection using expert predictions, radiomics evidence, context, and metadata, thereby replacing a single static forward pass with evidence-aware orchestration across experts.
Fig.~\ref{fig:WorkFlow} overviews ThyroidAgent as a policy-driven pipeline with expert construction and agentic inference. 
Multiple segmentation and classification experts are trained on stacked datasets and organized into an expert pool with a metadata registry that records imaging device provenance of the training data, validation performance, training-set scale, and input resolution.
As illustrated in Fig.~\ref{fig:WorkFlow} and Algorithm~\ref{alg:thyroidagent_inference}, during inference we execute candidate experts and summarize their predictions into compact evidence signals, together with context and metadata cues. 
ThyroidAgent then outputs a strict JSON decision to select or aggregate experts, producing the final mask and label. This workflow replaces a single fixed forward pass with evidence-aware orchestration across experts.

% 删除paper的最好结果
\begin{table*}[htbp]
    \begin{center}
    \caption{Performance comparison of segmentation models across 5 datasets.}
    \label{tab:table1_seg_blocks}
    \begin{tabular}{c|cc|cc|cc|cc|cc}
        \toprule
        \multirow{2}{*}{\textbf{Method}} & 
        \multicolumn{2}{c|}{\textbf{TN3K}} &
        \multicolumn{2}{c|}{\textbf{DDTI}} &
        \multicolumn{2}{c|}{\textbf{ThyroidXL}} &
        \multicolumn{2}{c|}{\textbf{PKTN}} &
        \multicolumn{2}{c}{\textbf{TN5K}}
        \\
        & Dice & HD95 & Dice & HD95 & Dice & HD95 & Dice & HD95 & Dice & HD95\\
        \midrule
        % 切换transunet的引用为mia的版本
        TransUnet~\cite{chen2024transunet} & 81.84 & 14.92 & 74.43 & 24.37 & 85.75 & 27.42  & 76.89 & 36.88  & 78.54 & 32.32 \\
        MedSegX~\cite{zhang2025generalist}          & 29.13 & 121.66 & 35.53 & 99.49 & 18.63 & 131.61 & 22.42 & 121.85 & 12.04 & 137.20\\
        MedSAM2~\cite{ma2025medsam2}          & 28.93 & 102.49 & 36.33 & 76.89 & 15.10 & 97.65 & 19.32 & 107.65 & 12.81 & 112.81 \\
        UltraFedFM~\cite{jiang2025pretraining}     & 83.32 & 13.63 & 82.93 & 12.83 & 67.47 & 28.05 & 58.31 & 37.36 & 56.16 & 35.32 \\
        \rowcolor{lightgray} % 设置背景色为浅灰色
        \textbf{ThyAgent-Seg} & \textbf{85.28} & \textbf{10.31} & \textbf{85.16} & \textbf{9.44} & \textbf{87.58} & \textbf{5.43} & \textbf{82.96} & \textbf{9.01} & \textbf{83.26} & \textbf{10.94}\\
        \bottomrule
    \end{tabular}
  \end{center}
\end{table*}

\section{Experiment}
\subsection{Experimental Details}
% 增加实验细节：数据集的规模、划分比例、训练的专家的个数
We evaluate on a consolidated thyroid ultrasound benchmark assembled from multiple sources, including TN3K~\cite{gong2021multi}, TN5K~\cite{zhang2025tn5000}, DDTI~\cite{pedraza2015open}, ThyroidXL~\cite{duong2025thyroidxl}, and PKTN~\cite{sun2025clip}, spanning heterogeneous acquisition protocols and device settings. The segmentation task predicts a binary nodule mask, and the classification task predicts benign or malignant labels. 
All splits are performed at the patient level to avoid leakage, using a 0.7/0.15/0.15 split protocol where applicable. 
We then construct stacked training sets by merging the training portions across datasets, the largest stacked set contains 26,074 images.
To build a diverse expert pool, we train 12 experts for each task by varying the stacked training set, dilation design, and input resolution (128, 224, and 448). 
The downstream agent then selects from these expert outputs during inference. All models are trained with PyTorch (v2.4.1) under a shared protocol (AdamW, learning rate $1e-4$, batch size 12, 50 epochs) on 3$\times$48\,GB NVIDIA RTX A6000 GPUs.

\subsection{Main Experimental Results: Segmentation and Classification}
%Segmentation performance is evaluated using Dice (\%, overlap between predicted and ground-truth masks) and HD95 (95th percentile of the Hausdorff distance). We compare our ThyAgent-Seg (Sec.~\ref{sec:dinov3_models}) against several baselines: (i) the transformer-based TransUNet \cite{chen2024transunet}, (ii) the ultrasound-specific baseline UltraFedFM \cite{jiang2025pretraining}, and (iii) general-purpose segmenters, including MedSegX \cite{zhang2025generalist} and MedSAM2 \cite{ma2025medsam2}.
% 不使用(i)(ii)这种形式，太占空间
Segmentation performance is evaluated using Dice (\%) and HD95. We compare ThyAgent-Seg against three categories of methods: general-purpose segmenters (MedSegX~\cite{zhang2025generalist}, MedSAM2~\cite{ma2025medsam2}), a specialized ultrasound model (UltraFedFM~\cite{jiang2025pretraining}), and a recent advanced transformer-based approach (TransUNet~\cite{chen2024transunet}).
\begin{table*}[!htp]
    \begin{center}
    \caption{Performance comparison of classification models across 4 datasets.}
    \label{tab:table2_cls_blocks2}
    \begin{tabular}{c|cc|cc|cc|cc}
        \toprule
        \multirow{2}{*}{\textbf{Method}} & 
        \multicolumn{2}{c|}{\textbf{TN3K}} &
        \multicolumn{2}{c|}{\textbf{DDTI}} &
        \multicolumn{2}{c|}{\textbf{ThyroidXL}} &
        \multicolumn{2}{c}{\textbf{TN5K}}
        \\
        & {\scriptsize AUROC} & {\scriptsize AUPRC} & {\scriptsize AUROC} & {\scriptsize AUPRC}
        & {\scriptsize AUROC} & {\scriptsize AUPRC} & {\scriptsize AUROC} & {\scriptsize AUPRC} \\
        \midrule
        ResNet-50~\cite{he2016deep}   & 0.767 & 0.687 & 0.674 & 0.248 & 0.904 & 0.888 & 0.932 & 0.967 \\
        RepViT~\cite{wang2023repvit}   & 0.514 & 0.380 & 0.640 & 0.183 & 0.561 & 0.511 & 0.375 & 0.665 \\
        LSNet~\cite{wang2025lsnet}   & 0.789 & 0.758 & 0.775 & 0.318 & 0.917 & 0.904 & 0.909 & 0.955 \\
        UltraFedFM~\cite{jiang2025pretraining} & 0.765 & \textbf{0.813} & 0.675 & \textbf{0.741} & 0.825 & 0.852 & 0.827 & 0.761 \\
        MedGemma~\cite{sellergren2025medgemma}  & 0.442 & 0.419 & 0.485 & 0.122 & 0.442 & 0.419 & 0.524 & 0.765 \\
        Qwen3-vl-8B~\cite{bai2025qwen3}  & 0.452 & 0.363 & 0.608 & 0.254 & 0.497 & 0.456 & 0.673 & 0.828 \\
        % 引用gpt5的system card
        GPT-5.1~\cite{openai2025gpt5systemcard}      & 0.640 & 0.487 & 0.705 & 0.330 & 0.599 & 0.472 & 0.673 & 0.843 \\
        \rowcolor{lightgray} % 设置背景色为浅灰色
        \textbf{ThyAgent-Cls} & \textbf{0.794} & 0.730 & \textbf{0.809}& 0.542 & \textbf{0.931} & \textbf{0.909} & \textbf{0.961} & \textbf{0.985}\\
        \bottomrule
    \end{tabular}
  \end{center}
\end{table*}
% 增加对几个VLM的prompt的描述
%For malignancy classification, we evaluate AUROC (Area Under the Receiver Operating Characteristic Curve) and AUPRC (Area Under the Precision-Recall Curve), comparing our ThyAgent-Cls (Sec.~\ref{sec:dinov3_models}) with several competitive models: (i) ResNet50 \cite{he2016deep}, RepViT \cite{\cite{wang2023repvit}} and LSNet \cite{\cite{wang2025lsnet}} a widely used baseline in medical image classification, (ii) UltraFedFM \cite{jiang2025pretraining}, and (iii) vision-language models (VLMs), including Qwen3-VL-8B \cite{bai2025qwen3}, MedGemma-4B \cite{sellergren2025medgemma}, and GPT-5.1\cite{openai2025gpt5systemcard}. 
%For fair comparison, all VLMs are evaluated with the same prompt template, using a unified binary malignancy-classification instruction and a constrained single-character output format (0 for benign, 1 for malignant).
For malignancy classification, we evaluate AUROC and AUPRC, comparing ThyAgent-Cls with three categories of methods: ultrasound-specific models (UltraFedFM~\cite{jiang2025pretraining}), general-purpose classifiers (LSNet~\cite{wang2025lsnet}, RepViT~\cite{wang2023repvit}, ResNet50~\cite{he2016deep}), and vision-language models (Qwen3-VL-8B~\cite{bai2025qwen3}, MedGemma-4B~\cite{sellergren2025medgemma}, GPT-5.1~\cite{openai2025gpt5systemcard}). 
All VLMs are evaluated using a unified binary malignancy-classification prompt with a single-character output format. 
Across datasets, both ThyAgent-Seg and ThyAgent-Cls achieve best or near-best performance on test sets, demonstrating their robustness under various imaging conditions.

\begin{table}[htbp]
\caption{Component-wise ablation and system analysis.}
\label{tab:table3_ablation_compact}
\centering
\resizebox{\linewidth}{!}{%
\begin{tabular}{lcc|lcc}
\hline
\textbf{Segmentation} & \textbf{Dice}$\uparrow$ & \textbf{HD95}$\downarrow$ &
\textbf{Classification} & \textbf{AUROC}$\uparrow$ & \textbf{AUPRC}$\uparrow$ \\
\hline
Seg (Best Single)  & 84.84 & 9.028  & Cls (Best Single)   & 0.873 & 0.793  \\
Seg + RL-CCA       & 85.18 & 8.483  & Radiomics+AutoGluon & 0.853 & 0.836 \\
\textbf{ThyAgent-Seg} & \textbf{85.31} & \textbf{8.303} &
\textbf{ThyAgent-Cls} & \textbf{0.888} & \textbf{0.877} \\
\hline
\end{tabular}%
}
\end{table}

\subsection{Ablation Study and System Analysis}
%The ablation study dissects the system into three key components: (i) interpretable radiomics-based classification, (ii) optional segmentation refinement, and (iii) the contributions of the segmentation and classification agents.
The ablation study begins with a classifier using PyRadiomics~\cite{van2017computational} and AutoGluon~\cite{erickson2020autogluon}, which leverages morphology and texture descriptors from segmentation masks to predict malignancy. Since radiomics features are mask-dependent, improvements in segmentation reliability enhance the stability of this prediction.
Additionally, reinforcement learning was applied to optimize hyperparameters for connected component analysis (CCA), achieving modest improvements in segmentation performance. ThyAgent-Seg and ThyAgent-Cls further boost performance through evidence-aware aggregation, combining segmentation masks, classification confidence, and radiomics features. 

% 尝试将其中一幅图改成饼图
\begin{figure}[htbp]
    \centering
    \includegraphics[width=1.0\linewidth]{figures/Fig3.pdf}
    \caption{Analysis of agentic aggregation.
    (a) Cls vote consistency distribution across models.
    (b) Distribution of Seg disagreement scores (Area-CV).
    (c) Cls performance across Seg Dice-score bins.}
    \label{fig:system_analysis}
\end{figure}

\subsubsection{Effectiveness of Agentic Aggregation.}
\label{sec:effectiveness}
% The rationale for using agents is supported by diagnostic evidence showing that multi-model outputs are not trivially redundant. Both segmentation and classification experts exhibit non-negligible disagreement across samples, as illustrated by the Area-CV distribution (median = 0.057, 90th percentile = 0.250) in Fig.~\ref{fig:system_analysis}.(b) and the vote-consistency histogram, in Fig.~\ref{fig:system_analysis}.(a). This indicates that no single model consistently performs across all images, highlighting the need for agent-based selection or aggregation to ensure reliable output.

%The use of agents is supported by evidence showing non-trivial disagreement among multi-model outputs. Both segmentation and classification experts exhibit notable variation across samples, as shown by the Area-CV distribution (median = 0.057, 90th percentile = 0.250) and the vote-consistency histogram in Fig.~\ref{fig:system_analysis}. This highlights the need for agent-based selection or aggregation to ensure reliable output. Furthermore, the relationship between segmentation quality and classification performance in Fig.~\ref{fig:system_analysis}.(c) reveals that the agent consistently outperforms common heuristics, such as selecting the most confident expert (Max) or taking the majority vote (Vote), particularly in the Dice score bins of [0.6, 0.8]. In this range, the improvement is likely due to the use of radiomics features for better contour and texture characterization, while the gap narrows in [0.8, 1.0] as segmentation quality becomes high and expert predictions converge.
The rationale for using agents is supported by diagnostic evidence showing that multi-model outputs are not trivially redundant. Both segmentation and classification experts exhibit non-negligible disagreement across samples, as illustrated by the Area-CV distribution (median = 0.057, 90th percentile = 0.250) in Fig.~\ref{fig:system_analysis}.(b) and the vote-consistency pie, in Fig.~\ref{fig:system_analysis}.(a). This indicates that no single model consistently performs across all images, highlighting the need for agent-based selection or aggregation to ensure reliable output.
%Evidence shows significant disagreement among multi-model outputs, with both segmentation and classification experts varying across samples (Area-CV median = 0.057, 90th percentile = 0.250) in Fig.~\ref{fig:system_analysis}.(b), highlighting the need for agent-based selection or aggregation. 
Fig.~\ref{fig:system_analysis}.(c) demonstrates that the agent outperforms heuristics like selecting the most confident expert or majority voting, especially in the Dice score range of [0.6, 0.8], where radiomics features improve performance. The gap narrows in the [0.8, 1.0] range as segmentation quality improves.


\subsubsection{Interpretability Analysis.}
%We investigate the model's decision-making process through SHAP values, analyzed from both global and individual case perspectives. Fig.~\ref{fig:interpretability_analysis}.(a) highlight the features most influential in malignancy prediction and segmentation reliability. The analysis shows that shape-related features such as Sphericity and Elongation, along with texture features like LRHGLE and SRHGLE, play a significant role in both tasks. These findings support the agent's evidence-aware decision-making by prioritizing these features during expert selection. At the case level, Fig.~\ref{fig:interpretability_analysis}.(b) illustrate SHAP waterfall plots for a classification prediction, the dominant feature contributions align with the final decision, confirming the model's interpretability.  These results highlight the potential for refining the agent’s focus on more reliable features, ultimately improving robustness and accuracy. For Fig.~\ref{fig:interpretability_analysis}.(c), the segmentation masks generated by different models are shown alongside the ground truth mask. The feature heatmap from ThyAgent-Seg provides an additional visualization. In contrast to classification models, segmentation models do not heavily prioritize the 2D shape features like Sphericity and Elongation, instead focusing more on the spatial structure of the object.

% 将图改成svg图，尽量让图变宽
\begin{figure}[htbp]
    \centering
    \includegraphics[width=1.0\linewidth]{figures/Fig4.pdf}
    \caption{Interpretability analysis of classification and segmentation evidence.}
    \label{fig:interpretability_analysis}
\end{figure}

% We investigate the model's decision-making through SHAP~\cite{lundberg2017unified} values from both global and individual case perspectives. Fig.~\ref{fig:interpretability_analysis}.(a) highlights the most influential features in malignancy prediction. Shape-related features and texture features like Sphericity and LRHGLE, are crucial in classification tasks, supporting the agent's evidence-aware decision-making. At the case level, Fig.~\ref{fig:interpretability_analysis}.(b) shows that the dominant feature contributions align with the final classification decision, confirming the model's interpretability. These results suggest that refining the agent’s focus on reliable features can improve robustness and accuracy. For Fig.~\ref{fig:interpretability_analysis}.(c), segmentation masks from different models are compared with the ground truth mask, with ThyAgent-Seg’s feature heatmap providing additional insights. Unlike classification models, segmentation models prioritize spatial structure over 2D shape features.
We analyze the model's decision-making using SHAP values from global and individual perspectives. Fig.~\ref{fig:interpretability_analysis}.(a) highlights key features like Sphericity in classification, supporting the agent's evidence-aware decisions. Fig.~\ref{fig:interpretability_analysis}.(b) shows that feature contributions align with the final classification, confirming the model's interpretability. Fig.~\ref{fig:interpretability_analysis}.(c) compares segmentation masks with ground truth, showing that ThyAgent-Seg focuses on spatial structure, unlike classification models which prioritize 2D shape features.

% Conclusion是否需要加上省基金项目信息
\section{Conclusion}
%In this work, we introduce ThyroidAgent, an innovative agent-based framework for unified thyroid ultrasound nodule segmentation and classification. By leveraging dynamic model selection based on contextual metadata, we enhance the interpretability and reliability of predictions under real-world conditions. Our experiments show that the agent-based approach improves performance across various datasets, highlighting its potential for more robust clinical deployment. This framework sets the foundation for future advancements in dynamic, context-aware medical image analysis systems.
%We propose ThyroidAgent, a novel agent-based framework that dynamically integrates segmentation and classification tasks for thyroid ultrasound analysis. By leveraging expert model selection based on contextual metadata, ThyroidAgent achieves superior performance across diverse ultrasound conditions, outperforming traditional static pipelines. The framework’s multi-task learning approach, combined with a curated thyroid ultrasound dataset, demonstrates significant improvements in both segmentation and classification tasks. Future work will focus on expanding the dataset and exploring additional modalities to further enhance model generalization. ThyroidAgent lays the foundation for future advancements in adaptive, evidence-driven systems, with promising applications in clinical decision support and real-time diagnostics.
We propose ThyroidAgent, an agent-based framework that dynamically integrates segmentation and classification for thyroid ultrasound analysis. By selecting expert models based on contextual metadata, it outperforms traditional static pipelines across diverse conditions. The multi-task learning approach, along with a curated dataset, enhances both segmentation and classification. Future work will focus on expanding the dataset and exploring additional modalities to improve model generalization.
%
% ---- Bibliography ----
%
% BibTeX users should specify bibliography style 'splncs04'.
% References will then be sorted and formatted in the correct style.
%
% \bibliographystyle{splncs04}
% \bibliography{mybibliography}
%
\bibliographystyle{splncs04}
\bibliography{ref}
\end{document}
