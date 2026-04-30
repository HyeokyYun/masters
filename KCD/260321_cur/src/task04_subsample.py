"""
Task 04 ─ 업력별 서브샘플 분석
═══════════════════════════════════════════════════════════
미팅 피드백:
  - "업력이 짧은데도 잘하는 애들은 왜 잘하는 걸까?"
  - 업력이 짧은 매장만 서브샘플 → MNLogit 별도 추정
  - 업력 구간별로 나누어 분석 (예: 1년 이하, 1-1.5년, 1.5년+)
  - 업력 분포 히스토그램
  - 업력이 2년만 살아남아도 이미 검증된 업장

출력:
  - fig_business_age_histogram.png     (업력 분포)
  - fig_business_age_vs_label.png      (업력별 레이블 비율)
  - mnlogit_subsample_young            (업력 짧은 매장 MNLogit)
  - mnlogit_subsample_medium           (업력 중간 매장 MNLogit)
  - mnlogit_subsample_mature           (업력 긴 매장 MNLogit)
  - subsample_coefficient_comparison.csv (서브그룹 계수 비교)
"""
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from src import config as cfg
from src.data_loader import load_labeled_features, load_meta, run_mnlogit


# ── 업력 계산 ─────────────────────────────────────────────

def compute_business_age(feat: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    """open_month로부터 업력(개월) 계산."""
    merged = feat.copy()

    if "open_month" not in meta.columns:
        print("[Task04] open_month 없음 → n_weeks 기반 업력 사용")
        merged["business_age_months"] = merged["n_weeks"] / 4.33
        return merged

    oinfo = meta[["public_id", "open_month"]].copy()
    oinfo["open_date"] = pd.to_datetime(
        oinfo["open_month"].astype(str), format="%Y-%m", errors="coerce"
    )

    # 데이터 관측 종료시점 추정: open_date + n_weeks
    merged = merged.merge(oinfo[["public_id", "open_date"]], on="public_id", how="left")

    # 업력 = n_weeks (관측 기간 ≈ 업력, 2019년 이후 개업 필터 적용)
    merged["business_age_months"] = merged["n_weeks"] / 4.33
    merged["business_age_years"] = merged["n_weeks"] / 52.0

    print(f"[Task04] 업력 계산 완료:")
    print(f"  n_weeks: min={merged['n_weeks'].min()}, "
          f"max={merged['n_weeks'].max()}, "
          f"mean={merged['n_weeks'].mean():.1f}")
    print(f"  업력(월): min={merged['business_age_months'].min():.1f}, "
          f"max={merged['business_age_months'].max():.1f}, "
          f"mean={merged['business_age_months'].mean():.1f}")

    return merged


def define_age_groups(df: pd.DataFrame) -> pd.DataFrame:
    """업력 구간 정의."""
    df = df.copy()

    # 관측 주 기반 구간 (MIN_WEEKS=52 이상이므로 모두 1년+)
    n_min = df["n_weeks"].min()
    n_max = df["n_weeks"].max()
    n_range = n_max - n_min

    if n_range < 20:
        # 범위가 좁으면 3등분
        q33, q66 = df["n_weeks"].quantile([0.33, 0.66])
        df["age_group"] = pd.cut(
            df["n_weeks"],
            bins=[n_min - 1, q33, q66, n_max + 1],
            labels=["단기", "중기", "장기"]
        )
    else:
        # 업력 구간: ~65주(≈1.25년), 65-85주(≈1.25-1.6년), 85+주(≈1.6년+)
        cut1 = max(n_min, 65)
        cut2 = max(cut1 + 10, 85)
        bins = [n_min - 1, cut1, cut2, n_max + 1]
        df["age_group"] = pd.cut(
            df["n_weeks"],
            bins=bins,
            labels=[f"~{cut1}주", f"{cut1}-{cut2}주", f"{cut2}주~"]
        )

    vc = df["age_group"].value_counts().sort_index()
    print(f"\n[Task04] 업력 구간 분포:")
    for group, cnt in vc.items():
        print(f"  {group}: {cnt:,} 매장")

    return df


def plot_business_age_histogram(df: pd.DataFrame, meta: pd.DataFrame):
    """업력 분포 히스토그램 (전체 meta + 분석 대상)."""
    plt = cfg.setup_matplotlib()
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 1) 전체 meta의 업력 분포 (개업월 기준)
    ax = axes[0]
    if "open_month" in meta.columns:
        meta_open = pd.to_datetime(meta["open_month"].astype(str),
                                    format="%Y-%m", errors="coerce")
        ref_date = meta_open.max()
        meta_age_months = ((ref_date - meta_open).dt.days / 30.44).dropna()
        meta_age_months = meta_age_months[meta_age_months > 0]

        ax.hist(meta_age_months, bins=80, color="lightgray",
                edgecolor="white", alpha=0.8, label="전체 meta")
        ax.axvline(12, color="red", linestyle="--", alpha=0.6, label="1년")
        ax.axvline(24, color="blue", linestyle="--", alpha=0.6, label="2년")
        ax.set_xlabel("업력 (개월)")
        ax.set_ylabel("매장 수")
        ax.set_title(f"전체 업장 업력 분포 (n={len(meta_age_months):,})")
        ax.legend()
    else:
        ax.text(0.5, 0.5, "open_month 없음", ha="center", va="center",
                transform=ax.transAxes)

    # 2) 분석 대상 매장의 n_weeks 분포
    ax = axes[1]
    ax.hist(df["n_weeks"], bins=40, color="steelblue",
            edgecolor="white", alpha=0.8)
    ax.set_xlabel("관측 기간 (주)")
    ax.set_ylabel("매장 수")
    ax.set_title(f"분석 대상 관측 기간 분포 (n={len(df):,})")

    # 구간 표시
    if "age_group" in df.columns:
        colors = ["#E53935", "#1976D2", "#388E3C"]
        for i, group in enumerate(df["age_group"].cat.categories):
            sub = df[df["age_group"] == group]
            ax.axvline(sub["n_weeks"].min(), color=colors[i % 3],
                       linestyle=":", alpha=0.7, label=f"{group} 시작")
        ax.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(cfg.FIGURE_DIR / "fig_business_age_histogram.png",
                dpi=150, bbox_inches="tight")
    plt.close("all")
    print("  → figures/fig_business_age_histogram.png")


def plot_age_vs_label(df: pd.DataFrame):
    """업력 그룹별 레이블 분포 비교."""
    plt = cfg.setup_matplotlib()

    if "age_group" not in df.columns or df["age_group"].isna().all():
        print("[Task04] 업력 그룹 없음 — 시각화 생략")
        return

    ct = pd.crosstab(df["age_group"], df["label"], normalize="index") * 100
    avail = [l for l in cfg.LIFECYCLE_LABELS if l in ct.columns]
    ct = ct.reindex(columns=avail, fill_value=0)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Stacked bar
    ax = axes[0]
    ct.plot(kind="bar", stacked=True, ax=ax, colormap="Set3")
    ax.set_ylabel("비율 (%)")
    ax.set_title("업력 그룹별 레이블 분포")
    ax.legend(fontsize=7, bbox_to_anchor=(1.05, 1), loc="upper left")
    ax.tick_params(axis="x", rotation=0)

    # Heatmap
    ax = axes[1]
    try:
        import seaborn as sns
        sns.heatmap(ct, annot=True, fmt=".1f", cmap="YlOrRd",
                    ax=ax, cbar_kws={"label": "%"})
    except ImportError:
        im = ax.imshow(ct.values, aspect="auto", cmap="YlOrRd")
        ax.set_xticks(range(len(ct.columns)))
        ax.set_xticklabels(ct.columns, rotation=45)
        ax.set_yticks(range(len(ct.index)))
        ax.set_yticklabels(ct.index)
        plt.colorbar(im, ax=ax, label="%")
    ax.set_title("업력 그룹 × 레이블 (%) Heatmap")

    plt.tight_layout()
    plt.savefig(cfg.FIGURE_DIR / "fig_business_age_vs_label.png",
                dpi=150, bbox_inches="tight")
    plt.close("all")
    print("  → figures/fig_business_age_vs_label.png")


def run_subsample_mnlogit(df: pd.DataFrame) -> dict:
    """업력 구간별 서브샘플 MNLogit 추정."""
    if "age_group" not in df.columns:
        print("[Task04] age_group 없음 → 서브샘플 분석 불가")
        return {}

    base_features = [
        "slope_early_mm", "cv", "mdd", "nc_rate", "del_ratio_log",
        "before_noon", "weekend", "trend_slope", "seasonal_strength",
        "noise_ratio",
    ]

    # 카테고리 더미
    if "category" in df.columns:
        cat_dummies = pd.get_dummies(df["category"], prefix="cat",
                                      drop_first=True, dtype=float)
        for c in cat_dummies.columns:
            df[c] = cat_dummies[c].values
        all_features = base_features + list(cat_dummies.columns)
    else:
        all_features = base_features

    avail = [c for c in all_features if c in df.columns]

    results = {}
    coef_rows = []

    group_names = {"단기": "young", "중기": "medium", "장기": "mature"}
    # fallback for auto-named groups
    for i, group in enumerate(df["age_group"].cat.categories):
        sub = df[df["age_group"] == group].copy()
        label = group_names.get(str(group), f"group{i}")

        vc = sub["label"].value_counts()
        sub = sub[sub["label"].isin(vc[vc >= 10].index)]

        if len(sub) < 50 or sub["label"].nunique() < 3:
            print(f"  [{group}] n={len(sub)}, classes={sub['label'].nunique()} "
                  f"→ 샘플 부족, 생략")
            continue

        print(f"\n[Task04] 서브샘플: {group} (n={len(sub):,})")
        prefix = f"mnlogit_subsample_{label}"

        try:
            result, _ = run_mnlogit(sub, avail, save_prefix=prefix)
            results[str(group)] = result

            params = result.params
            for var_idx, var_name in enumerate(["const"] + avail):
                if var_idx < params.shape[0]:
                    for j in range(params.shape[1]):
                        coef_rows.append({
                            "age_group": str(group),
                            "variable": var_name,
                            "class_idx": j,
                            "coefficient": params.iloc[var_idx, j],
                        })
        except Exception as e:
            print(f"  [{group}] MNLogit 실패: {e}")

    if coef_rows:
        coef_df = pd.DataFrame(coef_rows)
        coef_df.to_csv(cfg.TABLE_DIR / "subsample_coefficient_comparison.csv",
                       index=False, encoding="utf-8-sig")
        print(f"\n[Task04] 계수 비교 저장: subsample_coefficient_comparison.csv")

    return results


def subsample_label_summary(df: pd.DataFrame):
    """서브그룹별 레이블 요약 통계."""
    if "age_group" not in df.columns:
        return

    rows = []
    for group in df["age_group"].dropna().unique():
        sub = df[df["age_group"] == group]
        growth_pct = (sub["label"].str.endswith("_X").sum() / len(sub)) * 100
        stable_pct = (sub["label"].str.endswith("_Y").sum() / len(sub)) * 100
        decline_pct = (sub["label"].str.endswith("_Z").sum() / len(sub)) * 100
        rows.append({
            "age_group": str(group),
            "n": len(sub),
            "growth_pct": round(growth_pct, 1),
            "stable_pct": round(stable_pct, 1),
            "decline_pct": round(decline_pct, 1),
            "nc_rate_mean": round(sub["nc_rate"].mean(), 4) if "nc_rate" in sub else np.nan,
            "cv_mean": round(sub["cv"].mean(), 4) if "cv" in sub else np.nan,
        })

    summary = pd.DataFrame(rows)
    summary.to_csv(cfg.TABLE_DIR / "subsample_label_summary.csv",
                   index=False, encoding="utf-8-sig")
    print(f"\n[Task04] 서브그룹별 요약:")
    print(summary.to_string(index=False))
    return summary


# ── 엔트리 ────────────────────────────────────────────────

def run_task04():
    """Task 04 전체 실행."""
    print("\n" + "=" * 62)
    print("  Task 04: 업력별 서브샘플 분석")
    print("=" * 62)

    feat = load_labeled_features()
    meta = load_meta()

    df = compute_business_age(feat, meta)
    df = define_age_groups(df)

    plot_business_age_histogram(df, meta)
    plot_age_vs_label(df)
    subsample_label_summary(df)
    run_subsample_mnlogit(df)

    print("\n[Task04] 완료")
