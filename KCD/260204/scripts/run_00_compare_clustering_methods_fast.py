from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

from tslearn.clustering import TimeSeriesKMeans, KShape
from tslearn.preprocessing import TimeSeriesScalerMeanVariance


ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "outputs"
TBL_DIR = OUT_DIR / "tables"
for d in [OUT_DIR, TBL_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ---------------------------
# Fixed column mapping (confirmed)
# ---------------------------
STORE_COL = "public_id"
TIME_COL  = "date_id"
SALES_COL = "sales_card"


# ---------------------------
# Speed-optimized benchmark settings
# ---------------------------
METHODS = ["euclidean", "dtw", "kshape"]
K_LIST = [6]  # main K only for fast benchmark

SEEDS = [41, 42, 43]     # reduced
BOOT_SEED = 42
N_BOOT = 3               # reduced
SAMPLE_FRAC = 0.8

SAMPLE_N = 10_000        # same sample for ALL methods for fair + fast comparison
RNG_SEED = 42

# Output paths
OUT_CSV = TBL_DIR / "compare_clustering_methods_fast.csv"


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
    df = df_long[[store_col, time_col, sales_col]].copy()
    df[time_col] = pd.to_datetime(df[time_col])

    pivot = df.pivot_table(index=store_col, columns=time_col, values=sales_col, aggfunc="sum")
    pivot.columns = pd.to_datetime(pivot.columns)
    pivot = pivot.sort_index(axis=1)

    store_ids = pivot.index
    time_index = pivot.columns

    X_df = pivot.astype("float32")
    if fill_method == "interpolate":
        X_df = X_df.interpolate(axis=1, limit_direction="both")
    X_df = X_df.ffill(axis=1).bfill(axis=1).fillna(0.0)

    X = X_df.to_numpy(dtype=np.float32)
    return store_ids, time_index, X


def fit_labels(method: str, X_ts: np.ndarray, K: int, seed: int) -> np.ndarray:
    if method == "euclidean":
        model = TimeSeriesKMeans(n_clusters=K, metric="euclidean", random_state=seed,
                                 n_init=5, max_iter=50)
    elif method == "dtw":
        model = TimeSeriesKMeans(n_clusters=K, metric="dtw", random_state=seed,
                                 n_init=2, max_iter=10)
    elif method == "kshape":
        model = KShape(n_clusters=K, random_state=seed, n_init=5, max_iter=50)
    else:
        raise ValueError(f"Unknown method: {method}")

    return model.fit_predict(X_ts).astype(int)


def seed_stability(method: str, X_ts: np.ndarray, K: int, seeds: list[int]) -> tuple[float, float]:
    labels_list = [fit_labels(method, X_ts, K, s) for s in seeds]
    aris, nmis = [], []
    for i in range(len(labels_list)):
        for j in range(i + 1, len(labels_list)):
            aris.append(adjusted_rand_score(labels_list[i], labels_list[j]))
            nmis.append(normalized_mutual_info_score(labels_list[i], labels_list[j]))
    return float(np.mean(aris)), float(np.mean(nmis))


def bootstrap_stability(method: str, X_ts: np.ndarray, K: int, seed: int,
                        n_boot: int, sample_frac: float) -> float:
    rng = np.random.default_rng(seed)
    n = X_ts.shape[0]
    full_labels = fit_labels(method, X_ts, K, seed)

    aris = []
    for b in range(n_boot):
        idx = rng.choice(n, size=int(n * sample_frac), replace=False)
        labels_b = fit_labels(method, X_ts[idx], K, seed + 1000 + b)
        aris.append(adjusted_rand_score(full_labels[idx], labels_b))
    return float(np.mean(aris))


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
        "avg_sales_card","std_sales_card","cv_sales_card","max_sales","min_sales",
        "max_min_ratio","trend_slope","total_weeks"
    ]
    cols = [c for c in naive_cols if c in df.columns]
    if len(cols) == 0:
        raise ValueError("No naive numeric columns found for M1.")

    X = df[cols].copy()
    X = X.apply(pd.to_numeric, errors="coerce")
    X = X.fillna(X.median(numeric_only=True))

    if label_col not in df.columns:
        raise ValueError(f"Label column '{label_col}' not found.")

    X = pd.concat([X, pd.get_dummies(df[label_col].astype(int), prefix=label_col)], axis=1)

    y = df["success"].to_numpy(dtype=int)

    Xtr, Xte, ytr, yte = train_test_split(
        X.to_numpy(dtype=float), y, test_size=0.2, random_state=seed, stratify=y
    )

    model = LogisticRegression(max_iter=2000, n_jobs=-1)
    model.fit(Xtr, ytr)
    pred = model.predict(Xte)
    return float(f1_score(yte, pred))


def append_row_to_csv(row: dict, path: Path):
    df_row = pd.DataFrame([row])
    if path.exists():
        df_row.to_csv(path, mode="a", header=False, index=False)
    else:
        df_row.to_csv(path, mode="w", header=True, index=False)


def main():
    features_csv = ROOT / ".." / "basic_data" / "store_features_for_analysis.csv"
    weekly_primary = ROOT / ".." / "original_data" / "weekly_processed.parquet"
    weekly_fallback = ROOT / ".." / "original_data" / "weekly.parquet"

    print("[1/4] Load weekly parquet")
    df_long = load_weekly_long(weekly_primary, weekly_fallback)
    req_cols = {STORE_COL, TIME_COL, SALES_COL}
    if not req_cols.issubset(df_long.columns):
        raise ValueError(f"Weekly parquet missing required columns: {req_cols}\nHave: {df_long.columns.tolist()[:50]}")

    print("[2/4] Build store×time matrix")
    store_ids, time_index, X = build_store_time_matrix(df_long, STORE_COL, TIME_COL, SALES_COL)
    print(f"  n_store={len(store_ids)}, n_dates={len(time_index)}, X.shape={X.shape}")

    # tslearn format + scaling
    X_ts = X[:, :, None]
    X_ts = TimeSeriesScalerMeanVariance(mu=0.0, std=1.0).fit_transform(X_ts)

    # fixed sample for ALL methods
    rng = np.random.default_rng(RNG_SEED)
    idx_sample = rng.choice(X_ts.shape[0], size=min(SAMPLE_N, X_ts.shape[0]), replace=False)
    X_ts_s = X_ts[idx_sample]
    store_ids_s = store_ids[idx_sample]
    print(f"  Using fixed sample: n={len(store_ids_s)} (same for all methods)")

    print("[3/4] Load features CSV (downstream)")
    df_feat = load_features_csv(features_csv).copy()
    if "cluster" in df_feat.columns:
        df_feat = df_feat.rename(columns={"cluster": "cluster_old"})
    if "public_id" not in df_feat.columns:
        raise ValueError("Features CSV must contain 'public_id'.")

    df_feat["public_id"] = df_feat["public_id"].astype(str)
    df_feat["success"] = make_success(df_feat, metric="growth_rate", thr=1.0)

    # optional: clear old output to avoid mixing different runs
    # OUT_CSV.unlink(missing_ok=True)  # uncomment if you want fresh file every run

    print("[4/4] Run fast comparison (writes CSV after each row)")
    for K in K_LIST:
        for method in METHODS:
            print(f"\n--- Method={method} | K={K} ---")

            ari_seed, nmi_seed = seed_stability(method, X_ts_s, K, SEEDS)
            ari_boot = bootstrap_stability(method, X_ts_s, K, BOOT_SEED, n_boot=N_BOOT, sample_frac=SAMPLE_FRAC)

            print(f"  Seed stability: mean ARI={ari_seed:.4f}, mean NMI={nmi_seed:.4f}")
            print(f"  Bootstrap stability: mean ARI={ari_boot:.4f}")

            # canonical labels for downstream
            labels = fit_labels(method, X_ts_s, K, seed=42)
            df_label = pd.DataFrame({"public_id": store_ids_s.astype(str), "cluster_new": labels.astype(int)})

            merged = df_feat.merge(df_label, on="public_id", how="inner")
            if merged.empty:
                raise ValueError("Merge empty. Check public_id consistency between weekly and features.")

            var_sr = success_rate_variance(merged, label_col="cluster_new")
            m1_f1 = predict_M1_f1(merged, label_col="cluster_new", seed=42)

            print(f"  Downstream: success_rate_var={var_sr:.6f}, M1_F1={m1_f1:.4f}, n_merged={len(merged)}")

            row = {
                "method": method,
                "K": K,
                "seed_mean_ARI": ari_seed,
                "seed_mean_NMI": nmi_seed,
                "bootstrap_mean_ARI": ari_boot,
                "success_rate_var": var_sr,
                "M1_f1": m1_f1,
                "n_sample": int(len(store_ids_s)),
                "n_merged": int(len(merged)),
                "note": "fixed 10k sample for all methods",
            }
            append_row_to_csv(row, OUT_CSV)
            print(f"  Appended -> {OUT_CSV}")

    print("\nDone.")
    if OUT_CSV.exists():
        df_out = pd.read_csv(OUT_CSV)
        print("\nCurrent results:")
        print(df_out.sort_values(["K", "method"]).to_string(index=False))


if __name__ == "__main__":
    main()