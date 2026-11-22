#!/usr/bin/env bash
# Nature 主稿（26_Nature_ThyroidAgent / main_v2.tex）。与 latex-viewer 内 manuscript 目标相同。
# 不修改 Overleaf 稿源：生成 main_v2._local_build.tex（仅在 \documentclass 前加 PassOptionsToPackage{table}{xcolor}）。
set -euo pipefail
VIEWER="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "${VIEWER}/../26_Nature_ThyroidAgent" && pwd)"
OVERLAY="${VIEWER}/manuscript-overlay"
cd "$ROOT"
MAIN=main_v2
WRAP="${MAIN}._local_build.tex"
ENGINE=xelatex
export TEXINPUTS="${OVERLAY}:.:${ROOT}:"
export BIBINPUTS=".:${ROOT}:"

if [[ ! -f "${MAIN}.tex" ]]; then
  echo "MISSING: ${MAIN}.tex" >&2
  exit 1
fi

# 本地 wrap：去掉稿内重复 \usepackage{xcolor}（overlay 类已带 [table]；不改正稿 main_v2.tex）
grep -v -E '^\\usepackage(\[table\])?\{xcolor\}$' "${MAIN}.tex" > "${WRAP}"

run_latex() {
  echo "==> $ENGINE $*"
  "$ENGINE" -interaction=nonstopmode -file-line-error -jobname="${MAIN}" "${WRAP}" || true
}

run_latex "(pass 1)"
if [[ -f "${MAIN}.aux" ]] && grep -q '\\citation{' "${MAIN}.aux" 2>/dev/null; then
  echo "==> bibtex"
  bibtex "$MAIN" || true
fi
run_latex "(pass 2)"
run_latex "(pass 3)"

if [[ -f "${MAIN}.pdf" ]]; then
  echo "OK: ${MAIN}.pdf ($(wc -c <"${MAIN}.pdf") bytes)"
else
  echo "FAILED: no ${MAIN}.pdf" >&2
  exit 1
fi