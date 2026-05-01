# 제4장 방법론

본 장은 본 연구의 핵심 방법론, 즉 시즌 정렬 rolling-window 설계, G/S/D
라벨 생성, 가변 윈도우 피처 추출, A/B/C/D 모델 비교 프로토콜, 평가 지표를
순서대로 기술한다. 모든 절차는 `260430_claude/src/step0[1-5]*.py` 다섯 개
스크립트에 그대로 구현되어 있어 재현 가능하다.

## 4.1 분석 프레임

각 specification은 `(start_year, start_month, window_months, target_offset)`
4-튜플로 정의된다. 이 4-튜플로부터 다음 두 시간 구간이 결정된다.

- **Feature window** — `start_year`-`start_month`-01부터 `window_months`개월.
  점포의 영업 초기 거래 패턴을 관측하는 구간이며, 입력 피처를 추출하는
  데이터 소스다.
- **Target window** — `start_year + target_offset`-`start_month`-01부터
  `window_months`개월. feature window와 같은 캘린더 월·같은 길이를 가지며,
  점포의 G/S/D 상태 라벨을 정의하는 구간이다.
- **Lag window** — feature 끝 ~ target 시작 사이 구간. 라벨 누설 방지의
  hold-out 영역이며, 본 연구는 lag window 데이터를 사용하지 않는다.

이 설계의 핵심은 **feature와 target이 같은 캘린더 월**이라는 점이다. 시즌
변동(휴가, 명절, 학기, 날씨)이 두 윈도우에 비슷하게 영향을 주므로 시즌
변동을 라이프사이클 신호로 잘못 해석할 위험이 줄어든다. 이 설계는 2026년
4월 30일 지도교수 미팅에서 명시적으로 제안되었다(전사: `thesis/meeting_stt/
260430_personal_meeting.txt`).

## 4.2 컴비네이션 카탈로그

`260430_claude/src/utils_panel.py:enumerate_combos` 함수가 다음 조건을
만족하는 모든 4-튜플을 자동 생성한다.

- `feature_start ≥ 2021-01-01` (데이터 시작)
- `target_start ≤ 2023-08-28` (데이터 컷오프 안에 target 시작이 들어와야 함)

총 84개 후보 중 4개는 target window가 데이터 컷오프를 넘기 때문에 panel
구성 단계(`step01`)에서 0개 점포로 떨어지고, 80개가 유효 specification으로
남는다(`260430_claude/outputs/tables/panel_summary.csv`).

## 4.3 G/S/D 라벨 생성

`260430_claude/src/step02_relabel_gsd_calendar.py`의 절차다.

1. 각 점포의 feature+target 합치기 평균(`store_mean`)으로 매출을 나눠
   정규화한다. 이 정규화는 점포 간 매출 규모 차이를 표준화해 기울기를
   비교 가능하게 한다.
2. 점포의 target window 안의 정규화 매출 시퀀스에 대해 OLS 기울기
   `slope_target`을 계산한다(`utils_panel.row_slopes`). 결측은 NaN-safe
   linear regression으로 처리한다.
3. 점포 간 `slope_target`의 표준편차 σ를 계산하고, 임계값 `thr = 0.5σ`을
   설정한다(`config.SLOPE_THRESHOLD_SIGMA = 0.5`).
4. 라벨링 규칙:
   - `slope_target > thr` → **Growth**
   - `slope_target < -thr` → **Decline**
   - 그 외 → **Stable**
5. target window 안 유효 주차가 3주 미만인 점포는 제외한다.

이 라벨링은 `top_tier/src/step00_prepare_original_panel.py:217-227`의
`outcome_3` 임계값(0.5σ)과 동일한 형태지만, **기울기를 target 구간만에서
계산**한다는 점이 핵심 차이다. 기존 라벨은 전체 기간 기울기(`slope_all_mm`)
를 사용해 시즌이 라벨에 들어갔다.

## 4.4 가변 윈도우 피처 추출

`260430_claude/src/step03_extract_features.py`는 feature window가 4–13주로
가변임을 반영한다. 핵심 피처 43개는 다음 7개 그룹으로 분류된다.

| 그룹 | 피처 |
| --- | --- |
| 매출 통계 | `sales_mean`, `sales_std`, `sales_median`, `sales_min`, `sales_max`, `sales_range`, `sales_cv` |
| 기울기 | `slope_all`, `slope_first_half`, `slope_second_half`, `slope_half_diff` (윈도우 ≥ 6주: `slope_1_3`, `slope_2_3`, `slope_3_3`, `slope_accel`) |
| 이동평균 | 윈도우 ≥ 4주: `ma4_slope`, `ma4_std`, `vol_w4`; 윈도우 ≥ 8주: `ma8_slope`, `ma8_std`, `vol_w8` |
| 신규 고객 | `nc_mean`, `nc_std`, `nc_slope`; 윈도우 ≥ 4주: `nc_last_q`, `nc_first_q`, `nc_delta` |
| 고객 | `cust_slope`, `cust_mean`, `cust_cv` |
| 채널 | `del_mean`, `del_slope`, `bn_mean`, `wk_mean` |
| 분포 | `q25`, `q50`, `q75`, `iqr`; 윈도우 ≥ 3주: `diff_mean`, `diff_std`, `diff_max_abs`, `zero_cross` |

가변 윈도우 처리의 핵심은 윈도우 길이가 짧을 때 의미 없는 피처(예
`slope_1_3`처럼 3등분 슬로프)를 자동으로 skip하는 것이다. 이 설계는 1, 2,
3개월 윈도우 사이의 비교를 가능하게 한다.

피처 추출은 `top_tier/src/step03_prediction_model.py:build_feature_matrix`의
벡터화 패턴을 차용해 점포 5만 개 단위로 효율적으로 계산한다(panel당 처리
시간 약 5–10초).

## 4.5 모델 비교 프로토콜 (A/B/C/D)

`260430_claude/src/step05_train_main_model.py`의 프로토콜이다. 비교 대상은
다음 네 모델이다.

| 코드 | 피처 구성 | 피처 수 |
| --- | --- | --- |
| **A. Baseline** | §4.4의 43개 피처만 | 43 |
| **B. + Cluster** | A + KMeans (k=6) one-hot | 49 |
| **C. + Change-point** | A + change-point 7개 | 50 |
| **D. + Cluster + CP** | A + B + C | 56 |

**B의 클러스터링.** feature window의 점포별 정규화 매출 시퀀스 위에
StandardScaler 적용 후 KMeans(k=6, n_init=10, seed=42)를 학습. 점포별 클러스터
라벨을 6개 더미 변수로 인코딩한다.

**C의 change-point.** 각 점포의 정규화 매출 시퀀스에 대해 max-mean-gap
알고리즘으로 최적 분할 지점을 찾고, 7개 피처 (`cp_position`, `cp_pre_slope`,
`cp_post_slope`, `cp_delta_slope`, `cp_magnitude`, `has_up_cp`, `has_down_cp`)
를 생성한다. 이는 `top_tier/src/step10_hybrid_prediction.py:fast_change_point_features`
의 단순화 버전이다.

**모델·하이퍼파라미터.** 모든 비교 모델은 동일한 RandomForestClassifier
(n_estimators=240, max_depth=14, min_samples_leaf=10, n_jobs=-1,
class_weight="balanced", random_state=42)를 사용한다.

**평가.** 각 모델에 대해 Stratified 5-fold CV(seed=42)로 macro-F1, per-class
recall, per-class F1을 계산한다.

**검정.** A vs D의 통계적 유의성을 per-fold macro-F1에 대한 paired t-test
(자유도 4)로 검정한다(`scipy.stats.ttest_rel`).

## 4.6 시즌 baseline 평가

`260430_claude/src/step04_evaluate_seasonal_baseline.py`는 80개
specification 모두에 대해 RandomForest와 LightGBM 두 모델로 baseline
정확도를 측정한다. 본 단계는 §4.5의 A 모델만 평가하며, 시즌·시작연도·
윈도우 길이별 정확도 분포를 heatmap과 표로 출력한다(§5.2).

LightGBM 설정: n_estimators=200, learning_rate=0.05, num_leaves=63,
min_child_samples=30, subsample=0.9, colsample_bytree=0.9,
class_weight="balanced".

## 4.7 평가 지표

본 연구는 다음 지표를 기본으로 사용한다.

- **Macro-F1** — 세 클래스의 F1을 단순 평균. 라벨 불균형에 robust한 일차
  지표.
- **Per-class recall** — Decline / Stable / Growth 각각의 재현율. 정책
  활용 관점에서는 Decline recall이 가장 중요하다(쇠퇴 점포를 놓치지
  않는지).
- **Per-class F1** — precision과 recall의 조화평균. 클래스별 모델 성능
  세부 점검.
- **5-fold paired t-test** — 모델 비교의 유의성 검정. 자유도 4의 검정력
  한계는 §6.4에서 다룬다.

ROC AUC는 본 연구의 multi-class 설정에서 부수 지표로만 사용한다(보고는 ch5
에 일부 포함).

## 4.8 7개 대표 panel 선정

§4.5의 A/B/C/D 비교는 시즌 baseline 결과(§5.2)에서 다음 기준으로 선정한
7개 panel에서 수행한다.

- 모두 3-month 윈도우(`window_months=3`)와 1년 target offset(`target_offset=1`)
  로 통일.
- 시작연도 2021과 2022 모두 포함(코로나 vs 회복기 비교).
- 시작월은 1, 3, 5, 9월을 중심으로 분포(겨울/봄/초여름/가을 시즌 대표).
- 라벨 분포가 극단적으로 편중되지 않은 panel 위주(데이터 컷오프 근접 panel
  제외).

선정 panel: `sy2021_sm01_w3m_off1`, `sy2021_sm03_w3m_off1`,
`sy2021_sm05_w3m_off1`, `sy2021_sm09_w3m_off1`, `sy2022_sm01_w3m_off1`,
`sy2022_sm03_w3m_off1`, `sy2022_sm05_w3m_off1`. 자세한 선정 근거는 ch5.5
첫 단락에 정리한다.

## 4.9 재현 절차

```bash
cd /home/hyeoky98/kcd
python 260430_claude/src/step01_build_seasonal_panels.py
python 260430_claude/src/step02_relabel_gsd_calendar.py
python 260430_claude/src/step03_extract_features.py
PYTHONUNBUFFERED=1 python -u 260430_claude/src/step04_evaluate_seasonal_baseline.py
PYTHONUNBUFFERED=1 python -u 260430_claude/src/step05_train_main_model.py
```

총 wall clock은 8-core 기준 약 25–35분(step04가 가장 오래 걸림). 모든
random seed는 42로 고정되어 있다.
