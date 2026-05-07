# 미팅 사전 Q&A 노트

> 04-30 미팅 발화 패턴과 본 폴더 결과를 합쳐, 다음 미팅에서 교수가 던질
> 가능성이 있는 질문을 미리 정리하고 답변·근거 파일·숫자를 함께 둔다.

## Q1. "체인지 포인트랑 클러스터는 앞 정보로 알 수 있는 내용이?" (전사 17:29)

**답**: 네. 둘 다 feature 윈도우 구간(`segment == "feature"`)만의
정규화된 매출 시퀀스에서 산출됩니다. target 구간 시퀀스는 KMeans /
change-point feature 계산에 들어가지 않습니다.

- 코드 근거: `../src/step05_train_main_model.py:166–169`
  ```python
  feat_panel = panel[panel["segment"] == "feature"]
  ids, seq = _seq_matrix(feat_panel)
  cluster_df = _cluster(seq, ids)
  cp_df = _change_point_features(seq, ids)
  ```
- 잔여 우려: KMeans가 train fold가 아니라 panel 전체에서 fit됨. cross-fold
  엄격성을 위해 train-fold 제한 fit으로 돌리는 ablation은 1주 안에 가능.

## Q2. "그러면 코로나 효과랑 시즈널 효과를 어떻게 분리했나?"

**답**: 시작연도(2021 vs 2022) 평균 macro-F1 차이는 +0.0114입니다.
시작월 진폭(0.0682)의 약 17% 수준이라, 코로나 잔여 효과는 정확도
변동의 주된 원인이 아닙니다.

- 근거: `../outputs/tables/seasonal_results_summary.csv`,
  `02_rolling_results.md` §2-2 표.
- 추가: 2022년 시작 panel(sm01..07)에서도 시즌 패턴이 동일하게 반복 →
  시즌이 코로나와 독립으로 작용.

## Q3. "데이터 끝 8월 직전 panel은 어떻게 처리했나?" (전사 07:37 휴가 시즌 우려)

**답**: 라벨이 인공적으로 Decline-편중되는 것을 직접 확인했습니다.
예) `sy2022_sm08_w1m_off1` Decline 0.675, `sy2021_sm07_w2m_off2`
Decline 0.629. 본 분석에서는 **모델 비교 결론 근거에서 분리**하고,
sanity check로만 부록에 남길 계획입니다 (D2).

- 근거: `../outputs/tables/label_distribution.csv`.

## Q4. "그래서 1번 contribution(베이스라인+클러스터+CP)은 살아남았나?"

**답**: 시즌 정렬 후 평균 +0.0022 macro-F1로 약화됩니다. 7개 panel 중
1개(`sy2022_sm03`)만 5% 유의(p=0.026), 1개(`sy2021_sm01`)는 10% 경계
(p=0.052), 나머지 5개는 미유의입니다.

- 근거: `../outputs/tables/main_model_compare.csv`,
  `../outputs/tables/main_model_paired_AvD.csv`.
- 함의: framing 옵션 (a)/(b)/(c) 중 어느 쪽으로 갈지 결정 필요 (D3).

## Q5. "기존 top_tier의 D ≫ A (~0.05) 결과는 그럼 뭐였나?"

**답**: target 구간이 항상 2023-06~08(여름 휴가 시즌)에 고정된 시즈널
confound 위에서 성립한 결과로 해석됩니다. 시즌 정렬을 강제하면 같은
점포·같은 모델로도 macro-F1이 0.43–0.54로 분산되어, "마지막 30주
고정" 자체가 라벨 분포를 인위적으로 통일시키는 효과가 있었습니다.

- 후속: legacy 결과를 동일 점포 기준으로 재현해 차이 표를 만들기 (D6 task 3).

## Q6. "결과가 다이나믹하게 바뀔 것 같지 않은데, 뭐가 새로운가?" (전사 11:03)

**답**: 정확도 자체는 0.43–0.54 범위로 legacy와 같은 영역입니다. 새로운 것은
**같은 데이터·같은 모델로도 라벨링 시점만 바꾸면 정확도가 0.10 폭으로
흔들린다**는 것을 직접 증명한 점입니다. 즉, 본 분석의 주된 가치는
정확도 향상이 아니라 **신호 해석의 정당성** 확보입니다.

## Q7. "윈도우 길이는 어디까지 늘려봤나?"

**답**: w ∈ {1, 2, 3, 4, 6, 7} 개월. w=3 0.4890 → w=4 0.4963 → w=6 0.4936
→ w=7 0.4900으로 w=4부터는 정체. **w=3개월을 기본 윈도우로 채택**할
실증 근거가 있습니다 (D4).

- 근거: `../outputs/tables/seasonal_results_summary.csv` 윈도우별 평균.

## Q8. "RF 말고 다른 모델은?"

**답**: LightGBM도 같은 panel에서 5-fold로 평가했습니다. 평균 macro-F1
차이는 0.004(LGB 0.4914 vs RF 0.4877). panel 단위 차이도 대부분
0.01 미만이라 모델 선택은 결론에 영향이 없습니다 (D5).

## Q9. "5월 8일 학과 제출 어떻게 됐나?"

**답**: 커미티 선정해서 제출하는 것으로 알고 있고, 별도 행정으로
처리합니다. 본 미팅 범위 밖.

## Q10. "LEVI / EWS / 외부 공공 데이터 그건 어떻게 됐나?"

**답**: 04-30 결정대로 본문에서 빼고 future work / 저널 트랙으로
미뤘습니다. 단, 도시경제 연결은 LEVI 라는 지표가 아니라 그 구성
변수들로 다시 풀 수 있어서, 디펜스 / 저널 확장에서 검토합니다
(`03_discussion_points.md` D7).
