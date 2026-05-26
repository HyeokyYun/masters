<!--
원본: 260516_overleaf_en/chapters/ch7_discussion_conclusion.tex
번역일자: 2026-05-22
-->

# Chapter 7 — Discussion and Conclusion (국문 번역)

본 장은 Chapter 4(현상 분석)·Chapter 5(예측 모델)·Chapter 6(robustness)의 결과를 종합하고, 학술적·실무적 함의를 정리한 뒤 한계와 향후 연구 방향을 논의한다.

---

## §7.1 결과 종합

Chapter 1의 네 RQ(RQ1–RQ4)에 다음과 같이 답한다.

### §7.1.1 RQ1 — 점포 수준 G/S/D 설명 변수

점포 수준에서 영업기간과 신규 고객 동태가 G/S/D Growth 클래스의 일관된 설명 신호를 제공한다(§\ref{sec:significant_vars}). 시즌 정렬 코호트 로지스틱 회귀에서 신규 고객 슬로프 → Growth 계수는 모든 영업기간 코호트에서 양: Q1_short +2.026, Q2 +1.255, Q3 +1.286, Q4_long +1.649. 즉 객단가 성장이나 재방문 강화보다 *지속적 신규 고객 유입* 이 매출 성장 경로의 가장 뚜렷한 신호 중 하나이며, 이 양의 연관은 모든 영업기간 코호트에 걸쳐 관찰된다.

### §7.1.2 RQ2 — 업종 × 동 분포 이질성

업종 × 동 조합 수준(§\ref{sec:industry_dong})에서 G/S/D 비율은 단순 업종 평균·동 평균으로 가려지는 큰 이질성을 보인다. 예: 은평구 생맥주 전문점 Growth 비율 0.690(최고), 동대문구 한식 일반 Decline 비율 0.330(조합 순위 상위). 동일 업종 내에서도 Growth 비율은 동별로 수 배 차이가 난다. 이 *공간 × 산업 상호작용* 은 단순 평균으로는 드러나지 않으며, 본 논문이 도출한 해석적·실무적 가치의 한 축.

### §7.1.3 RQ3 (i) — 큰 폭 성장 식별: inflection + UDX representation 의 설명력

점포 관측구간 첫 분기 대비 마지막 분기 평균 매출 2배 이상(=100% 이상 성장) 이항 분류에서, 17-변수 운영 feature set 의 baseline binary $F_1$ 은 RF 0.539 / XGBoost 0.681; 변곡점 feature(P1/P2 슬로프) + UDX 코드 더미 + cluster 라벨 결합으로 동일 80/20 holdout 에서 0.795 / 0.844 로 상승. 매출 곡선 *shape* 이 관측구간 큰 폭 성장에 강한 설명력을 가짐을 보임. UDX 코드가 매출 궤적의 사후 요약이므로 forward predictive power 의 직접 향상이 아닌 *explanatory ablation* 으로 해석(§\ref{sec:limitations}); external validity 는 향후 연구.

### §7.1.4 RQ3 (ii) — 시즌 정렬 G/S/D 예측의 representation·모델 선택

3개월 feature + 1년 후 3개월 target 의 G/S/D 삼항 분류에서, A_baseline (RF, 매출 통계 + 메타데이터 + 고객 구성, 43 features) 은 14 패널에 걸쳐 macro-$F_1 \approx 0.50$ (패널 범위 0.467–0.546). cluster + change-point hybrid (D) 추가는 평균 $\Delta F_1 = +0.0017$, Bonferroni 후 0/14 유의 — 단기 시즌 정렬 task 에서 baseline 에 대부분 흡수된 *조건부* 개선.

그러나 6 비교 패널에서 LightGBM 이 RF 대비 동일 representation 위에서 작지만 일관된 우위 (평균 $\Delta F_1 = +0.0075$, 5/6 승, 2/6 $p < 0.05$). 영업기간 사분위 코호트 분해 시 마진은 Q4_long 에서 가장 크다(+0.019, 전체 평균의 약 2.5배; §\ref{sec:cohort_lgbm}). 본 데이터의 *feature 이질성 + 강한 소수 클래스 신호 + 큰 categorical cardinality* 와 LightGBM 구조 특성(leaf-wise growth, histogram splitting, 고-카디널리티 효율 처리) 의 적합에서 기인.

### §7.1.5 RQ4 — Robustness 이중 검증

Chapter 6 은 G/S/D 결과가 세 차원에서 안정적임을 검증: (i) 시즌 정렬 패널 rolling, (ii) 14 비-LightGBM 비교 모델, (iii) GNN 비교.

- **시즌 정렬 패널.** 7 핵심 3개월 패널 모두 패널 내부 5-fold 표준편차 ≤ 0.009, 붕괴 없음; 19 시즌 정렬 패널의 macro-$F_1$ 은 0.43–0.54 범위 유지, 단 strict OOT 분석은 start month 가 여전히 주요 변동원임을 보인다. 윈도우 확장(4·6·7개월) 도 0.475 ~ 0.550 유지.
- **14 비-LightGBM 비교 모델.** 14 비-LightGBM 비교 모델은 어느 것도 RF를 상회하지 못함(모두 음, −0.0345 ~ −0.2705); 우리 LightGBM 계열 3종(+0.0026 ~ +0.0075) 만 상회. 외부 모델 자체의 결함이 아니라 *데이터 특성 mismatch*(샘플링·빈도, 단면 이질성, 빈번한 불연속) 의 결과로 해석.
- **GNN.** 동-업종 결합 이종 그래프 + SHAP-가중 GCN 변형이 본 구성에서 RF 대비 −0.10 ~ −0.14. 공간 신호 부재가 아니라 *현재 그래프 구성·가중치 학습이 본 데이터의 공간 신호를 충분히 포착 못함* — 향후 연구의 직접 동기.

---

## §7.2 학술적 함의

세 가지.

### §7.2.1 현상 분석과 예측의 정합적 통합

기존 소상공인 연구는 (i) 횡단면 회귀로 *어떤 변수가 영향* 을 주는지 설명하는 갈래 \cite{stinchcombe1965social,gimeno1997survival,davidsson2003role,audretsch2005knowledge,kim2021smb,lee2023kcd} 와 (ii) 시계열 학습으로 *매출 패턴 자체* 를 예측하는 갈래로 분리되어 왔다. 본 논문은 두 갈래를 *단일 파이프라인 안에서* 묶고, 현상 분석에서 정보적이라 식별된 변수(영업기간, 신규 고객 동태 등)가 예측 representation 으로 이어지는지를 검토한다. 답은 task-의존적이다: 매출 곡선 형상은 관측구간 큰 폭 성장 상태를 강하게 *설명* 하지만(explanatory ablation), 시즌 정렬 G/S/D task 에서는 baseline 이 이미 신호 대부분을 흡수해 hybrid representation 의 증가분이 제한적·조건부($\Delta F_1 = +0.0017$)다. 즉 본 데이터에서 설명력이 곧바로 큰 예측 이득으로 이어지지는 않는다.

### §7.2.2 데이터 특성 기반 모델 선택 해석

본 논문은 LightGBM 의 RF 대비 우위를 단순히 "LightGBM 이 더 낫다" 로 보고하지 않고 데이터 특성 관점에서 해석(§\ref{sec:rf_vs_lgbm}). 마찬가지로 14 비-LightGBM 비교 모델이 음의 마진을 보인 결과도 외부 모델의 결함이 아니라 *데이터 특성 mismatch* 로 해석. "어떤 모델이 어떤 데이터에서 더 낫다" 는 일반 주장을 본 데이터의 *주간 빈도 + 점포 이질성 + 빈번한 불연속* 이라는 구체 차원으로 환원하려는 시도 \cite{hyndman2021forecasting,bergmeir2012use,elsayed2021dlmodels}.

### §7.2.3 공간 그래프 신호의 조건부 진단

본 논문의 GNN 비교 결과는 *공간 신호가 무의미하다* 는 결론이 아니라 *현재 그래프 구성·가중치 학습 방법이 본 데이터에 불충분하다* 는 진단. 동-업종 결합 그래프 + SHAP-가중 구성은 추가 마진을 주지 못했으나, 시간 차원을 결합하는 STGCN \cite{yu2018stgcn} 같은 향후 시공간 확장의 직접 동기를 분명히 제공.

---

## §7.3 실무적 함의

세 그룹에 직접 적용 가능.

### §7.3.1 점포주 (소상공인)

영업기간과 신규 고객 비율이 G/S/D 의 핵심 신호라는 발견은, 점포주가 자기 매출 동태를 자가 진단할 때 단순 매출 추세와 함께 *신규 고객 유입의 슬로프* 와 *재방문 구조* 를 모니터링해야 함을 시사. 특히 진입 직후 단기 코호트(Q1_short, 중위 약 7개월) 가 신규 고객 슬로프 계수가 가장 크므로(+2.026), 개업 초기의 신규 고객 확보 패턴이 이후 성장 경로의 중요한 조기 신호로 보인다.

### §7.3.2 정책 입안자 / 지자체

업종 × 동 G/S/D 분포 이질성(예: 동대문구 한식 일반 Decline 0.330, 조합 순위 상위) 은 정책 자원의 *공간·산업 targeting* 에 정량 근거 제공. fragile cluster 식별($n=744$, Decline 35.9%) 은 조기 경보 시스템의 출발점이 될 수 있으며, 전체 macro-$F_1$ ≈0.50 수준에서 이 분류기는 독립적 정책 결정 근거가 아니라 *1차 진단 스크리닝의 프로토타입* 으로 쓸 수 있다.

### §7.3.3 KCD 플랫폼 운영자

KCD 같은 카드 매출 SaaS 운영자는 본 논문 hybrid representation 의 구성 요소를 점포주 대시보드·사업 분석 리포트에 직접 통합 가능. 특히 매출 곡선 *형상(shape)* feature가 큰 폭 성장 점포 식별에 가장 크게 기여(이항 $F_1$ 최대 +0.26 향상; §\ref{sec:taskA_ablation}) 한다는 결과는 가능한 제품 방향을 시사: 기존 평면 매출 추세 리포트를 *shape 기반 진단* 으로 확장.

---

## §7.4 한계

본 논문의 결론은 다음 여섯 한계 안에서 해석되어야 한다.

### §7.4.1 제한된 분석 범위

서울 외식업 약 59,000 점포, 2021.01–2023.08 142주에 한정. 따라서 (i) 비외식 업종(소매·서비스), (ii) 비수도권, (iii) COVID-19 이전 시기로의 외삽은 별도 검증 없이 보장되지 않음. 외식업은 계절·외부 충격에 가장 민감한 부문이라 본 논문의 추정 연관·모델 비교 패턴은 타 업종에서 약해질 수 있음.

### §7.4.2 제한된 관측 단위 (카드 결제)

매출 데이터가 카드 결제 매출에 한정. 따라서 (i) 현금 결제 비중 높은 점포, (ii) 배달 플랫폼 매출, (iii) off-premise 매출(테이크아웃·케이터링) 은 부분만 반영. 카드 결제 침투율이 업종·점포별로 다른 점이 직접 매출 수준 비교의 caveat.

### §7.4.3 폐업·업종 변경의 불연속 처리

점포는 휴무·영업시간 변경·부분 상호 변경 등 빈번한 불연속을 가짐. 전처리가 결측 보간·마스킹으로 처리하지만, 불연속의 *이유*(자발적 폐업 vs 외부 충격 vs 사실상 폐업) 는 구분하지 않음. 14 비-LightGBM 비교 모델이 음의 마진을 보인 한 요인으로 해석.

관련하여, 각 패널은 입력·target 윈도우에 모두 관측된 점포만 라벨링하므로 표본은 target window 생존에 조건부이다: 그 전에 폐업한 점포는 라벨되지 않는다. 따라서 G/S/D 클래스 분포는 영업 지속 점포를 반영하며 terminal decline을 과소대표할 수 있다 — G/S/D 상태는 절대적 폐업이 아니라 *영업 윈도우 내 쇠퇴* 를 포착하며, 폐업 시점 예측은 후속 연구로 남긴다.

### §7.4.4 GNN 구성의 한계

Chapter 6 의 GNN 비교는 (i) 동·업종 결합 정적 이종 그래프, (ii) GCN \cite{kipf2017semi} 기반 공간 전파(GAT \cite{velickovic2018graph} 계열은 future), (iii) SHAP \cite{lundberg2017unified} 기반 엣지 가중 heuristic 에 한정. 시간 차원을 결합하는 STGCN \cite{yu2018stgcn} 계열·동적 그래프·더 깊은 이종 GNN 변형은 다루지 않음. "이 구성에서 GNN 은 추가 마진 없음" 결론은 본 구성 범위 내 진단.

### §7.4.5 두 prediction 타깃은 직접 비교 불가
(`sec:tasks_incomparable`)

본 논문의 두 prediction 타깃은 *별개* 로 직접 비교 불가.

- 큰 폭 성장 binary $F_1$ 0.539–0.844 (큰 폭 성장 baseline · inflection + UDX) 는 (i) 이항 라벨(`growth_rate ≥ 1.0`), (ii) binary $F_1$(양성=큰 폭 성장), (iii) 단일 80/20 stratified holdout, (iv) 점포 누적 운영 변수 + 사후 요약 UDX 코드 입력 위의 평가.
- G/S/D macro-$F_1$ 0.43–0.54 (시즌 정렬 패널 rolling) 는 (i) 3-class G/S/D 라벨($\pm 0.5\sigma$ 슬로프), (ii) macro-$F_1$, (iii) 14 패널 × store-grouped 5-fold CV, (iv) 동일 캘린더 3개월 입력 → 1년 후 3개월 target 의 *forward prediction* 평가.

두 타깃의 절대 수치는 합산·평균·동일 지표 비교를 해서는 안 되며, 본 논문은 타깃 내 향상·안정성만 주장.

### §7.4.6 큰 폭 성장 단일 holdout · 사후 요약 변수 의존
(`sec:taskA_caveats`)

큰 폭 성장 binary $F_1$ 0.795 / 0.844 향상은 다음 두 한계 안에서 해석.

1. **사후 요약 변수의 설명력.** 결합 representation 의 `final_code` (UDX: DUY, DDZ 등) 는 점포 매출 패턴 shape 의 사후 압축이며, 구성상 큰 폭 성장 패턴(UU 등) 과 강하게 연관. 따라서 여기의 $\Delta F_1$ 은 *매출 곡선 shape 이 장기 매출 성장과 강하게 연결됨* 을 보이는 *explanatory ablation* 이며, *forward predictive power 의 직접 향상* 으로 번역하려면 변곡점/UDX 정의 윈도우를 라벨 정의 윈도우와 분리해야 함 (예: 변곡점 정의 윈도우 이후 미래 기간에서 `growth_rate` 산출).
2. **단일 holdout · 단일 seed 평가.** 큰 폭 성장 결과는 stratified 80/20 holdout, seed=42 의 단일 시행; store-grouped 5-fold 또는 시즌 정렬 rolling 하의 안정성은 본 논문에서 미검증. 따라서 큰 폭 성장 task 의 XGBoost > RF 순위는 통계적으로 검증된 모델 비교가 아니라 서술적으로 해석해야 한다.

---

## §7.5 향후 연구

네 방향.

### §7.5.1 시공간 hybrid 모델 (STGCN 계열)

Chapter 6 의 GNN 결과는 *현재 정적 그래프 구성* 의 한계 진단이지 공간 신호 부재가 아님. 시간 차원·동적 그래프·attention 기반 시공간 모델을 결합하는 STGCN \cite{yu2018stgcn} 계열이 본 데이터 공간 신호를 더 잘 포착할 수 있음. 특히 점포 간 계절 공변동(co-seasonality) 과 인접 점포 간 매출 spillover 의 동시 모델링이 유망.

### §7.5.2 업종·지역 확장

외식업·서울 한정 결과를 비외식(소매·서비스)·비수도권(부산·대구 등) 으로 확장하려면 추정 연관과 모델 비교 순위의 *external validity* 보존 정도를 검증해야 함. 특히 카드 결제 침투율·계절 amplitude 가 다른 지역·업종에서 hybrid representation 마진이 어떻게 변하는지는 본 논문이 답하지 않음.

### §7.5.3 멀티모달·외부 신호 통합

본 논문은 KCD 카드 매출 단일 모달에 한정. (i) 행정안전부 인허가 데이터(개·폐업 시점), (ii) 통계청·지자체 공간·인구 데이터(거주·유동 인구, 지역 경제 활력 지수), (iii) 배달 플랫폼 거래 데이터 같은 외부 신호 결합으로 신호 공간 확장 가능. 특히 *개·폐업 시점 자체* 를 라벨로 결합하면 G/S/D 분류와 폐업 예측 사이 연속선의 통합 모델링이 가능.

### §7.5.4 조기 경보 시스템(EWS)·cost-sensitive 의사결정 확장

fragile cluster 식별(§5.6) 과 cost-sensitive 보조 실험(§5.8) 은 그 자체로 정책 결정 도구는 아니나, 임계값·비용 행렬을 명시한 EWS 로 후속 발전 가능. 핵심은 현재 macro-$F_1$ 지표를 보존하면서 정책 비용을 반영하는 *calibration·cost-sensitive 지표* 설계이며, 본 논문 결과(rf_decline_x2/x3 의 macro-$F_1$ 단조 감소) 는 단순 비용 가중이 충분치 않음을 이미 시사.

---

## §7.6 맺음말

본 석사학위논문은 KCD 가 제공한 서울 외식업 약 59,000 점포 주간 카드 매출 데이터 위에서 *현상 분석 → 예측 representation → 모델 비교 → robustness* 흐름을 통해 다음을 입증했다. 점포 수준에서 신규 고객 동태와 영업기간이 G/S/D Growth 클래스의 일관된 신호를 제공하고, 보조 큰 폭 성장 회귀에서는 신규 고객 비율과 매출 변동성이 관측구간 첫/끝 분기 매출 2배와 연관되며, 업종 × 동 조합 수준에서 G/S/D 비율 이질성이 분명하다.

큰 폭 성장 식별(이항 분류) 에서 변곡점·UDX 코드 feature 를 17-변수 운영 baseline 에 결합하면 binary $F_1$ 이 0.539→0.795 (RF), 0.681→0.844 (XGBoost). UDX 코드가 사후 요약이므로 단일 80/20 holdout 위의 explanatory ablation; external validity 는 향후 연구(§\ref{sec:taskA_caveats}).

시즌 정렬 14-패널 G/S/D 단기 예측 에서 A_baseline macro-$F_1 \approx 0.50$, cluster + change-point hybrid 평균 $\Delta F_1 = +0.0017$ (Bonferroni 후 0/14 유의) — *조건부* 개선. 동일 representation 에서 LightGBM 이 RF 대비 작지만 일관된 우위(6 패널 평균 $\Delta F_1 = +0.0075$, 5/6 승, 2/6 $p<0.05$), 원인은 본 데이터의 *feature 이질성 + 강한 소수 클래스 신호 + 큰 categorical cardinality* 와 LightGBM 구조 특성의 적합으로 해석. 19 시즌 정렬 패널 macro-$F_1$ 0.43–0.54, 14-모델 외부 비교에서 LightGBM 계열 3종만 우위·14 비-LightGBM 모델 모두 일관된 음의 마진, 본 구성 GNN 의 음의 마진이 함께 G/S/D 결과의 안정성과 향후 시공간 확장 동기를 제공.

본 논문이 제안한 *현상 분석에 근거한 representation 설계* 와 *데이터 특성 기반 모델 선택 해석* 이 후속 거래 기반 점포 분류 연구에 채택되면, 이 프로토콜은 그러한 연구와 신중한 정책 적용에 더 투명한 근거를 제공할 수 있다.
