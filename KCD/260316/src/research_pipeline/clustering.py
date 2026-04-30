from __future__ import annotations

from math import ceil
from typing import Callable, Dict

import matplotlib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from research_pipeline.config import get_work_dir
from research_pipeline.data_prep import build_analysis_inputs, slice_panel_by_week
from research_pipeline.lifecycle import build_lifecycle_bundle

try:
    from tslearn.clustering import KShape, TimeSeriesKMeans

    HAS_TSLEARN = True
except Exception:
    HAS_TSLEARN = False


def build_trajectory_matrix(panel: pd.DataFrame, max_weeks: int, min_weeks: int) -> pd.DataFrame:
    work = slice_panel_by_week(panel, 0, max_weeks)
    pivot = work.pivot_table(index="public_id", columns="week_index", values="sales_minmax", aggfunc="mean")
    expected_cols = list(range(max_weeks))
    pivot = pivot.reindex(columns=expected_cols)
    valid = pivot.notna().sum(axis=1) >= min_weeks
    pivot = pivot.loc[valid].copy()
    pivot = pivot.apply(lambda col: col.fillna(col.median()), axis=0).fillna(0.0)
    return pivot


def cluster_trajectories(matrix: pd.DataFrame, n_clusters: int, random_state: int) -> tuple[np.ndarray, np.ndarray, str]:
    x = matrix.to_numpy(dtype=float)

    if HAS_TSLEARN:
        x3 = x[:, :, None]
        for method_name, estimator in [
            ("kshape", KShape(n_clusters=n_clusters, random_state=random_state, n_init=3)),
            (
                "dtw_kmeans",
                TimeSeriesKMeans(n_clusters=n_clusters, metric="dtw", random_state=random_state, n_init=2),
            ),
        ]:
            try:
                labels = estimator.fit_predict(x3)
                centers = np.squeeze(estimator.cluster_centers_, axis=-1)
                return labels, centers, method_name
            except Exception:
                continue

    estimator = KMeans(n_clusters=n_clusters, n_init=15, random_state=random_state)
    labels = estimator.fit_predict(x)
    return labels, estimator.cluster_centers_, "kmeans"


def make_cluster_profiles(
    labels_df: pd.DataFrame,
    analysis_table: pd.DataFrame,
) -> pd.DataFrame:
    merged = analysis_table.merge(labels_df, on="public_id", how="inner")
    numeric_cols = [
        "avg_sales_total",
        "cv_sales_total",
        "growth_rate",
        "avg_customer",
        "new_customer_ratio",
        "delivery_ratio",
    ]
    numeric_cols = [c for c in numeric_cols if c in merged.columns]
    profile = (
        merged.groupby("cluster")[numeric_cols]
        .agg(["mean", "median"])
        .reset_index()
    )
    profile.columns = ["cluster"] + [f"{a}_{b}" for a, b in profile.columns.tolist()[1:]]
    life_cycle_dist = pd.crosstab(merged["cluster"], merged["life_cycle_category"], normalize="index").reset_index()
    return profile.merge(life_cycle_dist, on="cluster", how="left")


def compute_empirical_cluster_centers(matrix: pd.DataFrame, labels: np.ndarray) -> pd.DataFrame:
    work = matrix.copy()
    work["cluster"] = labels.astype(int)
    centers = work.groupby("cluster", sort=True).mean(numeric_only=True)
    centers.columns = [int(col) for col in centers.columns]
    return centers


def save_cluster_plot(centers: pd.DataFrame, method: str, out_path) -> None:
    fig, ax = plt.subplots(figsize=(11, 6))
    x = centers.columns.to_numpy(dtype=int)
    for cluster_id, row in centers.iterrows():
        ax.plot(x, row.to_numpy(dtype=float), linewidth=2, label=f"C{int(cluster_id)}")
    ax.set_title(f"Average Trajectories by Cluster ({method}; empirical mean)")
    ax.set_xlabel("Week Index")
    ax.set_ylabel("Normalized Sales")
    ax.set_ylim(-0.05, 1.05)
    ax.legend(ncol=3, frameon=False)
    fig.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def save_cluster_panel_plot(
    matrix: pd.DataFrame,
    labels: np.ndarray,
    method: str,
    out_path,
    max_lines_per_cluster: int = 600,
    random_state: int = 42,
) -> None:
    work = matrix.copy()
    work["cluster"] = labels.astype(int)
    cluster_ids = sorted(work["cluster"].unique().tolist())
    n_clusters = len(cluster_ids)
    ncols = min(3, max(1, n_clusters))
    nrows = ceil(n_clusters / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(6.5 * ncols, 4.6 * nrows), sharex=True, sharey=True)
    axes_arr = np.atleast_1d(axes).ravel()
    x = np.arange(matrix.shape[1], dtype=int)
    rng = np.random.default_rng(random_state)

    for ax, cluster_id in zip(axes_arr, cluster_ids):
        cluster_frame = work.loc[work["cluster"] == cluster_id, matrix.columns]
        values = cluster_frame.to_numpy(dtype=float)
        if len(cluster_frame) > max_lines_per_cluster:
            sample_idx = rng.choice(len(cluster_frame), size=max_lines_per_cluster, replace=False)
            display_values = values[sample_idx]
        else:
            display_values = values

        for row in display_values:
            ax.plot(x, row, color="0.55", alpha=0.05, linewidth=0.45)
        ax.plot(x, values.mean(axis=0), color="red", linewidth=2.0)
        ax.set_title(f"Cluster {cluster_id} (n={len(cluster_frame):,})")
        ax.set_xlabel("Week")
        ax.set_ylabel("Normalized Sales Ratio")
        ax.set_ylim(-0.05, 1.05)
        ax.grid(alpha=0.2, linewidth=0.5)

    for ax in axes_arr[n_clusters:]:
        ax.axis("off")

    fig.suptitle(f"Cluster Trajectories ({method}; gray=member stores, red=empirical mean)", fontsize=16, y=0.995)
    fig.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def run_clustering_bundle(cfg: Dict[str, object], log: Callable[[str], None]) -> Dict[str, pd.DataFrame]:
    work_dir = get_work_dir()
    panel_path = work_dir / "outputs" / "tables" / "store_week_panel.parquet"
    lifecycle_path = work_dir / "outputs" / "tables" / "lifecycle_analysis_table.csv"

    if panel_path.exists():
        panel = pd.read_parquet(panel_path)
    else:
        log("Panel not found. Building Step 1 outputs on the fly.")
        panel = build_analysis_inputs(cfg, log)["panel"]

    if lifecycle_path.exists():
        analysis_table = pd.read_csv(lifecycle_path)
        if "public_id" in analysis_table.columns:
            analysis_table["public_id"] = analysis_table["public_id"].astype(str)
    else:
        log("Lifecycle table not found. Building Step 2 outputs on the fly.")
        analysis_table = build_lifecycle_bundle(cfg, log)["analysis_table"]

    max_weeks = int(cfg["analysis"]["max_weeks"])
    min_weeks = int(cfg["analysis"]["min_weeks"])
    n_clusters = int(cfg["analysis"]["cluster_k"])
    random_state = int(cfg["analysis"]["random_state"])

    matrix = build_trajectory_matrix(panel, max_weeks=max_weeks, min_weeks=min_weeks)
    labels, centers, method = cluster_trajectories(matrix, n_clusters=n_clusters, random_state=random_state)
    labels_df = pd.DataFrame({"public_id": matrix.index.astype(str), "cluster": labels.astype(int), "cluster_method": method})
    empirical_centers = compute_empirical_cluster_centers(matrix, labels)

    profiles = make_cluster_profiles(labels_df, analysis_table)
    center_rows = []
    for cluster_id, row in empirical_centers.iterrows():
        for week_index, value in row.items():
            center_rows.append({"cluster": cluster_id, "week_index": week_index, "center_value": float(value)})
    centers_df = pd.DataFrame(center_rows)

    metrics = [{"metric": "n_stores", "value": float(len(matrix))}, {"metric": "n_clusters", "value": float(n_clusters)}]
    if len(np.unique(labels)) > 1 and len(matrix) > n_clusters:
        try:
            metrics.append({"metric": "silhouette", "value": float(silhouette_score(matrix, labels))})
        except Exception:
            metrics.append({"metric": "silhouette", "value": np.nan})
    else:
        metrics.append({"metric": "silhouette", "value": np.nan})

    save_cluster_plot(empirical_centers, method, work_dir / "outputs" / "figures" / "trajectory_cluster_means.png")
    save_cluster_panel_plot(
        matrix,
        labels,
        method,
        work_dir / "outputs" / "figures" / "trajectory_cluster_panels.png",
        random_state=random_state,
    )
    log(f"Clustered stores: {len(labels_df):,} via {method}")
    return {
        "labels": labels_df,
        "profiles": profiles,
        "centers": centers_df,
        "metrics": pd.DataFrame(metrics),
    }
