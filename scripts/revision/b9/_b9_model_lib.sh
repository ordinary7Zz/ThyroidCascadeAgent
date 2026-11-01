# shellcheck disable=SC2034
# Shared helpers for per-model B9 scripts. Source after env_malig_b9.sh.
#
# Protocol order:
#   1) Full train on zjh_train → eval zjh_test (primary external)
#   2) FTC only: eval Dai (fangdai_external_test.json)
#   3) 5-fold patient OOF on zjh_train (skip for medgemma / qwen3)

_b9_require_shared_folds() {
  if [[ ! -f "$SHARED_LNM/fold_manifest.json" || ! -f "$SHARED_FTC/fold_manifest.json" ]]; then
    echo "Missing shared folds. Run: bash scripts/revision/b9/01_export_shared_folds.sh" >&2
    exit 1
  fi
}

_b9_runs_root() {
  echo "${RUNS_ROOT:-$B9_OOF_ROOT/runs/revision_${RUN_TAG}}"
}

_b9_packed_for_task() {
  case "$1" in
    lnm) echo "$LNM_PACK" ;;
    ftcptc) echo "$FTC_PACK" ;;
    *) echo "Unknown task: $1" >&2; return 1 ;;
  esac
}

_b9_train_manifest() {
  case "$1" in
    lnm) echo "$MANIFEST_ZJH_TRAIN_LNM" ;;
    ftcptc) echo "$MANIFEST_ZJH_TRAIN_FTC" ;;
    *) return 1 ;;
  esac
}

_b9_test_manifest() {
  case "$1" in
    lnm) echo "$MANIFEST_ZJH_TEST_LNM" ;;
    ftcptc) echo "$MANIFEST_ZJH_TEST_FTC" ;;
    *) return 1 ;;
  esac
}

# CNN/ViT/VLM baselines via b9_oof/run_baseline_full_external.py
b9_baseline_full_external() {
  local model="$1"
  local task="$2"
  local runs_root out_dir packed train test
  runs_root="$(_b9_runs_root)"
  out_dir="$runs_root/${model}/${task}/full_external"
  packed="$(_b9_packed_for_task "$task")"
  train="$(_b9_train_manifest "$task")"
  test="$(_b9_test_manifest "$task")"

  local -a extra=()
  if [[ -n "${EPOCHS:-}" ]]; then
    extra+=(--epochs "$EPOCHS")
  fi
  if [[ "$task" == "ftcptc" ]]; then
    extra+=(--dai_manifest "$MANIFEST_DAI_FTC")
  fi
  if [[ "${DRY_RUN:-0}" == "1" ]]; then
    extra+=(--dry_run)
  fi

  echo ">>> [$model/$task] Step 1–2: full train + zjh_test (+ Dai if FTC)"
  echo "    output: $out_dir/external_summary.json"
  cd "$B9_OOF_ROOT"
  "$PYTHON" run_baseline_full_external.py \
    --model "$model" \
    --task "$task" \
    --packed_root "$packed" \
    --train_manifest "$train" \
    --zjh_test_manifest "$test" \
    --output_dir "$out_dir" \
    --cuda_device "$CUDA_DEVICE" \
    --seed "$CV_SEED" \
    "${extra[@]}"
}

b9_baseline_oof_cv() {
  local model="$1"
  local task="$2"
  local runs_root folds_root out_dir summary
  runs_root="$(_b9_runs_root)"
  case "$task" in
    lnm) folds_root="$SHARED_LNM" ;;
    ftcptc) folds_root="$SHARED_FTC" ;;
    *) echo "Unknown task: $task" >&2; return 1 ;;
  esac
  out_dir="$runs_root/${model}/${task}"
  summary="$out_dir/cv_summary.json"

  if [[ "${SKIP_IF_CV_SUMMARY:-0}" == "1" && -f "$summary" ]]; then
    echo "[skip] $model/$task CV — existing $summary"
    return 0
  fi

  local -a extra=()
  [[ -n "${MAX_FOLDS:-}" ]] && extra+=(--max_folds "$MAX_FOLDS")
  [[ -n "${EPOCHS:-}" ]] && extra+=(--epochs "$EPOCHS")
  [[ "${DRY_RUN:-0}" == "1" ]] && extra+=(--dry_run)

  echo ">>> [$model/$task] Step 3: 5-fold OOF"
  cd "$B9_OOF_ROOT"
  "$PYTHON" run_baseline_cv.py \
    --model "$model" \
    --task "$task" \
    --folds_root "$folds_root" \
    --output_dir "$out_dir" \
    --phase "${PHASE:-all}" \
    --cuda_device "$CUDA_DEVICE" \
    "${extra[@]}"
}

b9_baseline_model_tasks() {
  local model="$1"
  local tasks="${TASKS:-lnm ftcptc}"
  _b9_require_shared_folds
  export SHARED_LNM SHARED_FTC CUDA_DEVICE
  export RUNS_ROOT="${RUNS_ROOT:-$(_b9_runs_root)}"
  export ULTRAFEDFM_PYTHON="${ULTRAFEDFM_PYTHON:-/mnt/wangbd8/workspace/envs/ultrafedfm/bin/python}"

  for task in $tasks; do
    b9_baseline_full_external "$model" "$task"
    b9_baseline_oof_cv "$model" "$task"
  done
}

b9_vlm_model_tasks() {
  local model="$1"
  local tasks="${TASKS:-lnm ftcptc}"
  _b9_require_shared_folds
  export RUNS_ROOT="${RUNS_ROOT:-$(_b9_runs_root)}"

  for task in $tasks; do
    b9_baseline_full_external "$model" "$task"
    echo ">>> [$model/$task] Step 3 skipped (VLM: no 5-fold CV in B9 protocol)"
  done
}
