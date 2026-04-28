# 260428 — 학위논문 버전 진화 (V1 → V2 → V3)

작성: 2026-04-28
지도교수: KAIST 김지희 교수
주제: 지난 미팅 outline(V1) 이후의 점진적 확장 — 무엇이 언제, 왜 추가되었는지

> **본 자료는 미팅에서 교수님과 함께 보면서 학위논문 scope를 결정하기 위한 비교 문서입니다.** 단순한 변경 로그가 아니라 "왜 이렇게 진화했는가"의 동기 사슬을 함께 정리합니다.

---

## 0. 한눈에 보기 — 세 시점의 정체성

| | **V1** | **V2** | **V3** |
|---|---|---|---|
| **시점** | 지난 미팅 outline | LEVI 통합 | top_tier 통합 |
| **위치** | [drafts/v1/outline.md](../drafts/v1/outline.md) | [drafts/v2/](../drafts/v2/) | [drafts/v3/](../drafts/v3/) |
| **중심 메시지** | 이중 렌즈 (trajectory × state) | 이중 렌즈 + LEVI 외부 검증 (micro→meso→macro) | 6대 기여 (C1–C6) + DSR artifact |
| **기여 개수** | 3 | 3 | 6 |
| **사용 데이터** | KCD only | KCD + 서울시 공공 5종 | V2와 동일 |
| **분석 단위** | 점포 | 점포 + 자치구 | 점포 + 자치구 + 인공물 |
| **인과 식별** | ✗ | ✗ | ✓ (Granger + PSM-DiD + Panel FE) |
| **생존 분석** | ✗ | ✗ | ✓ (Cox PH + KM) |
| **DSR artifact** | ✗ | ✗ | ✓ (EWS + cost-sensitive) |
| **본인 방어 부담** | 낮음 | **낮음** | 높음 |

---

## 1. V1 → V2의 변화 — "외적 타당성" 한 가지 질문에서 출발

### 1.1 V1 마무리 시점에 떠오른 질문

> "KCD는 자사 가맹점만 포함된 단일 벤더 패널이다. 가맹점이 어떤 자기 선택(self-selection)으로 모인 집단일 가능성이 있고, 우리 데이터의 결과가 서울 전체 외식업으로 외삽 가능한지 모른다."

이 질문 하나에 답하려면 **KCD 외부**에서 독립적으로 측정된 자료와 비교하는 외부 검증이 필요합니다.

> **비유**: 한 카드사의 매출만 보고 "강남 상권이 좋아지고 있다"고 말하려면, 그 카드사 사용자가 강남 전체 결제의 어느 정도를 대표하는지 확인해야 합니다.

### 1.2 V2에서 새로 도입한 것

#### 새 데이터 (5종 외부 공공 데이터)

| 데이터 | 단위 | 본 연구 사용 |
|---|---|---|
| 서울시 생활인구 (LOCAL_PEOPLE_GU) | 자치구×시간대 | LEVI vs 인구 동태 검증 |
| 서울시 일반음식점 인허가 (seoul_food_permits.csv) | 점포 단위 | 자치구×월별 폐업률 산출 |
| 서울시 상권분석서비스 추정매출 (cda_est_sales) | 상권배후지×분기 | KCD 매출 vs 외부 매출 검증 |
| 서울시 상권분석서비스 자치구 점포 (cda_stores_by_district) | 자치구 | 점포 모집단 비교 |
| 서울시 상권분석서비스 배후지 점포 (cda_stores_by_hinterland) | 상권배후지 | 향후 확장 |

#### 새 분석

- **LEVI 설계**: 자치구별 (Growth−Decline)/N를 5개 공식(V1–V5)으로 산출
- **외부 상관 분석**: LEVI vs 생활인구·인허가·상권분석 추정매출의 Pearson·Spearman 상관

#### V2의 결과

| 검증 항목 | 결과 |
|---|---|
| LEVI vs 생활인구 변화율 | r = **0.853** |
| LEVI vs 생활인구 수준 | r ≈ 0 |
| LEVI vs 인허가 폐업률 | r = **−0.430** |
| KCD 분기매출 vs 상권분석 추정매출 | r = 0.766 (수준), 0.839 (QoQ) |

### 1.3 V2의 메시지 격상

V1 메시지: "이중 렌즈 + 30주 조기 예측"
↓
V2 메시지: "이중 렌즈 + LEVI를 통한 외적 타당성 입증 — micro(점포) → meso(자치구) → macro(도시 동태)"

V2는 V1의 메시지를 부정하지 않고 **확장**합니다. 점포 분석 결과는 그대로 살아있고, 그 결과를 자치구로 모아 외부 자료와 비교한 한 층이 추가됩니다.

### 1.4 V2 시점에 인지된 한계 (여전히 남은 것)

- **인과 해석 불가**: 여전히 진단·예측 틀
- **변동성의 의미 모호**: "변동성=위험" vs "Growth가 변동성 큼" 모순 미해결
- **생존 편향의 크기 미측정**: 5.4배 정량화는 V3에서 등장
- **운영 임계치 미정**: F1 0.572를 정책이 어떻게 사용해야 하는가 모호

---

## 2. V2 → V3의 변화 — top_tier 영문 paper 통합

### 2.1 V2 마무리 시점에 떠오른 4가지 질문

V2까지 답하지 못한 것들이 다음 4가지로 정리되었습니다.

1. **표본 편향의 크기는?** (지난 미팅 한계 #3을 정량화)
2. **변동성의 의미는 phase 의존?** (V2 시점의 모호함 해결)
3. **신규고객 → 매출이 인과인가?** (지난 미팅 한계 #1을 부분 극복)
4. **모델을 운영 인공물로 변환?** (V2 시점의 정책 활용성 강화)

이 4가지 질문은 영문 top-tier paper(HICSS/ICIS/DSS) 투고를 염두에 두고 깊이 있게 답해야 했습니다.

### 2.2 V3에서 새로 도입한 것

#### 새 분석 도구 (V2 대비)

| 도구 | 답하는 질문 | 본 연구에서의 결과 |
|---|---|---|
| 단순 비교 (panel 내부 vs 외부) | Q1 표본 편향 | 8.9% vs 48.3%, **5.4배** |
| Cox PH + outcome-conditional | Q2 변동성 의미 | Growth HR 0.84, Stable 0.61, Decline 1.18 |
| Granger 인과 | Q3 인과 (1) | nc → sales 비대칭 8.8% |
| PSM + DiD | Q3 인과 (2) | ATT = +0.1165 log-sales |
| Two-way Panel FE | Q3 인과 (3) | nc_l1 계수 0.278 |
| Hybrid 64D + Deep baseline | (V2의 보너스) | F1 0.639 / AUC 0.824 |
| Cost-sensitive threshold + Net utility | Q4 운영 인공물 | t = 0.10, utility 43,626 |
| DSR (Hevner·Peffers) 프레임 | (전체 격상) | EWS·LEVI를 artifact로 위치 |

#### 새 데이터

V2와 동일. V3에서는 **새 데이터 도입은 없고 새 분석만 추가**.

### 2.3 V3의 6대 기여 (C1–C6)

| 기여 | 한 줄 설명 | V2 대비 신규 |
|---|---|---|
| **C1** | 표본 편향 5.4배 정량화 | ✓ 신규 |
| **C2** | 변동성 역설의 phase 의존 분해 | ✓ 신규 |
| **C3** | 신규고객 → 매출 인과 삼각검증 | ✓ 신규 |
| **C4** | Hybrid 64D가 Deep을 상회 | ✓ 신규 |
| **C5** | EWS 인공물 + cost-sensitive 평가 | ✓ 신규 |
| **C6** | LEVI 외부 검증 | V2에서 이미 있음 |

V2의 3대 기여(이중 렌즈·업력별 driver·30주 예측·LEVI)는 V3에서 다음과 같이 흡수됩니다.

- "이중 렌즈" → Ch.5 §5.1 도입부로 압축
- "업력별 driver" → Ch.5 §5.8로 유지
- "30주 예측" → C4 (Hybrid)로 격상·재구성
- "LEVI" → C6로 명명 유지

### 2.4 V3의 메시지

> "주별 거래 데이터는 (1) 생애주기 분포의 편향 측정, (2) 변동성의 phase 의존성, (3) 신규고객 → 매출 인과, (4) Hybrid 표현의 우위, (5) cost-sensitive EWS 인공물, (6) 도시 모니터링 LEVI의 6가지 기여를 동시에 제공한다."

---

## 3. 세 버전의 점진적 확장 시각화

```
V1 (지난 미팅 outline)
├── KCD 점포 데이터
├── 시계열 클러스터링
├── Multinomial Logit (업력별 driver)
├── GBM 30주 조기 예측
└── 메시지: "이중 렌즈 + 조기 진단 가능"
           ↓
        [동기: 외적 타당성 검증]
           ↓
V2 (LEVI 통합)
├── KCD 점포 데이터
├── + 서울시 공공 5종 외부 데이터  ← 신규
├── 시계열 클러스터링
├── Multinomial Logit
├── GBM 30주 조기 예측
├── + LEVI 5공식 + 외부 상관 검증  ← 신규
└── 메시지: "이중 렌즈 + 외적 타당성 (micro→meso→macro)"
           ↓
        [동기: 영문 paper 깊이 있는 contribution]
           ↓
V3 (top_tier 통합 + DSR)
├── KCD 점포 데이터
├── 서울시 공공 5종 외부 데이터
├── 시계열 클러스터링
├── Multinomial Logit
├── GBM 30주 조기 예측
├── LEVI 5공식 + 외부 상관 검증
├── + 표본 편향 5.4배 정량화 (C1)  ← 신규
├── + Cox PH outcome-conditional (C2)  ← 신규
├── + Granger + PSM-DiD + Panel FE (C3)  ← 신규
├── + Hybrid 64D + Deep baseline (C4)  ← 신규
├── + EWS cost-sensitive threshold (C5)  ← 신규
├── + DSR 프레임 (Hevner·Peffers)  ← 신규
└── 메시지: "6대 기여 + DSR artifact"
```

---

## 4. 학위논문 scope 결정 — 세 옵션

본인이 학위논문에 어디까지 담을지를 미팅에서 결정해야 합니다. 세 옵션의 trade-off:

### 옵션 A. V1 그대로 학위 + V2·V3 모두 paper 분리

| 장점 | 단점 |
|---|---|
| 본인 방어 부담 최소 | 학위가 짧고 보수적 |
| 지난 미팅 outline 그대로 | LEVI 외부 검증의 강한 결과(r=0.853) 학위에서 활용 못 함 |
| 작업 부담 낮음 | KCD 단일 패널 한계가 학위 안에서 미해결 |

### 옵션 B. V2 학위 + V3 추가분만 paper (본인 추천)

| 장점 | 단점 |
|---|---|
| LEVI까지 학위 포함 → 외적 타당성 입증 | 외부 데이터 처리 작업 (이미 끝나 있음) |
| 본인 방어 부담 여전히 낮음 (LEVI는 단순) | V2 본문 4개 장(Ch.2/3/7/Ref)을 V3 정합에서 V2 정합으로 회귀 |
| micro→meso→macro 자연 narrative | |
| 학위 통과 가능성 높음 | |

### 옵션 C. V3 학위 (현행)

| 장점 | 단점 |
|---|---|
| 6대 기여 모두 활용 → 가장 풍부 | 본인 방어 부담 매우 큼 |
| 학위 = paper 단일 산출물 | C2·C3·C5의 통계적 정교함을 본인이 모두 설명해야 함 |
| | 심사위원 질문에 답할 부담 |

---

## 5. 옵션 B를 선택할 때의 작업 정리

### 5.1 무엇을 V2 정합으로 되돌려야 하는가

현재 [drafts/v3/](../drafts/v3/) 본문 9개 중 V2 정합으로 되돌려야 하는 부분:

| 파일 | V3 추가분 (제거 대상) | V2 시점 본 위치 |
|---|---|---|
| ch0_abstract.md | 6 contributions list | drafts/v2/ch0_abstract_and_frontmatter.md |
| ch1_introduction.md | RQ1–RQ6, 6대 기여 명시 | drafts/v2/ch1_introduction.md |
| ch2_literature.md | §2.4.3 DSR, §2.4.4 생존·인과, §2.5 C1–C6 매핑 | (V2 시점 본 없음, 별도 정리 필요) |
| ch3_data.md | §3.3.3 상권분석서비스, §3.4.1 C1 수치 | (V2 시점 본 없음, 별도 정리 필요) |
| ch4_methodology.md | DSR 프레임, C1–C6 분석법 | drafts/v2/ch4_methodology.md |
| ch5_results.md | C1–C6 순차, Cox PH, Granger·PSM·DiD, Hybrid, EWS | drafts/v2/ch5_results.md |
| ch6_discussion.md | DSR 평가, 인과 한계 | drafts/v2/ch6_discussion.md |
| ch7_conclusion.md | C1–C6 기여별 결론 | (V2 시점 본 없음, 별도 정리 필요) |
| references.md | Cox·KM·Granger·PSM·DiD·XGBoost | (V2 시점 본 없음, 별도 정리 필요) |

### 5.2 작업 양 추정

- drafts/v2/ 에 보관된 5개 파일은 그대로 사용
- 4개 파일(ch2/ch3/ch7/references)은 V2 톤으로 새로 작성 — 1.5–2시간 소요 추정
- THESIS_FULL.md V2 색인 갱신
- V3는 그대로 보관 → paper용 자료로 활용

### 5.3 미팅 자료 재작성

본 자료([260428_version_evolution.md](260428_version_evolution.md))와 함께:
- [260428_advisor_meeting.md](260428_advisor_meeting.md): 옵션 B 결정에 맞춰 "학위 = V2, paper = V3 추가분"의 분리 전략으로 톤 조정
- 또는 본 자료가 미팅 메인이 되고 260428_advisor_meeting.md는 보조

---

## 6. 미팅 진행 가이드 (제안)

| 단계 | 내용 | 시간 |
|---|---|---|
| 1 | §0 한눈 비교표로 세 시점 정체성 공유 | 3분 |
| 2 | §1 V1→V2 변화 (외적 타당성 동기 + LEVI) | 7분 |
| 3 | §2 V2→V3 변화 (4가지 새 질문 + V3 도구) | 7분 |
| 4 | §3 시각화로 점진적 확장 시각 확인 | 3분 |
| 5 | §4 학위 scope 옵션 A/B/C 비교 | 5분 |
| 6 | **결정**: 학위논문은 어느 버전으로? | 10분 |
| 7 | (옵션 B 결정 시) §5 작업 양 확인 | 5분 |

---

## 7. 미팅 시 본인이 자신 있게 답할 수 있는 질문 vs 어려운 질문

본인이 미팅에서 받을 만한 질문을 미리 분류해 봅니다.

### 자신 있게 답 가능 (V1·V2 범위)

- "이중 렌즈가 뭔가요?" → post-entry trajectory와 observed-window state 두 관점
- "LEVI가 뭔가요?" → 자치구별 (Growth−Decline)/N
- "LEVI가 외부 자료와 일치하나요?" → 생활인구 변화율과 r=0.853
- "왜 외부 데이터가 필요했나요?" → KCD 단일 벤더의 외적 타당성 검증
- "30주 예측 성능은?" → GBM weighted F1 0.572 (V1) 또는 Hybrid 0.639 (V3)

### 답하기 어려운 질문 (V3 추가분)

- "Cox PH의 비례위험 가정 검증은?" → Schoenfeld 잔차…
- "PSM에서 caliper는?" / "공통 지지(common support) 진단은?"
- "Granger 인과의 잔여 위협은?" / "Two-way FE의 점포×시점 상호작용 충격은?"
- "DSR 6단계 중 본 연구의 ‘rigor cycle’은?"
- "Cost matrix의 B/C_support/C_miss 값은 어떻게 정했나?"

만약 옵션 C(V3 학위)로 가면, 위 어려운 질문 목록을 모두 본인이 방어해야 합니다.
옵션 B(V2 학위)로 가면, 위 어려운 질문은 모두 "이건 학위 scope 밖, paper에서 다룹니다"로 답하면 됩니다.

---

## 8. 본인 추천: **옵션 B**

이유 정리:
1. 본인이 자신 있게 방어 가능한 V2 메시지로 학위 마무리
2. LEVI(C6)는 V2에 이미 포함되어 학위 narrative를 단단하게 만듦
3. V3에서 추가된 어려운 분석들(Cox·인과·DSR·EWS)은 이미 끝나 있는 자산이므로 paper로 즉시 분리 가능
4. 학위 통과 후 paper 진행으로 시간·정신 자원 분리
5. 영문 paper에서는 V3 추가분이 메인 contribution → 같은 데이터·코드의 두 산출물 병행 가능

---

## 9. 최종 결정 후 다음 단계 (옵션 B 기준)

1. drafts/v2/ 의 V2 본문 5개 검토 (Ch.0/1/4/5/6)
2. Ch.2/3/7/references를 V2 정합으로 새로 작성 (V3 추가분 제거)
3. drafts/v2/THESIS_FULL_V2.md 색인 갱신
4. 미팅 자료 [260428_advisor_meeting.md](260428_advisor_meeting.md)을 옵션 B 톤으로 재작성
5. (병행) [top_tier/paper_draft/](../../top_tier/paper_draft/) 의 영문 paper 작성 진행

---

*본 자료는 [drafts/v1/outline.md](../drafts/v1/outline.md), [drafts/v2/](../drafts/v2/), [drafts/v3/](../drafts/v3/) 의 실제 본문과 정합합니다. 미팅에서 교수님과 함께 보면서 옵션 A/B/C 중 하나를 결정하는 것이 본 자료의 목적입니다.*
