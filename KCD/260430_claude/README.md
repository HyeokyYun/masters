# 260430_claude — Seasonality-Matched Rolling Window Pipeline

2026-04-30 개인 미팅 후속 분석. 지도교수가 명시적으로 요청한 두 가지를 실행한다.

1. feature window와 target window를 **같은 캘린더 월**로 맞춘 롤링 윈도우 분석.
   현재 파이프라인은 항상 2023년 6–8월(여름 휴가)을 라벨 구간으로 사용해
   시즈널리티가 라이프사이클 신호와 confound 된다.
2. 시즈널 라벨 기준으로 메인 모델(베이스라인 vs +클러스터+체인지포인트) 재학습.

LEVI / EWS / 외부 공공 데이터 / 도시경제 활력 지수는 본 폴더 범위 밖이다.

## 디렉토리

```
260430_claude/
  src/
    config.py
    utils_panel.py
    step01_build_seasonal_panels.py
    step02_relabel_gsd_calendar.py
    step03_extract_features.py
    step04_evaluate_seasonal_baseline.py
    step05_train_main_model.py
  outputs/
    tables/
    figures/
  docs/
    260430_claude_design.md
    260430_claude_rolling_results.md
    260430_claude_main_model_results.md
```

## 실행 순서

```bash
cd /home/hyeoky98/kcd
python 260430_claude/src/step01_build_seasonal_panels.py
python 260430_claude/src/step02_relabel_gsd_calendar.py
python 260430_claude/src/step03_extract_features.py
python 260430_claude/src/step04_evaluate_seasonal_baseline.py
python 260430_claude/src/step05_train_main_model.py
```

각 스크립트는 `--combo_id` 또는 (`--start_year`, `--start_month`, `--window_months`) 인자로
단일 조합만 재현할 수 있다.

## 컴비네이션 정의

- `start_year ∈ {2021, 2022}`
- `start_month ∈ {1, …, 12}`
- `window_months ∈ {1, 2, 3}` (각각 ≈ 4 / 8 / 13 주)
- `target_year_offset ∈ {1, 2}` — feature 윈도우 시작에서 1년 후, 2년 후의 같은 달
- 데이터 범위 (2021-01-01 ~ 2023-08-28) 안에서 target window가 완전히 포함되는
  조합만 남긴다.

## 데이터 소스

- `original_data/weekly.parquet` — 6.58M 점포-주차, 142주.
- `original_data/meta.csv` — 59K 점포 메타.

## 참조 (read-only)

- `top_tier/src/step00_prepare_original_panel.py` — `slope_all_mm` 라벨 로직.
- `top_tier/src/step03_prediction_model.py` — 30주 피처 (가변 윈도우용으로 변형).
- `top_tier/src/step10_hybrid_prediction.py` — 클러스터 + 체인지포인트.
