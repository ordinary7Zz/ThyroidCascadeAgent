# Response to reviewers (draft, English)

Manuscript: ThyroidXAgent (Nature Communications, major revision).
Per point: **Reviewer comment** → **Response** → **Supporting tables and figures**.

## Deferred

- R1.2, R2.8, R3.1 — routing and component ablations (pending supplementary experiments).
- R1.5–R1.6, R2.13, R2.16–R2.19, R3.4–R3.5 — report generation and reader studies.
- R2.5 — reference standards and annotation protocols. R2.6 — NHC-MISD-TUS center-level analyses.
- R2.15, R2.22–R2.23, R2 code — ethics, language, TI-RADS, code release.
- R3.2 — routing metadata ablation.

---

## Reviewer 1 — Comment 1 (R1.1)

**Reviewer comment:**
Segmentation and classification results are largely reported at the image level. The authors should clarify patient- and examination-level splits, cross-dataset deduplication, and whether multiple frames or views from the same patient appear across splits. Patient-level re-analysis and cluster-aware confidence intervals would strengthen confidence in the reported performance.

**Response:**

- We thank the reviewer for this important point. We revised our statistical reporting as follows.
- Independence and near-duplicates. We screened **pairwise across source cohorts** (TN3K, TN5K, ThyroidXL, DDTI, PKTN, ZJH-8K, etc.) using dHash (Hamming ≤ 5; table below). For the ZJH–TN3K question (R2.4): TN3K (official train+val+test) vs ZJH-8K shows **1156** H=0 pairs; TN3K **official test** vs ZJH-8K shows **2** H=0 pairs. Cluster definitions. Where patient IDs are available (ZJH-8K, ThyroidXL), we use patient-level clusters; for cohorts without IDs, we use one image per cluster. Bootstrap CIs (1000 resamples, seed 42) are cluster-aware.
- Patient-level classification. For ZJH-8K and ThyroidXL we report patient-level AUROC/AUPRC after aggregating image probabilities (arithmetic mean within patient).
- Cluster-bootstrap confidence intervals. We recomputed 95% CIs using 1000 cluster bootstrap resamples (seed 42). The embedded tables reproduce revised **Table S4** in full manuscript layout (all supervised classifiers and ThyroidXAgent × five test cohorts; AUROC and AUPRC blocks). Table S3 (segmentation) is updated similarly in the supplement (Methods §4.6). DDTI classification uses n=349 labeled images.

**Supporting tables and figures**

#### dHash cross-cohort near-duplicate screening (Hamming ≤ 5)

| Cohort A | Cohort B | n (A) | n (B) | Pairs (H≤5) | H=0 | Near-only (1–5) |
| --- | --- | --- | --- | --- | --- | --- |
| TN3K (train+val+test) | ZJH-8K | 5347 | 7958 | 1333 | 1156 | 177 |
| TN3K (test) | ZJH-8K | 614 | 7958 | 39 | 2 | 37 |

Each row is a pairwise screen between two **standalone source cohorts** (not our internal merged training pool).

#### Draft Table S4 — AUROC

| Method | TN3K | ThyroidXL | TN5K | DDTI | ZJH-8K |
| --- | --- | --- | --- | --- | --- |
| ResNet-50 | 0.7681 (0.7276–0.8074) | 0.9029 (0.8845–0.9208) | 0.9321 (0.9132–0.9479) | 0.6155 (0.5334–0.6982) | 0.9125 (0.8965–0.9262) |
| RepViT | 0.8298 (0.7969–0.8598) | 0.9087 (0.8903–0.9269) | 0.8981 (0.8750–0.9194) | 0.7631 (0.6971–0.8244) | 0.8332 (0.8127–0.8549) |
| LSNet | 0.8094 (0.7738–0.8431) | 0.9178 (0.8999–0.9353) | 0.9091 (0.8862–0.9289) | 0.7749 (0.7065–0.8405) | 0.8455 (0.8253–0.8647) |
| UltraFedFM | 0.8474 (0.8137–0.8763) | 0.9231 (0.9062–0.9379) | 0.9277 (0.9087–0.9452) | 0.7819 (0.7095–0.8533) | 0.8718 (0.8536–0.8890) |
| MedSigLIP | 0.8293 (0.7968–0.8618) | 0.9122 (0.8937–0.9279) | 0.9084 (0.8864–0.9284) | 0.7486 (0.6671–0.8302) | 0.8481 (0.8291–0.8654) |
| BiomedCLIP | 0.7539 (0.7139–0.7901) | 0.7765 (0.7474–0.8027) | 0.8043 (0.7727–0.8344) | 0.6440 (0.5691–0.7253) | 0.7342 (0.7110–0.7578) |
| ThyroidXAgent | 0.8511 (0.8183–0.8824) | 0.9312 (0.9142–0.9458) | 0.9475 (0.9316–0.9612) | 0.7937 (0.7107–0.8719) | 0.9374 (0.9277–0.9472) |

#### Draft Table S4 — AUPRC

| Method | TN3K | ThyroidXL | TN5K | DDTI | ZJH-8K |
| --- | --- | --- | --- | --- | --- |
| ResNet-50 | 0.6900 (0.6281–0.7469) | 0.8863 (0.8604–0.9089) | 0.9677 (0.9544–0.9793) | 0.5312 (0.4423–0.6586) | 0.9160 (0.8961–0.9322) |
| RepViT | 0.7518 (0.6946–0.8055) | 0.8851 (0.8553–0.9125) | 0.9525 (0.9340–0.9685) | 0.6133 (0.5149–0.7554) | 0.8790 (0.8569–0.8982) |
| LSNet | 0.7580 (0.7054–0.8065) | 0.9039 (0.8790–0.9284) | 0.9551 (0.9378–0.9703) | 0.6178 (0.5232–0.7696) | 0.8742 (0.8513–0.8944) |
| UltraFedFM | 0.7954 (0.7446–0.8392) | 0.9086 (0.8854–0.9293) | 0.9687 (0.9581–0.9784) | 0.6938 (0.5750–0.8561) | 0.9115 (0.8933–0.9271) |
| MedSigLIP | 0.7403 (0.6788–0.7968) | 0.8899 (0.8624–0.9142) | 0.9596 (0.9470–0.9708) | 0.6302 (0.5195–0.7877) | 0.8804 (0.8566–0.9019) |
| BiomedCLIP | 0.6439 (0.5767–0.7098) | 0.7224 (0.6752–0.7680) | 0.9095 (0.8880–0.9309) | 0.5452 (0.4600–0.6648) | 0.8014 (0.7740–0.8305) |
| ThyroidXAgent | 0.8001 (0.7347–0.8562) | 0.9135 (0.8872–0.9351) | 0.9786 (0.9707–0.9854) | 0.7070 (0.5989–0.8649) | 0.9544 (0.9440–0.9635) |

Cluster-bootstrap 95% CIs (1000 resamples, seed 42). VLM rows follow submitted layout; CIs updated in final supplement.


---

## Reviewer 1 — Comment 3 (R1.3)

**Reviewer comment:**
Although overall performance on the private multi-center cohort is encouraging, performance varies substantially across centers (e.g., much lower nodule segmentation at some centers). The authors should examine associations with scanner type, image quality, case mix, and annotation protocols, and define calibration, abstention, or mandatory human review for low-confidence cases.

**Response:**

- We agree that center heterogeneity matters. Center-level meta-analyses for NHC-MISD-TUS (Reviewer 2, Comment 6) will be reported separately when center metadata are finalized (see our response to Reviewer 2, Comment 6). Here we address calibration and abstention for the five benign–malignant classification test cohorts with pathology labels.
- We fixed abstention thresholds on the OpenThyroid validation merge (n=875 images, same non-LLM inference protocol as testing), using vote entropy, top-2 margin, and minimum pairwise segmentation IoU among experts. Thresholds are the 95th percentile of each score on validation (no test-set tuning).
- On the labeled validation subset we report pooled ECE and Brier (see embedded table and reliability figure).
- On TN3K, TN5K, ThyroidXL, ZJH-8K, and DDTI test sets we report ECE, Brier, abstention rates, and risk–coverage curves (below). Under fixed **validation 95th-percentile** joint thresholds, four main public test cohorts show **~43–48%** flagged; **DDTI** is **3.7%** (same thresholds; tighter uncertainty on that cohort).
- A **high abstention rate is not tantamount to poor performance**: thresholds implement the reviewer-requested **conservative human-review policy** (flag if vote entropy, top-2 margin, or minimum expert seg IoU exceeds its validation 95th percentile; no test tuning). Risk–coverage curves show **falling risk on the retained (non-abstained) subset** as coverage decreases. We frame this as retrospective **automation plus mandatory review**, not full autonomous deployment; clinical handling of flagged cases is noted in Limitations/Discussion.

**Supporting tables and figures**

#### Validation calibration

| n | ECE | Brier |
| --- | --- | --- |
| 725 | 0.0881 | 0.0777 |


![Validation reliability diagram](/mnt/wangbd8/workspace/ThyroidAgent/ThyroidCascadeAgent/output/b8/fit_q95/reliability_val.png)

#### Test calibration & abstention (q=0.95 on validation)

| Cohort | n | ECE | Brier | Flagged % |
| --- | --- | --- | --- | --- |
| TN3K | 614 | 0.1825 | 0.1996 | 48.2% |
| TN5K | 1000 | 0.0661 | 0.0832 | 44.4% |
| ThyroidXL | 2090 | 0.0734 | 0.1101 | 44.9% |
| ZJH-8K | 7958 | 0.0971 | 0.1101 | 43.1% |
| DDTI | 349 | 0.0934 | 0.1098 | 3.7% |


![Risk–coverage panels (subplot titles: TN3K, TN5K, ThyroidXL, ZJH-8K, DDTI)](/mnt/wangbd8/workspace/ThyroidAgent/ThyroidCascadeAgent/output/b8/figures/risk_coverage_panels.png)


---

## Reviewer 1 — Comment 4 (R1.4)

**Reviewer comment:**
ZJH-8K is described as an external test set for segmentation and benign–malignant classification, while its malignant images are also used to develop LNM and FTC/PTC tasks. The manuscript should provide a complete data-flow diagram showing, for each component, which data were used for training, validation, threshold selection, and testing.

**Response:**

- We agree. Segmentation and generic benign–malignant experts were not trained on ZJH-8K. The malignant subset of ZJH-8K is used only for task-specific LNM and FTC/PTC development, with external testing on LymphUs Center 2 and FangDai, respectively.
- We provide the image-arm data-flow figure below (to be numbered Supplementary Figure S-X in the revision).

**Supporting tables and figures**

Source: [`DATAFLOW_FIGURE.mmd`](/mnt/wangbd8/workspace/ThyroidAgent/ThyroidCascadeAgent/docs/revision/b11_b12/DATAFLOW_FIGURE.mmd) (export PNG when available).
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
- Benign–malignant classification means (abstract, §2.2): corrected to unweighted macro-averages over five Table S4 cohorts (embedded table). Figure 3b axis labels were swapped and are corrected to match Table S5.
- LNM training pool size corrected to 4,936 images (4,756 ZJH-8K malignant + 180 LymphUs Center 1); five-fold CV uses 4,753 images in the combined development manifest (Table S5 excerpt below).

**Supporting tables and figures**

#### Macro-averaged BM classification means (AUROC / AUPRC rows)

| Metric | Unweighted macro mean | Weighted by test image count |
| --- | --- | --- |
| AUROC | 0.9001 | 0.9228 |
| AUPRC | 0.8705 | 0.9533 |

#### Draft Table S5 excerpt: ThyroidXAgent LNM / FTC (interim OOF)

| Task | n clusters | AUROC | 95% CI | AUPRC | 95% CI |
| --- | --- | --- | --- | --- | --- |
| LNM (ThyroidXAgent OOF) | 882 | 0.718 | 0.678–0.754 | 0.598 | 0.536–0.655 |
| FTC/PTC (ThyroidXAgent OOF) | 722 | 0.521 | 0.442–0.602 | 0.109 | 0.076–0.160 |


---

## Reviewer 2 — Comment 2 (R2.2)

**Reviewer comment:**
Many analyses are reported at the image level although the same patient, examination, or nodule may have multiple images (e.g., ZJH-8K contains 7,958 images from 1,149 patients). Treating correlated images as independent may yield overly narrow confidence intervals. The authors should use patient- or examination-level bootstrap resampling and report patient-level performance for clinically meaningful classification tasks.

**Response:**

- We agree. All segmentation and classification confidence intervals in Tables S3–S5 now use cluster bootstrap (1000 resamples, seed 42). For ZJH-8K and ThyroidXL we aggregate image probabilities within patient/cluster before AUROC/AUPRC; ZJH-8K example below.

**Supporting tables and figures**

#### ZJH-8K classification: image-level vs patient-level (example)

| Level | n | Image-level cls AUROC (95% CI) | Patient-level AUROC |
| --- | --- | --- | --- |
| Image-level | 7958 | 0.937 (0.928–0.947) | — |
| Patient-level | 1149 patients | — | 0.982 |


---

## Reviewer 2 — Comment 3 (R2.3)

**Reviewer comment:**
Please clarify why 28,458 observations are described as "non-overlapping test cases", as this number appears to combine 19,737 test images with 8,721 NHC-MISD-TUS cases.

**Response:**

- The reviewer is correct: 28,458 sums 19,737 test images from seven segmentation/classification cohorts and 8,721 NHC-MISD-TUS cases. We replaced this phrase with stratified counts; the image-arm data-flow figure (below) summarizes splits.

**Supporting tables and figures**

Source: [`DATAFLOW_FIGURE.mmd`](/mnt/wangbd8/workspace/ThyroidAgent/ThyroidCascadeAgent/docs/revision/b11_b12/DATAFLOW_FIGURE.mmd) (export PNG when available).
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

- ZJH-8K and TN3K were collected at the same hospital but serve different study roles; we softened “external center” wording and report **pairwise dHash screens between standalone source cohorts** (same table as R1.1). TN3K (train+val+test) vs ZJH-8K: **1156** H=0 pairs; TN3K **official test** vs ZJH-8K: **2** H=0 pairs. Patient-level overlap is discussed in Methods/Limitations where IDs exist.

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

- All cross-cohort “means” for benign–malignant classification are unweighted macro-averages over five Table S4 test cohorts. Corrected values and per-cohort point estimates are in the embedded tables below.

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

- We provide router specifications, structured routing logs, and five-repeat stability results in the embedded tables and excerpt below.

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

Router spec: [`router_spec.md`](/mnt/wangbd8/workspace/ThyroidAgent/ThyroidCascadeAgent/docs/supplementary/router_spec.md)


---

## Reviewer 2 — Comment 10 (R2.10)

**Reviewer comment:**
For FTC/PTC classification, the training cohort consists of classic PTC versus follicular-variant PTC, whereas the external test set uses FTC versus PTC. Follicular-variant PTC is not histologic FTC; training and testing therefore target different definitions.

**Response:**

- We describe FangDai evaluation as exploratory domain shift. Internal five-fold OOF for ThyroidXAgent is in the embedded Table S5 excerpt (interim DINO multitask OOF; full-stack fusion may update numbers). FangDai external results will follow development-set retraining.

**Supporting tables and figures**

#### Draft Table S5 excerpt: ThyroidXAgent LNM / FTC (interim OOF)

| Task | n clusters | AUROC | 95% CI | AUPRC | 95% CI |
| --- | --- | --- | --- | --- | --- |
| LNM (ThyroidXAgent OOF) | 882 | 0.718 | 0.678–0.754 | 0.598 | 0.536–0.655 |
| FTC/PTC (ThyroidXAgent OOF) | 722 | 0.521 | 0.442–0.602 | 0.109 | 0.076–0.160 |


---

## Reviewer 2 — Comment 11 (R2.11)

**Reviewer comment:**
The LNM task used only 4,753 malignant images, while Table S5 shows validation with only 20 cases. Please clarify: (a) whether transfer or multitask learning was used; (b) data augmentation; (c) how overfitting was mitigated.

**Response:**

- We replaced the 20-case hold-out with patient-level stratified five-fold CV (4,753 images, 882 clusters; seed 42). Out-of-fold metrics with cluster-bootstrap CIs are in the embedded Table S5 excerpt.

**Supporting tables and figures**

#### Draft Table S5 excerpt: ThyroidXAgent LNM / FTC (interim OOF)

| Task | n clusters | AUROC | 95% CI | AUPRC | 95% CI |
| --- | --- | --- | --- | --- | --- |
| LNM (ThyroidXAgent OOF) | 882 | 0.718 | 0.678–0.754 | 0.598 | 0.536–0.655 |
| FTC/PTC (ThyroidXAgent OOF) | 722 | 0.521 | 0.442–0.602 | 0.109 | 0.076–0.160 |


---

## Reviewer 2 — Comment 12 (R2.12)

**Reviewer comment:**
For lymph-node metastasis prediction, the manuscript inconsistently uses overall LNM, lateral LNM, and CN0/CN1 labels, including primary thyroid lesions on ZJH-8K versus lymph-node images on LymphUs.

**Response:**

- We harmonized terminology and clustering rules (ZJH by year/name; LymphUs Center 1 one image per cluster). Clinical definitions will be finalized with co-authors; statistical protocol matches Table S5 below.

**Supporting tables and figures**

#### Draft Table S5 excerpt: ThyroidXAgent LNM / FTC (interim OOF)

| Task | n clusters | AUROC | 95% CI | AUPRC | 95% CI |
| --- | --- | --- | --- | --- | --- |
| LNM (ThyroidXAgent OOF) | 882 | 0.718 | 0.678–0.754 | 0.598 | 0.536–0.655 |
| FTC/PTC (ThyroidXAgent OOF) | 722 | 0.521 | 0.442–0.602 | 0.109 | 0.076–0.160 |


---

## Reviewer 2 — Comment 14 (R2.14)

**Reviewer comment:**
It is unclear whether all expert baselines were retrained on the same development data, evaluated with original weights, or tested zero-shot.

**Response:**

- We added Supplementary Table S[X] documenting baseline training and inference protocols (excerpt embedded below).

**Supporting tables and figures**

#### Baseline training protocol (Supp. Table S[X] excerpt)

| model | task | protocol | upstream_pretraining | thyroid_development_set | checkpoint_for_tables | inference_input |
| --- | --- | --- | --- | --- | --- | --- |
| BiomedCLIP | classification | full_finetune_on_stacked_dev | OpenCLIP BiomedCLIP + dataset_3_cls head finetune | OpenThyroid stacked cls development: dataset_3 (TN3K + ThyroidXL + TN5K); train_val_test/Superimposed_multitask/dataset_3_cls/train (ResNet-50 / DINO multitask: dataset_3 with JSON, same image count) | ./infer_biomedclip/checkpoints/BM_2cls/best_model.pth | US image (image_only) |
| LSNet | classification | full_finetune_on_stacked_dev | ImageNet-pretrained LSNet | OpenThyroid stacked cls development: dataset_3 (TN3K + ThyroidXL + TN5K); train_val_test/Superimposed_multitask/dataset_3_cls/train (ResNet-50 / DINO multitask: dataset_3 with JSON, same image count) | ./infer_lsnet/checkpoints/checkpoint_best.pth | US image (image_only) |
| MedSAM2 | segmentation | full_finetune_on_stacked_dev | SAM2.1 Hiera pretrained | OpenThyroid stacked seg development: dataset_4 (TN3K + ThyroidXL + PKTN + TN5K); train under train_val_test/Superimposed_experiment/dataset_4/train | ./infer_medsam2/checkpoints/Nodule/checkpoint_15.pt | US image + GT box/mask for expert (gt_mask) |
| MedSegX | segmentation | full_finetune_on_stacked_dev | SAM ViT-B + MedSegX thyroid adapter | OpenThyroid stacked seg development: dataset_4 (TN3K + ThyroidXL + PKTN + TN5K); train under train_val_test/Superimposed_experiment/dataset_4/train | ./infer_medsegx/checkpoints/Nodule/model_best.pth | US image + GT box/mask for expert (gt_mask) |
| MedSigLIP | classification | full_finetune_on_stacked_dev | Google MedSigLIP + partial finetune on dataset_3_cls | OpenThyroid stacked cls development: dataset_3 (TN3K + ThyroidXL + TN5K); train_val_test/Superimposed_multitask/dataset_3_cls/train (ResNet-50 / DINO multitask: dataset_3 with JSON, same image count) | ./infer_medsiglip/checkpoints/BM_2cls/best_model.pt | US image (image_only) |
| RepViT | classification | full_finetune_on_stacked_dev | ImageNet-pretrained RepViT | OpenThyroid stacked cls development: dataset_3 (TN3K + ThyroidXL + TN5K); train_val_test/Superimposed_multitask/dataset_3_cls/train (ResNet-50 / DINO multitask: dataset_3 with JSON, same image count) | ./infer_repvit/checkpoints/BM/repvit_m1_0_224_0.025_0.001_0.25/checkpoint_best.pth | US image (image_only) |
| ResNet-50 | classification | full_finetune_on_stacked_dev | ImageNet ResNet-50 + dataset_3 finetune | OpenThyroid stacked cls development: dataset_3 (TN3K + ThyroidXL + TN5K); train_val_test/Superimposed_multitask/dataset_3_cls/train (ResNet-50 / DINO multitask: dataset_3 with JSON, same image count) | ./infer_resnet50/checkpoints/resnet50_thyroid_cls_epoch_50.pth | US image (image_only) |
| TransUNet | segmentation | full_finetune_on_stacked_dev | ImageNet-21k ViT-B/16 (TransUNet default) | OpenThyroid stacked seg development: dataset_4 (TN3K + ThyroidXL + PKTN + TN5K); train under train_val_test/Superimposed_experiment/dataset_4/train | ./infer_transunet/checkpoints/Nodule/epoch_49.pth | US image + GT box/mask for expert (gt_mask) |
| … | … | *（其余行见源文件）* |

源文件：[`baseline_training_protocol.md`](/mnt/wangbd8/workspace/ThyroidAgent/ThyroidCascadeAgent/docs/revision/b10/tables/baseline_training_protocol.md)


---

## Reviewer 2 — Comment 20 (R2.20)

**Reviewer comment:**
Thresholds for connected-component post-processing are not specified, including: (a) minimum component area; (b) whether nodules <5 mm may be removed; (c) how multiple nodules are separated.

**Response:**

- Methods now state ≥50 px components inside experts; reported Dice and radiomics use the same selected mask. Small-nodule statistics are in the embedded table (mm_per_pixel=0.1 sensitivity assumption).

**Supporting tables and figures**

#### R2.20(b) nodules <5 mm — pipeline failures

| 队列 | n 匹配 | <5.0 mm (N) | 失败 (M) | 小结节子集 mean Dice | GT 等价径 <50 px |
|------|--------|------------------|----------|----------------------|------------------|
| ddti_seg | 637 | 54 | 1 | 0.734 | 54 |
| pktn | 150 | 15 | 1 | 0.741 | 15 |
| rjh7k | 7288 | 366 | 1 | 0.766 | 366 |
| thyroidxl | 2090 | 0 | 0 | — | 0 |
| tn3k | 614 | 68 | 2 | 0.771 | 68 |
| tn5k | 1000 | 103 | 12 | 0.696 | 103 |
| zjh8k | 7958 | 1001 | 44 | 0.818 | 1001 |

源文件：[`R2_20_SUMMARY.md`](/mnt/wangbd8/workspace/ThyroidAgent/ThyroidCascadeAgent/docs/revision/b11_b12/tables/R2_20_SUMMARY.md)


---

## Reviewer 2 — Comment 21 (R2.21)

**Reviewer comment:**
The AutoGluon-based radiomics branch is insufficiently described.

**Response:**

- We expanded Methods §4.3 and the Supplementary radiomics specification; key parameters and an example reliability figure are embedded below.

**Supporting tables and figures**

#### Radiomics branch summary

规范全文：[`reproducibility_radiomics.md`](/mnt/wangbd8/workspace/ThyroidAgent/ThyroidCascadeAgent/docs/reproducibility_radiomics.md)。

![TN3K test reliability diagram (example)](/mnt/wangbd8/workspace/ThyroidAgent/ThyroidCascadeAgent/output/b8/cohorts_q95/tn3k/reliability_test.png)


---

## Reviewer 3 — Comment 3 (R3.3)

**Reviewer comment:**
The definition of "28,458 non-overlapping test cases" is unclear. Please describe the data hierarchy clearly, confirm patient-disjoint train/validation/test splits where applicable, and provide a simple flowchart relating patients, examinations, images/videos, lesions, and tasks.

**Response:**

- We aligned this response with R2.3 and R1.4 using the embedded data-flow figure and cross-cohort dHash table (R1.1).

**Supporting tables and figures**

Source: [`DATAFLOW_FIGURE.mmd`](/mnt/wangbd8/workspace/ThyroidAgent/ThyroidCascadeAgent/docs/revision/b11_b12/DATAFLOW_FIGURE.mmd) (export PNG when available).
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
