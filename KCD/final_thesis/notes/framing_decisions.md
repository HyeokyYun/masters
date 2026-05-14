# Framing Decisions — KCD 석사학위논문 final_thesis

본 문서는 본 논문 작성의 모든 챕터가 일관되게 따라야 할 **framing
결정**을 한 곳에 모은다. 결정의 근거(미팅 / 산출물 / 제출요령)도 함께
명시한다. 챕터를 쓰다가 톤이 흔들릴 때 이 문서를 먼저 다시 읽는다.

## D1. Framing = Prediction-first (재정의, 2026-05-13)

- **결정**: 본 논문의 상위 RQ 는 "초기 거래 패턴으로 G/S/D 를 얼마나
  잘 예측할 수 있고, 어떤 요인·표현·모델이 그 예측을 개선시키는가"
  의 prediction-first 질문이다. 시즌 정렬·hybrid·외부 SOTA·cost-
  sensitive 는 모두 이 상위 prediction 질문의 sub-component 다.
- **근거**: 2026-04-30 지도교수 개인 미팅
  (`260430_claude/meeting/07_meeting_feedback.md`) — "원래 목적은
  예측", "어떤 애들이 상승/유지/하락 인지 요인을 파악", "신규 유입·
  업력이 주요 요인", "technical novelty / 주식 예측 literature 비교".
  최초 final_thesis 가 seasonal alignment 를 main methodology 로
  설정한 것은 prediction 목적에서 멀어진 framing 이었음을 2026-05-13
  대화에서 확인 후 재정의.
- **본문 contribution 3 개**:
  1. Prediction baseline 과 요인 분해 (cohort × G/S/D, cluster ×
     G/S/D, cohort 별 신규고객 logit) — §5.7 ~ §5.8.
  2. Seasonal alignment label robustness 전제 — §5.2 ~ §5.4.
  3. 세 갈래 prediction-improvement 시도와 SMB-specific 차별화
     (hybrid / cost-sensitive / 외부 SOTA 14 종) — §5.5, §5.9, §5.6.
- **챕터 적용**: ch1 §1.2 ~ §1.4 / ch4 §4.9 ~ §4.10 / ch5 §5.6 ~
  §5.10 / ch6 §6.1.6 ~ §6.1.7 + §6.2.5 / ch7 §7.1 에서 prediction-
  first 위계 일관 유지.

## D2. Hybrid representation = 조건부 발견 (3 개 개선 시도 중 1 개)

- **결정**: cluster + change-point 추가가 macro-F1 을 향상시킨다는
  주장은 **조건부**로만 한다. 시즌 정렬된 14 panel 평균 ΔF1 = +0.0017,
  1 / 14 panel 만 p<0.05 (Bonferroni 보정 후 0/14).
- **근거**: `260430_claude/outputs/tables/main_model_compare.csv`,
  `main_model_paired_AvD.csv`.
- **금지 표현**: "신호 유지", "robustness evidence", "hybrid
  representation 의 개선이 시즌 정렬 후에도 살아남는다" 류 v4 톤.
- **허용 표현**: "라벨 분포가 편중된 일부 시즌에서만 통계적으로
  유의했다", "윈도우 길이·시즌에 따라 결과가 갈리는 조건부 발견",
  "예측 개선 세 갈래 (representation / weighting / model) 중
  representation 측 결과".
- **챕터 적용**: ch5 §5.5 / ch6 §6.1.2 / §6.2.2 에서 본 톤 강제.

## D3. LEVI / EWS / GNN / Golden Cross / 외부 공공 데이터 = future work

- **결정**: 본문 contribution 이 아니라 **ch6.5 / ch7** 의 future work
  에서 각각 1–2 문단으로만 다룬다. GNN (네트워크 모델) 도 본 목록에
  포함 (gnn_compare.csv 의 pilot 결과만 ch6.5 에 짧게 인용).
- **근거**: 2026-04-30 미팅 결정 + CLAUDE.md "LEVI And EWS Framing".
- **금지**: 본문 §1, §4, §5 에서 LEVI/EWS/GNN 을 contribution 으로
  끌어 올리지 말 것. 산출물 (`top_tier/outputs/`) 의 LEVI 외부 검증
  결과는 ch6.5 의 future work 단락에서 짧게만 인용.

## D7. Cohort/cluster 요인 분해 = 본문 §5.7 ~ §5.8 신설 (2026-05-13)

- **결정**: 업력 4분위 cohort × G/S/D 와 KMeans 6 cluster × G/S/D 의
  요인 분해를 본문 §5.7 ~ §5.8 에서 정량 보고한다. 본 절은 D1 의
  contribution 1 (prediction baseline 과 요인 분해) 의 핵심 근거다.
- **근거**: 2026-04-30 미팅 "신규 유입·업력이 주요 요인 (상승에 유
  의미)", "어떤 애들이 상승/유지/하락 인지 요인을 파악".
- **데이터**: `260430_claude/outputs/tables/age_cohort_nc_effect.csv`,
  `cluster_outcome_summary.csv`, `cluster_outcome_xtab.csv`,
  `per_cluster_feature_importance.csv`,
  `260511/phase5_external/outputs/tables/lgbm_per_cohort_summary.csv`.
- **금지**: cohort/cluster 결과를 prediction 본문에서 빼고 future
  work 로 미루는 것 (이전 v5_thesis_final → final_thesis 전환 때
  발생한 오류).

## D8. Prediction-improvement 세 갈래 = 본문 §5.5, §5.9, §5.6 (2026-05-13)

- **결정**: prediction 개선 시도를 다음 세 갈래로 본문에서 다룬다.
  - representation 측: hybrid (cluster + change-point) — §5.5.
  - weighting 측: cost-sensitive (rf_decline_x2/x3, lgbm_decline_x2,
    rf_shap_weighted) — §5.9.
  - model 측: 외부 SOTA 14 종 (foundation 2 + stock SOTA 7 + SMB
    attention 3 + cost-sensitive 2) — §5.6.
- **근거**: 2026-04-30 미팅 "예측 모델을 기본 말고 더 강화하면 어
  떨까? technical novelty 가 있으면 좋겠다" + "주식 예측하는 모델,
  기술 등 literature 와 관련성".
- **데이터**: `260511/phase5_external/outputs/tables/phase5_summary.csv`,
  `weighting_compare.csv`, `foundation_zeroshot_compare.csv`,
  `neuralforecast_compare.csv`, `attention_compare.csv`.
- **금지**: 세 갈래 모두 본문에서 빼고 auxiliary 로 강등하는 것 (
  v5_thesis_final → final_thesis 전환 때 외부 SOTA 가 auxiliary 로
  강등됐던 사례).

## D4. 데이터 갭 처리 (4·6·7 개월 확장 윈도우) = (C) 안

- **결정**: ch5 작성을 위해 step05 를 재실행하여 14 panel 결과로
  `main_model_compare.csv` 를 갱신한다. 단, 작성 진도는 막지 않는다.
  ch4·ch3·ch1·ch2·ch6 을 먼저 정련하고 step05 종료 후 ch5 를 채운다.
- **근거**: CLAUDE.md "Known gap (as of 2026-05-07)" — §5.5.2 에서
  14 panel 비교를 약속하지만 현재 CSV 는 7 개 3 개월 panel 만 포함.
  v5 README §결과 인용 위치 의 약속을 깎지 않으려면 갱신이 필요.
- **부산물**: 재실행 로그는 `final_thesis/notes/step05_rerun.log` 에
  남긴다. 재실행 결과가 기존 7 panel 수치를 유의미하게 바꾸면 (예
  ΔF1 평균이 +0.005 이상으로 올라가면) D2 의 "조건부" 톤을 재검토
  한다.

## D5. 제출용 양식 = KAIST 제출요령 우선

- **결정**: 본문 형식 / 표지 / 서지 / 참고문헌 등 **모든 형식 충돌은
  KAIST 제출요령 (2026, `paperGuideline.pdf`) 이 최종 권위**다. APA 7
  은 참고문헌 본체 작성 가이드로만 사용한다.
- **소속 표기 (확정)**:
  - 한글: 기술경영학부
  - 영문: School of Business and Technology Management (BTM)
  - Degree 코드 (서지): MBTM
- **학위명 영문 (미해결)**: BTM 석사 학위명이 MBA / MS / 그 외인지
  학과 행정실 확인 후 `04_submission_approval.md` 에 일괄 반영.

## D6. 작성 언어

- **결정**: 한국어 본문 + 영문 초록 1 부.
- **금지**: 한글 본문에 영문 글자 혼용. 꼭 필요할 때만
  `한글 낱말 (영문 낱말)` 꼴 (제출요령 17 쪽).
