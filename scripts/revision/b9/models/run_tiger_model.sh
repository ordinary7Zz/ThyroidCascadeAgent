#!/usr/bin/env bash
# Tiger-Model: (1) full+ZJH FTC, (2) Dai, (3) 5-fold OOF FTC
set -euo pipefail
source "$(dirname "$0")/_lib.sh"

run_tiger_full_zjh
run_tiger_dai_only
run_tiger_oof

echo "Done. Outputs: $OUT_ROOT/tiger_model/"
