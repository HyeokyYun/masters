"""260430 follow-up: calendar-matched seasonal rolling-window prediction.

This script is intentionally self-contained and writes only under
`/home/hyeoky98/kcd/260430`. It does not modify `top_tier` or `thesis`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
import warnings

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_recall_fscore_support, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path("/home/hyeoky98/kcd")
BASE = ROOT / "260430"
TABLE_DIR = BASE / "outputs" / "tables"
FIG_DIR = BASE / "outputs" / "figures"
DOC_DIR = BASE / "docs"
WEEKLY_PATH = ROOT / "original_data" / "weekly.parquet"
TOP_TIER_TABLE_DIR = ROOT / "top_tier" / "outputs" / "tables"

CLASSES = ["Growth", "Stable", "Decline"]
START_MONTHS = list(range(1, 13))
WINDOW_WEEKS = [4, 8, 12, 16, 20, 30]
BASE_YEARS = [2021, 2022]
LAG_YEARS = [1, 2]
MIN_OBS_SHARE = 0.70
CV_FOLDS = 5
SEED = 42

warnings.filterwarnings("ignore", message="Mean of empty slice", category=RuntimeWarning)


@dataclass(frozen=True)
class WindowSpec:
    spec_id: str
    base_year: int
    start_month: int
    window_weeks: int
    lag_years: int
    feature_start_idx: int
    target_start_idx: int
    feature_start_date: pd.Timestamp
    feature_end_date: pd.Timestamp
    target_start_date: pd.Timestamp
    target_end_date: pd.Timestamp


def ensure_dirs() -> None:
    for path in [TABLE_DIR, FIG_DIR, DOC_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def row_slope(mat: np.ndarray) -> np.ndarray:
    """Vectorized row-wise slope with NaN masking."""
    if mat.size == 0:
        return np.zeros(mat.shape[0], dtype=float)
    y = np.asarray(mat, dtype=float)
    mask = np.isfinite(y)
    x = np.arange(y.shape[1], dtype=float)[None, :]
    y0 = np.where(mask, y, 0.0)
    x0 = np.where(mask, x, 0.0)
    n = mask.sum(axis=1).astype(float)
    sum_x = x0.sum(axis=1)
    sum_y = y0.sum(axis=1)
    sum_xx = (x0 * x0).sum(axis=1)
    sum_yy = (y0 * y0).sum(axis=1)
    sum_xy = (x0 * y0).sum(axis=1)
    den = n * sum_xx - sum_x * sum_x
    var_y = n * sum_yy - sum_y * sum_y
    out = np.zeros(y.shape[0], dtype=float)
    ok = (n >= 3) & (den > 1e-12) & (var_y > 1e-12)
    out[ok] = (n[ok] * sum_xy[ok] - sum_x[ok] * sum_y[ok]) / den[ok]
    return out


def load_weekly_matrix() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[pd.Timestamp]]:
    cols = ["public_id", "date_id", "sales_card", "customer", "customer_new"]
    weekly = pd.read_parquet(WEEKLY_PATH, columns=cols)
    weekly["public_id"] = weekly["public_id"].astype(str)
    weekly["date_id"] = pd.to_datetime(weekly["date_id"])
    weekly.loc[weekly["sales_card"] < 0, "sales_card"] = np.nan
    weekly = weekly.sort_values(["public_id", "date_id"])

    weekly["sales_log"] = np.log1p(weekly["sales_card"])
    with np.errstate(divide="ignore", invalid="ignore"):
        weekly["nc_ratio"] = weekly["customer_new"] / weekly["customer"].replace(0, np.nan)
    weekly["customer_log"] = np.log1p(weekly["customer"])

    sales = weekly.pivot_table(
        index="public_id", columns="date_id", values="sales_log", aggfunc="mean"
    ).sort_index(axis=1)
    nc_ratio = weekly.pivot_table(
        index="public_id", columns="date_id", values="nc_ratio", aggfunc="mean"
    ).reindex(index=sales.index, columns=sales.columns)
    customer = weekly.pivot_table(
        index="public_id", columns="date_id", values="customer_log", aggfunc="mean"
    ).reindex(index=sales.index, columns=sales.columns)

    dates = [pd.Timestamp(d) for d in sales.columns]
    return sales, nc_ratio, customer, dates


def find_start_idx(dates: list[pd.Timestamp], start: pd.Timestamp) -> int | None:
    idx = int(np.searchsorted(np.array(dates, dtype="datetime64[ns]"), np.datetime64(start)))
    return idx if idx < len(dates) else None


def build_specs(dates: list[pd.Timestamp]) -> list[WindowSpec]:
    specs: list[WindowSpec] = []
    max_idx = len(dates)
    for base_year in BASE_YEARS:
        for month in START_MONTHS:
            feature_anchor = pd.Timestamp(year=base_year, month=month, day=1)
            feature_idx = find_start_idx(dates, feature_anchor)
            if feature_idx is None:
                continue
            for lag_years in LAG_YEARS:
                target_anchor = feature_anchor + pd.DateOffset(years=lag_years)
                target_idx = find_start_idx(dates, target_anchor)
                if target_idx is None:
                    continue
                for weeks in WINDOW_WEEKS:
                    if feature_idx + weeks > max_idx or target_idx + weeks > max_idx:
                        continue
                    spec_id = f"y{base_year}_m{month:02d}_w{weeks:02d}_lag{lag_years}y"
                    specs.append(
                        WindowSpec(
                            spec_id=spec_id,
                            base_year=base_year,
                            start_month=month,
                            window_weeks=weeks,
                            lag_years=lag_years,
                            feature_start_idx=feature_idx,
                            target_start_idx=target_idx,
                            feature_start_date=dates[feature_idx],
                            feature_end_date=dates[feature_idx + weeks - 1],
                            target_start_date=dates[target_idx],
                            target_end_date=dates[target_idx + weeks - 1],
                        )
                    )
    return specs


def extract_window_features(
    spec: WindowSpec,
    sales_arr: np.ndarray,
    nc_arr: np.ndarray,
    cust_arr: np.ndarray,
    ids: np.ndarray,
) -> pd.DataFrame:
    sl = slice(spec.feature_start_idx, spec.feature_start_idx + spec.window_weeks)
    sales = sales_arr[:, sl]
    nc = nc_arr[:, sl]
    cust = cust_arr[:, sl]
    valid = np.isfinite(sales).sum(axis=1)
    min_obs = int(np.ceil(spec.window_weeks * MIN_OBS_SHARE))
    keep = valid >= min_obs

    sales_k = sales[keep]
    nc_k = nc[keep]
    cust_k = cust[keep]
    ids_k = ids[keep]
    diff = np.diff(sales_k, axis=1)

    feats = pd.DataFrame(
        {
            "public_id": ids_k,
            "feature_valid_weeks": valid[keep],
            "sales_mean": np.nanmean(sales_k, axis=1),
            "sales_std": np.nanstd(sales_k, axis=1),
            "sales_min": np.nanmin(sales_k, axis=1),
            "sales_max": np.nanmax(sales_k, axis=1),
            "sales_slope": row_slope(sales_k),
            "sales_delta": np.nanmean(sales_k[:, -min(4, sales_k.shape[1]) :], axis=1)
            - np.nanmean(sales_k[:, : min(4, sales_k.shape[1])], axis=1),
            "diff_mean": np.nanmean(diff, axis=1),
            "diff_std": np.nanstd(diff, axis=1),
            "nc_mean": np.nanmean(nc_k, axis=1),
            "nc_slope": row_slope(nc_k),
            "customer_mean": np.nanmean(cust_k, axis=1),
            "customer_slope": row_slope(cust_k),
        }
    )
    feats["sales_cv"] = feats["sales_std"] / (feats["sales_mean"].abs() + 1e-9)
    feats["sales_range"] = feats["sales_max"] - feats["sales_min"]
    feats = feats.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return feats


def build_labels(spec: WindowSpec, sales_arr: np.ndarray, ids: np.ndarray) -> pd.DataFrame:
    sl = slice(spec.target_start_idx, spec.target_start_idx + spec.window_weeks)
    sales = sales_arr[:, sl]
    valid = np.isfinite(sales).sum(axis=1)
    min_obs = int(np.ceil(spec.window_weeks * MIN_OBS_SHARE))
    keep = valid >= min_obs
    slopes = row_slope(sales[keep])
    sigma = float(np.nanstd(slopes))
    threshold = 0.5 * sigma
    labels = np.select(
        [slopes > threshold, slopes < -threshold],
        ["Growth", "Decline"],
        default="Stable",
    )
    return pd.DataFrame(
        {
            "public_id": ids[keep],
            "target_valid_weeks": valid[keep],
            "target_slope": slopes,
            "outcome_3": labels,
            "label_threshold": threshold,
        }
    )


def eval_one_spec(df: pd.DataFrame, spec: WindowSpec) -> list[dict[str, object]]:
    y = df["outcome_3"].to_numpy()
    counts = pd.Series(y).value_counts()
    if len(counts) < 3 or counts.min() < CV_FOLDS:
        return []

    x_cols = [
        c
        for c in df.columns
        if c
        not in {
            "public_id",
            "outcome_3",
            "target_slope",
            "label_threshold",
            "feature_valid_weeks",
            "target_valid_weeks",
        }
    ]
    X = df[x_cols].to_numpy(dtype=float)
    skf = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=SEED)
    rows: list[dict[str, object]] = []
    for fold, (tr, te) in enumerate(skf.split(X, y)):
        model = make_pipeline(
            StandardScaler(),
            LogisticRegression(
                max_iter=800,
                class_weight="balanced",
                solver="lbfgs",
                random_state=SEED,
            ),
        )
        model.fit(X[tr], y[tr])
        pred = model.predict(X[te])
        proba = model.predict_proba(X[te])
        proba_df = pd.DataFrame(proba, columns=model.classes_)
        proba_full = proba_df.reindex(columns=CLASSES, fill_value=0.0).to_numpy()
        y_bin = pd.get_dummies(pd.Series(y[te])).reindex(columns=CLASSES, fill_value=0).to_numpy()
        per = precision_recall_fscore_support(y[te], pred, labels=CLASSES, zero_division=0)
        try:
            auc = roc_auc_score(y_bin, proba_full, multi_class="ovr")
        except Exception:
            auc = np.nan
        row = {
            "spec_id": spec.spec_id,
            "base_year": spec.base_year,
            "start_month": spec.start_month,
            "window_weeks": spec.window_weeks,
            "lag_years": spec.lag_years,
            "fold": fold,
            "n": len(df),
            "model": "balanced_logistic",
            "macro_f1": f1_score(y[te], pred, average="macro", zero_division=0),
            "weighted_f1": f1_score(y[te], pred, average="weighted", zero_division=0),
            "auc_ovr": auc,
        }
        for i, cls in enumerate(CLASSES):
            row[f"precision_{cls}"] = per[0][i]
            row[f"recall_{cls}"] = per[1][i]
            row[f"f1_{cls}"] = per[2][i]
        rows.append(row)
    return rows


def add_spec_metadata(spec: WindowSpec, n_features: int, n_labels: int, n_joined: int) -> dict[str, object]:
    return {
        "spec_id": spec.spec_id,
        "base_year": spec.base_year,
        "start_month": spec.start_month,
        "window_weeks": spec.window_weeks,
        "lag_years": spec.lag_years,
        "feature_start_date": spec.feature_start_date.date().isoformat(),
        "feature_end_date": spec.feature_end_date.date().isoformat(),
        "target_start_date": spec.target_start_date.date().isoformat(),
        "target_end_date": spec.target_end_date.date().isoformat(),
        "n_feature_stores": n_features,
        "n_target_stores": n_labels,
        "n_joined_stores": n_joined,
    }


def summarize_cv(cv: pd.DataFrame) -> pd.DataFrame:
    metric_cols = [
        "macro_f1",
        "weighted_f1",
        "auc_ovr",
        "recall_Growth",
        "recall_Stable",
        "recall_Decline",
        "f1_Growth",
        "f1_Stable",
        "f1_Decline",
    ]
    group_cols = ["spec_id", "base_year", "start_month", "window_weeks", "lag_years", "model", "n"]
    mean = cv.groupby(group_cols, observed=True)[metric_cols].mean().reset_index()
    std = cv.groupby(group_cols, observed=True)[metric_cols].std().reset_index()
    std = std.rename(columns={c: f"{c}_std" for c in metric_cols})
    return mean.merge(std, on=group_cols, how="left")


def read_top_tier_baselines() -> dict[str, float | None]:
    out: dict[str, float | None] = {
        "top_tier_xgb_macro_f1": None,
        "top_tier_hybrid_macro_f1": None,
        "top_tier_hybrid_auc": None,
    }
    hybrid_path = TOP_TIER_TABLE_DIR / "hybrid_prediction_summary.csv"
    if not hybrid_path.exists():
        return out
    raw = pd.read_csv(hybrid_path, header=[0, 1], index_col=0)
    if "D_base_cluster_cp_PROPOSED" in raw.index:
        out["top_tier_hybrid_macro_f1"] = float(raw.loc["D_base_cluster_cp_PROPOSED", ("macro_f1", "mean")])
        out["top_tier_hybrid_auc"] = float(raw.loc["D_base_cluster_cp_PROPOSED", ("auc_ovr", "mean")])
    if "A_base_46" in raw.index:
        out["top_tier_xgb_macro_f1"] = float(raw.loc["A_base_46", ("macro_f1", "mean")])
    return out


def make_figures(summary: pd.DataFrame, baselines: dict[str, float | None]) -> None:
    sns.set_theme(style="whitegrid")
    primary = summary[summary["lag_years"] == 1].copy()
    if primary.empty:
        primary = summary.copy()
    primary = (
        primary.sort_values("macro_f1", ascending=False)
        .groupby(["start_month", "window_weeks"], as_index=False, observed=True)
        .first()
    )

    for metric, fname, title in [
        ("macro_f1", "seasonal_macro_f1_heatmap.png", "Seasonal rolling-window Macro-F1"),
        ("recall_Decline", "seasonal_decline_recall_heatmap.png", "Seasonal rolling-window Decline recall"),
    ]:
        pivot = primary.pivot(index="window_weeks", columns="start_month", values=metric).sort_index()
        plt.figure(figsize=(11, 5.8))
        sns.heatmap(pivot, annot=True, fmt=".3f", cmap="viridis", cbar_kws={"label": metric})
        plt.title(title)
        plt.xlabel("Start month")
        plt.ylabel("Window length (weeks)")
        plt.tight_layout()
        plt.savefig(FIG_DIR / fname, dpi=220)
        plt.close()

    best = summary.sort_values("macro_f1", ascending=False).head(10).copy()
    best["label"] = best.apply(
        lambda r: f"{int(r.base_year)}-{int(r.start_month):02d} / {int(r.window_weeks)}w / lag{int(r.lag_years)}",
        axis=1,
    )
    plot_rows = [
        {"label": row["label"], "macro_f1": row["macro_f1"], "type": "seasonal"}
        for _, row in best.iterrows()
    ]
    if baselines.get("top_tier_xgb_macro_f1") is not None:
        plot_rows.append(
            {
                "label": "top_tier A_base_46",
                "macro_f1": baselines["top_tier_xgb_macro_f1"],
                "type": "existing",
            }
        )
    if baselines.get("top_tier_hybrid_macro_f1") is not None:
        plot_rows.append(
            {
                "label": "top_tier hybrid",
                "macro_f1": baselines["top_tier_hybrid_macro_f1"],
                "type": "existing",
            }
        )
    comp = pd.DataFrame(plot_rows)
    plt.figure(figsize=(11, max(4.8, 0.38 * len(comp))))
    sns.barplot(data=comp, y="label", x="macro_f1", hue="type", dodge=False)
    plt.xlabel("Macro-F1")
    plt.ylabel("")
    plt.title("Existing baseline vs calendar-matched seasonal windows")
    plt.xlim(0, max(0.75, float(comp["macro_f1"].max()) + 0.05))
    plt.tight_layout()
    plt.savefig(FIG_DIR / "baseline_vs_seasonal_comparison.png", dpi=220)
    plt.close()


def write_report(
    inventory: pd.DataFrame,
    labels: pd.DataFrame,
    summary: pd.DataFrame,
    baselines: dict[str, float | None],
) -> None:
    best = summary.sort_values("macro_f1", ascending=False).head(8)
    best_decline = summary.sort_values("recall_Decline", ascending=False).head(8)
    baseline_lines = []
    for key, val in baselines.items():
        baseline_lines.append(f"- {key}: {val:.3f}" if val is not None else f"- {key}: unavailable")

    text = f"""# 260430 Seasonality Analysis Report

## Purpose

This run addresses the meeting concern that the original late-window label may
mix lifecycle signal with calendar seasonality. The revised analysis compares
feature and target windows that start in the same calendar month across years.

## Run Summary

- Valid window specifications: {len(inventory):,}
- Evaluated CV specifications: {summary['spec_id'].nunique():,}
- Total CV rows: {len(summary) * CV_FOLDS:,}
- Label distribution rows: {len(labels):,}

## Existing Baseline Read From top_tier

{chr(10).join(baseline_lines)}

## Best Seasonal Windows By Macro-F1

{best[['spec_id','n','macro_f1','weighted_f1','auc_ovr','recall_Growth','recall_Stable','recall_Decline']].to_markdown(index=False)}

## Best Seasonal Windows By Decline Recall

{best_decline[['spec_id','n','macro_f1','weighted_f1','auc_ovr','recall_Growth','recall_Stable','recall_Decline']].to_markdown(index=False)}

## Interpretation

Use these outputs as a robustness check, not as a replacement for the full
`top_tier` pipeline. If the seasonal-window results preserve meaningful
classification performance, the thesis can argue that early trajectory signal is
not only a byproduct of comparing January starts with summer target windows.

The strongest defense wording is:

> After matching feature and target windows by calendar month, the early
> transaction signal remains informative for later Growth/Stable/Decline
> classification, though performance varies by start month and forecast horizon.

## Files

- `outputs/tables/seasonal_window_inventory.csv`
- `outputs/tables/seasonal_label_distribution.csv`
- `outputs/tables/seasonal_prediction_cv_results.csv`
- `outputs/tables/seasonal_prediction_summary.csv`
- `outputs/figures/seasonal_macro_f1_heatmap.png`
- `outputs/figures/seasonal_decline_recall_heatmap.png`
- `outputs/figures/baseline_vs_seasonal_comparison.png`
"""
    (DOC_DIR / "260430_seasonality_analysis_report.md").write_text(text, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    print("[260430] loading weekly matrix", flush=True)
    sales, nc_ratio, customer, dates = load_weekly_matrix()
    ids = sales.index.astype(str).to_numpy()
    sales_arr = sales.to_numpy(dtype=float)
    nc_arr = nc_ratio.to_numpy(dtype=float)
    cust_arr = customer.to_numpy(dtype=float)
    specs = build_specs(dates)
    print(f"[260430] valid calendar specs: {len(specs):,}", flush=True)

    inventory_rows: list[dict[str, object]] = []
    label_rows: list[dict[str, object]] = []
    cv_rows: list[dict[str, object]] = []

    for idx, spec in enumerate(specs, start=1):
        feats = extract_window_features(spec, sales_arr, nc_arr, cust_arr, ids)
        labels = build_labels(spec, sales_arr, ids)
        joined = feats.merge(labels, on="public_id", how="inner")
        inventory_rows.append(add_spec_metadata(spec, len(feats), len(labels), len(joined)))
        dist = joined["outcome_3"].value_counts().reindex(CLASSES, fill_value=0)
        for cls, n in dist.items():
            label_rows.append(
                {
                    "spec_id": spec.spec_id,
                    "base_year": spec.base_year,
                    "start_month": spec.start_month,
                    "window_weeks": spec.window_weeks,
                    "lag_years": spec.lag_years,
                    "outcome_3": cls,
                    "n": int(n),
                    "share": float(n / len(joined)) if len(joined) else np.nan,
                }
            )
        cv_rows.extend(eval_one_spec(joined, spec))
        if idx % 20 == 0 or idx == len(specs):
            print(f"[260430] processed {idx:,}/{len(specs):,} specs", flush=True)

    inventory = pd.DataFrame(inventory_rows)
    labels = pd.DataFrame(label_rows)
    cv = pd.DataFrame(cv_rows)
    if cv.empty:
        raise RuntimeError("No CV results were produced. Check window coverage and label distributions.")
    summary = summarize_cv(cv)
    baselines = read_top_tier_baselines()

    inventory.to_csv(TABLE_DIR / "seasonal_window_inventory.csv", index=False, encoding="utf-8-sig")
    labels.to_csv(TABLE_DIR / "seasonal_label_distribution.csv", index=False, encoding="utf-8-sig")
    cv.to_csv(TABLE_DIR / "seasonal_prediction_cv_results.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(TABLE_DIR / "seasonal_prediction_summary.csv", index=False, encoding="utf-8-sig")
    (TABLE_DIR / "seasonal_baseline_reference.json").write_text(
        json.dumps(baselines, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    make_figures(summary, baselines)
    write_report(inventory, labels, summary, baselines)

    best = summary.sort_values("macro_f1", ascending=False).iloc[0]
    print("[260430] saved outputs under", BASE, flush=True)
    print(
        "[260430] best macro_f1:",
        best["spec_id"],
        f"macro_f1={best['macro_f1']:.3f}",
        f"decline_recall={best['recall_Decline']:.3f}",
        flush=True,
    )


if __name__ == "__main__":
    main()
