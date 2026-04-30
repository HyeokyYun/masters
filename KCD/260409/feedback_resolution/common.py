"""260409 feedback resolution — 공용 유틸리티.

지난 미팅(260409)에서 받은 피드백 3종을 해결하기 위한 공통 함수.

- load_panel_with_labels(): top_tier가 만든 observed_window panel + outcome_3 라벨 로드
- extract_window_features(): 임의 window 길이로 시계열 feature 추출
- run_cv(): 5-fold stratified CV (LightGBM) 수행
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import f1_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold

warnings.filterwarnings("ignore")

# top_tier/config.py 사용
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "top_tier"))
import config as cfg  # noqa: E402

import lightgbm as lgb  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent / "outputs"
OUT_DIR.mkdir(exist_ok=True)


def load_panel_with_labels() -> tuple[pd.DataFrame, pd.DataFrame]:
    panel = pd.read_parquet(cfg.PANEL_PATH)
    panel["public_id"] = panel["public_id"].astype(str)
    feats = pd.read_csv(cfg.FEATURES_PATH)
    feats["public_id"] = feats["public_id"].astype(str)
    feats = feats.dropna(subset=["outcome_3"])
    return panel, feats


def _slope(y: np.ndarray) -> float:
    if np.isnan(y).all():
        return 0.0
    mask = ~np.isnan(y)
    if mask.sum() < 3 or np.nanstd(y) == 0:
        return 0.0
    x = np.arange(len(y), dtype=float)
    s, *_ = stats.linregress(x[mask], y[mask])
    return float(s)


def _vol(y: np.ndarray, win: int = 4) -> float:
    if len(y) < win or np.isnan(y).all():
        return 0.0
    rs = pd.Series(y).rolling(win, min_periods=win // 2).std()
    m = np.nanmean(y)
    return float(np.nanmean(rs) / m) if m else 0.0


def _segment_stats(y: np.ndarray, prefix: str) -> dict:
    """주어진 시계열 segment의 기울기·평균·변동성·표준편차 한 묶음."""
    y = y[~np.isnan(y)]
    if len(y) < 2:
        return {f"{prefix}_slope": 0.0, f"{prefix}_mean": 0.0, f"{prefix}_vol": 0.0, f"{prefix}_std": 0.0}
    return {
        f"{prefix}_slope": _slope(y),
        f"{prefix}_mean": float(np.nanmean(y)),
        f"{prefix}_vol": _vol(y),
        f"{prefix}_std": float(np.nanstd(y)),
    }


def extract_window_features(panel: pd.DataFrame, weeks: int) -> pd.DataFrame:
    """첫 `weeks` 주의 매출 시퀀스에서 feature 추출."""
    sub = panel[panel["observed_week_idx"] < weeks].sort_values(["public_id", "observed_week_idx"])
    sales_pivot = sub.pivot_table(index="public_id", columns="observed_week_idx", values="sales_card", aggfunc="mean")
    cust_pivot = sub.pivot_table(index="public_id", columns="observed_week_idx", values="customer", aggfunc="mean").reindex_like(sales_pivot)
    cust_new_pivot = sub.pivot_table(index="public_id", columns="observed_week_idx", values="customer_new", aggfunc="mean").reindex_like(sales_pivot)

    valid = sales_pivot.notna().sum(axis=1) >= max(weeks // 2, 5)
    sales_pivot = sales_pivot.loc[valid].sort_index(axis=1)
    cust_pivot = cust_pivot.loc[valid].sort_index(axis=1)
    cust_new_pivot = cust_new_pivot.loc[valid].sort_index(axis=1)

    s = np.log1p(sales_pivot.to_numpy(dtype=float))
    c = cust_pivot.to_numpy(dtype=float)
    cn = cust_new_pivot.to_numpy(dtype=float)

    rows = []
    for i, pid in enumerate(sales_pivot.index):
        sy, cy, cny = s[i], c[i], cn[i]
        feat = {"public_id": pid}
        feat.update(_segment_stats(sy, "sales_full"))
        feat["sales_cv"] = _vol(sy)
        # 추가 customer/nc feature
        nc_rate = np.where(cy > 0, cny / cy, 0.0)
        feat["nc_rate_mean"] = float(np.nanmean(nc_rate))
        feat["customer_mean"] = float(np.nanmean(cy))
        rows.append(feat)
    return pd.DataFrame(rows)


def extract_segmented_features(panel: pd.DataFrame, weeks: int, seg_len: int = 10) -> pd.DataFrame:
    """첫 `weeks` 주의 시퀀스를 (early seg_len, late seg_len) 두 구간으로 쪼갠 feature 추출.

    피드백 2·3 공통: early/late segment의 기울기·평균·변동성·신규고객 비율 산출.
    """
    sub = panel[panel["observed_week_idx"] < weeks].sort_values(["public_id", "observed_week_idx"])
    sales_pivot = sub.pivot_table(index="public_id", columns="observed_week_idx", values="sales_card", aggfunc="mean")
    cust_pivot = sub.pivot_table(index="public_id", columns="observed_week_idx", values="customer", aggfunc="mean").reindex_like(sales_pivot)
    cust_new_pivot = sub.pivot_table(index="public_id", columns="observed_week_idx", values="customer_new", aggfunc="mean").reindex_like(sales_pivot)

    valid = sales_pivot.notna().sum(axis=1) >= max(weeks // 2, 5)
    sales_pivot = sales_pivot.loc[valid].sort_index(axis=1)
    cust_pivot = cust_pivot.loc[valid].sort_index(axis=1)
    cust_new_pivot = cust_new_pivot.loc[valid].sort_index(axis=1)

    s = np.log1p(sales_pivot.to_numpy(dtype=float))
    c = cust_pivot.to_numpy(dtype=float)
    cn = cust_new_pivot.to_numpy(dtype=float)

    early_idx = slice(0, seg_len)
    late_idx = slice(weeks - seg_len, weeks)

    rows = []
    for i, pid in enumerate(sales_pivot.index):
        sy, cy, cny = s[i], c[i], cn[i]
        nc_rate = np.where(cy > 0, cny / cy, 0.0)

        feat = {"public_id": pid}
        feat.update(_segment_stats(sy[early_idx], "early_sales"))
        feat.update(_segment_stats(sy[late_idx], "late_sales"))
        feat["early_nc_rate"] = float(np.nanmean(nc_rate[early_idx]))
        feat["late_nc_rate"] = float(np.nanmean(nc_rate[late_idx]))
        feat["early_customer_mean"] = float(np.nanmean(cy[early_idx]))
        feat["late_customer_mean"] = float(np.nanmean(cy[late_idx]))
        rows.append(feat)
    return pd.DataFrame(rows)


def run_cv(X: np.ndarray, y: np.ndarray, n_splits: int = 5, seed: int = 42) -> dict:
    """LightGBM 5-fold stratified CV → 평균 성능."""
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    f1s, recs, aucs = [], {0: [], 1: [], 2: []}, []
    for tr_idx, te_idx in skf.split(X, y):
        X_tr, X_te = X[tr_idx], X[te_idx]
        y_tr, y_te = y[tr_idx], y[te_idx]

        model = lgb.LGBMClassifier(
            n_estimators=200, num_leaves=31, learning_rate=0.05,
            min_child_samples=50, random_state=seed, n_jobs=-1, verbose=-1,
        )
        model.fit(X_tr, y_tr)
        proba = model.predict_proba(X_te)
        pred = proba.argmax(axis=1)

        f1s.append(f1_score(y_te, pred, average="macro"))
        for cls in (0, 1, 2):
            recs[cls].append(recall_score(y_te, pred, labels=[cls], average="macro", zero_division=0))
        try:
            aucs.append(roc_auc_score(y_te, proba, multi_class="ovr"))
        except ValueError:
            aucs.append(np.nan)

    return {
        "macro_f1_mean": float(np.mean(f1s)),
        "macro_f1_std": float(np.std(f1s)),
        "recall_Decline_mean": float(np.mean(recs[0])),
        "recall_Stable_mean": float(np.mean(recs[1])),
        "recall_Growth_mean": float(np.mean(recs[2])),
        "auc_ovr_mean": float(np.mean(aucs)),
    }


OUTCOME_TO_INT = {"Decline": 0, "Stable": 1, "Growth": 2}


def merge_label(features: pd.DataFrame, feats_labeled: pd.DataFrame) -> pd.DataFrame:
    out = features.merge(
        feats_labeled[["public_id", "outcome_3"]], on="public_id", how="inner"
    )
    out["y"] = out["outcome_3"].map(OUTCOME_TO_INT)
    return out.dropna(subset=["y"]).reset_index(drop=True)
