# Additional Analyses Plan — paper submission 전 4가지 보강

Phase 5 결과만으로도 paper 본문 80%가 채워지지만, 다음 4가지 추가 분석으로
reviewer 핵심 질문에 선제 대응한다. 3주 안에 완료 목표.

## 분석 1: Per-cohort LightGBM Δ 분해 (1–2일)

### 문제 의식
- 현재 LGBM Δ = +0.008은 6 panel 평균.
- reviewer: "+0.008은 너무 작다" → "특정 sub-population에서는 더 크다" 답변 필요.

### 가설
- Q4_long (업력 9년+) cohort 에서 LGBM > RF Δ가 +0.020 이상일 가능성
- fragile cluster (cluster 3, Decline 36%) 에서 더 클 가능성

### 실험
```
파일: 260511/phase5_external/src/s5d_weighting/run_weighting_cohort.py (신규)
- _load_features에서 tenure_quartile (Q1–Q4) 또는 cluster 정보 추가 로드
- 각 cohort subset에 대해 RF / LGBM 3-fold 재학습
- Δ_lgbm vs Δ_rf per cohort 출력
```

### 산출물
- `outputs/tables/lgbm_per_cohort.csv` (panel × cohort × Δ)
- `outputs/figures/lgbm_per_cohort_heatmap.png`
- paper §4.5 (Results) 의 LightGBM 표 다음 단락 + 추가 figure

## 분석 2: EWS calibration + decile table (2–3일)

### 문제 의식
- LightGBM proba output을 EWS deciles로 변환할 때 calibration 필요.
- DSS submission에도 필수 (decision-support artifact angle).

### 실험
```
파일: 260511/phase5_external/src/s5d_weighting/run_ews_calibration.py (신규)
- LightGBM proba (Decline class) 추출, 6 panels OOF
- reliability diagram (predicted vs observed bin avg)
- Brier score
- 10 deciles → observed-decline rate 표
```

### 산출물
- `outputs/tables/ews_calibration.csv` (decile × observed_decline × predicted_avg)
- `outputs/tables/ews_brier.csv` (panel × method × Brier)
- `outputs/figures/ews_reliability_diagram.png`
- paper §4.6 또는 §5.2 (decision-support implication) 자료

## 분석 3: Cost-sensitivity sweep (dollar value) (1–2일)

### 문제 의식
- "+0.008 macro_F1는 너무 작다"는 비판에 대해 정책적 cost로 환산.
- 예: Decline 점포 1개 false negative = X원 손실 가정 (assumption based).

### 실험
```
파일: 260511/phase5_external/src/s5d_weighting/run_cost_sensitivity.py (신규)
- threshold τ ∈ {0.1, 0.2, ..., 0.9}
- 각 τ에서 confusion matrix → expected cost (FN × cost_FN + FP × cost_FP)
- RF vs LightGBM 두 모델, 4가지 cost ratio 시나리오 (FN/FP = 5, 10, 20, 50)
```

### 산출물
- `outputs/tables/cost_sensitivity.csv` (panel × model × τ × cost ratio × expected_cost)
- `outputs/figures/cost_sensitivity_curves.png`
- paper §5.2 또는 §4 마지막의 정책 함의

## 분석 4: Synthetic long-history ablation (3–4일)

### 문제 의식
- "stock SOTA가 안 통하는 이유 중 'short window' 가설을 분리하라"
- raw weekly에서 4년 연속 history 있는 stores만 extract → 같은 SOTA 재학습.

### 실험
```
파일: 260511/phase5_external/src/s5b_neuralforecast/run_long_history_ablation.py (신규)
- weekly.parquet에서 history ≥ 156 weeks (3년) stores 선별
- subset으로 5B의 7 모델 (특히 PatchTST, TFT, Informer) 재학습
- input_size를 156 또는 78로 키워 다시 시도
- macro_F1 vs short_window baseline 비교
```

### 산출물
- `outputs/tables/long_history_ablation.csv` (model × window_length × macro_F1)
- `outputs/figures/long_history_effect.png`
- paper §5.1 mechanism (1) 의 정량 입증. "short window이 원인의 X%" 같은 정량 statement 가능.

## 통합 timeline

| Day | 작업 |
|---|---|
| Day 1–2 | 분석 1 (cohort 분해) — 빠른 |
| Day 3–5 | 분석 2 (EWS calibration) |
| Day 6–7 | 분석 3 (cost-sensitivity) |
| Day 8–11 | 분석 4 (synthetic long-history) — 가장 시간 소요 |
| Day 12–14 | figures + 표 통합 + 결과 정리 |
| Day 15 | paper §4 results draft 완성 |

총 ~3주.

## paper reviewer 예상 질문 → 본 분석 매핑

| 예상 reviewer 질문 | 답하는 분석 |
|---|---|
| "+0.008는 너무 작다" | 분석 1 (per-cohort Δ) |
| "decision-support artifact 측면이 약하다" | 분석 2 (calibration) |
| "정책 implication이 정성적이다" | 분석 3 (cost dollar value) |
| "왜 stock SOTA가 안 통하는가?" | 분석 4 (long-history ablation) |
| "Moirai 결과가 불완전" | (별도) 1/6 panel partial로 명시, future work |
| "한국에 한정" | (별도) limitation 명시, future work |
