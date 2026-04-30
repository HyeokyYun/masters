# 260320_cur — 개별미팅(2026-03-20) 후속 분석

## 목적

`260301` 다항 로짓 결과에 대한 교수님 피드백을 반영:

- **추세 대비 잔차** 기준으로 매출 변동성 재정의
- **동 단위 업종 밀도** 및 **업종×밀도 상호작용**
- **대표 연령** 통제 (meta `age` 파싱)
- **업력 구간별 서브샘플** 재추정
- 업력 분포 **히스토그램**
- 조기예측 문헌 기준 **조사 가이드** (`docs/forecasting_literature_notes.md`)

## 미구현 / 한계

- **프랜차이즈 여부**: 데이터 품질 이슈로 미포함
- **성별**: `meta.csv`에 컬럼 없음 — 병합 데이터 확보 시 추가

## 실행

```bash
python 260320_cur/run_all.py
```

또는 단계별 스크립트는 `docs/meeting_notes_260320.md` 참고.

## 출력

- `outputs/tables/store_trend_residual_cv.csv` — 점포별 추세 잔차 CV
- `outputs/tables/df_extended_for_regression.csv` — 밀도·연령·잔차 CV 병합
- `outputs/tables/multinomial_logit_ext_ref_*.txt` — 확장 다항 로짓
- `outputs/tables/mnlogit_subsample_*_ref_Stable.txt` — 업력 서브샘플
- `outputs/figures/business_age_histogram.png` — 업력 분포

## 의존성

- `pandas`, `numpy`, `statsmodels`
- `run_01`은 `pyarrow` 또는 `fastparquet` (parquet 읽기)
- `run_05` 그림: `matplotlib`
