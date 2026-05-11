"""Sequence loader — step06의 _load_seq를 추출.

또한 raw weekly.parquet에서 panel window보다 긴 context를 뽑는
_load_long_context 함수를 추가 제공 (foundation 모델용).
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from .paths import CHANNELS, CLS_TO_IDX, OUTCOME_CLASSES, up

_COMBO_RE = re.compile(r"^sy(\d{4})_sm(\d{2})_w(\d+)m_off(\d+)$")


def spec_from_combo_id(combo_id: str) -> up.WindowSpec:
    m = _COMBO_RE.match(combo_id)
    if not m:
        raise ValueError(f"bad combo_id: {combo_id}")
    return up.WindowSpec(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)))


def load_seq(combo_id: str):
    """(ids, X[N,T,C], y[N]) — step06와 동일 protocol."""
    p_path = up.panel_path(combo_id)
    l_path = up.label_path(combo_id)
    if not (p_path.exists() and l_path.exists()):
        return None, None, None
    panel = pd.read_parquet(p_path)
    labels = pd.read_parquet(l_path)
    labels["public_id"] = labels["public_id"].astype(str)
    feat_seg = panel[panel["segment"] == "feature"].copy()
    feat_seg["public_id"] = feat_seg["public_id"].astype(str)
    feat_seg = feat_seg.sort_values(["public_id", "date_id"])

    valid_ids = labels.loc[labels["outcome_3"].isin(OUTCOME_CLASSES), "public_id"].unique()
    feat_seg = feat_seg[feat_seg["public_id"].isin(valid_ids)]

    ids = sorted(feat_seg["public_id"].unique())
    dates = sorted(feat_seg["date_id"].unique())
    T = len(dates)
    if T < 4 or len(ids) < 500:
        return None, None, None
    id_idx = {pid: i for i, pid in enumerate(ids)}
    date_idx = {d: i for i, d in enumerate(dates)}

    X = np.zeros((len(ids), T, len(CHANNELS)), dtype=np.float32)
    mask = np.zeros((len(ids), T), dtype=np.float32)
    for ch_i, ch in enumerate(CHANNELS):
        if ch not in feat_seg.columns:
            continue
        arr = feat_seg[ch].to_numpy(dtype=np.float32)
        rows = feat_seg["public_id"].map(id_idx).to_numpy()
        cols = feat_seg["date_id"].map(date_idx).to_numpy()
        X[rows, cols, ch_i] = np.where(np.isfinite(arr), arr, 0.0)
        mask[rows, cols] = 1.0

    means = X.sum(axis=1) / np.maximum(mask.sum(axis=1, keepdims=True), 1.0)
    means = np.where(means > 1e-9, means, 1.0)
    Xn = X / means[:, None, :]
    Xn = np.where(np.isfinite(Xn), Xn, 0.0)

    lbl_map = labels.set_index("public_id")["outcome_3"].to_dict()
    y = np.array([CLS_TO_IDX[lbl_map[pid]] for pid in ids], dtype=np.int64)
    return np.array(ids), Xn, y


def load_long_context(combo_id: str, max_history_weeks: int = 104):
    """Foundation 모델용 — raw weekly에서 panel feature window 시작 이전의
    최대 max_history_weeks(=2년) 의 sales_card 시계열을 store 별로 뽑아 반환.

    Returns:
        ids: np.ndarray of public_id (str)
        ctx: list of np.ndarray (variable length per store)
        y:   np.ndarray of class index
        spec: dict with feature_start, feature_end, target_start, target_end, horizon
    """
    spec = spec_from_combo_id(combo_id)
    weekly = up.load_weekly(use_cols=["public_id", "date_id", "sales_card"])
    weekly["public_id"] = weekly["public_id"].astype(str)
    weekly["date_id"] = pd.to_datetime(weekly["date_id"])

    # target labels
    l_path = up.label_path(combo_id)
    labels = pd.read_parquet(l_path)
    labels["public_id"] = labels["public_id"].astype(str)
    labels = labels[labels["outcome_3"].isin(OUTCOME_CLASSES)]

    # 컨텍스트: feature_start 이전 max_history_weeks 부터 feature_end 직전까지 사용
    ctx_start = spec.feature_start - pd.Timedelta(weeks=max_history_weeks)
    ctx_end = spec.feature_end
    ctx_df = weekly[(weekly["date_id"] >= ctx_start) & (weekly["date_id"] < ctx_end)].copy()
    ctx_df = ctx_df.sort_values(["public_id", "date_id"])

    horizon_weeks = int(round((spec.target_end - spec.target_start).days / 7))
    valid_ids = sorted(set(labels["public_id"]) & set(ctx_df["public_id"]))

    lbl_map = labels.set_index("public_id")["outcome_3"].to_dict()
    grouped = ctx_df.groupby("public_id")["sales_card"]

    ids = []
    ctx_list = []
    y_list = []
    for pid in valid_ids:
        if pid not in grouped.groups:
            continue
        s = grouped.get_group(pid).to_numpy(dtype=np.float32)
        if len(s) < 8:
            continue
        ids.append(pid)
        ctx_list.append(s)
        y_list.append(CLS_TO_IDX[lbl_map[pid]])

    return (
        np.array(ids),
        ctx_list,
        np.array(y_list, dtype=np.int64),
        {
            "feature_start": spec.feature_start,
            "feature_end": spec.feature_end,
            "target_start": spec.target_start,
            "target_end": spec.target_end,
            "horizon_weeks": horizon_weeks,
        },
    )
