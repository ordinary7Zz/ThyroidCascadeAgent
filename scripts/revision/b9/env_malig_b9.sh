# shellcheck disable=SC2034
# Source from orchestration scripts:  source "$(dirname "$0")/env_malig_b9.sh"
#
# Malignant subtasks (B9): datasets match pyradiomics binary_class/my_run.md
#   LNM  -> LymphUs fake + pred mask (LymphUs_train/test_labels.json)
#   FTC  -> filtered malignant cropped JSON (train/test_labels_filtered_by_csv.json)
# Metrics: image-level CV and external eval (B9_CV_CLUSTER=filename / image).

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
THYROID_AGENT="$(cd "$REPO_ROOT/.." && pwd)"

B9_MY_RUN_DATA="${B9_MY_RUN_DATA:-$REPO_ROOT/docs/revision/b9/data}"
B9_MY_RUN_MANIFESTS="${B9_MY_RUN_MANIFESTS:-$REPO_ROOT/docs/revision/b9/manifests}"

# Regenerate with: bash scripts/revision/b9/build_my_run_manifests.sh
MANIFEST_LNM_TRAIN="${MANIFEST_LNM_TRAIN:-$B9_MY_RUN_MANIFESTS/lnm_lymphus_predmask_train.json}"
MANIFEST_LNM_TEST="${MANIFEST_LNM_TEST:-$B9_MY_RUN_MANIFESTS/lnm_lymphus_predmask_test.json}"
MANIFEST_FTC_TRAIN="${MANIFEST_FTC_TRAIN:-$B9_MY_RUN_MANIFESTS/ftcptc_filtered_train.json}"
MANIFEST_FTC_TEST="${MANIFEST_FTC_TEST:-$B9_MY_RUN_MANIFESTS/ftcptc_filtered_test.json}"
IMAGE_ROOTS_LNM="${IMAGE_ROOTS_LNM:-$B9_MY_RUN_DATA/lnm_lymphus_predmask_image_roots.json}"
IMAGE_ROOTS_FTC="${IMAGE_ROOTS_FTC:-$B9_MY_RUN_DATA/ftcptc_filtered_image_roots.json}"

# Aliases used by existing scripts (train/CV vs hold-out test)
MANIFEST_ZJH_TRAIN_LNM="$MANIFEST_LNM_TRAIN"
MANIFEST_ZJH_TEST_LNM="$MANIFEST_LNM_TEST"
MANIFEST_ZJH_TRAIN_FTC="$MANIFEST_FTC_TRAIN"
MANIFEST_ZJH_TEST_FTC="$MANIFEST_FTC_TEST"

# DINO / baseline packed_io roots (manifests live under B9_MY_RUN_MANIFESTS)
LNM_PACK="${LNM_PACK:-$B9_MY_RUN_DATA}"
FTC_PACK="${FTC_PACK:-$B9_MY_RUN_DATA}"
FTC_IMAGE_BASE="${FTC_IMAGE_BASE:-/mnt/wangbd8/workspace/DataSets/ThyroidAgent/Classifaction_Data/Malignant_ultrasound_images_cropped}"
FTC_MASK_DIR="${FTC_MASK_DIR:-/mnt/wangbd8/workspace/DataSets/ThyroidAgent/Classifaction_Data/Malignant_ultrasound_images_cropped_predictions}"

MANIFEST_DAI_FTC="${MANIFEST_DAI_FTC:-/mnt/wangbd8/workspace/DataSets/ThyroidAgent/Classifaction_Data/FTCPTC_ZJH8K_FangDai_packed/manifests/fangdai_external_test.json}"
FTC_DAI_IMAGE_BASE="${FTC_DAI_IMAGE_BASE:-/mnt/wangbd8/workspace/DataSets/ThyroidAgent/Classifaction_Data/FTCPTC_ZJH8K_FangDai_packed}"

SPLIT_REGISTRY="${SPLIT_REGISTRY:-$REPO_ROOT/docs/revision/b9/zjh_malignant_patient_split.json}"

B9_OOF_ROOT="${B9_OOF_ROOT:-$THYROID_AGENT/Classification_Models/b9_oof}"
DINO_ROOT="${DINO_ROOT:-$THYROID_AGENT/dino_unet_multitask}"
LLNM_ROOT="${LLNM_ROOT:-$THYROID_AGENT/LLNM-Net}"
TIGER_ROOT="${TIGER_ROOT:-$THYROID_AGENT/Tiger-Model}"

SHARED_FOLDS_ROOT="${SHARED_FOLDS_ROOT:-$REPO_ROOT/docs/revision/b9/runs/shared_folds}"
SHARED_LNM="${SHARED_LNM:-$SHARED_FOLDS_ROOT/lnm}"
SHARED_FTC="${SHARED_FTC:-$SHARED_FOLDS_ROOT/ftcptc}"

CV_SEED="${CV_SEED:-42}"
N_SPLITS="${N_SPLITS:-5}"
# filename = one image per CV cluster (image-level stratified K-fold)
B9_CV_CLUSTER="${B9_CV_CLUSTER:-filename}"
case "${B9_CV_CLUSTER}" in
  patient | patient_id)
    B9_CV_CLUSTER_PY=patient
    LLNM_CLUSTER_KEY=patient_id
    ;;
  *)
    B9_CV_CLUSTER_PY=image
    LLNM_CLUSTER_KEY=filename
    ;;
esac
CUDA_DEVICE="${CUDA_DEVICE:-0}"
PYTHON="${PYTHON:-python3}"

RUN_TAG="${RUN_TAG:-zjh20261101}"

BASELINE_EPOCHS="${BASELINE_EPOCHS:-10}"
VLM_EPOCHS="${VLM_EPOCHS:-3}"
SPECIALIST_EPOCHS="${SPECIALIST_EPOCHS:-30}"
