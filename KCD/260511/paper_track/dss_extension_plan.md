# DSS Extension Plan — HICSS 통과 후 DSS journal submission

## 한 줄 목표

> HICSS 2027 proceedings 통과 후 6–9개월 안에 DSS (Decision Support Systems)
> journal 에 확장 paper 제출. EWS calibration + cost-sensitivity + field
> validation 1개를 핵심 추가 contribution 으로.

## DSS vs HICSS 차이

| 측면 | HICSS | DSS |
|---|---|---|
| Type | conference proceedings | journal IF≈7 |
| Length | 10 pages | 30+ pages |
| Review | 1 round, ~6 months | 2–3 rounds, 12+ months |
| Framing | benchmark + lit review | artifact + calibration + field |
| Theory | descriptive | design science framework |
| Audience | broad IS | decision-support specialists |

## DSS Submission timeline

| 시점 | 작업 |
|---|---|
| HICSS accept 통지 (2026-12) | DSS extension 시작 |
| 2027-01 (HICSS Hawaii event) | networking + reviewer feedback 수집 |
| 2027-02 ~ 04 (3개월) | EWS field validation 시나리오 + 정책 partner 1개 식별 |
| 2027-05 ~ 06 | DSS draft v1 (~25 pages) |
| 2027-07 ~ 08 | co-author review + revision |
| **2027-09 (target submit)** | DSS submission |
| 2027-10 ~ 2028-04 | review round 1, 2 |
| 2028-05+ | acceptance (목표) |

## 추가 contribution (HICSS 위에 더)

### (i) EWS as decision-support artifact

- HICSS 의 분석 2 (EWS calibration) 확장:
  - reliability diagram을 panels × seasons × cohorts 매트릭스로 확장
  - Platt scaling / isotonic regression 적용 비교
  - DCA (Decision Curve Analysis) 도입

### (ii) Cost-sensitivity 다각화

- HICSS 의 분석 3 (cost-sensitivity sweep) 확장:
  - SMB 정책 시나리오 3종 (lending, subsidy, intervention) 별 cost matrix
  - 한국 정부 통계 기반 dollar value calibration (e.g., 한국 폐업 손실 평균)
  - threshold 정책 권고 (top 10% targeted intervention 가설)

### (iii) Field validation (DSS 의 핵심 차별화)

- 정책 partner 1개 (예: 서울신용보증재단, KCD 자체) 와 협업 시나리오
- backtest: 2023년 데이터를 hold-out 으로 사용해 2024년 outcome 예측 시뮬레이션
- prospective deployment 1주 ~ 1개월 (가능 시)
- (대안) field validation 없으면 historical backtest + sensitivity analysis 만으로도 가능

### (iv) Design Science framework

- Hevner et al. (2004) "Design Science in IS Research" 프레임 적용
- artifact (EWS) × evaluation (calibration + cost) × communication
- managerial implications 강화

## DSS paper 구조 (30 pages)

| Section | Page | HICSS와의 차이 |
|---|---|---|
| 1. Introduction | 2 | 더 길게 — DSS 정책 배경 강조 |
| 2. Related Work | 4 | HICSS 70편 + EWS / artifact / calibration literature 추가 |
| 3. Problem Description | 2 | (신규) SMB EWS specific framing |
| 4. Method | 5 | HICSS Method + EWS calibration method |
| 5. Results — Benchmark | 5 | HICSS Results 압축 |
| 6. Results — EWS Artifact | 6 | (확장) calibration + cost + field validation |
| 7. Discussion + Design Implications | 3 | managerial / policy strong framing |
| 8. Conclusion + Future | 1 | (LEVI 도입 시) external validation 명시 |
| 9. References | 2 | 100+ |

## DSS 위험 / trade-off

| 위험 | 완화 |
|---|---|
| field validation 1개 구하기 어려움 | historical backtest 충분히 강화 + sensitivity analysis 풍부 |
| 정책 partner 협업 시간 부담 | 협업 못 구하면 simulation-based scenarios로 대체 |
| DSS review 12+ months | HICSS 통과로 visibility 확보 후 DSS 안정 진행 |
| HICSS reject 시 DSS 직행 | abstract + draft 가 더 강해야 함 — additional analyses 4개 모두 |

## DSS 이후 (참고)

- LEVI 외부 검증 통합 → Small Business Economics paper 가능
- I&M paper 는 managerial/strategic framing 강화
- ICIS / MISQ 는 IS theory layer 보강 후

## DSS submission 전 체크리스트

- [ ] HICSS proceedings publication 확인
- [ ] EWS calibration (분석 2) 결과 충분히 강한가
- [ ] Cost-sensitivity (분석 3) 정책 시나리오 3개 명확한가
- [ ] field validation 1개 또는 strong historical backtest 확보
- [ ] Design Science framework 명시
- [ ] managerial implications 단락 2–3 page
- [ ] 100+ references
