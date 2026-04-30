# Deep Research One-File Prompt And Evidence Brief

## Copy-Paste Prompt

저는 학위논문을 작성하려고 합니다. 주제는 KCD 주별 거래 데이터를 활용한 서울시 외식업 소상공인의 생애주기 진단과 조기 예측입니다.

첨부한 자료들을 바탕으로 학위논문용 outline과 main result 구조를 잡아주세요. 특히 이 파일(`DEEP_RESEARCH_ONEFILE.md`)의 evidence brief와 해석 제약을 최우선으로 반영해주세요. 원본 실험 폴더 전체는 Deep Research에 없으므로, 이 파일에 정리된 수치와 해석 제약을 따라 주세요.

원하는 결과물:

1. 학위논문 전체 outline
   - Chapter 1 Introduction부터 Conclusion까지.
   - 각 장의 핵심 질문, 들어갈 결과, 들어갈 표/그림 제안 포함.
2. Main result 3개 선정
   - Result 1: 초기 trajectory와 observed-window 상태를 분리해야 한다는 결과.
   - Result 2: 업력 구간별 driver가 다르며 trend, MDD, 신규 고객 비율이 핵심이라는 결과.
   - Result 3: 초기 정보 기반 예측에서 level-only보다 trend/volatility, customer behavior, local context가 성능을 올린다는 결과.
3. Main figure 구성
   - Figure 1: 초기 trajectory 패턴 + 전체 업장 업력별 Growth/Stable/Decline 비중을 합친 composite figure.
   - Figure 2: 업력 구간별 핵심 driver, 예: trend/MDD/nc_rate coefficient 또는 importance summary.
   - Figure 3: 예측 feature ablation, 예: level only -> trend/volatility -> customer behavior -> local context -> cluster.
   - 보조/appendix figure로 보낼 것들도 구분.
4. 논문 제목 후보 5개
   - 영어 제목과 한국어 제목 둘 다 제안.
5. Abstract 초안
   - 250~350 words 영어 abstract.
   - 지나친 인과 주장 없이 empirical design과 main findings 중심으로 작성.
6. 작성 전략
   - 어떤 결과를 본문에 넣고, 어떤 결과를 appendix로 보내야 하는지.
   - 기존 `KCD_FINAL.pdf`에서 가져올 부분과 최신 분석으로 교체할 부분.
   - 교수님께 보여줄 1페이지 요약 구조.

## Central Thesis Direction

The recommended central claim is:

> Small-business life cycles should not be treated as a single start-up -> growth -> maturity -> decline curve. Weekly transaction data reveal heterogeneous post-entry trajectories, and these must be distinguished from observed-window Growth/Stable/Decline states among surviving stores.

This implies two empirical lenses:

1. Post-entry trajectory analysis for recently opened stores.
2. Full-sample observed-window analysis for the broader stock of surviving stores.

These are complementary, not substitutes.

## Uploaded Files In The 10-File Pack

1. `DEEP_RESEARCH_ONEFILE.md`
   - This prompt and evidence brief.
2. `KCD_FINAL.pdf`
   - Earlier KCD final report / thesis seed document.
3. `KER_Extended_Abstract_Final.md`
   - Current abstract-style summary.
4. `개별미팅 26-1.docx`
   - Most important meeting file.
5. `개별미팅_25-1학기.docx`
   - Earlier meeting context.
6. `fig01_trajectories.png`
   - Post-entry trajectory patterns.
7. `fullsample_age_overview.png`
   - Full-sample observed-window age-bucket distribution.
8. `fig_forecast_weeks.png`
   - Forecasting performance by early observation window.
9. `new_customer_overview.png`
   - Supplementary new-customer-ratio figure.
10. `volatility_comparison.png`
   - Supplementary volatility-definition figure.

## Key Evidence

### `KCD_FINAL.pdf`

Core content:

- Uses Seoul food-service weekly sales data to define small-business life-cycle patterns.
- Argues that stores do not neatly follow a canonical start-up -> growth -> stability -> decline path.
- Suggests diagnosing patterns from weekly sales trajectory.
- Original example labels include DDZ and UUX.
- Early report says post-opening 20-30 weeks contain useful signal for life-cycle diagnosis.

Use for:

- Motivation.
- Data description.
- Original life-cycle diagnosis framing.

Do not use for:

- Latest main result numbers unless confirmed by later experiments.

### Early Analyses: `260121`, `260127`

`260121`:

- Early clustering and determinant analysis.
- XGBoost cluster/code classification performance around Accuracy `0.731`, F1 `0.727`.
- Top determinant features included `growth_rate`, `total_weeks`, `cv_sales_card`, `trend_slope`, `business_age_months`, `new_customer_ratio`.

`260127`:

- LSTM-based prediction trials.
- LSTM sales forecasting was unstable or not strong enough to be a main result.
- Use as a trial that motivated simpler interpretable trajectory/state features.

### Clustering, Inflection, UDX: `260204`, `260211`, `260223`, `260224`

Key results:

- Method comparison from `compare_methods_no_dtw.csv`:
  - Euclidean K=6: seed ARI about `0.856`, bootstrap ARI about `0.834`.
  - K-shape K=6: seed ARI about `0.320`, bootstrap ARI about `0.373`.
  - M1 F1 about `0.445` for both in that comparison.
- Prediction with UDX/inflection:
  - XGBoost base only: accuracy `0.9085`, F1 `0.6806`.
  - XGBoost base + UDX/inflection: accuracy `0.9530`, F1 `0.8435`.
  - Random Forest base only: F1 `0.5392`.
  - Random Forest base + UDX/inflection: F1 `0.7952`.
- Event-study style DUY vs DDZ results suggested a possible new-customer-ratio spike around `t=-4`, but this should be treated as supportive/subsidiary evidence unless revalidated.

Use carefully:

- Do not overstate K-shape as the central innovation. Its stability was weaker than Euclidean in the comparison.
- Do not make the "golden cross" the main result without caveats.

### Robustness: `260303`

Practical impact metrics:

- Declining precision `0.674`.
- Declining recall `0.834`.
- Declining F1 `0.745`.
- Top-decile lift `2.426`.
- Declining base rate `0.376`.
- Declining top-decile rate `0.912`.
- Median intervention lead window `112` weeks.

Robustness master table:

- Pattern-only baseline macro F1 `0.753`, weighted F1 `0.741`.
- Pattern + growth quantile tails macro F1 `0.814`, weighted F1 `0.805`.
- Strict pattern growth gate macro F1 `0.811`, weighted F1 `0.806`.
- Random forest model robustness weighted F1 `0.785`.
- Multinomial logit weighted F1 `0.735`.
- Linear SVM weighted F1 `0.679`.

Use for:

- Robustness section.
- Practical targeting/intervention section.

### Post-Entry Trajectory Labels: `260319_cur`

Key content:

- Uses 12 trajectory labels such as DD_Z, DU_Y, UU_X, UD_X.
- Best figure candidate: `fig01_trajectories.png`.
- This figure shows heterogeneity in early sales trajectories.
- Forecasting 12-class labels is difficult; 3-class outcome is more stable.

Use for:

- Main Result 1, Panel A: heterogeneous post-entry trajectories.

### Forecasting Windows: `260321_cur`

Forecasting results from `forecast_weeks_comparison.csv`:

- For 3-class Growth/Stable/Decline:
  - 20 weeks, GBM weighted F1 about `0.542`.
  - 30 weeks, GBM weighted F1 about `0.572`.
  - 40 weeks, GBM weighted F1 about `0.600`.
  - 50 weeks, GBM weighted F1 about `0.631`.
- 12-class trajectory prediction is much harder:
  - 20 weeks, GBM weighted F1 about `0.223`.
  - 30 weeks, GBM weighted F1 about `0.260`.
  - 40 weeks, GBM weighted F1 about `0.291`.
  - 50 weeks, GBM weighted F1 about `0.320`.

Use for:

- Main Result 3: early prediction is feasible in the coarser 3-class state space, and improves with longer early windows.

### Latest Reanalysis: `260325`

Important caution:

- Do not say "Growth stores are simply more volatile."
- Better claim: conventional CV conflates trend and volatility; trend-adjusted residual volatility is more appropriate for explanation.

Volatility results:

- Recommended volatility definition in summary: `vol_resid_rolling12`.
- Volatility screening:
  - `vol_resid_rolling8`: Stable mean `0.2862`, Growth mean `0.2190`, Decline mean `0.2712`, ANOVA F `269.995`.
  - `vol_resid_rolling12`: Stable mean `0.3036`, Growth mean `0.2359`, Decline mean `0.2883`, ANOVA F `249.143`.
  - Old `vol_cv_mean`: Stable mean `0.4191`, Growth mean `0.3843`, Decline mean `0.4558`, ANOVA F `103.936`.
- Model fit:
  - Baseline volatility model pseudo R2 `0.57849`, AIC `18830.19`.
  - Adjusted volatility model pseudo R2 `0.57879`, AIC `18816.79`.

New-customer results:

- New-customer model comparison:
  - Without new customer: pseudo R2 `0.591356`, AIC `18680.54`.
  - With new customer: pseudo R2 `0.591904`, AIC `18659.60`.
- New-customer quantiles:
  - Q1 low: growth share `0.3465`, decline share `0.1861`.
  - Q5 high: growth share `0.4472`, decline share `0.1811`.

Forecast feature ablation:

- Classification feature block gains:
  - `level_only`: weighted F1 `0.5620`.
  - `plus_trend_volatility`: weighted F1 `0.6333`.
  - `plus_customer_behavior`: weighted F1 `0.6540`.
  - `plus_local_context`: weighted F1 `0.6692`.
  - `plus_cluster`: weighted F1 `0.6690`.
- Interpretation:
  - The biggest gain comes from trend/volatility.
  - Customer behavior and local context add smaller gains.
  - Cluster adds little incremental value after other features.

### Full-Sample Observed-Window Analysis: `260326_fullsample`

Key results:

- Stores with at least minimum observed weeks: `50,635`.
- Observed-window 3-class distribution:
  - Growth: `20,273` stores, `40.04%`.
  - Stable: `19,365` stores, `38.24%`.
  - Decline: `10,997` stores, `21.72%`.
- Median full business age: `54` months.
- Median age at first observation: `24` months.

Age-bucket distribution:

- `0_12m`: Growth `234`, Stable `186`, Decline `238`.
- `12_24m`: Growth `1,528`, Stable `1,969`, Decline `1,907`.
- `24_36m`: Growth `2,319`, Stable `2,650`, Decline `2,130`.
- `36_60m`: Growth `5,997`, Stable `5,866`, Decline `3,581`.
- `60_120m`: Growth `6,704`, Stable `5,901`, Decline `2,467`.
- `120m_plus`: Growth `3,491`, Stable `2,785`, Decline `654`.

Interpretation:

- Growth share rises and Decline share falls in older business-age buckets.
- This is an observed-window survivor-stock result, not a literal post-entry life-cycle curve.

Age-bucket driver results:

- `0_12m`: trend_slope is dominant; Growth coefficient `11.494`, Decline coefficient `-9.014`.
- `12_24m`: trend_slope dominant; MDD suppresses Growth / points toward Decline; new-customer ratio connected to Growth.
- `24_36m`: trend_slope, MDD, and new-customer ratio are core.
- `36_60m`: trend_slope remains first; MDD and new-customer ratio are secondary.
- `60_120m`: trend_slope, new-customer ratio, MDD.
- `120m_plus`: trend_slope remains first; new-customer ratio distinguishes dynamic states.

## Recommended Main Results

### Result 1: Two empirical lenses are necessary

Post-entry trajectories are heterogeneous and do not support a single canonical life-cycle curve. The full surviving-store sample shows a different observed-window distribution: Growth 40.0%, Stable 38.2%, Decline 21.7%. These are not contradictory because they answer different questions.

Main figure:

- Composite Figure 1:
  - Panel A: `fig01_trajectories.png`.
  - Panel B: `fullsample_age_overview.png`.

### Result 2: Drivers differ by business-age bucket

Across age buckets, sales trend is the most consistent discriminator. MDD is closely associated with decline, and new-customer ratio becomes a meaningful growth/dynamic-state signal after the very earliest stage.

Main figure:

- Create a coefficient/importance heatmap or bar chart from the age-bucket driver results.

### Result 3: Early prediction works through feature blocks, not cluster alone

Early observed data predict later state better than level-only baselines. The largest gain comes from trend/volatility features, with additional smaller gains from customer behavior and local context. Cluster adds little after these blocks.

Main figure:

- Create a feature-ablation bar chart:
  - level only weighted F1 `0.5620`.
  - plus trend/volatility weighted F1 `0.6333`.
  - plus customer behavior weighted F1 `0.6540`.
  - plus local context weighted F1 `0.6692`.
  - plus cluster weighted F1 `0.6690`.

## Claims To Avoid Or Downweight

Avoid making these central claims:

1. "K-shape is the main methodological innovation."
   - K-shape stability was weaker than Euclidean in the comparison.
   - Use it as a trajectory visualization/state-labeling support, not as the entire contribution.

2. "Growth stores have high volatility."
   - This was challenged by later trend-adjusted volatility results.
   - Safer claim: volatility must be defined after removing trend; conventional CV can mislead.

3. "Golden cross is the main finding."
   - Interesting but not robust enough to anchor the thesis.
   - Use as a supplementary new-customer-ratio result.

4. "Initial 30-week cluster alone drives prediction."
   - Later feature ablation suggests trend/volatility, customer behavior, and local context are more important.

## Recommended Thesis Structure

1. Introduction
   - Problem: conventional small-business life-cycle stages are too coarse.
   - Contribution: transaction-based diagnosis with two empirical lenses.

2. Literature Review
   - Small-business life-cycle policy.
   - Transaction-based business dynamics.
   - Time-series clustering/trajectory analysis.
   - Early prediction/business forecasting.

3. Data
   - KCD Seoul food-service weekly transaction data.
   - Metadata and weekly variables.
   - Sample construction.
   - Difference between entrant/post-entry sample and full observed-window sample.

4. Methodology
   - Post-entry trajectory labeling.
   - Observed-window Growth/Stable/Decline labeling.
   - Multinomial logit by business-age bucket.
   - Forecasting and feature ablation.

5. Main Result I: Heterogeneous Life-Cycle Trajectories
   - Post-entry trajectory patterns.
   - Full-sample observed-window distribution.
   - Composite main figure.

6. Main Result II: Age-Bucket Drivers
   - Trend, MDD, and new-customer ratio.
   - Volatility reinterpretation.
   - New-customer-ratio supplementary result.

7. Main Result III: Early Prediction
   - Prediction windows.
   - Feature-block ablation.
   - Practical targeting/declining-risk metrics.

8. Robustness And Additional Analyses
   - Label robustness.
   - Sample robustness.
   - Model robustness.
   - Method choice discussion.

9. Conclusion
   - Summary.
   - Policy implications.
   - Limitations: Seoul food-service sample, survivor bias, COVID-period shocks, non-causal design.

