"""
Step 04 ─ 생애주기 레이블 할당 (Data-driven, 6-class)
  slope_early × slope_late × mdd → 6 클래스

  DD_Z: 전반↓ 후반↓ 고손실 (쇠퇴)
  DD_Y: 전반↓ 후반↓ 저손실 (저성과 안정)
  DU  : 전반↓ 후반↑        (반등)
  UU  : 전반↑ 후반↑        (지속 성장)
  UD_Z: 전반↑ 후반↓ 고손실 (급락)
  UD_Y: 전반↑ 후반↓ 저손실 (완만 하락)
"""
import pandas as pd
import numpy as np
from src import config as cfg


def assign_labels(feat: pd.DataFrame) -> pd.DataFrame:
    """피처 DataFrame에 label 컬럼 추가."""
    mdd_med = feat["mdd"].median()
    print(f"[Step04] MDD 중앙값(임계): {mdd_med:.4f}")

    def _label(row):
        up_e = row["slope_early_mm"] > 0
        up_l = row["slope_late_mm"]  > 0
        hi   = row["mdd"] >= mdd_med

        if   not up_e and not up_l: return "DD_Z" if hi else "DD_Y"
        elif not up_e and     up_l: return "DU"
        elif     up_e and     up_l: return "UU"
        else:                       return "UD_Z" if hi else "UD_Y"

    feat = feat.copy()
    feat["label"] = feat.apply(_label, axis=1)

    print("\n[Step04] 레이블 분포:")
    vc = feat["label"].value_counts().reindex(cfg.LIFECYCLE_LABELS, fill_value=0)
    for lbl in cfg.LIFECYCLE_LABELS:
        cnt = vc[lbl]
        pct = cnt / len(feat) * 100
        print(f"  {lbl:6s}: {cnt:6,} ({pct:5.1f}%)  {cfg.LABEL_DESC[lbl]}")

    return feat


def cross_validate_with_clusters(feat: pd.DataFrame, cluster_df: pd.DataFrame):
    """레이블 ↔ 궤적 클러스터 교차표로 일관성 검증."""
    merged = feat.merge(cluster_df, on="public_id", how="inner")
    if "traj_cluster" not in merged.columns:
        print("[Step04] 클러스터 정보 없음 — 교차검증 생략")
        return None

    ct = pd.crosstab(merged["label"], merged["traj_cluster"], margins=True)
    ct.to_csv(cfg.TABLE_DIR / "label_cluster_crosstab.csv", encoding="utf-8-sig")

    # 정보이론 지표: Adjusted Mutual Information
    from sklearn.metrics import adjusted_mutual_info_score
    ami = adjusted_mutual_info_score(merged["label"], merged["traj_cluster"])
    print(f"\n[Step04] 레이블 ↔ 클러스터 AMI: {ami:.4f}")
    print(f"  교차표 → label_cluster_crosstab.csv")
    return ct


def label_distribution_by_category(feat: pd.DataFrame):
    """업종별 레이블 분포."""
    if "category" not in feat.columns:
        return None
    ct = pd.crosstab(feat["category"], feat["label"], normalize="index") * 100
    ct = ct.round(1)
    ct.to_csv(cfg.TABLE_DIR / "label_by_category.csv", encoding="utf-8-sig")
    print(f"\n[Step04] 업종별 레이블 분포(%) → label_by_category.csv")
    return ct


def run_labeling(feat, cluster_df=None):
    """레이블링 전체 파이프라인."""
    feat = assign_labels(feat)

    if cluster_df is not None:
        cross_validate_with_clusters(feat, cluster_df)

    label_distribution_by_category(feat)

    feat.to_csv(cfg.TABLE_DIR / "store_features_labeled.csv", index=False, encoding="utf-8-sig")
    print(f"[Step04] 저장 → store_features_labeled.csv")

    # 클래스별 피처 평균
    cols = ["slope_early_mm", "slope_late_mm", "mdd", "cv", "nc_rate",
            "trend_slope", "seasonal_strength", "n_weeks"]
    avail = [c for c in cols if c in feat.columns]
    summary = feat.groupby("label")[avail].mean().reindex(cfg.LIFECYCLE_LABELS).round(4)
    summary.to_csv(cfg.TABLE_DIR / "label_feature_means.csv", encoding="utf-8-sig")
    print(f"\n[Step04] 클래스별 피처 평균:\n{summary.to_string()}")

    return feat
