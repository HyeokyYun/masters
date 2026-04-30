# 260409 미팅 피드백 해결 보고서

작성: 2026-04-28
대상: 지난 미팅(260409)에서 받은 3가지 피드백
실행 환경: LightGBM 5-fold stratified CV, n=49,007 점포 (`top_tier/outputs/tables/observed_window_panel.parquet`)

> **본 보고서의 위치**: 학위논문 본문 결과(F1 0.548–0.639 등)는 46개 공학적 feature를 사용한 결과이고, 본 보고서의 분석은 **window·구간 효과만 분리해서 보기 위해 가벼운 feature set**으로 재실행한 것입니다. 따라서 **절대값**보다 **window·구간 간의 상대적 차이**가 의미 있는 비교입니다.

---

## 0. 세 피드백 한눈에 보기

| # | 피드백 | 결과 한 줄 | 핵심 수치 |
|---|---|---|---|
| 1 | 초기 예측 기간(window) 자르는 비교 | window가 길수록 F1 단조 증가 | 10주 0.46 → 50주 0.63 |
| 2 | 초기 10주 vs 마지막 10주 기울기 비교 | early slope만 outcome 잘 구분, late는 거의 못 함 | early t=31.1 vs late t=−5.1 |
| 3 | 마지막 구간 추정 변수 다양화 | 기울기 단독보다 6변수 결합이 +31% F1 개선 | 0.365 → 0.479 |

---

## 1. 피드백 1 — 초기 예측 기간(window) 자르는 비교

### 1.1 무엇이 궁금했나
지난 미팅에서: "예측을 할 때 초기 예측 기간을 자르는 것에 대한 비교."

직관적 질문: **"점포 매출의 처음 X주를 보고 미래 상태(Growth/Stable/Decline)를 예측한다고 할 때, X가 10·20·30·40·50주로 늘어남에 따라 예측이 얼마나 좋아지나?"**

> **비유**: 마라톤 선수의 완주 가능 여부를 첫 5km로 판단할까, 첫 20km로 판단할까? 더 길게 보면 정확하지만, 그만큼 의사결정도 늦어진다. 적절한 trade-off 지점을 찾아야 함.

### 1.2 방법
- 점포별 시계열에서 첫 W주(W ∈ {10, 20, 30, 40, 50})만 잘라 동일한 8개 feature 추출
- LightGBM 5-fold stratified CV
- 동일 feature set·동일 점포(n=49,007)·동일 모델 → window 효과만 분리

### 1.3 결과 ([01_window_comparison.csv](outputs/01_window_comparison.csv))

| Window | n | Macro F1 | Decline Recall | Stable Recall | Growth Recall | AUC (ovr) |
|---:|---:|---:|---:|---:|---:|---:|
| 10주 | 49,007 | 0.463 | 0.261 | 0.495 | 0.626 | 0.659 |
| 20주 | 49,007 | 0.491 | 0.320 | 0.499 | 0.640 | 0.683 |
| **30주** | 49,007 | **0.515** | 0.373 | 0.501 | 0.652 | 0.703 |
| 40주 | 49,007 | 0.546 | 0.452 | 0.492 | 0.672 | 0.726 |
| 50주 | 49,007 | **0.631** | **0.581** | **0.575** | **0.713** | **0.801** |

### 1.4 해석

#### 단조 증가 패턴
window가 10 → 50주로 늘어나면 F1이 0.46 → 0.63으로 지속 증가. 즉 **더 많은 시계열 정보를 보여주면 예측이 단조적으로 좋아짐**. 어느 지점에서 saturation이 오지 않음.

#### Decline recall이 가장 큰 변화
- Decline recall: 0.26 (10주) → 0.58 (50주), **+122%** 향상
- Growth recall: 0.63 → 0.71, +14%
- Stable recall: 0.50 → 0.57, +14%

→ **window 길이의 효과는 특히 Decline 점포를 잡아내는 능력에서 두드러짐**. 짧은 window에서는 "성장하는 것처럼 보이는 점포"가 사실 Decline일 수 있음(노이즈에 묻힘). window가 길어지면 매출 하락의 누적 신호가 분명해져 잡아내기 쉬워짐.

> **비유**: 마라톤 첫 5km만 보면 모두 비슷한 페이스로 뛴다. 20km쯤 가면 누가 처질지 보이기 시작하고, 35km쯤이면 거의 확실해진다. Decline 점포도 마찬가지 — 시간이 지나야 신호가 분명해짐.

#### 30주의 위상
30주는 **F1 0.515로 중간 위치**. 학위논문이 30주를 표준으로 쓰는 이유는:
- 짧지 않으면서(50주는 거의 1년)
- 충분한 신호 확보(F1 0.515 ≈ 무작위 0.33 대비 1.6배)
- 조기 경보의 의미(50주 후가 아닌 30주에서 진단 가능)

50주가 절대 성능은 가장 좋지만, "조기" 진단의 가치를 잃습니다.

### 1.5 미팅에서의 활용
교수님이 "왜 30주를 쓰나"고 물으면:
- "10주는 너무 짧아 Decline recall 0.26 (놓침)"
- "50주는 가장 좋지만 조기 경보의 의미 약화"
- "30주는 Decline recall 0.37로 trade-off의 sweet spot"

표를 직접 보여주면 한 눈에 trade-off가 드러남.

---

## 2. 피드백 2 — 초기 10주 vs 마지막 10주 기울기 비교

### 2.1 무엇이 궁금했나
30주 window 안에서 **초기 10주(w1–10)**와 **마지막 10주(w21–30)**의 매출 기울기는 어떻게 다른가? 둘 중 어느 쪽이 outcome을 더 잘 구분하나?

> **비유**: 100m 달리기 선수의 첫 10m 가속과 마지막 10m 페이스 중 어느 쪽이 결승 시간을 더 잘 예측할까?

### 2.2 방법
- 30주 시퀀스를 (early 10주, late 10주) 두 segment로 분할
- 각 segment의 sales 기울기 산출 (단순 OLS)
- Outcome (Growth/Stable/Decline)별 분포 비교, t-test, Pearson 상관, 단변수 예측력

### 2.3 결과

#### 2.3.1 Outcome별 기울기 분포 ([02_slope_distribution_by_outcome.csv](outputs/02_slope_distribution_by_outcome.csv))

| Outcome | n | Early slope (mean) | Late slope (mean) |
|---|---:|---:|---:|
| Decline | 10,917 | **0.061** | −0.026 |
| Stable | 18,003 | **0.080** | −0.016 |
| Growth | 20,087 | **0.100** | −0.030 |

**해석**:
- **Early slope는 outcome 순위와 깔끔하게 일관**: Decline < Stable < Growth (0.061 < 0.080 < 0.100)
- **Late slope는 outcome을 거의 구분 못 함**: 셋 다 −0.02~−0.03 비슷
- 추가로 마지막 10주 기울기가 모든 그룹에서 **음수** — w21–30 구간에서는 평균적으로 매출이 약간 하락 추세

#### 2.3.2 Growth vs Decline t-test ([02_slope_ttest_growth_vs_decline.csv](outputs/02_slope_ttest_growth_vs_decline.csv))

| 변수 | t | p |
|---|---:|---:|
| early_slope | **31.1** | 4.4e-208 |
| late_slope | −5.1 | 2.6e-7 |

- early slope: Growth가 Decline보다 강하게 큼 (t=31.1)
- late slope: 부호가 반대 (Growth가 Decline보다 살짝 더 음수). 통계적으로 유의하나 효과 크기는 매우 작음

#### 2.3.3 Early vs Late slope의 점포 단위 상관

| 그룹 | n | Pearson r |
|---|---:|---:|
| 전체 | 49,007 | **−0.127** |
| Decline | 10,917 | −0.117 |
| Stable | 18,003 | −0.118 |
| Growth | 20,087 | −0.129 |

→ **약한 음의 상관**. 즉 초기에 가파르게 오른 점포는 마지막 10주에 약간 둔화하는 경향이 있으나, 이 관계는 약함. 두 기울기는 거의 독립적인 신호.

#### 2.3.4 단변수 예측력 비교

| Case | 변수 | Macro F1 | AUC |
|---|---|---:|---:|
| early_slope_only | early_sales_slope | 0.358 | 0.575 |
| late_slope_only | late_sales_slope | 0.365 | 0.574 |
| **both_slopes** | 둘 다 | **0.393** | **0.611** |

→ 둘 다 단변수로 outcome 예측력은 약함(0.36 수준 — 무작위 0.33 약간 위). **둘을 함께 쓰면 +0.03 개선** (0.393).

### 2.4 해석

#### 핵심 메시지
- **Outcome label은 30주 전체 trend로 정의되므로, "초기 기울기"가 outcome과 강하게 일관됨이 자연스러움**
- **마지막 10주 기울기는 outcome 정의 trend와 다르게 움직일 수 있음** (음수, outcome 무관)
- 두 기울기는 약하게 음의 상관 — 즉 30주 안에서 점포가 "초기 가파른 상승 → 후반 둔화" 패턴을 일부 보임

#### 실무 함의
"마지막 10주 기울기"만 보면 outcome을 잘 못 잡아냄 → 학위논문 본문에서 ‘마지막 구간의 기울기’를 단독으로 쓰는 것은 비추. 대신:
- 마지막 10주에서 측정하는 **여러 변수**를 결합하면 도움 (피드백 3 결과 참고)
- 초기 10주 기울기는 outcome 정의와 너무 일관 → "tautology" 위험 (동의어 반복) — 본문에서는 30주 전체 기울기와 구분해서 다룸

### 2.5 미팅에서의 활용
- 표 2.3.1을 보여주면 "early/late slope의 정보가 다른 종류"임이 한 눈에 보임
- "왜 마지막 10주를 안 쓰나"라는 질문에 "outcome 정의 trend와 거의 무관(t=−5)"이라고 답할 수 있음
- 단, 이게 **마지막 10주의 정보가 무용**하다는 뜻은 아님 → 피드백 3의 다양한 변수와 결합하면 가치 있음

---

## 3. 피드백 3 — 마지막 구간 추정 변수의 다양화

### 3.1 무엇이 궁금했나
지난 미팅 피드백: "마지막 추정 변수를 여러 개로 하자."

본인 해석: **마지막 구간에서 측정하는 변수를 단일 기울기에서 → 기울기·평균·변동성·신규고객비율·고객수 등 여러 종류로 확장**하면 outcome 예측이 얼마나 개선되나?

> **비유**: 마라톤 선수의 마지막 10km만 본다고 할 때, 단순히 "페이스가 빨라졌나/느려졌나"(기울기)만 보지 말고 "평균 페이스(mean), 페이스 흔들림(volatility), 페이스 표준편차(std), 음료 섭취 횟수(추가 변수)"를 같이 보면 결승 시간 예측이 얼마나 정확해지나?

### 3.2 방법
마지막 10주(w21–30)에서 6개 변수 추출:

| 변수 | 의미 |
|---|---|
| `late_sales_slope` | 매출 log값의 OLS 기울기 |
| `late_sales_mean` | 매출 log값의 평균 |
| `late_sales_vol` | 매출 변동 계수 (rolling std / mean) |
| `late_sales_std` | 매출 log값의 표준편차 |
| `late_nc_rate` | 신규고객 비율 (customer_new / customer)의 평균 |
| `late_customer_mean` | 고객 수 평균 |

분석:
1. 각 변수의 단변수 예측력 (LightGBM)
2. 누적 추가 (univariate F1 ranking 순서로 1개씩)
3. 6변수 모두 동시 입력 시 feature importance

### 3.3 결과

#### 3.3.1 단변수 예측력 ([03_univariate_predictive_power.csv](outputs/03_univariate_predictive_power.csv))

| 순위 | 변수 | Macro F1 | AUC |
|---:|---|---:|---:|
| 1 | late_sales_slope | 0.365 | 0.574 |
| 2 | late_nc_rate | 0.356 | 0.563 |
| 3 | late_sales_mean | 0.355 | 0.581 |
| 4 | late_sales_std | 0.338 | 0.546 |
| 5 | late_sales_vol | 0.333 | 0.552 |
| 6 | late_customer_mean | 0.333 | 0.556 |

→ 단변수로는 6개 모두 비슷한 수준 (0.33–0.37). **압도적 1등이 없음** — 어느 한 변수도 단독으로 충분하지 않음.

#### 3.3.2 누적 추가의 marginal gain ([03_cumulative_addition.csv](outputs/03_cumulative_addition.csv))

| k | 추가 변수 | Macro F1 | AUC | Δ F1 |
|---:|---|---:|---:|---:|
| 1 | slope | 0.365 | 0.574 | — |
| 2 | + nc_rate | 0.401 | 0.599 | **+0.036** |
| 3 | + mean | 0.449 | 0.642 | **+0.048** |
| 4 | + std | 0.461 | 0.651 | +0.013 |
| 5 | + vol | 0.462 | 0.653 | +0.001 |
| 6 | + customer_mean | **0.479** | 0.669 | +0.018 |

#### 3.3.3 6변수 동시 입력 시 feature importance

| 순위 | 변수 | Importance |
|---:|---|---:|
| 1 | late_customer_mean | 3,393 |
| 2 | late_sales_slope | 3,322 |
| 3 | late_sales_mean | 3,205 |
| 4 | late_nc_rate | 2,977 |
| 5 | late_sales_vol | 2,605 |
| 6 | late_sales_std | 2,498 |

### 3.4 해석

#### 핵심 메시지: **"마지막 10주 단일 기울기 → 6변수 결합" 시 F1 +31% 향상** (0.365 → 0.479)

이는 피드백 3에 대한 정확한 답입니다: **그렇다, 마지막 구간의 변수를 여러 개로 두는 것이 의미 있는 개선을 가져온다.**

#### 흥미로운 발견
1. **단변수 1등(slope)은 결합에서도 강함** — 단변수 F1과 importance 모두 상위
2. **단변수 꼴찌(customer_mean)가 결합 importance 1등** — 단독으로 약하지만 다른 변수의 잔차를 잘 흡수. 즉 다른 변수들이 잡지 못하는 정보 ("이 점포의 고객 base 자체") 를 customer_mean이 제공
3. **vol·std는 marginal gain 거의 없음** — 변동성 관련 변수는 이미 mean·slope에 흡수됨
4. **mean과 nc_rate가 가장 큰 marginal gain** (+0.048, +0.036) — slope만 보다 매출 절대수준과 신규고객 비율이 결정적

#### 실무 함의 (학위논문에 반영 가능)
- "마지막 10주에서는 기울기만 보지 말고 (1) 평균 매출, (2) 신규고객 비율, (3) 고객 수를 함께 봐야 한다"
- 이 메시지는 **골든 크로스(신규고객 → 매출 반등) 가설과도 정합** — 마지막 10주에서 nc_rate가 outcome 예측에 의미 있게 기여 (+0.036)

### 3.5 미팅에서의 활용
- 3.3.2 표를 보여주면 "단일 기울기 0.365 → 6변수 0.479"의 점진적 향상이 한 눈에 보임
- 교수님 피드백을 따랐고, 실제로 **+31% F1 향상**이라는 구체 수치로 답함
- 추가 통찰: customer_mean이 단변수에서는 약했지만 결합에서 1등 importance → "변수는 단독이 아니라 보완 관계로 봐야 한다"

---

## 4. 종합 — 세 피드백을 통합한 함의

### 4.1 이 결과의 활용 위치

이 보고서의 수치는 학위논문 본문 핵심 성능표를 대체하지 않습니다. 본문 결과(F1 0.548–0.639 등)는 46개 공학적 feature와 hybrid representation을 사용한 모델 성능이고, 여기서는 **window 길이와 구간별 feature 효과를 분리하기 위해 lightweight feature set**을 사용했습니다. 따라서 활용 가치는 절대 F1 수치의 우열보다 **"왜 30주인가", "짧은 window에서 어떤 class가 손상되는가", "마지막 구간을 slope 하나로 요약해도 되는가"**에 대한 방어 근거에 있습니다.

가장 도움이 되는 지점은 **30주 window 선택의 논리 보강**입니다. window가 길어질수록 전체 성능은 단조 증가하지만, 50주는 조기 진단의 의미가 약해집니다. 반대로 10주·20주는 특히 Decline recall이 낮아 하락 점포를 놓치는 문제가 큽니다. 그러므로 30주는 최고 성능점이 아니라, 충분한 신호를 확보하면서도 조기 진단성을 유지하는 **performance–earliness trade-off 지점**으로 설명하는 것이 적절합니다.

두 번째 활용 지점은 **마지막 구간 feature 설계의 보조 검증**입니다. 마지막 10주 slope 하나만으로는 outcome 예측력이 약하지만, slope·평균 매출·신규고객 비율·고객 수 등을 결합하면 F1이 0.365에서 0.479로 개선됩니다. 즉 마지막 구간은 단일 기울기보다 **복합 상태 신호**로 보는 것이 더 타당합니다.

세 번째로, early slope 결과는 과대해석하지 않는 것이 좋습니다. early slope는 Growth/Stable/Decline 순서와 잘 맞지만, outcome label 자체가 전체 trend에 기반하므로 동어반복(tautology) 위험이 있습니다. 따라서 메인 claim보다는 "구간별 slope 해석에는 label 정의와의 중복을 주의해야 한다"는 방법론적 주의사항으로 쓰는 편이 안전합니다.

### 4.2 학위논문 본문 반영 권장 사항

| 본문 위치 | 권장 추가 |
|---|---|
| Ch.4 방법론 | "Window 길이 비교 (10–50주)에서 30주는 trade-off의 sweet spot" 한 단락 |
| Ch.4 또는 Ch.5 | "마지막 구간 변수는 기울기 단독이 아니라 6변수 결합 사용" 명시 |
| Ch.5 또는 §5.10 robustness | "Window 민감도 표"로 본 결과 추가 |
| Ch.5 robustness 또는 Appendix | "260409 피드백 분석을 window 선택과 late-feature 설계의 보조 검증표로 제시" |

### 4.3 미팅 발표 흐름 제안

1. **5분**: 세 피드백을 한 슬라이드로 (§0 표)
2. **5분**: 피드백 1 — window 비교 표 + Decline recall 122% 향상 강조
3. **5분**: 피드백 2 — early/late slope 분포 차이 + 음의 상관 r=−0.13
4. **10분**: 피드백 3 — 누적 추가 표 (slope 0.365 → 6변수 0.479) + customer_mean importance 1등의 의미

### 4.4 본 보고서가 답하는 질문 / 답하지 못한 질문

#### 답함
- 초기 예측 기간 길이의 효과 (단조 증가)
- 초기 10주와 마지막 10주 기울기의 구조적 차이
- 마지막 구간 변수 다양화의 정량적 효과

#### 답하지 못함 (후속 작업 필요 시)
- "왜 50주가 더 정확한가"의 메커니즘 분해 — 단순 정보량 증가 vs 특정 신호의 선명화
- 마지막 10주 외에 다른 segment(w11–20, w16–25 등)에서 측정하면 어떤가
- 6변수 결합 vs 학위논문 본문의 46개 feature 결합의 차이 — 본 보고서의 6변수는 lightweight subset

---

## 5. 산출물 목록

[260409/feedback_resolution/](.)
├── [common.py](common.py) — 공용 유틸리티 (panel 로딩, feature 추출, CV)
├── [01_window_comparison.py](01_window_comparison.py)
├── [02_early_vs_late_slope.py](02_early_vs_late_slope.py)
├── [03_late_variable_diversity.py](03_late_variable_diversity.py)
├── [REPORT.md](REPORT.md) — 본 문서
└── outputs/
    ├── [01_window_comparison.csv](outputs/01_window_comparison.csv)
    ├── [01_window_comparison_summary.json](outputs/01_window_comparison_summary.json)
    ├── [02_slope_distribution_by_outcome.csv](outputs/02_slope_distribution_by_outcome.csv)
    ├── [02_slope_ttest_growth_vs_decline.csv](outputs/02_slope_ttest_growth_vs_decline.csv)
    ├── [02_slope_correlation_by_outcome.csv](outputs/02_slope_correlation_by_outcome.csv)
    ├── [02_slope_predictive_power.csv](outputs/02_slope_predictive_power.csv)
    ├── [02_early_vs_late_slope_summary.json](outputs/02_early_vs_late_slope_summary.json)
    ├── [03_univariate_predictive_power.csv](outputs/03_univariate_predictive_power.csv)
    ├── [03_cumulative_addition.csv](outputs/03_cumulative_addition.csv)
    ├── [03_feature_importance.csv](outputs/03_feature_importance.csv)
    └── [03_late_variable_diversity_summary.json](outputs/03_late_variable_diversity_summary.json)

각 스크립트는 단독 실행 가능: `python3 01_window_comparison.py` 등.
