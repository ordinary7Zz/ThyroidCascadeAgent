#!/usr/bin/env bash
# LLNM-Net: (1) full train + ZJH eval, (2) no Dai, (3) 5-fold OOF LNM
#
# Optional skips (env):
#   SKIP_STEP1=1       — skip train + ZJH eval (only OOF)
#   SKIP_FULL_TRAIN=1  — reuse full_train/best_model.pth; still run eval unless SKIP_ZJH_EVAL=1
#   SKIP_ZJH_EVAL=1    — skip evaluate.py (zjh_test_eval.json)
#   SKIP_OOF=1         — skip 5-fold OOF
#   SKIP_IF_CV_SUMMARY=1 — skip OOF if lnm/oof/cv_summary.json exists
#
# Example (full train done, only OOF):
#   SKIP_STEP1=1 bash scripts/revision/b9/models/run_llnm_net.sh
set -euo pipefail
source "$(dirname "$0")/_lib.sh"

run_llnm_full_zjh
run_llnm_oof

echo "Done. Outputs: $OUT_ROOT/llnm_net/"
echo "  full_train: $OUT_ROOT/llnm_net/lnm/full_train/ (zjh_test_eval.json)"
echo "  OOF:        $OUT_ROOT/llnm_net/lnm/oof/cv_summary.json"
