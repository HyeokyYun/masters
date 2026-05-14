# final_thesis — KCD 석사학위논문 최종 작성 폴더

KAIST 기술경영학부(BTM) 석사학위논문(MBTM)의 **제출 직전 최종본**을
모으는 폴더다. 이전의 `thesis/drafts/v5_thesis_final/` 가 워킹 드래프트
였다면, 본 폴더는 그것을 KAIST 학위논문 작성 및 제출요령(2026,
`paperGuideline.pdf`) 양식에 맞춰 최종 정련한 결과물을 담는다.

## 폴더 구조

```
final_thesis/
  README.md                       — 본 파일
  paperGuideline.pdf              — KAIST 작성 및 제출요령 (2026)
  paperGuideline.txt              — 위 PDF 텍스트 추출본 (참조용)
  notes/
    framing_decisions.md          — 4/30 미팅 후 framing 결정 로그
    step05_rerun.log              — step05 재실행 로그
  thesis/                         — 본문 (한국어)
    ch0_abstract.md               — 한글 500자 + 영문 300단어
    ch1_introduction.md
    ch2_literature.md
    ch3_data.md
    ch4_methodology.md
    ch5_results.md
    ch6_discussion.md
    ch7_conclusion.md
    references.md
  front_matter/                   — 머리지면 양식 (제출요령 9~16쪽)
    01_cover.md                   — 겉표지
    02_inner_cover.md             — 속표지
    03_approval_stamp.md          — 심사완료 검인
    04_submission_approval.md     — 제출 승인서·연구윤리 준수 확인
    05_bibliographic_abstract.md  — 서지사항·초록
    06_toc.md                     — 차례
```

## 작성 정책

1. **Prediction-first framing.** 상위 RQ 는 "초기 거래 패턴으로 G/S/D
   를 얼마나 잘 예측할 수 있고, 어떤 요인·표현·모델이 그 예측을
   개선시키는가" 다. 시즌 정렬 / hybrid representation / 외부 SOTA
   benchmark / cost-sensitive 보조 실험은 모두 이 상위 prediction
   질문의 sub-component 로 위치한다 (2026-04-30 미팅 결정).
2. **출처 인용은 경로로 한다.** 그림·표는 본 폴더에 복사하지 않고
   `260430_claude/outputs/...` 또는 `260511/phase5_external/outputs/...`
   경로를 명시한다.
3. **수치는 산출물에서 그대로 인용**한다. 임의로 반올림하거나 재추정
   하지 않는다.
4. **한국어 본문 + 영문 초록.** 한글 본문에는 영문 글자를 섞지 않는다
   (KAIST 제출요령 4쪽). 꼭 필요할 때만 `한글 낱말 (영문 낱말)` 꼴.
5. **톤은 정직하게.** v4 의 "신호 유지", "robustness evidence" 표현은
   부활시키지 않는다. 시즌 정렬 후 hybrid representation 향상이 14
   panel 평균 ΔF1 = +0.0017 (5% 유의 1/14, Bonferroni 후 0/14) 이라는
   것을 모든 챕터에서 일관되게 반영한다.
6. **LEVI / EWS / GNN / Golden Cross / 외부 공공 데이터 = ch6.5 / ch7
   future work 에서만 1–2 문단**으로 다룬다(2026-04-30 미팅 결정).
7. **기존 자산은 보존.** `thesis/drafts/v5_thesis_final/`,
   `260430_claude/outputs/`, `260511/phase5_external/outputs/`,
   `top_tier/` 는 읽기만 한다.

## 본문 구조 (세 contribution)

본 학위논문은 세 본문 기여를 다음 순서로 제시한다.

1. **Prediction baseline 과 요인 분해 (기여 1).** §5.2 ~ §5.5
   baseline + §5.7 업력 cohort 분석 + §5.8 cluster 요인 분해.
2. **Seasonal alignment label robustness 전제 (기여 2).** §5.2 ~ §5.4
   145 specification baseline (시작월 진폭 0.10 ≫ 윈도우 길이 0.02–
   0.04 ≫ 시작연도 0.01 미만).
3. **세 갈래 prediction-improvement 와 SMB-specific 차별화 (기여 3).**
   §5.5 (hybrid representation 조건부 +0.0017) + §5.9 (cost-sensitive
   음(−)) + §5.6 (외부 SOTA 14 종 중 LightGBM 1 종만 RF 능가).

## 진행 체크리스트

- [x] final_thesis 스켈레톤 + framing 메모
- [x] step05 재실행 → main_model_compare.csv 14 panel 갱신
      (`notes/step05_rerun.log` 참조; 14 panel × 4 모델 = 56 행 + 헤더)
- [x] ch3 data
- [x] ch4 methodology + §4.9 cohort/cluster 정의 + §4.10 cost-sensitive
      프로토콜
- [x] ch5 results — §5.7 업력·신규고객 cohort 분석 + §5.8 cluster
      요인 분해 + §5.9 cost-sensitive 보조 실험 + §5.6 외부 SOTA 14
      종 보강
- [x] ch1 introduction — prediction-first framing + 4 RQ + 3 contribution
      구조 재작성
- [x] ch2 literature
- [x] ch6 discussion — §6.1.6 cohort + §6.1.7 cluster + §6.2.5 경제적
      해석 + §6.5 future work 에 GNN / cost-sensitive policy sweep 추가
- [x] ch7 conclusion — 7 finding + 3 contribution mirror
- [x] ch0 abstract (한 485/500자, 영 290/300단어)
- [x] front_matter 6 종 (지은이/지도교수/제목/학위명 영문은 placeholder)
- [x] references (KAIST 양식 우선 + APA 7)

## 인용된 외부 산출물 (수정 금지, 읽기 전용)

```
260430_claude/outputs/tables/
  main_model_compare.csv               — 14 panel × 4 모델 (A/B/C/D)
  main_model_paired_AvD.csv            — paired t-test
  seasonal_results_summary.csv         — 145 specification baseline
  age_cohort_nc_effect.csv             — 업력 × 신규고객 logit
  cluster_outcome_summary.csv          — cluster 내 macro-F1
  cluster_outcome_xtab.csv             — cluster × G/S/D 교차표
  per_cluster_feature_importance.csv   — cluster 별 feature importance
  gnn_compare.csv                      — GNN pilot (future work)

260511/phase5_external/outputs/tables/
  phase5_summary.csv                   — 14 종 외부 SOTA 종합표
  foundation_zeroshot_compare.csv      — Chronos, Moirai zero-shot
  neuralforecast_compare.csv           — TFT/N-BEATS/N-HiTS/PatchTST/
                                          DLinear/Informer/Autoformer
  attention_compare.csv                — SMB-attention 3 종
  weighting_compare.csv                — cost-sensitive / SHAP-weighted
  lgbm_per_cohort_summary.csv          — Q1-Q4 cohort × LGB-RF Δ
```

## 사용자 확인 필요 항목 (front_matter placeholder 채움용)

| placeholder | 위치 | 비고 |
| --- | --- | --- |
| 지은이 한글·한자·영문 (Last, First) 이름 | 01·02·03·04·05 | 디렉터리명에서 추측하지 않고 placeholder 로 둠 |
| 한글 / 영문 논문 제목 | 01·04·05 | prediction-first framing 으로 바뀌어 새 후보 필요 |
| 학위명 영문 (MBA / MS / 그 외) | 04 | **학과 행정실 확인 필수** |
| 지도교수 한글·영문 이름 / 칭호 | 03·04·05 | 공식 표기 확인 |
| 심사 통과일 / 심사위원 명단 | 03·04 | 심사 후 |
| 본문 / 서문 쪽 수 | 05 | 조판 후 |
