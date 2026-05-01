# 메인 모델 결과 (Step 05)

> 자동 생성 표/그림: `outputs/tables/main_model_compare.csv`,
> `outputs/tables/main_model_paired_AvD.csv`,
> `outputs/figures/main_model_compare_bars.png`,
> `outputs/figures/main_model_delta.png`.

## 1. 비교 대상

`top_tier/src/step10_hybrid_prediction.py`의 A/B/C/D 프로토콜을 시즈널
정렬 panel 위에서 다시 돌렸다.

| 코드 | 피처 구성 | 피처 수 |
| --- | --- | --- |
| A | Step 03 베이스라인 (매출 통계 + 슬로프 + 이동평균 + 신규 고객 + 채널 비율 + 분포) | 43 |
| B | A + KMeans cluster one-hot (k=6, normalized 매출 시퀀스) | 49 |
| C | A + change-point 7개 | 50 |
| D | A + B + C | 56 |

평가:
- RandomForest 240 trees, depth 14, class_weight=balanced.
- Stratified 5-fold CV (seed 42).
- A vs D paired t-test (per-fold macro_F1, 자유도=4).

## 2. 결과 표

| panel | A | B | C | D | Δ(D−A) | t | p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| sy2021_sm01_w3m_off1 (Jan–Mar 21→22) | 0.5007 | 0.5014 | 0.5008 | **0.5030** | +0.0023 | 2.73 | 0.052 |
| sy2021_sm03_w3m_off1 (Mar–May 21→22) | 0.4954 | 0.4967 | **0.4994** | 0.4986 | +0.0032 | 1.32 | 0.258 |
| sy2021_sm05_w3m_off1 (May–Jul 21→22) | 0.4875 | 0.4872 | 0.4874 | **0.4882** | +0.0007 | 0.29 | 0.787 |
| sy2021_sm09_w3m_off1 (Sep–Nov 21→22) | 0.5096 | **0.5103** | 0.5076 | 0.5101 | +0.0005 | 0.30 | 0.778 |
| sy2022_sm01_w3m_off1 (Jan–Mar 22→23) | 0.5144 | 0.5136 | **0.5165** | 0.5165 | +0.0021 | 1.04 | 0.356 |
| sy2022_sm03_w3m_off1 (Mar–May 22→23) | 0.4684 | 0.4716 | 0.4726 | **0.4740** | **+0.0055** | **3.47** | **0.026** |
| sy2022_sm05_w3m_off1 (May–Jul 22→23) | 0.5176 | 0.5186 | **0.5207** | 0.5190 | +0.0014 | 0.72 | 0.511 |

평균 Δ(D−A) = **+0.0022 macro-F1**. 7개 panel 중 5% 유의는 1개
(`sy2022_sm03`), 10% 유의 경계 1개 (`sy2021_sm01` p=0.052), 나머지 5개는
유의하지 않음.

## 3. 핵심 해석 (미팅 의도와 충돌하는 부분)

> 미팅에서 교수가 인정한 유일한 아카데믹 contribution은 "베이스라인 + 클러스터
> + 체인지 포인트로 G/S/D 분류 정확도가 향상된다"는 것이었다. 시즈널 정렬
> 라벨로 재검증한 결과 이 향상은 **데이터 전체에 일반화되지 않는다.**

- **시즈널 confound 통제 후, 클러스터 + 체인지 포인트의 추가 정보량은 평균
  +0.002 macro-F1에 그친다.** 이는 5-fold 표준편차(평균 0.005~0.01) 안쪽으로
  사실상 noise.
- **유의한 향상은 가장 어려운 시즌 panel(`sy2022_sm03`)에서만** 발생.
  이 panel은 베이스라인 Decline recall이 0.295로 가장 낮고 (라벨 분포가
  Stable 75% 편중), 따라서 추가 신호가 살아남는다.
- **균형 잡힌 시즌 panel (sm09, sm05)에서는 향상이 사실상 0.** 시즈널 confound
  를 제거하면 매출 슬로프 / 변동성만으로도 이미 라벨이 거의 설명됨.

## 4. 논문 1번 contribution에 미치는 영향

- 기존 `top_tier`의 hybrid 모델 결과(D ≫ A by ~0.05 macro-F1)는 라벨 구간이
  2023년 6–8월(여름 휴가 시즌)에 고정된 시즈널리티 confound 위에서 성립한
  결과일 가능성이 크다.
- 시즈널 정렬을 강제하면 **D vs A의 통계적 유의성과 효과 크기가 모두 무너진다**.
  이는 원래 contribution 주장의 외적 타당성에 직접적인 위협이다.

### 가능한 framing 옵션

a. **조건부 contribution (현실적)**: "클러스터 + 체인지 포인트는 라벨 분포가
   심하게 편중된 시즌 panel에서만 의미 있는 추가 신호를 준다"고 좁혀서 기술.
   `sy2022_sm03` 케이스를 사례로 제시.

b. **Trajectory 해석에 한정**: 클러스터 라벨 자체의 정성적 해석(상승/유지/하락
   trajectory를 사람이 읽기 쉬운 형태로 분리)에 가치를 부여하고, 정량적
   분류 향상은 보조 결과로만 표시.

c. **시즈널 confound 자체를 contribution으로 재포지션**: "기존 라이프사이클
   분류는 시즈널리티에 의해 inflate 되어 있었음을 데이터로 증명"이 본 분석의
   주된 실험적 발견. D 모델의 작은 향상은 robustness 보강 정도로 다룸.

미팅에서 교수가 우려한 "코로나 영향"은 결과 정확도에 큰 영향을 주지 않았으나,
시즈널리티 통제가 cluster+CP contribution을 사실상 무력화한다는 결과는
미팅에서 예상하지 못한 더 강한 함의를 가짐.

## 5. 후속 액션 제안

1. 미팅에서 교수에게 본 결과(D−A 평균 +0.002, 1개 panel만 유의)를 그대로 보고
   하고, 위 framing 중 어느 쪽으로 갈지 의사결정 받기.
2. 만약 **option (a) 조건부 contribution**으로 가면: 더 다양한 시즌 panel
   (현재 7개 → 80개 전체)에서 D−A delta heat map을 그려, 어떤 시즌에서
   contribution이 살아남는지 정량적으로 보여주는 보강 분석 추가.
3. 만약 **option (c) 시즈널 confound 노출 자체를 메인**으로 가면: legacy
   `top_tier` 결과를 동일 점포 기준으로 재현해 차이를 표로 만들고, 이 표
   하나가 논문의 핵심 figure가 됨.
4. 어느 쪽이든, 논문 1번 메인 contribution의 정량 클레임을 기존 `top_tier`
   숫자(예: macro-F1 0.55, Decline recall 0.45 등)에서 본 결과 숫자로 교체
   해야 함. 시즈널 정렬 후 macro-F1은 0.43–0.54 범위, 이 안에서 D−A는
   사실상 0.
