# 260428 패널DB 결측 및 imputation 메모

작성일: 2026-04-28

## 기본 구조

- 사용 파일: `260204 대학기술사업화패널DB-재원구성(엄익천)v4.xlsx`
- 시트: `DB`
- 기간: 2007-2023
- 대학 수: 139
- 행 수: 2363
- 변수 수: 60

## 결측률 상위 변수

| variable | missing_count | missing_rate_pct | variable_group | recommended_imputation |
| --- | --- | --- | --- | --- |
| tncs | 662 | 28.0152 | analysis_or_control | within_school_linear_interpolation |
| p_top10 | 662 | 28.0152 | analysis_or_control | within_school_linear_interpolation |
| tto_commer | 551 | 23.3178 | analysis_or_control | bounded_linear_interpolation |
| tto_size | 548 | 23.1909 | analysis_or_control | within_school_linear_interpolation_round_nonnegative |
| tto_expert | 548 | 23.1909 | analysis_or_control | within_school_linear_interpolation_round_nonnegative |
| cumgrant_stock_3 | 417 | 17.6471 | analysis_or_control | within_school_linear_interpolation_round_nonnegative |
| pmistock_3 | 417 | 17.6471 | analysis_or_control | within_school_linear_interpolation |
| tto_exp | 89 | 3.7664 | analysis_or_control | within_school_linear_interpolation |
| dompatapp_num | 54 | 2.2852 | analysis_or_control | within_school_linear_interpolation_round_nonnegative |
| forepatapp_num | 54 | 2.2852 | analysis_or_control | within_school_linear_interpolation_round_nonnegative |
| dompatgrant_num | 52 | 2.2006 | analysis_or_control | within_school_linear_interpolation_round_nonnegative |
| forepatgrant_num | 52 | 2.2006 | analysis_or_control | within_school_linear_interpolation_round_nonnegative |

## 처리 원칙

- 식별자(`year`, `schoolname`)는 결측 대체하지 않고 원자료 확인 대상으로 둔다.
- 대학 특성 범주형 변수는 대학 내 최빈값으로 보완한 뒤 예외를 수동 확인한다.
- 연구비ㆍ교육비ㆍTTO 예산처럼 금액형 연속 변수는 대학 내 시간 보간을 기본으로 한다.
- 비율 변수는 보간 후 가능한 범위를 벗어나는지 확인한다.
- 건수 변수는 보간 후 음수 방지와 정수형 반올림을 적용한다.
- 네트워크 중심성 변수는 이번 회의에서 당장 필요하지 않다고 했으므로 1차 분석용 패널에서는 제외 후보로 둔다.
- 결측률이 50% 이상인 변수는 이론적으로 필수인지 먼저 확인하고, 설명변수로 바로 투입하지 않는다.

## 다음 단계

- 위 원칙을 기반으로 실제 imputed panel을 생성한다.
- 변수별 대체 전후 분포를 비교한다.
- 2013년 이후 분석용 버전과 2007년 이후 보조 분석용 버전을 분리한다.
