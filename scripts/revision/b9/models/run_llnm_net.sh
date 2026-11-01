#!/usr/bin/env bash
# LLNM-Net: (1) full+ZJH LNM, (2) no Dai, (3) 5-fold OOF LNM
set -euo pipefail
source "$(dirname "$0")/_lib.sh"

run_llnm_full_zjh
run_llnm_oof

echo "Done. Outputs: $OUT_ROOT/llnm_net/"
