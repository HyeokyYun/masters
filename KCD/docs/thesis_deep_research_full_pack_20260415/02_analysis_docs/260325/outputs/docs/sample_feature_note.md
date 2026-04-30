# 최근 개업 표본의 핵심 feature 메모

아래 결과는 `21,365개` 최근 개업 표본에서 `Growth / Stable / Decline`을 전반적으로 가르는 요인을 한 번에 요약한 것입니다.

- 방법: 다항 로짓(MNLogit)
- 종속변수: `outcome_3`
- 포함 변수: `매출 추세`, `추세조정 변동성`, `최대 낙폭`, `신규 고객 비율`, `배달 비중`, `오전/주말 비중`, `계절성`, `점포 면적`, `배달앱 입점`, `동일업종 밀집도`, `표본 내부 업력`, `주요 업종 더미`

- `매출 추세`: Growth coef `3.772`, Decline coef `-3.448`, 해석은 `Growth 쪽으로 강하고 Decline은 억제`
- `계절성 강도`: Growth coef `1.064`, Decline coef `1.144`, 해석은 `Stable보다 Growth/Decline 같은 동적 상태와 연결`
- `최대 낙폭(MDD)`: Growth coef `-0.035`, Decline coef `0.563`, 해석은 `Decline 쪽과 연결`
- `표본 내부 업력(개월)`: Growth coef `0.465`, Decline coef `0.255`, 해석은 `Stable보다 Growth/Decline 같은 동적 상태와 연결`
- `추세조정 변동성`: Growth coef `0.031`, Decline coef `-0.288`, 해석은 `Stable 쪽과 연결`
- `배달 비중(log)`: Growth coef `-0.067`, Decline coef `0.175`, 해석은 `Decline 쪽과 연결`
