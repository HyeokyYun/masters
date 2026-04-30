from __future__ import annotations

from pathlib import Path
import time
import numpy as np
import pandas as pd

from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

from tslearn.clustering import TimeSeriesKMeans, KShape
from tslearn.preprocessing import TimeSeriesScalerMeanVariance


ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "outputs"
TBL_DIR = OUT_DIR / "tables"
for d in [OUT_DIR, TBL_DIR]:
    d.mkdir(parents=True, exist_ok=True)

STORE_COL = "public_id"
TIME_COL = "date_id"
SALES_COL = "sales_card"

# ultralite settings
K_LIST = [6]
METHODS = ["euclidean", "kshape", "dtw"]  # dtw included but ultralite

SAMPLE_N = 6000          # dtw-friendly default (use 6000 because you observed n_merged ~ 6k)
RNG_SEED = 42

# DTW window constraint (try)
USE_DTW_WINDOW = True
SAKOE_CHIBA_RADIUS = 5   # 5~10 추천. 작을수록 빠름.

OUT_CSV = TBL_DIR / "compare_methods_dtw_ultralite.csv"


def log(msg: str):
    print(msg, flush=True)


def append_row_to_csv(row: dict, path: Path):
    df_row = pd.DataFrame([row])
    if path.exists():
        df_row.to_csv(path, mode="a", header=False, index=False)
    else:
        df_row.to_csv(path, mode="w", header=True, index=False)


def load_weekly_long(path_primary: Path, path_fallback: Path) -> pd.DataFrame:
    if path_primary.exists():
        return pd.read_parquet(path_primary)
    if path_fallback.exists():
        return pd.read_parquet(path_fallback)
    raise FileNotFoundError(f"Weekly parquet not found:\n- {path_primary}\n- {path_fallback}")


def build_store_time_matrix(df_long: pd.DataFrame,
                            store_col: str,
                            time_col: str,
                            sales_col: str) -> tuple[pd.Index, pd.DatetimeIndex, np.ndarray]:
    df = df_long[[store_col, time_col, sales_col]].copy()
    df[time_col] = pd.to_datetime(df[time_col])

    pivot = df.pivot_table(index=store_col, columns=time_col, values=sales_col, aggfunc="sum")
    pivot.columns = pd.to_datetime(pivot.columns)
    pivot = pivot.sort_index(axis=1)

    X_df = pivot.astype("float32")
    X_df = X_df.interpolate(axis=1, limit_direction="both")
    X_df = X_df.ffill(axis=1).bfill(axis=1).fillna(0.0)

    return pivot.index, pivot.columns, X_df.to_numpy(dtype=np.float32)


def load_features_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Features CSV not found: {path}")
    return pd.read_csv(path)


def make_success(df_feat: pd.DataFrame, metric="growth_rate", thr=1.0) -> pd.Series:
    return (df_feat[metric].astype(float) >= float(thr)).astype(int)


def success_rate_variance(df: pd.DataFrame, label_col="cluster_new") -> float:
    g = df.groupby(label_col)["success"].mean()
    return float(g.var())


def predict_M1_f1(df: pd.DataFrame, label_col: str = "cluster_new", seed: int = 42) -> float:
    naive_cols = [
        "avg_sales_card", "std_sales_card", "cv_sales_card",
        "max_sales", "min_sales", "max_min_ratio",
        "trend_slope", "total_weeks"
    ]
    cols = [c for c in naive_cols if c in df.columns]
    if len(cols) == 0:
        raise ValueError("No naive numeric columns found for M1.")

    X = df[cols].copy()
    X = X.apply(pd.to_numeric, errors="coerce")
    X = X.fillna(X.median(numeric_only=True))

    X = pd.concat([X, pd.get_dummies(df[label_col].astype(int), prefix=label_col)], axis=1)
    y = df["success"].to_numpy(dtype=int)

    Xtr, Xte, ytr, yte = train_test_split(
        X.to_numpy(dtype=float), y, test_size=0.2, random_state=seed, stratify=y
    )

    model = LogisticRegression(max_iter=2000, n_jobs=-1)
    model.fit(Xtr, ytr)
    pred = model.predict(Xte)
    return float(f1_score(yte, pred))


def fit_labels(method: str, X_ts: np.ndarray, K: int, seed: int) -> tuple[np.ndarray, str]:
    """
    Returns (labels, dtw_note)
    """
    if method == "euclidean":
        model = TimeSeriesKMeans(n_clusters=K, metric="euclidean",
                                 random_state=seed, n_init=5, max_iter=50)
        labels = model.fit_predict(X_ts).astype(int)
        return labels, ""
    if method == "kshape":
        model = KShape(n_clusters=K, random_state=seed, n_init=5, max_iter=50)
        labels = model.fit_predict(X_ts).astype(int)
        return labels, ""
    if method == "dtw":
        # ultralite: 1 run only (no seed/boot stability)
        metric_params = None
        note = "dtw single-run"
        if USE_DTW_WINDOW:
            metric_params = {"sakoe_chiba_radius": SAKOE_CHIBA_RADIUS}
            note += f"; window={SAKOE_CHIBA_RADIUS}"

        try:
            model = TimeSeriesKMeans(
                n_clusters=K, metric="dtw", random_state=seed,
                n_init=1, max_iter=5,
                metric_params=metric_params
            )
            labels = model.fit_predict(X_ts).astype(int)
            return labels, note
        except TypeError:
            # tslearn version might not support metric_params here
            model = TimeSeriesKMeans(
                n_clusters=K, metric="dtw", random_state=seed,
                n_init=1, max_iter=5
            )
            labels = model.fit_predict(X_ts).astype(int)
            return labels, "dtw single-run; window=unsupported"
    raise ValueError(f"Unknown method: {method}")


def main():
    features_csv = ROOT / ".." / "basic_data" / "store_features_for_analysis.csv"
    weekly_primary = ROOT / ".." / "original_data" / "weekly_processed.parquet"
    weekly_fallback = ROOT / ".." / "original_data" / "weekly.parquet"

    log("=== [DTW-ULTRALITE] Method comparison start (euclidean/kshape + dtw single-run) ===")
    log(f"Output CSV: {OUT_CSV}")

    t0 = time.time()

    log("[1/5] Load features CSV")
    df_feat = load_features_csv(features_csv).copy()
    if "cluster" in df_feat.columns:
        df_feat = df_feat.rename(columns={"cluster": "cluster_old"})
    if "public_id" not in df_feat.columns:
        raise ValueError("Features CSV must contain 'public_id'.")
    df_feat["public_id"] = df_feat["public_id"].astype(str)
    df_feat["success"] = make_success(df_feat, metric="growth_rate", thr=1.0)
    feature_ids = set(df_feat["public_id"].unique())
    log(f"  features: n={len(df_feat):,}, unique public_id={len(feature_ids):,}")

    log("[2/5] Load weekly parquet")
    df_long = load_weekly_long(weekly_primary, weekly_fallback)
    log(f"  weekly rows={len(df_long):,}")

    log("[3/5] Filter weekly to IDs present in features (critical for speed + consistent downstream)")
    df_long = df_long[df_long[STORE_COL].astype(str).isin(feature_ids)].copy()
    log(f"  weekly filtered rows={len(df_long):,}")

    log("[4/5] Build store×time matrix + scale")
    store_ids, time_index, X = build_store_time_matrix(df_long, STORE_COL, TIME_COL, SALES_COL)
    log(f"  matrix: n_store={len(store_ids):,}, n_dates={len(time_index)}, X.shape={X.shape}")

    X_ts = X[:, :, None]
    X_ts = TimeSeriesScalerMeanVariance(mu=0.0, std=1.0).fit_transform(X_ts)

    log("[5/5] Fixed sampling for speed (dtw-friendly)")
    rng = np.random.default_rng(RNG_SEED)
    idx_sample = rng.choice(X_ts.shape[0], size=min(SAMPLE_N, X_ts.shape[0]), replace=False)
    X_ts_s = X_ts[idx_sample]
    store_ids_s = store_ids[idx_sample]
    log(f"  sample_n={len(store_ids_s):,}")

    for K in K_LIST:
        for method in METHODS:
            log(f"\n--- Running: method={method} | K={K} ---")
            t1 = time.time()

            labels, note = fit_labels(method, X_ts_s, K, seed=42)
            df_label = pd.DataFrame({"public_id": store_ids_s.astype(str), "cluster_new": labels.astype(int)})
            merged = df_feat.merge(df_label, on="public_id", how="inner")
            if merged.empty:
                raise ValueError("Merge empty. Check public_id consistency.")

            var_sr = success_rate_variance(merged, label_col="cluster_new")
            m1_f1 = predict_M1_f1(merged, label_col="cluster_new", seed=42)

            row = {
                "method": method,
                "K": K,
                # stability skipped intentionally (ultralite)
                "seed_mean_ARI": np.nan,
                "seed_mean_NMI": np.nan,
                "bootstrap_mean_ARI": np.nan,
                "success_rate_var": var_sr,
                "M1_f1": m1_f1,
                "n_sample": int(len(store_ids_s)),
                "n_merged": int(len(merged)),
                "note": note if note else "no-stability; single-run labels",
                "elapsed_sec": round(time.time() - t1, 2),
            }
            append_row_to_csv(row, OUT_CSV)

            log(f"  Downstream: success_rate_var={var_sr:.6f}, M1_F1={m1_f1:.4f}, n_merged={len(merged):,}")
            log(f"  Appended -> {OUT_CSV}")
            log(f"  Done in {row['elapsed_sec']} sec | {row['note']}")

    log(f"\nAll done. Total elapsed: {round(time.time() - t0, 2)} sec")
    if OUT_CSV.exists():
        log("\nCurrent results snapshot:")
        print(pd.read_csv(OUT_CSV).sort_values(["K", "method"]).to_string(index=False))


if __name__ == "__main__":
    main()