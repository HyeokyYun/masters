"""캘린더 정렬 패널 빌드 공용 유틸."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg  # noqa: E402


@dataclass(frozen=True)
class WindowSpec:
    start_year: int
    start_month: int
    window_months: int
    target_offset: int

    @property
    def feature_start(self) -> pd.Timestamp:
        return pd.Timestamp(year=self.start_year, month=self.start_month, day=1)

    @property
    def feature_end(self) -> pd.Timestamp:
        ts = self.feature_start + pd.DateOffset(months=self.window_months)
        return ts - pd.Timedelta(days=1)

    @property
    def target_start(self) -> pd.Timestamp:
        return pd.Timestamp(
            year=self.start_year + self.target_offset,
            month=self.start_month,
            day=1,
        )

    @property
    def target_end(self) -> pd.Timestamp:
        ts = self.target_start + pd.DateOffset(months=self.window_months)
        return ts - pd.Timedelta(days=1)

    @property
    def combo_id(self) -> str:
        return cfg.combo_id(
            self.start_year, self.start_month, self.window_months, self.target_offset
        )


def enumerate_combos() -> list[WindowSpec]:
    """Generate all calendar-aligned (feature, target) combos that fit the data range.

    Constraint: target_end must lie before DATA_END (we keep equality OK).
    Note: we also keep cases where target_end is slightly after DATA_END but at
    least MIN_TARGET_WEEKS_RATIO worth of weeks fit before DATA_END. This is
    handled at panel-build time, but here we drop combos whose target_start
    itself is past DATA_END.
    """
    data_end = pd.Timestamp(cfg.DATA_END)
    combos: list[WindowSpec] = []
    for sy in cfg.START_YEARS:
        for sm in cfg.START_MONTHS:
            for w in cfg.WINDOW_MONTHS:
                for off in cfg.TARGET_YEAR_OFFSETS:
                    spec = WindowSpec(sy, sm, w, off)
                    if spec.feature_start < pd.Timestamp(cfg.DATA_START):
                        continue
                    if spec.target_start > data_end:
                        continue
                    combos.append(spec)
    return combos


def load_weekly(use_cols: Iterable[str] | None = None) -> pd.DataFrame:
    cols = list(use_cols) if use_cols else None
    df = pd.read_parquet(cfg.WEEKLY_PATH, columns=cols)
    df["public_id"] = df["public_id"].astype(str)
    df["date_id"] = pd.to_datetime(df["date_id"])
    return df


def load_meta() -> pd.DataFrame:
    df = pd.read_csv(cfg.META_PATH)
    df["public_id"] = df["public_id"].astype(str)
    return df


def slice_window(weekly: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """Inclusive on both ends (date_id is the week label)."""
    mask = (weekly["date_id"] >= start) & (weekly["date_id"] <= end)
    return weekly.loc[mask]


def expected_weeks_in(start: pd.Timestamp, end: pd.Timestamp) -> int:
    return max(1, int(np.floor((end - start).days / 7)) + 1)


def linregress_slope(y: np.ndarray, x: np.ndarray | None = None) -> tuple[float, float]:
    """Return (slope, r2). Robust against constant / NaN inputs."""
    y = np.asarray(y, dtype=float)
    if x is None:
        x = np.arange(len(y), dtype=float)
    mask = np.isfinite(y)
    if mask.sum() < 3:
        return 0.0, 0.0
    yy = y[mask]
    xx = x[mask]
    vx = xx - xx.mean()
    vy = yy - yy.mean()
    den = float(np.dot(vx, vx))
    vary = float(np.dot(vy, vy))
    if den < 1e-12 or vary < 1e-12:
        return 0.0, 0.0
    slope = float(np.dot(vx, vy) / den)
    r2 = float((np.dot(vx, vy) ** 2) / (den * vary))
    return slope, r2


def row_slopes(arr: np.ndarray) -> np.ndarray:
    """Vectorized OLS slope per row, NaN-safe."""
    n_rows, n_cols = arr.shape
    out = np.zeros(n_rows, dtype=float)
    if n_cols < 3:
        return out
    x = np.arange(n_cols, dtype=float)
    mask = np.isfinite(arr)
    counts = mask.sum(axis=1)
    valid = counts >= 3
    a = np.where(mask, arr, 0.0)
    cnt = mask.sum(axis=1).clip(min=1)
    sum_x = (mask * x).sum(axis=1)
    sum_y = a.sum(axis=1)
    mean_x = sum_x / cnt
    mean_y = sum_y / cnt
    cov = (mask * (x - mean_x[:, None]) * (a - mean_y[:, None] * mask)).sum(axis=1)
    var_x = (mask * (x - mean_x[:, None]) ** 2).sum(axis=1)
    safe = (var_x > 1e-12) & valid
    out[safe] = cov[safe] / var_x[safe]
    return out


def normalize_per_row(mat: np.ndarray) -> np.ndarray:
    """Divide by row mean (0/NaN-safe) so slope magnitude is comparable across stores."""
    means = np.nanmean(mat, axis=1, keepdims=True)
    means = np.where(np.isfinite(means) & (means > 1e-9), means, 1.0)
    return mat / means


def pivot_sales(panel: pd.DataFrame, value: str = "sales_card") -> pd.DataFrame:
    return panel.pivot_table(index="public_id", columns="date_id", values=value, aggfunc="mean")


def panel_path(combo_id: str) -> Path:
    return cfg.PANEL_DIR / f"panel_{combo_id}.parquet"


def label_path(combo_id: str) -> Path:
    return cfg.LABEL_DIR / f"labels_{combo_id}.parquet"


def feature_path(combo_id: str) -> Path:
    return cfg.FEATURE_DIR / f"features_{combo_id}.parquet"
