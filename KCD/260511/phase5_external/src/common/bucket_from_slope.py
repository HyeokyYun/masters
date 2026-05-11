"""Foundation 모델/SOTA가 만든 forecast → slope → G/S/D bucket.

Phase 0가 결정한 ±0.5σ 규칙을 그대로 적용. σ는 train fold의 라벨에서 다시
계산해야 leakage가 없다.

Inputs:
  forecast: np.ndarray [N, H]  — N store × H horizon weeks forecast (sales_card)
  scale:    optional [N] divisor (foundation 모델이 raw scale 반환 시 정규화 용)

Outputs:
  cls_idx:  np.ndarray [N] of {0:Decline, 1:Stable, 2:Growth} indices.
"""
from __future__ import annotations

import numpy as np

from .paths import OUTCOME_CLASSES

CLS_DECLINE = OUTCOME_CLASSES.index("Decline")
CLS_STABLE = OUTCOME_CLASSES.index("Stable")
CLS_GROWTH = OUTCOME_CLASSES.index("Growth")


def forecast_slope(forecast: np.ndarray, scale: np.ndarray | None = None) -> np.ndarray:
    """forecast [N,H] → slope_norm [N]. slope = OLS slope / mean."""
    N, H = forecast.shape
    if scale is None:
        scale = forecast.mean(axis=1)
    safe = np.where(np.abs(scale) > 1e-9, scale, 1.0)
    x = np.arange(H, dtype=np.float32)
    x_c = x - x.mean()
    denom = (x_c * x_c).sum()
    if denom < 1e-12:
        return np.zeros(N, dtype=np.float32)
    means = forecast.mean(axis=1, keepdims=True)
    y_c = forecast - means
    slope = (x_c * y_c).sum(axis=1) / denom
    return (slope / safe).astype(np.float32)


def fit_thresholds(slope_norm_train: np.ndarray, k_sigma: float = 0.5) -> tuple[float, float]:
    """train fold slopes로부터 (low, high) threshold 산출. ±k_sigma * std."""
    s = slope_norm_train.astype(np.float32)
    sigma = float(s.std())
    return (-k_sigma * sigma, +k_sigma * sigma)


def bucket(slope_norm: np.ndarray, thresholds: tuple[float, float]) -> np.ndarray:
    low, high = thresholds
    out = np.full(len(slope_norm), CLS_STABLE, dtype=np.int64)
    out[slope_norm <= low] = CLS_DECLINE
    out[slope_norm >= high] = CLS_GROWTH
    return out
