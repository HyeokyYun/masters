"""
Step 03-GPU ─ GPU 가속 시계열 클러스터링
═══════════════════════════════════════════════════════════
NVIDIA GPU (CUDA) 를 활용한 DTW 클러스터링.
CPU 버전(step03_clustering.py) 과 동일한 인터페이스.

방법 1: cuML KMeans (RAPIDS) — GPU Euclidean, 전체 데이터 고속
방법 2: Soft-DTW + PyTorch — GPU DTW 거리 계산
방법 3: tslearn + joblib 병렬 — CPU 멀티코어 최적화 (GPU 없어도 가능)

요구사항:
  방법 1: pip install cuml-cu12   (RAPIDS, CUDA 12.x)
  방법 2: pip install torch sdtw-gpu   또는 아래 순수 PyTorch 구현 사용
  방법 3: pip install tslearn joblib (CPU fallback)

실행:
  python -c "from src.step03_clustering_gpu import run_gpu_clustering; ..."
  또는
  python src/step03_clustering_gpu.py   (standalone)
═══════════════════════════════════════════════════════════
"""
import warnings
warnings.filterwarnings("ignore")

import time
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path

import sys
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src import config as cfg
from src.step03_clustering import (
    build_trajectory_matrix,
    evaluate_clustering,
    _print_cluster_stats,
    _stratified_sample,
)

# ── GPU 라이브러리 감지 ───────────────────────────────────
HAS_CUML = False
HAS_TORCH = False

try:
    import cuml
    from cuml.cluster import KMeans as cuKMeans
    HAS_CUML = True
except ImportError:
    pass

try:
    import torch
    HAS_TORCH = torch.cuda.is_available()
    if HAS_TORCH:
        print(f"[GPU] PyTorch CUDA: {torch.cuda.get_device_name(0)}")
except ImportError:
    pass


# ═════════════════════════════════════════════════════════
# 방법 1: cuML KMeans (GPU Euclidean)
# ═════════════════════════════════════════════════════════
def cuml_kmeans(X, n_clusters=6):
    """RAPIDS cuML KMeans — GPU에서 Euclidean 클러스터링."""
    if not HAS_CUML:
        raise ImportError("cuML 미설치. pip install cuml-cu12")

    import cudf
    X_gpu = cudf.DataFrame(X)
    km = cuKMeans(n_clusters=n_clusters, random_state=cfg.SEED,
                  max_iter=500, n_init=15)
    km.fit(X_gpu)
    labels = km.labels_.values_host.astype(int)
    centers = km.cluster_centers_.values_host

    class CuMLModelWrapper:
        def __init__(self, centers, n_clusters):
            self.cluster_centers_ = centers
            self.n_clusters = n_clusters
    return labels, CuMLModelWrapper(centers, n_clusters)


# ═════════════════════════════════════════════════════════
# 방법 2: Soft-DTW with PyTorch (GPU)
# ═════════════════════════════════════════════════════════
def _soft_dtw_distance_matrix_gpu(X_tensor, gamma=1.0):
    """GPU에서 Soft-DTW 거리 행렬 계산 (O(n² × T²), batch 처리)."""
    n, T = X_tensor.shape
    D = torch.zeros(n, n, device=X_tensor.device)

    for i in range(n):
        # 한 시계열 vs 나머지 전체를 batch로
        xi = X_tensor[i].unsqueeze(0).expand(n, -1)  # (n, T)
        xj = X_tensor                                 # (n, T)
        D[i] = _soft_dtw_batch(xi, xj, gamma)

    return D


def _soft_dtw_batch(x, y, gamma=1.0):
    """x: (batch, T), y: (batch, T) → (batch,) Soft-DTW distances."""
    batch, T = x.shape
    cost = (x.unsqueeze(2) - y.unsqueeze(1)) ** 2  # (batch, T, T)

    R = torch.full((batch, T + 1, T + 1), float("inf"), device=x.device)
    R[:, 0, 0] = 0.0

    for i in range(1, T + 1):
        for j in range(1, T + 1):
            r0 = R[:, i - 1, j - 1]
            r1 = R[:, i - 1, j]
            r2 = R[:, i, j - 1]
            rmin = torch.stack([r0, r1, r2], dim=1)
            R[:, i, j] = cost[:, i - 1, j - 1] + (-gamma * torch.logsumexp(-rmin / gamma, dim=1))

    return R[:, T, T]


def softdtw_kmeans_gpu(X, n_clusters=6, max_iter=20, gamma=1.0, device=None):
    """Soft-DTW KMeans on GPU using PyTorch."""
    if not HAS_TORCH:
        raise ImportError("PyTorch CUDA 필요. pip install torch")

    device = device or torch.device("cuda:0")
    n, T = X.shape

    X_t = torch.tensor(X, dtype=torch.float32, device=device)

    # 초기 중심: kmeans++ 대신 random
    rng = np.random.RandomState(cfg.SEED)
    center_idx = rng.choice(n, n_clusters, replace=False)
    centers = X_t[center_idx].clone()

    labels = torch.zeros(n, dtype=torch.long, device=device)

    for it in range(max_iter):
        # Assignment: 각 시계열과 각 중심 간 soft-DTW 거리
        dists = torch.zeros(n, n_clusters, device=device)
        for c in range(n_clusters):
            center_exp = centers[c].unsqueeze(0).expand(n, -1)
            dists[:, c] = _soft_dtw_batch(X_t, center_exp, gamma)

        new_labels = dists.argmin(dim=1)

        # 수렴 체크
        changed = (new_labels != labels).sum().item()
        labels = new_labels
        print(f"    iter {it+1}/{max_iter}  changed={changed}")
        if changed == 0:
            break

        # Update centers
        for c in range(n_clusters):
            mask = labels == c
            if mask.sum() > 0:
                centers[c] = X_t[mask].mean(dim=0)

    labels_np = labels.cpu().numpy()
    centers_np = centers.cpu().numpy()

    class SoftDTWModelWrapper:
        def __init__(self, centers, n_clusters):
            self.cluster_centers_ = centers
            self.n_clusters = n_clusters
    return labels_np, SoftDTWModelWrapper(centers_np, n_clusters)


# ═════════════════════════════════════════════════════════
# 방법 3: tslearn + joblib 병렬 (CPU 멀티코어)
# ═════════════════════════════════════════════════════════
def tslearn_dtw_parallel(X, n_clusters=6, n_jobs=-1):
    """tslearn DTW-KMeans with parallel (CPU 멀티코어)."""
    try:
        from tslearn.clustering import TimeSeriesKMeans
    except ImportError:
        raise ImportError("tslearn 필요. pip install tslearn")

    X3 = X.reshape(X.shape[0], X.shape[1], 1) if X.ndim == 2 else X
    model = TimeSeriesKMeans(
        n_clusters=n_clusters, metric="dtw",
        max_iter=30, n_init=cfg.DTW_N_INIT,
        random_state=cfg.SEED, verbose=1, n_jobs=n_jobs,
    )
    labels = model.fit_predict(X3)
    return labels, model


# ═════════════════════════════════════════════════════════
# 통합 실행
# ═════════════════════════════════════════════════════════
def run_gpu_clustering(ts, method="auto", k_range=None, device=None):
    """
    GPU 클러스터링 파이프라인.

    method:
      "cuml"     — cuML KMeans (GPU Euclidean, 빠름)
      "softdtw"  — Soft-DTW KMeans on GPU (PyTorch, 느리지만 DTW)
      "parallel" — tslearn DTW + CPU 멀티코어
      "auto"     — cuML → softdtw → parallel 순서로 시도
    """
    k_range = k_range or cfg.CLUSTER_K_RANGE

    X_full, store_ids_full, categories = build_trajectory_matrix(ts)

    # 자동 감지
    if method == "auto":
        if HAS_CUML:
            method = "cuml"
            print("[GPU] cuML KMeans 사용")
        elif HAS_TORCH:
            method = "softdtw"
            print("[GPU] Soft-DTW (PyTorch CUDA) 사용")
        else:
            method = "parallel"
            print("[GPU] GPU 없음 → tslearn DTW 멀티코어 사용")

    # DTW 계열은 샘플링 (softdtw의 O(n²T²) 고려)
    if method == "softdtw":
        X_run, sids_run, idx_run = _stratified_sample(
            X_full, store_ids_full, categories, max_n=min(cfg.CLUSTER_MAX_STORES, 8000))
    elif method == "parallel":
        X_run, sids_run, idx_run = _stratified_sample(
            X_full, store_ids_full, categories)
    else:
        X_run, sids_run, idx_run = X_full, store_ids_full, np.arange(len(X_full))

    eval_rows = []
    all_models = {}

    print(f"\n[GPU] K별 클러스터링 ({method}, {len(X_run):,} 매장):")
    for k in k_range:
        t0 = time.time()
        print(f"\n  ── K={k}", end="")

        if method == "cuml":
            labels_k, model_k = cuml_kmeans(X_run, n_clusters=k)
        elif method == "softdtw":
            labels_k, model_k = softdtw_kmeans_gpu(X_run, n_clusters=k,
                                                     device=device)
        else:
            labels_k, model_k = tslearn_dtw_parallel(X_run, n_clusters=k)

        elapsed = time.time() - t0
        m_k = evaluate_clustering(X_run, labels_k)
        m_k["K"] = k
        m_k["elapsed_sec"] = elapsed
        eval_rows.append(m_k)
        all_models[k] = model_k

        print(f"  ({elapsed:.1f}s)  Sil={m_k['silhouette']:.4f}  "
              f"DB={m_k['davies_bouldin']:.3f}")

        if hasattr(model_k, "cluster_centers_"):
            _print_cluster_stats(labels_k, model_k.cluster_centers_, prefix=f"K{k}-")

        # 저장
        pd.DataFrame({
            "public_id": sids_run,
            "traj_cluster": labels_k,
        }).to_csv(cfg.TABLE_DIR / f"gpu_cluster_labels_K{k}_{method}.csv", index=False)

        if hasattr(model_k, "cluster_centers_"):
            ctrs = np.asarray(model_k.cluster_centers_)
            if ctrs.ndim == 3:
                ctrs = ctrs.reshape(ctrs.shape[0], -1)
            pd.DataFrame(ctrs).to_csv(
                cfg.TABLE_DIR / f"gpu_cluster_centers_K{k}_{method}.csv", index=False)

    eval_df = pd.DataFrame(eval_rows)
    eval_df.to_csv(cfg.TABLE_DIR / f"gpu_cluster_evaluation_{method}.csv", index=False)

    best_k = int(eval_df.loc[eval_df["silhouette"].idxmax(), "K"])
    print(f"\n[GPU] 최적 K={best_k} (Silhouette 기준, {method})")
    print(eval_df.to_string(index=False))

    return eval_df, best_k, all_models


# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GPU 클러스터링")
    parser.add_argument("--method", default="auto",
                        choices=["auto", "cuml", "softdtw", "parallel"])
    parser.add_argument("--gpu", type=int, default=0, help="CUDA device index")
    args = parser.parse_args()

    device = None
    if HAS_TORCH and args.gpu >= 0:
        device = torch.device(f"cuda:{args.gpu}")
        print(f"[GPU] 사용 장치: {torch.cuda.get_device_name(args.gpu)}")

    # 데이터 로드
    from src.step01_preprocessing import preprocess
    ts, meta = preprocess()

    eval_df, best_k, models = run_gpu_clustering(
        ts, method=args.method, device=device)
