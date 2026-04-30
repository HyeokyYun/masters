# 석사학위논문 완성 계획 (KAIST 기술경영학부)

작성일: 2026-04-22
상태: 제안 — 지도교수 및 본인 확인 후 각 장 초안 작성으로 이행

---

## 0. 논문 정체성

- **제목(가제)**: 주별 거래 데이터로 본 소상공인의 성장·하락 신호: 신규 고객 유입과 업력의 역할
- **영문 제목(가제)**: Diagnosing Small-Business Growth and Decline from Weekly Transaction Data: The Role of New-Customer Inflow across Business-Age Buckets
- **학위**: KAIST 경영대학 기술경영학부 석사
- **지도교수**: 김지희 교수
- **데이터 공급**: Korea Credit Data (KCD) — 서울시 외식업 주별 거래 패널

### 중심 주장 (Thesis statement)

> 소상공인의 생애주기는 "창업-성장-성숙-쇠퇴"의 단일 곡선으로 요약되지 않는다. 주별 거래 데이터로 관찰한 **성장·정체·하락** 상태는 업력 구간에 따라 드라이버가 다르며, 특히 **업력 12개월 이후부터 신규 고객 유입(new-customer ratio)**은 매출 추세(trend slope) 다음으로 강력한 성장 판별 신호로 부상한다. 이 진단은 **초기 30주의 관측만으로도** 의미 있는 예측력을 갖는다.

### 3대 기여

1. **실증 렌즈 분리**: post-entry trajectory(개업 직후 경로) vs observed-window state(생존 점포의 현재 상태) — 두 렌즈가 상호 보완적임을 보임.
2. **업력별 드라이버 지도**: 업력 bucket(0-12, 12-24, 24-36, 36-60, 60-120, 120+개월)마다 성장/하락 판별 feature의 **중요도 구조가 달라짐**을 정량화. 신규 고객 비율의 importance가 업력이 길어질수록 증가(2.19 → 7.47).
3. **초기 관측 기반 조기 진단**: 30주 관측 + feature-block 조합으로 level-only baseline(F1 0.562) 대비 weighted F1 0.669까지 도달. Cluster label은 이미 포함된 feature block 대비 marginal gain이 작음을 보여 "클러스터가 핵심"이라는 초기 서술을 실증적으로 수정.

---

## 1. 사용 자료 지도 (What's already there)

| 자산 | 경로 | 상태 | 논문 활용 위치 |
|---|---|---|---|
| 원자료 meta | `original_data/meta.csv` — 59,089점포 | 완료 | Ch.3 데이터 |
| 원자료 weekly | `original_data/weekly.parquet` — 6.58M store-weeks, 142주 | 완료 | Ch.3 데이터 |
| 기존 최종보고서 | `docs/KCD_FINAL.pdf` | 완료 | Ch.1·2 배경, Ch.6 한계 논의 |
| DEEP_RESEARCH_BRIEF | `docs/DEEP_RESEARCH_BRIEF.md` | 완료 | 전장 구조 가이드 |
| Extended Abstract | `docs/KER_Extended_Abstract_Final.md` | 완료 | Ch.7 요약·Conclusion base |
| Figure 1 (two lenses) | `docs/thesis_figures/main_figures/figure1_two_lenses_lifecycle.png` | 완료 | Ch.5 §5.1 |
| Figure 2 (age-bucket drivers) | `docs/thesis_figures/main_figures/figure2_age_bucket_drivers.png` | 완료 | Ch.5 §5.2 [핵심] |
| Figure 3 (prediction & ablation) | `docs/thesis_figures/main_figures/figure3_prediction_windows_and_ablation.png` | 완료 | Ch.5 §5.3 |
| Figure S1 (new customer / volatility) | `docs/thesis_figures/supporting_figures/figureS1_new_customer_and_volatility.png` | 완료 | Ch.5 보충 |
| Source tables | `docs/thesis_figures/source_tables/*.csv` | 완료 | 표 작성 원자료 |
| Paper draft (English, 4장) | `top_tier/paper_draft/0[1-4]_*.md` | 완료 | 한글 번역·압축하여 Ch.1-4 초안 소스 |
| Top-tier 리뷰 보고서 | `top_tier_review_20260416/top_tier_research_development_report.md` | 완료 | 약점·제한 체크리스트 |

핵심 수치(이미 계산되어 있음):
- 전체 표본 50,635점포 중 Growth 40.04%, Stable 38.24%, Decline 21.72%
- Age-bucket별 Growth 비중 상승·Decline 비중 하락 경향
- `trend_slope` 모든 bucket에서 importance 1위
- `nc_rate` importance: 12-24m(2.19) → 24-36m(5.18) → 36-60m(5.60) → 60-120m(7.47) → 120m+(6.12)
- 3-class early prediction (GBM weighted F1): 20w 0.542, 30w 0.572, 40w 0.600, 50w 0.631
- Feature ablation (weighted F1): level-only 0.562 → +trend/vol 0.633 → +customer 0.654 → +local 0.669 → +cluster 0.669

---

## 2. 논문 구조 (한글, KAIST MoT 석사논문 기준)

분량 기준: 본문 60-90쪽(한글 200자 원고지 환산).

### 목차

1. **서론** (6-8쪽)
   - 1.1 연구 배경: 소상공인 경제 비중·폐업 충격
   - 1.2 문제의식: 설문 기반·연단위 재무제표 기반 선행연구의 한계, 생존편향
   - 1.3 연구 질문 3가지 (아래 RQ1-3)
   - 1.4 기여 및 논문 구성

2. **이론적 배경 및 선행연구** (8-12쪽)
   - 2.1 조직 생애주기 이론(Boulding, Adizes, Miller & Friesen)과 그 한계
   - 2.2 소상공인 생존·성장 결정요인 문헌
   - 2.3 Transaction-based business dynamics / digital trace analytics
   - 2.4 시계열 클러스터링·조기 경보 시스템(EWS) 문헌
   - 2.5 연구 격차 정리 및 본 연구 포지셔닝

3. **데이터** (6-8쪽)
   - 3.1 KCD 데이터 개요 (59,089점포, 142주, 6.58M store-weeks, 2021-01-01~2023-08-28)
   - 3.2 Meta 변수 및 주별 변수 정의
   - 3.3 두 개의 실증 표본 구성
     - 3.3.1 Post-entry 표본 (24,278점포, open 기준 정렬, 108/162주)
     - 3.3.2 Observed-window 표본 (50,635점포, 최소 52주 관측)
   - 3.4 기술통계 및 결측 처리
   - 3.5 표본 편향 논의 (생존 편향, 관측 중단)

4. **연구방법** (10-14쪽)
   - 4.1 분석 프레임워크 개요 (두 렌즈)
   - 4.2 Post-entry trajectory 레이블링
     - 4.2.1 시계열 클러스터링 (Euclidean K-Means 주 사용, K-shape 비교)
     - 4.2.2 변곡점 식별 및 레이블 체계 (DDZ/DDY/DUY/UUX/UDY/UDZ)
   - 4.3 Observed-window 3-class 상태 레이블링
     - 4.3.1 Growth/Stable/Decline 정의 (trend 기반 ±0.5σ 컷오프)
     - 4.3.2 업력 bucket 구성
   - 4.4 Feature 엔지니어링
     - 4.4.1 Level features (매출 수준)
     - 4.4.2 Trend/Volatility features (trend_slope, residual volatility)
     - 4.4.3 Customer behavior features (nc_rate, 반복 구매, 주말/시간대 비중)
     - 4.4.4 Local context features (동 단위 경쟁 강도, 업종 더미)
   - 4.5 모델링
     - 4.5.1 Multinomial Logit — 업력 bucket별 driver 분석
     - 4.5.2 Gradient Boosting (GBM/XGBoost) — 조기 예측
     - 4.5.3 성능 평가 지표(macro F1, weighted F1, AUC, recall by class)
   - 4.6 Robustness 설계
     - 4.6.1 컷오프 민감도 (0.3σ/0.5σ/0.7σ)
     - 4.6.2 관측기간 민감도 (52/78/104/142주)
     - 4.6.3 Out-of-time validation

5. **결과** (18-22쪽)
   - 5.1 **결과 1 — 이질적 생애주기 경로** (Figure 1)
     - 5.1.1 Post-entry trajectory: 6-label 분포, DDZ 62% 지배
     - 5.1.2 Observed-window: Growth 40% / Stable 38% / Decline 22%
     - 5.1.3 업력 bucket별 상태 분포
   - 5.2 **결과 2 — 업력별 driver의 차이** (Figure 2) [핵심]
     - 5.2.1 전 구간: trend_slope가 1위
     - 5.2.2 신규 고객 비율의 등장과 강화 — 12-24m부터 top-3, 120m+에서 2위
     - 5.2.3 MDD는 Decline과 일관 연결
     - 5.2.4 해석: 업력에 따른 운영 리스크의 질적 변화
   - 5.3 **결과 3 — 조기 예측 가능성** (Figure 3)
     - 5.3.1 관측 창 길이 효과 (20w/30w/40w/50w)
     - 5.3.2 Feature block ablation — level-only vs + trend/vol vs + customer vs + local vs + cluster
     - 5.3.3 3-class vs 12-class 예측 난이도 비교
   - 5.4 보조 분석 (Figure S1)
     - 5.4.1 신규 고객 quantile별 Growth/Decline share
     - 5.4.2 Volatility의 재해석 — CV vs residual volatility
   - 5.5 Robustness
     - 5.5.1 컷오프·관측기간 민감도
     - 5.5.2 업종·구역별 일관성
     - 5.5.3 Out-of-time (2023년 cohort test)

6. **토의** (6-8쪽)
   - 6.1 이론적 시사점: 단일 생애주기 곡선을 넘어선 거래 기반 진단
   - 6.2 신규 고객 유입의 의미: 성장기 뿐 아니라 장기 생존 업장에서의 재활력 지표
   - 6.3 정책·플랫폼 시사점: 생애주기 기반 지원 체계의 재설계 방향
   - 6.4 한계
     - 6.4.1 인과 해석 불가 (진단·예측 틀임을 명시)
     - 6.4.2 서울·외식업 단일 도메인, 2021-2023 관측창
     - 6.4.3 생존편향의 잔여 영향
     - 6.4.4 데이터 비공개 (재현성 제한)
   - 6.5 향후 연구: 서울 타 업종 확장, 상권 정보 결합, 폐업일 매칭을 통한 survival model

7. **결론** (2-3쪽)

**참고문헌 / 부록** (feature 정의표, hyperparameter 표, robustness 확장표, 업종·구역 교차표)

---

## 3. 연구 질문과 근거 매핑

| RQ | 질문 | 답 | 근거 파일 |
|---|---|---|---|
| RQ1 | 소상공인 매출 궤적은 단일 곡선으로 요약되는가? | 아니다. Post-entry에서 DDZ(62%)가 압도적이고, 종 모양(UDY)은 0.8%에 불과. | `260319_cur`, `260326_fullsample` |
| RQ2 | 성장·하락을 가르는 신호는 업력에 따라 어떻게 달라지는가? | `trend_slope`는 전 구간 1위이나, `nc_rate`는 12개월 이후부터 top-3로 부상하고 importance가 업력과 함께 증가. | `260326_fullsample/outputs/tables/fullsample_age_bucket_feature_top5.csv` |
| RQ3 | 초기 30주 관측만으로 장기 상태를 예측할 수 있는가? | 가능하지만 level-only(F1 0.562)보다 trend/volatility·customer·local context를 추가할 때 실질 gain(F1 0.669). 관측 창이 길수록 개선. Cluster는 marginal. | `260321_cur`, `260325` |

---

## 4. 진행 체크리스트 (What's left to COMPLETE)

### (A) 이미 완성된 자산 (그대로 활용)
- [x] Figure 1/2/3/S1 (pdf/png)
- [x] Source tables (CSV)
- [x] 핵심 수치 결과
- [x] 영문 paper draft 4개 섹션 (Introduction / Theoretical / Related Work / Methodology)

### (B) 본 계획에서 채워야 할 것
- [ ] 본 문서 `THESIS_PLAN.md` 확정
- [ ] Ch.1 서론 한글 초안
- [ ] Ch.2 이론적 배경·선행연구 한글 초안 (KCD_FINAL 2장 재활용 + Greiner/Miller & Friesen 확장)
- [ ] Ch.3 데이터 한글 초안 (표본 버전 불일치 명확히)
- [ ] Ch.4 연구방법 한글 초안
- [ ] Ch.5 결과 한글 초안 — 3개 결과 + 보조 + robustness
- [ ] Ch.6 토의 한글 초안
- [ ] Ch.7 결론 한글 초안
- [ ] 국문초록 / 영문초록
- [ ] 참고문헌 정리 (한국 문헌 + 영문 문헌)
- [ ] 부록 표 정리 (feature 목록, hyperparameter, robustness 확장표)

### (C) 심사 방어를 위해 선제적으로 정리할 약점
- 표본 버전 불일치: `KCD_FINAL.pdf`의 66,667/2019-2023 vs 본 논문의 59,089/2021-2023 → 본문에서 "원자료 업데이트 및 분석 창 재정의" 각주 반드시 포함
- Clustering silhouette 낮음(0.03-0.07) → "behavioral state construction 보조 도구"로 position
- 인과 단어 사용 금지: 모든 문장에서 `precede`, `cause`, `leads to`가 아닌 `associated with`, `predicts`, `diagnostic signal`
- "Golden cross"는 본문 중심이 아닌 보조 결과(§5.4)로만 언급
- "30주로 F1 0.84"는 **쓰지 않는다**. 최신 수치 F1 0.572(3-class, 30w, GBM)를 사용

---

## 5. 진행 순서

각 장마다 (1) 골격 bullet → (2) 산문 초안 → (3) 지도교수 검토 후 수정의 3회 반복으로 진행.

1. **이번 단계**: 본 `THESIS_PLAN.md`를 사용자 검토 받아 고정
2. 다음 단계: Ch.3 데이터 → Ch.4 방법 → Ch.5 결과 순으로 먼저 쓰기 (사실 기반이므로 불확실성 최소)
3. 그 다음: Ch.1 서론 → Ch.2 이론 → Ch.6 토의 → Ch.7 결론 (서사 기반이므로 결과 확정 후)
4. 마지막: 초록 및 참고문헌·부록

---

## 6. 본 계획에서 **하지 않을** 것 (scope creep 방지)

- K-shape를 "핵심 방법론 혁신"으로 주장하지 않는다
- "Growth 업장이 변동성이 높다"고 쓰지 않는다 (최신 residual volatility 결과에 의해 기각됨)
- Golden cross를 중심 결과로 쓰지 않는다
- 인과 추정(DiD/PSM/IV)을 본 논문에 포함시키지 않는다. 석사논문 scope에서는 diagnostic·predictive framing을 유지. (저널 확장 시 추가)
- Survival analysis·Cox PH를 본 논문의 주요 결과로 끌어올리지 않는다. (부록 또는 향후 연구)
- KDD/ICIS/MISQ 투고를 전제로 한 추가 실험을 벌이지 않는다. 석사학위 완성이 최우선.
