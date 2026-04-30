"""
Task 03 ─ 대표자 연령/성별 변수 추가
═══════════════════════════════════════════════════════════
미팅 피드백:
  - 대표자 연령(age), 성별(gender) 변수를 MNLogit에 추가
  - "뭐가 나타나면 얘기를 더 할 수 있고, 안 나타나도 안 나타난다고 얘기할 수 있으니까"

출력:
  - mnlogit_demographics           (MNLogit 결과)
  - demographics_summary.csv       (연령/성별별 레이블 분포)
  - fig_demographics.png           (연령/성별 분포)
"""
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from src import config as cfg
from src.data_loader import load_labeled_features, load_meta, run_mnlogit


def prepare_demographics(meta: pd.DataFrame) -> pd.DataFrame:
    """meta에서 연령·성별 변수 추출 및 가공."""
    demo = meta[["public_id"]].copy()

    # 연령 (age)
    if "age" in meta.columns:
        demo["owner_age"] = pd.to_numeric(meta["age"], errors="coerce")
        demo["owner_age"] = demo["owner_age"].clip(18, 80)

        bins = [0, 29, 39, 49, 59, 100]
        labels = ["20대이하", "30대", "40대", "50대", "60대이상"]
        demo["age_group"] = pd.cut(demo["owner_age"], bins=bins,
                                    labels=labels, right=True)
        valid = demo["owner_age"].notna().sum()
        print(f"[Task03] 연령 정보: {valid:,} / {len(demo):,} 매장 "
              f"(mean={demo['owner_age'].mean():.1f})")
    else:
        print("[Task03] 연령(age) 컬럼 없음")
        demo["owner_age"] = np.nan
        demo["age_group"] = np.nan

    # 성별 (gender) — meta에 존재하면 사용
    gender_cols = [c for c in meta.columns
                   if any(k in c.lower() for k in ("gender", "sex", "성별"))]
    if gender_cols:
        gcol = gender_cols[0]
        demo["gender"] = meta[gcol]
        print(f"[Task03] 성별 정보 발견: {gcol}")
    else:
        print("[Task03] 성별 정보 없음 — 연령만 사용")
        demo["gender"] = np.nan

    return demo


def demographics_summary(feat: pd.DataFrame, demo: pd.DataFrame) -> pd.DataFrame:
    """연령/성별별 레이블 분포 요약."""
    merged = feat.merge(demo, on="public_id", how="left")

    summaries = []

    # 연령 그룹별
    if merged["age_group"].notna().any():
        for ag in merged["age_group"].dropna().unique():
            sub = merged[merged["age_group"] == ag]
            dist = sub["label"].value_counts(normalize=True) * 100
            for label, pct in dist.items():
                summaries.append({
                    "group_var": "age_group",
                    "group_value": ag,
                    "label": label,
                    "pct": round(pct, 2),
                    "n": len(sub),
                })

    # 성별
    if merged["gender"].notna().any():
        for g in merged["gender"].dropna().unique():
            sub = merged[merged["gender"] == g]
            dist = sub["label"].value_counts(normalize=True) * 100
            for label, pct in dist.items():
                summaries.append({
                    "group_var": "gender",
                    "group_value": g,
                    "label": label,
                    "pct": round(pct, 2),
                    "n": len(sub),
                })

    if summaries:
        sdf = pd.DataFrame(summaries)
        sdf.to_csv(cfg.TABLE_DIR / "demographics_summary.csv",
                   index=False, encoding="utf-8-sig")
        print(f"[Task03] 인구통계 요약 저장: {len(sdf)} 행")
        return sdf
    return pd.DataFrame()


def run_mnlogit_demographics(feat: pd.DataFrame, demo: pd.DataFrame):
    """연령/성별 추가 MNLogit."""
    merged = feat.merge(demo, on="public_id", how="left")

    base_features = [
        "slope_early_mm", "cv", "mdd", "nc_rate", "del_ratio_log",
        "before_noon", "weekend", "trend_slope", "seasonal_strength",
        "noise_ratio", "n_weeks",
    ]

    # 연령 변수 추가
    extra_features = []
    if merged["owner_age"].notna().mean() > 0.3:
        merged["owner_age_z"] = (
            (merged["owner_age"] - merged["owner_age"].mean())
            / (merged["owner_age"].std() + 1e-9)
        )
        extra_features.append("owner_age_z")

        # 연령 그룹 더미
        if merged["age_group"].notna().any():
            age_dummies = pd.get_dummies(merged["age_group"], prefix="age",
                                          drop_first=True, dtype=float)
            for c in age_dummies.columns:
                merged[c] = age_dummies[c].values
            extra_features.extend(list(age_dummies.columns))

    # 성별 변수 추가
    if merged["gender"].notna().mean() > 0.3:
        gen_dummies = pd.get_dummies(merged["gender"], prefix="gender",
                                      drop_first=True, dtype=float)
        for c in gen_dummies.columns:
            merged[c] = gen_dummies[c].values
        extra_features.extend(list(gen_dummies.columns))

    if not extra_features:
        print("[Task03] 추가할 인구통계 변수 없음 (결측 과다)")
        return None

    # 카테고리 더미
    if "category" in merged.columns:
        cat_dummies = pd.get_dummies(merged["category"], prefix="cat",
                                      drop_first=True, dtype=float)
        for c in cat_dummies.columns:
            merged[c] = cat_dummies[c].values
        base_features = base_features + list(cat_dummies.columns)

    # (A) 연령만 (연속)
    features_age_cont = base_features + ["owner_age_z"] if "owner_age_z" in extra_features else base_features
    avail_a = [c for c in features_age_cont if c in merged.columns]
    print(f"\n[Task03] Model A: 기본 + 연령(연속) ({len(avail_a)}개 변수)")
    result_a, _ = run_mnlogit(merged, avail_a,
                              save_prefix="mnlogit_demographics_age_cont")

    # (B) 연령 그룹 더미
    age_dummy_cols = [c for c in extra_features if c.startswith("age_")]
    if age_dummy_cols:
        features_age_group = base_features + age_dummy_cols
        avail_b = [c for c in features_age_group if c in merged.columns]
        print(f"\n[Task03] Model B: 기본 + 연령(더미) ({len(avail_b)}개 변수)")
        result_b, _ = run_mnlogit(merged, avail_b,
                                  save_prefix="mnlogit_demographics_age_group")

    # (C) 연령 + 성별 (있으면)
    gender_cols = [c for c in extra_features if c.startswith("gender_")]
    if gender_cols:
        features_all = base_features + extra_features
        avail_c = [c for c in features_all if c in merged.columns]
        print(f"\n[Task03] Model C: 기본 + 연령 + 성별 ({len(avail_c)}개 변수)")
        result_c, _ = run_mnlogit(merged, avail_c,
                                  save_prefix="mnlogit_demographics_full")

    return result_a


def plot_demographics(feat: pd.DataFrame, demo: pd.DataFrame):
    """연령/성별 분포 시각화."""
    plt = cfg.setup_matplotlib()
    merged = feat.merge(demo, on="public_id", how="left")

    has_age = merged["owner_age"].notna().any()
    has_gender = merged["gender"].notna().any()
    n_plots = int(has_age) * 2 + int(has_gender)
    if n_plots == 0:
        print("[Task03] 시각화 생략 — 인구통계 데이터 없음")
        return

    fig, axes = plt.subplots(1, max(n_plots, 1), figsize=(6 * n_plots, 5))
    if n_plots == 1:
        axes = [axes]
    ax_idx = 0

    if has_age:
        # 연령 히스토그램
        ax = axes[ax_idx]
        merged["owner_age"].dropna().hist(ax=ax, bins=30, color="steelblue",
                                           edgecolor="white")
        ax.set_xlabel("대표자 연령")
        ax.set_ylabel("매장 수")
        ax.set_title("대표자 연령 분포")
        ax_idx += 1

        # 연령 그룹별 레이블 비율 (heatmap)
        if merged["age_group"].notna().any():
            ax = axes[ax_idx]
            ct = pd.crosstab(merged["age_group"], merged["label"],
                             normalize="index") * 100
            avail_labels = [l for l in cfg.LIFECYCLE_LABELS if l in ct.columns]
            ct = ct.reindex(columns=avail_labels, fill_value=0)
            try:
                import seaborn as sns
                sns.heatmap(ct, annot=True, fmt=".1f", cmap="YlOrRd",
                            ax=ax, cbar_kws={"label": "%"})
            except ImportError:
                ax.imshow(ct.values, aspect="auto", cmap="YlOrRd")
                ax.set_xticks(range(len(ct.columns)))
                ax.set_xticklabels(ct.columns, rotation=45)
                ax.set_yticks(range(len(ct.index)))
                ax.set_yticklabels(ct.index)
            ax.set_title("연령 그룹별 레이블 분포 (%)")
            ax_idx += 1

    if has_gender:
        ax = axes[ax_idx]
        ct = pd.crosstab(merged["gender"], merged["label"],
                         normalize="index") * 100
        ct.plot(kind="bar", ax=ax, stacked=True, colormap="Set3")
        ax.set_title("성별 레이블 분포 (%)")
        ax.set_ylabel("%")
        ax.legend(fontsize=6, bbox_to_anchor=(1.05, 1))
        ax_idx += 1

    plt.tight_layout()
    plt.savefig(cfg.FIGURE_DIR / "fig_demographics.png",
                dpi=150, bbox_inches="tight")
    plt.close("all")
    print("  → figures/fig_demographics.png")


# ── 엔트리 ────────────────────────────────────────────────

def run_task03():
    """Task 03 전체 실행."""
    print("\n" + "=" * 62)
    print("  Task 03: 대표자 연령/성별 변수 추가")
    print("=" * 62)

    feat = load_labeled_features()
    meta = load_meta()

    demo = prepare_demographics(meta)
    demographics_summary(feat, demo)
    run_mnlogit_demographics(feat, demo)
    plot_demographics(feat, demo)

    print("\n[Task03] 완료")
