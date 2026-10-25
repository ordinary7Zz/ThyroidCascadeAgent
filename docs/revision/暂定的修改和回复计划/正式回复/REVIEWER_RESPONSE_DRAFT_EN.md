# Response to Reviewers

Manuscript: ThyroidXAgent (*Nature Communications*, major revision).

---

## Reviewer 1 — Comment 1 (R1.1)

**Reviewer comment:**
Segmentation and classification results are largely reported at the image level. The authors should clarify patient- and examination-level splits, cross-dataset deduplication, and whether multiple frames or views from the same patient appear across splits. Patient-level re-analysis and cluster-aware confidence intervals would strengthen confidence in the reported performance.

**Response:**

- We thank the reviewer for this important point. We revised our statistical reporting as follows.
- Independence and near-duplicates. We screened **pairwise across source cohorts** (TN3K, TN5K, ThyroidXL, DDTI, PKTN, ZJH-8K, etc.) using dHash (Hamming ≤ 5; **Table R1** at the end of this letter). For the ZJH–TN3K question (R2.4): TN3K (official train+val+test) vs ZJH-8K shows **1156** H=0 pairs; TN3K **official test** vs ZJH-8K shows **2** H=0 pairs. Cluster definitions. Where patient IDs are available (ZJH-8K, ThyroidXL), we use patient-level clusters; for cohorts without IDs, we use one image per cluster. Bootstrap CIs (1000 resamples, seed 42) are cluster-aware.
- Patient-level classification. For ZJH-8K and ThyroidXL we report patient-level AUROC/AUPRC after aggregating image probabilities (arithmetic mean within patient).
- Cluster-bootstrap confidence intervals. We recomputed 95% CIs using 1000 cluster bootstrap resamples (seed 42). **Table S4** (benign–malignant classification: seven methods × five test cohorts) and **Table S3** (nodule segmentation: five methods × seven test cohorts; Dice and HD95) are in **Tables R2–R4** at the end of this letter. DDTI classification uses **n=349**; segmentation **DDTI** uses **637** images.

**Supporting material:** See **Table R1** (dHash near-duplicate screening), **Tables R2–R3** (Supplementary Table S4, AUROC/AUPRC), and **Table R4** (Supplementary Table S3, segmentation Dice/HD95) at the end of this letter.

---

## Reviewer 1 — Comment 3 (R1.3)

**Reviewer comment:**
Although overall performance on the private multi-center cohort is encouraging, performance varies substantially across centers (e.g., much lower nodule segmentation at some centers). The authors should examine associations with scanner type, image quality, case mix, and annotation protocols, and define calibration, abstention, or mandatory human review for low-confidence cases.

**Response:**

- We agree that center heterogeneity matters. Center-level meta-analyses for NHC-MISD-TUS (Reviewer 2, Comment 6) will be reported separately when center metadata are finalized (see our response to Reviewer 2, Comment 6). Here we address calibration and abstention for the five benign–malignant classification test cohorts with pathology labels.
- For the five pathology-labeled test cohorts we use vote entropy, top-2 margin, and minimum pairwise segmentation IoU (same protocol as testing). **On each test cohort separately**, we set percentile thresholds (separate quantiles for entropy vs. margin/IoU), flag if **any** rule fires (OR), and tune quantiles so flagged rates fall in roughly **5%–15%** per cohort (one decimal place in **Table R5**). Thresholds were fit on each cohort’s test scores without re-running inference.
- ECE/Brier in **Table R5** are on the **full test set** with flags applied. The **reliability diagrams** and **risk–coverage** **Figures R1–R2** use the **same per-cohort percentile thresholds** as in **Table R5**; **operating points** on the risk–coverage plots match the flagged rates in **Table R5**. Retained-subset accuracy is summarized in the supplement.
- We describe this as retrospective automation with human review for high-uncertainty cases; Methods will state the threshold-fitting set vs evaluation. Clinical handling of flagged cases is noted in Limitations/Discussion.

**Supporting material:** See **Table R5** (external-test calibration and referral), **Figure R1** (reliability diagrams), and **Figure R2** (risk–coverage curves) at the end of this letter.

---

## Reviewer 1 — Comment 4 (R1.4)

**Reviewer comment:**
ZJH-8K is described as an external test set for segmentation and benign–malignant classification, while its malignant images are also used to develop LNM and FTC/PTC tasks. The manuscript should provide a complete data-flow diagram showing, for each component, which data were used for training, validation, threshold selection, and testing.

**Response:**

- We agree. Segmentation and generic benign–malignant experts were not trained on ZJH-8K. The malignant subset of ZJH-8K is used only for task-specific LNM and FTC/PTC development, with external testing on LymphUs Center 2 and FangDai, respectively.
- The image-arm data-flow figure is **to be supplied**; the tabular summary is in **Table R6** summarizes splits in the interim.

**Supporting material:** Patient–examination–image–task dataflow figure (to be supplied); tabular summary in **Table R6** at the end of this letter.

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
- Benign–malignant classification means (abstract, §2.2): corrected to unweighted macro-averages over five Table S4 cohorts—AUROC **0.9001**, AUPRC **0.8707** (**Table R7** at the end of this letter); weighted by test image count—AUROC **0.9286**, AUPRC **0.9533** (consistent with ThyroidXAgent per-cohort point estimates in Table S4). Figure 3b axis labels were swapped and are corrected to match **Table S4** and the **Table R7** at the end of this letter.
- LNM training pool size corrected to 4,936 images (4,756 ZJH-8K malignant + 180 LymphUs Center 1); five-fold CV uses 4,753 images in the combined development manifest. **Table S5** is split into **external test (S5a)** and **development five-fold OOF (S5b)** blocks (three expert systems); general baseline rows match the submitted Supplementary Table S5 (**Table R8** at the end of this letter).

**Supporting material:** See **Table R7** (five-cohort summary means) and **Table R8** (Supplementary Table S5a/S5b) at the end of this letter.

---

## Reviewer 2 — Comment 2 (R2.2)

**Reviewer comment:**
Many analyses are reported at the image level although the same patient, examination, or nodule may have multiple images (e.g., ZJH-8K contains 7,958 images from 1,149 patients). Treating correlated images as independent may yield overly narrow confidence intervals. The authors should use patient- or examination-level bootstrap resampling and report patient-level performance for clinically meaningful classification tasks.

**Response:**

- We agree that treating multiple images from the same patient or examination as independent can yield anti-conservatively narrow confidence intervals and misaligns with clinical decision units.
- **Statistical protocol (Methods):** Where reproducible **patient IDs** exist (ZJH-8K, ThyroidXL), bootstrap resamples **patient clusters** with replacement (1000 resamples, seed 42) before expanding to images; cohorts without IDs (e.g., TN3K, TN5K, DDTI) use **one image per cluster**. All **95% CIs** in **Tables S3–S5** are reported under this cluster-bootstrap convention.
- **Which cohorts change:** For **TN3K, TN5K, DDTI**, one image per cluster implies cluster-bootstrap **95% CIs match per-image bootstrap** (point estimates unchanged). **Only ZJH-8K and ThyroidXL** show **slightly wider** image-level CIs under cluster resampling, plus **patient-level** classification and segmentation (**Tables R9** and **R10** at the end of this letter); other benign–malignant cohorts are in **Tables R2–R3** at the end of this letter.
- **ZJH clustering (manuscript-wide):** We use one **patient-level cluster** rule for ZJH images (name/`patient_id` mapping; malignant-task development manifests share the same patient-ID construction). **1146** clusters on the full test set versus fewer clusters in the malignant development pool reflect **different image subsets**, not different clustering keys.
- **Benign–malignant classification (patient-level supplement):** For ZJH-8K and ThyroidXL we **arithmetically average** image-level malignancy probabilities within patient, assign patient labels by the **within-patient max** over images, and report patient-level AUROC/AUPRC with cluster-bootstrap CIs (**Table R7** at the end of this letter), in addition to image-level Table S4.
- **Segmentation:** Image-level Dice remains per-image; the revised full **Table S3** (all baselines × seven cohorts, Dice/HD95 layout) is **Table R4** at the end of this letter; **mean within-patient Dice** for ZJH-8K and ThyroidXL is **Table R10** at the end of this letter.
- **Malignant subtyping (LNM, FTC/PTC):** **Table S5a** reports LymphUs Center 2 / FangDai **external** tests; **Table S5b** reports development five-fold **OOF** for the three expert systems, separate from image-level bootstrap summaries where applicable.
- **ZJH-8K patient count:** Reproducible ID clustering yields **1146** patients (**7958** images); the **1149** cases cited by the reviewer reflect the cohort’s original registration field—we clarify mapping and exclusions in Methods.

**Supporting material:** Full **Tables S3/S4** are **Tables R2–R4**; patient-level ZJH-8K / ThyroidXL results are **Tables R9** and **R10** at the end of this letter.

---

## Reviewer 2 — Comment 3 (R2.3)

**Reviewer comment:**
Please clarify why 28,458 observations are described as "non-overlapping test cases", as this number appears to combine 19,737 test images with 8,721 NHC-MISD-TUS cases.

**Response:**

- The reviewer is correct: 28,458 sums 19,737 test images from seven segmentation/classification cohorts and 8,721 NHC-MISD-TUS cases. We replaced this phrase with stratified counts; the image-arm data-flow **Table R6** summarizes (figure to be supplied) splits.

**Supporting material:** Dataflow figure (to be supplied); tabular summary in **Table R6** at the end of this letter.

---

## Reviewer 2 — Comment 4 (R2.4)

**Reviewer comment:**
ZJH-8K and TN3K were both collected at Nanfang Hospital, Southern Medical University. Unless patient populations, acquisition periods, cohort composition, and clinical workflows are demonstrably independent, ZJH-8K should not be described as an external center cohort.

**Response:**

- ZJH-8K and TN3K were collected at the same hospital but serve different study roles; we softened “external center” wording and report **pairwise dHash screens between standalone source cohorts** (same protocol as R1.1 (**Table R1** at the end of this letter)). TN3K (train+val+test) vs ZJH-8K: **1156** H=0 pairs; TN3K **official test** vs ZJH-8K: **2** H=0 pairs. Patient-level overlap is discussed in Methods/Limitations where IDs exist.

**Supporting material:** dHash screening in **Table R1** at the end of this letter (same protocol as R1.1).

---

## Reviewer 2 — Comment 7 (R2.7)

**Reviewer comment:**
The authors should clarify whether reported "means" are unweighted macro-averages across cohorts, sample-size-weighted averages, or another scheme.

**Response:**

- All cross-cohort “means” for benign–malignant classification are unweighted macro-averages over five Table S4 test cohorts. Corrected values and per-cohort point estimates are in **Table R7** and **Tables R2–R3** at the end of this letter.

**Supporting material:** See **Table R7** at the end of this letter.

---

## Reviewer 2 — Comment 9 (R2.9)

**Reviewer comment:**
The manuscript states that the LLM router "reasons" to select the best expert output but does not report prompt design, LLM version, decoding parameters, reproducibility, or decision stability when candidate quality is similar. The authors should provide structured routing records for at least ten representative cases.

**Response:**

- We provide **model and decoding parameters, full prompt templates, JSON output schemas, and structured routing-log fields** at the end of this letter (**Table R11**, **Appendix A1**) (the revised Supplementary Information will contain the same content). On the TN3K `test_for_llm_malignancy` cohort (*N* = 250), every routing call is logged in `routing_log.jsonl`. With **frozen Phase 1–2 expert outputs**, we repeated LLM **segmentation** routing five times per case on a stability subset (*n* = **10**; Path A classification consensus is not re-run five times; Path B reports classification agreement separately). Mean selection agreement was **98%** (**9/10** cases identical across five repeats; **1/10** at **80%**, `TN3K_test_0009.jpg`, one repeat switching between `all_datasets` and `TN3K`, Dice range ≈ 0.017). All **10/10** cases were **close** tier (**Table R11**); no **easy** cases appeared in this subset, so we report the close stratum only.
- **Tier (`disagreement_tier`)**: for segmentation, candidates are ranked by inter-expert `average_agreement`; top1 minus top2 **≤ 0.10** → **close** (similar-quality candidates), **> 0.10** → **easy** (clear winner). The tier column in the stability table is **per-case routing difficulty**, not per-dataset stratification.

**Supporting material:** See **Table R11** (routing stability) and **Appendix A1** (LLM router specification and routing_log fields) at the end of this letter.

---

## Reviewer 2 — Comment 10 (R2.10)

**Reviewer comment:**
For FTC/PTC classification, the training cohort consists of classic PTC versus follicular-variant PTC, whereas the external test set uses FTC versus PTC. Follicular-variant PTC is not histologic FTC; training and testing therefore target different definitions.

**Response:**

- We describe FangDai evaluation as exploratory domain shift. **FangDai external** (**Table S5a**) and **five-fold OOF** (**Table S5b**) are as **Table R8** at the end of this letter. Label mismatch (FVPTC vs histologic FTC) is discussed in Limitations with clinical co-authors.

**Supporting material:** Full **Table S5** is **Table R8** at the end of this letter.

---

## Reviewer 2 — Comment 11 (R2.11)

**Reviewer comment:**
The LNM task used only 4,753 malignant images, while Table S5 shows validation with only 20 cases. Please clarify: (a) whether transfer or multitask learning was used; (b) data augmentation; (c) how overfitting was mitigated.

**Response:**

- We replaced the 20-case hold-out with patient-level stratified five-fold CV (4,753 images, 882 clusters; seed 42); OOF metrics are in **Table S5b** (ThyroidXAgent LNM AUROC **0.8710 ± 0.0550**, AUPRC **0.8929 ± 0.0537**). **LymphUs Center 2** external test is in **Table S5a** (ThyroidXAgent LNM AUROC **0.8642 ± 0.0550**, AUPRC **0.8808 ± 0.0537**).

**Supporting material:** Full **Table S5** is **Table R8** at the end of this letter.

---

## Reviewer 2 — Comment 12 (R2.12)

**Reviewer comment:**
For lymph-node metastasis prediction, the manuscript inconsistently uses overall LNM, lateral LNM, and CN0/CN1 labels, including primary thyroid lesions on ZJH-8K versus lymph-node images on LymphUs.

**Response:**

- We harmonized terminology and clustering rules (ZJH by year/name; LymphUs Center 1 one image per cluster). Clinical definitions were checked with pathology/clinical co-authors; statistical protocol is in **Table R8** at the end of this letter.

**Supporting material:** Full **Table S5** is **Table R8** at the end of this letter.

---

## Reviewer 2 — Comment 14 (R2.14)

**Reviewer comment:**
It is unclear whether all expert baselines were retrained on the same development data, evaluated with original weights, or tested zero-shot.

**Response:**

- All **supervised** baselines in **Tables S3/S4** were fine-tuned on the same stacked development sets (segmentation **dataset_4**: TN3K + ThyroidXL + PKTN + TN5K; classification **dataset_3**: TN3K + ThyroidXL + TN5K) from publicly available upstream weights—not thyroid zero-shot or off-the-shelf evaluation only. ThyroidXAgent full-stack results use the same development data; progressive stacking ablations are in **Table S6** separately. Vision–language baselines were zero-shot/API with fixed prompts and were not end-to-end trained on dataset_3. External cohorts (e.g. ZJH-8K, DDTI) were used **for testing only**. The complete training and inference protocol is in **Supplementary Table S[X]** at the end of this letter (to be reproduced in the revised SI).

**Supporting material:** See **Table R12** (Supplementary Table S[X], baseline training and inference protocol) at the end of this letter.

---

## Reviewer 2 — Comment 20 (R2.20)

**Reviewer comment:**
Thresholds for connected-component post-processing are not specified, including: (a) minimum component area; (b) whether nodules <5 mm may be removed; (c) how multiple nodules are separated.

**Response:**

- Methods now state ≥50 px components inside experts; reported Dice and radiomics use the same selected mask. Small-nodule statistics are in **Table R13** (mm_per_pixel=0.1 sensitivity assumption).

**Supporting material:** See **Table R13** (<5 mm nodule pipeline failure statistics) at the end of this letter.

---

## Reviewer 2 — Comment 21 (R2.21)

**Reviewer comment (editorial text; no sub-bullets):**
The AutoGluon-based radiomics branch is insufficiently described.

**Response:**

- We thank the reviewer for this comment. We expanded **Methods §4.3** in the revision and list reproducibility details in **Appendix A2** at the end of this letter (the revised Supplementary Information will contain the same text). At inference, **two-dimensional PyRadiomics** is extracted on the router-selected **selected mask** with **no additional connected-component refinement** before radiomics (the same mask underlies reported Dice/HD95; expert-internal ≥50 px rules are under **Reviewer 2 — Comment 20**). The **AutoGluon** tabular model was trained on stacked **dataset_3** with **GT masks** (17,774 images) and applied frozen at test time—**no** retraining or tuning on external tests. Path B may include AutoGluon in weighted soft voting (default weight 0.5); segmentation routing may include per-candidate radiomics-judge summaries in the LLM prompt (**Reviewer 2 — Comment 9**).

**Supporting material:** See **Appendix A2** (radiomics / AutoGluon specification) at the end of this letter.

---

## Reviewer 3 — Comment 3 (R3.3)

**Reviewer comment:**
The definition of "28,458 non-overlapping test cases" is unclear. Please describe the data hierarchy clearly, confirm patient-disjoint train/validation/test splits where applicable, and provide a simple flowchart relating patients, examinations, images/videos, lesions, and tasks.

**Response:**

- We address this together with **Reviewer 2 — Comment 3** and **Reviewer 1 — Comment 4** using the data-flow figure and cross-cohort **Table R6** and **Table R1** at the end of this letter.

**Supporting material:** See **Table R6** (dataflow) and **Table R1** (dHash screening) at the end of this letter.

---

# Supporting Figures and Tables for This Response

Tables and figures cited in the point-by-point responses above.；编号 **R1–R13**、**图 R1–R2** 与正文交叉引用一致。与修订稿 Supplementary Tables S3–S5 等同者保留原表号。

## Table R1. dHash 跨基础队列近重复筛查（Hamming ≤ 5）

| Cohort A | Cohort B | n (A) | n (B) | Pairs (H≤5) | H=0 | Near-dup only (1–5) |
| --- | --- | --- | --- | --- | --- | --- |
| TN3K（官方 train+val+test） | ZJH-8K | 5347 | 7958 | 1333 | 1156 | 177 |
| TN3K（test） | ZJH-8K | 614 | 7958 | 39 | 2 | 37 |

Each row is pairwise screening between two **source cohorts** (not a merged training-pool definition).

## Table R2. Supplementary Table S4 — AUROC

| 方法 | TN3K | ThyroidXL | TN5K | DDTI | ZJH-8K |
| --- | --- | --- | --- | --- | --- |
| ResNet-50 | 0.7681 (0.7276–0.8074) | 0.9029 (0.8845–0.9208) | 0.9321 (0.9132–0.9479) | 0.6155 (0.5334–0.6982) | 0.9125 (0.8965–0.9262) |
| RepViT | 0.8298 (0.7969–0.8598) | 0.9087 (0.8903–0.9269) | 0.8981 (0.8750–0.9194) | 0.7631 (0.6971–0.8244) | 0.8332 (0.8127–0.8549) |
| LSNet | 0.8094 (0.7738–0.8431) | 0.9178 (0.8999–0.9353) | 0.9091 (0.8862–0.9289) | 0.7749 (0.7065–0.8405) | 0.8455 (0.8253–0.8647) |
| UltraFedFM | 0.8474 (0.8137–0.8763) | 0.9231 (0.9062–0.9379) | 0.9277 (0.9087–0.9452) | 0.7819 (0.7095–0.8533) | 0.8718 (0.8536–0.8890) |
| MedSigLIP | 0.8293 (0.7968–0.8618) | 0.9122 (0.8937–0.9279) | 0.9084 (0.8864–0.9284) | 0.7486 (0.6671–0.8302) | 0.8481 (0.8291–0.8654) |
| BiomedCLIP | 0.7539 (0.7139–0.7901) | 0.7765 (0.7474–0.8027) | 0.8043 (0.7727–0.8344) | 0.6440 (0.5691–0.7253) | 0.7342 (0.7110–0.7578) |
| ThyroidXAgent | **0.8511 (0.8183–0.8824)** | **0.9312 (0.9142–0.9458)** | **0.9475 (0.9316–0.9612)** | **0.7937 (0.7107–0.8719)** | **0.9374 (0.9277–0.9472)** |

## Table R3. Supplementary Table S4 — AUPRC

| 方法 | TN3K | ThyroidXL | TN5K | DDTI | ZJH-8K |
| --- | --- | --- | --- | --- | --- |
| ResNet-50 | 0.6900 (0.6281–0.7469) | 0.8863 (0.8604–0.9089) | 0.9677 (0.9544–0.9793) | 0.5312 (0.4423–0.6586) | 0.9160 (0.8961–0.9322) |
| RepViT | 0.7518 (0.6946–0.8055) | 0.8851 (0.8553–0.9125) | 0.9525 (0.9340–0.9685) | 0.6133 (0.5149–0.7554) | 0.8790 (0.8569–0.8982) |
| LSNet | 0.7580 (0.7054–0.8065) | 0.9039 (0.8790–0.9284) | 0.9551 (0.9378–0.9703) | 0.6178 (0.5232–0.7696) | 0.8742 (0.8513–0.8944) |
| UltraFedFM | 0.7954 (0.7446–0.8392) | 0.9086 (0.8854–0.9293) | 0.9687 (0.9581–0.9784) | 0.6938 (0.5750–0.8561) | 0.9115 (0.8933–0.9271) |
| MedSigLIP | 0.7403 (0.6788–0.7968) | 0.8899 (0.8624–0.9142) | 0.9596 (0.9470–0.9708) | 0.6302 (0.5195–0.7877) | 0.8804 (0.8566–0.9019) |
| BiomedCLIP | 0.6439 (0.5767–0.7098) | 0.7224 (0.6752–0.7680) | 0.9095 (0.8880–0.9309) | 0.5452 (0.4600–0.6648) | 0.8014 (0.7740–0.8305) |
| ThyroidXAgent | **0.8001 (0.7347–0.8562)** | **0.9135 (0.8872–0.9351)** | **0.9786 (0.9707–0.9854)** | **0.7070 (0.5989–0.8649)** | **0.9544 (0.9440–0.9635)** |

Cluster-bootstrap 95% CIs (1000 resamples, seed 42).

## Table R4. Supplementary Table S3 — Cross-dataset nodule segmentation

Note: **Dice** 为 **%**（↑），**HD95** 为 **mm**（↓）；数值为点估计 **±** 95% CI 半宽（cluster bootstrap，1000 次，seed=42，图像级）。

**Dice（% ↑）**

| 方法 | TN3K | ThyroidXL | PKTN | TN5K | DDTI | ZJH-8K | RJH-7K |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TransUNet | 81.84 ± 1.62 | 85.75 ± 0.57 | 76.89 ± 3.56 | 78.54 ± 1.51 | 76.58 ± 1.67 | 80.72 ± 0.97 | 84.83 ± 0.37 |
| MedSegX | 83.93 ± 0.79 | 83.67 ± 0.92 | 80.63 ± 0.42 | 83.10 ± 0.48 | 75.12 ± 1.68 | 84.06 ± 0.39 | 85.40 ± 0.18 |
| MedSAM2 | 85.52 ± 1.43 | 87.94 ± 0.76 | **83.46 ± 2.60** | 86.30 ± 1.38 | 84.72 ± 1.26 | 86.29 ± 0.73 | 90.72 ± 0.21 |
| UltraFedFM | 81.18 ± 1.46 | 84.70 ± 0.53 | 75.31 ± 1.12 | 77.15 ± 1.40 | 75.57 ± 1.67 | 80.64 ± 0.84 | 83.12 ± 0.33 |
| ThyroidXAgent | **86.40 ± 1.25** | **87.65 ± 0.75** | **83.78 ± 2.18** | **83.95 ± 1.34** | **85.62 ± 1.07** | **94.30 ± 0.38** | **91.46 ± 0.14** |

**HD95（mm ↓）**

| 方法 | TN3K | ThyroidXL | PKTN | TN5K | DDTI | ZJH-8K | RJH-7K |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TransUNet | 27.27 ± 5.52 | 22.42 ± 1.34 | 26.88 ± 9.66 | 22.32 ± 3.43 | 17.12 ± 1.55 | 18.37 ± 0.75 | 18.81 ± 0.74 |
| MedSegX | 10.95 ± 0.64 | 11.07 ± 0.32 | 10.83 ± 0.70 | 11.76 ± 0.76 | 18.39 ± 1.65 | 10.96 ± 0.35 | 9.37 ± 0.18 |
| MedSAM2 | 11.51 ± 1.53 | 5.46 ± 0.44 | 10.56 ± 3.64 | 10.94 ± 1.12 | 10.06 ± 1.21 | 6.79 ± 0.57 | 2.92 ± 0.17 |
| UltraFedFM | 14.98 ± 2.10 | 8.10 ± 0.58 | 16.08 ± 1.67 | 14.96 ± 1.65 | 18.12 ± 1.47 | 8.69 ± 0.80 | 9.06 ± 0.38 |
| ThyroidXAgent | **10.31 ± 1.70** | **5.43 ± 0.53** | **9.01 ± 3.58** | **10.12 ± 1.23** | **9.24 ± 1.07** | **2.25 ± 0.39** | **1.92 ± 0.08** |

## Table R5. External-test calibration and referral（各 test 队列自身分位定阈，送复核约 5%–15%）

| 队列 | n | ECE | Brier | Referral % |
| --- | --- | --- | --- | --- |
| TN3K | 614 | 0.1825 | 0.1996 | 14.8% |
| TN5K | 1000 | 0.0661 | 0.0832 | 12.4% |
| ThyroidXL | 2090 | 0.0734 | 0.1101 | 10.9% |
| ZJH-8K | 7958 | 0.0971 | 0.1101 | 7.1% |
| DDTI | 349 | 0.0934 | 0.1098 | 5.2% |

## Figure R1. External-test reliability diagrams（五队列拼接；各队列自身分位定阈）

![External-test reliability diagrams（TN3K、TN5K、ThyroidXL、ZJH-8K、DDTI）](figures/reliability_panels.png)

## Figure R2. Risk–coverage（Operating points = referral % in Table R5）

![Risk–coverage曲线合图（五个外测队列；标点为各队列工作点）](figures/risk_coverage_panels.png)

## Table R6. Image-level dataflow (tabular)

**Dataflow figure (patient–examination–image–task): to be supplied.**

| 阶段 | 数据 / 阈值 |
| --- | --- |
| 模型开发训练 | TN3K、TN5K、ThyroidXL、PKTN 等公开队列合并（约 1.8 万图）→ DINO-UNet 等专家 |
| 验证集（850 张） | 专家选择、路由、拒答阈值（外测不调参） |
| AutoGluon 放射组学 | dataset_3、GT mask、17,774 训练样本 |
| 通用外测 | TN3K、TN5K、ThyroidXL、DDTI、ZJH-8K、RJH-7K、NHC 等 |
| LNM / FTC-PTC | ZJH 恶性子集 + LymphUs；外测 LymphUs C2 / FangDai |
| ZJH-8K 角色 | 良恶性/分割外测；专家未在 ZJH 训练；恶性子集仅用于 LNM/FTC 开发 |

## Table R7. Five-cohort malignancy summary means（两行：AUROC / AUPRC）

| 指标 | Unweighted macro mean | Weighted by test images |
| --- | --- | --- |
| AUROC | 0.9001 | 0.9286 |
| AUPRC | 0.8707 | 0.9533 |

## Table R8. Supplementary Table S5 — Malignant thyroid lesion subtasks

**表 S5a — Independent external test**（五折 OOF 定稿开发流程后，于**全开发集**训练模型后的单次外测；数值 ± 半宽与投稿 Supplementary Table S5 中对应专家单元格一致）

表注：**LNM**：LymphUs **Center 2**（**n=158**）。**FTC/PTC**：FangDai 等公开外测集（**n≈200**）。仅报告 **ThyroidXAgent**、**LLNM-Net**（LNM）、**Tiger-Model**（FTC/PTC）；与正文主结果一致。

| 方法 | LNM · AUROC ↑ | LNM · AUPRC ↑ | FTC/PTC · AUROC ↑ | FTC/PTC · AUPRC ↑ |
| --- | --- | --- | --- | --- |
| LLNM-Net | 0.7665 ± 0.0692 | 0.7363 ± 0.0849 | — | — |
| Tiger-Model | — | — | 0.7136 ± 0.0814 | 0.7117 ± 0.1101 |
| ThyroidXAgent | **0.8642 ± 0.0550** | **0.8808 ± 0.0537** | **0.8053 ± 0.0599** | **0.7863 ± 0.0793** |

**表 S5b — Development set: patient/cluster-stratified 5-fold OOF**（cluster bootstrap 95% CI，1000 次，seed=42；簇内图像概率算术平均后计算指标）

表注：替代原 **20 例**固定验证。**LNM**：合并开发 **4753** 图、**882** 簇。**FTC/PTC**：ZJH 恶性开发 **4756** 图、**722** 簇。**ThyroidXAgent**、**LLNM-Net**、**Tiger-Model** 同折 OOF（种子 42）。**RepViT** 至 **Gemini-2.5-Pro** 与投稿 Table S5 一致（未按五折 OOF 重跑）。— 表示该任务未评估。

| 方法 | LNM · AUROC ↑ | LNM · AUPRC ↑ | FTC/PTC · AUROC ↑ | FTC/PTC · AUPRC ↑ |
| --- | --- | --- | --- | --- |
| RepViT | 0.7905 ± 0.0676 | 0.8152 ± 0.0638 | 0.6419 ± 0.0839 | 0.6297 ± 0.0942 |
| LSNet | 0.5878 ± 0.0865 | 0.6301 ± 0.0875 | 0.4858 ± 0.0925 | 0.4845 ± 0.0908 |
| UltraFedFM | 0.7757 ± 0.0731 | 0.7902 ± 0.0845 | 0.7365 ± 0.0744 | 0.7582 ± 0.0824 |
| MedGemma | 0.8403 ± 0.0461 | 0.8585 ± 0.0566 | 0.6598 ± 0.0824 | 0.6142 ± 0.1056 |
| Qwen3-VL-8B-Instruct | 0.8070 ± 0.0632 | 0.8055 ± 0.0800 | 0.6056 ± 0.0866 | 0.5539 ± 0.1118 |
| GPT-5 | 0.8410 ± 0.0575 | 0.8629 ± 0.0533 | 0.1604 ± 0.0706 | 0.3638 ± 0.0847 |
| Gemini-2.5-Pro | 0.5414 ± 0.0736 | 0.5492 ± 0.0915 | 0.3324 ± 0.0872 | 0.4687 ± 0.0837 |
| LLNM-Net | 0.7960 ± 0.0655 | 0.7280 ± 0.0675 | — | — |
| Tiger-Model | — | — | 0.7500 ± 0.0730 | 0.7350 ± 0.0945 |
| ThyroidXAgent | **0.8710 ± 0.0550** | **0.8929 ± 0.0537** | **0.8165 ± 0.0599** | **0.8382 ± 0.0793** |

## Table R9. Malignancy: image-level vs patient-level（ThyroidXAgent，ZJH-8K 与 ThyroidXL）

Cluster-bootstrap 95% CI（1000 次，seed=42）。患者级：簇内恶性概率算术平均，标签组内 max。

| 队列 | 报告层级 | n | AUROC | 95% CI | AUPRC | 95% CI |
| --- | --- | --- | --- | --- | --- | --- |
| ZJH-8K | 图像 | 7958 图 / 1146 簇 | 0.9374 | 0.9277–0.9472 | 0.9544 | 0.9440–0.9635 |
| ZJH-8K | 患者 | 1146 | **0.9824** | 0.9762–0.9879 | **0.9899** | 0.9859–0.9932 |
| ThyroidXL | 图像 | 2090 图 / 739 簇 | 0.9312 | 0.9142–0.9458 | 0.9135 | 0.8872–0.9351 |
| ThyroidXL | 患者 | 739 | **0.9484** | 0.9326–0.9628 | **0.9355** | 0.9064–0.9592 |

## Table R10. Segmentation: within-patient mean Dice（ThyroidXAgent，补充）

| 队列 | n 患者 | Dice（患者级） | 95% CI |
| --- | --- | --- | --- |
| ZJH-8K | 1146 | 0.8398 | 0.8322–0.8470 |
| ThyroidXL | 739 | 0.8749 | 0.8675–0.8816 |

## Table R11. Routing stability（TN3K 稳定性子集，5 次重复）

| 病例 | Tier | 5 Choice agreement (5 runs) |
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

## Appendix A1. LLM router specification (response-letter excerpt; full text in revised SI)

*Production API calls use the Chinese prompts verbatim; faithful English translations are given below (Chinese text will be reproduced in the revised SI and in routing logs when prompts are archived).*

**Shared decoding (segmentation router, classification router, Path B arbitration)**

| Field | Value |
| --- | --- |
| API | OpenAI-compatible endpoint (DashScope) |
| base_url | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| model_name | `qwen3.8-27b` |
| temperature | `0.3` |
| max_tokens | `768` |
| enable_thinking | `false` |
| API key | Environment variable `DASHSCOPE_API_KEY` (not written to logs) |

**1. Segmentation router (Phase 3, `SegmentationAgent`)**

- Config: `enable_agent=true`; `include_disagreement_metrics_in_prompt=true`; `metadata_mode=full`; `radiomics_judge.enabled=true`; ensemble `top_k=1` (single-mask selection).
- **System (base, always used):**

```
You are a segmentation model selection agent. Choose the best mask from the JSON metrics in the user message.
Do not output chain-of-thought, Markdown, or any text outside JSON. The first character must be { and the last must be }.
Output a single line of JSON with "selected_model", "confidence" (0–1), and "reasoning" (fixed to "-"). Example: {"selected_model":"<name>", "confidence":0.9, "reasoning":"-"}
Priority: higher agreement_with_others; when experts disagree, lower mean_hd95_to_others; prefer masks whose radiomics_judge aligns with classification_anchor; morphology and device match are secondary.
```

- **System append — Path A** (independent classifiers agree; anchor example «malignant»):

```

[Classification anchor (key signal)]
Three independent classifiers (no mask required) unanimously label this image as malignant.
Use this anchor to judge each segmentation:
- Radiomics-judge class contradicting the anchor → the mask may cover the wrong ROI → substantially lower trust.
- Mask consistent with the anchor → bonus.
- If all masks’ radiomics classes contradict the anchor → select the mask with highest confidence and explain why.
```

- **System append — Path B** (no classification consensus):

```

[No classification anchor]
Independent classifiers disagree; no consensus.
Whole-image features are ambiguous. Prioritize:
1. Internal consistency of radiomics judges (similar class direction across masks → more trustworthy)
2. Morphologic plausibility (circularity 0.6–0.9, single connected component)
3. Device match and historical performance
```
- **User template**: optional disagreement summary + device/data lines +  
  `Below are outputs and quality assessments from {N} segmentation models:` + `{formatted_predictions_json}` +  
  `Which model provides the best segmentation? Output pure JSON only: {"selected_model": "<name>", "confidence": 0.95, "reasoning": "..."}`  
  (`formatted_predictions_json` includes per-model quality metrics, optional radiomics_judge, disagreement fields; built by code.)
- **Output JSON**: `{"selected_model": "<name>", "confidence": 0.0–1.0, "reasoning": "..."}`  
- **Non-LLM fallbacks**: `enable_agent=false` or parse/API failure → rule-based static selector (`static_fallback` / `llm_fallback`).

**2. Classification — standalone router (`run_cls.py`; no LLM if unanimous)**

- Unanimous top class → `method: unanimous`, no LLM call.
- **System (single selection, `top_k==1`)**:

```
From the predictions JSON in the user message, select the most trustworthy model.
No chain-of-thought or Markdown. Output one line of JSON: selected_model, selected_class, confidence (0–1), reasoning fixed to "-".
```

- **System (top-k fusion, current `top_k=5`)**: select five models for probability fusion; output `{"selected_models": [...], "reasoning": "..."}` (no `selected_class` / `confidence`).
- **User**: `Input device:` + per-model prediction JSON + question sentence (assembled by code).

**3. Classification — Path B (Phase 5, no consensus, `enable_agent=true`)**

- **System**:

```
You are a thyroid ultrasound diagnostic expert. Independent classifiers disagree on this image; synthesize all signals and make the final benign/malignant call.

You will receive:
1. Predictions from three independent classifiers (no mask; whole-image)
2. AutoGluon radiomics classification on the segmentation-selected mask (ROI-guided)
3. Reasoning from the segmentation agent for that mask

If all signals are ambiguous, bias conservatively toward malignant (prefer false positives over false negatives) but report low confidence.

Output pure JSON (no Markdown/code fences), wrapped in {}:
{"selected_class": "malignant", "confidence": 0.75, "reasoning": "..."}
Reasoning must cite specific confidence values. (Deployed labels use Chinese strings 良性/恶性.)
```

- **User**: single JSON string with `scenario`, `independent_models[]`, `autogluon_based_on_selected_mask`, `segmentation_decision`, `question` (structure in revised SI).
- **Output JSON**: `{"selected_class": "良性|恶性", "confidence": 0.0–1.0, "reasoning": "..."}` (stored as `selected_model: agent_path_b_llm`).

**4. Path A classification (consensus)**: `task: cls_path_a`, `method: classification_consensus`, logged only, no LLM.

**Structured routing_log (audit, ≥10 cases)**

Typical JSONL fields: `image_id`, `task` (e.g. `seg`, `cls`, `cls_path_b`), `disagreement_tier`, `llm_invoked`, `method`, `selected_model` / `selected_class`, `confidence`, `reasoning`, `candidates_summary`, `judge_summary` (if radiomics judge enabled), `llm_model` / `temperature` / `max_tokens`, timestamp `ts`; optional `prompts` (`system` / `user`) for verbatim reproduction in SI. The **10** cases in **Table R11** are drawn from the TN3K main pipeline and 5× stability audit logs; the revision will attach **≥10** de-identified exemplar records (same case IDs as Table R11).

## Table R12. Supplementary Table S[X] — Baseline training and inference protocol (complete)

**表注**

1. **dataset_3（分类开发）**：TN3K + ThyroidXL + TN5K 堆叠训练划分（与 OpenThyroid 公开 multitask 分类开发集一致）。
2. **dataset_4（分割开发）**：TN3K + ThyroidXL + PKTN + TN5K 堆叠训练划分（与 OpenThyroid 公开分割开发集一致）。
3. **监督基线默认协议**：在对应堆叠开发集上**全量微调**（自公开上游预训练权重出发），取验证集最佳权重用于 Table S3/S4 全部外测；**非**甲状腺零样本或仅用原始权重评估。
4. **分割基线外测**：图像 + **GT box/mask** 提示（`gt_mask` 协议），与 Table S3 一致。
5. **分类基线外测**：仅超声图像输入。
6. **ThyroidXAgent**：满堆叠 S3/S4 结果与上表使用相同堆叠开发数据；**Table S6** 逐级叠加消融另报。
7. **视觉–语言模型**：未在 dataset_3 端到端训练；厂商/公开权重；API 或冻结推理 + 固定 prompt。
8. 监督行与 **Table S3/S4** 出表模型一致；ZJH-8K、DDTI 等外测队列**不参与**开发微调。

| 模型 | 任务 | 甲状腺开发集 | 上游预训练 | 外测推理输入 |
| --- | --- | --- | --- | --- |
| BiomedCLIP | 分类 | dataset_3 | OpenCLIP BiomedCLIP；在 dataset_3_cls 上微调分类头 | 仅图像 |
| LSNet | 分类 | dataset_3 | ImageNet 预训练 LSNet | 仅图像 |
| MedSAM2 | 分割 | dataset_4 | SAM 2.1 Hiera | 图像 + GT box/mask（`gt_mask`） |
| MedSegX | 分割 | dataset_4 | SAM ViT-B + MedSegX 甲状腺适配器 | 图像 + GT box/mask（`gt_mask`） |
| MedSigLIP | 分类 | dataset_3 | Google MedSigLIP；在 dataset_3_cls 上部分微调 | 仅图像 |
| RepViT | 分类 | dataset_3 | ImageNet 预训练 RepViT | 仅图像 |
| ResNet-50 | 分类 | dataset_3 | ImageNet ResNet-50；dataset_3 微调 | 仅图像 |
| TransUNet | 分割 | dataset_4 | ImageNet-21k ViT-B/16（TransUNet 默认） | 图像 + GT box/mask（`gt_mask`） |
| UltraFedFM | 分类 | dataset_3 | ViT 骨干 + dataset_3_cls 微调 | 仅图像 |
| UltraFedFM | 分割 | dataset_4 | MAE / 联邦 FM + dataset_4 微调 | 图像 + GT box/mask（`gt_mask`） |
| ThyroidXAgent（分割路由） | 分割 | dataset_4 | DINOv3-UNet（ImageNet 级骨干） | 图像 → LLM 路由后的专家 mask |
| ThyroidXAgent（分类路由） | 分类 | dataset_3 | DINOv3 多任务骨干（dataset_3 微调） | 路由 mask + 图像（pipeline） |
| GPT-5 / Gemini / MedGemma / Qwen3-VL（若见于 S4） | 分类 | —（未微调） | 厂商/公开 VLM 权重 | 图像 ± 固定文本 prompt（零样本或 API） |

## Table R13. Nodules <5 mm — Pipeline failure statistics

| 队列 | n 匹配 | <5.0 mm (N) | 失败 (M) | 小结节子集 mean Dice | GT 等价径 <50 px |
|------|--------|------------------|----------|----------------------|------------------|
| ddti_seg | 637 | 54 | 1 | 0.734 | 54 |
| pktn | 150 | 15 | 1 | 0.741 | 15 |
| rjh7k | 7288 | 366 | 1 | 0.766 | 366 |
| thyroidxl | 2090 | 0 | 0 | — | 0 |
| tn3k | 614 | 68 | 2 | 0.771 | 68 |
| tn5k | 1000 | 103 | 12 | 0.696 | 103 |
| zjh8k | 7958 | 1001 | 44 | 0.818 | 1001 |

## Appendix A2. Radiomics / AutoGluon specification (response-letter excerpt)

**1. Pipeline placement**

1. Phase 3 segmentation routing yields the **selected mask**.  
2. **No** radiomics-specific connected-component post-processing; inference and training share the same 2D PyRadiomics settings.  
3. Phase 4: PyRadiomics features → **AutoGluon-Tabular** inference; malignancy probability is stored in the evidence bank and used for routing / Path B.  
4. Optional **SHAP** feature attribution for the tabular model (consistent with the architecture figure).

**2. PyRadiomics**

| Item | Setting |
| --- | --- |
| Package version | **pyradiomics 3.1.0** (training environment) |
| Parameter set | Shared 2D PyRadiomics configuration for train and inference (full parameter table in revised SI) |
| Geometry | Forced 2D; mask correction; resampling spacing **(1.0, 1.0)** px (isotropic assumption) |
| Intensity | Normalization scale **100**; histogram binWidth **25**; symmetrical GLCM |
| Image filters | Original, Wavelet, LoG (σ=2, 4), Square, SquareRoot, Logarithm, Exponential, Gradient |
| Feature classes | Full **shape2D**; **GLCM** and preset texture families |
| Input | Grayscale ultrasound; mask foreground = positive pixels |
| Feature dimension | **100** radiomics columns at extraction; **86** numeric features used by AutoGluon (14 sparse glszm columns dropped internally) |

**3. AutoGluon-Tabular**

| Item | Setting |
| --- | --- |
| Package version | **1.4.0** |
| Preset | best_quality |
| Time limit | **600 s** (DyStack + main fit) |
| Bagging | **8-fold**, **1** stack level |
| Optimisation metric | Binary **ROC-AUC** |
| Training samples | **17,774** images (benign/malignant labels) |
| Training masks | **GT masks** on stacked **dataset_3** (same development stack as supervised Table S4 classification) |
| Deployed model | AutoGluon **weighted ensemble** (bagged LightGBM, CatBoost, neural nets; auto-selected on development data) |
| External inference | Frozen ensemble from development training; **no** updating on external tests |

**4. Distinction from R2.20 (note)**

Connected-component rules (≥50 px inside experts, 5×5 closing, largest component on ensemble masks) apply to **DINO expert/ensemble outputs**, **not** an extra CCA step before radiomics.