#!/usr/bin/env bash
# GPT-5: API only — no local train / no OOF table row protocol
set -euo pipefail
source "$(dirname "$0")/_lib.sh"

run_vlm_api_note "gpt5"
echo "Implement API batch eval for LNM+FTC on zjh_test.json and ftcptc on Dai → $OUT_ROOT/gpt5/"
