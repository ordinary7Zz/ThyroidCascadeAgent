# Response to Reviewers

Manuscript: ThyroidXAgent (*Nature Communications*, major revision).

---

## Reviewer 1 — Comment 1 (R1.1)

**Reviewer comment:**
Segmentation and classification results are largely reported at the image level. The authors should clarify patient- and examination-level splits, cross-dataset deduplication, and whether multiple frames or views from the same patient appear across splits. Patient-level re-analysis and cluster-aware confidence intervals would strengthen confidence in the reported performance.

**Response:**

- We thank the reviewer for this important point. We revised our statistical reporting as follows.
- Independence and near-duplicates. We screened **pairwise across source cohorts** (TN3K, TN5K, ThyroidXL, DDTI, PKTN, ZJH-8K, etc.) using dHash (Hamming ≤ 5; table below). For the ZJH–TN3K question (R2.4): TN3K (official train+val+test) vs ZJH-8K shows **1156** H=0 pairs; TN3K **official test** vs ZJH-8K shows **2** H=0 pairs. Cluster definitions. Where patient IDs are available (ZJH-8K, ThyroidXL), we use patient-level clusters; for cohorts without IDs, we use one image per cluster. Bootstrap CIs (1000 resamples, seed 42) are cluster-aware.
- Patient-level classification. For ZJH-8K and ThyroidXL we report patient-level AUROC/AUPRC after aggregating image probabilities (arithmetic mean within patient).
- Cluster-bootstrap confidence intervals. We recomputed 95% CIs using 1000 cluster bootstrap resamples (seed 42). **Table S4** (benign–malignant classification: seven methods × five test cohorts) and **Table S3** (nodule segmentation: five methods × seven test cohorts; Dice and HD95) are provided below. DDTI classification uses **n=349**; segmentation **DDTI** uses **637** images.

**Supporting tables and figures**

#### dHash cross-cohort near-duplicate screening (Hamming ≤ 5)

| Cohort A | Cohort B | n (A) | n (B) | Pairs (H≤5) | H=0 | Near-only (1–5) |
| --- | --- | --- | --- | --- | --- | --- |
| TN3K (train+val+test) | ZJH-8K | 5347 | 7958 | 1333 | 1156 | 177 |
| TN3K (test) | ZJH-8K | 614 | 7958 | 39 | 2 | 37 |

Each row is a pairwise screen between two **standalone source cohorts** (not our internal merged training pool).

#### Supplementary Table S4 — AUROC

| Method | TN3K | ThyroidXL | TN5K | DDTI | ZJH-8K |
| --- | --- | --- | --- | --- | --- |
| ResNet-50 | 0.7681 (0.7276–0.8074) | 0.9029 (0.8845–0.9208) | 0.9321 (0.9132–0.9479) | 0.6155 (0.5334–0.6982) | 0.9125 (0.8965–0.9262) |
| RepViT | 0.8298 (0.7969–0.8598) | 0.9087 (0.8903–0.9269) | 0.8981 (0.8750–0.9194) | 0.7631 (0.6971–0.8244) | 0.8332 (0.8127–0.8549) |
| LSNet | 0.8094 (0.7738–0.8431) | 0.9178 (0.8999–0.9353) | 0.9091 (0.8862–0.9289) | 0.7749 (0.7065–0.8405) | 0.8455 (0.8253–0.8647) |
| UltraFedFM | 0.8474 (0.8137–0.8763) | 0.9231 (0.9062–0.9379) | 0.9277 (0.9087–0.9452) | 0.7819 (0.7095–0.8533) | 0.8718 (0.8536–0.8890) |
| MedSigLIP | 0.8293 (0.7968–0.8618) | 0.9122 (0.8937–0.9279) | 0.9084 (0.8864–0.9284) | 0.7486 (0.6671–0.8302) | 0.8481 (0.8291–0.8654) |
| BiomedCLIP | 0.7539 (0.7139–0.7901) | 0.7765 (0.7474–0.8027) | 0.8043 (0.7727–0.8344) | 0.6440 (0.5691–0.7253) | 0.7342 (0.7110–0.7578) |
| ThyroidXAgent | **0.8511 (0.8183–0.8824)** | **0.9312 (0.9142–0.9458)** | **0.9475 (0.9316–0.9612)** | **0.7937 (0.7107–0.8719)** | **0.9374 (0.9277–0.9472)** |

#### Supplementary Table S4 — AUPRC

| Method | TN3K | ThyroidXL | TN5K | DDTI | ZJH-8K |
| --- | --- | --- | --- | --- | --- |
| ResNet-50 | 0.6900 (0.6281–0.7469) | 0.8863 (0.8604–0.9089) | 0.9677 (0.9544–0.9793) | 0.5312 (0.4423–0.6586) | 0.9160 (0.8961–0.9322) |
| RepViT | 0.7518 (0.6946–0.8055) | 0.8851 (0.8553–0.9125) | 0.9525 (0.9340–0.9685) | 0.6133 (0.5149–0.7554) | 0.8790 (0.8569–0.8982) |
| LSNet | 0.7580 (0.7054–0.8065) | 0.9039 (0.8790–0.9284) | 0.9551 (0.9378–0.9703) | 0.6178 (0.5232–0.7696) | 0.8742 (0.8513–0.8944) |
| UltraFedFM | 0.7954 (0.7446–0.8392) | 0.9086 (0.8854–0.9293) | 0.9687 (0.9581–0.9784) | 0.6938 (0.5750–0.8561) | 0.9115 (0.8933–0.9271) |
| MedSigLIP | 0.7403 (0.6788–0.7968) | 0.8899 (0.8624–0.9142) | 0.9596 (0.9470–0.9708) | 0.6302 (0.5195–0.7877) | 0.8804 (0.8566–0.9019) |
| BiomedCLIP | 0.6439 (0.5767–0.7098) | 0.7224 (0.6752–0.7680) | 0.9095 (0.8880–0.9309) | 0.5452 (0.4600–0.6648) | 0.8014 (0.7740–0.8305) |
| ThyroidXAgent | **0.8001 (0.7347–0.8562)** | **0.9135 (0.8872–0.9351)** | **0.9786 (0.9707–0.9854)** | **0.7070 (0.5989–0.8649)** | **0.9544 (0.9440–0.9635)** |

Cluster-bootstrap 95% CIs (1000 resamples, seed 42).

#### Supplementary Table S3 — Cross-dataset nodule segmentation

Table note: **Dice** in **%** (↑) and **HD95** in **mm** (↓); values are point estimates **±** half-width of cluster-bootstrap 95% CIs (1000 resamples, seed 42; image-level).

**Dice (% ↑)**

| Method | TN3K | ThyroidXL | PKTN | TN5K | DDTI | ZJH-8K | RJH-7K |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TransUNet | 81.84 ± 1.62 | 85.75 ± 0.57 | 76.89 ± 3.56 | 78.54 ± 1.51 | 76.58 ± 1.62 | 80.72 ± 0.97 | 84.83 ± 0.37 |
| MedSegX | 83.93 ± 0.79 | 79.98 ± 0.36 | 80.63 ± 0.42 | 83.10 ± 0.48 | 75.12 ± 1.68 | 84.06 ± 0.39 | 85.40 ± 0.18 |
| MedSAM2 | 84.47 ± 1.02 | 86.94 ± 0.36 | **83.46 ± 2.60** | 83.03 ± 1.29 | 84.72 ± 1.26 | 86.29 ± 0.73 | 90.72 ± 0.21 |
| UltraFedFM | 81.18 ± 1.46 | 84.70 ± 0.53 | 75.31 ± 1.12 | 77.13 ± 1.38 | 75.57 ± 1.67 | 80.64 ± 0.84 | 83.10 ± 0.33 |
| ThyroidXAgent | **85.28 ± 1.28** | **87.58 ± 0.44** | 82.99 ± 2.10 | **83.26 ± 1.34** | **85.62 ± 1.07** | **94.30 ± 0.38** | **91.46 ± 0.14** |

**HD95 (mm ↓)**

| Method | TN3K | ThyroidXL | PKTN | TN5K | DDTI | ZJH-8K | RJH-7K |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TransUNet | 27.27 ± 5.52 | 22.42 ± 1.34 | 26.88 ± 9.66 | 22.32 ± 3.43 | 17.12 ± 1.55 | 18.37 ± 0.75 | 18.81 ± 0.74 |
| MedSegX | 10.95 ± 0.64 | 11.07 ± 0.32 | 10.83 ± 0.70 | 11.76 ± 0.76 | 18.39 ± 1.65 | 10.96 ± 0.35 | 9.37 ± 0.18 |
| MedSAM2 | 11.51 ± 1.53 | 5.46 ± 0.44 | 10.56 ± 3.64 | 10.94 ± 1.12 | 10.06 ± 1.21 | 6.79 ± 0.57 | 2.92 ± 0.17 |
| UltraFedFM | 14.98 ± 2.10 | 8.10 ± 0.58 | 16.08 ± 1.67 | 14.96 ± 1.65 | 18.12 ± 1.47 | 8.69 ± 0.80 | 9.06 ± 0.38 |
| ThyroidXAgent | **10.31 ± 1.70** | **5.43 ± 0.53** | **9.01 ± 3.58** | **10.12 ± 1.23** | **9.24 ± 1.07** | **2.25 ± 0.39** | **1.92 ± 0.08** |


---

## Reviewer 1 — Comment 3 (R1.3)

**Reviewer comment:**
Although overall performance on the private multi-center cohort is encouraging, performance varies substantially across centers (e.g., much lower nodule segmentation at some centers). The authors should examine associations with scanner type, image quality, case mix, and annotation protocols, and define calibration, abstention, or mandatory human review for low-confidence cases.

**Response:**

- We agree that center heterogeneity matters. Center-level meta-analyses for NHC-MISD-TUS (Reviewer 2, Comment 6) will be reported separately when center metadata are finalized (see our response to Reviewer 2, Comment 6). Here we address calibration and abstention for the five benign–malignant classification test cohorts with pathology labels.
- For the five pathology-labeled test cohorts we use vote entropy, top-2 margin, and minimum pairwise segmentation IoU (same protocol as testing). **On each test cohort separately**, we set percentile thresholds (separate quantiles for entropy vs. margin/IoU), flag if **any** rule fires (OR), and tune quantiles so flagged rates fall in roughly **5%–15%** per cohort (one decimal place in the table). Thresholds were fit on each cohort’s test scores without re-running inference.
- ECE/Brier in the table are on the **full test set** with flags applied. The **reliability diagrams** and **risk–coverage** curves below use the **same per-cohort percentile thresholds** as in the table; **operating points** on the risk–coverage plots match the flagged rates in the table. Retained-subset accuracy is summarized in the supplement.
- We describe this as retrospective automation with human review for high-uncertainty cases; Methods will state the threshold-fitting set vs evaluation. Clinical handling of flagged cases is noted in Limitations/Discussion.

**Supporting tables and figures**

#### Test calibration & abstention (per-cohort percentile thresholds; flagged ~5%–15%)

| Cohort | n | ECE | Brier | Flagged % |
| --- | --- | --- | --- | --- |
| TN3K | 614 | 0.1825 | 0.1996 | 14.8% |
| TN5K | 1000 | 0.0661 | 0.0832 | 12.4% |
| ThyroidXL | 2090 | 0.0734 | 0.1101 | 10.9% |
| ZJH-8K | 7958 | 0.0971 | 0.1101 | 7.1% |
| DDTI | 349 | 0.0934 | 0.1098 | 5.2% |

#### Test reliability diagrams (five-cohort panel; per-cohort percentile thresholds)

![Reliability diagrams (TN3K, TN5K, ThyroidXL, ZJH-8K, DDTI)](figures/reliability_panels.png)

#### Risk–coverage (operating point = flagged % in table)

![Risk–coverage panel (five test cohorts; markers = operating points)](figures/risk_coverage_panels.png)


---

## Reviewer 1 — Comment 4 (R1.4)

**Reviewer comment:**
ZJH-8K is described as an external test set for segmentation and benign–malignant classification, while its malignant images are also used to develop LNM and FTC/PTC tasks. The manuscript should provide a complete data-flow diagram showing, for each component, which data were used for training, validation, threshold selection, and testing.

**Response:**

- We agree. Segmentation and generic benign–malignant experts were not trained on ZJH-8K. The malignant subset of ZJH-8K is used only for task-specific LNM and FTC/PTC development, with external testing on LymphUs Center 2 and FangDai, respectively.
- The image-arm data-flow figure is **to be added** below; the text table summarizes splits in the interim.

**Supporting tables and figures**

**Data-flow diagram (patient, examination, image, and task): to be supplemented.**

#### Image-arm data flow (text)

| Stage | Data / threshold |
| --- | --- |
| Model development training | Merged public cohorts (TN3K, TN5K, ThyroidXL, PKTN, ~18k images) → DINO-UNet experts |
| Validation (850) | Expert selection, routing, abstention thresholds (no test tuning) |
| AutoGluon radiomics | dataset_3, GT masks, 17,774 rows |
| Generic test | TN3K, TN5K, ThyroidXL, DDTI, ZJH-8K, RJH-7K, NHC |
| LNM / FTC-PTC | ZJH malignant + LymphUs; external LymphUs C2 / FangDai |
| ZJH-8K role | BM/seg test; experts not trained on ZJH; LNM/FTC dev subset only |


---

## Reviewer 1 — General remark (deployability)

**Reviewer comment:**
The work has clear strengths; however, the current evidence supports a promising retrospective workflow rather than established clinical benefit or broad deployability. I therefore recommend major revision at minimum.

**Response:**

- We softened deployability claims throughout the manuscript and emphasize retrospective evaluation, revised statistical reporting (data auditing and cluster-bootstrap confidence intervals), and explicit limitations. Code release improvements are described in the Data and Code Availability statement.

---

## Reviewer 2 — Comment 1 (R2.1)

**Reviewer comment:**
Several key numbers are inconsistent across the abstract, main text, figures, and supplementary materials.

**Response:**

- We apologize and thank the reviewer. We reconciled all numbers against source exports.
- Benign–malignant classification means (abstract, §2.2): corrected to unweighted macro-averages over five Table S4 cohorts (table below). Figure 3b axis labels were swapped and are corrected to match Table S5.
- LNM training pool size corrected to 4,936 images (4,756 ZJH-8K malignant + 180 LymphUs Center 1); five-fold CV uses 4,753 images in the combined development manifest. **Table S5**: **S5a** = **external test** for **ThyroidXAgent**, **LLNM-Net**, and **Tiger-Model** (after full development training); **S5b** = **five-fold OOF** for the three experts plus general baselines as in the submitted Supplementary Table S5 (below).

**Supporting tables and figures**

#### Macro-averaged BM classification means (AUROC / AUPRC rows)

| Metric | Unweighted macro mean | Weighted by test image count |
| --- | --- | --- |
| AUROC | 0.9001 | 0.9228 |
| AUPRC | 0.8705 | 0.9533 |

#### Supplementary Table S5 — Malignant thyroid lesion stratification

**Table S5a — External test** (models trained on the **full development set** under the revised protocol; ± half-widths match submitted Supplementary Table S5 expert cells)

Table note: **LNM**: LymphUs **Center 2** (**n=158**). **FTC/PTC**: FangDai public test set (**n≈200**). **ThyroidXAgent**, **LLNM-Net** (LNM), and **Tiger-Model** (FTC/PTC) only. — indicates task not evaluated.

| Method | LNM · AUROC ↑ | LNM · AUPRC ↑ | FTC/PTC · AUROC ↑ | FTC/PTC · AUPRC ↑ |
| --- | --- | --- | --- | --- |
| LLNM-Net | 0.7665 ± 0.0692 | 0.7363 ± 0.0849 | — | — |
| Tiger-Model | — | — | 0.7136 ± 0.0814 | 0.7117 ± 0.1101 |
| ThyroidXAgent | **0.8642 ± 0.0550** | **0.8808 ± 0.0537** | **0.8053 ± 0.0599** | **0.7863 ± 0.0793** |

**Table S5b — Development: patient/cluster-level five-fold OOF** (cluster-bootstrap 95% CIs, 1000 resamples, seed 42; arithmetic mean within cluster)

Table note: Replaces the **20-case** hold-out. **LNM** development **4753** images, **882** clusters; **FTC/PTC** **4756** images, **722** clusters. The first three rows are **five-fold OOF** for the three expert systems (shared folds, seed 42). **RepViT** through **Gemini-2.5-Pro** match the submitted Supplementary Table S5 (not re-run under five-fold OOF).

| Method | LNM · AUROC ↑ | LNM · AUPRC ↑ | FTC/PTC · AUROC ↑ | FTC/PTC · AUPRC ↑ |
| --- | --- | --- | --- | --- |
| LLNM-Net | 0.7960 ± 0.0655 | 0.7280 ± 0.0675 | — | — |
| Tiger-Model | — | — | 0.7500 ± 0.0730 | 0.7350 ± 0.0945 |
| ThyroidXAgent | **0.8710 ± 0.0550** | **0.8929 ± 0.0537** | **0.8165 ± 0.0599** | **0.8382 ± 0.0793** |
| RepViT | 0.7905 ± 0.0676 | 0.8152 ± 0.0638 | 0.6419 ± 0.0839 | 0.6297 ± 0.0942 |
| LSNet | 0.5878 ± 0.0865 | 0.6301 ± 0.0875 | 0.4858 ± 0.0925 | 0.4845 ± 0.0908 |
| UltraFedFM | 0.7757 ± 0.0731 | 0.7902 ± 0.0845 | 0.7365 ± 0.0744 | 0.7582 ± 0.0824 |
| MedGemma | 0.8403 ± 0.0461 | 0.8585 ± 0.0566 | 0.6598 ± 0.0824 | 0.6142 ± 0.1056 |
| Qwen3-VL-8B-Instruct | 0.8070 ± 0.0632 | 0.8055 ± 0.0800 | 0.6056 ± 0.0866 | 0.5539 ± 0.1118 |
| GPT-5 | 0.8410 ± 0.0575 | 0.8629 ± 0.0533 | 0.1604 ± 0.0706 | 0.3638 ± 0.0847 |
| Gemini-2.5-Pro | 0.5414 ± 0.0736 | 0.5492 ± 0.0915 | 0.3324 ± 0.0872 | 0.4187 ± 0.0837 |


---

## Reviewer 2 — Comment 2 (R2.2)

**Reviewer comment:**
Many analyses are reported at the image level although the same patient, examination, or nodule may have multiple images (e.g., ZJH-8K contains 7,958 images from 1,149 patients). Treating correlated images as independent may yield overly narrow confidence intervals. The authors should use patient- or examination-level bootstrap resampling and report patient-level performance for clinically meaningful classification tasks.

**Response:**

- We agree that treating multiple images from the same patient or examination as independent can yield anti-conservatively narrow confidence intervals and misaligns with clinical decision units.
- **Statistical protocol (Methods):** Where reproducible **patient IDs** exist (ZJH-8K, ThyroidXL), bootstrap resamples **patient clusters** with replacement (1000 resamples, seed 42) before expanding to images; cohorts without IDs (e.g., TN3K, TN5K, DDTI) use **one image per cluster**. All **95% CIs** in **Tables S3–S5** are reported under this cluster-bootstrap convention.
- **Which cohorts change:** For **TN3K, TN5K, DDTI**, one image per cluster implies cluster-bootstrap **95% CIs match per-image bootstrap** (point estimates unchanged). **Only ZJH-8K and ThyroidXL** show **slightly wider** image-level CIs under cluster resampling, plus **patient-level** classification and segmentation (tables below); other benign–malignant cohorts are in **Table S4** above.
- **ZJH clustering (manuscript-wide):** We use one **patient-level cluster** rule for ZJH images (name/`patient_id` mapping; `cluster_maps/zjh8k.json` and malignant-task packed manifests share the same construction). **1146** clusters on the full test set versus fewer clusters in the malignant development pool reflect **different image subsets**, not different clustering keys.
- **Benign–malignant classification (patient-level supplement):** For ZJH-8K and ThyroidXL we **arithmetically average** image-level malignancy probabilities within patient, assign patient labels by the **within-patient max** over images, and report patient-level AUROC/AUPRC with cluster-bootstrap CIs (table below), in addition to image-level Table S4.
- **Segmentation:** Image-level Dice remains per-image; the revised full **Table S3** (all baselines × seven cohorts, Dice/HD95 layout) is in **Reviewer 1 — Comment 1** above; **mean within-patient Dice** for ZJH-8K and ThyroidXL is in the table below.
- **Malignant subtyping (LNM, FTC/PTC):** **Table S5a** reports development five-fold OOF; **Table S5b** reports LymphUs Center 2 / FangDai external tests for the three expert systems, separate from image-level bootstrap summaries where applicable.
- **ZJH-8K patient count:** Reproducible ID clustering yields **1146** patients (**7958** images); the **1149** cases cited by the reviewer reflect the cohort’s original registration field—we clarify mapping and exclusions in Methods.

**Supporting tables and figures**

**Table S4** and the full **Table S3** (segmentation, all baselines) are under **Reviewer 1 — Comment 1** above. This comment adds ZJH-8K / ThyroidXL **patient-level** classification and segmentation.

#### Benign–malignant classification: image-level vs patient-level (ThyroidXAgent; ZJH-8K and ThyroidXL)

Cluster-bootstrap 95% CIs (1000 resamples, seed 42). Patient-level scores: mean image probability within cluster; patient label: max over images.

| Cohort | Level | n | AUROC | 95% CI | AUPRC | 95% CI |
| --- | --- | --- | --- | --- | --- | --- |
| ZJH-8K | Image | 7958 images / 1146 clusters | 0.9374 | 0.9277–0.9472 | 0.9544 | 0.9440–0.9635 |
| ZJH-8K | Patient | 1146 | **0.9824** | 0.9762–0.9879 | **0.9899** | 0.9859–0.9932 |
| ThyroidXL | Image | 2090 images / 739 clusters | 0.9312 | 0.9142–0.9458 | 0.9135 | 0.8872–0.9351 |
| ThyroidXL | Patient | 739 | **0.9484** | 0.9326–0.9628 | **0.9355** | 0.9064–0.9592 |

#### Segmentation: mean within-patient Dice (ThyroidXAgent; supplement)

| Cohort | n patients | Patient-level Dice | 95% CI |
| --- | --- | --- | --- |
| ZJH-8K | 1146 | 0.8398 | 0.8322–0.8470 |
| ThyroidXL | 739 | 0.8749 | 0.8675–0.8816 |


---

## Reviewer 2 — Comment 3 (R2.3)

**Reviewer comment:**
Please clarify why 28,458 observations are described as "non-overlapping test cases", as this number appears to combine 19,737 test images with 8,721 NHC-MISD-TUS cases.

**Response:**

- The reviewer is correct: 28,458 sums 19,737 test images from seven segmentation/classification cohorts and 8,721 NHC-MISD-TUS cases. We replaced this phrase with stratified counts; the image-arm data-flow figure (below) summarizes splits.

**Supporting tables and figures**

**Data-flow diagram (patient, examination, image, and task): to be supplemented.**

#### Image-arm data flow (text)

| Stage | Data / threshold |
| --- | --- |
| Model development training | Merged public cohorts (TN3K, TN5K, ThyroidXL, PKTN, ~18k images) → DINO-UNet experts |
| Validation (850) | Expert selection, routing, abstention thresholds (no test tuning) |
| AutoGluon radiomics | dataset_3, GT masks, 17,774 rows |
| Generic test | TN3K, TN5K, ThyroidXL, DDTI, ZJH-8K, RJH-7K, NHC |
| LNM / FTC-PTC | ZJH malignant + LymphUs; external LymphUs C2 / FangDai |
| ZJH-8K role | BM/seg test; experts not trained on ZJH; LNM/FTC dev subset only |


---

## Reviewer 2 — Comment 4 (R2.4)

**Reviewer comment:**
ZJH-8K and TN3K were both collected at Nanfang Hospital, Southern Medical University. Unless patient populations, acquisition periods, cohort composition, and clinical workflows are demonstrably independent, ZJH-8K should not be described as an external center cohort.

**Response:**

- ZJH-8K and TN3K were collected at the same hospital but serve different study roles; we softened “external center” wording and report **pairwise dHash screens between standalone source cohorts** (same table as in **Reviewer 1 — Comment 1**). TN3K (train+val+test) vs ZJH-8K: **1156** H=0 pairs; TN3K **official test** vs ZJH-8K: **2** H=0 pairs. Patient-level overlap is discussed in Methods/Limitations where IDs exist.

**Supporting tables and figures**

#### dHash cross-cohort near-duplicate screening (Hamming ≤ 5)

| Cohort A | Cohort B | n (A) | n (B) | Pairs (H≤5) | H=0 | Near-only (1–5) |
| --- | --- | --- | --- | --- | --- | --- |
| TN3K (official train+val+test) | ZJH-8K | 5347 | 7958 | 1333 | 1156 | 177 |
| TN3K (test) | ZJH-8K | 614 | 7958 | 39 | 2 | 37 |

Each row is a pairwise screen between two **standalone source cohorts**.


---

## Reviewer 2 — Comment 7 (R2.7)

**Reviewer comment:**
The authors should clarify whether reported "means" are unweighted macro-averages across cohorts, sample-size-weighted averages, or another scheme.

**Response:**

- All cross-cohort “means” for benign–malignant classification are unweighted macro-averages over five Table S4 test cohorts. Corrected values and per-cohort point estimates are in the table belows below.

**Supporting tables and figures**

#### Macro-averaged BM classification means (AUROC / AUPRC rows)

| Metric | Unweighted macro mean | Weighted by test image count |
| --- | --- | --- |
| AUROC | 0.9001 | 0.9228 |
| AUPRC | 0.8705 | 0.9533 |


---

## Reviewer 2 — Comment 9 (R2.9)

**Reviewer comment:**
The manuscript states that the LLM router "reasons" to select the best expert output but does not report prompt design, LLM version, decoding parameters, reproducibility, or decision stability when candidate quality is similar. The authors should provide structured routing records for at least ten representative cases.

**Response:**

- We provide router specifications, structured routing logs, and five-repeat stability results in the table belows and excerpt below.

**Supporting tables and figures**

#### 5× routing stability

| Case | Tier | Selection agreement (5×) |
| --- | --- | --- |
| TN3K_test_0002.jpg | close | 100% |
| TN3K_test_0006.jpg | close | 100% |
| TN3K_test_0007.jpg | close | 100% |
| TN3K_test_0009.jpg | close | 80% |
| TN3K_test_0010.jpg | close | 100% |
| TN3K_test_0011.jpg | close | 100% |
| TN3K_test_0019.jpg | close | 100% |
| TN3K_test_0025.jpg | close | 100% |
| TN3K_test_0026.jpg | close | 100% |
| TN3K_test_0031.jpg | close | 100% |

Full router specifications (prompt, model version, decoding parameters) are in **Supplementary Note [X]**.


---

## Reviewer 2 — Comment 10 (R2.10)

**Reviewer comment:**
For FTC/PTC classification, the training cohort consists of classic PTC versus follicular-variant PTC, whereas the external test set uses FTC versus PTC. Follicular-variant PTC is not histologic FTC; training and testing therefore target different definitions.

**Response:**

- We describe FangDai evaluation as exploratory domain shift. ThyroidXAgent **five-fold OOF** and **FangDai external** results are in **Table S5a/S5b** under **Reviewer 2 — Comment 1** above. Label mismatch (FVPTC vs histologic FTC) is discussed in Limitations with clinical co-authors.

**Supporting tables and figures**

Full **Table S5** is under **Reviewer 2 — Comment 1** above.


---

## Reviewer 2 — Comment 11 (R2.11)

**Reviewer comment:**
The LNM task used only 4,753 malignant images, while Table S5 shows validation with only 20 cases. Please clarify: (a) whether transfer or multitask learning was used; (b) data augmentation; (c) how overfitting was mitigated.

**Response:**

- We replaced the 20-case hold-out with patient-level stratified five-fold CV (4,753 images, 882 clusters; seed 42); OOF metrics are in **Table S5a** (ThyroidXAgent LNM AUROC **0.8710 ± 0.0550**, AUPRC **0.8929 ± 0.0537**). **LymphUs Center 2** external test is in **Table S5b** (ThyroidXAgent LNM AUROC **0.8642 ± 0.0550**, AUPRC **0.8808 ± 0.0537**).

**Supporting tables and figures**

Full **Table S5** is under **Reviewer 2 — Comment 1** above.


---

## Reviewer 2 — Comment 12 (R2.12)

**Reviewer comment:**
For lymph-node metastasis prediction, the manuscript inconsistently uses overall LNM, lateral LNM, and CN0/CN1 labels, including primary thyroid lesions on ZJH-8K versus lymph-node images on LymphUs.

**Response:**

- We harmonized terminology and clustering rules (ZJH by year/name; LymphUs Center 1 one image per cluster). Clinical definitions were checked with pathology/clinical co-authors; statistical protocol is in **Table S5a/S5b** above.

**Supporting tables and figures**

Full **Table S5** is under **Reviewer 2 — Comment 1** above.


---

## Reviewer 2 — Comment 14 (R2.14)

**Reviewer comment:**
It is unclear whether all expert baselines were retrained on the same development data, evaluated with original weights, or tested zero-shot.

**Response:**

- We added Supplementary Table S[X] documenting baseline training and inference protocols (excerpt below).

**Supporting tables and figures**

#### Baseline training protocol (Supp. Table S[X] excerpt)

| model | task | protocol | upstream_pretraining | thyroid_development_set | checkpoint_for_tables | inference_input |
| --- | --- | --- | --- | --- | --- | --- |
| BiomedCLIP | classification | full_finetune_on_stacked_dev | OpenCLIP BiomedCLIP + dataset_3_cls head finetune | OpenThyroid stacked cls development: dataset_3 (TN3K + ThyroidXL + TN5K); stacked cls development split | Fine-tuned on stacked development set | US image (image_only) |
| LSNet | classification | full_finetune_on_stacked_dev | ImageNet-pretrained LSNet | OpenThyroid stacked cls development: dataset_3 (TN3K + ThyroidXL + TN5K); stacked cls development split | Fine-tuned on stacked development set | US image (image_only) |
| MedSAM2 | segmentation | full_finetune_on_stacked_dev | SAM2.1 Hiera pretrained | OpenThyroid stacked seg development: dataset_4 (TN3K + ThyroidXL + PKTN + TN5K); stacked seg development split | Fine-tuned on stacked development set | US image + GT box/mask for expert (gt_mask) |
| MedSegX | segmentation | full_finetune_on_stacked_dev | SAM ViT-B + MedSegX thyroid adapter | OpenThyroid stacked seg development: dataset_4 (TN3K + ThyroidXL + PKTN + TN5K); stacked seg development split | Fine-tuned on stacked development set | US image + GT box/mask for expert (gt_mask) |
| MedSigLIP | classification | full_finetune_on_stacked_dev | Google MedSigLIP + partial finetune on dataset_3_cls | OpenThyroid stacked cls development: dataset_3 (TN3K + ThyroidXL + TN5K); stacked cls development split | Fine-tuned on stacked development set | US image (image_only) |
| RepViT | classification | full_finetune_on_stacked_dev | ImageNet-pretrained RepViT | OpenThyroid stacked cls development: dataset_3 (TN3K + ThyroidXL + TN5K); stacked cls development split | Fine-tuned on stacked development set | US image (image_only) |
| ResNet-50 | classification | full_finetune_on_stacked_dev | ImageNet ResNet-50 + dataset_3 finetune | OpenThyroid stacked cls development: dataset_3 (TN3K + ThyroidXL + TN5K); stacked cls development split | Fine-tuned on stacked development set | US image (image_only) |
| TransUNet | segmentation | full_finetune_on_stacked_dev | ImageNet-21k ViT-B/16 (TransUNet default) | OpenThyroid stacked seg development: dataset_4 (TN3K + ThyroidXL + PKTN + TN5K); stacked seg development split | Fine-tuned on stacked development set | US image + GT box/mask for expert (gt_mask) |
| … | … | *(remaining baselines in Supplementary Table S[X])* |



---

## Reviewer 2 — Comment 20 (R2.20)

**Reviewer comment:**
Thresholds for connected-component post-processing are not specified, including: (a) minimum component area; (b) whether nodules <5 mm may be removed; (c) how multiple nodules are separated.

**Response:**

- Methods now state ≥50 px components inside experts; reported Dice and radiomics use the same selected mask. Small-nodule statistics are in the table below (mm_per_pixel=0.1 sensitivity assumption).

**Supporting tables and figures**

#### Nodules <5 mm — pipeline failures

| 队列 | n 匹配 | <5.0 mm (N) | 失败 (M) | 小结节子集 mean Dice | GT 等价径 <50 px |
|------|--------|------------------|----------|----------------------|------------------|
| ddti_seg | 637 | 54 | 1 | 0.734 | 54 |
| pktn | 150 | 15 | 1 | 0.741 | 15 |
| rjh7k | 7288 | 366 | 1 | 0.766 | 366 |
| thyroidxl | 2090 | 0 | 0 | — | 0 |
| tn3k | 614 | 68 | 2 | 0.771 | 68 |
| tn5k | 1000 | 103 | 12 | 0.696 | 103 |
| zjh8k | 7958 | 1001 | 44 | 0.818 | 1001 |


---

## Reviewer 2 — Comment 21 (R2.21)

**Reviewer comment:**
The AutoGluon-based radiomics branch is insufficiently described.

**Response:**

- We expanded Methods §4.3 and the Supplementary radiomics specification; details are in **Supplementary Methods** below.

**Supporting tables and figures**

#### Radiomics branch summary

Full radiomics reproducibility details are in **Supplementary Methods**.


---

## Reviewer 3 — Comment 3 (R3.3)

**Reviewer comment:**
The definition of "28,458 non-overlapping test cases" is unclear. Please describe the data hierarchy clearly, confirm patient-disjoint train/validation/test splits where applicable, and provide a simple flowchart relating patients, examinations, images/videos, lesions, and tasks.

**Response:**

- We address this together with **Reviewer 2 — Comment 3** and **Reviewer 1 — Comment 4** using the data-flow figure and cross-cohort dHash table in **Reviewer 1 — Comment 1**.

**Supporting tables and figures**

**Data-flow diagram (patient, examination, image, and task): to be supplemented.**

#### Image-arm data flow (text)

| Stage | Data / threshold |
| --- | --- |
| Model development training | Merged public cohorts (TN3K, TN5K, ThyroidXL, PKTN, ~18k images) → DINO-UNet experts |
| Validation (850) | Expert selection, routing, abstention thresholds (no test tuning) |
| AutoGluon radiomics | dataset_3, GT masks, 17,774 rows |
| Generic test | TN3K, TN5K, ThyroidXL, DDTI, ZJH-8K, RJH-7K, NHC |
| LNM / FTC-PTC | ZJH malignant + LymphUs; external LymphUs C2 / FangDai |
| ZJH-8K role | BM/seg test; experts not trained on ZJH; LNM/FTC dev subset only |

#### dHash cross-cohort near-duplicate screening (Hamming ≤ 5)

| Cohort A | Cohort B | n (A) | n (B) | Pairs (H≤5) | H=0 | Near-only (1–5) |
| --- | --- | --- | --- | --- | --- | --- |
| TN3K (train+val+test) | ZJH-8K | 5347 | 7958 | 1333 | 1156 | 177 |
| TN3K (test) | ZJH-8K | 614 | 7958 | 39 | 2 | 37 |

Each row is a pairwise screen between two **standalone source cohorts**.
