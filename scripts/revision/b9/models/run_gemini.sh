#!/usr/bin/env bash
# Gemini-2.5-Pro: API only — no local train / no OOF
set -euo pipefail
source "$(dirname "$0")/_lib.sh"

run_vlm_api_note "gemini"
echo "Implement API batch eval for LNM+FTC on zjh_test.json and ftcptc on Dai → $OUT_ROOT/gemini/"
