# Open Questions — 교수 미팅에서 결정 필요 항목

**작성일**: 2026-04-21 | **지도교수**: 김지희 교수

---

## Q1. Target Venue

- [ ] ICIS 2026 (5/1 마감, D-10) — **옵션 A**
- [ ] HICSS 2027 (6월 중순 마감 예상, D-55) — **옵션 B**
- [ ] ICIS 우선 시도 → 실패 시 HICSS — **옵션 C**
- [ ] Other (저널 직행 등):

**교수 판단 필요 포인트**:
- 교수님 schedule 상 10일 내 2회 리뷰(4/26, 4/29) 가능한가?
- ICIS 실패 시 1년 공백의 기회비용 vs HICSS 확실성

---

## Q2. Authorship

- **제1저자**: (학생 본인)
- **교신저자**: 김지희 교수님으로 확정?
- **공저자 추가 필요**: KCD 담당자 / 타 연구실 협력자 포함 여부?

---

## Q3. KCD Data Publication Permission

- 출판·공개용 데이터 사용에 대해 KCD 측 사전 허가 확보되어 있는가?
- Data Agreement 문구에 학회 투고가 포함되어 있는지 확인 필요
- Data availability statement에 넣을 조건 (예: "available upon request with KCD approval")?

---

## Q4. 이론 프레이밍 방향

아래 중 어느 관점으로 theoretical contribution을 걸까?

- [ ] **(a) Entrepreneurship / SME lifecycle** — Shane, Shepherd 계열. 전통적 "survival" 이론의 한계 지적.
- [ ] **(b) Design Science Research** — Hevner 2004. EWS artifact 중심. DSR의 evaluation rigor 강조.
- [ ] **(c) IS for social good / policy informatics** — 정책 의사결정 지원, 사회적 영향.
- [ ] **(d) Methodological innovation** — Hybrid clustering × change-point representation의 일반화 주장.

**권장**: (b) DSR + (a) lifecycle 혼합 — HICSS/ICIS 모두에 안전한 조합.

---

## Q5. Self-plagiarism & Prior Work

- 이전 경로 (`260321_codex/`, `260326_fullsample/`, etc.) 결과물이 다음에 쓰였는가?
  - [ ] 이전 학회 발표 (국내·국외)
  - [ ] 워킹페이퍼·preprint
  - [ ] 학위 논문 구성물
  - [ ] 산학 보고서
- 재사용 정도에 따라 "incremental contribution" 프레이밍 필요

---

## Q6. 실증 추가 작업 필요 여부

현재 step01-13 완료. 아래 중 교수님이 추가 요구하는 것?

- [ ] **업종별 확장**: 음식점 외 (소매·서비스) 데이터로 generalizability 검증
- [ ] **Temporal 확장**: 2019-2020 (코로나 이전) 데이터 접근 가능?
- [ ] **파일럿 배포**: KCD 앱 등에 EWS 실제 탑재 사례 확보?
- [ ] **User study**: 소상공인 20-30명 대상 risk score 활용성 설문?
- [ ] **Instrumental variable**: causal 식별 강화?
- [ ] **현재로 충분 — 논문 작성에 집중**

---

## Q7. 작성 분담 및 리뷰 일정

**10일(ICIS) 시나리오**:
- 4/22-25: 학생 본문 drafting (LLM 병행)
- 4/26: 교수 1차 리뷰 — **확보 가능한가?**
- 4/27-28: 피드백 반영
- 4/29: 교수 2차 리뷰 — **확보 가능한가?**
- 4/30: 최종 polish
- 5/1: 제출

**55일(HICSS) 시나리오**:
- 4/22 ~ 5/10: 학생 전체 본문 drafting
- 5/11: 교수 1차 리뷰
- 5/12 ~ 5/25: major revision
- 5/26: 교수 2차 리뷰
- 5/27 ~ 6/10: minor revision + polish
- 6/11 ~ 6/14: submission prep

---

## Q8. Figure/Table 완성도 목표

현재 생성 완료: fig2-13 (12개), 테이블 15개. 교수님이 추가/수정 요구하는 figure?

- [ ] Conceptual framework diagram (Fig 1) — 아직 없음. **제작 필요**
- [ ] Event study plot (Golden Cross 전후 +/- 10주 average) — Fig 4로 있으나 강화?
- [ ] SHAP interaction plot — 아직 없음. 필요시 추가 가능
- [ ] EWS dashboard mockup — DSR artifact 강조 시 유용

---

## Q9. Submission 대상 저널 장기 전략

- **DSS (Decision Support Systems)** — impact factor 7.5, acceptance ~15%, 확장판 2027년 목표?
- **IS Research** — 가능하나 bar 높음
- **ECRA (Electronic Commerce Research and Applications)** — 안전한 대안
- **IEEE Intelligent Systems** — artifact 중심 가능
- **ISF (Information Systems Frontiers)** — SMB applied research 우호적

**권장**: DSS 주, ISF 예비.

---

## Q10. 다음 미팅 일정

- 이번 미팅 결론 정리 시점: __________
- 차기 리뷰 미팅 시점: __________

---

# 미팅 전 교수님께 보낼 권장 자료 패키지

1. `01_executive_briefing.md` (5분 read — 6 findings 요약)
2. `02_venue_decision_memo.md` (5분 read — venue comparison)
3. `03_paper_skeleton.md` (10분 read — 논문 구조)
4. `04_open_questions.md` (이 문서)
5. `top_tier/outputs/docs/top_tier_report.md` (참조용 detail — 필요 시)
6. **핵심 수치 cheat sheet** (옵션):
   - Proposed D F1 0.648 / AUC 0.830
   - DL best F1 0.517 / AUC 0.709
   - DiD ATT +0.117 (p<10⁻⁷²)
   - Survivorship 9.6% vs 51.8%
   - EWS AP Decline 0.699 (3.1× baseline)
