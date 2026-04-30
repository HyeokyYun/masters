# 260430 개별 연구미팅 — 발표 자료 보강 메모

작성일: 2026-04-30
짝 자료: [`260430_personal_meeting.docx`](260430_personal_meeting.docx)
출처 brief: [`260430_advisor_meeting.md`](260430_advisor_meeting.md), [`260430_additional_progress_brief.md`](260430_additional_progress_brief.md), [`260430_research_progress_share.md`](260430_research_progress_share.md)

목적: 발표 자료 docx에 빠져 있는 (a) 지난 피드백 매핑, (b) 핵심 수치, (c) docx에 누락된 기여 두 가지(C1·C2), (d) 학위 scope 권장, (e) 미팅 결정 안건을 한 곳에 정리. docx는 수정하지 않고 본 메모와 함께 참고.

---

## §1. 지난 260427 미팅 피드백 ↔ 오늘 진행 매핑

docx 단락 1 "지난 미팅 feedback 진행"의 두 갈래에 피드백 의도와 결과 해석을 함께 명시.

| 피드백 | 오늘 진행 (docx 단락) | 결과 | 의미 |
|---|---|---|---|
| ① 예측 window를 늘려가며 효과를 보자 | 단락 4–6: 주별 예측 10/30/50주 비교 | macro F1 0.46 → 0.63, **Decline recall +122%** (10→50주). Growth/Stable recall은 +14%에 그침 | window가 길어질수록 잡기 어려운 클래스인 Decline에 가장 큰 효과. 단, decline 잡기는 "주차 누적 데이터의 양"으로 결정됨을 정량화 |
| ② 초기 10주 vs 마지막 10주 기울기를 비교해 보자 | 단락 8–20: 두 기울기의 outcome 정합·상관·예측력 | 초기 10주 기울기는 Decline<Stable<Growth로 outcome 정합. 마지막 10주는 셋이 비슷 → outcome과 거의 무관. 두 기울기 간 상관 약함(독립). **둘 다 outcome 예측력은 낮음** | 단순 선형 기울기는 outcome을 가르는 신호로 부족 → §3의 **Volatility Paradox(C2)** 분해가 왜 필요한지 자연스럽게 연결됨 |

발표 시 한 줄: "지난 피드백 두 가지를 모두 진행했고, 두 번째에서 단순 기울기로는 outcome을 잘 못 가른다는 결과가 나와 변동성 분해(C2)로 넘어갔습니다."

---

## §2. 핵심 수치 보강 (docx의 정성 서술 옆에 붙일 숫자)

### 2.1 주별 예측 (docx 단락 4–6)

| 항목 | 10주 | 30주 | 50주 |
|---|---:|---:|---:|
| macro F1 | 0.46 | — | 0.63 |
| Decline recall | (기준) | — | **+122%** |
| Growth recall | (기준) | — | +14% |
| Stable recall | (기준) | — | +14% |

발표 추가 문장: "특히 Decline 잡기는 30주보다 50주에서 결정적으로 좋아지며, 30주 window는 Growth/Stable 분리에는 충분하지만 Decline 조기 식별에는 짧을 수 있다는 시사를 줍니다."

### 2.2 LEVI 외부 검증 (docx 단락 41–46)

docx에는 r=0.853 산점도 캡션과 폐업률 14.7–16.2%만. 다음 4건을 묶어 한 표로:

| 비교 | r | 의미 |
|---|---:|---|
| LEVI vs 서울시 생활인구 **변화율** | **+0.853** | 사람이 늘어나는 동네일수록 성장 점포가 많음 |
| LEVI vs 서울시 생활인구 **수준** | ≈ 0 | 동네 크기와 무관 — LEVI는 동태를 잡음 |
| LEVI vs 서울시 인허가 폐업률 | **−0.430** | 공식 폐업률 높은 동네일수록 LEVI 낮음 |
| KCD 분기매출 vs 상권분석 추정매출 (수준) | +0.766 | KCD 매출 흐름이 서울시 외식업 상권 매출 흐름과 일치 |
| KCD QoQ 매출증감 vs 외부 QoQ | +0.839 | 변화 방향까지 정합 |

추가: **LEVI 5개 공식 견고성** — 비중차·log-odds·평균 추세·중앙값 추세·shrinkage 5종 모두 서로 r ≥ 0.83. 공식 선택에 결과가 의존하지 않음을 한 줄로 언급.

출처: `260430_advisor_meeting.md` lines 95–98, `260430_research_progress_share.md` lines 63–66.

### 2.3 Golden Cross 인과 삼각검증 (docx 단락 51–52)

docx에는 방법명 3개만. 다음 수치로 보강:

| 방법 | 핵심 결과 |
|---|---|
| Granger | 3,000 점포 중 nc → sales 유의 **10.5%**, nc만 유의 8.8% |
| PSM + DiD | ATT **+0.1165 log-sales** (≈ **+12.3% 매출**, p < 1e-72) |
| Panel Two-way FE | nc_l1 / nc_l2 / nc_l4 모두 양·유의, nc lag 계수 약 **0.278** |

발표용 한 줄: "세 방법은 다른 약점을 가지지만 모두 같은 방향이라, '신규고객 유입은 매출 반등의 선행 신호이며 인과적 경로와 일관된 증거'라고 표현 가능합니다." (인과 표현 수위 — §5 결정 안건 3 참조)

출처: `260430_additional_progress_brief.md` lines 84–94, `260430_research_progress_share.md` lines 161–167.

### 2.4 EWS threshold 표 (docx 단락 59–64)

docx에는 정성 트레이드오프 서술만. 다음 표로 보강:

| Threshold | Accuracy | Precision | Recall | F1 | Flagged |
|---:|---:|---:|---:|---:|---:|
| 0.10 | 64.8% | 38.2% | **93.9%** | 0.544 | 54.7% |
| 0.25 | 79.3% | 52.4% | 78.3% | 0.628 | 33.3% |
| **0.30** | **81.4%** | 56.5% | 72.1% | **0.634** | 28.4% |
| 0.35 | 82.8% | 60.5% | 66.0% | 0.631 | 24.3% |
| 0.50 | 84.2% | 71.7% | 47.8% | 0.573 | 14.8% |

추가:
- **Decline Average Precision = 0.688** (baseline = 0.223, 약 3배)
- Cost-sensitive optimal threshold = **0.10**, max net utility = **43,626**
- 정책 모드별 권장: 균형형 0.30–0.35 / 놓침 비용 큰 모드 0.10

출처: `260430_additional_progress_brief.md` lines 117–142.

### 2.5 Hybrid Representation (docx 단락 67–68)

docx는 "정확도 올라감"만. 다음 수치로 보강:

| 모델 | F1 | AUC |
|---|---:|---:|
| Base (engineered 46D) | 0.548 | 0.736 |
| **Hybrid (46 + cluster + change-point = 64D)** | **0.639** | **0.824** |
| 개선 폭 | +0.091 | +0.088 |

발표 한 줄: "30주의 짧은 시계열·5만 점포 규모에서는 raw sequence 딥러닝보다 통계 특성 + cluster + change-point 결합이 더 효율적이라는 inductive bias 증거입니다."

출처: `260430_additional_progress_brief.md` lines 178–190.

---

## §3. docx에 빠진 두 가지 기여 (C1 · C2)

### 3.1 C1. Survivorship Bias — 5.4배 격차

- 분석 패널 내부 폐업률 **8.9%** vs 패널 바깥 폐업률 **48.3%** → 약 **5.4배 격차**.
- docx 단락 75에서 "Growth 41 / Stable 37 / Decline 22"라는 분포는 **이미 살아남을 확률이 5배 높은 집단**의 분포라는 점.
- 비유: 마라톤 완주자에게만 "어떠셨어요" 물으면 "할 만했어요"라 답함. 우리가 보고하는 것은 완주자만의 분포.
- 학위논문에 넣으면 정직성·방법론 기여가 커지나, 표본 해석 주의 메시지도 함께 온다.

### 3.2 C2. Volatility Paradox — outcome-conditional Cox PH

- V1에서 "성장 점포가 변동성 크다"는 관찰을 outcome-conditional 분해.
- 같은 cv 수치도 phase에 따라 **정반대 의미**:

| 표본 | Hazard Ratio (cv) | 의미 |
|---|---:|---|
| 전체 | 1.09 | 약한 위험 |
| Growth | **0.84** | 보호 |
| Stable | **0.61** | 보호 |
| Decline | **1.18** | 위험 |

- 이 결과가 **§1의 두 번째 피드백**(초기·마지막 기울기 모두 outcome 예측력 약함)과 직접 연결됨: 단순 선형 기울기 한 숫자로는 outcome이 안 갈리고, 변동성을 phase별로 분해해야 의미가 드러난다.

출처: `260430_advisor_meeting.md` lines 104, `260430_research_progress_share.md` lines 169–175.

---

## §4. V1 / V2 / V3 학위 scope 권장 (docx 단락 71–85 보강)

docx에는 V1/V2/V3 한 줄 스토리만 있고 권장 안이 없음. 짝 자료들이 일관되게 권장하는 안을 한 단락 추가:

> **권장: 학위논문 본문은 V2까지(점포 단위 진단 + LEVI 외부 검증). V3 추가분(Golden Cross 인과 격상·Volatility Paradox·Survivorship Bias·EWS 인공물·Hybrid 정식화)은 동일 데이터·코드를 그대로 활용해 영문 paper(HICSS 2027 우선, Small Business Economics 분기)로 분리.**

사유:
1. V1·V2 메시지("이중 렌즈 + LEVI 외적 타당성")는 본인이 자신 있게 방어 가능
2. V3 추가분은 분석·코드·결과가 모두 끝나 있는 자산 → paper로 즉시 분리 가능
3. 학위 통과 후 paper 진행 → 시간·정신 자원 분리
4. 동일 데이터의 두 산출물(한글 학위 + 영문 paper) 병행, 학위 narrative는 단단하게 유지
5. 작업량: V2 톤으로 일부 챕터(ch1·ch4·ch5·ch6) 회귀 + V2 시점 ch2·ch3·ch7·references 새로 작성 — 약 1.5–2시간 추정

출처: `260430_advisor_meeting.md` lines 79–86.

---

## §5. 미팅 결정 안건 (사용자 1순위 = 학위 scope)

오늘 미팅에서 받아야 할 결정. **위에서부터 순서대로** 다루는 것을 권장.

### 1. 학위 scope — V1 / V2까지 / V3 전체  ★ 1순위

| 옵션 | 내용 | 장점 | 리스크 |
|---|---|---|---|
| A. V1 중심 | 260409 outline 그대로 | 가장 단순, 방어 쉬움 | 최근 분석 자산을 못 씀 |
| **B. V2까지** (권장) | V1 + LEVI 외부 검증 | 학위로 안정적, 외적 타당성 ↑ | V3는 별도 paper 분리 |
| C. V3 전체 | 6대 기여 + DSR + EWS | 가장 강한 패키지 | 방어 부담·설명 복잡도 큼 |

이 결정이 풀려야 본문 정합·DSR 강도·인과 표현 수위가 모두 따라온다.

### 2. DSR 프레임 강도 (옵션 B 시 자연스럽게 약화)
- 약: "정책 활용 가능한 진단·조기경보 도구" 정도로만 표현
- 중: EWS·LEVI를 artifact라고 부르되 본문 중심은 생애주기 분석
- 강: build-evaluate 프레임을 논문 전체 구조로 사용

### 3. Golden Cross 인과 표현 수위
- 강한 표현: "신규고객 유입이 매출 반등을 인과적으로 일으킨다"
- **권장**: "신규고객 유입은 매출 반등을 선행하며, 복수의 식별 전략에서 인과적 경로와 일관된 증거를 보인다"

### 4. 투고 전략
- HICSS 2027 (도메인·DSR fit ★★★★★, 마감 **2026-06-15**) 우선
- 후속 Small Business Economics (도메인 fit 가장 정확)
- ICIS 2026 제외 (마감 임박 + IS theory framing 부담)

### 5. 심사 일정 / 위원 구성
- 예심·본심 일정
- 부심 위원 구성

### 6. Fig 5.2 (C1 Survivorship 시각화) 작성 여부
- C1을 학위 본문에 넣지 않으면 figure 작업 불필요
- C1을 부록·보조자료로만 두는 안도 가능

---

## §6. 미팅 직전 1분 체크리스트

- [ ] §1 매핑 표를 발표 모두에서 한 번 보여주기 (지난 피드백→오늘 진행)
- [ ] §2.2 LEVI 표, §2.3 Golden Cross 표, §2.4 EWS threshold 표를 docx 발표 중간에 호명
- [ ] §3 C1 5.4배 / §3 C2 outcome-conditional HR을 학위 scope 결정 직전에 제시 ("이 두 가지를 학위에 포함할지?")
- [ ] §4 권장안(B)을 명시하고 §5의 결정 6개 안건 순서대로 진행
