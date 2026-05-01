# v4: 계절성 보정 점포 생애주기 예측 논문 초안

작성일: 2026-05-01

이 폴더는 2026-04-30 연구미팅 이후 학위논문 범위를 재정리한 버전이다. 기존 `v3`가 LEVI, EWS, Golden Cross, 생존편향, hybrid model까지 모두 포함한 넓은 DSR형 초안이었다면, `v4`는 석사학위논문 제출을 우선하기 위해 다음 하나의 중심 질문으로 범위를 좁힌다.

> 초기 카드거래 패턴은 이후 점포가 성장, 유지, 하락 중 어느 생애주기 상태로 이동할지를 예측할 수 있는가, 그리고 이 신호는 계절성을 통제해도 유지되는가?

## 핵심 범위

1. 서울시 외식업 점포의 주간 카드거래 패널을 사용한다.
2. 점포 단위의 Growth, Stable, Decline 생애주기 상태 예측을 주 분석으로 둔다.
3. 관측 초기 구간 길이와 예측 성능의 관계를 검토한다.
4. 마지막 고정 구간을 outcome으로 쓰는 기존 접근의 계절성 우려를 인정하고, 같은 월에 시작하는 rolling window 비교를 robustness check로 사용한다.
5. cluster, change-point, hybrid representation은 예측 성능을 높이는 보조 설명으로 포함하되, 사용 가능한 정보 시점이 예측 시점 이전인지 명시한다.

## 본문에서 낮추는 내용

- LEVI는 독립적인 도시경제 활력지수 논문으로 밀지 않는다.
- EWS는 본 논문의 중심 기여가 아니라 응용 가능성 또는 후속 연구로 둔다.
- Golden Cross는 신규고객 유입이 매출 반등을 선행한다는 보조 메커니즘으로만 사용한다.
- 정책 처방, 인과효과, 실제 현장개입 효과는 주장하지 않는다.

## 작성 파일

- [THESIS_FULL.md](THESIS_FULL.md): 전체 색인 및 논문 구조
- [ch0_abstract.md](ch0_abstract.md): 국문/영문 초록
- [ch1_introduction.md](ch1_introduction.md): 서론
- [ch2_literature.md](ch2_literature.md): 선행연구
- [ch3_data.md](ch3_data.md): 데이터
- [ch4_methodology.md](ch4_methodology.md): 방법론
- [ch5_results.md](ch5_results.md): 결과
- [ch6_discussion.md](ch6_discussion.md): 토의
- [ch7_conclusion.md](ch7_conclusion.md): 결론
- [references.md](references.md): 참고문헌 초안

## 현재 사용 가능한 근거

- 원자료: `original_data/weekly.parquet`, `original_data/meta.csv`
- 기존 예측 결과: `top_tier/outputs/`
- 260430 계절성 검증: `260430/docs/260430_seasonality_analysis_report.md`
- 260430 학위논문 방향 정리: `260430/docs/260430_thesis_story_update.md`
- 미팅 STT: `thesis/meeting_stt/260430_personal_meeting.txt`

