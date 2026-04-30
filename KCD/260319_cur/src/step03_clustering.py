"""
Step 03 ─ 시계열 클러스터링
  ● DTW 기반 TimeSeriesKMeans  (tslearn)
  ● K-Shape 클러스터링          (tslearn, 대안)
  ● 평가: Silhouette, Davies-Bouldin, Calinski-Harabasz
  ● K=4~9 전체에 대해 중심선·레이블·평가지표 일괄 저장
  ● 층화 추출 (업종 비율 유지) for DTW/K-Shape
  ● KMeans-Euclidean 은 전체 데이터에 적용
"""
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from src import config as cfg

try:
    from tslearn.clustering import TimeSeriesKMeans, KShape
    from tslearn.preprocessing import TimeSeriesScalerMeanVariance
    HAS_TSLEARN = True
except ImportError:
    HAS_TSLEARN = False
    print("[Step03] tslearn 미설치 → DTW/K-Shape 비활성, KMeans-Euclidean만 사용")


# ─────────────────────────────────────────────────────────
def build_trajectory_matrix(ts: pd.DataFrame, value_col="sales_card_mm"):
    """(n_stores, MAX_WEEKS) 궤적 행렬 + 업종 매핑 생성."""
    sub = ts[ts["weeks_since_open"] < cfg.MAX_WEEKS].copy()
    pivot = (
        sub.drop_duplicates(["public_id", "weeks_since_open"])
           .pivot_table(index="public_id", columns="weeks_since_open",
                        values=value_col, aggfunc="mean")
    )
    pivot = pivot.dropna(axis=1, thresh=int(len(pivot) * 0.6))
    pivot = pivot.dropna(axis=0, thresh=int(pivot.shape[1] * 0.85))
    X = pivot.fillna(pivot.median(axis=0)).values
    store_ids = pivot.index.tolist()

    # 업종 정보 (층화추출용)
    cat_map = {}
    if "category" in ts.columns:
        cat_map = ts.groupby("public_id")["category"].first().to_dict()
    categories = [cat_map.get(sid, "기타") for sid in store_ids]

    print(f"[Step03] 궤적 행렬: {X.shape[0]:,} 매장 × {X.shape[1]} 주")
    return X, store_ids, categories


# ─────────────────────────────────────────────────────────
def _stratified_sample(X, store_ids, categories, max_n=None):
    """업종(category) 비율을 유지하는 층화 추출."""
    max_n = max_n or cfg.CLUSTER_MAX_STORES
    n = len(X)
    if n <= max_n:
        return X, store_ids, np.arange(n)

    rng = np.random.RandomState(cfg.SEED)
    cats = np.array(categories)
    unique_cats = np.unique(cats)

    selected = []
    for cat in unique_cats:
        cat_idx = np.where(cats == cat)[0]
        cat_n = max(1, int(len(cat_idx) / n * max_n))
        if cat_n >= len(cat_idx):
            selected.extend(cat_idx.tolist())
        else:
            selected.extend(rng.choice(cat_idx, cat_n, replace=False).tolist())

    selected = np.array(sorted(set(selected)))
    if len(selected) > max_n:
        selected = rng.choice(selected, max_n, replace=False)
        selected.sort()

    print(f"  층화추출: {n:,} → {len(selected):,} 매장 (업종 비율 유지)")
    return X[selected], [store_ids[i] for i in selected], selected


# ─────────────────────────────────────────────────────────
def kmeans_euclidean(X, n_clusters=None):
    k = n_clusters or cfg.CLUSTER_K_DEFAULT
    km = KMeans(n_clusters=k, random_state=cfg.SEED, n_init=15, max_iter=500)
    labels = km.fit_predict(X)
    return labels, km


def dtw_clustering(X, n_clusters=None, metric="dtw"):
    if not HAS_TSLEARN:
        print("  tslearn 없음 → Euclidean KMeans fallback")
        return kmeans_euclidean(X, n_clusters)
    k = n_clusters or cfg.CLUSTER_K_DEFAULT
    X3 = X.reshape(X.shape[0], X.shape[1], 1) if X.ndim == 2 else X
    model = TimeSeriesKMeans(
        n_clusters=k, metric=metric,
        max_iter=30, n_init=cfg.DTW_N_INIT,
        random_state=cfg.SEED, verbose=0,
    )
    labels = model.fit_predict(X3)
    return labels, model


def kshape_clustering(X, n_clusters=None):
    if not HAS_TSLEARN:
        return kmeans_euclidean(X, n_clusters)
    k = n_clusters or cfg.CLUSTER_K_DEFAULT
    X3 = X.reshape(X.shape[0], X.shape[1], 1) if X.ndim == 2 else X
    scaler = TimeSeriesScalerMeanVariance()
    X3 = scaler.fit_transform(X3)
    model = KShape(n_clusters=k, max_iter=50, random_state=cfg.SEED, verbose=0)
    labels = model.fit_predict(X3)
    return labels, model


# ─────────────────────────────────────────────────────────
def evaluate_clustering(X, labels) -> dict:
    n_labels = len(set(labels))
    if n_labels < 2 or n_labels >= len(X):
        return {"silhouette": np.nan, "davies_bouldin": np.nan, "calinski_harabasz": np.nan}
    return {
        "silhouette":        silhouette_score(X, labels, metric="euclidean",
                                              sample_size=min(5000, len(X)),
                                              random_state=cfg.SEED),
        "davies_bouldin":    davies_bouldin_score(X, labels),
        "calinski_harabasz": calinski_harabasz_score(X, labels),
    }


# ─────────────────────────────────────────────────────────
def _print_cluster_stats(labels, centers, prefix=""):
    for c in range(len(centers)):
        ctr = np.asarray(centers[c]).flatten()
        if len(ctr) < 2:
            continue
        s, *_ = stats.linregress(np.arange(len(ctr), dtype=float), ctr)
        n = (np.asarray(labels) == c).sum()
        print(f"  {prefix}C{c}: n={n:,} ({n/len(labels)*100:.1f}%)  "
              f"slope={s:+.5f}  start={ctr[:8].mean():.3f}  end={ctr[-8:].mean():.3f}")


# ─────────────────────────────────────────────────────────
def run_all_k_euclidean(X_full, store_ids_full):
    """K=4~9 각각에 대해 Euclidean KMeans → 레이블·중심선·평가 저장."""
    k_range = cfg.CLUSTER_K_RANGE
    eval_rows = []
    all_models = {}

    print("\n[Step03] K별 Euclidean KMeans (전체 데이터):")
    for k in k_range:
        labels_k, km_k = kmeans_euclidean(X_full, n_clusters=k)
        m_k = evaluate_clustering(X_full, labels_k)
        m_k["K"] = k
        eval_rows.append(m_k)
        all_models[k] = km_k

        print(f"\n  ── K={k}  Sil={m_k['silhouette']:.4f}  DB={m_k['davies_bouldin']:.3f}  CH={m_k['calinski_harabasz']:.0f}")
        _print_cluster_stats(labels_k, km_k.cluster_centers_)

        # 레이블 저장
        pd.DataFrame({
            "public_id": store_ids_full,
            "traj_cluster": labels_k,
        }).to_csv(cfg.TABLE_DIR / f"cluster_labels_K{k}.csv", index=False)

        # 중심선 저장
        pd.DataFrame(km_k.cluster_centers_).to_csv(
            cfg.TABLE_DIR / f"cluster_centers_K{k}.csv", index=False)

    eval_df = pd.DataFrame(eval_rows)
    eval_df.to_csv(cfg.TABLE_DIR / "cluster_evaluation.csv", index=False)

    best_k = int(eval_df.loc[eval_df["silhouette"].idxmax(), "K"])
    print(f"\n[Step03] 최적 K={best_k} (Silhouette 기준)")
    return eval_df, best_k, all_models


# ─────────────────────────────────────────────────────────
def run_clustering(ts):
    """전체 클러스터링 파이프라인."""
    X_full, store_ids_full, categories = build_trajectory_matrix(ts)

    # 1) K=4~9 Euclidean KMeans (전체 데이터)
    eval_df, best_k, all_km_models = run_all_k_euclidean(X_full, store_ids_full)

    km_model = all_km_models[best_k]
    labels_km = km_model.predict(X_full)

    # 2) DTW 클러스터링 (층화추출 샘플, best_k)
    X_sub, store_ids_sub, idx_sub = _stratified_sample(
        X_full, store_ids_full, categories)

    print(f"\n[Step03] DTW 클러스터링 (K={best_k}, 층화추출 {len(X_sub):,}개)...")
    labels_dtw, dtw_model = dtw_clustering(X_sub, n_clusters=best_k)
    m_dtw = evaluate_clustering(X_sub, labels_dtw)
    print(f"  Sil={m_dtw['silhouette']:.4f}  DB={m_dtw['davies_bouldin']:.3f}")

    # 3) K-Shape (층화추출 샘플, best_k)
    print(f"\n[Step03] K-Shape (K={best_k}, 층화추출 {len(X_sub):,}개)...")
    labels_ks, ks_model = kshape_clustering(X_sub, n_clusters=best_k)
    m_ks = evaluate_clustering(X_sub, labels_ks)
    print(f"  Sil={m_ks['silhouette']:.4f}  DB={m_ks['davies_bouldin']:.3f}")

    # 비교 테이블
    m_km_best = evaluate_clustering(X_full, labels_km)
    compare = pd.DataFrame([
        {"method": "KMeans-Euclidean (전체)", **m_km_best},
        {"method": "DTW-KMeans (층화추출)",    **m_dtw},
        {"method": "K-Shape (층화추출)",       **m_ks},
    ])
    compare.to_csv(cfg.TABLE_DIR / "cluster_method_comparison.csv", index=False)
    print(f"\n[Step03] 클러스터링 비교 (K={best_k}):")
    print(compare.to_string(index=False))

    # best_k 기준 레이블 (메인)
    cluster_df = pd.DataFrame({
        "public_id": store_ids_full,
        "traj_cluster": labels_km,
    })
    cluster_df.to_csv(cfg.TABLE_DIR / "cluster_labels.csv", index=False)

    return cluster_df, km_model, eval_df, compare, all_km_models
