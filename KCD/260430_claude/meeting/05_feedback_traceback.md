# 04-30 미팅 피드백 추적표

> `thesis/meeting_stt/260430_personal_meeting.txt` 의 모든 피드백 항목과
> 본 폴더 / 본 미팅 자료에서의 처리 위치를 1:1로 매핑.

## 처리 완료

| # | 전사 라인 | 피드백 | 처리 위치 |
| --- | --- | --- | --- |
| 1 | 09:01–10:39 | "feature window와 target window를 같은 캘린더 월로 맞춰라. 2월 4월, 3월 5월 식으로 롤링." | 폴더 전체 (146 panel). `02_rolling_results.md` §1, §2-3. |
| 2 | 10:39 | "여러 단위, 여러 기간에 대해서도 가능하잖아요. 2월 8월, 3월 9월" | start_month 1..12 × window 1·2·3·4·6·7개월 모두 평가. `02_rolling_results.md` §1, §3. |
| 3 | 11:03 | "결과가 다이나믹하게 바뀌지 않을 수도, 더 잘 나올 수도" | 시즌 정렬 후 정확도 0.43–0.54 분산, 평균 변화 미미. `01_one_pager.md` 결론 박스 / `04_anticipated_qa.md` Q6. |
| 4 | 17:29 | "체인지 포인트랑 클러스터는 앞 정보로 알 수 있는 내용이?" | feature 구간만으로 산출. `02_rolling_results.md` §8 / `03_discussion_points.md` D8 / `04_anticipated_qa.md` Q1. |
| 5 | 18:32 | "마지막 거(베이스라인+클러스터+CP)는 academic 의미 있다" | Step 05 A/B/C/D 비교 + paired t-test. `02_rolling_results.md` §7. |
| 6 | 26:22 | "2022년 1월부터 시작도 봐라 (코로나 영향 ↓)" | sy2022_sm01..07 panel 전부 포함. 2021 vs 2022 비교 표. `02_rolling_results.md` §2-2. |
| 7 | 25:11 | "1월 첫째 주 소비 낮음 / 시즈널 다 달라서 조심" | 시작월별 macro-F1 / Decline recall 표로 직접 노출. `02_rolling_results.md` §2-3. |
| 8 | 07:37 | "마지막 8월 = 여름 휴가 빠진 거 아닌가" | 라벨 분포 sanity로 검출 (sm07/sm08 + off2 Decline 0.51–0.68). `02_rolling_results.md` §5 / `04_anticipated_qa.md` Q3. |

## 보류 결정 (현재 본 폴더 범위 밖이지만 미팅에서 톤 정리 필요)

| # | 전사 라인 | 피드백 | 처리 위치 |
| --- | --- | --- | --- |
| 9 | 21:33–22:55 | "2번(LEVI/도시경제) 빼라. 단 LEVI 빼고 도시경제 연결은 future work / 저널에서 ok" | `03_discussion_points.md` D7 첫 행. |
| 10 | 23:19–23:35 | "3번(EWS/조기 쇠퇴 경보)은 엔지니어링이라 academic angle 부족. 더 테크니컬해야" | `03_discussion_points.md` D7 두 번째 행. |
| 11 | 19:43 | "5번(외부 공공 데이터 5종)은 보강용 정도" | `03_discussion_points.md` D7 세 번째 행. |
| 12 | 27:34 | "5/8 학과 커미티 선정해서 제출" | `03_discussion_points.md` D7 네 번째 행. |

## 본 폴더에서 추가로 답해야 할 부분 (미팅 의제 확장)

| 항목 | 사유 | 처리 위치 |
| --- | --- | --- |
| 윈도우 길이 정착점 (w=3) 선언 | w 4·6·7 평탄, 비용 대비 함의 정량화 | `03_discussion_points.md` D4. |
| 시즈널 confound를 contribution으로 framing | hybrid contribution 약화 → 1번 framing 재조정 | `03_discussion_points.md` D3. |
| Step 05 panel 7개 vs 80개 D−A delta heatmap | 7 panel만으로 일반화 주장 어려움 | `03_discussion_points.md` D1. |
| top_tier legacy 재현 표 | "D ≫ A 0.05" 숫자 출처 검증 | `03_discussion_points.md` D6 task 3. |

## 본 폴더에서 의도적으로 다루지 않은 04-30 항목

| 항목 | 사유 |
| --- | --- |
| LEVI 지표 자체 산출식 / 새 외부 변수 연결 | future-work / 저널 트랙. |
| EWS 캘리브레이션 / cost-sensitivity | paper 트랙 별도 의제. |
| 외부 공공 데이터 5종의 raw 비교 그림 | 보강용. 본 미팅 의제 외. |
