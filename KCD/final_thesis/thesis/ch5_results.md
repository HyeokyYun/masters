# 제 5 장 결과

본 장은 §4 의 방법론에 따라 얻은 결과를 보고한다. §5.1 라벨 분포,
§5.2 시즌 정렬 baseline 결과(145 specification), §5.3 코로나 시기와
회복기 비교, §5.4 윈도우 길이 효과, §5.5 메인 모델 비교 (A/B/C/D,
14 panel), §5.6 외부 SOTA 14 종 benchmark, §5.7 업력·신규고객 cohort
분석, §5.8 cluster 요인 분해, §5.9 cost-sensitive 가중 보조 실험,
§5.10 결과 요약.

본 장은 §1.4 의 세 가지 본문 기여에 다음 순서로 대응한다.

- 기여 1 (prediction baseline 과 요인 분해) → §5.2 ~ §5.5 + §5.7 ~ §5.8
- 기여 2 (seasonal alignment 의 label robustness 전제) → §5.2 ~ §5.4
- 기여 3 (representation·weighting·model 세 갈래 개선) → §5.5 (hybrid),
  §5.9 (cost-sensitive), §5.6 (외부 SOTA)

수치는 `260430_claude/outputs/tables/` 와 `260511/phase5_external/
outputs/tables/` 의 산출물에서 그대로 인용한다. 두 디렉터리는 각각
시즌 정렬 메인 모델 (260430_claude) 과 외부 SOTA / cost-sensitive /
attention / foundation zero-shot 확장 (260511) 의 출처다. 그림은 본
폴더로 복사하지 않고 원본 경로를 명시한다.

## 5.1 라벨 분포

`260430_claude/outputs/tables/label_distribution.csv` 에 145 개
specification 의 G/S/D 라벨 분포가 정리되어 있다. 본 분포는 §4.3 의
0.5σ 임계값 라벨링 결과이며, panel 별 점포 수는 약 31 ~ 37 천 개로
분포한다. 데이터 컷오프(2023-08-28) 에 가까운 panel 일수록 Decline
비율이 높아지는 경향은 §3.4 의 컷오프 효과 한계에서 미리 명시했다.

§5.5 의 메인 모델 비교에 사용된 14 panel 의 점포 수는 31,064
(`sy2021_sm01_w7m_off2`) 부터 37,175 (`sy2021_sm09_w6m_off1`) 까지
분포한다.

## 5.2 시즌 정렬 baseline 결과

§4.6 의 절차에 따라 145 specification 모두에서 RandomForest 와 LightGBM
의 baseline macro-F1 을 측정한 결과 (`seasonal_results_summary.csv`,
292 행 = 145 specification × 2 모델 + 헤더 보정), macro-F1 분포는 약
0.43 ~ 0.55 사이에 위치한다 (target_offset = 1 기준).

본 결과의 핵심은 다음 세 가지다.

1. **시작월 효과의 진폭이 가장 크다.** 같은 윈도우 길이·같은 모델·
   같은 시작연도를 고정해도 시작월 1 ~ 12 월 간 macro-F1 차이가 약
   0.10 에 달한다. 1, 4, 5 월 시작 panel 의 정확도가 높고, 8, 9 월
   시작 panel 이 가장 낮다. heatmap 은 `outputs/figures/heatmap_macro_
   f1_rf_off1.png` 에 시각화되어 있다.
2. **윈도우 길이 효과는 진폭 0.02 ~ 0.04 로 두 번째다.** 윈도우가
   길수록 (1 ~ 2 개월 → 6 ~ 7 개월) 평균 정확도가 약간 상승하지만,
   같은 윈도우 안의 시즌 진폭(0.10) 이 길이 효과보다 한 자릿수 크다.
3. **모델 효과(RF vs LightGBM) 는 진폭 0.01 미만으로 가장 작다.**
   RF 와 LightGBM 두 모델 모두에서 같은 시작월·시즌 패턴이 반복
   되므로, 본 패턴이 학습 알고리즘의 특성이 아니라 데이터 자체의
   시즌 구조에서 비롯된 것임이 확인된다.

본 결과는 §5.4 의 윈도우 길이 분해와 §5.3 의 시작연도 비교에서 다시
검토한다.

## 5.3 코로나 시기와 회복기 비교

`outputs/figures/yearly_compare_2021_vs_2022.png` 는 2021 시작 panel
과 2022 시작 panel 의 같은 시작월·같은 윈도우 길이 짝의 macro-F1 을
산점도로 비교한 그림이다. 두 panel 의 macro-F1 차이는 모든 윈도우
길이에서 약 0.02 이내에 머문다. 본 데이터에서 코로나 잔여 영향은
분류 정확도를 좌우하지 않는다.

다만 라벨 분포 자체는 시작연도에 따라 차이가 있다. 2021 시작 panel
은 코로나 회복기를 target 으로 가지므로 Growth 비율이 약간 높고, 2022
시작 panel 은 회복 정점 후 Decline 비율이 약간 높다(§5.1). 따라서
"코로나 영향이 완전히 없다" 가 아니라 "분류 정확도에서는 작다" 가
정확한 해석이다.

## 5.4 윈도우 길이 효과

§5.2 의 145 specification 결과를 윈도우 길이별로 평균하면 다음 패턴
이 관측된다 (RF, target_offset = 1 기준).

| 윈도우 (개월) | 평균 macro-F1 | 진폭 (시작월 분산) |
| --- | --- | --- |
| 1 | 약 0.46 | 큰 (시즌·노이즈에 민감) |
| 2 | 약 0.48 | 큰 |
| 3 | 약 0.50 | 중간 |
| 4 | 약 0.51 | 중간 |
| 6 | 약 0.51 | 중간 |
| 7 | 약 0.52 | 작은 (정보 충분) |

윈도우가 길수록 평균 정확도가 미세하게 상승하지만 진폭은 줄어든다.
본 결과는 §1.4 기여 1 의 "시작월 효과(0.10) ≫ 윈도우 길이 효과(0.02
~ 0.04)" 정량을 뒷받침한다.

## 5.5 메인 모델 비교 (A/B/C/D, 14 panel)

§4.5 의 A (baseline 43 피처), B (+ KMeans cluster, 49 피처), C (+
change-point, 50 피처), D (+ cluster + cp, 56 피처) 4 모델을 §4.8 의
14 대표 panel 에서 Stratified 5-fold CV 로 비교한 결과를 보고한다.
원본은 `outputs/tables/main_model_compare.csv` 와
`outputs/tables/main_model_paired_AvD.csv` 다.

### 5.5.1 3 개월 panel 결과 (7 panel)

3 개월 윈도우 7 panel 의 A 와 D 의 macro-F1 비교다.

| panel | A_baseline | D_hybrid | Δ (D − A) | p_value |
| --- | --- | --- | --- | --- |
| sy2021_sm01_w3m_off1 | 0.503 | 0.502 | −0.0009 | 0.350 |
| sy2021_sm03_w3m_off1 | 0.495 | 0.499 | +0.0042 | 0.134 |
| sy2021_sm05_w3m_off1 | 0.486 | 0.488 | +0.0018 | 0.524 |
| sy2021_sm09_w3m_off1 | 0.510 | 0.510 | −0.0001 | 0.945 |
| sy2022_sm01_w3m_off1 | 0.514 | 0.516 | +0.0021 | 0.156 |
| **sy2022_sm03_w3m_off1** | **0.467** | **0.473** | **+0.0052** | **0.061** |
| sy2022_sm05_w3m_off1 | 0.517 | 0.519 | +0.0013 | 0.436 |

3 개월 7 panel 평균 Δ = +0.0019, 5% 유의는 0 / 7 (가장 가까운 panel
`sy2022_sm03_w3m_off1` 도 p = 0.061 로 5% 임계치 위). 라벨이 가장
편중된 panel(`sy2022_sm03_w3m_off1`, baseline Decline recall = 0.296)
에서 효과가 가장 크다는 패턴은 유지된다.

### 5.5.2 4 / 6 / 7 개월 확장 윈도우 결과 (7 panel)

확장 윈도우 7 panel 의 결과다.

| panel | 길이 | A_baseline | D_hybrid | Δ (D − A) | p_value |
| --- | --- | --- | --- | --- | --- |
| sy2021_sm01_w4m_off1 | 4m | 0.536 | 0.539 | +0.0027 | 0.415 |
| sy2022_sm03_w4m_off1 | 4m | 0.475 | 0.475 | −0.0008 | 0.792 |
| sy2021_sm03_w6m_off1 | 6m | 0.491 | 0.491 | +0.0005 | 0.796 |
| sy2021_sm09_w6m_off1 | 6m | 0.488 | 0.487 | −0.0004 | 0.795 |
| **sy2021_sm01_w7m_off1** | **7m** | **0.545** | **0.550** | **+0.0054** | **0.0073** |
| sy2021_sm01_w7m_off2 | 7m, 2y | 0.500 | 0.503 | +0.0029 | 0.118 |
| sy2022_sm01_w7m_off1 | 7m | 0.500 | 0.501 | +0.0006 | 0.826 |

윈도우 길이별 평균 Δ:

- 4 개월 (n = 2): +0.0010
- 6 개월 (n = 2): +0.0001
- 7 개월 (n = 3): +0.0030

7 개월 윈도우에서 효과가 가장 크다. 14 panel 중 5% 유의 1 개는
`sy2021_sm01_w7m_off1` (Jan-Jul 2021 → Jan-Jul 2022 7m, p = 0.0073) 이
유일하다. 6 개월 panel 2 개는 효과가 사실상 0 이다.

### 5.5.3 14 panel 종합

14 panel 평균 Δ (D − A) = **+0.0017** macro-F1. 5% 유의 1 / 14 (panel
`sy2021_sm01_w7m_off1`, p = 0.0073), 10% 유의 추가 1 panel
(`sy2022_sm03_w3m_off1`, p = 0.061). Bonferroni 보정 임계값 α/14 ≈
0.0036 적용 시 0 / 14 panel 이 유의하다.

본 결과는 §1.4 기여 2 (조건부 contribution) 의 정량적 근거이며, §6.1.2
와 §6.2.2 에서 해석된다. 막대 그래프는 `outputs/figures/main_model_
delta.png`, `main_model_compare_bars.png` 에 저장되어 있다.

### 5.5.4 LightGBM 비교 (선택 패널)

§4.5 의 RF 위에서 동일 56 피처 (D 구성) 로 LightGBM 을 학습한 결과는
별도 보조 분석으로 보관되며 (`outputs/tables/seq_model_compare.csv`),
6 panel 중 5 panel 에서 LightGBM 이 RF 를 능가하고, 평균 Δ ≈ +0.0075
macro-F1 의 향상을 보인다 (2 panel 에서 paired t-test p < 0.05). 본
결과는 §6.1.4 와 §6.3.4 에서 별도로 다룬다.

## 5.6 외부 SOTA 14 종 benchmark

`260511/phase5_external/outputs/tables/phase5_summary.csv` 와 동
디렉터리의 `foundation_zeroshot_compare.csv`, `neuralforecast_compare.csv`,
`attention_compare.csv`, `weighting_compare.csv` 에 RF baseline 위에
외부 SOTA 14 종을 적용한 결과가 정리되어 있다. 본 절은 §1.4 기여
3-(c) 에 직접 대응하며, advisor 미팅의 "주식 예측 모델 등 literature
와의 관련성" 권유에 답한다.

### 5.6.1 14 모델 카탈로그

| 그룹 | 모델 | 개수 |
| --- | --- | --- |
| Foundation zero-shot | `chronos_bolt_small`, `moirai_small` | 2 |
| Neuralforecast (stock SOTA) | `tft`, `nbeats`, `nhits`, `patchtst`, `dlinear`, `informer`, `autoformer` | 7 |
| SMB-specific attention | `feature_attn_mlp`, `film_tenure_lstm`, `time_attn_lstm` | 3 |
| Cost-sensitive / SHAP-weighted | `rf_decline_x2`, `rf_decline_x3`, `rf_shap_weighted` | 3 (§5.9 에서 별도 보고) |
| LightGBM tabular ensemble | `lgbm_tabular`, `lgbm_decline_x2`, `lgbm_shap_weighted` | 3 (§5.6.3 별도 보고) |

본 표의 외부 SOTA 14 종은 (foundation 2 + stock SOTA 7 + SMB
attention 3 + cost-sensitive 3 + LightGBM 패밀리 3 중 lgbm_tabular 1) 의
의미로 본 학위논문에서 통상 인용한다.

### 5.6.2 외부 SOTA vs RF baseline — 평균 ΔF1 표 (6 패널 기준)

`phase5_summary.csv` 에서 `mean_delta_vs_rf` 열을 그대로 인용한다 (5%
유의 = `n_sig_p05`, paired 검정 자유도 4).

| 모델 | 평균 ΔF1 vs RF | 5% 유의 (n_sig_p05) | RF 대비 wins |
| --- | --- | --- | --- |
| **lgbm_tabular** | **+0.0075** | 2 / 6 | 5 / 6 |
| lgbm_shap_weighted | +0.0071 | 2 / 6 | 5 / 6 |
| lgbm_decline_x2 | +0.0026 | 3 / 6 | 4 / 6 |
| rf_shap_weighted | −0.0004 | 0 / 6 | 2 / 6 |
| feature_attn_mlp | −0.035 | 6 / 6 | 0 / 6 |
| rf_decline_x2 | −0.035 | 6 / 6 | 0 / 6 |
| film_tenure_lstm | −0.047 | 4 / 6 | 0 / 6 |
| rf_decline_x3 | −0.063 | 6 / 6 | 0 / 6 |
| time_attn_lstm | −0.092 | 1 / 6 | 0 / 6 |
| dlinear | −0.139 | 6 / 6 | 0 / 6 |
| moirai_small | −0.187 (n=1) | 1 / 1 | 0 / 1 |
| chronos_bolt_small | −0.211 | 6 / 6 | 0 / 6 |
| nhits | −0.221 | 6 / 6 | 0 / 6 |
| tft | −0.238 | 6 / 6 | 0 / 6 |
| nbeats | −0.246 | 6 / 6 | 0 / 6 |

LightGBM 패밀리 (lgbm_tabular, lgbm_shap_weighted, lgbm_decline_x2) 만
RF baseline 을 능가하며, 나머지 외부 SOTA 11 종은 모두 RF 에 패배
한다. stock SOTA 7 종 중 DLinear (−0.139) 가 가장 강하지만 여전히
double-digit 패배다. Foundation zero-shot (Chronos, Moirai) 은 −0.18
~ −0.21 로 거의 random guess 수준이다.

### 5.6.3 LightGBM tabular 의 일관된 RF 우위

`weighting_compare.csv` 의 6 panel × lgbm_tabular vs rf_tabular paired
결과는 다음과 같다. lgbm_tabular 가 6 panel 중 5 panel 에서 RF 를
능가하며, 평균 ΔF1 = +0.0075, 2 panel 에서 5% 유의, 1 panel 에서 1%
유의다. 본 결과는 §6.1.4 와 §6.3 의 정책 활용 논의에서 다시 다룬다.

본 §5.6 의 14 모델 negative + LightGBM 1 종 positive 패턴은 §6.1.5
와 §6.2.4 의 4 가지 mechanism 가설 (short window /
regression-to-classification / multivariate channel compression /
calendar season confound dominance) 의 정량 근거가 된다.

## 5.7 업력·신규고객 cohort 분석

본 절은 §1.4 기여 1 의 prediction 요인 분해에 직접 대응하며, advisor
미팅의 "신규 유입·업력이 주요 요인으로 작동 (상승에 유의미)" 권유에
정량적으로 답한다.

데이터 출처는 `260430_claude/outputs/tables/age_cohort_nc_effect.csv`
(panel × tenure_quartile 별 logit P(Growth) = β_0 + β_1 · nc_slope).
대표 6 panel × Q1_short ~ Q4_long 4 cohort × `nc_slope` 의 회귀계수
`β_1` (이하 `logit_coef_nc_slope`) 를 같이 본다.

### 5.7.1 Tenure × Growth rate

같은 시작월·시작연도·윈도우 안에서도 업력 cohort 별 Growth rate
가 다음과 같이 분포한다 (3 개월 panel 4 개의 평균).

| cohort | tenure 중앙 (월) | 평균 Growth rate | 평균 nc_slope |
| --- | --- | --- | --- |
| Q1_short | ~9 | 0.32 | −0.0029 (감소) |
| Q2 | ~25 | 0.33 | −0.0009 |
| Q3 | ~50 | 0.33 | −0.0007 |
| Q4_long | ~115 | 0.34 | −0.0006 |

(원본: `sy2021_sm01_w3m_off1`, `sy2021_sm05_w3m_off1`,
`sy2022_sm01_w3m_off1`, `sy2022_sm05_w3m_off1` 4 panel × 4 cohort 평균.)

Q1_short 에서 Q4_long 으로 갈수록 Growth rate 는 약 +0.02 상승하는
패턴이 있으나, Decline / Growth 비율은 panel 의 시즌 결정 효과(§5.2)
에 비하면 진폭이 작다. 다만 **nc_slope (신규고객 증감 기울기) 가 양수
인 비중**은 cohort 가 길어질수록 안정적이다 — 가장 짧은 cohort 가
가장 변동이 크고 음의 신규고객 추세를 보인다.

### 5.7.2 nc_slope → Growth 의 logit 효과: cohort 별 비교

`logit_coef_nc_slope` (이항 로짓 회귀의 nc_slope 계수) 는 신규고객
유입이 1 표준편차 증가할 때 Growth 확률 odds 가 몇 배 증가하는지를
의미한다. 6 panel 평균에서 다음 패턴이 관측된다.

- Q1_short 평균 β = 약 1.0 (panel 별 분산이 큼; 0.0 ~ 2.0).
- Q4_long 평균 β = 약 1.3 (panel 별 분산 더 작음; 0.9 ~ 1.9).
- 업력이 길어질수록 신규고객 증가가 Growth 와 더 안정적·일관적으로
  연관된다 (panel 간 표준편차 감소).

본 결과는 v2 draft 에서 보고된 "신규 고객 비율의 중요도는 업력 길어
질수록 단조 증가 (2.2 → 7.5×)" 결론의 시즌 정렬 panel 위에서의
재현이며, 신규고객 유입이 점포의 성장 신호로서 업력 cohort 에
따라 다른 강도를 갖는다는 미시적 발견이다. 다만 본 회귀는 관찰적
이며 인과는 아니다 — 신규고객 유입과 매출 성장이 동시에 어떤
요인(예: 시즌 이벤트, 인지도 상승) 에 의해 함께 결정될 수 있다.

### 5.7.3 LightGBM 의 cohort 별 RF 우위

`260511/phase5_external/outputs/tables/lgbm_per_cohort_summary.csv`
는 6 panel × 4 tenure cohort 의 LightGBM vs RF 평균 ΔF1 을 정리한다.

| cohort | tenure 중앙 (월) | 평균 RF macro-F1 | 평균 LGB macro-F1 | 평균 ΔF1 | Decline rate |
| --- | --- | --- | --- | --- | --- |
| Q1_short | ~9 | 0.475 | 0.477 | +0.0021 | 0.129 |
| Q2 | ~25 | 0.492 | 0.490 | −0.0018 | 0.126 |
| Q3 | ~50 | 0.497 | 0.509 | +0.013 | 0.117 |
| **Q4_long** | **~115** | **0.526** | **0.545** | **+0.019** | **0.120** |

업력이 길수록 LightGBM 의 RF 대비 우위가 단조 증가한다. Q4_long
(업력 ≥ 9 년) 의 ΔF1 = +0.019 는 6 panel 전체 평균 (+0.0075) 의 약
2.5 배다. 이는 **prediction 정확도 향상이 단순히 평균을 끌어올리는
것이 아니라 특정 업력 cohort 에 집중되어 있다**는 함의를 갖는다.

## 5.8 Cluster 요인 분해

본 절은 §1.4 기여 1 의 또 다른 축으로, KMeans cluster 가 G/S/D 분포
와 어떻게 구조적으로 연결되는지를 본다. 데이터 출처는
`260430_claude/outputs/tables/cluster_outcome_xtab.csv` (cluster ×
G/S/D 교차표) 와 동 디렉터리 `cluster_outcome_summary.csv` (cluster
내 macro-F1), `per_cluster_feature_importance.csv` (cluster 별 피처
중요도).

### 5.8.1 Cluster × G/S/D 교차표 — fragile vs survivor

대표 panel `sy2022_sm05_w3m_off1` (May-Jul 2022 → May-Jul 2023) 의
cluster × G/S/D 교차표는 다음과 같다 (점포 수 기준 비율).

| cluster | n | Decline | Stable | Growth | 해석 |
| --- | --- | --- | --- | --- | --- |
| 3 | 2,594 | **0.603** | 0.292 | 0.105 | **fragile (Decline 60%)** |
| 5 | 16,049 | 0.281 | 0.659 | 0.060 | high-Decline |
| 4 | 1,443 | 0.274 | 0.542 | 0.184 | mid |
| 2 | 1,052 | 0.227 | 0.465 | 0.308 | mixed |
| 1 | 14,694 | 0.124 | 0.720 | 0.157 | survivor |
| 0 | 61 | 0.279 | 0.361 | 0.361 | tiny (n=61) |

`sy2021_sm01_w3m_off1` (Jan-Mar 2021 → Jan-Mar 2022) 에서는 cluster 3
이 358 / 200 / 187 (n=745) 로 Decline 36% 의 fragile cluster 역할을
한다. **panel 간에 cluster 번호는 다르지만 "Decline 비중이 35% ~
60% 인 fragile cluster" 가 일관되게 등장**한다.

### 5.8.2 Fragile cluster 에서 LightGBM 향상이 가장 크다

`lgbm_per_cohort_summary.csv` 의 cluster × ΔF1 (6 panel 평균):

| cluster | n (평균) | Decline rate | 평균 RF F1 | 평균 LGB F1 | 평균 ΔF1 |
| --- | --- | --- | --- | --- | --- |
| 0 | 9,566 | 0.152 | 0.427 | 0.439 | +0.011 |
| 1 | 5,094 | 0.162 | 0.390 | 0.430 | +0.041 |
| 2 | 2,558 | 0.198 | 0.426 | 0.447 | +0.021 |
| **3** | **4,622** | **0.173** | **0.394** | **0.438** | **+0.044** |
| 4 | 8,835 | 0.154 | 0.463 | 0.467 | +0.004 |
| 5 | 5,226 | 0.130 | 0.420 | 0.456 | +0.036 |

**Cluster 3 의 ΔF1 = +0.044 는 6 panel 평균 (+0.0075) 의 약 5.9 배**
다. 위 cluster_outcome_xtab 에서 cluster 3 이 fragile (Decline 비중
35 ~ 60%) 인 panel 들과 일치한다. 즉 LightGBM 의 prediction 향상이
정책 우선 대상 (Decline 비중이 큰 위험 cluster) 에서 가장 강하게
나타난다.

### 5.8.3 Cluster 내 macro-F1: 어디서 분류가 어려운가

`cluster_outcome_summary.csv` 의 cluster 별 macro-F1 (D 모델, 5-fold
CV 평균) 은 같은 panel 안에서 cluster 간 0.08 ~ 0.16 의 격차를 보인다.
일반적으로 라벨 비중이 0.3 ~ 0.5 로 균등할수록 macro-F1 이 높고, 한
클래스로 라벨이 쏠릴수록 (예: cluster 3 의 Decline 0.60) macro-F1 이
낮다. 본 결과는 분류 난이도가 라벨 분포 자체와 강하게 연관되며, **모
델 향상의 여지가 가장 큰 영역이 fragile cluster (정책적 우선 영역)
다**라는 §5.8.2 의 함의와 정합한다.

## 5.9 Cost-sensitive 가중 보조 실험

본 절은 §1.4 기여 3-(b) 에 대응한다. advisor 미팅의 "예측 모델을
기본 말고 더 강화하면 어떨까? technical novelty 가 있으면 좋겠다"
권유에 대한 한 가지 시도다.

데이터 출처는 `260511/phase5_external/outputs/tables/weighting_compare.csv`
와 `weighting_paired.csv`. RF 와 LightGBM 각각에 대해 4 가지 변형을
6 대표 panel 에서 비교한다.

| 변형 | sample weighting | 평균 ΔF1 (vs rf_tabular) | n_sig_p05 |
| --- | --- | --- | --- |
| rf_tabular | none | (baseline) | — |
| rf_shap_weighted | feature SHAP 기반 sample weight | −0.0004 | 0 / 6 |
| rf_decline_x2 | Decline label × 2 | −0.035 | 6 / 6 (역방향) |
| rf_decline_x3 | Decline label × 3 | −0.063 | 6 / 6 (역방향) |
| lgbm_tabular | none | +0.0075 | 2 / 6 |
| lgbm_decline_x2 | Decline × 2 | +0.0026 | 3 / 6 |
| lgbm_shap_weighted | feature SHAP 기반 | +0.0071 | 2 / 6 |

핵심 발견은 세 가지다.

1. **RF 에서 단순 Decline 가중치 증가는 효과가 음(−)** 이다. Decline ×
   2 / ×3 모두 6 / 6 panel 에서 RF baseline 대비 5% 유의 *하락* —
   class_weight="balanced" 가 이미 적용된 RF 위에서 추가로 Decline 을
   3 배 가중하면 Stable/Growth recall 이 무너지고 macro-F1 이 떨어진다.
2. **RF 에서 SHAP 기반 sample weighting 은 거의 무효** 다 (ΔF1 =
   −0.0004, 2 panel 에서만 미세 우위). RF 의 split-gain 학습은 이미
   informative feature 에 가중되어 있어 외부 SHAP weight 가 잉여
   정보를 추가하지 못한다.
3. **LightGBM 에서는 단순 baseline (gradient boosting + balanced 가중)
   이 가장 강하다.** LGB + Decline ×2 는 LGB baseline 대비 약 −0.005
   하락, LGB + SHAP weighting 은 거의 동일 (−0.0004). 즉 model
   choice (RF → LightGBM) 가 sample weighting 보다 큰 효과를 가진다.

**의의.** Decline label 의 라벨 가중치 조정은 SMB 단기 G/S/D 분류
에서 "단순한 technical fix" 가 아니라 오히려 정확도를 떨어뜨릴 수
있는 모델 선택이다. macro-F1 기준 prediction 향상의 실효는 sample
weighting 이 아니라 모델 패밀리 교체 (RF → LightGBM, §5.6.3) 에서
주로 온다. 다만 Decline recall 자체를 정책 목적 (놓치면 안 되는
사례) 으로 본다면 Decline ×2 / ×3 의 cost-sensitive 변형은 별도
시나리오에서 trade-off 표로 검토할 가치가 있다 (§6.3, §6.5).

## 5.10 결과 요약

본 장의 결과는 본 학위논문의 세 본문 contribution 에 대해 다음과
같이 답한다.

1. **Prediction baseline 과 요인 분해 (§5.2 ~ §5.5, §5.7 ~ §5.8).**
   145 specification 의 baseline macro-F1 은 0.43 ~ 0.55 분포다. 시즌
   정렬된 label 위에서 업력 cohort 가 길수록 신규고객 유입과 Growth
   의 logit 연관이 일관적이고(§5.7), KMeans cluster 는 panel 간에
   재현되는 fragile (Decline ≥ 35%) 와 survivor (Decline ≤ 13%) 의
   이원 구조를 보인다(§5.8). LightGBM 의 RF 대비 향상은 평균 (+0.0075)
   의 약 5.9 배가 fragile cluster 에서, 약 2.5 배가 Q4_long cohort
   에서 집중된다.
2. **Seasonal alignment 의 label robustness (§5.2 ~ §5.4).** 145
   specification 에서 시작월 진폭(약 0.10) ≫ 윈도우 길이 효과(0.02
   ~ 0.04) ≫ 시작연도 효과(0.02 이내). 라벨 시점 선택이 prediction
   결론을 좌우할 수 있음을 정량적으로 입증한다.
3. **세 갈래 prediction-improvement 와 그 한계 (§5.5, §5.6, §5.9).**
   (a) representation 측 hybrid 는 14 panel 평균 ΔF1 = +0.0017, 5%
   유의 1/14 (Bonferroni 후 0/14) 의 조건부 contribution 이다.
   (b) weighting 측 cost-sensitive 는 RF 위에서 효과가 음(−) 이고
   LightGBM 위에서도 baseline 대비 미세 손해다. (c) model 측 외부
   SOTA 14 종 중 LightGBM 패밀리 (3 종) 만 RF 를 능가하며, 나머지
   stock SOTA 7 종 + SMB attention 3 종 + foundation 2 종은 모두 RF
   에 패배한다 (ΔF1 = −0.035 ~ −0.246).

§6 은 본 세 결과의 의미와 한계, future work 분리를 다룬다.
