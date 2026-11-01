# Shared helpers for per-model malignant-subtask pipelines.
# Order: (1) full train + ZJH test, (2) Dai FTC eval, (3) 5-fold OOF [optional]

MODELS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
B9_SCRIPT_DIR="$(cd "$MODELS_DIR/.." && pwd)"
# shellcheck source=../env_malig_b9.sh
source "$B9_SCRIPT_DIR/env_malig_b9.sh"

FULL_EXT="$B9_SCRIPT_DIR/run_baseline_full_external.py"
CV_PY="$B9_SCRIPT_DIR/run_baseline_cv.py"

OUT_ROOT="${OUT_ROOT:-$REPO_ROOT/docs/revision/b9/runs/models_${RUN_TAG}}"

ensure_shared_folds() {
  if [[ -f "$SHARED_LNM/fold_manifest.json" && -f "$SHARED_FTC/fold_manifest.json" ]]; then
    return 0
  fi
  echo ">>> Exporting shared 5-fold splits (once)"
  bash "$B9_SCRIPT_DIR/01_export_shared_folds.sh"
}

run_baseline_full_task() {
  local model="$1"
  local task="$2"
  local packed="$3"
  local train_manifest="$4"
  local test_manifest="$5"
  local dai_manifest="${6:-}"
  local skip_train="${7:-0}"
  local out_dir="$OUT_ROOT/$model/$task/full_external"
  echo ""
  echo ">>> [$model/$task] full train + ZJH hold-out${dai_manifest:+ + Dai}$([[ "$skip_train" == "1" ]] && echo ' (skip_train)')"
  mkdir -p "$out_dir"
  local -a dai_args=()
  if [[ -n "$dai_manifest" && -f "$dai_manifest" ]]; then
    dai_args=(--dai_manifest "$dai_manifest")
  fi
  local -a skip_args=()
  if [[ "$skip_train" == "1" ]]; then
    skip_args=(--skip_train)
  fi
  "$PYTHON" "$FULL_EXT" \
    --model "$model" \
    --task "$task" \
    --packed_root "$packed" \
    --train_manifest "$train_manifest" \
    --zjh_test_manifest "$test_manifest" \
    --output_dir "$out_dir" \
    --cuda_device "$CUDA_DEVICE" \
    --seed "$CV_SEED" \
    "${skip_args[@]}" \
    "${dai_args[@]}"
}

run_baseline_full_zjh_both_tasks() {
  local model="$1"
  run_baseline_full_task "$model" lnm "$LNM_PACK" "$MANIFEST_ZJH_TRAIN_LNM" "$MANIFEST_ZJH_TEST_LNM"
  run_baseline_full_task "$model" ftcptc "$FTC_PACK" "$MANIFEST_ZJH_TRAIN_FTC" "$MANIFEST_ZJH_TEST_FTC"
}

run_baseline_dai_ftc() {
  local model="$1"
  echo ""
  echo ">>> [$model/ftcptc] Dai external (reuse FTC checkpoint)"
  run_baseline_full_task "$model" ftcptc "$FTC_PACK" \
    "$MANIFEST_ZJH_TRAIN_FTC" "$MANIFEST_ZJH_TEST_FTC" "$MANIFEST_DAI_FTC" 1
}

run_baseline_oof_both_tasks() {
  local model="$1"
  ensure_shared_folds
  export SHARED_LNM SHARED_FTC
  export RUNS_ROOT="$OUT_ROOT/$model/oof"
  export MODELS="$model"
  export TASKS="lnm ftcptc"
  export CUDA_DEVICE
  export PHASE="${PHASE:-all}"
  export SKIP_IF_CV_SUMMARY="${SKIP_IF_CV_SUMMARY:-0}"
  echo ""
  echo ">>> [$model] 5-fold OOF (LNM + FTC/PTC)"
  mkdir -p "$RUNS_ROOT"
  cd "$B9_OOF_ROOT"
  bash scripts/run_all_baselines_cv.sh
}

run_llnm_full_zjh() {
  local out="$OUT_ROOT/llnm_net/lnm/full_train"
  echo ""
  echo ">>> [LLNM-Net/LNM] full train + ZJH hold-out"
  cd "$LLNM_ROOT"
  "$PYTHON" new_code/train.py \
    --train_json "$MANIFEST_ZJH_TRAIN_LNM" \
    --test_json "$MANIFEST_ZJH_TEST_LNM" \
    --image_roots_json "$LNM_PACK/image_roots.json" \
    --output_dir "$out" \
    --batch_size "${BATCH_SIZE:-4}" \
    --epochs "${EPOCHS:-50}" \
    --learning_rate "${LEARNING_RATE:-1e-5}" \
    --device "${DEVICE:-cuda}"
  "$PYTHON" new_code/evaluate.py \
    --test_json "$MANIFEST_ZJH_TEST_LNM" \
    --image_roots_json "$LNM_PACK/image_roots.json" \
    --weights "$out/best_model.pth" \
    --norm_stats "$out/train_norm_stats.pkl" \
    --output "$out/zjh_test_eval.json" \
    --device "${DEVICE:-cuda}"
}

run_llnm_oof() {
  local out="$OUT_ROOT/llnm_net/lnm/oof"
  echo ""
  echo ">>> [LLNM-Net/LNM] 5-fold OOF"
  cd "$LLNM_ROOT"
  "$PYTHON" new_code/run_b9_patient_cv.py \
    --train_manifest "$MANIFEST_ZJH_TRAIN_LNM" \
    --image_roots_json "$LNM_PACK/image_roots.json" \
    --output_dir "$out" \
    --n_splits "$N_SPLITS" \
    --batch_size "${BATCH_SIZE:-4}" \
    --epochs "${EPOCHS:-50}" \
    --learning_rate "${LEARNING_RATE:-1e-5}" \
    --device "${DEVICE:-cuda}"
}

run_tiger_full_zjh() {
  echo ""
  echo ">>> [Tiger-Model/FTC] step 1: full train + ZJH hold-out"
  cd "$TIGER_ROOT"
  EXPORT_ZJH="$OUT_ROOT/tiger_model/ftcptc/full_external/zjh_test" \
  EXTERNAL_STEP=zjh \
  bash "$B9_SCRIPT_DIR/06_run_tiger_ftc_external.sh"
}

run_tiger_dai_only() {
  echo ""
  echo ">>> [Tiger-Model/FTC] step 2: Dai external (reuse checkpoint)"
  cd "$TIGER_ROOT"
  EXPORT_DAI="$OUT_ROOT/tiger_model/ftcptc/full_external/dai" \
  EXTERNAL_STEP=dai \
  SKIP_TRAIN=1 \
  bash "$B9_SCRIPT_DIR/06_run_tiger_ftc_external.sh"
}

run_tiger_oof() {
  echo ""
  echo ">>> [Tiger-Model/FTC] 5-fold OOF"
  cd "$TIGER_ROOT"
  OUTPUT_DIR="$OUT_ROOT/tiger_model/ftcptc/oof" \
  JSON_PATH="$MANIFEST_ZJH_TRAIN_FTC" \
  bash "$B9_SCRIPT_DIR/05_run_tiger_ftc_b9.sh"
}

run_txagent_oof_both() {
  echo ""
  echo ">>> [ThyroidXAgent] DINO multitask 5-fold OOF (LNM + FTC)"
  RUN_TAG="$RUN_TAG" TASKS="lnm ftcptc" \
  bash "$B9_SCRIPT_DIR/03_run_dino_multitask_oof.sh"
}

run_txagent_full_note() {
  echo ""
  echo ">>> [ThyroidXAgent] steps 1–2 (full ZJH + Dai): run Cascade E1–E4 after DINO checkpoints exist."
  echo "    Output target: $OUT_ROOT/thyroidxagent/"
  echo "    See Malignant_Cls_Model/b9/README.md and B9_ThyroidXAgent_补充实验计划.md"
}

run_vlm_api_note() {
  local name="$1"
  echo ""
  echo ">>> [$name] steps 1–2: closed API — no local full train; evaluate on ZJH test + Dai manifests separately."
  echo "    Skip step 3 (no OOF in tab_malig_oof for $name)."
  mkdir -p "$OUT_ROOT/$name"
}
