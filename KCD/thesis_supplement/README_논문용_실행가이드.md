# 논문 보강 스크립트 — 실행 가이드

**목적**: 석사논문 검토 시 권장된 보완 사항을 독립 스크립트로 제공.  
**기존 파일 수정 없음** — 모든 스크립트는 `thesis_supplement/` 에 새로 추가됨.

---

## 1. 실행 순서

```
26-1/
├── thesis_supplement/
│   ├── README_논문용_실행가이드.md     ← 이 문서
│   ├── run_30w_prediction_extended.py  ← 30주 예측 평가 보강
│   ├── run_event_study_new_customer.py ← Event Study (new_customer_ratio)
│   ├── run_methodology_comparison.py   ← 방법론 비교 (v5 vs final_code)
│   └── outputs/                        ← 산출물 저장
```

### 사전 요구사항

- `original_data/weekly.parquet` 또는 `weekly_reduced.parquet` (Event Study용)
- `original_data/weekly_processed.parquet` (30주 예측용)
- `original_data/meta.csv`
- 260301 또는 260223 실행 완료 → `df_base_features` (growth_type)
- 260204_gem 실행 완료 → `final_code` (방법론 비교, Event Study)
- 260309_claude/lifecycle_pipeline_v5.py 실행 완료 → `lifecycle_features_v5.csv` (방법론 비교)

---

## 2. 스크립트별 실행 방법

### 2.1 30주 예측 평가 보강

**기능**: F1 외 AUC-ROC, PR-AUC, Precision, Recall, 혼동행렬 산출  
**클래스 불균형**: `class_weight="balanced"` 적용

```bash
cd /Volumes/SAMSUMG_128/master_graduate/KCD_source_code_from_Yang/26-1
source .venv/bin/activate  # 또는 conda activate
python thesis_supplement/run_30w_prediction_extended.py
```

**출력**:
- `thesis_supplement/outputs/30w_prediction_extended_metrics.csv`
- `thesis_supplement/outputs/30w_prediction_classification_report.txt`

---

### 2.2 Event Study (new_customer_ratio 기반)

**기능**: 4주 매출성장률 대리지표 대신 신규고객비율 사용  
**동어반복 이슈 해소**: DUY/DDZ 정의와 독립적인 지표

```bash
python thesis_supplement/run_event_study_new_customer.py
```

**출력**:
- `thesis_supplement/outputs/event_study_new_customer_ratio.png`
- `thesis_supplement/outputs/event_study_new_customer_means.csv`

**주의**: `weekly.parquet`에 `customer`, `customer_new` 컬럼 필요.  
`weekly_processed.parquet`만 있는 경우에는 기존 260223 Event Study 사용.

---

### 2.3 방법론 비교 (v5 vs final_code)

**기능**: 데이터 드리븐(v5) vs K-Shape+변곡점(final_code) 레이블 비교  
**논문 활용**: 방법론 선택 근거, 교차표

```bash
# 먼저 v5 파이프라인 실행 (weekly_reduced 사용 시 빠름)
python 260309_claude/lifecycle_pipeline_v5.py

# 방법론 비교
python thesis_supplement/run_methodology_comparison.py
```

**출력**:
- `thesis_supplement/outputs/methodology_comparison_crosstab.csv`
- `thesis_supplement/outputs/methodology_comparison_match_rates.csv`

---

## 3. 논문 목차와의 매핑

| 논문 장 | 내용 | 관련 스크립트 |
|---------|------|---------------|
| 2장 | 기존 방법론 한계, 하이브리드 제안 | 방법론 비교 |
| 3.2 | Multinomial Logit | 260301/260225 (기존) |
| 4장 | 초기 30주 예측 | 30주 예측 보강 |
| 3b | Event Study | Event Study (new_customer_ratio) |

---

## 4. 논문 작성 시 권장 사항

1. **30주 예측**: F1만 보고하지 말고 AUC-ROC, PR-AUC, 혼동행렬 추가
2. **Event Study**: new_customer_ratio 사용 시 "동어반복 없는 지표"로 명시
3. **방법론**: v5 vs final_code 비교 결과를 방법론 선택 근거로 활용
4. **클래스 불균형**: `class_weight="balanced"` 적용 여부와 성능 변화 기술

---

## 5. 트러블슈팅

| 문제 | 해결 |
|------|------|
| `df_base_features` 없음 | `python 260301/run_all.py` 먼저 실행 |
| `final_code` 없음 | 260204_gem 파이프라인 실행 |
| `lifecycle_features_v5.csv` 없음 | `python 260309_claude/lifecycle_pipeline_v5.py` 실행 |
| weekly.parquet 없음 | `weekly_reduced.parquet` 사용 (Event Study용) |
| 메모리 부족 | `weekly_reduced.parquet` 사용 |

---

*작성일: 2026-03-09*
