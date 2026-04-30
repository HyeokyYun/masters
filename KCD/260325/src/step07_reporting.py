from __future__ import annotations

from pathlib import Path

import pandas as pd

from src import config as cfg


def _load_csv(path: Path) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def _pick_text(df: pd.DataFrame, item: str, default: str = "n/a") -> str:
    if df.empty:
        return default
    match = df.loc[df["item"] == item, "value"]
    if match.empty:
        return default
    return str(match.iloc[0])


def _frame_to_text(df: pd.DataFrame, n: int | None = None) -> str:
    if df.empty:
        return "No output."
    view = df.head(n) if n is not None else df
    return view.to_string(index=False)


def write_summary_report() -> None:
    diagnostics = _load_csv(cfg.TABLE_DIR / "base_dataset_diagnostics.csv")
    volatility_note = _load_csv(cfg.TABLE_DIR / "volatility_selection_note.csv")
    volatility_screen = _load_csv(cfg.TABLE_DIR / "volatility_metric_screening.csv")
    industry_fit = _load_csv(cfg.TABLE_DIR / "industry_competition_model_fit.csv")
    early_summary = _load_csv(cfg.TABLE_DIR / "young_store_outcome_summary.csv")
    nc_fit = _load_csv(cfg.TABLE_DIR / "new_customer_model_fit_comparison.csv")
    full_age_summary = _load_csv(cfg.TABLE_DIR / "full_business_age_summary.csv")
    full_age_inclusion = _load_csv(cfg.TABLE_DIR / "full_age_sample_inclusion_summary.csv")

    preferred_metric = _pick_text(volatility_note, "preferred_metric", "vol_resid_stl13")
    sample_rows = _pick_text(diagnostics, "sample_rows", "0")
    early_share = _pick_text(diagnostics, "early_store_rate", "0")
    full_store_count = _pick_text(full_age_summary, "full_meta_store_count", "n/a")
    full_age_median = _pick_text(full_age_summary, "full_age_months_median", "n/a")

    top_vol = _frame_to_text(volatility_screen, 3)
    model_fit_text = _frame_to_text(industry_fit)
    early_text = _frame_to_text(early_summary)
    nc_fit_text = _frame_to_text(nc_fit)
    full_age_inclusion_text = _frame_to_text(full_age_inclusion)

    summary = f"""# 260325 TODO 진행 요약

## 이번 폴더에서 진행한 항목

1. 매출 변동성을 평균 기준 CV에서 추세조정 잔차 기반 지표로 다시 비교했습니다.
2. 업종 효과를 `Growth / Stable / Decline` 기준으로 다시 요약했습니다.
3. 동 단위 동일업종 비중을 경쟁 밀도 변수로 만들었습니다.
4. 패스트푸드/카페/술집과 지역 경쟁도의 인터랙션 항을 추가했습니다.
5. 업력 분포를 시각화하고 초기 업장(`<= 12개월`) 서브샘플을 분리했습니다.
6. 초기 업장 중 성장 업장의 특징을 별도 비교하고 로짓으로 점검했습니다.
7. 신규 고객 비율 해석을 강화하기 위해 분위 분석과 모델 비교를 추가했습니다.
8. 전체 meta 업장을 기준으로 한 `전체 업력` 분석을 별도로 추가했습니다.

## 기본 정보

- 현재 분석 표본 수: {sample_rows}
- 초기 업장 비율(<=12개월): {early_share}
- 추천 변동성 정의: {preferred_metric}
- 전체 meta 업장 수: {full_store_count}
- 전체 업력 중앙값(개월): {full_age_median}

## 변동성 스크리닝 상위 결과

{top_vol}

## 업종/경쟁/인터랙션 모델 적합도

{model_fit_text}

## 초기 업장 요약

{early_text}

## 신규 고객 비율 모델 비교

{nc_fit_text}

## 전체 업력 구간별 분석 표본 포함률

{full_age_inclusion_text}

## 주요 산출물

- `outputs/tables/base_dataset.csv`
- `outputs/tables/volatility_candidates.csv`
- `outputs/tables/industry_effect_detail.csv`
- `outputs/tables/competition_density_summary.csv`
- `outputs/tables/business_age_bucket_summary.csv`
- `outputs/tables/full_business_age_bucket_summary.csv`
- `outputs/tables/full_age_sample_inclusion_summary.csv`
- `outputs/tables/young_store_growth_vs_others.csv`
- `outputs/tables/new_customer_quantile_summary.csv`
- `outputs/figures/volatility_comparison.png`
- `outputs/figures/industry_competition_overview.png`
- `outputs/figures/business_age_overview.png`
- `outputs/figures/full_business_age_overview.png`
- `outputs/figures/new_customer_overview.png`
"""

    with open(cfg.DOC_DIR / "summary.md", "w", encoding="utf-8") as handle:
        handle.write(summary)
