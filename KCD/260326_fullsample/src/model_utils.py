from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src import config as cfg


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


def fit_outcome_mnlogit(df: pd.DataFrame, predictors: list[str], out_prefix: str) -> pd.DataFrame:
    work = df[["outcome_3"] + predictors].dropna(subset=["outcome_3"]).copy()
    for column in predictors:
        work[column] = _standardize(work[column])

    categories = list(cfg.OUTCOME_ORDER)
    y = pd.Categorical(work["outcome_3"], categories=categories, ordered=True)
    work = work[y.codes >= 0].copy()
    y = pd.Categorical(work["outcome_3"], categories=categories, ordered=True)
    X = sm.add_constant(work[predictors].astype(float), has_constant="add")

    result = sm.MNLogit(y.codes, X).fit(method="lbfgs", maxiter=500, disp=False)

    params = result.params.copy()
    pvalues = result.pvalues.copy()
    params.columns = [f"{categories[i + 1]}_coef" for i in range(params.shape[1])]
    pvalues.columns = [f"{categories[i + 1]}_pvalue" for i in range(pvalues.shape[1])]
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
