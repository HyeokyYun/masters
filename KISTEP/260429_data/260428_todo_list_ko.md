# 260428 미팅 후 할 일 목록

작성일: 2026-04-28

## A. 바로 진행할 작업

### A1. 3극 특허 기술통계

- `251022 대학특허권자연구주체검증완료본-한국(전주경).xlsx`의 `DB` 시트를 사용한다.
- `삼극특허_현황` 컬럼을 기준으로 3극 특허 여부를 판정한다.
- 연도별, 대학별, 기술 대분류ㆍ중분류별, 정부지원 여부별, 권리자 유형 조합별 3극 특허 비중을 만든다.
- 139개 대학 패널DB 목록과 매칭되는 특허 subset을 따로 표시한다.
- 산출물은 `outputs_260428/tables/`와 `outputs_260428/docs/`에 저장한다.

### A2. 최신 패널DB v4 결측 진단 및 imputation 설계

- `260204 대학기술사업화패널DB-재원구성(엄익천)v4.xlsx`의 `DB` 시트를 기준으로 한다.
- 2007-2023년, 139개 대학 패널 구조를 확인한다.
- 변수별 결측률, 연도별 결측률, 대학별 결측률을 만든다.
- 네트워크 중심성 변수는 별도 표시하고, 우선 분석용 패널에서는 제외 후보로 둔다.
- 변수군별 결측 처리 원칙과 변수별 추천 imputation 방식을 문서화한다.
- 기존 `university_panel_imputed_2013_2021.xlsx`와 기간ㆍ변수 차이를 요약한다.

### A3. 네트워크 입력 데이터 초안

- 특허 원자료의 1-16번째 특허권자명, 국적, 유형을 사용한다.
- 139개 대학 목록에 포함되는 대학만 기준 대학으로 둔다.
- 대학-기업 two-mode edge list를 만든다.
- 동일 특허에 복수 대학이 있으면 대학-대학 one-mode edge list를 만든다.
- 연도별 edge count와 필터링 로그를 만든다.
- 이 단계에서는 중심성 계산까지 하지 않고, TERGM/네트워크 분석에 넣을 수 있는 입력 초안 생성까지만 한다.

## B. 외부 조회 또는 데이터 제공자 확인 후 진행할 작업

### B1. 발명자 정보 보강

- 현재 원자료에는 `발명자수`만 있고 발명자 이름 목록은 없다.
- KIPRIS/특허청 API 또는 원자료 제공자의 추가 추출이 필요하다.
- 우선 등록번호, 국가, kipro 번호로 조회 가능한지 확인하고, 필요한 필드 목록을 정리한다.

### B2. 특허 갱신상태 보강

- 현재 원자료에는 `생존지수`가 있지만 연차료 납부 이력이나 갱신 중단 연도는 없다.
- 권리 유지/소멸 상태를 등록번호 기준으로 조회할 수 있는지 확인해야 한다.
- 한국 특허 갱신비는 비용 신호가 약하다는 한계를 같이 문서화한다.

### B3. 대학 랭킹 자료 활용 검토

- Leiden Ranking은 평판 변수라기보다 논문 성과 기반 지표로 해석한다.
- THE/QS/중앙일보 랭킹처럼 평판 요소가 섞인 자료와 구분한다.
- 네트워크 형성 모형에서 지위, 모방, 성과 stratification 변수로 쓸 수 있는지 검토한다.

## C. 이번 1차 실행의 산출물

- `outputs_260428/src/run_260428_tasks.py`
- `outputs_260428/tables/01_triadic_by_year.csv`
- `outputs_260428/tables/02_triadic_by_university.csv`
- `outputs_260428/tables/03_triadic_by_technology.csv`
- `outputs_260428/tables/04_triadic_by_support_and_owner_type.csv`
- `outputs_260428/tables/05_panel_missing_by_variable.csv`
- `outputs_260428/tables/06_panel_missing_by_year.csv`
- `outputs_260428/tables/07_panel_missing_by_university.csv`
- `outputs_260428/tables/08_network_two_mode_edges.csv`
- `outputs_260428/tables/09_network_one_mode_edges.csv`
- `outputs_260428/tables/10_network_year_summary.csv`
- `outputs_260428/docs/260428_initial_results_ko.md`
- `outputs_260428/docs/260428_imputation_memo_ko.md`
- `outputs_260428/docs/260428_data_request_memo_ko.md`
