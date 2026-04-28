# 대학-기업 공동특허와 기술사업화 성과 분석

생성일: 2026-04-27 05:37:13 UTC

## Executive Summary

- 패널 DB는 139개 대학, 2007-2023년, 2,363개 대학-연도 관측치다.
- 특허 원자료는 2005-2024년, 41,218건이다.
- 특허권자 유형이 대학인 이름 47,147회 중 패널 대학명과 정확히 매칭된 것은 45,763회다. 고유 이름 기준 138개 패널 대학이 매칭됐고, 패널 대학 중 미등장 대학은 용인대학교 1개다.
- 전체 패널 대학의 기업공동특허 합계는 2007년 511건에서 2023년 1924건으로 변했다.
- 기술이전 수입 합계는 2007년 19924.6573에서 2023년 99670.9223로 증가했다.
- 이 분석은 인과효과 식별이 아니라, 연구질문을 정교화하기 위한 기술통계, 시차상관, 집단차이, 양방향 고정효과 기반의 연관성 분석이다.

## 분석 이름과 산출물

1. `01_data_coverage_and_matching`: 원자료 범위, 대학명 매칭률, 미매칭 대학명 점검
2. `02_patent_collaboration_trends`: 연도별 공동특허, 기업협력, 정부지원, 대기업협력 추세
3. `03_university_year_collaboration_panel`: 대학-연도 단위 기업협력 특허 패널 구축
4. `04_merged_panel_for_modeling`: 기존 기술사업화 패널과 공동특허 패널 병합
5. `05_lagged_association_analysis`: 공동특허와 기술이전/연구비/논문/중심성의 동시 및 1-3년 후 상관
6. `06_group_comparison_analysis`: 수도권/지방, 국공립/사립, 의대 여부, Top20 여부 비교
7. `07_revenue_paradox_analysis`: 협력은 많지만 기술이전 수입은 낮은 대학, 반대 사례 탐색
8. `08_two_way_fixed_effects_models`: 대학 및 연도 고정효과를 제거한 패널 연관성 분석
9. `09_partner_and_technology_concentration`: 기업 파트너와 IPC 기술분야 집중도 분석

## 주요 결과

### 1. 대학명 매칭

- 패널 대학 139개 중 특허 데이터에서 정확히 등장한 대학은 138개다.
- 미매칭 대학 유형명은 168개, 1,384회다. 대부분 전문대/보건대/패널 외 대학이다.
- 따라서 현재 패널 DB와 특허 원자료의 병합은 대학명 exact match만으로도 충분히 높은 신뢰도를 갖는다.

### 2. 상위 협력 대학

- 1. 서울대학교: 기업공동특허 2657건, 기술이전수입 80604.5926, 지역=수도권
- 2. 한국과학기술원: 기업공동특허 2326건, 기술이전수입 67087.3907, 지역=지방
- 3. 연세대학교: 기업공동특허 1720건, 기술이전수입 59048.6117, 지역=수도권
- 4. 한양대학교: 기업공동특허 1167건, 기술이전수입 89924.4649, 지역=수도권
- 5. 성균관대학교: 기업공동특허 1154건, 기술이전수입 55157.0009, 지역=수도권
- 6. 포항공과대학교: 기업공동특허 1124건, 기술이전수입 37790.2668, 지역=지방
- 7. 고려대학교: 기업공동특허 1008건, 기술이전수입 54578.8539, 지역=수도권
- 8. 울산대학교: 기업공동특허 686건, 기술이전수입 9205.7572, 지역=지방
- 9. 경희대학교: 기업공동특허 482건, 기술이전수입 46747.9458, 지역=수도권
- 10. 울산과학기술원: 기업공동특허 459건, 기술이전수입 11388.3334, 지역=지방

### 3. 공동특허와 성과의 상관

- `collab_patent_count` vs `total_rdexp` +0년: Pearson=0.8847, Spearman=0.784, n=2363
- `collab_patent_count` vs `total_rdexp` +1년: Pearson=0.8781, Spearman=0.7753, n=2224
- `firm_partner_count_unique` vs `total_rdexp` +0년: Pearson=0.8699, Spearman=0.7348, n=2363
- `firm_collab_patent_count` vs `total_rdexp` +0년: Pearson=0.8636, Spearman=0.7267, n=2363
- `firm_partner_count_unique` vs `total_rdexp` +1년: Pearson=0.8595, Spearman=0.7255, n=2224
- `firm_collab_patent_count` vs `total_rdexp` +1년: Pearson=0.8578, Spearman=0.7181, n=2224
- `collab_patent_count` vs `private_rdexp` +0년: Pearson=0.8511, Spearman=0.7324, n=2363
- `gov_supported_collab_count` vs `total_rdexp` +0년: Pearson=0.8482, Spearman=0.761, n=2363
- `collab_patent_count` vs `private_rdexp` +1년: Pearson=0.8461, Spearman=0.7279, n=2224
- `gov_supported_collab_count` vs `total_rdexp` +1년: Pearson=0.8402, Spearman=0.7507, n=2224
- `firm_collab_patent_count` vs `private_rdexp` +0년: Pearson=0.8395, Spearman=0.6776, n=2363
- `firm_collab_patent_count` vs `private_rdexp` +1년: Pearson=0.838, Spearman=0.6731, n=2224

### 4. 양방향 고정효과 모델의 핵심 계수

- M1_transfer_revenue: lagged firm collaboration coefficient=-0.031357, SE=0.043448, t=-0.7217, n=2139, within R2=0.0234
- M2_transfer_cases: lagged firm collaboration coefficient=0.069468, SE=0.024859, t=2.7945, n=2139, within R2=0.026
- M3_private_research_funding: lagged firm collaboration coefficient=0.030368, SE=0.036177, t=0.8394, n=2224, within R2=0.1244
- M4_sci_papers: lagged firm collaboration coefficient=-0.020174, SE=0.014174, t=-1.4234, n=2224, within R2=0.1746
- M5_network_centrality: lagged firm collaboration coefficient=0.620344, SE=0.105084, t=5.9033, n=1676, within R2=0.0302

### 5. 수익성 역설 후보

- high_collaboration_low_revenue: 국립공주대학교 (기업공동특허 182건, 기술이전수입 3382.0586, 지역=지방)

## 해석 기준

- `firm_collab_patent_count`는 한 특허에 패널 대학과 기업 특허권자가 함께 있는 경우를 해당 대학에 배정한 값이다.
- 한 특허에 복수 대학이 있으면 각 패널 대학에 1건씩 집계된다. 따라서 대학별 합계는 특허 원자료 행 수보다 커질 수 있다.
- `large_firm_collab_patent_count`는 기업명 키워드 기반 휴리스틱이다. 대기업 여부 공식 분류가 아니므로 보조 지표로만 사용해야 한다.
- 고정효과 모델은 대학 불변 특성과 연도 공통 충격을 제거하지만, 역인과와 누락변수 문제를 완전히 해결하지 않는다.

## 연구질문에 대한 현재 데이터 기반 판단

현재 데이터는 취업률, 학생 유입, 평판을 직접 측정하지 않는다. 따라서 그 부분은 직접 검증할 수 없다. 대신 연구비, 논문, 기술이전 성과, 네트워크 중심성은 측정 가능하다.

가장 방어 가능한 연구 질문은 다음이다.

> 대학-기업 공동특허 협력은 기술이전 수익보다 연구비 확보, 연구성과, 네트워크 지위와 더 강하게 연결되는가?

이 질문은 현재 생성된 `05_lagged_association_analysis.csv`와 `08_two_way_fixed_effects_models.csv`를 중심으로 검토하면 된다.

## 다음 단계

- 교수님 미팅용으로는 `research_report_ko.md`, `05_lagged_association_analysis.csv`, `06_group_differences.csv`, `07_revenue_paradox_cases.csv`, `08_two_way_fixed_effects_models.csv`만 먼저 보면 된다.
- 논문화하려면 대기업 분류를 공식 기업규모 데이터로 대체하고, 공동특허의 출원/등록 시차와 기술이전 수입 발생 시차를 더 엄밀히 설정해야 한다.
