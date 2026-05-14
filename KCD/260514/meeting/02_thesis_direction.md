# 02. 학위논문의 방향성

> **활성 본문**: `/home/hyeoky98/kcd/final_thesis/thesis/` (ch0 ~ ch7 + references).
> **수치 원천**: `260430_claude/outputs/tables/`, `260511/phase5_external/outputs/tables/`.
> **이전 버전과의 관계**: v5_thesis_final (seasonal-main) 의 framing 을
> prediction-first 로 재정렬한 결과. v1 ~ v4 / v5 는 이력 보존, 본문은
> `final_thesis/`.

---

## 1. 상위 RQ (Research Question)

> "초기 1–7 개월 거래 패턴으로 G/S/D (Growth / Stable / Decline) 를 얼마나
> 잘 예측할 수 있고, 어떤 **요인·표현·모델** 이 그 예측을 개선시키는가."

본 RQ 는 2026-04-30 advisor 발언 ("원래 목적은 예측", "신규 유입·업력 = 주요
요인", "예측 모델 강화", "주식 예측 literature 대조") 과 정합하도록 설정.

---

## 2. 본문 3 contribution

`final_thesis/thesis/ch1_introduction.md §1.4` 기반.

| # | Contribution | 핵심 수치 | 본문 절 | 한계 |
| --- | --- | --- | --- | --- |
| **C1** | **Prediction baseline + 요인 분해** | baseline macro-F1 0.43 ~ 0.55 (145 spec). Q1_short → Q4_long ΔF1 +0.0021 → **+0.019**. fragile cluster ΔF1 **+0.044**. | §5.2 ~ §5.5 + §5.7 (cohort) + §5.8 (cluster) | logit β 는 관찰적·인과 아님. k=6 단일. |
| **C2** | **Seasonal calendar alignment 의 label robustness 전제** | 시작월 진폭 **0.10** ≫ 윈도우 길이 0.02–0.04 ≫ 시작연도 < 0.01 (145 spec) | §5.2 ~ §5.4 | 외식업 한정. cash 결제 누락. 2y 컷오프. |
| **C3** | **세 갈래 prediction-improvement 시도 + SMB-specific 차별화** | (a) hybrid +0.0017 (Bonferroni 후 0/14); (b) cost-sens. RF Δ −0.035 ~ −0.063; (c) 외부 SOTA 14 중 LGB 1 종만 RF 능가 (+0.0075). 4 mechanism 가설. | §5.5 + §5.6 + §5.9 | seed=42 단일. SOTA grid 미수행. 4 가설은 가설 단계. |

(상세 표: `260514/tables/three_contributions.md`, 다이어그램: `260514/figures/fig01_three_contributions.png`)

---

## 3. 본문 구조 (ch0 ~ ch7)

`final_thesis/thesis/` 의 9 챕터:

```
ch0_abstract.md          한 485/500 자 + 영 290/300 단어
ch1_introduction.md      §1.1 motivation, §1.2 background, §1.3 RQ, §1.4 contribution
ch2_literature.md        70 편 lit review (5 영역 매트릭스)
ch3_data.md              KCD weekly + meta, 59,089 store, 2021–2023
ch4_methodology.md       seasonal panel, label, feature, 5-fold CV
ch5_results.md           §5.1 ~ §5.10 (3 contribution + cohort + cluster + cost-sens. + 요약)
ch6_discussion.md        §6.1 implication, §6.2 mechanism, §6.5 future work
ch7_conclusion.md        §7.1 contribution mirror, §7.2 future work
references.md
```

**front_matter** (`final_thesis/front_matter/`): 04 학위명·05 본문 쪽수
미정 (학과 행정실 확인 + 조판 후 채움).

---

## 4. 의사결정 항목 (D1 / D2 / D3)

본 미팅에서 advisor 결정을 요청. 상세 옵션은
`260514/decisions/decisions_to_discuss.md`.

| # | 항목 | 학생 권고 |
| --- | --- | --- |
| **D1** | Prediction-first framing 적절성 | **현재 안 유지** (advisor 4/30 발언과 정합). 단 §1.2.2 / §6.4 에서 "seasonal alignment 는 prediction 의 sub-component 라도 정량적·재현 가능한 기여" 임을 명시. |
| **D2** | Hybrid representation 결론 톤 | **대안 A 검토** — "조건부 contribution" 에서 "입증적 한계" (negative finding) 로 강화. C2 (seasonal alignment) 의 정당화 근거로 더 직접적. advisor 의 v5 D2 결정 ("조건부 유지") 이 명시되어 있다면 현재 안 유지. |
| **D3** | GNN 본격 확장 일정 | **옵션 B** — 학위논문 본문은 §6.5 future-work 1 문단 유지, 본격 확장 (heterogeneous / GAT / spatial-temporal grid) 은 paper-track 으로 분리 (졸업 후 1–2 개월). |

---

## 5. Hybrid representation 의 좌천 (v5 → final_thesis)

이전 결론 ("D ≫ A 0.05 macro-F1") 을 **seasonal confound artifact** 로
재해석. 14 panel 갱신 결과:

- 평균 ΔF1 = **+0.0017** (3m 평균 +0.0019, 4m +0.0010, 6m +0.0001, 7m +0.0030).
- 5% 유의 1/14 (`sy2021_sm01_w7m_off1`, p=0.0073), Bonferroni 후 **0/14**.
- 즉 7 개월 윈도우의 라벨 편중 panel 에서만 잔존, 6 개월에서는 사실상 0.

이를 C3 의 (a) 로 격하하고, "조건부 contribution" (현재) 또는 "입증적 한계
= negative finding" (대안 A, 권고) 으로 톤 결정.

---

## 6. LEVI / EWS / 외부 공공 데이터의 위치

학위논문 본문이 아닌 future work 로 분리:

- **LEVI** (local economic vitality index): §6.5 / §7.2 future work 1 문단.
  메인 contribution 으로 복귀시키지 않음 (2026-04-30 미팅 결정).
- **EWS** (early warning system): §6.5 / §7.2 future work. DSS submission
  단계 (2027 Q2) 의 핵심 contribution 으로 분리.
- **외부 공공 데이터** (소상공인 폐업율, 거주인구): §6.5 / §7.2.
- **Golden Cross / 시즌 정렬 재검증**: §6.5.

---

## 7. 남은 학생 작업

1. **한·영 논문 제목 후보 3–5 개 작성** — prediction-first framing 위.
   advisor 미팅에서 후보를 받고 검토 요청.
2. **학위명 영문 확정** — KAIST 기술경영학부 (BTM, 석사) 행정실 확인.
   front_matter 04 표지·서지 영문명 = **"School of Business and Technology
   Management (BTM)"** 고정 (memory: user_affiliation).
3. **심사일 / 심사위원 / 심사 통과일** — advisor 와 일정 협의.
4. **본문·서문 쪽 수** — 조판 후 front_matter 05 기재.
5. **(advisor 요청 시) repeated CV (10-fold × 10 repeats)** — 1 일.
6. **(D 결정 후 본문 보정)**:
   - D2 = 대안 A → ch5 §5.5, ch6 §6.1.2 / §6.2.2, ch1 §1.4 표현 보정 (반나절).
   - D3 = 옵션 A → ch5 신설 §5.11 + 표 + figure (2–3 일).

---

## 8. 한 줄 요약

> 학위논문은 **prediction-first framing 위에 3 contribution** (C1 요인 분해,
> C2 seasonal alignment, C3 세 갈래 improvement + 4 mechanism) 으로 정렬.
> Hybrid representation 은 14 panel ΔF1 +0.0017 (Bonferroni 후 0/14) 로
> "조건부" → "입증적 한계" 로 톤 강화 검토. LEVI / EWS / 본격 GNN 은 future
> work 로 분리.
