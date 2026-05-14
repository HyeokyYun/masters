# 의사결정 항목 — 2026-05-14 advisor 미팅

본 메모는 미팅에서 다음 세 가지 의사결정을 받고자 함을 정리한다.
각 항목은 (현재 안 / 대안 / 권고 / 영향 받는 본문 절) 4 묶음으로 구성.

---

## D1. Prediction-first framing 의 적절성

### 배경
- 2026-04-30 advisor 미팅에서 "원래 목적은 예측", "신규 유입·업력이 주요 요인",
  "예측 모델을 기본 말고 더 강화", "주식 예측 literature 와의 관련성 검토" 등의
  발언이 prediction-oriented framing 을 가리킴.
- 2026-05-13 본 학생의 점검에서 final_thesis 가 seasonal alignment 를 main
  methodology 로 설정해 prediction 목적에서 벗어났음을 확인 → prediction-first
  framing 으로 ch1·ch4·ch5·ch6·ch7·ch0 전체 재구성.

### 현재 안
**상위 RQ**: "초기 1–7개월 거래 패턴으로 G/S/D 를 얼마나 잘 예측할 수 있고,
어떤 요인·표현·모델이 그 예측을 개선시키는가."

**3 본문 contribution**:
1. Prediction baseline 과 요인 분해 (cohort × G/S/D, cluster × G/S/D)
2. Seasonal alignment label robustness 전제
3. 세 갈래 improvement (hybrid / cost-sensitive / 외부 SOTA 14 종)

### 대안
- **대안 A**: v5_thesis_final 의 seasonal-main 으로 복귀 (methodological focus).
  주된 장점은 "단일 main contribution" 의 명확성, 단점은 advisor 미팅 발언
  과의 거리.
- **대안 B**: dual lens (prediction lens + methodology lens 둘 다 main).
  ch1 에서 두 lens 의 trade-off 를 명시. 장점은 어느 쪽에서 보아도 안전,
  단점은 응집력 약화.

### 권고 (학생)
**현재 안 유지** — advisor 미팅 발언과 정합. 단, 본문 §1.2.2 와 §6.4
한계 절에서 "seasonal alignment 가 prediction 의 sub-component 라도,
구조적으로는 본 학위논문의 가장 정량적·재현 가능한 기여" 임을 분명히 명시.

### 영향 받는 본문 절
- ch1 §1.2 ~ §1.4 (RQ·contribution)
- ch7 §7.1 (결론 contribution mirror)
- ch0_abstract (한·영 초록 키워드)

---

## D2. Hybrid representation 결론의 톤

### 배경
- §5.5 의 14 panel 평균 ΔF1 = +0.0017. 5% 유의 1/14 (`sy2021_sm01_w7m_off1`,
  p=0.0073), Bonferroni 후 0/14.
- 윈도우 길이별: 3m +0.0019, 4m +0.0010, 6m +0.0001, 7m +0.0030.
- 즉 7 개월 윈도우의 라벨 편중 panel 에서만 효과가 살아남고, 6 개월에서는
  사실상 0.

### 현재 안
"조건부 contribution" — 라벨 / 시즌 / 윈도우 분포에 의존하는 modest 한 발견.

### 대안
- **대안 A (강화)**: "입증적 한계" 로 톤 강화. 즉 hybrid representation 이
  baseline 통계 피처 위에서 통계적으로 의미 있는 향상을 주지 않으며, 이는
  기존 D ≫ A 결론이 시즌 confound 의 artifact 였음을 확정한다는 negative
  finding 으로 격상.
- **대안 B (제거)**: hybrid 자체를 본문 contribution 에서 빼고 §6.5 future
  work 로 미룸. 즉 본문 main 은 (1) prediction baseline + 요인 분해 + (2)
  seasonal alignment 로 줄임.

### 권고 (학생)
**대안 A (강화) 검토 권고**. 현재 안의 "조건우 contribution" 톤보다,
"동일 데이터·동일 모델에서 representation 선택만으로 결론을 바꿀 수 없음"
의 negative finding 이 seasonal alignment contribution (기여 2) 의 정당화
근거로 더 직접적. 단, advisor 가 v5 의 D2 결정 ("조건부 contribution
유지") 을 명시했다면 현재 안을 유지.

### 영향 받는 본문 절
- ch5 §5.5 (수치는 그대로, 해석 톤만 조정)
- ch6 §6.1.2 + §6.2.2 (학문적 의의 절)
- ch1 §1.4 contribution 3-(a) (수치 그대로, 표현 조정)

---

## D3. GNN 본격 확장 일정

### 배경
- 2026-04-30 미팅 발언 "예를 들면 네트워크 모델 추가 (GNN 등)".
- `260430_claude/outputs/tables/gnn_compare.csv` 에 pilot 결과 존재 (3 panel
  × 4 graph definition × 2 model). 핵심 발견: GCN 은 MLP / RF 대비 모두
  패배 (Δ ≈ −0.04 ~ −0.10), hybrid_dong_industry 그래프가 가장 강함
  (Δ 작음).
- 현재 본문은 §6.5 / §7.2 의 future work 1 문단으로만 다룸.

### 옵션
- **옵션 A**: 본 학위논문 본문 §5.6 또는 별도 §5.11 에 GNN pilot 결과를
  외부 SOTA 14 종과 같은 위치에서 보고. 추가 작업: 3 panel → 6 panel
  확장 + paired t-test 표 + figure. 시간: 2–3 일.
- **옵션 B**: 본 학위논문에서는 §6.5 future work 1 문단만 유지. 본격
  GNN 확장 (heterogeneous GNN, spatial-temporal, GAT 등 grid) 은
  paper-track 으로 분리. 시간: 1–2 개월 (졸업 후).
- **옵션 C**: 학위논문 본문에서 GNN 언급을 완전 제거. paper-track 별
  도 라인.

### 권고 (학생)
**옵션 B** — 학위논문은 정직한 pilot finding (GCN ≤ MLP / RF) 으로
short future-work 단락만 유지하고, 본격 확장은 졸업 후 paper-track 으로
분리. 이유는 (a) GCN 의 RF 패배가 4 mechanism 가설 (§6.2.4) 의 한 case
study 로 적합, (b) 본격 GNN grid 는 그래프 정의 자체에 또 다른 design
choice 가 다수 → 학위논문 본문이 산만해질 위험.

### 영향 받는 본문 절
- ch6 §6.5 (future work 1 문단 위치, 옵션 B 시 변동 없음)
- ch7 §7.2 (future work 4 항목 중 GNN 부분, 옵션 B 시 변동 없음)
- 옵션 A 채택 시 ch5 신설 §5.11 + 표 1 + figure 1.

---

## 미팅 후 후속 작업

(D1, D2, D3 결정에 따라 ch1·ch5·ch6·ch7 본문 표현 일부 조정.)
- D1 = 현재 안 유지: 추가 작업 없음 (학생 권고 채택 시).
- D2 = 대안 A 채택: ch5 §5.5, ch6 §6.1.2/§6.2.2, ch1 §1.4 표현 보정 (반나절).
- D3 = 옵션 B 유지: 추가 작업 없음 (학생 권고 채택 시).
- D3 = 옵션 A 채택: GNN 6 panel 확장 (2–3 일).

추가로 advisor 요청 시:
- repeated CV (10-fold × 10 repeats) — 1 일 (`step05` 의 fold 매개변수만 조정).
- 학위논문 영문 제목 후보 3–5 개 — 학생이 작성해 advisor 검토.
