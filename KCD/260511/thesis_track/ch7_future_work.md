# Ch7 Future Work — 추가 항목

본 thesis가 닫지 못한 questions를 정직히 명시하고, paper-track에서 다룰 항목을
표시한다. paper-track의 후속 작업을 thesis 본문에서 "future work"으로 미리
선언하면, defense 시 "왜 paper가 따로 필요한가" 답변이 자연스러워진다.

## §7.1 Phase 5 미시도 / 보강 항목

### 7.1.1 Per-cohort LightGBM Δ 분해

- 현재 LGBM Δ = +0.008 macro_F1는 6 panel 평균. cohort/cluster별 분해 미수행.
- 가설: Q4_long(업력 9년+) tenure cohort 또는 fragile cluster(cluster 3) 에서
  Δ가 +0.020 이상일 가능성 — 작은 평균이 큰 sub-population 효과를 가릴 수 있음.
- 측정 방법: `260511/phase5_external/src/s5d_weighting/run_weighting.py` 를 cohort
  필터 추가 버전으로 재실행.
- **paper-track에서 우선 수행 권장**.

### 7.1.2 Chronos LoRA finetune

- Phase 5에서 zero-shot 결과(F1=0.289)가 너무 약해 finetune 생략.
- LoRA로 SMB 데이터 30K store에 finetune 시 RF 근접 가능성은 낮지만 실험적 가치 있음.
- 측정 방법: `260511/phase5_external/src/s5a_foundation/finetune_chronos_lora.py` (스크립트 placeholder만 존재).
- thesis 본문에는 "시도하지 않음 (zero-shot 결과로 정황 명확)" 한 줄로 기록.

### 7.1.3 Synthetic long-history ablation

- "단지 short window이 원인인가?" 분리 실험.
- raw weekly에서 4년 연속 history가 있는 stores subset 추출 → 같은 stock SOTA
  돌려 보기 → window length × model 결과 매트릭스.
- thesis 본문 §6.x.1(a) mechanism 가설 (a) 입증 가능.

### 7.1.4 Multivariate ROCKET / MiniRocket

- Phase 5 5C/5B에서 미시도. ROCKET 변형은 multivariate 6채널을 지원.
- 56-피처 통계 vs ROCKET 10K random kernel의 직접 비교 가능.

## §7.2 LEVI · EWS 외부 검증

본 thesis에 포함하지 않은 future-work 영역. paper-track의 DSS/SBE 방향으로 확장 가능.

- **LEVI** (Local Economic Vitality Index): living-population, permit closure rate
  등 외부 공공 데이터로 construct 검증. v4 단계에서 부분 완료, v5는 봉인.
- **EWS** (Early Warning System): LightGBM proba → 의사결정 deciles + 비용 sensitivity 표.
  Phase 5 5D LightGBM이 baseline으로 적합.
- **Survival analysis 통합**: business closure event를 SMB lifecycle 마지막 단계로 모델링.

## §7.3 정책 implication 강화

본 thesis는 "fragile cluster" 식별만 제시. 정책 권고는 conservative.

- per-cluster intervention cost-benefit 모델.
- decile-based targeting (top 10% Decline risk 점포 대상 지원).
- 이는 paper-track DSS submission의 핵심 보강 영역.

## §7.4 GNN 변형 — GAT, 작은 attention 그래프

본 thesis Phase 3 spatial GCN negative. 다음 시도 가능:

- GAT (Graph Attention Network) — edge attention 학습.
- 작은 노드 피처(cust_slope만) + 좁은 그래프(같은 골목+업종) — Phase 3 hybrid가 가장
  덜 나빴던 점을 더 좁혀.
- 본 thesis 본문에서는 "future work" 단락에 한 문장만.

## §7.5 다른 도시 / 국가 transfer

- 본 데이터: 서울 KCD card transaction.
- 부산/대구 등 다른 도시 데이터 transfer 가능성 (계절 패턴 다름).
- 일본/대만 등 유사 small-business 시장 transfer (regulatory 다름).

## 본 chapter의 한 줄 결론

> 본 thesis는 SMB 단기 매출 lifecycle classification의 차별화 mechanism 4가지를
> 정량 입증한다. paper-track에서는 (1) per-cohort LightGBM Δ 분해 (2) EWS
> calibration 보강 (3) synthetic long-history ablation (4) LEVI 외부 검증
> 4가지를 통해 본 thesis의 contribution을 정책/이론 차원으로 확장한다.
