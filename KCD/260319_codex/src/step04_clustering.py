from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score

from src import config as cfg

warnings.filterwarnings("ignore")

try:
    from tslearn.clustering import KShape, TimeSeriesKMeans
    from tslearn.preprocessing import TimeSeriesScalerMeanVariance

    HAS_TSLEARN = True
except ImportError:
    HAS_TSLEARN = False


def build_trajectory_matrix(ts: pd.DataFrame, value_col: str = "sales_card_mm"):
    sub = ts[ts["weeks_since_open"] < cfg.MAX_WEEKS].copy()
    pivot = (
        sub.drop_duplicates(["public_id", "weeks_since_open"])
        .pivot_table(index="public_id", columns="weeks_since_open", values=value_col, aggfunc="mean")
    )
    pivot = pivot.dropna(axis=1, thresh=int(len(pivot) * 0.6))
    pivot = pivot.dropna(axis=0, thresh=int(pivot.shape[1] * 0.85))
    matrix = pivot.fillna(pivot.median(axis=0)).to_numpy()
    store_ids = pivot.index.astype(str).tolist()
    categories = ["기타"] * len(store_ids)
    if "classification__kcd_v3__depth_2_name" in sub.columns:
        mapping = sub.groupby("public_id")["classification__kcd_v3__depth_2_name"].first().to_dict()
        categories = [str(mapping.get(store_id, "기타")) for store_id in store_ids]
    return matrix, store_ids, categories


def _stratified_sample(matrix, store_ids, categories, max_n=None):
    max_n = max_n or cfg.CLUSTER_MAX_STORES
    n = len(matrix)
    if n <= max_n:
        return matrix, store_ids, np.arange(n)

    rng = np.random.RandomState(cfg.SEED)
    categories = np.asarray(categories)
    selected = []
    for category in np.unique(categories):
        idx = np.where(categories == category)[0]
        take = max(1, int(len(idx) / n * max_n))
        if take >= len(idx):
            selected.extend(idx.tolist())
        else:
            selected.extend(rng.choice(idx, take, replace=False).tolist())
    selected = np.array(sorted(set(selected)))
    if len(selected) > max_n:
        selected = rng.choice(selected, max_n, replace=False)
        selected.sort()
    return matrix[selected], [store_ids[i] for i in selected], selected


def _evaluate(matrix: np.ndarray, labels: np.ndarray) -> dict[str, float]:
    n_labels = len(set(labels))
    if n_labels < 2 or n_labels >= len(matrix):
        return {"silhouette": np.nan, "davies_bouldin": np.nan, "calinski_harabasz": np.nan}
    return {
        "silhouette": silhouette_score(
            matrix,
            labels,
            metric="euclidean",
            sample_size=min(5000, len(matrix)),
            random_state=cfg.SEED,
        ),
        "davies_bouldin": davies_bouldin_score(matrix, labels),
        "calinski_harabasz": calinski_harabasz_score(matrix, labels),
    }


def _print_cluster_stats(labels, centers, prefix=""):
    for cluster_id in range(len(centers)):
        center = np.asarray(centers[cluster_id]).flatten()
        if len(center) < 2:
            continue
        slope, *_ = stats.linregress(np.arange(len(center), dtype=float), center)
        count = int((np.asarray(labels) == cluster_id).sum())
        print(
            f"  {prefix}C{cluster_id}: n={count:,} ({count/len(labels)*100:.1f}%) "
            f"slope={slope:+.5f} start={center[:8].mean():.3f} end={center[-8:].mean():.3f}"
        )


def _kmeans(matrix: np.ndarray, n_clusters: int):
    model = KMeans(n_clusters=n_clusters, n_init=15, max_iter=500, random_state=cfg.SEED)
    labels = model.fit_predict(matrix)
    return labels, model


def _dtw(matrix: np.ndarray, n_clusters: int):
    if not HAS_TSLEARN:
        return _kmeans(matrix, n_clusters)
    series = matrix.reshape(matrix.shape[0], matrix.shape[1], 1)
    model = TimeSeriesKMeans(
        n_clusters=n_clusters,
        metric="dtw",
        n_init=cfg.DTW_N_INIT,
        max_iter=30,
        random_state=cfg.SEED,
        verbose=0,
    )
    labels = model.fit_predict(series)
    return labels, model


def _kshape(matrix: np.ndarray, n_clusters: int):
    if not HAS_TSLEARN:
        return _kmeans(matrix, n_clusters)
    series = matrix.reshape(matrix.shape[0], matrix.shape[1], 1)
    series = TimeSeriesScalerMeanVariance().fit_transform(series)
    model = KShape(n_clusters=n_clusters, max_iter=50, random_state=cfg.SEED, verbose=0)
    labels = model.fit_predict(series)
    return labels, model


def run_clustering(ts: pd.DataFrame, labeled: pd.DataFrame | None = None):
    matrix, store_ids, categories = build_trajectory_matrix(ts)
    eval_rows = []
    all_models: dict[int, object] = {}

    print(f"[Step04] 궤적 행렬: {matrix.shape[0]:,}개 매장 × {matrix.shape[1]}주")
    for k in cfg.CLUSTER_K_RANGE:
        labels_k, model_k = _kmeans(matrix, k)
        metrics = _evaluate(matrix, labels_k)
        metrics["K"] = k
        eval_rows.append(metrics)
        all_models[k] = model_k

        pd.DataFrame({"public_id": store_ids, "traj_cluster": labels_k}).to_csv(
            cfg.TABLE_DIR / f"cluster_labels_K{k}.csv", index=False, encoding="utf-8-sig"
        )
        pd.DataFrame(model_k.cluster_centers_).to_csv(
            cfg.TABLE_DIR / f"cluster_centers_K{k}.csv", index=False, encoding="utf-8-sig"
        )

    eval_df = pd.DataFrame(eval_rows).sort_values("K").reset_index(drop=True)
    eval_df.to_csv(cfg.TABLE_DIR / "cluster_evaluation.csv", index=False, encoding="utf-8-sig")
    best_k = int(eval_df.loc[eval_df["silhouette"].idxmax(), "K"])
    best_model = all_models[best_k]
    best_labels = best_model.predict(matrix)
    cluster_df = pd.DataFrame({"public_id": store_ids, "traj_cluster": best_labels})
    cluster_df.to_csv(cfg.TABLE_DIR / "cluster_labels.csv", index=False, encoding="utf-8-sig")

    _print_cluster_stats(best_labels, best_model.cluster_centers_)

    sub_matrix, _, _ = _stratified_sample(matrix, store_ids, categories)
    dtw_labels, _ = _dtw(sub_matrix, best_k)
    kshape_labels, _ = _kshape(sub_matrix, best_k)
    comparison = pd.DataFrame(
        [
            {"method": "KMeans-Euclidean (전체)", **_evaluate(matrix, best_labels)},
            {"method": "DTW-KMeans (층화추출)", **_evaluate(sub_matrix, dtw_labels)},
            {"method": "K-Shape (층화추출)", **_evaluate(sub_matrix, kshape_labels)},
        ]
    )
    comparison.to_csv(cfg.TABLE_DIR / "cluster_method_comparison.csv", index=False, encoding="utf-8-sig")

    if labeled is not None:
        merged = labeled.merge(cluster_df, on="public_id", how="inner")
        final_ct = pd.crosstab(merged["final_code"], merged["traj_cluster"], margins=True)
        final_ct.to_csv(cfg.TABLE_DIR / "final_code_cluster_crosstab.csv", encoding="utf-8-sig")

        pattern_ct = pd.crosstab(merged["Pattern_label"], merged["traj_cluster"], margins=True)
        pattern_ct.to_csv(cfg.TABLE_DIR / "pattern_cluster_crosstab.csv", encoding="utf-8-sig")

    return {"cluster_labels": cluster_df, "cluster_evaluation": eval_df, "comparison": comparison}


def load_or_run_clustering(ts: pd.DataFrame, labeled: pd.DataFrame | None = None):
    labels_path = cfg.TABLE_DIR / "cluster_labels.csv"
    eval_path = cfg.TABLE_DIR / "cluster_evaluation.csv"
    if labels_path.exists() and eval_path.exists():
        cluster_df = pd.read_csv(labels_path)
        if labeled is not None:
            merged = labeled.merge(cluster_df, on="public_id", how="inner")
            pd.crosstab(merged["final_code"], merged["traj_cluster"], margins=True).to_csv(
                cfg.TABLE_DIR / "final_code_cluster_crosstab.csv", encoding="utf-8-sig"
            )
            pd.crosstab(merged["Pattern_label"], merged["traj_cluster"], margins=True).to_csv(
                cfg.TABLE_DIR / "pattern_cluster_crosstab.csv", encoding="utf-8-sig"
            )
        return {
            "cluster_labels": cluster_df,
            "cluster_evaluation": pd.read_csv(eval_path),
            "comparison": pd.read_csv(cfg.TABLE_DIR / "cluster_method_comparison.csv")
            if (cfg.TABLE_DIR / "cluster_method_comparison.csv").exists()
            else None,
        }
    return run_clustering(ts, labeled)
