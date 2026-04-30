from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src import config as cfg


FEATURES = [
    "trend_slope",
    "cv",
    "mdd",
    "nc_rate",
    "del_ratio_log",
    "before_noon",
    "weekend",
    "delivery_link",
    "business_square_size",
]

FEATURE_LABELS = {
    "trend_slope": "매출 추세",
    "cv": "기존 변동성(CV)",
    "mdd": "최대 낙폭(MDD)",
    "nc_rate": "신규 고객 비율",
    "del_ratio_log": "배달 비중(log)",
    "before_noon": "오전 매출 비중",
    "weekend": "주말 매출 비중",
    "delivery_link": "배달앱 입점",
    "business_square_size": "점포 면적",
}

BUCKET_LABELS = {
    "0_12m": "0~12개월",
    "12_24m": "12~24개월",
    "24_36m": "24~36개월",
    "36_60m": "36~60개월",
    "60_120m": "60~120개월",
    "120m_plus": "120개월+",
}


def _standardize(series: pd.Series) -> pd.Series:
    series = pd.to_numeric(series, errors="coerce")
    median = series.median()
    series = series.fillna(median)
    lower = series.quantile(0.01)
    upper = series.quantile(0.99)
    series = series.clip(lower=lower, upper=upper)
    std = series.std()
    if pd.notna(std) and std > 1e-12:
        return (series - series.mean()) / std
    return pd.Series(np.zeros(len(series)), index=series.index)


def _interpret_signal(row: pd.Series) -> str:
    growth_sig = row["growth_pvalue"] < 0.05
    decline_sig = row["decline_pvalue"] < 0.05
    growth_coef = row["growth_coef"]
    decline_coef = row["decline_coef"]

    if growth_sig and decline_sig and growth_coef > 0 and decline_coef < 0:
        return "Growth 쪽으로 강하고 Decline은 억제"
    if growth_sig and decline_sig and growth_coef > 0 and decline_coef > 0:
        return "Stable보다 Growth/Decline 같은 동적 상태와 연결"
    if growth_sig and decline_sig and growth_coef < 0 and decline_coef < 0:
        return "Growth와 Decline 모두 낮아져 Stable 쪽과 연결"
    if growth_sig and growth_coef > 0:
        return "Growth 쪽과 연결"
    if growth_sig and growth_coef < 0:
        return "Growth를 억제"
    if decline_sig and decline_coef > 0:
        return "Decline 쪽과 연결"
    if decline_sig and decline_coef < 0:
        return "Stable 쪽과 연결"
    return "강한 신호는 아님"


def _bucket_top_note(bucket_code: str, ranked: pd.DataFrame) -> str:
    bucket_label = BUCKET_LABELS.get(bucket_code, bucket_code)
    top = ranked.sort_values("importance_score", ascending=False).head(4)
    lines = [f"## {bucket_label}"]
    for row in top.itertuples():
        lines.append(
            f"- `{row.feature_label}`: Growth coef `{row.growth_coef:.3f}`, "
            f"Decline coef `{row.decline_coef:.3f}`, 해석은 `{row.interpretation}`"
        )
    return "\n".join(lines)


def run_bucket_feature_importance() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(cfg.TABLE_DIR / "fullsample_age_analysis_table.csv")

    all_rows: list[dict[str, object]] = []
    top_rows: list[dict[str, object]] = []
    fit_rows: list[dict[str, object]] = []
    notes: list[str] = []

    for bucket_code in cfg.FULL_AGE_BUCKET_LABELS:
        subset = df[df["full_age_bucket"] == bucket_code].copy()
        if subset.empty:
            continue

        work = subset[["outcome_3"] + FEATURES].dropna(subset=["outcome_3"]).copy()
        for feature in FEATURES:
            work[feature] = _standardize(work[feature])

        y = pd.Categorical(work["outcome_3"], categories=cfg.OUTCOME_ORDER, ordered=True)
        work = work[y.codes >= 0].copy()
        y = pd.Categorical(work["outcome_3"], categories=cfg.OUTCOME_ORDER, ordered=True)
        X = sm.add_constant(work[FEATURES].astype(float), has_constant="add")

        result = sm.MNLogit(y.codes, X).fit(method="lbfgs", maxiter=500, disp=False)

        params = result.params.copy()
        pvalues = result.pvalues.copy()
        params.columns = ["growth_coef", "decline_coef"]
        pvalues.columns = ["growth_pvalue", "decline_pvalue"]
        ranked = pd.concat([params, pvalues], axis=1).loc[FEATURES].reset_index().rename(columns={"index": "feature"})
        ranked["bucket_code"] = bucket_code
        ranked["bucket_label"] = BUCKET_LABELS.get(bucket_code, bucket_code)
        ranked["feature_label"] = ranked["feature"].map(FEATURE_LABELS)
        ranked["importance_score"] = (
            ranked[["growth_coef", "decline_coef"]].abs().max(axis=1)
            * (-np.log10(ranked[["growth_pvalue", "decline_pvalue"]].min(axis=1) + 1e-12))
        )
        ranked["interpretation"] = ranked.apply(_interpret_signal, axis=1)
        ranked = ranked.sort_values("importance_score", ascending=False).reset_index(drop=True)

        for rank, row in enumerate(ranked.itertuples(), start=1):
            all_rows.append(
                {
                    "bucket_code": row.bucket_code,
                    "bucket_label": row.bucket_label,
                    "rank_within_bucket": rank,
                    "feature": row.feature,
                    "feature_label": row.feature_label,
                    "growth_coef": row.growth_coef,
                    "growth_pvalue": row.growth_pvalue,
                    "decline_coef": row.decline_coef,
                    "decline_pvalue": row.decline_pvalue,
                    "importance_score": row.importance_score,
                    "interpretation": row.interpretation,
                }
            )

        top_ranked = ranked.head(5).copy()
        for rank, row in enumerate(top_ranked.itertuples(), start=1):
            top_rows.append(
                {
                    "bucket_code": row.bucket_code,
                    "bucket_label": row.bucket_label,
                    "rank_within_bucket": rank,
                    "feature": row.feature,
                    "feature_label": row.feature_label,
                    "importance_score": row.importance_score,
                    "growth_coef": row.growth_coef,
                    "decline_coef": row.decline_coef,
                    "interpretation": row.interpretation,
                }
            )

        counts = subset["outcome_3"].value_counts()
        total = counts.sum()
        fit_rows.append(
            {
                "bucket_code": bucket_code,
                "bucket_label": BUCKET_LABELS.get(bucket_code, bucket_code),
                "nobs": float(result.nobs),
                "pseudo_r2": float(result.prsquared),
                "growth_share": float(counts.get("Growth", 0) / total),
                "stable_share": float(counts.get("Stable", 0) / total),
                "decline_share": float(counts.get("Decline", 0) / total),
            }
        )
        notes.append(_bucket_top_note(bucket_code, ranked))

    importance_df = pd.DataFrame(all_rows)
    top_df = pd.DataFrame(top_rows)
    fit_df = pd.DataFrame(fit_rows)

    importance_df.to_csv(
        cfg.TABLE_DIR / "fullsample_age_bucket_feature_importance.csv",
        index=False,
        encoding="utf-8-sig",
    )
    top_df.to_csv(
        cfg.TABLE_DIR / "fullsample_age_bucket_feature_top5.csv",
        index=False,
        encoding="utf-8-sig",
    )
    fit_df.to_csv(
        cfg.TABLE_DIR / "fullsample_age_bucket_feature_model_fit.csv",
        index=False,
        encoding="utf-8-sig",
    )

    note = """# 업력 구간별 핵심 feature 메모

아래 결과는 전체 업장 observed-window 표본에서 업력 구간별로 `Growth / Stable / Decline`을 구분하는 feature를 따로 본 것입니다.

- 분석 표본: `50,635개`
- 종속변수: `outcome_3`
- 방법: 업력 구간별 다항 로짓(MNLogit)
- 사용 feature: `매출 추세`, `기존 변동성(CV)`, `최대 낙폭(MDD)`, `신규 고객 비율`, `배달 비중(log)`, `오전 매출 비중`, `주말 매출 비중`, `배달앱 입점`, `점포 면적`
- `n_observed_weeks_used`는 관측 구조 영향이 커서 해석용 중요도 표에서는 제외했습니다.

""" + "\n\n".join(notes) + "\n"

    with open(cfg.DOC_DIR / "age_bucket_feature_note.md", "w", encoding="utf-8") as handle:
        handle.write(note)

    return importance_df, top_df, fit_df
