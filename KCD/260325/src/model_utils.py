from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src import config as cfg


def winsorize_series(series: pd.Series, lower: float = 0.01, upper: float = 0.99) -> pd.Series:
    low = series.quantile(lower)
    high = series.quantile(upper)
    return series.clip(lower=low, upper=high)


def standardize_numeric_frame(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    for column in columns:
        if column not in out.columns:
            continue
        series = pd.to_numeric(out[column], errors="coerce")
        median = series.median()
        series = series.fillna(median)
        series = winsorize_series(series)
        std = series.std()
        if pd.notna(std) and std > 1e-12:
            out[column] = (series - series.mean()) / std
        else:
            out[column] = 0.0
    return out


def fit_outcome_mnlogit(
    df: pd.DataFrame,
    predictors: list[str],
    out_prefix: str,
    label_col: str = "outcome_3",
) -> pd.DataFrame:
    work = df[[label_col] + predictors].copy()
    work = work.dropna(subset=[label_col]).copy()

    numeric_predictors = [column for column in predictors if work[column].dtype.kind in {"i", "u", "f", "b"}]
    work = standardize_numeric_frame(work, numeric_predictors)

    for column in predictors:
        if column not in numeric_predictors:
            work[column] = work[column].fillna(0)

    categories = list(cfg.OUTCOME_ORDER)
    y = pd.Categorical(work[label_col], categories=categories, ordered=True)
    work = work[y.codes >= 0].copy()
    y = pd.Categorical(work[label_col], categories=categories, ordered=True)

    X = sm.add_constant(work[predictors].astype(float), has_constant="add")
    model = sm.MNLogit(y.codes, X)
    result = model.fit(method="lbfgs", maxiter=500, disp=False)

    params = result.params.copy()
    pvalues = result.pvalues.copy()
    target_names = categories[1:]
    params.columns = [f"{name}_coef" for name in target_names]
    pvalues.columns = [f"{name}_pvalue" for name in target_names]
    coef_table = pd.concat([params, pvalues], axis=1).reset_index().rename(columns={"index": "feature"})
    coef_table.to_csv(cfg.TABLE_DIR / f"{out_prefix}_coefficients.csv", index=False, encoding="utf-8-sig")

    fit_table = pd.DataFrame(
        [
            {
                "model_name": out_prefix,
                "nobs": float(result.nobs),
                "pseudo_r2": float(result.prsquared),
                "llf": float(result.llf),
                "aic": float(result.aic),
            }
        ]
    )
    fit_table.to_csv(cfg.TABLE_DIR / f"{out_prefix}_fit.csv", index=False, encoding="utf-8-sig")

    with open(cfg.DOC_DIR / f"{out_prefix}_summary.txt", "w", encoding="utf-8") as handle:
        handle.write(str(result.summary2()))

    return fit_table


def fit_binary_logit(df: pd.DataFrame, target_col: str, predictors: list[str], out_prefix: str) -> pd.DataFrame:
    work = df[[target_col] + predictors].dropna(subset=[target_col]).copy()
    numeric_predictors = [column for column in predictors if work[column].dtype.kind in {"i", "u", "f", "b"}]
    work = standardize_numeric_frame(work, numeric_predictors)
    for column in predictors:
        if column not in numeric_predictors:
            work[column] = work[column].fillna(0)

    X = sm.add_constant(work[predictors].astype(float), has_constant="add")
    y = work[target_col].astype(float)
    result = sm.Logit(y, X).fit(method="lbfgs", maxiter=500, disp=False)

    coef_table = pd.DataFrame(
        {
            "feature": result.params.index,
            "coef": result.params.values,
            "pvalue": result.pvalues.values,
            "odds_ratio": np.exp(result.params.values),
        }
    )
    coef_table.to_csv(cfg.TABLE_DIR / f"{out_prefix}_coefficients.csv", index=False, encoding="utf-8-sig")

    fit_table = pd.DataFrame(
        [
            {
                "model_name": out_prefix,
                "nobs": float(result.nobs),
                "pseudo_r2": float(result.prsquared),
                "llf": float(result.llf),
                "aic": float(result.aic),
            }
        ]
    )
    fit_table.to_csv(cfg.TABLE_DIR / f"{out_prefix}_fit.csv", index=False, encoding="utf-8-sig")

    with open(cfg.DOC_DIR / f"{out_prefix}_summary.txt", "w", encoding="utf-8") as handle:
        handle.write(str(result.summary2()))

    return fit_table
