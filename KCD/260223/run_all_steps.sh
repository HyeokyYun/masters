#!/bin/bash
# 260223 4-step pipeline — 순서대로 실행
# Run from 260223: bash run_all_steps.sh

set -e
cd "$(dirname "$0")"
echo "=== Step 1: Base features ==="
python3 01_preprocess/run_step1_base_features.py
echo "=== Step 2: UDX labels ==="
python3 02_extract/run_step2_udx_labels.py
echo "=== Step 3a: Regression (Model 1/2/3) ==="
python3 03_econometrics/run_step3_regression.py
echo "=== Step 3b: Event Study ==="
python3 03_econometrics/run_step3_event_study.py
echo "=== Step 4: ML + importance ==="
python3 04_prediction/run_step4_ml_shap.py
echo "=== Done. Check outputs/tables/ and outputs/figures/ ==="
