#!/usr/bin/env bash
# Nature 主稿（26_Nature_ThyroidAgent / main_v2.tex）。与 latex-viewer 内 manuscript 目标相同。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../26_Nature_ThyroidAgent" && pwd)"
cd "$ROOT"
MAIN=main_v2
ENGINE=xelatex

echo "==> $ENGINE (pass 1)"
$ENGINE -interaction=nonstopmode -file-line-error "${MAIN}.tex" || true
if [[ -f "${MAIN}.aux" ]] && grep -q '\\citation{' "${MAIN}.aux" 2>/dev/null; then
  echo "==> bibtex"
  bibtex "$MAIN" || true
fi
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