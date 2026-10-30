#!/usr/bin/env bash
# Reviewer response requires XeLaTeX (fontspec + ctex for ZH). Do not use pdflatex.
set -euo pipefail
cd "$(dirname "$0")"

xelatex_run() {
  local tex=$1
  local base=${tex%.tex}
  echo "==> xelatex: $tex"
  if ! xelatex -interaction=nonstopmode -file-line-error "$tex" >"${base}.compile.stdout" 2>&1; then
    echo "FAILED: $tex (exit $?)" >&2
    tail -n 40 "${base}.log" 2>/dev/null || tail -n 40 "${base}.compile.stdout" >&2
    return 1
  fi
  if grep -q '^! ' "${base}.log" 2>/dev/null; then
    echo "FAILED: $tex (LaTeX errors in ${base}.log)" >&2
    grep '^! ' "${base}.log" | head -5 >&2
    tail -n 30 "${base}.log" >&2
    return 1
  fi
  return 0
}

for tex in REVIEWER_RESPONSE_ZH.tex REVIEWER_RESPONSE_EN.tex; do
  echo "==> build x2: $tex"
  xelatex_run "$tex"
  xelatex_run "$tex"
  echo "    OK: ${tex%.tex}.pdf"
done
