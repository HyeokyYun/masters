"""
WEEKLY-PARQUET clustering pipeline (track B) — K-Shape + stability.
Run from 260204: python scripts/run_02_cluster_fix.py
Self-contained: no project src imports.

Data file is not modified. Column mapping is done in code:
- Store: config id_col_store, or first of (public_id, store_id) present.
- Week: config time_col_week, or day_after1, or computed from date_id (week index).
- Sales: config y_col_sales, or first of (sales_card, sales) present.
"""
from pathlib import Path
import yaml
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime
from tslearn.clustering import KShape
from tslearn.preprocessing import TimeSeriesScalerMeanVariance
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

ROOT = Path(__file__).resolve().parent.parent

LOG_PATH = ROOT / "outputs" / "logs" / "run_02_cluster_fix.log"
TABLES_DIR = ROOT / "outputs" / "tables"
FIGURES_DIR = ROOT / "outputs" / "figures"

# Fallback names when config keys are missing in the parquet (data file unchanged)
STORE_CANDIDATES = ["public_id", "store_id"]
WEEK_CANDIDATES = ["week_id", "day_after1"]
SALES_CANDIDATES = ["sales_card", "sales"]


def load_config():
    with open(ROOT / "configs" / "base.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_weekly_path(cfg):
    data = cfg.get("data", {})
    primary = ROOT / data.get("weekly_parquet_primary", "../original_data/weekly_processed.parquet")
    if primary.exists():
        return primary
    fallback = ROOT / data.get("weekly_parquet_fallback", "../original_data/weekly.parquet")
    return fallback


def resolve_weekly_columns(df, data_cfg):
    """
    Resolve store, week, sales columns from parquet without changing the file.
    If week column is missing but date_id exists, compute week index (1,2,...) in-place on a copy.
    Returns (df, col_store, col_week, col_sales). df may have new column _week_index.
    """
    df = df.copy()
    cols = set(df.columns)

    # Store
    col_store = data_cfg.get("id_col_store") or "public_id"
    if col_store not in cols:
        for c in STORE_CANDIDATES:
            if c in cols:
                col_store = c
                break
        else:
            raise ValueError(
                "Weekly parquet: no store-id column found. "
                f"Tried: {STORE_CANDIDATES}. Actual columns: {sorted(cols)!r}."
            )

    # Week: config → day_after1 → week_id → from date_id
    col_week = data_cfg.get("time_col_week")
    if col_week and col_week in cols:
        pass
    elif "day_after1" in cols:
        col_week = "day_after1"
    elif "week_id" in cols:
        col_week = "week_id"
    elif "date_id" in cols:
        # Derive week index from date_id (same logic as prepare_data: week 1, 2, ...)
        df["date_id"] = pd.to_datetime(df["date_id"])
        min_date = df["date_id"].min()
        df["_week_index"] = ((df["date_id"] - min_date).dt.days // 7) + 1
        df = df[df["_week_index"] != 0]
        col_week = "_week_index"
    else:
        raise ValueError(
            "Weekly parquet: no week/time column found. "
            f"Tried: week_id, day_after1, or date_id to derive week. Actual columns: {sorted(cols)!r}."
        )

    # Sales: config → sales_card → sales
    col_sales = data_cfg.get("y_col_sales")
    if col_sales and col_sales in cols:
        pass
    else:
        for c in SALES_CANDIDATES:
            if c in cols:
                col_sales = c
                break
        else:
            raise ValueError(
                "Weekly parquet: no sales column found. "
                f"Tried: {SALES_CANDIDATES}. Actual columns: {sorted(cols)!r}."
            )

    return df, col_store, col_week, col_sales


def build_store_week_matrix(df, col_store, col_week, col_sales, fill_method="interpolate"):
    """Pivot to store x week, then fill missing: interpolate then ffill then bfill."""
    wide = df.pivot_table(index=col_store, columns=col_week, values=col_sales, aggfunc="mean")
    wide = wide.sort_index(axis=0).sort_index(axis=1)
    # Fill: interpolate along columns (weeks), then forward/back fill
    if fill_method == "interpolate":
        wide = wide.T.interpolate(method="linear").ffill().bfill().T
    else:
        wide = wide.ffill(axis=1).bfill(axis=1)
    # Any remaining NaN (e.g. all-NaN rows) fill with 0
    wide = wide.fillna(0)
    return wide


def main():
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    def log(msg: str):
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    cfg = load_config()
    data_cfg = cfg.get("data", {})
    clust_cfg = cfg.get("clustering", {})

    weekly_path = get_weekly_path(cfg)
    if not weekly_path.exists():
        log(f"ERROR: Weekly parquet not found. Tried: {weekly_path}")
        return

    log(f"Loading weekly data from {weekly_path}")
    df = pd.read_parquet(weekly_path)
    df, col_store, col_week, col_sales = resolve_weekly_columns(df, data_cfg)
    log(f"Using columns: store={col_store!r}, week={col_week!r}, sales={col_sales!r}")

    fill_method = clust_cfg.get("fill_method", "interpolate")
    log("Building store x week matrix (fill: interpolate then ffill/bfill).")
    wide = build_store_week_matrix(df, col_store, col_week, col_sales, fill_method=fill_method)
    store_ids = wide.index.tolist()
    n_stores, n_weeks = wide.shape
    log(f"Matrix shape: {n_stores} stores x {n_weeks} weeks.")

    # tslearn expects (n_ts, sz, d)
    X_raw = np.asarray(wide, dtype=float)
    if X_raw.ndim == 2:
        X_raw = X_raw[:, :, np.newaxis]
    scaler = TimeSeriesScalerMeanVariance(mu=0.0, std=1.0)
    X = scaler.fit_transform(X_raw)

    k_list = clust_cfg.get("k_list", [1, 2, 3])
    seed = clust_cfg.get("seed", 42)
    n_seed_runs = clust_cfg.get("n_seed_runs", 10)
    n_boot = clust_cfg.get("n_boot", 20)
    sample_frac = clust_cfg.get("sample_frac", 0.8)

    stability_rows = []

    for K in k_list:
        log(f"--- K = {K} ---")

        # Reference run (fixed seed) for labels and centroids
        ks_ref = KShape(n_clusters=K, random_state=seed, n_init=1)
        labels_ref = ks_ref.fit_predict(X)
        centers_ref = ks_ref.cluster_centers_

        # Seed stability: n_seed_runs different seeds, pairwise ARI and NMI
        rng = np.random.RandomState(seed)
        seed_labels = []
        for _ in range(n_seed_runs):
            s = int(rng.randint(0, 2**31))
            ks_s = KShape(n_clusters=K, random_state=s, n_init=1)
            seed_labels.append(ks_s.fit_predict(X))
        aris, nmis = [], []
        for i in range(len(seed_labels)):
            for j in range(i + 1, len(seed_labels)):
                aris.append(adjusted_rand_score(seed_labels[i], seed_labels[j]))
                nmis.append(normalized_mutual_info_score(seed_labels[i], seed_labels[j]))
        seed_ari = float(np.mean(aris)) if aris else 0.0
        seed_nmi = float(np.mean(nmis)) if nmis else 0.0
        log(f"  Seed stability: mean ARI={seed_ari:.4f}, mean NMI={seed_nmi:.4f}")

        # Bootstrap stability: sample stores, recluster, ARI vs full-sample labels on subset
        boot_aris = []
        for b in range(n_boot):
            rng_b = np.random.RandomState(seed + 1000 + b)
            idx = rng_b.choice(n_stores, size=int(n_stores * sample_frac), replace=False)
            idx.sort()
            X_boot = X[idx]
            labels_full_subset = labels_ref[idx]
            ks_b = KShape(n_clusters=K, random_state=seed + b, n_init=1)
            labels_boot = ks_b.fit_predict(X_boot)
            boot_aris.append(adjusted_rand_score(labels_full_subset, labels_boot))
        boot_ari = float(np.mean(boot_aris))
        log(f"  Bootstrap stability: mean ARI={boot_ari:.4f}")

        stability_rows.append({
            "K": K,
            "seed_stability_ARI": seed_ari,
            "seed_stability_NMI": seed_nmi,
            "bootstrap_stability_ARI": boot_ari,
        })

        # Save store labels (reference run)
        labels_df = pd.DataFrame({col_store: store_ids, "cluster": labels_ref})
        labels_df.to_parquet(TABLES_DIR / f"store_cluster_labels_K{K}.parquet", index=False)
        log(f"  Saved {TABLES_DIR / f'store_cluster_labels_K{K}.parquet'}")

        # Figure: cluster means (centroids)
        fig, ax = plt.subplots()
        # centers_ref shape (n_clusters, n_weeks, 1)
        if centers_ref.ndim == 3:
            cents = centers_ref[:, :, 0]
        else:
            cents = centers_ref
        for k in range(K):
            ax.plot(cents[k], label=f"Cluster {k}", alpha=0.8)
        ax.set_xlabel("Week")
        ax.set_ylabel("Centroid (scaled)")
        ax.set_title(f"K-Shape cluster means (K={K})")
        ax.legend()
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / f"cluster_means_K{K}.png", bbox_inches="tight")
        plt.close(fig)
        log(f"  Saved {FIGURES_DIR / f'cluster_means_K{K}.png'}")

    summary_df = pd.DataFrame(stability_rows)
    summary_df.to_csv(TABLES_DIR / "cluster_stability_summary.csv", index=False)
    log(f"Saved {TABLES_DIR / 'cluster_stability_summary.csv'}")
    log("run_02_cluster_fix finished.")


if __name__ == "__main__":
    main()
