#!/usr/bin/env bash
# 完整回信 Overleaf 工程（response_letter / main.tex）。与 latex-viewer 内 response 目标相同。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../response_letter" && pwd)"
cd "$ROOT"
MAIN=main
ENGINE=pdflatex

echo "==> $ENGINE (pass 1)"
$ENGINE -interaction=nonstopmode -file-line-error "${MAIN}.tex" || true
for i in 2 3; do
  echo "==> $ENGINE (pass $i)"
  $ENGINE -interaction=nonstopmode -file-line-error "${MAIN}.tex" || true
done
if [[ -f "${MAIN}.pdf" ]]; then
  echo "OK: ${MAIN}.pdf ($(wc -c <"${MAIN}.pdf") bytes)"
else
  echo "FAILED: no ${MAIN}.pdf" >&2
  exit 1
fi