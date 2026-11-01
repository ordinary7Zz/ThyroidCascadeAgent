# shellcheck disable=SC2034
# Source from orchestration scripts:  source "$(dirname "$0")/env_malig_b9.sh"
#
# ZJH malignant protocol (2026-11): TN3K dHash exclusion + patient hold-out (seed 42).
# OOF / full-train use zjh_train only (517 patients, 3227 images). External: zjh_test + (FTC) Dai.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
THYROID_AGENT="$(cd "$REPO_ROOT/.." && pwd)"

LNM_PACK="${LNM_PACK:-/mnt/wangbd8/workspace/DataSets/ThyroidAgent/Classifaction_Data/LNM_ZJH8K_LymphUs_C1C2_packed}"
FTC_PACK="${FTC_PACK:-/mnt/wangbd8/workspace/DataSets/ThyroidAgent/Classifaction_Data/FTCPTC_ZJH8K_FangDai_packed}"

MANIFEST_ZJH_TRAIN_LNM="${MANIFEST_ZJH_TRAIN_LNM:-$LNM_PACK/manifests/zjh_train.json}"
MANIFEST_ZJH_TRAIN_FTC="${MANIFEST_ZJH_TRAIN_FTC:-$FTC_PACK/manifests/zjh_train.json}"
MANIFEST_ZJH_TEST_LNM="${MANIFEST_ZJH_TEST_LNM:-$LNM_PACK/manifests/zjh_test.json}"
MANIFEST_ZJH_TEST_FTC="${MANIFEST_ZJH_TEST_FTC:-$FTC_PACK/manifests/zjh_test.json}"
MANIFEST_DAI_FTC="${MANIFEST_DAI_FTC:-$FTC_PACK/manifests/fangdai_external_test.json}"

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
CUDA_DEVICE="${CUDA_DEVICE:-0}"
PYTHON="${PYTHON:-python3}"

RUN_TAG="${RUN_TAG:-zjh20261101}"
