#!/usr/bin/env bash
set -euo pipefail

cd /home/hyeoky98/kcd
export MPLCONFIGDIR=/tmp/matplotlib-top-tier
mkdir -p "$MPLCONFIGDIR" top_tier/outputs/docs

run_step() {
  local step="$1"
  echo
  echo "===== $(date -u '+%Y-%m-%dT%H:%M:%SZ') :: ${step} ====="
  python -u "${step}"
}

run_step top_tier/src/step00_prepare_original_panel.py
run_step top_tier/src/step01_data_foundation.py
run_step top_tier/src/step02_survival_analysis.py
run_step top_tier/src/step03_prediction_model.py
run_step top_tier/src/step10_hybrid_prediction.py
run_step top_tier/src/step12_early_warning.py
run_step top_tier/src/step15_external_validation.py
run_step top_tier/src/step08_figures.py
run_step top_tier/src/step09_report.py

echo
echo "===== $(date -u '+%Y-%m-%dT%H:%M:%SZ') :: DONE ====="
