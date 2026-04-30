"""
GAF PoC: 데이터 로드 → GAF 변환 → 샘플 시각화 → (선택) CNN 클러스터링

- 142주 매출 시계열을 Gramian Angular Field (GAF) 이미지로 변환
- 특징적인 샘플 10개 GAF 이미지 저장
- 선택: CNN Autoencoder + K-Means로 이미지 기반 클러스터링

Run from 260211: python scripts/run_gaf_poc.py
"""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "configs" / "gaf_poc.yaml"
LOG_PATH = ROOT / "outputs" / "logs" / "run_gaf_poc.log"
FIG_DIR = ROOT / "outputs" / "figures"
TBL_DIR = ROOT / "outputs" / "tables"

# yaml 미설치 시 사용할 기본 설정
DEFAULT_CONFIG = {
    "data": {
        "weekly_parquet_primary": "../original_data/weekly_processed.parquet",
        "weekly_parquet_fallback": "../original_data/weekly.parquet",
        "id_col_store": "public_id",
        "time_col_week": "day_after1",
        "y_col_sales": "sales_card",
    },
    "gaf": {"n_weeks": 142, "min_weeks": 100, "image_size_cnn": 64, "method": "summation", "sample_range": [-1, 1]},
    "poc": {"n_sample_images": 10, "max_stores": 5000, "run_cnn_clustering": False, "n_clusters": 6, "seed": 42},
    "outputs": {"tables": "outputs/tables", "figures": "outputs/figures", "logs": "outputs/logs"},
}


def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TBL_DIR.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_config() -> dict:
    try:
        import yaml
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return DEFAULT_CONFIG


def get_weekly_path(cfg: dict) -> Path:
    primary = ROOT / cfg["data"]["weekly_parquet_primary"]
    if primary.exists():
        return primary
    return ROOT / cfg["data"]["weekly_parquet_fallback"]


def load_and_pivot_weekly(cfg: dict) -> tuple[pd.DataFrame, np.ndarray, list]:
    """주간 데이터 로드 후 (store_id, week_1..week_N) 피벗, 결측 보간."""
    path = get_weekly_path(cfg)
    if not path.exists():
        raise FileNotFoundError(f"Weekly parquet not found: {path}")
    log(f"Loading weekly data from {path}...")
    df = pd.read_parquet(path, columns=[
        cfg["data"]["id_col_store"],
        cfg["data"]["time_col_week"],
        cfg["data"]["y_col_sales"],
    ])
    id_col = cfg["data"]["id_col_store"]
    week_col = cfg["data"]["time_col_week"]
    sales_col = cfg["data"]["y_col_sales"]
    n_weeks = int(cfg["gaf"]["n_weeks"])
    min_weeks = int(cfg["gaf"]["min_weeks"])

    # 주별 합계 (동일 store-week 여러 행 있을 수 있음)
    agg = df.groupby([id_col, week_col], as_index=False)[sales_col].sum()
    pivot = agg.pivot(index=id_col, columns=week_col, values=sales_col)
    # week 1..n_weeks 컬럼으로 정렬·보완 (없는 주는 NaN → 이후 보간)
    pivot = pivot.reindex(columns=list(range(1, n_weeks + 1)))

    # 결측: 축 방향 보간 후 ffill/bfill
    pivot = pivot.astype("float32")
    pivot = pivot.interpolate(axis=1, limit_direction="both")
    pivot = pivot.ffill(axis=1).bfill(axis=1).fillna(0.0)

    # 최소 주 수 이상 있는 매장만 (실제로는 이미 전체 기간 채우므로 행 수만 필터)
    store_ids = pivot.index.astype(str).tolist()
    X = pivot.to_numpy(dtype=np.float32)
    # NaN/Inf 제거
    np.nan_to_num(X, copy=False, nan=0.0, posinf=0.0, neginf=0.0)
    log(f"Pivot shape: {X.shape[0]} stores x {X.shape[1]} weeks")
    return pivot, X, store_ids


def normalize_for_gaf(X: np.ndarray, sample_range: tuple[float, float]) -> np.ndarray:
    """행별로 [min,max]를 sample_range로 선형 스케일. (pyts는 [-1,1] 권장.)"""
    out = np.empty_like(X, dtype=np.float64)
    low, high = sample_range[0], sample_range[1]
    for i in range(X.shape[0]):
        row = X[i].astype(np.float64)
        rmin, rmax = row.min(), row.max()
        if rmax <= rmin:
            out[i] = low
        else:
            out[i] = low + (row - rmin) / (rmax - rmin) * (high - low)
    return out.astype(np.float32)


def fit_gaf(X: np.ndarray, cfg: dict):
    """시계열 → GAF 이미지 (numpy 벡터화, pyts 불필요)."""
    method = cfg["gaf"].get("method", "summation")
    sample_range = tuple(cfg["gaf"].get("sample_range", [-1, 1]))
    X_scaled = normalize_for_gaf(X, sample_range)
    X_scaled = np.clip(X_scaled.astype(np.float64), -1.0, 1.0)
    phi = np.arccos(X_scaled)  # (n_samples, n_weeks)
    cos_phi = np.cos(phi)
    sin_phi = np.sin(phi)
    log("Computing GAF transform (vectorized)...")
    if method == "summation":  # GASF: cos(φ_i + φ_j)
        # (n, T, 1) * (n, 1, T) - (n, T, 1) * (n, 1, T)
        X_gaf = cos_phi[:, :, np.newaxis] * cos_phi[:, np.newaxis, :] - sin_phi[:, :, np.newaxis] * sin_phi[:, np.newaxis, :]
    else:  # GADF: sin(φ_i - φ_j)
        X_gaf = sin_phi[:, :, np.newaxis] * cos_phi[:, np.newaxis, :] - cos_phi[:, :, np.newaxis] * sin_phi[:, np.newaxis, :]
    X_gaf = X_gaf.astype(np.float32)
    log(f"GAF shape: {X_gaf.shape}")
    return X_gaf, X_scaled.astype(np.float32)


def select_diverse_sample_indices(
    X: np.ndarray, n: int, store_ids: list, seed: int
) -> np.ndarray:
    """다양한 패턴을 보이도록 인덱스 선택: 평균/분산 분위수 + 랜덤."""
    mean_ts = np.mean(X, axis=1)
    std_ts = np.std(X, axis=1)
    cv = std_ts / (mean_ts + 1e-8)
    rng = np.random.default_rng(seed)
    chosen = set()
    # 극단 패턴 각 1~2개
    for idx in np.argsort(mean_ts)[:2].tolist():
        chosen.add(int(idx))
    for idx in np.argsort(mean_ts)[-2:].tolist():
        chosen.add(int(idx))
    for idx in np.argsort(cv)[-2:].tolist():
        chosen.add(int(idx))
    # 나머지는 랜덤
    pool = [i for i in range(X.shape[0]) if i not in chosen]
    need = n - len(chosen)
    if need > 0 and pool:
        add = rng.choice(pool, size=min(need, len(pool)), replace=False)
        chosen.update(add.tolist())
    out = np.array(sorted(chosen)[:n])
    return out


def save_sample_gaf_images(
    X_gaf: np.ndarray,
    store_ids: list,
    indices: np.ndarray,
    cfg: dict,
) -> None:
    """선택된 샘플의 GAF 이미지를 저장."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    n_weeks = X_gaf.shape[1]
    for k, idx in enumerate(indices):
        fig, ax = plt.subplots(1, 1, figsize=(5, 4))
        im = ax.imshow(X_gaf[idx], cmap="viridis", aspect="equal")
        ax.set_title(f"Store {store_ids[idx]} (GAF {n_weeks}x{n_weeks})")
        plt.colorbar(im, ax=ax)
        plt.tight_layout()
        out_path = FIG_DIR / f"gaf_sample_{k+1}_{store_ids[idx]}.png"
        plt.savefig(out_path, dpi=120)
        plt.close()
        log(f"Saved {out_path.name}")
    # 10개 한 번에 보기 (2x5 그리드)
    fig, axes = plt.subplots(2, 5, figsize=(14, 6))
    for k, idx in enumerate(indices):
        ax = axes[k // 5, k % 5]
        ax.imshow(X_gaf[idx], cmap="viridis", aspect="equal")
        ax.set_title(str(store_ids[idx])[:12], fontsize=8)
        ax.axis("off")
    plt.suptitle("GAF sample (10 stores)")
    plt.tight_layout()
    grid_path = FIG_DIR / "gaf_sample_10_grid.png"
    plt.savefig(grid_path, dpi=120)
    plt.close()
    log(f"Saved grid {grid_path.name}")


def cnn_clustering(
    X_gaf: np.ndarray,
    n_clusters: int,
    image_size: int,
    seed: int,
    device: str = "cpu",
) -> tuple[np.ndarray, object]:
    """간단한 CNN Autoencoder로 latent 추출 후 K-Means 클러스터링."""
    import torch
    import torch.nn as nn
    from torch.utils.data import TensorDataset, DataLoader
    from sklearn.cluster import KMeans

    # 리사이즈: (N, H, W) → (N, 1, image_size, image_size)
    from scipy.ndimage import zoom
    n, h, w = X_gaf.shape
    if (h, w) != (image_size, image_size):
        scale = image_size / h
        X_resized = np.stack([
            zoom(X_gaf[i], scale, order=1) for i in range(n)
        ]).astype(np.float32)
    else:
        X_resized = X_gaf.astype(np.float32)
    X_tensor = torch.from_numpy(X_resized[:, np.newaxis, :, :])  # (N, 1, size, size)

    class SmallCNNEncoder(nn.Module):
        def __init__(self, latent_dim=32):
            super().__init__()
            self.encoder = nn.Sequential(
                nn.Conv2d(1, 16, 3, padding=1),
                nn.ReLU(),
                nn.MaxPool2d(2),
                nn.Conv2d(16, 32, 3, padding=1),
                nn.ReLU(),
                nn.MaxPool2d(2),
                nn.Conv2d(32, 64, 3, padding=1),
                nn.ReLU(),
                nn.AdaptiveAvgPool2d(1),
                nn.Flatten(),
                nn.Linear(64, latent_dim),
            )
            self.latent_dim = latent_dim

        def forward(self, x):
            return self.encoder(x)

    class Autoencoder(nn.Module):
        def __init__(self, latent_dim=32, size=image_size):
            super().__init__()
            self.encoder = SmallCNNEncoder(latent_dim)
            self.decoder = nn.Sequential(
                nn.Linear(latent_dim, 64 * (size // 4) ** 2),
                nn.Unflatten(1, (64, size // 4, size // 4)),
                nn.ConvTranspose2d(64, 32, 2, stride=2),
                nn.ReLU(),
                nn.ConvTranspose2d(32, 16, 2, stride=2),
                nn.ReLU(),
                nn.Conv2d(16, 1, 3, padding=1),
            )

        def forward(self, x):
            z = self.encoder(x)
            return self.decoder(z), z

    latent_dim = 32
    model = Autoencoder(latent_dim=latent_dim, size=image_size).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    mse = nn.MSELoss()
    batch_size = 64
    ds = TensorDataset(X_tensor)
    dl = DataLoader(ds, batch_size=batch_size, shuffle=True)
    model.train()
    for epoch in range(15):
        for (batch,) in dl:
            batch = batch.to(device)
            recon, z = model(batch)
            loss = mse(recon, batch)
            opt.zero_grad()
            loss.backward()
            opt.step()

    model.eval()
    latents = []
    with torch.no_grad():
        for (batch,) in dl:
            _, z = model(batch.to(device))
            latents.append(z.cpu().numpy())
    Z = np.vstack(latents)
    log(f"Latent shape: {Z.shape}")

    km = KMeans(n_clusters=n_clusters, random_state=seed, n_init=10)
    labels = km.fit_predict(Z)
    log(f"CNN clustering done: {n_clusters} clusters")
    return labels, model


def main() -> None:
    log("===== GAF PoC start =====")
    cfg = load_config()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TBL_DIR.mkdir(parents=True, exist_ok=True)

    pivot, X, store_ids = load_and_pivot_weekly(cfg)
    max_stores = cfg["poc"].get("max_stores")
    if max_stores is not None:
        max_stores = int(max_stores)
        if len(store_ids) > max_stores:
            rng = np.random.default_rng(cfg["poc"].get("seed", 42))
            idx = rng.choice(len(store_ids), max_stores, replace=False)
            X = X[idx]
            store_ids = [store_ids[i] for i in idx]
            log(f"Subsampled to {max_stores} stores")
    if X.shape[0] == 0:
        log("ERROR: No data after filter.")
        sys.exit(1)

    X_gaf, X_scaled = fit_gaf(X, cfg)
    n_sample = min(cfg["poc"].get("n_sample_images", 10), X_gaf.shape[0])
    sample_idx = select_diverse_sample_indices(
        X_scaled, n_sample, store_ids, cfg["poc"].get("seed", 42)
    )
    save_sample_gaf_images(X_gaf, store_ids, sample_idx, cfg)

    if cfg["poc"].get("run_cnn_clustering", False):
        try:
            import torch  # noqa: F401
        except ImportError:
            log("torch not installed: skipping CNN clustering. (GAF images are saved.)")
        else:
            try:
                image_size = int(cfg["gaf"].get("image_size_cnn", 64))
                labels, _ = cnn_clustering(
                    X_gaf,
                    n_clusters=int(cfg["poc"].get("n_clusters", 6)),
                    image_size=image_size,
                    seed=cfg["poc"].get("seed", 42),
                )
                out_df = pd.DataFrame({
                    cfg["data"]["id_col_store"]: store_ids,
                    "gaf_cluster": labels,
                })
                out_path = TBL_DIR / "gaf_cnn_cluster_labels.parquet"
                out_df.to_parquet(out_path, index=False)
                log(f"Saved cluster labels to {out_path}")
            except Exception as e:
                log(f"CNN clustering failed (optional): {e}")
                import traceback
                traceback.print_exc()

    log("===== GAF PoC done =====")


if __name__ == "__main__":
    main()
