# 제3장 데이터

## 3.1 데이터 출처

본 연구는 한국신용데이터(KCD) 가 보유한 서울시 외식업 점포의 주간 카드
거래 패널을 사용한다. 두 개 파일로 구성된다.

- `original_data/weekly.parquet` — 점포-주차 단위 패널. 약 658 만 행, 점포
  약 5만 9천 개, 주차 142 개(2021-01-01 ~ 2023-08-28). 각 행은 한 점포의
  한 주의 거래 합계.
- `original_data/meta.csv` — 점포 단위 메타. 약 5만 9천 행. 개점월, 업종
  분류, 주소(시·도·시·군·구·동), 영업 면적, 배달 지원 여부 등.

데이터는 가맹점 약관에 따라 점포 단위로 익명화돼 있으며, 점포 ID
(`public_id`) 를 키로 weekly 와 meta 가 결합된다. 본 연구는 어떠한 식별
가능 점포 정보(상호, 대표자명, 정확 주소)도 사용하지 않는다.

## 3.2 변수 정의

### 3.2.1 weekly.parquet 핵심 변수

| 컬럼 | 타입 | 정의 |
| --- | --- | --- |
| `public_id` | int32 | 점포 익명 ID |
| `date_id` | string → datetime | 주차 시작 일자(주 단위 라벨) |
| `sales_card` | int64 | 카드 결제 매출 합계(원) |
| `sales_invoice` | int64 | 세금계산서 발행 매출 |
| `sales_delivery` | int64 | 배달 채널 매출 |
| `customer` | int64 | 고객 수(중복 포함 결제 건 수 기반) |
| `customer_new` | int64 | 신규 고객 수 |
| `before_noon_sales` | float64 | 정오 이전 매출 |
| `after_noon_sales` | float64 | 정오 이후 매출 |
| `weekend_sales` | float64 | 주말(토·일) 매출 |
| `purchase_card` | int64 | 점포의 카드 매입 |

본 연구의 1 차 종속/입력 변수는 `sales_card` 이다. 보조 변수 `customer`,
`customer_new`, `sales_delivery`, `before_noon_sales`, `weekend_sales` 는
피처 추출에 사용된다. `purchase_*` 는 본 연구의 분석 범위 밖이다.

### 3.2.2 meta.csv 핵심 변수

| 컬럼 | 타입 | 정의 |
| --- | --- | --- |
| `public_id` | int64 | 점포 익명 ID |
| `open_month` | string | 개점월(YYYY-MM) |
| `classification__kcd_v3__depth_2_name` | object | KCD v3 분류 depth-2 |
| `dong` | object | 행정동 |
| `sigungu` | object | 시·군·구 |
| `sido` | object | 시·도(서울시) |
| `business_square_size` | float64 | 영업 면적(㎡) |
| `delivery_link` | int64 | 배달 플랫폼 연동 여부(0/1) |

분석에서는 `classification__kcd_v3__depth_2_name` 을 카페 / 베이커리·디저트 /
술집 / 한식 / 일식 / 양식 / 중식 / 분식 / 패스트푸드 / 기타 외식업의 10 개
범주로 재분류한다(`top_tier/src/step00_prepare_original_panel.py:_category`).

## 3.3 전처리

본 연구는 `260430_claude/src/step01_build_seasonal_panels.py` 의 절차를
따른다.

1. **점포 필터.** 데이터 범위(2021-01-01 ~ 2023-08-28) 안에서 관측된
   점포만 사용. 점포-주차 단위 패널을 캘린더 윈도우(§3.5)로 슬라이스한
   후, feature window 와 target window 모두에서 일정 비율 이상의 주차가
   관측된 점포만 분석에 포함한다(`MIN_FEATURE_WEEKS_RATIO = 0.6`,
   `MIN_TARGET_WEEKS_RATIO = 0.6`).
2. **음수 매출 처리.** `sales_card < 0` 은 환불 등으로 발생하는 음수
   매출이므로 NaN 으로 치환한 뒤 점포별 선형 보간(`top_tier/src/
   step00_prepare_original_panel.py` 의 처리와 동일).
3. **결측 보조 변수 처리.** `customer`, `customer_new`, `sales_delivery`,
   `before_noon_sales`, `weekend_sales` 는 결측을 0 으로 대체.
4. **정규화.** 점포별 매출 추세를 점포 평균으로 나눠 정규화 매출을
   생성한다(`260430_claude/src/step02_relabel_gsd_calendar.py`). 이 정규화
   매출의 OLS 기울기로 G/S/D 라벨을 정의한다(§4.3).
5. **점포 매출 0 필터.** feature window 와 target window 안에서 매출 합이
   0 인 점포는 폐업·휴업으로 간주해 분석에서 제외한다.

## 3.4 데이터 범위와 한계

- **시간 범위.** 2021-01-01 ~ 2023-08-28 (142 주). 코로나 확산기(2021)와
  엔데믹 회복기(2022 ~ 2023 상반기) 가 모두 포함된다.
- **컷오프 효과.** 데이터가 2023-08-28 에 끝나므로, target window 가
  2023 년 6 ~ 8 월에 가까운 specification 일수록 휴가 시즌 매출 하락이
  라벨에 들어가 Decline 비율이 인위적으로 증가한다(§5.1).
- **외식업 한정.** 본 데이터는 외식업(요식업) 점포만 포함한다. 도소매·
  서비스업 점포의 라이프사이클은 본 연구의 일반화 범위 밖이다.
- **현금 결제 누락.** 카드 매출만 관측되므로 현금 매출 비중이 큰 점포의
  실 매출은 과소 추정된다. 단, 본 연구는 점포의 절대 매출이 아니라 상대
  추세(기울기)를 라벨/피처로 사용하므로 이 누락의 영향은 제한적이다.
- **결측 점포 / 짧은 관측.** 26 주 미만 관측된 점포는 분석에서 제외된다
  (`260430_claude/src/config.py:MIN_PANEL_WEEKS = 26`). 이 필터로 약 8천 개
  점포가 빠지며, 본 연구 모집단은 약 5만 1천 개 점포 수준이다.

## 3.5 Specification 카탈로그

데이터 범위 안에서 다음 4 개 차원의 specification 이 분석 대상이다.

- `start_year ∈ {2021, 2022}` (2 개)
- `start_month ∈ {1, 2, …, 12}` (12 개)
- `window_months ∈ {1, 2, 3, 4, 6, 7}` (6 개; 약 4 / 8 / 13 / 18 / 26 / 31
  주)
- `target_offset ∈ {1, 2}` (2 개; 1 년 후 / 2 년 후 같은 캘린더 월)

총 후보는 2 × 12 × 6 × 2 = 288 개이지만, target window 가 데이터 컷오프
(2023-08-28) 를 넘는 specification 은 panel 구성 단계(`step01`) 에서 0 개
점포로 떨어지고, 데이터 범위 안에서 살아남는 specification 은 약 145 개
(panel) 다. 짧은 윈도우(1 / 2 / 3 개월) 80 개와 확장 윈도우(4 / 6 / 7
개월) 65 개 가량으로 분포한다. 자세한 panel 별 점포 수와 라벨 분포는
`260430_claude/outputs/tables/panel_summary.csv`,
`label_distribution.csv` 에서 확인할 수 있다(§5.1).

## 3.6 본 장 요약

KCD weekly + meta 패널은 점포 단위 거래 추세를 142 주 동안 관측한 사실상
유일한 비행정 데이터다. 본 연구는 이 데이터를 점포-주차 단위 패널로 정렬한
후, §4 에서 시즌 정렬 rolling-window 로 specification 을 정의해 G/S/D
라벨과 피처를 추출한다. 데이터 컷오프, 외식업 한정, 현금 결제 누락의
세 가지가 결과 해석의 가장 큰 데이터 측면 한계다.
