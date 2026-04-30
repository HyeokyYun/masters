# Thesis Deep Research File Guide

이 패키지는 GPT Deep Research가 석사학위논문 outline, main result, main figure, 초안 작성 전략을 만들도록 준비한 자료 묶음입니다.

## Start Here

- `00_START_HERE/MASTER_PROMPT.md`
  - Deep Research에 그대로 붙여넣을 최상위 프롬프트입니다.
- `00_START_HERE/EVIDENCE_BRIEF.md`
  - 전체 실험 폴더에서 추린 핵심 결과, 수치, 해석 제약입니다.
- `00_START_HERE/FILE_GUIDE.md`
  - 이 파일입니다.

## Original Docs

- `01_original_docs/KCD_FINAL.pdf`
  - 기존 KCD 최종 보고서/학위논문 seed 문서입니다.
  - 동기, 데이터 설명, 초기 trajectory framing에 사용하세요.
  - 최신 main result 수치는 이후 분석 자료로 교체해야 합니다.
- `01_original_docs/KER_Extended_Abstract_Final.md`
  - 현재 연구 방향에 가까운 extended abstract입니다.
- `01_original_docs/개별미팅 26-1.docx`
  - 최신 개별미팅 흐름입니다.
- `01_original_docs/개별미팅_25-1학기.docx`
  - 이전 학기 개별미팅 흐름입니다.
- `01_original_docs/연구 발표.pdf`
  - 연구 발표 자료입니다.

## Analysis Docs

- `02_analysis_docs/260216` to `02_analysis_docs/260326_fullsample`
  - 각 실험 시점의 README, summary, methodology, meeting note입니다.
  - 연구가 발전한 순서를 파악할 때 사용하세요.
- `02_analysis_docs/260409`
  - 이전 thesis outline draft입니다.
  - 단, golden cross와 volatility 해석은 최신 분석과 충돌할 수 있으므로 그대로 main result로 쓰지 마세요.

## Key Tables

- `03_key_tables/main_clustering`
  - clustering 방법 비교, stability, 초기 ablation 결과입니다.
  - K-shape를 과장하지 말고, 안정성 비교 근거로 사용하세요.
- `03_key_tables/post_entry`
  - post-entry trajectory label, cluster, prediction 평가 결과입니다.
  - 초기 trajectory heterogeneity와 12-class 예측 난이도 설명에 사용하세요.
- `03_key_tables/fullsample`
  - 전체 생존 업장 observed-window 분석의 핵심 표입니다.
  - age bucket별 Growth/Stable/Decline 분포와 driver 분석에 사용하세요.
- `03_key_tables/forecasting`
  - 초기 observation window별 예측 성능과 feature block ablation입니다.
  - Main Result 3의 핵심 근거입니다.
- `03_key_tables/volatility_new_customer`
  - volatility definition 재검토와 신규 고객 비율 분석입니다.
  - 본문 보조 결과 또는 appendix 근거로 사용하세요.
- `03_key_tables/robustness_practical`
  - practical impact, robustness, intervention lead window 관련 결과입니다.
  - discussion 또는 appendix에 적합합니다.

## Key Figures

- `04_key_figures/main_result_1`
  - Figure 1 후보입니다.
  - `fig01_trajectories.png`: 개업 직후 trajectory heterogeneity
  - `fullsample_age_overview.png`: 전체 업장 observed-window age distribution
- `04_key_figures/forecasting`
  - 예측 window와 feature ablation을 설명할 figure 후보입니다.
- `04_key_figures/supporting`
  - volatility, new customer, competition, SHAP, robustness 등 보조 그림입니다.

## Source-Preserved Outputs

- `05_all_small_tables_by_source_path`
  - 1MB 미만의 주요 output table을 원래 경로 구조 그대로 보존한 폴더입니다.
  - `03_key_tables`에서 같은 파일명 때문에 덮였을 가능성이 있거나, 추가 확인이 필요할 때 사용하세요.
- `06_all_figures_by_source_path`
  - 5MB 미만의 output figure를 원래 경로 구조 그대로 보존한 폴더입니다.
  - 본문/appendix figure 후보를 더 넓게 탐색할 때 사용하세요.

## Recommended Thesis Structure

1. Introduction
   - 왜 소상공인 생애주기를 주별 거래 데이터로 봐야 하는가.
   - 기존 단일 생애주기 곡선의 한계.
2. Data and Empirical Design
   - KCD weekly transaction data, sample, store age, observation window.
   - post-entry trajectory와 observed-window state의 차이.
3. Post-Entry Trajectory Heterogeneity
   - 개업 직후 12 trajectory label과 heterogeneity.
4. Full-Sample Observed-Window Life-Cycle States
   - Growth/Stable/Decline 분포, 업력별 driver.
5. Early Prediction
   - 20-50주 정보 기반 예측, feature block ablation.
6. Robustness and Discussion
   - volatility definition, new customer, practical targeting, limitations.
7. Conclusion
   - 진단/예측 프레임의 기여와 한계.

## Important Do-Not-Overclaim List

- Golden cross is not the main result.
- K-shape is not the main methodological contribution.
- Growth does not simply mean higher volatility.
- Cluster features are not the main source of predictive gain.
- Results are predictive and descriptive, not causal.
