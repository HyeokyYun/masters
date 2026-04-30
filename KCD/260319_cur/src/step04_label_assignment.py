"""
Step 04 ─ 생애주기 레이블 할당 (Data-driven, 12-class)
  slope_early × slope_late × slope_all → 12 클래스

  1st letter: 전반기 추세 (U=상승, D=하락)  ← slope_early_mm
  2nd letter: 후반기 추세 (U=상승, D=하락)  ← slope_late_mm
  suffix:     전체 추세                      ← slope_all_mm
              _X = 전체 추세 상승  (slope_all > +threshold)
              _Y = 전체 추세 유지  (-threshold ≤ slope_all ≤ +threshold)
              _Z = 전체 추세 하락  (slope_all < -threshold)

  threshold = std(slope_all_mm) × SLOPE_ALL_THRESHOLD_FACTOR

  DD_Z / DD_Y / DD_X   전반↓ 후반↓ + 전체방향
  DU_Z / DU_Y / DU_X   전반↓ 후반↑ + 전체방향
  UU_Z / UU_Y / UU_X   전반↑ 후반↑ + 전체방향
  UD_Z / UD_Y / UD_X   전반↑ 후반↓ + 전체방향
"""
import pandas as pd
import numpy as np
from src import config as cfg


def _overall_suffix(slope_all: float, threshold: float) -> str:
    """전체 추세 방향에 따라 _X/_Y/_Z 접미사 반환."""
    if slope_all > threshold:
        return "_X"
    elif slope_all < -threshold:
        return "_Z"
    else:
        return "_Y"


def assign_labels(feat: pd.DataFrame) -> pd.DataFrame:
    """피처 DataFrame에 label 컬럼 추가.

    분류 기준:
      - 전반/후반 방향: slope_early_mm, slope_late_mm 부호 → D/U
      - 전체 추세 방향: slope_all_mm vs ±threshold → Z/Y/X
      - threshold = std(slope_all_mm) × SLOPE_ALL_THRESHOLD_FACTOR
    """
    sa_std = feat["slope_all_mm"].std()
    threshold = sa_std * cfg.SLOPE_ALL_THRESHOLD_FACTOR
    print(f"[Step04] 분류 기준: slope_early × slope_late × slope_all(3단계)")
    print(f"  slope_all_mm: mean={feat['slope_all_mm'].mean():.6f}, "
          f"median={feat['slope_all_mm'].median():.6f}, std={sa_std:.6f}")
    print(f"  유지(Y) 대역: [{-threshold:.6f}, {+threshold:.6f}]  "
          f"(factor={cfg.SLOPE_ALL_THRESHOLD_FACTOR})")

    def _label(row):
        prefix_e = "D" if row["slope_early_mm"] <= 0 else "U"
        prefix_l = "D" if row["slope_late_mm"]  <= 0 else "U"
        suffix   = _overall_suffix(row["slope_all_mm"], threshold)
        return f"{prefix_e}{prefix_l}{suffix}"

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
    cols = ["slope_early_mm", "slope_late_mm", "slope_all_mm", "mdd", "cv",
            "nc_rate", "trend_slope", "seasonal_strength", "n_weeks"]
    avail = [c for c in cols if c in feat.columns]
    summary = feat.groupby("label")[avail].mean().reindex(cfg.LIFECYCLE_LABELS).round(4)
    summary.to_csv(cfg.TABLE_DIR / "label_feature_means.csv", encoding="utf-8-sig")
    print(f"\n[Step04] 클래스별 피처 평균:\n{summary.to_string()}")

    return feat
