# Step 4: Predictive Modeling (보강)

**목표**: ML 예측(RF, XGBoost, LightGBM) + Ablation + SHAP.

**입력**: Step 1·2 산출물 (기본 피처 + UDX·변곡점 피처).  
**산출**: `../outputs/tables/prediction_metrics.csv`, `../outputs/figures/shap_summary_plot.png`.

- **Ablation**: 기본 피처만 vs 기본+UDX+변곡점.
- **SHAP**: 성장 예측 시 변수 기여도 시각화.

참고: 260211 run_prediction_80_20, run_regression_30w. 스크립트 추후 추가.
