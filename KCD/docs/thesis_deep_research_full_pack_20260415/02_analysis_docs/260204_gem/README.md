# 260204_gem — 변곡점 추출 및 P1/P2 라벨링

업장(public_id)별 주별 매출에 대해 **Piecewise Linear Regression(분절 회귀)**로 변곡점을 찾고, P1/P2 구간에 U/D 라벨을 부여합니다.

## 데이터

- **경로**: `../original_data/weekly_processed.parquet` (또는 `weekly.parquet`)
- **컬럼**: `public_id`, `day_after1`(주), `sales_card`(매출)
- 업장당 최대 142주 분량 사용

## 실행

```bash
# 260204_gem 폴더에서
cd 260204_gem
python scripts/run_01_inflection_p1p2.py
```

전체 업장이 많을 경우 테스트용으로 일부만 실행:

```bash
python scripts/run_01_inflection_p1p2.py --limit 500
```

## 로직 요약

1. **변곡점 탐색**: 각 업장별로 가능한 변곡 주(break_week)를 바꿔 가며 두 구간 선형 회귀를 수행하고, **총 RSS가 최소**가 되는 주를 변곡점으로 선택.
2. **P1 / P2**: 변곡점 **이전** = P1, **이후** = P2.
3. **라벨**: P1 기울기 양수 → `P1_label = 'U'`, 음수 → `'D'`. P2도 동일.
4. **변곡점 미발견 시**: 전체 주수의 절반을 기준으로 분할 (142주 기준 **71주**).  
   - 데이터가 적거나, 유효한 변곡 후보가 없을 때 적용.

## 출력

- **테이블**: `outputs/tables/inflection_p1p2_labels.csv`
  - `public_id`, `n_weeks`, `inflection_week`, `P1_label`, `P2_label`, `slope_P1`, `slope_P2`, `used_fallback`
- **로그**: `outputs/logs/run_01_inflection_p1p2.log`

## 설정

`configs/base.yaml`에서 데이터 경로, 컬럼명, 구간 최소 주 수 등을 수정할 수 있습니다.
