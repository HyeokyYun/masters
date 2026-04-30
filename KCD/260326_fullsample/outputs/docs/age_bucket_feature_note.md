# 업력 구간별 핵심 feature 메모

아래 결과는 전체 업장 observed-window 표본에서 업력 구간별로 `Growth / Stable / Decline`을 구분하는 feature를 따로 본 것입니다.

- 분석 표본: `50,635개`
- 종속변수: `outcome_3`
- 방법: 업력 구간별 다항 로짓(MNLogit)
- 사용 feature: `매출 추세`, `기존 변동성(CV)`, `최대 낙폭(MDD)`, `신규 고객 비율`, `배달 비중(log)`, `오전 매출 비중`, `주말 매출 비중`, `배달앱 입점`, `점포 면적`
- `n_observed_weeks_used`는 관측 구조 영향이 커서 해석용 중요도 표에서는 제외했습니다.

## 0~12개월
- `매출 추세`: Growth coef `11.494`, Decline coef `-9.014`, 해석은 `Growth 쪽으로 강하고 Decline은 억제`
- `최대 낙폭(MDD)`: Growth coef `-0.561`, Decline coef `1.176`, 해석은 `강한 신호는 아님`
- `기존 변동성(CV)`: Growth coef `0.679`, Decline coef `-0.045`, 해석은 `강한 신호는 아님`
- `배달 비중(log)`: Growth coef `0.729`, Decline coef `0.376`, 해석은 `강한 신호는 아님`

## 12~24개월
- `매출 추세`: Growth coef `8.839`, Decline coef `-8.219`, 해석은 `Growth 쪽으로 강하고 Decline은 억제`
- `최대 낙폭(MDD)`: Growth coef `-0.287`, Decline coef `1.265`, 해석은 `Growth를 억제`
- `신규 고객 비율`: Growth coef `0.376`, Decline coef `0.170`, 해석은 `Growth 쪽과 연결`
- `기존 변동성(CV)`: Growth coef `0.271`, Decline coef `0.128`, 해석은 `Growth 쪽과 연결`

## 24~36개월
- `매출 추세`: Growth coef `9.464`, Decline coef `-8.567`, 해석은 `Growth 쪽으로 강하고 Decline은 억제`
- `최대 낙폭(MDD)`: Growth coef `-0.101`, Decline coef `1.820`, 해석은 `Decline 쪽과 연결`
- `신규 고객 비율`: Growth coef `0.515`, Decline coef `0.156`, 해석은 `Growth 쪽과 연결`
- `배달 비중(log)`: Growth coef `-0.384`, Decline coef `-0.024`, 해석은 `Growth를 억제`

## 36~60개월
- `매출 추세`: Growth coef `10.046`, Decline coef `-8.169`, 해석은 `Growth 쪽으로 강하고 Decline은 억제`
- `최대 낙폭(MDD)`: Growth coef `0.001`, Decline coef `0.931`, 해석은 `Decline 쪽과 연결`
- `신규 고객 비율`: Growth coef `0.466`, Decline coef `0.223`, 해석은 `Stable보다 Growth/Decline 같은 동적 상태와 연결`
- `기존 변동성(CV)`: Growth coef `0.032`, Decline coef `0.111`, 해석은 `Decline 쪽과 연결`

## 60~120개월
- `매출 추세`: Growth coef `9.010`, Decline coef `-7.120`, 해석은 `Growth 쪽으로 강하고 Decline은 억제`
- `최대 낙폭(MDD)`: Growth coef `0.179`, Decline coef `1.070`, 해석은 `Stable보다 Growth/Decline 같은 동적 상태와 연결`
- `신규 고객 비율`: Growth coef `0.622`, Decline coef `0.331`, 해석은 `Stable보다 Growth/Decline 같은 동적 상태와 연결`
- `주말 매출 비중`: Growth coef `-0.106`, Decline coef `-0.027`, 해석은 `Growth를 억제`

## 120개월+
- `매출 추세`: Growth coef `8.074`, Decline coef `-6.163`, 해석은 `Growth 쪽으로 강하고 Decline은 억제`
- `신규 고객 비율`: Growth coef `0.510`, Decline coef `0.460`, 해석은 `Stable보다 Growth/Decline 같은 동적 상태와 연결`
- `최대 낙폭(MDD)`: Growth coef `-0.027`, Decline coef `0.762`, 해석은 `Decline 쪽과 연결`
- `오전 매출 비중`: Growth coef `0.287`, Decline coef `0.035`, 해석은 `Growth 쪽과 연결`
