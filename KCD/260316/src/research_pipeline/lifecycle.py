from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict

import numpy as np
import pandas as pd

from research_pipeline.config import get_work_dir, load_config
from research_pipeline.data_prep import slice_panel_by_week


def _linear_fit_stats(values: np.ndarray) -> tuple[float, float]:
    arr = np.asarray(values, dtype=float)
    if arr.size < 2:
        return np.nan, np.inf
    x = np.arange(arr.size, dtype=float)
    coef = np.polyfit(x, arr, 1)
    pred = coef[0] * x + coef[1]
    sse = float(np.square(arr - pred).sum())
    return float(coef[0]), sse


def _max_drawdown(values: np.ndarray) -> float:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return np.nan
    running_max = np.maximum.accumulate(arr)
    drawdown = (running_max - arr) / np.where(running_max == 0, 1.0, running_max)
    return float(np.nanmax(drawdown))


def infer_inflection_week(
    series: np.ndarray,
    min_segment_weeks: int,
    improvement_threshold: float,
) -> tuple[int, float, float, bool]:
    n = len(series)
    midpoint = n // 2
    if n < max(2 * min_segment_weeks, 4):
        slope_p1, _ = _linear_fit_stats(series[:midpoint])
        slope_p2, _ = _linear_fit_stats(series[midpoint:])
        return midpoint, slope_p1, slope_p2, True

    total_slope, total_sse = _linear_fit_stats(series)
    best = None
    for split in range(min_segment_weeks, n - min_segment_weeks + 1):
        slope_p1, sse_p1 = _linear_fit_stats(series[:split])
        slope_p2, sse_p2 = _linear_fit_stats(series[split:])
        combined_sse = sse_p1 + sse_p2
        if best is None or combined_sse < best[0]:
            best = (combined_sse, split, slope_p1, slope_p2)

    if best is None:
        slope_p1, _ = _linear_fit_stats(series[:midpoint])
        slope_p2, _ = _linear_fit_stats(series[midpoint:])
        return midpoint, slope_p1, slope_p2, True

    improvement = 0.0 if not np.isfinite(total_sse) or total_sse == 0 else 1.0 - best[0] / total_sse
    if improvement < improvement_threshold:
        slope_p1, _ = _linear_fit_stats(series[:midpoint])
        slope_p2, _ = _linear_fit_stats(series[midpoint:])
        return midpoint, slope_p1, slope_p2, True
    return int(best[1]), float(best[2]), float(best[3]), False


def _direction_label(slope: float, epsilon: float) -> str:
    if pd.isna(slope):
        return "N"
    return "U" if slope >= epsilon else "D"


def _pattern_label(series: np.ndarray, threshold: float) -> str:
    n = len(series)
    edge = min(12, max(4, n // 4))
    start_mean = float(np.mean(series[:edge]))
    end_mean = float(np.mean(series[-edge:]))
    if start_mean == 0:
        change = 0.0 if end_mean == 0 else 1.0
    else:
        change = (end_mean - start_mean) / abs(start_mean)
    if change >= threshold:
        return "X"
    if change <= -threshold:
        return "Z"
    return "Y"


def _life_cycle_category(pattern_label: str) -> str | None:
    mapping = {"X": "rising", "Y": "maintaining", "Z": "declining"}
    return mapping.get(pattern_label)


def build_lifecycle_labels(panel: pd.DataFrame, cfg: Dict[str, object]) -> pd.DataFrame:
    analysis_cfg = cfg["analysis"]
    max_weeks = int(analysis_cfg["max_weeks"])
    min_weeks = int(analysis_cfg["min_weeks"])
    min_segment_weeks = int(analysis_cfg["min_segment_weeks"])
    slope_epsilon = float(analysis_cfg["slope_epsilon"])
    pattern_threshold = float(analysis_cfg["pattern_growth_threshold"])
    improvement_threshold = float(analysis_cfg["fallback_improvement_threshold"])

    work = slice_panel_by_week(panel, 0, max_weeks)
    labels = []
    for public_id, group in work.groupby("public_id"):
        group = group.sort_values("week_index")
        if len(group) < min_weeks:
            continue
        sales_norm = group["sales_minmax"].fillna(0.0).to_numpy(dtype=float)
        inflection_week, slope_p1, slope_p2, used_fallback = infer_inflection_week(
            sales_norm,
            min_segment_weeks=min_segment_weeks,
            improvement_threshold=improvement_threshold,
        )
        pattern_label = _pattern_label(sales_norm, threshold=pattern_threshold)
        p1_label = _direction_label(slope_p1, slope_epsilon)
        p2_label = _direction_label(slope_p2, slope_epsilon)
        labels.append(
            {
                "public_id": public_id,
                "n_weeks": len(group),
                "inflection_week": inflection_week,
                "P1_label": p1_label,
                "P2_label": p2_label,
                "slope_P1": slope_p1,
                "slope_P2": slope_p2,
                "used_fallback": int(used_fallback),
                "Pattern_label": pattern_label,
                "final_code": f"{p1_label}{p2_label}{pattern_label}",
                "life_cycle_category": _life_cycle_category(pattern_label),
                "mdd": _max_drawdown(sales_norm),
            }
        )
    return pd.DataFrame(labels)


def build_lifecycle_bundle(cfg: Dict[str, object], log: Callable[[str], None]) -> Dict[str, pd.DataFrame]:
    work_dir = get_work_dir()
    panel_path = work_dir / "outputs" / "tables" / "store_week_panel.parquet"
    feature_path = work_dir / "outputs" / "tables" / "store_features_full.csv"

    if not panel_path.exists() or not feature_path.exists():
        from research_pipeline.data_prep import build_analysis_inputs

        log("Base inputs not found. Building Step 1 outputs on the fly.")
        base_bundle = build_analysis_inputs(cfg, log)
        panel = base_bundle["panel"]
        store_features = base_bundle["store_features"]
    else:
        panel = pd.read_parquet(panel_path)
        store_features = pd.read_csv(feature_path)
        if "public_id" in panel.columns:
            panel["public_id"] = panel["public_id"].astype(str)
        if "public_id" in store_features.columns:
            store_features["public_id"] = store_features["public_id"].astype(str)

    labels = build_lifecycle_labels(panel, cfg)
    if "public_id" in labels.columns:
        labels["public_id"] = labels["public_id"].astype(str)
    analysis_table = store_features.merge(labels, on="public_id", how="inner")
    distribution = (
        analysis_table["life_cycle_category"]
        .value_counts(dropna=False)
        .rename_axis("life_cycle_category")
        .reset_index(name="store_count")
    )
    log(f"Lifecycle-labeled stores: {len(analysis_table):,}")
    return {
        "labels": labels,
        "analysis_table": analysis_table,
        "distribution": distribution,
    }
