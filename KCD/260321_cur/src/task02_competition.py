"""
Task 02 ─ 경쟁 밀도 지수 (Competition Density Index)
═══════════════════════════════════════════════════════════
미팅 피드백:
  - 동(dong)별 전체 업장 수 대비 동일 업종 업장 수 비율
  - competition_index = same_category_count / total_count (per dong)
  - 업종 더미 × competition_index 인터랙션 텀 추가
  - "crowdedness" 또는 "competition density" 로 정의

출력:
  - competition_index_by_store.csv      (매장별 경쟁 지수)
  - competition_dong_summary.csv        (동별 요약)
  - mnlogit_competition                 (MNLogit 결과)
  - fig_competition_distribution.png    (경쟁 지수 분포)
"""
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from src import config as cfg
from src.data_loader import load_labeled_features, load_meta, run_mnlogit


def build_competition_index(meta: pd.DataFrame) -> pd.DataFrame:
    """동(dong)별 경쟁 밀도 지수 계산.
    competition_index = (동 내 동일 업종 수) / (동 내 전체 업장 수)
    """
    df = meta[["public_id"]].copy()

    # 업종 분류
    cat_col = "classification__kcd_v3__depth_2_name"
    if cat_col in meta.columns:
        df["category"] = meta[cat_col].apply(cfg.classify_industry)
    else:
        df["category"] = "기타"

    # 동 정보
    if "dong" in meta.columns:
        df["dong"] = meta["dong"].fillna("unknown")
    elif "sigungu" in meta.columns:
        df["dong"] = meta["sigungu"].fillna("unknown")
    else:
        print("[Task02] 동(dong) 정보 없음 → 경쟁 지수 계산 불가")
        return None

    # 동별 전체 업장 수
    dong_total = df.groupby("dong")["public_id"].transform("count")
    df["dong_total_stores"] = dong_total

    # 동별 동일 업종 업장 수
    dong_cat_count = df.groupby(["dong", "category"])["public_id"].transform("count")
    df["dong_same_cat_stores"] = dong_cat_count

    # 경쟁 밀도 지수
    df["competition_index"] = df["dong_same_cat_stores"] / (df["dong_total_stores"] + 1e-9)

    # 동일 업종 밀도 (log1p for skewness)
    df["competition_log"] = np.log1p(df["competition_index"])

    # HHI (Herfindahl-Hirschman Index) per dong
    hhi = (df.groupby("dong")
           .apply(lambda x: ((x.groupby("category")["public_id"].count()
                               / len(x)) ** 2).sum(),
                  include_groups=False)
           .reset_index()
           .rename(columns={0: "dong_hhi"}))
    df = df.merge(hhi, on="dong", how="left")

    print(f"[Task02] 경쟁 지수 계산: {len(df):,} 매장, "
          f"{df['dong'].nunique():,} 동")
    print(f"  competition_index: mean={df['competition_index'].mean():.4f}, "
          f"median={df['competition_index'].median():.4f}")

    return df


def dong_summary(comp_df: pd.DataFrame) -> pd.DataFrame:
    """동별 요약 통계."""
    summary = (comp_df.groupby("dong")
               .agg(
                   total_stores=("public_id", "count"),
                   n_categories=("category", "nunique"),
                   mean_competition=("competition_index", "mean"),
                   hhi=("dong_hhi", "first"),
               )
               .sort_values("total_stores", ascending=False)
               .reset_index())

    summary.to_csv(cfg.TABLE_DIR / "competition_dong_summary.csv",
                   index=False, encoding="utf-8-sig")
    print(f"\n[Task02] 동별 요약: 상위 10개 동")
    print(summary.head(10).to_string(index=False))
    return summary


def merge_competition_with_features(feat: pd.DataFrame,
                                     comp_df: pd.DataFrame) -> pd.DataFrame:
    """피처 데이터에 경쟁 지수 병합."""
    keep = ["public_id", "dong", "competition_index", "competition_log",
            "dong_total_stores", "dong_same_cat_stores", "dong_hhi"]
    avail = [c for c in keep if c in comp_df.columns]

    merged = feat.merge(comp_df[avail], on="public_id", how="left")
    merged["competition_index"] = merged["competition_index"].fillna(
        merged["competition_index"].median()
    )
    merged["competition_log"] = merged["competition_log"].fillna(
        merged["competition_log"].median()
    )

    print(f"[Task02] 병합 완료: {len(merged):,} 매장 (경쟁 지수 포함)")
    return merged


def build_interaction_terms(df: pd.DataFrame) -> pd.DataFrame:
    """업종 더미 × competition_index 인터랙션 텀 생성."""
    df = df.copy()
    if "category" not in df.columns:
        return df

    for cat in df["category"].unique():
        if cat == "기타":
            continue
        col_name = f"comp_x_{cat}"
        df[col_name] = (df["category"] == cat).astype(float) * df["competition_index"]

    interaction_cols = [c for c in df.columns if c.startswith("comp_x_")]
    print(f"[Task02] 인터랙션 텀 {len(interaction_cols)}개 생성: {interaction_cols}")
    return df


def run_mnlogit_competition(merged: pd.DataFrame):
    """경쟁 지수 포함 MNLogit."""
    base_features = [
        "slope_early_mm", "cv", "mdd", "nc_rate", "del_ratio_log",
        "before_noon", "weekend", "trend_slope", "seasonal_strength",
        "noise_ratio", "n_weeks",
    ]

    # (A) 기본 + competition_index 만
    features_a = base_features + ["competition_index"]

    # (B) 기본 + competition_index + 인터랙션
    interaction_cols = [c for c in merged.columns if c.startswith("comp_x_")]
    features_b = base_features + ["competition_index"] + interaction_cols

    # 카테고리 더미 추가
    if "category" in merged.columns:
        cat_dummies = pd.get_dummies(merged["category"], prefix="cat",
                                      drop_first=True, dtype=float)
        for c in cat_dummies.columns:
            merged[c] = cat_dummies[c].values
        cat_cols = list(cat_dummies.columns)
        features_a = features_a + cat_cols
        features_b = features_b + cat_cols

    avail_a = [c for c in features_a if c in merged.columns]
    avail_b = [c for c in features_b if c in merged.columns]

    print(f"\n[Task02] Model A: 기본 + competition_index ({len(avail_a)}개 변수)")
    result_a, _ = run_mnlogit(merged, avail_a,
                              save_prefix="mnlogit_competition_base")

    print(f"\n[Task02] Model B: 기본 + competition + interaction ({len(avail_b)}개 변수)")
    result_b, _ = run_mnlogit(merged, avail_b,
                              save_prefix="mnlogit_competition_interaction")

    return result_a, result_b


def plot_competition(merged: pd.DataFrame):
    """경쟁 지수 분포 시각화."""
    plt = cfg.setup_matplotlib()
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    # 1) 전체 분포
    ax = axes[0]
    ax.hist(merged["competition_index"].dropna(), bins=50, color="steelblue",
            edgecolor="white", alpha=0.8)
    ax.set_xlabel("Competition Index (동일업종/전체)")
    ax.set_ylabel("매장 수")
    ax.set_title("경쟁 밀도 지수 분포")
    ax.axvline(merged["competition_index"].median(), color="red",
               linestyle="--", label=f"중앙값={merged['competition_index'].median():.3f}")
    ax.legend()

    # 2) 업종별 경쟁 지수
    ax = axes[1]
    if "category" in merged.columns:
        cat_means = (merged.groupby("category")["competition_index"]
                     .mean().sort_values(ascending=False))
        ax.barh(cat_means.index, cat_means.values, color="steelblue")
        ax.set_xlabel("평균 Competition Index")
        ax.set_title("업종별 평균 경쟁 밀도")

    # 3) 레이블별 경쟁 지수
    ax = axes[2]
    labels_in_data = [l for l in cfg.LIFECYCLE_LABELS if l in merged["label"].values]
    label_means = merged.groupby("label")["competition_index"].mean().reindex(labels_in_data)
    ax.barh(label_means.index, label_means.values, color="coral")
    ax.set_xlabel("평균 Competition Index")
    ax.set_title("생애주기 레이블별 평균 경쟁 밀도")

    plt.tight_layout()
    plt.savefig(cfg.FIGURE_DIR / "fig_competition_distribution.png",
                dpi=150, bbox_inches="tight")
    plt.close("all")
    print("  → figures/fig_competition_distribution.png")


# ── 엔트리 ────────────────────────────────────────────────

def run_task02():
    """Task 02 전체 실행."""
    print("\n" + "=" * 62)
    print("  Task 02: 경쟁 밀도 지수 (Competition Density)")
    print("=" * 62)

    feat = load_labeled_features()
    meta = load_meta()

    comp_df = build_competition_index(meta)
    if comp_df is None:
        print("[Task02] 중단 — 위치 정보 부족")
        return

    comp_df.to_csv(cfg.TABLE_DIR / "competition_index_by_store.csv",
                   index=False, encoding="utf-8-sig")

    dong_summary(comp_df)

    merged = merge_competition_with_features(feat, comp_df)
    merged = build_interaction_terms(merged)
    run_mnlogit_competition(merged)
    plot_competition(merged)

    print("\n[Task02] 완료")
