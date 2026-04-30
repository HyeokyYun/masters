"""OLS regression with statsmodels. Use dense numpy arrays to avoid sparse issues."""
import numpy as np
import pandas as pd
import statsmodels.api as sm


def prepare_design_matrix(
    df: pd.DataFrame,
    numeric_cols: list[str],
    categorical_cols: list[str] | None = None,
    drop_first: bool = True,
) -> np.ndarray:
    """Build dense design matrix: numeric + dummies from categorical, then add_constant.
    get_dummies -> .values so statsmodels gets dense arrays."""
    X_num = df[numeric_cols].astype(float)
    if categorical_cols:
        dummies = pd.get_dummies(df[categorical_cols], drop_first=drop_first, dtype=float)
        X = pd.concat([X_num, dummies], axis=1)
    else:
        X = X_num.copy()
    # Dense numpy for statsmodels
    X_dense = np.asarray(X, dtype=float)
    return sm.add_constant(X_dense, has_constant="add")


def ols_fit(y: np.ndarray, X: np.ndarray) -> sm.regression.linear_model.RegressionResultsWrapper:
    """Fit OLS. y and X must be dense 1d and 2d numpy arrays."""
    y = np.asarray(y, dtype=float).ravel()
    X = np.asarray(X, dtype=float)
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    return sm.OLS(y, X).fit()
