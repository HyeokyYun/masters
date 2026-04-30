# 260430 지도교수 미팅 메모

작성: 2026-04-30
지도교수: KAIST 김지희 교수
보조 자료: [260427_advisor_meeting.md](260427_advisor_meeting.md), [260428_advisor_meeting.md](260428_advisor_meeting.md), [260428_unified_briefing.md](260428_unified_briefing.md), [260428_version_evolution.md](260428_version_evolution.md), [260428_glossary.md](260428_glossary.md)

원본 outline: [260409/THESIS_OUTLINE.md](../../260409/THESIS_OUTLINE.md) — 본 메모의 V1 베이스라인

---

## 진행한 것 — V1 → V2 → V3 두 차례 확장

원본 V1 outline은 그 자체로 완성도 있는 석사 논문 구성. V2·V3는 V1을 부정하지 않고 위에 두 층을 얹은 확장입니다. 각 층에서 무엇을 더했고 왜 더했는지를 분리해 정리합니다.

### V1 (베이스라인, 260409 outline)에 이미 있던 것

- Hybrid clustering = K-Shape + Change Point Detection → **UDX 상태 코드** (4장)
- **Golden Cross 발견** — 반등 점포에서 t=−4부터 신규고객 비율 선행 급등 (5.1) — *descriptive*
- **Volatility-driven Growth 발견** — 성장 집단이 쇠퇴/유지 집단보다 초기 변동성 큼 (5.2) — *descriptive*
- Multinomial Logit으로 영향 인자 분리 (5.2)
- Early Prediction 모델 A/B/C/Proposed, F1 0.68 → 0.84 (6장)

V1은 **발견(descriptive) 단계**의 이야기로 이미 한 편의 논문으로 완성됨. 본인 방어 부담 낮음.

### V1 → V2: 외적 타당성 질문 한 가지에 답하기 위한 확장

- **추가한 것**
  - 서울시 외부 공공데이터 **5종** 통합: 생활인구(LOCAL_PEOPLE_GU), 일반음식점 인허가(seoul_food_permits), 상권분석서비스 추정매출(cda_est_sales), 자치구/배후지 점포 현황(cda_stores_*)
  - 분석 단위 확장: 점포 → **자치구**(meso) 집계
  - **LEVI(Local Economic Vitality Index)** 설계 — 자치구별 활력 지수, 정의는 (Growth 점포 수 − Decline 점포 수) / 전체 점포 수
    - *비유*: 동네의 "기온" 같은 것. 양수면 동네가 **따뜻해지는 중**(상권 활력 ↑), 음수면 차가워지는 중(쇠퇴)
    - *잡는 것*: 동네가 **활성화되는 동태**(인구 변화율과 r=0.853)
    - *잡지 않는 것*: 동네 크기·인구 수준(인구 수준과 r ≈ 0) → "큰 동네에서 잘된다"가 아니라 "동네 동태"를 잡음
    - 점포 단위 분석 결과를 자치구로 모아서 외부 공공자료와 직접 비교 가능한 **하나의 숫자**로 압축한 것이 핵심
  - LEVI 5개 공식(V1~V5: 비중차·log-odds·평균 추세·중앙값 추세·shrinkage) 견고성 점검 — 공식 간 r ≥ 0.83 → 결과가 특정 공식 선택에 의존하지 않음
- **이유**
  - KCD는 단일 벤더(자사 가맹점)에서만 수집된 패널 → 서울 외식업 모집단의 동태와 일치하는지 검증 불가
  - V1의 모든 결과는 KCD 패널 내부 결과 — 외부 자료와 한 번도 비교한 적이 없음
- **V1과의 관계**: V1을 부정하지 않고 한 층(meso-macro)을 위에 얹음. V1의 점포 단위 결과는 그대로 살아있고 외부에서 한 번 더 검증한 셈
- **메시지 격상**: "이중 렌즈 + 30주 조기 예측" → "이중 렌즈 + LEVI 외적 타당성 (micro → meso → macro)"
- **학위 방어 부담**: **낮음** — 새 통계 기법이 거의 추가되지 않고, 외부 데이터 매칭과 상관 분석이 주

### V2 → V3: 두 묶음으로 나뉨 — (a) V1 발견의 격상 + (b) 완전 새 차원

V3 추가분은 성격이 다른 두 묶음입니다.

**(a) V1 발견을 "정식 통계 식별"로 격상** — descriptive → formal identification

| V1 (descriptive) | V3 (formal identification) |
|---|---|
| Golden Cross — 신규고객 선행 급등 *관찰* | **Granger + PSM-DiD + Panel FE 인과 삼각검증** → 인과 주장 (ATT +12%, p<1e-72) |
| Volatility-driven Growth — 성장 집단 변동성 큼 *관찰* | **Cox PH outcome-conditional + 4가설 분해** → Volatility Paradox로 재해석 (Growth 보호, Decline 위험) |
| Proposed Model — UDX + 시퀀스 결합 | **Hybrid 64D representation 정식화** (engineered 46 + cluster + change-point) + LSTM/GRU/Transformer 비교 |

각 도구 간단 설명:
- *Cox PH*: 보험회사가 "흡연자가 비흡연자보다 시간당 사망 위험 1.5배"라고 추정할 때 쓰는 통계 기법. 이걸 outcome별로 쪼개서 같은 변동성 수치도 phase에 따라 의미가 달라짐을 보임
- *Granger + PSM-DiD + Panel FE*: 세 명의 다른 의사가 다른 검사로 모두 "암"이라 진단하면 한 명만 진단했을 때보다 신뢰. 셋이 동시에 거짓양성일 확률은 거의 0
  - Granger = 시간 선행 / PSM-DiD = 비슷한 짝 매칭 후 처치 전후 차이의 차이 / Panel FE = 같은 점포 시간 변화 + 공통 시간 충격 제거

→ 의미: "발견했다"에서 "통계적으로 식별했다"로 격상. 학술적 무게는 늘지만 본인이 방어해야 할 통계 지식(비례위험 가정·PSM caliper·잔여 confounder)도 늘어남.

**(b) V1에 없던 완전 새 기여**

- **Survivorship Bias 정량화 (C1)** — 분석 패널 내부 vs 외부 폐업률 직접 비교 (5.4배 격차)
  - *비유*: 마라톤 완주자에게만 "마라톤 어떠셨어요?"라 물으면 "할 만했어요"라 답함. 포기자 답은 들리지 않음. 우리가 보고한 분포가 "완주자만의 분포"임을 측정
  - Denrell(2003) 이론 경고를 한국 소상공인 데이터로 처음 숫자화
- **EWS 인공물 (C5)** — Cost-sensitive threshold + Net utility 산출
  - *비유*: 응급실 트리아지(녹·황·적). 모든 환자를 동등하게 보지 않고 위험 점수 + 임계치로 자원 배분. 놓치는 비용이 가짜 경고 비용보다 크면 임계치를 낮춤
  - 모델을 단순 분류기가 아닌 **정책 의사결정 도구**로 변환
- **DSR framing** (Hevner 2004 / Peffers 2007)
  - *비유*: 학회 발표 두 모드. (A) "X 데이터에서 Y 패턴 발견" vs (B) "X 데이터로 Z 도구를 만들고 평가". V3는 모드 B
  - 연구의 메타 프레임 자체를 "발견 모드"에서 "인공물 설계·평가 모드"로 전환

→ 의미: V1에 없던 새 차원(생존 편향·정책 도구·연구 패러다임)을 도입. 가장 야심차지만 가장 방어 부담이 큰 부분.

- **메시지 격상**: "이중 렌즈 + LEVI 외적 타당성" → "6대 기여(C1~C6) + DSR artifact"
- **학위 방어 부담**: **높음** — Cox PH 비례위험 가정·PSM caliper·Granger 잔여 위협·DSR 6단계·cost matrix 정당화 모두 본인이 직접 설명 가능해야 함

### 제안: 학위논문은 V2까지, V3 추가분은 영문 paper로 분리

- **이유**
  1. V1·V2 메시지(이중 렌즈 + LEVI 외적 타당성)는 본인이 자신 있게 방어 가능
  2. V3 추가분 (a) V1 발견의 격상 분석 + (b) 새 차원(Survivorship·EWS·DSR)은 이미 분석·코드·결과 모두 끝나 있는 자산 → paper로 즉시 분리 가능
  3. 학위 통과 후 paper 진행 형태로 **시간·정신 자원 분리** 가능
  4. 동일 데이터·코드의 두 산출물(한글 학위 + 영문 paper) 병행, 학위 narrative는 단단하게 유지
- **작업량**: V2 톤으로 일부 챕터(ch1·ch4·ch5·ch6) 회귀 + V2 시점에 본 없는 챕터(ch2·ch3·ch7·references) 새로 작성 — 약 1.5~2시간 추정

## 결과 공유

### V2 산물 (학위 scope에 포함)

- **C6 LEVI 외부 검증**
  - 한 줄 결론: KCD 단일 벤더 패널의 결과가 서울시 외식업 전체와 강하게 일관 → **외적 타당성 확보**
  - 검증 수치
    - LEVI vs 서울시 생활인구 변화율 **r = 0.853** (매우 강한 정방향)
    - LEVI vs 생활인구 수준 r ≈ 0 (동네 크기와는 무관)
    - LEVI vs 인허가 폐업률 r = **−0.430** (방향 일관)
    - KCD 분기 매출 vs 상권분석 추정매출 r = 0.766 (수준), 0.839 (QoQ 변화)
  - 자치구 분포: 상위는 종로·중구·용산·강남·마포(도심·업무지구), 하위는 중랑·강북·도봉(외곽 주거지) → 경제 지리적 직관과 일치

### V3 산물 — (a) V1 발견의 격상 (paper로 분리 검토)

- **C2 Volatility Paradox** (V1의 Volatility-driven Growth 격상)
  - 같은 변동성 수치도 **점포 상태에 따라 정반대 의미**. 전체 cv HR=1.09(위험)이지만 outcome별로 분리하면 Growth 0.84(보호) / Stable 0.61(보호) / Decline 1.18(위험)
- **C3 Golden Cross 인과** (V1의 Golden Cross 격상)
  - 신규고객과 매출이 단순 동반이 아니라 **신규고객이 매출의 원인**. 정책이 신규고객 유입을 늘리는 개입(SNS·쿠폰 등)을 하면 평균적으로 다음 주 매출 +12% 기대
- **C4 Hybrid 64D** (V1의 Proposed Model 격상)
  - 30주짜리 짧은 시계열·수만 점포 규모에서는 **딥러닝이 만능이 아님**. 데이터 길이·규모에 맞는 inductive bias(사람의 통계 지식 + 알고리즘 자동 추출)가 더 효율적
  - F1 0.548 → 0.639, AUC 0.736 → 0.824 (V1의 0.68→0.84와는 metric/표본/feature 정의 다름)

### V3 산물 — (b) 완전 새 차원 (paper로 분리 검토)

- **C1 Survivorship Bias**: 패널 내부 vs 외부 폐업률 **8.9% vs 48.3% → 5.4배** 격차
  - 우리가 지금까지 보고한 "Growth 41% / Stable 37% / Decline 22%"는 **이미 살아남을 확률이 5배 높은 집단**의 분포. 마라톤 완주자들의 분포였음
- **C5 EWS 인공물**: cost-sensitive threshold로 정책이 즉시 사용할 운영 임계치 산출 (최적 t = 0.10, max net utility 43,626)
  - 모델 = 단순 분류기가 아니라 **정책이 그대로 가져다 쓸 의사결정 도구**. "위험 점수 0.10 이상 점포를 우선 지원"이라는 운영 지침으로 변환됨

## 학위 논문 작성 진행

V3 본문 9개 챕터 중 핵심 5개 챕터 초고 완성 ([drafts/v3/](../drafts/v3/)). 진행 상태:

- **초록 (ch0)**: 국·영문 모두 작성, 6대 기여(C1~C6) 한 단락씩 + 키워드 + 목차 정렬
- **서론 (ch1)**: 연구 배경 + 기존 연구 4가지 한계(설문 기반 분류·단일 곡선 가정·생존 편향·진단/예측/의사결정 분절) + RQ1~RQ6 정리
- **이론적 배경 / 선행 연구 (ch2)**: 조직 생애주기 이론(Boulding·Adizes·Miller&Friesen), 소상공인 결정요인(국내외), 거래 데이터 연구, EWS·DSR·생존/인과 방법론까지 5절 구성, 6대 기여를 문헌 공백에 매핑
- **데이터 (ch3)**: KCD 패널 정의(59,089점포·142주), 두 실증 표본(post-entry / observed-window), 외부 공공데이터 5종, 표본 편향·결측 처리 규칙
- **방법론 (ch4)**: DSR build-evaluate 프레임으로 C1~C6 분석법 체계화 — Survivorship 정량화·KM/Cox PH·Volatility 4가설 분해·Granger+PSM-DiD+Panel FE·Hybrid 64D + EWS·LEVI + 외부 검증·Robustness

나머지 챕터(ch5 결과 / ch6 토의 / ch7 결론 / references)는 작성됐으나 본 미팅 정리 범위에서는 제외.

## 논의 사항 / 결정

- **학위 scope** — 옵션 A(V1 그대로) / **B(V2까지, 본인 추천)** / C(V3 전부) 중 선택
- **DSR 프레임 비중** — 한글 학위논문에서 DSR 명시 강도 (옵션 B 시 자연스럽게 약화)
- **C3 인과 주장 위상** — V3에서는 메인 기여, 옵션 B 시 paper로 이관
- **투고 전략** — HICSS 2027 (도메인·DSR fit ★★★★★, 마감 2026-06-15) 우선, 후속으로 Small Business Economics (도메인 fit 가장 정확) 저널 확장. ICIS 2026은 마감 임박 + IS theory framing 부담으로 제외
- **심사 일정** — 위원 구성·예심·본심 일정
- **Fig 5.2(C1 시각화)** 작성 여부

## 다음 단계

- 학위 scope 결정 후 본문 정합 작업 (옵션 B 시 V2 톤으로 일부 챕터 회귀, 약 1.5~2시간 추정)
- 영문 paper 분기 진행 (top_tier/paper_draft/) — HICSS 2027 → Small Business Economics 두 갈래
- 미해결: Fig 5.2, References BibTeX 변환
