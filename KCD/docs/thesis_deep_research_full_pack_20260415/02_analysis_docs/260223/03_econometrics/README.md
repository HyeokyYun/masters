# Step 3: Econometric Analysis (신규)

**목표**: 정통 회귀(Model 1/2/3) + Event Study.

**입력**: `df_base_features` + `df_udx_labels`.  
**산출**: `../outputs/tables/regression_tables.csv`, `../outputs/figures/event_study_plots.png`.

- **회귀**: Logit(성장/쇠퇴) 또는 OLS(growth_rate); 통제변수 + sigungu/depth_2 고정효과.
- **Event Study**: 변곡점 t=0 정렬 후 전후 구간 시계열 시각화.

스크립트: `run_regression_with_fe.py`, `run_event_study.py` 등 (추가 예정).
