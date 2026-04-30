# 260325 TODO 진행 요약

## 이번 폴더에서 진행한 항목

1. 매출 변동성을 평균 기준 CV에서 추세조정 잔차 기반 지표로 다시 비교했습니다.
2. 업종 효과를 `Growth / Stable / Decline` 기준으로 다시 요약했습니다.
3. 동 단위 동일업종 비중을 경쟁 밀도 변수로 만들었습니다.
4. 패스트푸드/카페/술집과 지역 경쟁도의 인터랙션 항을 추가했습니다.
5. 업력 분포를 시각화하고 초기 업장(`<= 12개월`) 서브샘플을 분리했습니다.
6. 초기 업장 중 성장 업장의 특징을 별도 비교하고 로짓으로 점검했습니다.
7. 신규 고객 비율 해석을 강화하기 위해 분위 분석과 모델 비교를 추가했습니다.
8. 전체 meta 업장을 기준으로 한 `전체 업력` 분석을 별도로 추가했습니다.

## 기본 정보

- 현재 분석 표본 수: 21365.0
- 초기 업장 비율(<=12개월): 0.0313597004446524
- 추천 변동성 정의: vol_resid_rolling12
- 전체 meta 업장 수: 59023.0
- 전체 업력 중앙값(개월): 52.0

## 변동성 스크리닝 상위 결과

             metric  is_detrended  stable_mean  growth_mean  decline_mean    anova_f       anova_p
 vol_resid_rolling8          True     0.286240     0.219048      0.271224 269.994929 1.735718e-116
vol_resid_rolling10          True     0.295357     0.227763      0.280439 260.430793 1.948960e-112
vol_resid_rolling13          True     0.307652     0.238908      0.293227 251.422031 1.283089e-108

## 업종/경쟁/인터랙션 모델 적합도

                           model_name    nobs  pseudo_r2          llf          aic
               outcome3_industry_base 21365.0   0.597068 -9170.255403 18428.510807
                 outcome3_competition 21365.0   0.597816 -9153.228307 18414.456613
     outcome3_competition_interaction 21365.0   0.597903 -9151.250559 18422.501118
outcome3_competition_full_interaction 21365.0   0.598330 -9141.549390 18447.098779

## 초기 업장 요약

outcome_3  stores  mean_nc_rate  mean_preferred_volatility  mean_competition_index  mean_delivery_link
  Decline     276      0.659433                   0.289390                0.164297            0.326087
   Growth     172      0.625036                   0.272567                0.177499            0.331395
   Stable     222      0.650348                   0.249547                0.169423            0.288288

## 신규 고객 비율 모델 비교

                   model_name    nobs  pseudo_r2          llf          aic
outcome3_without_new_customer 21365.0   0.591356 -9300.271440 18680.542879
   outcome3_with_new_customer 21365.0   0.591904 -9287.799798 18659.599596

## 전체 업력 구간별 분석 표본 포함률

full_age_bucket  full_store_count  analysis_sample_count  inclusion_rate
           0_6m              2457                      7        0.002849
          6_12m              2222                    624        0.280828
         12_24m              5599                   5401        0.964637
         24_36m              7509                   7084        0.943401
         36_60m             17454                   8249        0.472614
        60_120m             16476                      0        0.000000
      120m_plus              7306                      0        0.000000

## 주요 산출물

- `outputs/tables/base_dataset.csv`
- `outputs/tables/volatility_candidates.csv`
- `outputs/tables/industry_effect_detail.csv`
- `outputs/tables/competition_density_summary.csv`
- `outputs/tables/business_age_bucket_summary.csv`
- `outputs/tables/full_business_age_bucket_summary.csv`
- `outputs/tables/full_age_sample_inclusion_summary.csv`
- `outputs/tables/young_store_growth_vs_others.csv`
- `outputs/tables/new_customer_quantile_summary.csv`
- `outputs/figures/volatility_comparison.png`
- `outputs/figures/industry_competition_overview.png`
- `outputs/figures/business_age_overview.png`
- `outputs/figures/full_business_age_overview.png`
- `outputs/figures/new_customer_overview.png`
