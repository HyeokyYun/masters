# Defense Q&A — 예상 질문 12개 + 정직한 답변

본 thesis 발표에서 받을 수 있는 핵심 질문과 정직한 답변 초안. 발표 1주 전
지도교수와 함께 다듬을 것.

---

### Q1. 주된 contribution이 정확히 무엇인가요?

**A.** Seasonal calendar alignment입니다. feature 윈도우와 target 윈도우를 동일
캘린더 월에 정렬해 seasonal confound를 제거하는 방법론입니다. 이전 분석(v4)에서
hybrid representation이 +0.05 macro_F1로 보였던 결과가 seasonal confound 때문
이었음을 정량으로 입증했고, alignment 후에는 hybrid 효과가 +0.0017로 축소됨을
14 panel에서 확인했습니다.

부수적으로 (a) LightGBM이 RF baseline 위에 +0.008 안정적 향상, (b) tenure
meta features가 +0.008 추가 향상을 conditional contribution으로 보고합니다.

### Q2. +0.008 macro_F1는 너무 작지 않나요?

**A.** 절대값은 작지만 세 가지 관점에서 의미 있습니다. 첫째, 14 panel 중
**일관된 방향성**입니다 — meta features 8 panels 중 3개 p<0.05, LightGBM 6
panels 중 5개 wins/2 p<0.05. random fluctuation이 아닙니다.

둘째, **stock literature의 14종 SOTA가 모두 RF에 −0.139 ~ −0.270 macro_F1로
패배**한다는 baseline에서의 +0.008은 (상대적으로) 의미 있는 향상입니다.

세째 (**핵심**), per-cohort 분해 결과 +0.008은 **sub-population별 효과를 가린
평균**입니다 (`lgbm_per_cohort_summary.csv`):

- **Q4_long (업력 9년+) tenure cohort: Δ = +0.019** (전체의 2.4×)
- **fragile cluster 3 (Decline 17%): Δ = +0.044** (5.5×)
- **cluster 1, 5: 각 +0.041, +0.036**
- tenure quartile 단조 증가: Q1=+0.002 → Q4=+0.019

미팅 피드백 "업력이 상승에 유의미" 가 모델 향상에도 그대로 적용됨을 정량 확인.

### Q3. Cluster 분석은 결국 어떻게 사용되었나요?

**A.** 미팅 피드백 ("클러스터링이 무의미해지면 안 됨") 에 따라 cluster를
**G/S/D 이질성을 드러내는 도구**로 재의미화했습니다. cluster 3 (fragile)은
Decline 36%, cluster 1 (안정)은 Decline 7% — 7 panel 모두에서 일관됨.

cluster를 예측 목표로 쓰지 않고 (정확도 낮음), G/S/D 분류의 **이질성 진단
도구**로 사용 → 정책적 함의 (fragile cluster 타겟 지원) 도출.

### Q4. 왜 LSTM/Transformer가 RF를 못 이겼나요?

**A.** Ch6 mechanism 가설 4가지:
1. **Short window** (13–31주) — Transformer self-attention의 sweet spot 밖
2. **6채널 multivariate** — 56개 통계 피처가 channel-aware 압축으로 raw 시계열 정보 거의 다 포착
3. **Regression-trained models** — forecast → slope → bucket 변환에서 정보 손실
4. **Calendar season confound** — RF + alignment가 이미 잡음

stock literature와 다른 SMB-specific 조건입니다.

### Q5. Foundation models (TimesFM, Chronos)가 왜 그렇게 약했나요?

**A.** zero-shot 결과로 Chronos-Bolt F1=0.289, TimesFM-200m F1=0.230 — random
guessing(F1≈0.33)에 가깝거나 그 이하. 주요 원인은:

1. pretrain 도메인 mismatch — utility/retail daily 데이터로 학습, SMB 주간 매출의 zero-inflated/intermittent와 거리
2. 13–31주 context가 foundation models의 일반 가정(200+ context)에 부족
3. forecast → slope → ±0.5σ bucket 변환에서 forecast 노이즈 amplification

LoRA finetune이 RF에 도달할 가능성은 낮다고 판단해 paper-track의 future work으로 명시.

### Q6. v4의 D ≫ A 결과는 어떻게 된 건가요?

**A.** v4에서 보였던 hybrid representation의 +0.05 macro_F1 우위는 **seasonal
confound의 artifact**였습니다. v4에서는 feature 윈도우와 target 윈도우의
캘린더 월이 다를 수 있었고, 이 경우 같은 점포가 panel에 따라 다른 G/S/D 라벨을 받음.

v5에서 캘린더 정렬 후 14 panel 재집계 시 +0.0017로 축소. 이는 v4 결과를
부정하는 게 아니라 **새로운 mechanism (seasonal confound)** 을 발견했음을 의미하며,
v5 main contribution의 정당성을 강화합니다.

### Q7. GNN이 안 통한다는 건 어떻게 해석해야 하나요?

**A.** dong/industry/hybrid 3종 spatial GCN 모두 baseline MLP보다 macro_F1 감소
(−0.027 ~ −0.085). 본 데이터에서 "같은 동네 다른 점포의 매출 dynamics가 본
점포에 영향을 준다" 가설은 약함.

해석:
1. 56-피처 통계가 이미 store-specific하게 강함 → graph aggregation의 추가 정보 마이너스
2. GAT (attention 기반) 또는 더 좁은 그래프 (같은 골목 + 같은 업종)로 다시 시도 가능 — future work
3. stock 문헌에서 inter-stock correlation은 효과적이지만 SMB는 그렇지 않음 — 또 다른 SMB-specific 차이

### Q8. 데이터 출처와 ethics는?

**A.** 서울 KCD card transaction (2021–2023), 59,089 stores, 6.5M weekly
records. 개인 식별 정보 제거된 store-level aggregate. 본 thesis 분석은
descriptive/predictive로 한정, 개별 점포 closure decision에 사용되지 않음.
정책 implication도 cluster-level (anonymous group) 으로 한정.

### Q9. Generalizability는 어떻게 보장되나요?

**A.** 14 panel × 3-fold CV로 sample-level / panel-level 안정성을 모두 확인.
seasonal panel 분리로 같은 시즌 다른 연도 비교 (sm01_2021 vs sm01_2022) 도
포함 — temporal generalization 일부 입증.

한계: 서울 단일 도시. future work으로 다른 도시 transfer 명시.

### Q10. Causal inference는 안 했나요?

**A.** 안 했습니다. 본 thesis는 **descriptive + predictive** 로 명시 한정.
SHAP feature importance는 모델 내 contribution이며 causal effect로 해석하지
않습니다. tenure cohort × new-customer-slope effect도 logistic 회귀 coefficient
로 보고 (correlational).

paper-track에서 LEVI/EWS 확장 시 instrumental variables 또는 quasi-experiment
도입 가능성을 future work으로 표시.

### Q11. 코드/데이터 재현 가능한가요?

**A.** 네, 두 단계:
- 본 thesis는 `260511/` 및 `260511/phase5_external/` 전체 코드 + outputs/tables/* CSV 제공
- 환경: `phase5_external/envs/phase5_sm61.yml` (torch 2.3.1+cu118, sm_61 GPU 호환)
- 재실행 명령: `phase5_external/README.md` 의 "재실행" 섹션
- GitHub repo: `git@github.com:HyeokyYun/masters.git` 의 `KCD/260511/`

step06의 RF baseline F1 = 0.49020498 (3-fold)을 1e-6 이내 재현 검증 완료.

### Q12. 그래서 다음은 paper인가요? 어떤 venue?

**A.** 1순위는 **HICSS** (decision analytics, public-value analytics track).
Phase 5 14-model benchmark + 70편 lit review가 그대로 paper 절반. 6-9개월.

2순위는 **DSS** (Decision Support Systems) — EWS calibration + cost-sensitivity
보강 필요. 12-18개월.

전략: HICSS 우선 + 본 thesis 졸업 → HICSS 통과 시 DSS로 확장.

---

## 발표 1주 전 체크리스트

- [ ] 위 12개 답변 5분 안에 말할 수 있게 연습
- [ ] 슬라이드에서 "+0.008", "+0.0017", "−0.139", "−0.270" 핵심 수치 위치 확인
- [ ] Phase 5 figure 2장이 슬라이드에 들어가 있는지 확인
- [ ] mechanism 4가지 (Q4 답) 한 슬라이드에 정리되어 있는지 확인
- [ ] 지도교수와 mock defense 1회 (Q4, Q6, Q10 집중 확인)
