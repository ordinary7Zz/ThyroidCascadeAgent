# Radiomics / AutoGluon branch (B11, R2.21)

Inference in this repo matches training-side `pyradiomics_train` / `extract_radiomics_2d.py`.

## Pipeline placement

1. Segmentation router selects **`selected_masks`** (Phase 3).
2. **No connected-component refinement** is applied before radiomics (`radiomics_judge/feature_extractor.py`).
3. Phase 4: PyRadiomics features → **AutoGluon TabularPredictor** (`radiomics_judge/judge.py`, `pipeline/cascade.py`).
4. Reported **Dice / HD95** use the same **selected** masks (`pipeline/evaluate.py`).

## PyRadiomics

| Item | Value |
|------|--------|
| Package (training env) | **pyradiomics 3.1.0** (see `Classification_Agent/weights/dataset_3/autogluon_model_20260106_215755/metadata.json`) |
| Config file | `radiomics_judge/radiomics_2d.yaml` (same as `pyradiomics_train/radiomics_2d.yaml`) |
| Geometry | `force2D: true`, `force2Ddimension: 0`, `correctMask: true`, spacing **(1.0, 1.0)** in code |
| Intensity | `normalize: true`, `normalizeScale: 100`, `binWidth: 25`, `symmetricalGLCM: true` |
| Filters | Original, Wavelet, LoG (σ=2,4), Square, SquareRoot, Logarithm, Exponential, Gradient |
| Feature classes | Full **shape2D**; **GLCM** with listed texture names (see yaml) |

Grayscale: PIL `convert("L")` (ITU-R 601-2). Mask foreground: `mask > 0`.

Inference aligns SimpleITK geometry with `msk_sitk.CopyInformation(img_sitk)` after `SetSpacing` (same as fixing systematic `correctMask` resample warnings when image is float32 and mask is uint8).

Training extraction yields **100** radiomics columns; AutoGluon preprocessing uses **86** numeric features at fit time (14 sparse/unused glszm columns dropped internally).

## AutoGluon

| Item | Value |
|------|--------|
| Version | **1.4.0** |
| Model directory (default in configs) | `../Classification_Agent/weights/dataset_3/autogluon_model_20260106_215755` |
| Training log | `.../logs/predictor_log.txt` |
| Preset | `best_quality` |
| Time limit | **600 s** total (DyStack + main fit) |
| Bagging | **8-fold** (`num_bag_folds=8`), **1** stack level |
| Metric | **roc_auc** (binary malignancy) |
| Training rows | **17,774** images, label column `label` |
| Training features | GT masks on stacked **`dataset_3`** (see `Superimposed_multitask/dataset_3` paths in Classification_Agent docs) |
| Deployed ensemble | `WeightedEnsemble_L3` (LightGBM / CatBoost / NeuralNet bagged bases; see `leaderboard.csv`) |

Load at inference: `TabularPredictor.load(model_dir, require_py_version_match=False)`.

## Config hook

```yaml
radiomics_judge:
  enabled: true
  model_dir: ../Classification_Agent/weights/dataset_3/autogluon_model_20260106_215755
  radiomics_params: null   # → default radiomics_2d.yaml
```

Path B classification may include AutoGluon in weighted soft voting (`radiomics_judge.voting_weight`, default 0.5).

## Segmentation post-processing (not radiomics CCA)

- Per-expert DINO-UNet (`segmentation/dino_unet_model.py`): threshold **0.5**, drop CC **&lt; 50 px**, 5×5 ellipse closing.
- Optional ensemble mask (`segmentation/agent.py`): threshold **0.5**, keep **largest** connected component only.

These apply to expert/ensemble outputs; they are **not** an extra radiomics-only CCA step.
