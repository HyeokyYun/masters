# Forecasting Benchmark Literature Review

## 1. 목적

이 문서는 발표에서 사용할 수 있도록, `forecasting / prediction 성능이 어느 정도면 괜찮다고 볼 수 있는가`를 관련 문헌 기준으로 정리한 메모이다.

특히 아래 네 영역을 비교 대상으로 삼는다.

1. `stock-market forecasting`
2. `firm / sales forecasting`
3. `production-support forecasting`
4. `future demand forecasting`

핵심 결론부터 말하면, **우리 연구와 가장 가까운 비교 문헌은 stock-market이 아니라 retail / sales / demand forecasting 문헌**이다.  
주별 매출, 업장별 패널, 미래 성과 예측이라는 점에서 가장 가까운 것은 `retail demand forecasting`, `store/SKU sales forecasting`, `tactical sales forecasting` 쪽이다.

---

## 2. 먼저 정리해야 하는 기준

### 2.1 분야마다 주로 쓰는 지표가 다르다

- `금융 예측`에서는 `out-of-sample R2`, `directional accuracy`, `AUC`, `Sharpe ratio`를 많이 쓴다.
- `소매/수요 예측`에서는 `MAPE`, `MAE`, `RMSE`, `WAPE`, `WRMSSE`, `MASE`가 더 일반적이다.
- `분류 문제`로 바꾸면 `accuracy`, `F1`, `AUC`를 쓸 수 있지만, **순수 수치 예측 논문에서는 분류 지표보다 오차 지표가 표준**이다.

즉, **우리 결과가 R2 하나만 있으면 수요예측 문헌과는 직접 비교가 어렵다.**  
발표에서는 다음처럼 말하는 것이 가장 안전하다.

`금융 예측 문헌에서는 OOS R2가 자주 쓰이지만, 소매/매출 수요예측 문헌에서는 MAE, MAPE, WAPE, WRMSSE 같은 오차 지표가 더 표준적입니다. 따라서 우리 결과도 가능하면 R2와 함께 benchmark 대비 error reduction을 같이 제시하는 것이 바람직합니다.`

### 2.2 “좋은 성능”은 절대값보다 benchmark 개선폭으로 보는 경우가 많다

탑저널 문헌에서는 아래 방식이 흔하다.

- `naive / seasonal naive / linear baseline` 대비 몇 % 좋아졌는가
- `best statistical benchmark` 대비 몇 % 개선되었는가
- out-of-sample에서 안정적으로 이기느냐

즉, 발표에서도 `R2 = 0.43` 하나만 말하기보다,

- `naive 대비 얼마나 개선되는지`
- `linear regression 대비 얼마나 개선되는지`
- `classification으로 바꾸면 accuracy / F1이 얼마나 나오는지`

를 함께 주는 쪽이 문헌 관행에 더 가깝다.

---

## 3. 한눈에 보는 벤치마크

| 영역 | 사용자 연구와의 유사성 | 자주 쓰는 지표 | 문헌에서 보이는 성능 감각 |
|---|---|---|---|
| Stock-market forecasting | 낮음~중간 | OOS R2, ACC, AUC, F1, Sharpe | `OOS R2`는 매우 작아도 의미 있음. `0~2%` 수준도 강한 결과로 간주됨 |
| Firm / tactical sales forecasting | 높음 | MAPE, MAE, sMAPE, RMSE | 강한 논문은 baseline 대비 `10~20%+` 개선을 보임 |
| Production-support forecasting | 높음 | MAE, MAPE, RMSE | 생산/재고 의사결정용 예측은 error reduction과 operational value를 같이 봄 |
| Retail / future demand forecasting | 매우 높음 | MAE, MAPE, WAPE, WRMSSE, MASE | 상위 방법은 benchmark 대비 `10~25%` 수준 개선도 보고됨 |

---

## 4. Stock-market forecasting

### 4.1 Gu, Kelly, Xiu (2020), Review of Financial Studies

- 논문: `Empirical Asset Pricing via Machine Learning`
- 저널: `Review of Financial Studies`
- 링크: https://academic.oup.com/rfs/article/33/5/2223/5758276

이 논문은 금융예측에서 가장 자주 인용되는 기준 논문 중 하나다.  
핵심은 **머신러닝이 주가수익률 예측에서 기존 선형모형보다 낫더라도, out-of-sample R2 자체는 매우 작다**는 점이다.

직접 보고된 수치:

- 개별주식 월별 OOS R2:
  - Elastic Net `0.11%`
  - PCR `0.26%`
  - PLS `0.27%`
- S&P 500 월별 OOS R2:
  - GLM `0.71%`
  - 3-layer neural network `1.80%`

해석:

- 금융에서는 `OOS R2가 1% 안팎`이어도 매우 강한 결과다.
- 따라서 금융 문헌 기준으로 보면, 만약 우리 결과가 진짜 미래예측 `OOS R2 = 0.37~0.43`이라면 **상당히 큰 값**이다.
- 다만 금융의 target은 주가수익률이고 noise가 매우 크므로, 이 수치를 소매 매출 예측과 직접 비교하면 안 된다.

### 4.2 Campisi, Muzzioli, De Baets (2024), International Journal of Forecasting

- 논문: `A comparison of machine learning methods for predicting the direction of the US stock market on the basis of volatility indices`
- 저널: `International Journal of Forecasting`
- 링크: https://www.sciencedirect.com/science/article/pii/S0169207023000729
- 오픈 PDF: https://biblio.ugent.be/publication/01HZEQ2CFT9EG1TB7GY3TBTDF0/file/01HZEQ9WX35CGD3633QD8AGPVV.pdf

이 논문은 금융예측을 `방향 예측`으로 본 경우의 benchmark다.

직접 보고된 수치:

- feature selection 후 classification 성능:
  - Logistic regression: `ACC 0.6776`, `AUC 0.6365`, `F1 0.8076`
  - Random forest: `ACC 0.8239`, `AUC 0.8495`, `F1 0.8828`
  - Bagging: `ACC 0.8275`, `AUC 0.8493`, `F1 0.8845`

해석:

- 금융에서 `분류로 문제를 바꾸면` accuracy나 F1은 꽤 높게 나올 수 있다.
- 따라서 `R2가 낮다`와 `accuracy가 높다`는 서로 모순이 아니다.
- 이 때문에 발표에서는 **회귀 예측과 분류 예측의 숫자를 같은 척도로 비교하면 안 된다**고 분명히 말하는 편이 좋다.

### 4.3 Makridakis, Spiliotis, Michailidis (2025), International Journal of Forecasting

- 논문: `Avoiding overconfidence: Evidence from the M6 financial competition`
- 저널: `International Journal of Forecasting`
- 링크: https://www.sciencedirect.com/science/article/pii/S016920702400102X

직접 보고된 수치:

- `less than 25%`의 팀만 equal-probability benchmark를 이김
- benchmark의 RPS는 `0.16`
- 가장 정확한 제출도 benchmark보다 `2.2%`만 더 정확함

해석:

- 금융예측은 **benchmark를 조금만 이겨도 의미가 큰 영역**이다.
- 이 문헌은 금융에서 “잘 맞춘다”의 기준이 매우 엄격하다는 점을 보여준다.

### Stock-market 영역의 요약

- 금융에서는 `OOS R2`가 아주 작아도 publishable하다.
- direction classification에서는 `ACC 0.60~0.83`, `AUC 0.58~0.85`, `F1 0.72~0.88` 같은 수치가 나올 수 있다.
- 그러나 이 수치는 target 정의와 horizon에 크게 좌우된다.
- 따라서 **우리 연구를 금융 기준으로 설명하면 숫자가 과하게 좋아 보일 수 있으므로, 이쪽은 보조 비교용으로만 쓰는 것이 적절**하다.

---

## 5. Firm / Sales / Production-support forecasting

### 5.1 Lawrence, Edmundson, O’Connor (2000), European Journal of Operational Research

- 논문: `A field study of sales forecasting accuracy and processes`
- 저널: `European Journal of Operational Research`
- 링크: https://www.sciencedirect.com/science/article/pii/S0377221799000855

이 논문은 제조기업 판매예측 실무를 다룬 고전적인 benchmark다.

직접 보고된 결과:

- 13개 기업 field study
- `Only for a minority of four companies was the final company forecast significantly more accurate than the naive forecast.`

해석:

- 실무 sales forecasting에서는 생각보다 naive benchmark를 안정적으로 이기기 어렵다.
- 따라서 논문 발표에서 **“baseline 대비 얼마나 개선되는가”**를 보여주는 것이 매우 중요하다.

### 5.2 Sagaert, Aghezzaf, Kourentzes, Desmet (2018), European Journal of Operational Research

- 논문: `Tactical sales forecasting using a very large set of macroeconomic indicators`
- 저널: `European Journal of Operational Research`
- 링크: https://www.sciencedirect.com/science/article/pii/S0377221717305957

직접 보고된 수치:

- 제안한 접근법이 case company에서 정확도를 `18.8%` 개선

해석:

- 판매/생산지원 예측에서는 절대 R2보다 **error reduction percentage**가 많이 쓰인다.
- 탑저널 기준으로도 `10~20%대 개선`이면 충분히 강한 결과로 읽힌다.

### Firm / Sales / Production-support 영역의 요약

- 실무 sales forecasting은 naive를 항상 크게 이기지 못한다.
- 따라서 `18.8% improvement` 수준은 꽤 의미 있는 결과다.
- 우리 연구도 발표 때 `기준모형 대비 상대 개선폭`을 반드시 같이 주는 편이 좋다.

---

## 6. Future demand forecasting / Retail demand forecasting

이 영역이 사용자 연구와 가장 가깝다.  
주별 매출, 업장/점포 패널, 미래 수요, 운영 의사결정 연결이라는 점에서 가장 직접적인 comparison set이다.

### 6.1 Fildes, Ma, Kolassa (2022), International Journal of Forecasting

- 논문: `Retail forecasting: Research and practice`
- 저널: `International Journal of Forecasting`
- 링크: https://www.sciencedirect.com/science/article/pii/S016920701930192X

이 논문은 retail forecasting 전반을 정리한 review라서 발표에서 인용 가치가 높다.

핵심 메시지:

- causal models가 simple benchmark보다 대체로 낫다
- product-level retail forecasting에서는 오차 지표가 중심이다
- 당시까지는 ML superiority에 대한 증거가 제한적이었지만,
- 후속 논문들에서는 large-scale/global learning 상황에서 ML 우위가 점점 분명해지고 있다

발표용 해석:

`우리 문제는 주별 업장 매출 예측이므로 retail demand forecasting 문헌과 직접 비교하는 것이 더 타당하며, 이 문헌에서는 R2보다 MAE/MAPE/WAPE류가 더 표준입니다.`

### 6.2 Huber, Stuckenschmidt (2020), International Journal of Forecasting

- 논문: `Daily retail demand forecasting using machine learning with emphasis on calendric special days`
- 저널: `International Journal of Forecasting`
- 링크: https://www.sciencedirect.com/science/article/pii/S0169207020300224

핵심 내용:

- 독일 bakery chain
- `100개 이상 점포`
- `store-product level`
- production / delivery / staffing 의사결정과 직접 연결

직접 보고된 결론:

- machine learning이 기존 접근보다 더 정확
- `classification-based approaches outperform regression-based approaches`

해석:

- 사용자 연구와 가장 가까운 케이스 중 하나다.
- 특히 `점포`, `주기적 수요`, `운영 의사결정 연결`, `분류 문제로의 변환 가능성`이 매우 유사하다.
- 발표에서 이 논문을 사용하면, **우리도 forecasting을 회귀뿐 아니라 범주형 결과 예측으로 병행해 볼 이유가 있다**고 자연스럽게 연결할 수 있다.

### 6.3 Huang, Ma, Fildes (2016), European Journal of Operational Research

- 논문: `Demand forecasting with high dimensional data: The case of SKU retail sales forecasting with intra- and inter-category promotional information`
- 저널: `European Journal of Operational Research`
- 링크: https://www.sciencedirect.com/science/article/pii/S0377221715007845

직접 보고된 수치:

- baseline 대비 forecasting accuracy를 `12.6%` 개선
- 개선분의 `95%`는 intra-category 정보에서, `5%`는 inter-category 정보에서 옴

해석:

- 예측력 개선은 보통 `몇 %포인트 accuracy`보다 `error reduction`으로 제시된다.
- 또한 추가 변수는 많을수록 좋은 것이 아니라, **해당 업장과 가까운 경쟁/동종 정보가 핵심**이라는 점을 시사한다.
- 이는 이번 프로젝트에서 만든 `상권/경쟁 밀도`, `업종 × 경쟁도` 변수와도 잘 연결된다.

### 6.4 Huang, Fildes, Soopramanien (2014), European Journal of Operational Research

- 논문: `The value of competitive information in forecasting FMCG retail product sales and the variable selection problem`
- 저널: `European Journal of Operational Research`
- 링크: https://www.sciencedirect.com/science/article/pii/S0377221714001374

직접 보고된 결론:

- competitive information이 forecasting accuracy를 `substantially` 증가시킴

해석:

- 경쟁 정보, 동종 업종 밀집도, 주변 판촉/가격 환경이 중요하다는 점을 보여준다.
- 사용자 분석에서 만든 `competition density`, `업종 × competition` 항의 타당성을 지지하는 문헌으로 쓰기 좋다.

### 6.5 Elalem, Maier, Seifert (2023), International Journal of Forecasting

- 논문: `A machine learning-based framework for forecasting sales of new products with short life cycles using deep neural networks`
- 저널: `International Journal of Forecasting`
- 링크: https://www.sciencedirect.com/science/article/pii/S0169207022001364

직접 보고된 수치:

- simple `ARIMAX`가 DNN보다 `mean absolute errors up to 21%–24% lower`

해석:

- 이 문헌은 매우 중요한 메시지를 준다.
- **복잡한 딥러닝이 항상 더 좋은 것이 아니다.**
- 탑저널에서도 단순한 통계모형이 더 잘 나오는 경우가 충분히 있다.
- 따라서 발표에서는 `기본모형으로도 이미 상당한 성능이 나온다`는 점을 방어 논리로 사용할 수 있다.

### 6.6 Makridakis, Spiliotis, Assimakopoulos (2022), International Journal of Forecasting

- 논문: `M5 accuracy competition: Results, findings, and conclusions`
- 저널: `International Journal of Forecasting`
- 링크: https://www.researchgate.net/publication/357756884_M5_accuracy_competition_Results_findings_and_conclusions
- 관련 공식 배경 논문: https://www.sciencedirect.com/science/article/pii/S0169207021001187

직접 보고된 수치:

- top 50 방법 모두 best benchmark보다 `14% 이상` 개선
- top 5는 `20% 이상` 개선
- 1위 팀은 `22.4%` 개선

해석:

- retail demand forecasting에서 `10~20%대 error reduction`은 매우 강한 결과다.
- 이 benchmark는 사용자 연구처럼 `대규모 점포/상품 패널`, `미래 수요`, `운영 연결`이라는 점에서 비교 가치가 높다.

### Retail / future demand 영역의 요약

- 이 분야에서는 `R2`보다 `MAPE/MAE/WAPE/WRMSSE`가 표준적이다.
- 상위 논문은 baseline 대비 `12.6%`, `18.8%`, `21~24%`, `22.4%` 같은 개선폭을 보여준다.
- 따라서 우리 연구도 **R2만 제시하는 것보다 baseline 대비 error reduction을 추가하는 것이 훨씬 문헌 친화적**이다.

---

## 7. 사용자 연구에 가장 가까운 문헌은 무엇인가

가까운 순서대로 정리하면 다음과 같다.

1. `Huber & Stuckenschmidt (2020, IJF)`
   - 점포 수준
   - 수요/매출 예측
   - 생산/운영 의사결정 연결
   - 회귀 vs 분류 비교

2. `Huang, Ma, Fildes (2016, EJOR)`
   - 소매 제품 수준
   - 고차원 explanatory variables
   - 경쟁/동종 정보의 가치

3. `Sagaert et al. (2018, EJOR)`
   - sales forecasting
   - 생산/재고/원자재 계획 연결

4. `Elalem et al. (2023, IJF)`
   - 신제품/짧은 life cycle
   - 복잡한 ML이 항상 우위는 아님

보조 비교용:

5. `Gu, Kelly, Xiu (2020, RFS)`
   - 미래예측이라는 점에서 참고
   - 그러나 데이터 생성 구조가 너무 다름

6. `Campisi et al. (2024, IJF)`
   - 분류지표(ACC/F1/AUC) benchmark로 참고
   - 역시 금융이므로 직접 비교는 제한적

---

## 8. 발표에서 이렇게 말하면 좋다

### 8.1 한 문장 요약

`우리 연구와 가장 가까운 문헌은 retail demand forecasting과 tactical sales forecasting 문헌이며, 이 분야에서는 R2보다 MAE·MAPE·WAPE·WRMSSE 같은 오차 지표와 baseline 대비 개선폭이 더 표준적입니다.`

### 8.2 현재 결과를 해석하는 방법

만약 현재 결과가 다음과 같다면:

- `30주 기준 R2 ≈ 0.37`
- `50주 기준 R2 ≈ 0.43`

발표에서는 이렇게 해석하는 것이 안전하다.

`이 수치는 금융예측 문헌의 OOS R2와 비교하면 매우 큰 편입니다. 다만 우리 연구와 더 가까운 retail/sales forecasting 문헌에서는 R2 자체보다 benchmark 대비 error reduction을 더 중요하게 보기 때문에, 후속 보고에서는 naive 또는 단순 시계열 benchmark 대비 얼마나 오차를 줄였는지를 함께 제시하는 것이 적절합니다.`

### 8.3 실제 발표용 메시지

1. `금융예측에서는 OOS R2가 1% 내외여도 강한 결과입니다.`
2. `하지만 우리 연구는 금융보다 retail demand forecasting에 더 가깝습니다.`
3. `이 문헌에서는 보통 MAE/MAPE/WAPE/WRMSSE와 baseline 대비 10~20%대 개선 여부를 봅니다.`
4. `따라서 우리도 R2 하나만이 아니라 baseline 대비 개선폭을 같이 제시해야 문헌과 더 잘 맞습니다.`

---

## 9. 발표용 최종 결론

### 결론 1

`forecasting에서 어느 정도면 잘한 것인가`는 분야마다 다르다.

- 금융: `OOS R2 0~2%`도 강함
- 소매/수요예측: `baseline 대비 10~20%+ 개선`이면 강함
- 분류 문제: `ACC/F1/AUC`를 쓰지만 회귀 결과와 직접 비교하면 안 됨

### 결론 2

사용자 연구와 가장 가까운 문헌은 `retail demand / sales forecasting`이다.

### 결론 3

따라서 발표와 논문에서는 아래를 추가하는 것이 가장 중요하다.

1. `naive / linear / seasonal baseline` 대비 개선폭
2. 가능하면 `MAE`, `MAPE` 또는 `WAPE`
3. 필요하면 별도 분류문제로 바꾸어 `accuracy`, `F1`, `AUC`

### 결론 4

현재의 `R2 0.37~0.43`이 진짜 out-of-sample future forecasting이라면,  
단순히 낮다고 보기는 어렵고 **오히려 꽤 강한 신호일 가능성**이 있다.  
다만 탑저널 문헌과 같은 언어로 말하려면 `error-based benchmark comparison`이 반드시 필요하다.

---

## 10. 참고문헌 링크

1. Gu, Kelly, Xiu (2020), Review of Financial Studies  
https://academic.oup.com/rfs/article/33/5/2223/5758276

2. Campisi, Muzzioli, De Baets (2024), International Journal of Forecasting  
https://www.sciencedirect.com/science/article/pii/S0169207023000729

3. Campisi et al. open PDF  
https://biblio.ugent.be/publication/01HZEQ2CFT9EG1TB7GY3TBTDF0/file/01HZEQ9WX35CGD3633QD8AGPVV.pdf

4. Makridakis, Spiliotis, Michailidis (2025), International Journal of Forecasting  
https://www.sciencedirect.com/science/article/pii/S016920702400102X

5. Lawrence, Edmundson, O’Connor (2000), European Journal of Operational Research  
https://www.sciencedirect.com/science/article/pii/S0377221799000855

6. Sagaert, Aghezzaf, Kourentzes, Desmet (2018), European Journal of Operational Research  
https://www.sciencedirect.com/science/article/pii/S0377221717305957

7. Fildes, Ma, Kolassa (2022), International Journal of Forecasting  
https://www.sciencedirect.com/science/article/pii/S016920701930192X

8. Huber, Stuckenschmidt (2020), International Journal of Forecasting  
https://www.sciencedirect.com/science/article/pii/S0169207020300224

9. Huang, Ma, Fildes (2016), European Journal of Operational Research  
https://www.sciencedirect.com/science/article/pii/S0377221715007845

10. Huang, Fildes, Soopramanien (2014), European Journal of Operational Research  
https://www.sciencedirect.com/science/article/pii/S0377221714001374

11. Elalem, Maier, Seifert (2023), International Journal of Forecasting  
https://www.sciencedirect.com/science/article/pii/S0169207022001364

12. Makridakis, Spiliotis, Assimakopoulos (2022), International Journal of Forecasting, M5 background  
https://www.sciencedirect.com/science/article/pii/S0169207021001187

13. M5 Accuracy competition results excerpt  
https://www.researchgate.net/publication/357756884_M5_accuracy_competition_Results_findings_and_conclusions
