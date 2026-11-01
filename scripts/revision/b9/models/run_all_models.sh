#!/usr/bin/env bash
# Run all per-model pipelines (long). Filter with MODELS="repvit lsnet".
#
#   CUDA_VISIBLE_DEVICES=0 bash scripts/revision/b9/models/run_all_models.sh
#   MODELS=repvit bash scripts/revision/b9/models/run_all_models.sh
set -euo pipefail
MODELS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$MODELS_DIR/_lib.sh"

MODELS="${MODELS:-repvit lsnet ultrafedfm medgemma qwen3 llnm_net tiger_model thyroidxagent gpt5 gemini}"

for m in $MODELS; do
  script="$MODELS_DIR/run_${m}.sh"
  case "$m" in
    llnm_net) script="$MODELS_DIR/run_llnm_net.sh" ;;
    tiger_model) script="$MODELS_DIR/run_tiger_model.sh" ;;
    thyroidxagent) script="$MODELS_DIR/run_thyroidxagent.sh" ;;
    gpt5) script="$MODELS_DIR/run_gpt5.sh" ;;
    gemini) script="$MODELS_DIR/run_gemini.sh" ;;
    qwen3) script="$MODELS_DIR/run_qwen3.sh" ;;
  esac
  if [[ ! -f "$script" ]]; then
    echo "Skip unknown model: $m (no $script)" >&2
    continue
  fi
  echo ""
  echo "########################################"
  echo "# MODEL: $m"
  echo "########################################"
  bash "$script"
done

echo ""
echo "All requested models finished. Root: $OUT_ROOT"
