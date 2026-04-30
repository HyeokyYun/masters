"""Step 04 — 클러스터링 품질 개선.

K-Shape / K-Means / GMM 3가지를 K=3~15 범위에서 비교하고,
UDX label과의 NMI·ARI로 외부 검증. 최적 K와 방법 선정.

Output:
  outputs/tables/clustering_comparison.csv
  outputs/tables/clustering_external_validation.csv
  outputs/figures/clustering_metrics.png
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import (adjusted_rand_score, calinski_harabasz_score,
                             davies_bouldin_score, normalized_mutual_info_score,
                             silhouette_score)
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg  # noqa: E402

plt.rcParams.update(cfg.FIG_STYLE)

try:
    from tslearn.clustering import KShape
    from tslearn.preprocessing import TimeSeriesScalerMeanVariance
    HAS_TSLEARN = True
except ImportError:
    HAS_TSLEARN = False


def build_trajectory_matrix(panel: pd.DataFrame, feats: pd.DataFrame, weeks: int = 60):
    panel = panel[panel["observed_week_idx"] < weeks].copy()
    pivot = panel.pivot_table(index="public_id", columns="observed_week_idx",
                              values="sales_card_mm", aggfunc="mean")
    pivot = pivot.dropna(axis=1, thresh=int(len(pivot) * 0.6))
    pivot = pivot.dropna(axis=0, thresh=int(pivot.shape[1] * 0.85))
    pivot = pivot.fillna(pivot.median(axis=0))
    pivot.index = pivot.index.astype(str)

    feats = feats.copy()
    feats["public_id"] = feats["public_id"].astype(str)
    common = pivot.index.intersection(feats["public_id"])
    pivot = pivot.loc[common]
    labels_df = feats.set_index("public_id").loc[common, ["label", "outcome_3"]]

    matrix = pivot.to_numpy()
    print(f"[04] Trajectory matrix: {matrix.shape}")
    return matrix, pivot.index.tolist(), labels_df


def evaluate(matrix: np.ndarray, labels: np.ndarray) -> dict:
    if len(set(labels)) < 2:
        return {"silhouette": np.nan, "davies_bouldin": np.nan, "calinski_harabasz": np.nan}
    try:
        sil = silhouette_score(matrix, labels, metric="euclidean",
                              sample_size=min(5000, len(matrix)), random_state=cfg.SEED)
    except Exception:
        sil = np.nan
    return {
        "silhouette": float(sil),
        "davies_bouldin": float(davies_bouldin_score(matrix, labels)),
        "calinski_harabasz": float(calinski_harabasz_score(matrix, labels)),
    }


def run_kmeans(matrix, k):
    model = KMeans(n_clusters=k, n_init=15, max_iter=500, random_state=cfg.SEED)
    return model.fit_predict(matrix), model


def run_kshape(matrix, k, max_n=8000):
    if not HAS_TSLEARN:
        return None, None
    if len(matrix) > max_n:
        rng = np.random.RandomState(cfg.SEED)
        idx = rng.choice(len(matrix), max_n, replace=False)
        sub = matrix[idx]
    else:
        sub = matrix
        idx = np.arange(len(matrix))
    series = sub.reshape(sub.shape[0], sub.shape[1], 1)
    series = TimeSeriesScalerMeanVariance().fit_transform(series)
    model = KShape(n_clusters=k, max_iter=30, random_state=cfg.SEED, verbose=0)
    labels = model.fit_predict(series)
    return labels, (idx, model)


def run_gmm(matrix, k):
    model = GaussianMixture(n_components=k, covariance_type="full",
                           random_state=cfg.SEED, max_iter=200, n_init=3)
    labels = model.fit_predict(matrix)
    bic = model.bic(matrix)
    aic = model.aic(matrix)
    return labels, (model, bic, aic)


def main():
    panel = pd.read_parquet(cfg.PANEL_PATH)
    panel["public_id"] = panel["public_id"].astype(str)
    feats = pd.read_csv(cfg.FEATURES_PATH)

    matrix, store_ids, labels_df = build_trajectory_matrix(panel, feats, weeks=60)
    scaled = StandardScaler().fit_transform(matrix)

    rows = []
    external_rows = []
    for k in cfg.K_RANGE:
        km_labels, _ = run_kmeans(scaled, k)
        km_metrics = evaluate(scaled, km_labels)
        km_metrics.update({"method": "KMeans", "K": k})
        rows.append(km_metrics)
        external_rows.append({
            "method": "KMeans", "K": k,
            "nmi_vs_outcome": normalized_mutual_info_score(labels_df["outcome_3"], km_labels),
            "ari_vs_outcome": adjusted_rand_score(labels_df["outcome_3"], km_labels),
            "nmi_vs_label": normalized_mutual_info_score(labels_df["label"], km_labels),
            "ari_vs_label": adjusted_rand_score(labels_df["label"], km_labels),
        })

        gmm_labels, (gmm_model, bic, aic) = run_gmm(scaled, k)
        gmm_metrics = evaluate(scaled, gmm_labels)
        gmm_metrics.update({"method": "GMM", "K": k, "bic": float(bic), "aic": float(aic)})
        rows.append(gmm_metrics)
        external_rows.append({
            "method": "GMM", "K": k,
            "nmi_vs_outcome": normalized_mutual_info_score(labels_df["outcome_3"], gmm_labels),
            "ari_vs_outcome": adjusted_rand_score(labels_df["outcome_3"], gmm_labels),
            "nmi_vs_label": normalized_mutual_info_score(labels_df["label"], gmm_labels),
            "ari_vs_label": adjusted_rand_score(labels_df["label"], gmm_labels),
        })

        if HAS_TSLEARN:
            ks_labels, meta = run_kshape(scaled, k)
            if ks_labels is not None:
                idx, _ = meta
                sub = scaled[idx]
                ks_metrics = evaluate(sub, ks_labels)
                ks_metrics.update({"method": "KShape", "K": k})
                rows.append(ks_metrics)
                sub_outcome = labels_df["outcome_3"].iloc[idx]
                sub_label = labels_df["label"].iloc[idx]
                external_rows.append({
                    "method": "KShape", "K": k,
                    "nmi_vs_outcome": normalized_mutual_info_score(sub_outcome, ks_labels),
                    "ari_vs_outcome": adjusted_rand_score(sub_outcome, ks_labels),
                    "nmi_vs_label": normalized_mutual_info_score(sub_label, ks_labels),
                    "ari_vs_label": adjusted_rand_score(sub_label, ks_labels),
                })
        print(f"  K={k}: KMeans sil={km_metrics['silhouette']:.3f}  "
              f"GMM sil={gmm_metrics['silhouette']:.3f}  bic={bic:.0f}")

    comparison = pd.DataFrame(rows)
    comparison.to_csv(cfg.TABLE_DIR / "clustering_comparison.csv", index=False, encoding="utf-8-sig")
    external = pd.DataFrame(external_rows)
    external.to_csv(cfg.TABLE_DIR / "clustering_external_validation.csv", index=False, encoding="utf-8-sig")

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for method in comparison["method"].unique():
        sub = comparison[comparison["method"] == method].sort_values("K")
        axes[0, 0].plot(sub["K"], sub["silhouette"], "o-", label=method)
        axes[0, 1].plot(sub["K"], sub["davies_bouldin"], "o-", label=method)
        axes[1, 0].plot(sub["K"], sub["calinski_harabasz"], "o-", label=method)
    gmm_sub = comparison[comparison["method"] == "GMM"].sort_values("K")
    if "bic" in gmm_sub.columns and gmm_sub["bic"].notna().any():
        axes[1, 1].plot(gmm_sub["K"], gmm_sub["bic"], "o-", label="BIC")
        axes[1, 1].plot(gmm_sub["K"], gmm_sub["aic"], "o-", label="AIC")

    axes[0, 0].set_title("Silhouette (higher = better)")
    axes[0, 1].set_title("Davies-Bouldin (lower = better)")
    axes[1, 0].set_title("Calinski-Harabasz (higher = better)")
    axes[1, 1].set_title("GMM BIC / AIC (lower = better)")
    for ax in axes.flat:
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlabel("K")
    fig.tight_layout()
    fig.savefig(cfg.FIGURE_DIR / "clustering_metrics.png")
    plt.close(fig)
    print("[04] clustering_metrics.png saved")

    best_rows = []
    for method in comparison["method"].unique():
        sub = comparison[comparison["method"] == method].dropna(subset=["silhouette"])
        if sub.empty:
            continue
        best = sub.loc[sub["silhouette"].idxmax()]
        best_rows.append({"method": method, "best_K": int(best["K"]),
                         "silhouette": best["silhouette"],
                         "davies_bouldin": best["davies_bouldin"]})
    pd.DataFrame(best_rows).to_csv(cfg.TABLE_DIR / "clustering_best_configs.csv", index=False, encoding="utf-8-sig")
    print(pd.DataFrame(best_rows).to_string(index=False))


if __name__ == "__main__":
    main()
