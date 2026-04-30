"""
Step 07 ─ 논문용 시각화 (모든 Figure 일괄 생성)
  Fig 1: 레이블별 평균 궤적 + 개별 궤적 (spaghetti)
  Fig 2: 레이블 분포 (bar)
  Fig 3: 전반/후반 기울기 사분면 (scatter)
  Fig 4: K-means 클러스터 중심선
  Fig 5: Optimal-K 선택 (Silhouette × K)
  Fig 6: Ablation Study 결과 (grouped bar)
  Fig 7: STL 분해 예시 (sample store)
  Fig 8: 업종별 레이블 분포 (heatmap)
"""
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from scipy import stats
from src import config as cfg


def _plt():
    return cfg.setup_matplotlib()


# ─────────────────────────────────────────────────────────
def fig_trajectories(feat, ts, out="fig01_trajectories.png"):
    """레이블별 평균 궤적 + spaghetti."""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(14, 7))

    for lbl in cfg.LIFECYCLE_LABELS:
        pids = feat.loc[feat["label"] == lbl, "public_id"].values
        trajs = []
        for pid in pids[:250]:
            g = (ts[ts["public_id"] == pid]
                   .sort_values("weeks_since_open")
                   .drop_duplicates("weeks_since_open"))
            y = g["sales_card_mm"].fillna(0).values.astype(float)
            if len(y) >= 50 and np.isfinite(y).all():
                trajs.append(y[:cfg.MAX_WEEKS])
        if not trajs:
            continue
        L = min(len(t) for t in trajs)
        avg = np.mean([t[:L] for t in trajs], axis=0)
        c = cfg.LABEL_COLORS[lbl]
        for traj in trajs[:30]:
            ax.plot(traj[:L], color=c, alpha=0.04, linewidth=0.7)
        n_total = len(feat[feat["label"] == lbl])
        ax.plot(avg, color=c, linewidth=2.5,
                label=f"{lbl}  {cfg.LABEL_DESC[lbl]}  (n={n_total:,})")

    ax.axhline(0.5, color="gray", ls="--", alpha=0.3)
    ax.set_title("생애주기 레이블별 평균 매출 궤적 (MinMax, 오픈 후 주차)",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("오픈 후 경과 주차")
    ax.set_ylabel("정규화 매출")
    ax.set_ylim(-0.05, 1.1)
    ax.legend(fontsize=7, loc="upper right", ncol=2)
    ax.grid(alpha=0.3)
    plt.savefig(cfg.FIGURE_DIR / out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  → {out}")


# ─────────────────────────────────────────────────────────
def fig_distribution(feat, out="fig02_distribution.png"):
    """레이블 분포 bar chart."""
    plt = _plt()
    n_labels = len(cfg.LIFECYCLE_LABELS)
    fig, ax = plt.subplots(figsize=(max(10, n_labels * 1.1), 5))
    vc = feat["label"].value_counts().reindex(cfg.LIFECYCLE_LABELS, fill_value=0)
    bars = ax.bar(cfg.LIFECYCLE_LABELS, vc.values,
                  color=[cfg.LABEL_COLORS[l] for l in cfg.LIFECYCLE_LABELS],
                  edgecolor="white")
    fs = 8 if n_labels > 8 else 9
    for bar, lbl, v in zip(bars, cfg.LIFECYCLE_LABELS, vc.values):
        pct = v / len(feat) * 100
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + len(feat) * 0.003,
                f"{v:,}\n({pct:.1f}%)", ha="center", fontsize=fs, fontweight="bold")
    ax.tick_params(axis="x", labelrotation=45)
    ax.set_title(f"생애주기 패턴 분포 ({len(cfg.LIFECYCLE_LABELS)}-class)", fontsize=12, fontweight="bold")
    ax.set_ylabel("매장 수")
    ax.grid(alpha=0.3, axis="y")
    plt.savefig(cfg.FIGURE_DIR / out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  → {out}")


# ─────────────────────────────────────────────────────────
def fig_slope_quadrant(feat, out="fig03_slope_quadrant.png"):
    """전반/후반 기울기 사분면 scatter."""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(8, 8))
    for lbl in cfg.LIFECYCLE_LABELS:
        grp = feat[feat["label"] == lbl]
        sample = grp.sample(min(800, len(grp)), random_state=cfg.SEED)
        ax.scatter(sample["slope_early_mm"], sample["slope_late_mm"],
                   label=lbl, alpha=0.35, s=12, color=cfg.LABEL_COLORS[lbl])
    ax.axhline(0, color="gray", ls="--", alpha=0.6)
    ax.axvline(0, color="gray", ls="--", alpha=0.6)
    ax.set_xlabel("전반부 기울기 (MinMax)")
    ax.set_ylabel("후반부 기울기 (MinMax)")
    ax.set_title("전반/후반 기울기 사분면", fontsize=12, fontweight="bold")
    ax.legend(fontsize=7, markerscale=2, ncol=2, loc="best")
    ax.grid(alpha=0.3)
    plt.savefig(cfg.FIGURE_DIR / out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  → {out}")


# ─────────────────────────────────────────────────────────
def fig_cluster_centers(km_model, out="fig04_cluster_centers.png"):
    """KMeans 클러스터 중심선."""
    if km_model is None:
        return
    plt = _plt()
    fig, ax = plt.subplots(figsize=(12, 5))
    nc = km_model.n_clusters
    cmap = plt.cm.get_cmap("tab10", nc)
    for c in range(nc):
        ctr = np.asarray(km_model.cluster_centers_[c]).flatten()
        s, *_ = stats.linregress(np.arange(len(ctr), dtype=float), ctr)
        ax.plot(ctr, color=cmap(c), linewidth=2.2,
                label=f"C{c}  (slope {s:+.4f})")
    ax.axhline(0.5, color="gray", ls="--", alpha=0.3)
    ax.set_title(f"K-Means 궤적 클러스터 중심 (K={nc})", fontsize=12, fontweight="bold")
    ax.set_xlabel("오픈 후 경과 주차")
    ax.set_ylabel("정규화 매출")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    plt.savefig(cfg.FIGURE_DIR / out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  → {out}")


# ─────────────────────────────────────────────────────────
def fig_optimal_k(eval_df, out="fig05_optimal_k.png"):
    """Silhouette × K 그래프."""
    if eval_df is None or eval_df.empty:
        return
    plt = _plt()
    fig, ax1 = plt.subplots(figsize=(8, 4))
    ax1.plot(eval_df["K"], eval_df["silhouette"], "o-", color="#1565C0", label="Silhouette")
    ax1.set_xlabel("K (클러스터 수)")
    ax1.set_ylabel("Silhouette Score", color="#1565C0")

    ax2 = ax1.twinx()
    ax2.plot(eval_df["K"], eval_df["davies_bouldin"], "s--", color="#C62828", label="Davies-Bouldin")
    ax2.set_ylabel("Davies-Bouldin Index", color="#C62828")

    ax1.set_title("클러스터 수(K) 선택", fontsize=12, fontweight="bold")
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=9)
    ax1.grid(alpha=0.3)
    plt.savefig(cfg.FIGURE_DIR / out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  → {out}")


# ─────────────────────────────────────────────────────────
def fig_ablation(abl_df, out="fig06_ablation.png"):
    """Ablation study grouped bar chart."""
    if abl_df is None or abl_df.empty:
        return
    plt = _plt()
    fig, ax = plt.subplots(figsize=(10, 5))
    fsets  = abl_df["Feature Set"].unique()
    models = abl_df["Model"].unique()
    x = np.arange(len(models))
    w = 0.8 / len(fsets)
    palette = ["#90A4AE", "#42A5F5", "#1565C0", "#0D47A1"]

    for i, fs in enumerate(fsets):
        sub = abl_df[abl_df["Feature Set"] == fs]
        bars = ax.bar(x + i * w, sub["F1_mean"].values, w,
                      label=fs, color=palette[i % len(palette)],
                      yerr=sub["F1_std"].values, capsize=4)
        ax.bar_label(bars, fmt="%.3f", fontsize=8, padding=3)

    ax.set_xticks(x + w * (len(fsets) - 1) / 2)
    ax.set_xticklabels(models)
    ax.set_ylim(0, 1.0)
    ax.set_title("Ablation Study: 조기 예측 피처셋별 F1", fontsize=12, fontweight="bold")
    ax.set_ylabel("F1 (weighted)")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3, axis="y")
    plt.savefig(cfg.FIGURE_DIR / out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  → {out}")


# ─────────────────────────────────────────────────────────
def fig_stl_example(ts, out="fig07_stl_example.png"):
    """STL 분해 예시 (3-panel: observed, trend, seasonal)."""
    plt = _plt()
    pids = ts["public_id"].unique()
    rng = np.random.RandomState(cfg.SEED)
    sample_pid = rng.choice(pids)
    g = ts[ts["public_id"] == sample_pid].sort_values("weeks_since_open").head(cfg.MAX_WEEKS)

    fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
    x = g["weeks_since_open"].values

    axes[0].plot(x, g["sales_card"].values, color="#333", linewidth=1.2)
    axes[0].set_ylabel("원시 매출")
    axes[0].set_title(f"STL 분해 예시 (매장 {sample_pid})", fontsize=12, fontweight="bold")

    if "trend" in g.columns:
        axes[1].plot(x, g["trend"].values, color="#1565C0", linewidth=1.5)
    axes[1].set_ylabel("Trend")

    if "seasonal" in g.columns:
        axes[2].plot(x, g["seasonal"].values, color="#C62828", linewidth=1.0)
    axes[2].set_ylabel("Seasonal")
    axes[2].set_xlabel("오픈 후 경과 주차")

    for ax in axes:
        ax.grid(alpha=0.3)
    plt.savefig(cfg.FIGURE_DIR / out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  → {out}")


# ─────────────────────────────────────────────────────────
def fig_category_heatmap(feat, out="fig08_category_heatmap.png"):
    """업종별 레이블 분포 heatmap."""
    if "category" not in feat.columns:
        return
    plt = _plt()
    import seaborn as sns

    ct = pd.crosstab(feat["category"], feat["label"], normalize="index") * 100
    ct = ct.reindex(columns=cfg.LIFECYCLE_LABELS, fill_value=0)
    ct = ct.loc[ct.sum(axis=1).sort_values(ascending=False).index]

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(ct, annot=True, fmt=".1f", cmap="YlOrRd", ax=ax,
                linewidths=0.5, cbar_kws={"label": "%"})
    ax.set_title("업종별 생애주기 레이블 분포 (%)", fontsize=12, fontweight="bold")
    ax.set_ylabel("")
    plt.savefig(cfg.FIGURE_DIR / out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  → {out}")


# ─────────────────────────────────────────────────────────
def fig_all_k_centers(all_km_models=None, out="fig09_all_k_centers.png"):
    """K=4~9 클러스터 중심선 비교 서브플롯."""
    if all_km_models is None:
        # CSV fallback: 저장된 중심선 파일에서 로드
        all_km_models = {}
        for k in cfg.CLUSTER_K_RANGE:
            p = cfg.TABLE_DIR / f"cluster_centers_K{k}.csv"
            if p.exists():
                all_km_models[k] = pd.read_csv(p).values
        if not all_km_models:
            return

    plt = _plt()
    ks = sorted(all_km_models.keys())
    n_plots = len(ks)
    cols = 3
    rows = (n_plots + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 4 * rows), sharex=True, sharey=True)
    if rows == 1:
        axes = axes.reshape(1, -1)

    cmap = plt.cm.get_cmap("tab10", 10)

    for idx, k in enumerate(ks):
        ax = axes[idx // cols, idx % cols]
        # km_model 또는 numpy 배열
        obj = all_km_models[k]
        if hasattr(obj, "cluster_centers_"):
            centers = obj.cluster_centers_
        else:
            centers = obj  # numpy array from CSV

        for c in range(len(centers)):
            ctr = np.asarray(centers[c]).flatten()
            s, *_ = stats.linregress(np.arange(len(ctr), dtype=float), ctr)
            n_weeks = len(ctr)
            ax.plot(ctr, color=cmap(c), linewidth=1.8,
                    label=f"C{c} ({s:+.4f})")
        ax.axhline(0.5, color="gray", ls="--", alpha=0.3)
        ax.set_title(f"K={k}", fontsize=11, fontweight="bold")
        ax.legend(fontsize=6, loc="upper right", ncol=2)
        ax.grid(alpha=0.3)
        if idx // cols == rows - 1:
            ax.set_xlabel("주차")
        if idx % cols == 0:
            ax.set_ylabel("MinMax 매출")

    # 빈 서브플롯 숨기기
    for idx in range(n_plots, rows * cols):
        axes[idx // cols, idx % cols].set_visible(False)

    fig.suptitle("K별 클러스터 중심선 비교 (KMeans-Euclidean)", fontsize=13, fontweight="bold")
    plt.savefig(cfg.FIGURE_DIR / out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  → {out}")


# ─────────────────────────────────────────────────────────
def run_visualization(feat, ts, km_model=None, eval_df=None, abl_df=None,
                      all_km_models=None):
    """모든 Figure 일괄 생성."""
    print("\n" + "=" * 60)
    print("[Step07] 시각화")
    print("=" * 60)

    fig_trajectories(feat, ts)
    fig_distribution(feat)
    fig_slope_quadrant(feat)
    fig_cluster_centers(km_model)
    fig_optimal_k(eval_df)
    fig_ablation(abl_df)
    fig_stl_example(ts)
    fig_category_heatmap(feat)
    fig_all_k_centers(all_km_models)

    print(f"\n[Step07] 완료: {cfg.FIGURE_DIR}")
