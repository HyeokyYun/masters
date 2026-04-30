"""Prediction helpers (e.g. fitted model predict, metrics)."""
import numpy as np


def predict_ols(results, X: np.ndarray) -> np.ndarray:
    """Predict using statsmodels OLS results. X must be dense (incl. constant column)."""
    X = np.asarray(X, dtype=float)
    return results.predict(X)


def mse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean squared error."""
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()
    return float(np.mean((y_true - y_pred) ** 2))
