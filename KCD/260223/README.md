# 260223 — 계량경제학적 보강 실험 및 4단계 파이프라인

**목적**: 논문 보강을 위한 **정통 계량경제학적 분석**과 **4단계 실험 로드맵** 정리.  
지금까지의 데이터 마이닝(패턴 발견)에 더해, **"통제된 조건 하에서 어떤 변수가 생존과 쇠퇴를 결정하는가?"**를 통계적으로 증명하는 실험을 수행·정리한다.

---

## 폴더 구조

```
260223/
├── README.md
├── docs/
│   ├── 경과보고_전체정리.md      # 지금까지 진행 사항 전체 정리 (경과 보고용)
│   ├── 보강실험_로드맵_260223.md # 보강 실험 3가지 + 4단계 파이프라인 (Gemini 정리 반영)
│   └── 작업체크리스트_260223.md  # Step별 구체적 작업 할 일
├── 01_preprocess/    # Step 1: 데이터 전처리 → df_base_features
├── 02_extract/       # Step 2: K-Shape·변곡점·UDX → df_udx_labels
├── 03_econometrics/  # Step 3: 회귀(Model 1/2/3) + Event Study ★ 신규
├── 04_prediction/    # Step 4: ML 예측 + SHAP ★ 보강
├── configs/
└── outputs/
    ├── tables/
    └── figures/
```

---

## 4단계 파이프라인 요약

| Step | 이름 | 입력 | 출력 | 비고 |
|------|------|------|------|------|
| **1** | Data Preprocessing | weekly_processed.parquet, meta_processed.csv | df_base_features.csv | 기존 260121/260204 참조 |
| **2** | Signal Extraction | 시계열 매트릭스 | df_udx_labels.csv | 기존 260204, 260204_gem 참조 |
| **3** | Econometric Analysis | df_base + df_udx | regression_tables.csv, event_study_plots.png | **신규** |
| **4** | Predictive Modeling | df_base + df_udx | prediction_metrics.csv, shap_summary_plot.png | **보강** |

---

## 보강 실험 3가지 (논문용)

1. **정통 계량경제학적 회귀**  
   Logit/OLS with 통제변수 + 지역·업종 고정효과 → Model 1/2/3 표.

2. **변곡점 기준 사건 연구 (Event Study)**  
   변곡점 t=0 정렬 후, 전후 12주 **신규 고객 비율** 추이 (DUY vs DDZ 그룹 비교, 매출 동어반복 회피).

3. **Ablation + SHAP**  
   목적: UDX·변곡점 피처의 **설명력(Feature Importance)** 증명. RF/XGBoost/LightGBM, base vs base+UDX+변곡점, SHAP Summary Plot (`pip install xgboost lightgbm shap` 권장).

---

## 사용 방법

1. **경과 보고**: `docs/경과보고_전체정리.md` 참고.
2. **로드맵·작업 파악**: `docs/보강실험_로드맵_260223.md`, `docs/작업체크리스트_260223.md` 참고.
3. **실행 순서** (전체 한 번에: `bash run_all_steps.sh`):
   ```bash
   python3 01_preprocess/run_step1_base_features.py
   python3 02_extract/run_step2_udx_labels.py
   python3 03_econometrics/run_step3_regression.py
   python3 03_econometrics/run_step3_event_study.py
   python3 04_prediction/run_step4_ml_shap.py
   ```
4. **논문/학회용 결과**: `docs/논문용_결과_요약.md`, `outputs/tables/`, `outputs/figures/` 참고.

---

## 참고 경로 (기존 프로젝트)

- 원본 데이터: `../original_data/weekly_processed.parquet`, `meta_processed.csv`
- 피처·클러스터·변곡점: `../260204/`, `../260204_gem/`, `../260211/`, `../260121/`
- 경과·논문 정리: `../260216/docs/`
