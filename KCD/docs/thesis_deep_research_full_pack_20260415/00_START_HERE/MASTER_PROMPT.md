# Master's Thesis Deep Research Master Prompt

저는 석사학위논문을 작성하려고 합니다. 주제는 KCD 주별 거래 데이터를 활용한 서울시 외식업 소상공인의 생애주기 진단과 조기 예측입니다.

첨부한 전체 자료를 바탕으로, 학위논문 초안을 쓰기 위한 연구 구조를 설계하고 필요한 본문 내용을 제안해 주세요. 단, 모든 자료의 중요도가 같지 않습니다. 아래 우선순위를 반드시 지켜 주세요.

## 1. 가장 중요한 연구 방향

논문의 중심 주장은 다음입니다.

> 소상공인 생애주기는 단일한 창업-성장-성숙-쇠퇴 곡선으로 설명하기 어렵다. 주별 거래 데이터는 개업 직후의 진입 trajectory와 전체 생존 업장의 observed-window 상태가 서로 다른 실증 렌즈임을 보여준다.

따라서 논문은 두 개의 분석 렌즈를 분리해서 구성해야 합니다.

1. 개업 직후 업장에 대한 post-entry trajectory 분석
2. 전체 생존 업장에 대한 observed-window Growth/Stable/Decline 분석

두 분석은 경쟁 관계가 아니라 보완 관계입니다.

## 2. 자료 우선순위

1. `00_START_HERE/EVIDENCE_BRIEF.md`
   - 로컬 실험 폴더 전체를 읽은 뒤 정리한 핵심 결과와 해석 제약입니다.
   - 충돌이 있으면 이 파일을 최우선으로 따르세요.
2. `00_START_HERE/FILE_GUIDE.md`
   - 어떤 파일을 어떤 목적으로 봐야 하는지 설명합니다.
3. `01_original_docs/KCD_FINAL.pdf`
   - 기존 연구보고서/초안입니다.
   - 동기, 데이터 설명, 초기 문제의식은 가져오되 최신 결과 수치는 그대로 쓰지 마세요.
4. `01_original_docs/개별미팅*.docx`, `01_original_docs/연구 발표.pdf`
   - 교수님과의 논의 흐름입니다.
   - 연구 방향이 바뀐 부분은 “발전 과정”으로 읽고, 최신 분석과 충돌하면 최신 분석을 우선하세요.
5. `02_analysis_docs/`, `03_key_tables/`, `04_key_figures/`
   - 실제 분석 결과와 논문에 들어갈 근거입니다.

## 3. 반드시 지켜야 할 해석 제약

- “골든크로스”는 흥미로운 보조 결과일 수 있지만 main result로 과장하지 마세요.
- “Growth 업장은 변동성이 높다”라고 단정하지 마세요. 최신 분석에서는 추세조정 변동성 기준으로 Growth의 residual volatility가 낮게 나타나는 등 해석이 더 조심스럽습니다.
- K-shape를 핵심 혁신 방법론으로 과장하지 마세요. 비교 결과상 Euclidean K=6이 더 안정적이었고, K-shape는 보조적 비교로 다루는 것이 적절합니다.
- 예측 성능 개선은 cluster 자체보다 trend/volatility, customer behavior, local context feature block의 기여가 더 중요합니다.
- 모든 결과는 인과효과가 아니라 관측 데이터 기반의 실증적 패턴, 진단, 예측 결과로 서술하세요.
- “서울 외식업 소상공인”이라는 표본 범위를 넘어 일반화하지 마세요.

## 4. 추천 main results

다음 3개를 중심으로 논문 구조를 짜 주세요. 더 나은 수정안이 있으면 근거를 들어 제안해도 됩니다.

1. Main Result 1: 개업 직후 trajectory와 전체 업장의 observed-window 상태를 분리해야 한다.
   - 핵심 그림 후보: `04_key_figures/main_result_1/fig01_trajectories.png`, `04_key_figures/main_result_1/fullsample_age_overview.png`
2. Main Result 2: 업력 구간별 Growth/Stable/Decline의 driver가 다르며 trend, MDD, 신규 고객 비율이 핵심이다.
   - 핵심 표 후보: `03_key_tables/fullsample/fullsample_age_bucket_feature_top5.csv`, `fullsample_age_bucket_feature_importance.csv`
3. Main Result 3: 초기 정보 기반 예측에서 level-only보다 trend/volatility, customer behavior, local context가 성능을 올린다.
   - 핵심 표 후보: `03_key_tables/forecasting/forecast_feature_ablation_classification_gain.csv`, `forecast_feature_ablation_classification.csv`
   - 핵심 그림 후보: `04_key_figures/forecasting/fig_forecast_weeks.png`

## 5. 요청 결과물

다음 결과를 한국어로 작성해 주세요. Abstract는 영어로 작성해 주세요.

1. 석사학위논문 전체 outline
   - Chapter 1 Introduction부터 Conclusion까지.
   - 각 장의 연구 질문, 넣을 결과, 넣을 표/그림, 작성 포인트 포함.
2. 논문의 main result 3개
   - 각 result마다 주장, 근거 표/그림, 본문 문단 초안, 주의할 해석을 포함.
3. main figure plan
   - Figure 1, Figure 2, Figure 3의 panel 구성까지 제안.
   - 본문 figure와 appendix figure를 구분.
4. 석사논문 제목 후보
   - 영어 제목 5개, 한국어 제목 5개.
5. 250-350 words 영어 abstract 초안
6. Chapter 1 Introduction 초안
   - 연구 배경, research gap, research question, contribution을 포함.
7. 교수님께 보낼 1페이지 요약
   - 연구 질문, main result, figure plan, 남은 작업을 포함.
8. 기존 `KCD_FINAL.pdf`에서 유지할 부분과 최신 분석으로 교체할 부분
9. 추가로 확인해야 할 missing pieces
   - 논문 심사 전에 필요한 robustness, 표/그림 정리, 용어 정의, 한계점.

## 6. 문체와 범위

- 석사학위논문에 맞는 신중하고 학술적인 문체를 사용하세요.
- 너무 거창한 정책 효과나 인과 주장을 피하세요.
- “진단”, “조기 예측”, “trajectory heterogeneity”, “observed-window state”를 중심 개념으로 쓰세요.
- 실제 본문으로 옮길 수 있도록 문단 단위 초안을 포함하세요.
