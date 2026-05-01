# 260430_claude 설계 문서

## 1. 배경

2026-04-30 개인 미팅(`thesis/meeting_stt/260430_personal_meeting.txt`) 후속.
지도교수가 명시적으로 지적한 두 가지 문제와 그 해결을 코드로 검증한다.

### 1.1 시즈널리티 confound

기존 `top_tier` 파이프라인은 점포의 "초기 N주차"로 피처를 만들고
`slope_all_mm` (전체 정규화 매출 기울기) 또는 마지막 N주차 기울기로
G/S/D 라벨을 생성한다. 데이터가 2021-01-01 ~ 2023-08-28 (142주)이므로
**라벨 구간이 항상 2023년 6–8월(여름 휴가 시즌)에 고정**된다.
이 경우 라이프사이클 신호와 시즈널리티가 분리되지 않는다.

### 1.2 메인 모델 contribution 검증

미팅에서 지도교수는 LEVI/EWS/도시활력 지표는 보강이고, 진짜
아카데믹 contribution은 "베이스라인 + 클러스터 + 체인지 포인트"로
G/S/D 분류 정확도가 향상된다는 결과뿐이라고 정리. 따라서 시즈널 라벨
기준에서 **D = A+B+C** 조합이 베이스라인을 이기는지 재검증해야 한다.

## 2. 컴비네이션 정의

```python
start_year      ∈ {2021, 2022}
start_month     ∈ {1, 2, …, 12}
window_months   ∈ {1, 2, 3}        # 약 4 / 8 / 13 주
target_offset   ∈ {1, 2}           # +1년 후 / +2년 후 같은 캘린더 월
```

조건: feature window와 target window 모두 데이터 범위(2021-01-01 ~
2023-08-28) 안에 들어와야 함. 이 조건으로 후보 84개 중 80개가 살아남았다.

## 3. 라벨 정의 (Step 02)

target window 매출을 점포 평균(feature+target 합치기 평균)으로 정규화한 뒤,
target window 안의 OLS 기울기를 계산.

```python
sigma  = std(slope_target_norm)
thr    = 0.5 * sigma
Growth  if slope > thr
Decline if slope < -thr
Stable  otherwise
```

기존 `top_tier/src/step00_prepare_original_panel.py`의 `outcome_3` 임계값
공식과 동일한 형태(0.5σ)이지만, 슬로프를 **target 구간만**으로 계산한다는
점이 다르다.

## 4. 피처 (Step 03)

`top_tier/src/step03_prediction_model.py:build_feature_matrix`를 가변 윈도우용
으로 변형. 윈도우가 짧으면 `slope_1_3` 같은 3등분 슬로프와 `ma15` 류는 자동
스킵된다. 핵심 피처 목록:

- 매출 통계: `sales_mean/std/median/min/max/range/cv`
- 기울기: `slope_all`, `slope_first_half`, `slope_second_half`, `slope_half_diff`
  (윈도우가 길면 `slope_1_3 / 2_3 / 3_3`, `slope_accel` 추가)
- 이동평균: `ma4_*`, `ma8_*`, `vol_w4`, `vol_w8`
- 신규 고객: `nc_mean/std/slope/last_q/first_q/delta`
- 고객: `cust_slope/mean/cv`
- 채널 비율: `del_mean/slope`, `bn_mean`, `wk_mean`
- 분포: `q25/q50/q75/iqr`, `diff_*`, `zero_cross`

## 5. 모델

**Step 04 (시즈널 베이스라인 평가):**
- RandomForest (200 trees, depth 12, class_weight=balanced)
- LightGBM (300 trees, lr 0.05, num_leaves 63, class_weight=balanced)
- Stratified 5-fold CV

**Step 05 (메인 contribution 검증):**
- A: baseline (Step 03 피처)
- B: A + KMeans cluster one-hot (k=6, on 정규화 매출 시퀀스)
- C: A + change-point 7개 피처 (`top_tier/src/step10_hybrid_prediction.py`의
  `fast_change_point_features` 단순화 버전)
- D: A + B + C
- 5-fold paired t-test (D vs A)

## 6. 출력 파일

| 단계 | 위치 | 내용 |
| --- | --- | --- |
| 01 | `outputs/tables/panels/` | 80개 조합별 panel parquet |
| 01 | `outputs/tables/panel_summary.csv` | 조합별 점포 수, 윈도우 정의 |
| 02 | `outputs/tables/labels/` | 조합별 라벨 parquet |
| 02 | `outputs/tables/label_distribution.csv` | 조합별 G/S/D 비율 |
| 03 | `outputs/tables/features/` | 조합별 피처 parquet |
| 04 | `outputs/tables/seasonal_results_long.csv` | fold 단위 결과 |
| 04 | `outputs/tables/seasonal_results_summary.csv` | 조합×모델 평균/표준편차 |
| 04 | `outputs/figures/heatmap_*.png` | 시작월 × 윈도우 길이 히트맵 |
| 05 | `outputs/tables/main_model_compare.csv` | A/B/C/D 비교 |
| 05 | `outputs/tables/main_model_paired_AvD.csv` | 페어드 t-test |
| 05 | `outputs/figures/main_model_*.png` | 막대 그래프 |

## 7. Out of scope

- LEVI 도시경제 활력 지수.
- EWS 조기 쇠퇴 경보.
- 외부 공공 데이터 5종 추가 검증.
- 점포 메타(업종, 자치구) 기반 stratified 분석.
- 코로나 효과 분리 (2021 시작 panel과 2022 시작 panel을 직접 비교하는 정도까지만).
