#!/usr/bin/env bash
# ThyroidXAgent (DINO multitask specialist): full zjh_train → zjh_test (+ FTC Dai).
#
# Outputs (mirrors CNN baselines):
#   docs/revision/b9/runs/models_${RUN_TAG}/thyroidxagent/{lnm,ftcptc}/full_external/external_summary.json
#
# Usage:
#   CUDA_VISIBLE_DEVICES=0 bash scripts/revision/b9/08_run_dino_full_external.sh
#   TASKS=lnm EPOCHS=1 LIMIT_SAMPLES=32 bash scripts/revision/b9/08_run_dino_full_external.sh  # smoke
#   SKIP_TRAIN=1 bash scripts/revision/b9/08_run_dino_full_external.sh  # eval only
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=env_malig_b9.sh
source "$SCRIPT_DIR/env_malig_b9.sh"

TASKS="${TASKS:-lnm ftcptc}"
EPOCHS="${EPOCHS:-${SPECIALIST_EPOCHS:-30}}"
OUT_ROOT="${OUT_ROOT:-$REPO_ROOT/docs/revision/b9/runs/models_${RUN_TAG}}"

run_one() {
  local task="$1"
  local packed train test roots out extra=()
  case "$task" in
    lnm)
      packed="$LNM_PACK"
      train="$MANIFEST_LNM_TRAIN"
      test="$MANIFEST_LNM_TEST"
      roots="$IMAGE_ROOTS_LNM"
      out="$OUT_ROOT/thyroidxagent/lnm/full_external"
      ;;
    ftcptc)
      packed="$FTC_PACK"
      train="$MANIFEST_FTC_TRAIN"
      test="$MANIFEST_FTC_TEST"
      roots="$IMAGE_ROOTS_FTC"
      out="$OUT_ROOT/thyroidxagent/ftcptc/full_external"
      extra+=(--dai_manifest "$MANIFEST_DAI_FTC")
      ;;
    *)
      echo "Unknown task $task" >&2
      return 1
      ;;
  esac

  [[ -n "${LIMIT_SAMPLES:-}" ]] && extra+=(--limit_samples "$LIMIT_SAMPLES")
  [[ "${SKIP_TRAIN:-0}" == "1" ]] && extra+=(--skip_train)
  [[ "${DRY_RUN:-0}" == "1" ]] && extra+=(--dry_run)

  echo ">>> DINO full external task=$task → $out"
  cd "$DINO_ROOT"
  CUDA_VISIBLE_DEVICES="${CUDA_DEVICE}" "$PYTHON" Malignant_Cls_Model/b9/run_full_external.py \
    --task "$task" \
    --packed_root "$packed" \
    --train_manifest "$train" \
    --zjh_test_manifest "$test" \
    --image_roots_json "$roots" \
    --output_dir "$out" \
    --epochs "$EPOCHS" \
    --cuda_device 0 \
    "${extra[@]}"
}

for task in $TASKS; do
  run_one "$task"
done

echo "Done. ThyroidXAgent DINO external under $OUT_ROOT/thyroidxagent/"
