#!/usr/bin/env bash
# 兼容入口 → scripts/revision/b3/zjh/run_zjh8k_reinfer_chunks.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "${ROOT}/scripts/revision/b3/zjh/run_zjh8k_reinfer_chunks.sh" "$@"
