# KCD 소상공인 생애주기 연구 — Executive Briefing

**지도교수**: KAIST 김지희 교수 | **갱신일**: 2026-04-23  
**상세 결과**: `top_tier/outputs/docs/top_tier_report.md`

---

## 1. Research Problem

소상공인 폐업 연구는 주로 설문, 재무제표, 또는 생존/폐업 이분법에 기대어 왔다. 본 연구는 KCD 주간 카드거래 패널을 이용해 음식점 생애주기를 Growth/Stable/Decline의 동적 trajectory로 모델링하고, 서울시 공개 행정·상권 데이터를 결합해 내부 예측 지표가 실제 지역경제 신호와 맞물리는지 검증한다.

**Target artifact**: 30주 관측만으로 이후 outcome과 Decline 위험을 예측하는 Early Warning System(EWS).

---

## 2. Data Foundation

- **KCD 원본 데이터**: `original_data/weekly.parquet`, `original_data/meta.csv`
- 서울 음식점 **59,089개**, 2021-01-01 ~ 2023-08-28, 주간 거래 **6.58M row**
- 폐업 추정: **9,247개** (15.6%) / 생존 censored: **49,842개**
- 분석 패널: **49,007개** 점포
- Outcome 3-class: Growth **20,087** / Stable **18,003** / Decline **10,917**

**중요 변경**: 기존 `260326_fullsample`, `260321_codex`, `260204_gem` 의존을 제거하고, `top_tier` 파이프라인이 `original_data`에서 관측 패널과 label feature를 직접 생성하도록 수정.

---

## 3. External Validation — 새 보강 포인트

`thesis/data_external`의 서울시 공개 데이터를 `top_tier`에 통합했다.

- 서울시 내국인 생활인구 자치구 단위 2021-2023
- 서울시 음식점 인허가/폐업 등록부
- 서울시 상권분석서비스 점포-상권, 점포-상권배후지, 추정매출-상권배후지 2021-2023

핵심 결과:

- **KCD LEVI vs 생활인구 변화율**: Pearson **0.853**, Spearman **0.802** (n=25)
- **KCD LEVI vs 인허가 폐업률**: Pearson **-0.430** (n=25)
- **KCD 추정 폐업률 vs 인허가 폐업률**: Pearson **0.430** (n=25)
- **KCD 분기 매출 vs 서울 상권 추정매출**: Pearson **0.766**, Spearman **0.727** (n=11)
- **QoQ 매출증감 상관**: Pearson **0.839**, Spearman **0.891** (n=10)

해석: KCD 거래 기반 lifecycle 지표가 내부 분류 결과에 머물지 않고, 생활인구 변화·공식 폐업 등록·서울시 상권 매출 흐름과 일관된 방향으로 움직인다. 이는 단일 민간 패널의 외적 타당성 약점을 상당히 보완한다.

---

## 4. Updated Key Findings

### F1. Survivorship Bias 5배 정량화

분석 패널 내 폐업률 **8.9%** (n=48,980) vs 패널 바깥 **48.3%** (n=10,027). 패널 구성 기준이 조기 폐업 점포를 체계적으로 배제한다는 점을 수치화.

### F2. External Validity of KCD Lifecycle Signal

자치구별 KCD LEVI가 생활인구 변화율과 강한 양의 상관을 보이고, 인허가 폐업률과 음의 상관을 보인다. 분기별 KCD 매출도 서울시 상권 추정매출과 높은 상관을 보인다.

### F3. Survival and Hazard Patterns

Kaplan-Meier log-rank는 outcome별 생존함수 차이를 강하게 지지한다. Cox PH 기준 주요 hazard signal은 신규고객비율, 변동성, 초기/후기 slope, mdd, trend slope로 확인된다.

### F4. Hybrid Prediction and EWS

새 `original_data` 기반 label로 prediction, hybrid, EWS, SHAP을 재학습했다.

- Baseline XGBoost: Macro-F1 **0.548**, AUC **0.736**
- Proposed D (base + KMeans cluster + change-point): Macro-F1 **0.639**, AUC **0.824**
- Proposed D는 baseline 대비 F1 **+0.091**, AUC **+0.088**
- EWS Average Precision: Decline **0.688** (baseline 0.223), Growth **0.819** (baseline 0.410)
- Cost-sensitive 최적 threshold: **0.10**, net utility **43,626**

---

## 5. 현재 상태와 남은 작업

완료:

- `step00_prepare_original_panel.py` 추가: `original_data` 기반 패널/label 생성
- `step15_external_validation.py` 추가: 생활인구·인허가·상권분석 외부 검증
- `top_tier_report.md` 외부 검증 섹션 반영
- `run_external_refresh.sh` 추가: 전체 재실행 스크립트
- 새 원본 label 기준 prediction/hybrid/EWS/SHAP 재학습 완료

주의:

- 외부 검증, 생존분석, prediction, hybrid, EWS, SHAP은 새 원본 기반 데이터로 갱신 완료.
- audit01-04, fold-safe leakage, enhanced PSM, multivariate deep-learning robustness는 legacy label 결과가 섞여 있어 현재 리포트 본문에서 제외했다. 최종 투고 전 재실행 필요.
- 서버에서 VS Code를 꺼도 계속 돌게 하려면 sandbox 밖 `nohup` 실행 승인이 필요하다.

---

## 6. 교수님께 드릴 한 줄 요약

본 연구는 이제 “KCD 내부 예측 모델”을 넘어, 서울시 생활인구·공식 인허가 폐업·상권 추정매출과 맞물리는 **외부 검증된 소상공인 lifecycle/EWS 연구**로 프레이밍할 수 있다.
