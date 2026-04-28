# 260428 data 폴더 파일 설명

작성일: 2026-04-28

## 1. 전체 구성

`data/` 폴더에는 원자료 2개, 설명 문서 1개, R 시각화 스크립트 1개, 기존 요약 산출물 폴더 1개가 있습니다.

| 파일 | 성격 | 현재 파악한 역할 |
|---|---|---|
| `251214_University_Tech_Commercialization_Panel_DB_Patent_Stock.xlsx` | 핵심 패널 DB | 대학-연도 단위의 기술사업화/연구/특허/TTO/네트워크/지역 변수 |
| `kistep_univ.xlsx` | 특허 협력 원자료 | 대학이 포함된 공동특허/협력특허 건별 자료 |
| `260204_University_Tech_Commercialization_Panel_DB.docx` | 변수 설명 문서 | 재원구성 관련 변수 설명으로 보임 |
| `university_trends_top20.R` | 시각화 스크립트 | 2021년 기술이전 수입 Top 20 대학 추세 그래프 생성 목적 |
| `analysis_output/` | 기존 요약 산출물 | 표준 라이브러리 기반 Excel 요약 결과 |

## 2. `251214_University_Tech_Commercialization_Panel_DB_Patent_Stock.xlsx`

### 데이터 단위

- 핵심 시트: `DB`
- 관측 단위: 대학 x 연도
- 기간: 2007-2023년
- 대학 수: 139개
- 행 수: 2,363행
- 구조: 139개 대학 x 17년 균형 패널

### 주요 변수군

| 변수군 | 대표 변수 | 설명 |
|---|---|---|
| 식별자 | `year`, `schoolname` | 연도, 대학명 |
| 대학 특성 | `est_type`, `regional_dum`, `medical_dum`, `fulltime_faculty`, `understudent_num` | 설립유형, 수도권 여부, 의대 보유 여부, 전임교원 수, 학부생 수 |
| 연구개발비 | `total_rdexp`, `gov_rdexp`, `gov_rdratio`, `private_rdexp`, `privatge_rdratio` | 총 연구비, 정부 연구비, 정부 연구비 비중, 민간 연구비, 민간 연구비 비중 |
| 논문 | `paperkci_num`, `papersci_num`, `tncs`, `p_top10` | KCI/SCI 논문 수, 인용/상위논문 지표 |
| 특허 | `dompatapp_num`, `dompatgrant_num`, `forepatapp_num`, `forepatgrant_num`, `cumgrant_stock`, `pmigrant_stock` | 국내/해외 출원·등록, 특허스톡 |
| TTO | `tto_exp`, `tto_size`, `tto_expert`, `tto_commer` | 기술이전조직 예산, 인력, 전문인력, 사업화 관련 지표 |
| 네트워크 중심성 | `degree`, `closeness`, `betweenness`, `eigenvector`, `katz`, `nscore_centrality` | 대학 협력 네트워크 내 위치 |
| 지역 통제 | `manucompany_num`, `ictcompany_num`, `regional_gdp`, `regionalgdp_deflator`, `oldpop_65` | 지역 제조업/ICT 기업 수, GRDP, 디플레이터, 고령인구 비중 |
| 성과 | `tcp_num`, `tcp_value` | 기술이전 건수, 기술이전 수입 |

### 핵심 수치

- `tcp_num`, `tcp_value`는 결측이 없습니다.
- 전체 기술이전 수입 합계는 2007년 19,924.6573에서 2023년 99,670.9223으로 증가했습니다.
- 2023년 `tcp_value` 상위 대학은 한양대학교, 서울대학교, 연세대학교, 경희대학교, 세종대학교 순입니다.
- `tncs`, `p_top10`은 결측 또는 비수치값이 686건 있습니다.
- TTO 관련 변수에는 결측이 있습니다: `tto_exp` 89건, `tto_size` 548건, `tto_expert` 548건, `tto_commer` 551건.

### 미팅에서 확인할 점

- `tcp_value`의 단위가 무엇인지 확인해야 합니다. R 스크립트에는 “2020년 실질 백만원”처럼 표기되어 있으나, 현재 Excel 자체의 단위 설명을 재확인해야 합니다.
- `total_rdexp`, `gov_rdexp`, `private_rdexp`, `tto_exp`의 단위와 가격 기준연도도 확인해야 합니다.
- `nscore_centrality`가 여러 중심성 지표를 어떻게 결합한 점수인지 확인해야 합니다.
- `cumgrant_stock_3`, `pmistock_3`의 정확한 산식과 3년 창 처리 방식을 확인해야 합니다.
- 0값이 실제 0인지, 관측 불가/미수집을 0으로 넣은 것인지 확인해야 합니다.

## 3. `kistep_univ.xlsx`

### 데이터 단위

- 핵심 시트: `Sheet1`
- 관측 단위: 특허 등록 건
- 기간: 2005-2024년
- 행 수: 41,218건
- 주요 내용: 국가, 등록번호, 등록년도, 정부지원 여부, 협력유형, 특허권자명/국적/유형, IPC 대분류/중분류

### 주요 변수군

| 변수군 | 대표 변수 | 설명 |
|---|---|---|
| 특허 식별 | `국가`, `등록번호`, `등록년도`, `연도구간` | 특허의 국가, 번호, 등록연도 |
| 지원 여부 | `정부지원` | 정부지원 특허 여부 |
| 협력유형 | `협력유형1`-`협력유형4` | 대학-기업, 대학-연구소 등 공동특허 협력 구조 |
| 권리자 | `제1특허권자명`-`제9특허권자명` 및 국적/유형 | 공동권리자 정보 |
| 기술분류 | `대분류`, `중분류` | IPC 또는 기술분류 코드 |

### 핵심 수치

- 국가: KR 35,151건, US 6,067건
- 정부지원: Y 18,378건, N 22,840건
- `협력유형1` 기준 상위 유형: 대학기업 20,236건, 대학연구소 4,309건, 대학대학 4,169건, 기업대학 3,708건
- `협력유형4` 기준: 법인 간 38,824건, 법인-개인 2,394건
- 제1특허권자 상위: 서울대학교, 한국과학기술원, 연세대학교, 삼성전자, 한양대학교
- `Sheet2`, `Sheet3`에는 연도별 대학협력특허 수, 전체특허 수, 비율 요약이 있습니다.

### 미팅에서 확인할 점

- `협력유형1`-`협력유형4`가 각각 어떤 규칙으로 생성된 변수인지 확인해야 합니다.
- `대학기업`과 `기업대학`이 방향성 차이인지, 제1권리자 기준 차이인지 확인해야 합니다.
- `정부지원`의 판정 기준과 출처를 확인해야 합니다.
- 제3특허권자 이후 결측은 대부분 공동권리자 수가 적어서 생긴 구조적 결측으로 보이나, 빈칸 처리 규칙을 확인해야 합니다.
- 특허 원자료와 패널 DB의 학교명 매칭 기준을 확인해야 합니다.

## 4. `260204_University_Tech_Commercialization_Panel_DB.docx`

이 문서는 다음 변수들을 설명합니다.

- `regional_upper`: 대학 소재 광역지자체
- `regional_lower`: 대학 소재 기초지자체
- `intra_rdexp`: 대학의 교내 연구비
- `intra_rdratio`: 대학의 교내 연구비 비중
- `local_rdexp`: 지자체 연구비
- `local_rdratio`: 지자체 연구비 비중
- `foreign_rdexp`: 외국 연구비
- `foreign_rdratio`: 외국 연구비
- `total_eudexp`: 총 교육비
- `univ_grant_exp`: 중앙정부와 지방정부의 재정지원액 합계

중요한 점은 현재 Excel 패널 DB에는 위 변수 중 일부가 보이지 않는다는 것입니다. 따라서 이 DOCX가 현재 `251214_...Patent_Stock.xlsx`의 설명 문서인지, 아니면 별도의 `260204` 재원구성 DB 설명 문서인지 확인해야 합니다.

## 5. `university_trends_top20.R`

이 R 스크립트는 2021년 `tcp_value` 기준 Top 20 대학을 뽑고, 기술이전 수입/건수와 특허활동 추세를 그리는 목적입니다.

주의할 점:

- 현재 스크립트는 Windows 절대경로의 별도 Excel 파일을 읽도록 되어 있습니다.
- 스크립트가 참조하는 `intra_rdratio`, `local_rdratio`, `foreign_rdratio`, `univ_grant_exp` 변수는 현재 `251214_...Patent_Stock.xlsx`의 `DB` 시트에는 없습니다.
- 즉, 현재 데이터 폴더 기준으로 바로 실행 가능한 분석 스크립트라기보다, 이전 또는 다른 버전 DB에 맞춘 시각화 코드로 보는 것이 안전합니다.

## 6. `analysis_output/`

기존 요약 산출물입니다.

- `summary.md`: 파일/시트별 행 수, 열 수, 핵심 신호 요약
- `columns.csv`: 컬럼별 결측, 타입, 고유값 정보
- `numeric_stats.csv`: 수치형 변수의 count/missing/min/mean/median/max
- `categorical_top_values.csv`: 범주형 변수의 상위값
- `brief_ko.md`: 한국어 요약 브리프

오늘 미팅에서는 이 폴더를 원자료 검토의 보조 증거로 사용하면 됩니다.
