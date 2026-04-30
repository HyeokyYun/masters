from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

from tqdm import tqdm

from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

from tslearn.clustering import TimeSeriesKMeans, KShape
from tslearn.preprocessing import TimeSeriesScalerMeanVariance


ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "outputs"
TBL_DIR = OUT_DIR / "tables"
FIG_DIR = OUT_DIR / "figures"
LOG_DIR = OUT_DIR / "logs"
for d in [OUT_DIR, TBL_DIR, FIG_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ---------------------------
# 0) fixed column mapping (confirmed)
# ---------------------------
STORE_COL = "public_id"
TIME_COL  = "date_id"
SALES_COL = "sales_card"


# ---------------------------
# 1) data loading + matrix build
# ---------------------------
def load_weekly_long(path_primary: Path, path_fallback: Path) -> pd.DataFrame:
    if path_primary.exists():
        return pd.read_parquet(path_primary)
    if path_fallback.exists():
        return pd.read_parquet(path_fallback)
    raise FileNotFoundError(f"Weekly parquet not found:\n- {path_primary}\n- {path_fallback}")


def build_store_time_matrix(df_long: pd.DataFrame,
                            store_col: str,
                            time_col: str,
                            sales_col: str,
                            fill_method: str = "interpolate") -> tuple[pd.Index, pd.DatetimeIndex, np.ndarray]:
    """
    Returns:
      store_ids, time_index(datetime), X (n_store, T)
    """
    df = df_long[[store_col, time_col, sales_col]].copy()

    # ensure datetime
    df[time_col] = pd.to_datetime(df[time_col])

    # pivot (store x time)
    pivot = df.pivot_table(index=store_col, columns=time_col, values=sales_col, aggfunc="sum")

    # ensure time ordering
    pivot.columns = pd.to_datetime(pivot.columns)
    pivot = pivot.sort_index(axis=1)

    store_ids = pivot.index
    time_index = pivot.columns

    X_df = pivot.astype("float32")

    # fill missing along time axis
    if fill_method == "interpolate":
        X_df = X_df.interpolate(axis=1, limit_direction="both")
    X_df = X_df.ffill(axis=1).bfill(axis=1).fillna(0.0)

    X = X_df.to_numpy(dtype=np.float32)
    return store_ids, time_index, X


# ---------------------------
# 2) clustering runners (tslearn)
# ---------------------------
def fit_labels(method: str, X_ts: np.ndarray, K: int, seed: int) -> np.ndarray:
    """
    X_ts: (n, T, 1)
    """
    if method == "euclidean":
        model = TimeSeriesKMeans(
            n_clusters=K, metric="euclidean", random_state=seed, n_init=2, max_iter=30
        )
    elif method == "dtw":
        model = TimeSeriesKMeans(
            n_clusters=K, metric="dtw", random_state=seed, n_init=2, max_iter=15
        )
    elif method == "kshape":
        model = KShape(
            n_clusters=K, random_state=seed, n_init=2, max_iter=50
        )
    else:
        raise ValueError(f"Unknown method: {method}")

    labels = model.fit_predict(X_ts)
    return labels.astype(int)


def seed_stability(method: str, X_ts: np.ndarray, K: int, seeds: list[int]) -> tuple[float, float]:
    """
    Mean pairwise ARI/NMI across multiple seeds.
    """
    labels_list = [fit_labels(method, X_ts, K, s) for s in seeds]

    aris, nmis = [], []
    for i in range(len(labels_list)):
        for j in range(i + 1, len(labels_list)):
            aris.append(adjusted_rand_score(labels_list[i], labels_list[j]))
            nmis.append(normalized_mutual_info_score(labels_list[i], labels_list[j]))

    return float(np.mean(aris)), float(np.mean(nmis))


def bootstrap_stability(method: str, X_ts: np.ndarray, K: int, seed: int,
                        n_boot: int = 10, sample_frac: float = 0.8) -> float:
    """
    Full-sample labels vs bootstrap-sample labels compared on sampled indices only.
    """
    rng = np.random.default_rng(seed)
    n = X_ts.shape[0]
    full_labels = fit_labels(method, X_ts, K, seed)

    aris = []
    for b in range(n_boot):
        idx = rng.choice(n, size=int(n * sample_frac), replace=False)
        X_b = X_ts[idx]
        labels_b = fit_labels(method, X_b, K, seed + 1000 + b)
        aris.append(adjusted_rand_score(full_labels[idx], labels_b))

    return float(np.mean(aris))


# ---------------------------
# 3) downstream checks (minimal)
# ---------------------------
def load_features_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Features CSV not found: {path}")
    return pd.read_csv(path)


def make_success(df_feat: pd.DataFrame, metric="growth_rate", thr=1.0) -> pd.Series:
    return (df_feat[metric].astype(float) >= float(thr)).astype(int)


def success_rate_variance(df: pd.DataFrame, label_col="cluster") -> float:
    """
    Variance of success rate across clusters.
    Higher => clusters separate success types more clearly.
    """
    g = df.groupby(label_col)["success"].mean()
    return float(g.var())


def predict_M1_f1(df: pd.DataFrame, label_col: str = "cluster_new", seed: int = 42) -> float:
    """
    M1: naive numeric + cluster one-hot -> LogisticRegression
    """
    naive_cols = [
        "avg_sales_card","std_sales_card","cv_sales_card","max_sales","min_sales",
        "max_min_ratio","trend_slope","total_weeks"
    ]
    cols = [c for c in naive_cols if c in df.columns]
    if len(cols) == 0:
        raise ValueError("No naive numeric columns found for M1.")

    X = df[cols].copy()
    X = X.apply(pd.to_numeric, errors="coerce")
    X = X.fillna(X.median(numeric_only=True))

    # cluster one-hot
    if label_col not in df.columns:
        raise ValueError(f"Label column '{label_col}' not found. Columns={df.columns.tolist()[:50]}")

    X = pd.concat(
        [X, pd.get_dummies(df[label_col].astype(int), prefix=label_col, drop_first=False)],
        axis=1
    )

    y = df["success"].to_numpy(dtype=int)

    Xtr, Xte, ytr, yte = train_test_split(
        X.to_numpy(dtype=float), y, test_size=0.2, random_state=seed, stratify=y
    )

    model = LogisticRegression(max_iter=2000, n_jobs=-1)
    model.fit(Xtr, ytr)
    pred = model.predict(Xte)
    return float(f1_score(yte, pred))


# ---------------------------
# 4) main
# ---------------------------
def main():
    # paths (relative to 260204)
    features_csv = ROOT / ".." / "basic_data" / "store_features_for_analysis.csv"
    weekly_primary = ROOT / ".." / "original_data" / "weekly_processed.parquet"
    weekly_fallback = ROOT / ".." / "original_data" / "weekly.parquet"

    # minimal experiment settings
    methods = ["euclidean", "dtw", "kshape"]
    K_list = [4, 5, 6]

    # stability config (keep small for speed; increase later if needed)
    seeds = [41, 42, 43, 44, 45]  # seed stability runs
    boot_seed = 42
    n_boot = 10
    sample_frac = 0.8

    # DTW sampling (critical for feasibility)
    dtw_sample_n = 10000  # adjust to 5000~15000 depending on machine
    rng = np.random.default_rng(42)

    print("[1/4] Loading weekly parquet...")
    df_long = load_weekly_long(weekly_primary, weekly_fallback)
    if not set([STORE_COL, TIME_COL, SALES_COL]).issubset(df_long.columns):
        raise ValueError(
            f"Weekly parquet missing required columns.\n"
            f"Need: {STORE_COL}, {TIME_COL}, {SALES_COL}\n"
            f"Have: {df_long.columns.tolist()[:50]}"
        )

    print("[2/4] Building store×time matrix (this may take some time)...")
    store_ids, time_index, X = build_store_time_matrix(
        df_long, STORE_COL, TIME_COL, SALES_COL, fill_method="interpolate"
    )
    print(f"  n_store={len(store_ids)}, n_dates={len(time_index)}, X.shape={X.shape}")

    # tslearn format: (n, T, 1)
    X_ts = X[:, :, None]
    # scale for fair comparison (shape-focused)
    X_ts = TimeSeriesScalerMeanVariance(mu=0.0, std=1.0).fit_transform(X_ts)

    # DTW sample
    dtw_idx = rng.choice(X_ts.shape[0], size=min(dtw_sample_n, X_ts.shape[0]), replace=False)
    X_ts_dtw = X_ts[dtw_idx]
    store_ids_dtw = store_ids[dtw_idx]

    print("[3/4] Loading features CSV for downstream evaluation...")
    df_feat = load_features_csv(features_csv).copy()
    if "cluster" in df_feat.columns:
        df_feat = df_feat.rename(columns={"cluster": "cluster_old"})
    if "public_id" not in df_feat.columns:
        raise ValueError(f"Features CSV must contain 'public_id'. Columns={df_feat.columns.tolist()[:50]}")

    df_feat["public_id"] = df_feat["public_id"].astype(str)
    df_feat["success"] = make_success(df_feat, metric="growth_rate", thr=1.0)

    rows = []

    print("[4/4] Running method comparison...")
    for K in K_list:
        for method in methods:
            print(f"\n--- Method={method} | K={K} ---")

            # choose data for this method
            if method == "dtw":
                X_use = X_ts_dtw
                store_use = store_ids_dtw
            else:
                X_use = X_ts
                store_use = store_ids

            # stability
            ari_seed, nmi_seed = seed_stability(method, X_use, K, seeds)
            ari_boot = bootstrap_stability(method, X_use, K, boot_seed, n_boot=n_boot, sample_frac=sample_frac)
            print(f"  Seed stability: mean ARI={ari_seed:.4f}, mean NMI={nmi_seed:.4f}")
            print(f"  Bootstrap stability: mean ARI={ari_boot:.4f}")

            # canonical labels (seed=42) for downstream checks
            labels = fit_labels(method, X_use, K, seed=42)

            df_label = pd.DataFrame({
                "public_id": store_use.astype(str),
                "cluster_new": labels.astype(int),
            })

            merged = df_feat.merge(df_label, on="public_id", how="inner")
            if merged.empty:
                raise ValueError(
                    "Merge between features CSV and weekly store IDs returned empty.\n"
                    "Check that 'public_id' matches in both data sources."
                )

            # downstream metrics
            var_sr = success_rate_variance(merged, label_col="cluster_new")
            m1_f1 = predict_M1_f1(merged, label_col="cluster_new", seed=42)

            print(f"  Downstream: success_rate_var={var_sr:.6f}, M1_F1={m1_f1:.4f}, n_merged={len(merged)}")

            rows.append({
                "method": method,
                "K": K,
                "seed_mean_ARI": ari_seed,
                "seed_mean_NMI": nmi_seed,
                "bootstrap_mean_ARI": ari_boot,
                "success_rate_var": var_sr,
                "M1_f1": m1_f1,
                "n_merged": int(len(merged)),
                "note": "DTW uses subsample" if method == "dtw" else "",
            })

    res = pd.DataFrame(rows).sort_values(["K", "method"]).reset_index(drop=True)
    out_path = TBL_DIR / "compare_clustering_methods_minimal.csv"
    res.to_csv(out_path, index=False)
    print(f"\nSaved: {out_path}")

    # best method per K by M1_f1 (downstream)
    best = res.sort_values(["K", "M1_f1"], ascending=[True, False]).groupby("K").head(1)
    best_path = TBL_DIR / "compare_clustering_best_byK.csv"
    best.to_csv(best_path, index=False)
    print(f"Saved: {best_path}")

    print("\n=== Summary (best by K using M1_f1) ===")
    print(best[["K", "method", "M1_f1", "seed_mean_ARI", "bootstrap_mean_ARI", "success_rate_var", "note"]].to_string(index=False))


if __name__ == "__main__":
    main()