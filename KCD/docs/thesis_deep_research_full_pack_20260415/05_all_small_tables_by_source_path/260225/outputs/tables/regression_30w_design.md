# Step 3: 회귀 2가지 설계

## (1) 전체 데이터 회귀
- Step 2 Multinomial Logit과 동일
- X: 전체 기간 요약 변수 (new_customer_ratio, cv_sales_card, business_age_months 등)

## (2) 첫 30주만 사용 회귀
- X: early_avg, early_cv, early_slope, business_age_months
- 30주 변수가 유의하면 → "초기 30주가 성공 예측" 주장 가능