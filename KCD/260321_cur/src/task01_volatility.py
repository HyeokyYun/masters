"""
Task 01 ─ 매출 변동성 재정의 (Trend-adjusted Volatility)
═══════════════════════════════════════════════════════════
문제: 기존 CV(=std/mean)는 성장 추세 자체를 변동성으로 잡음.
해결: 추세(trend) 곡선을 피팅하고, 잔차(residual)의 변동성을 측정.

피팅 방법:
  1) Linear       — 직선 회귀
  2) Polynomial-2 — 2차 다항식
  3) Polynomial-3 — 3차 다항식
  4) Log          — log(1+t) 회귀
  5) LOWESS       — 국소 회귀 (비모수)

출력:
  - volatility_methods_comparison.csv  (방법별 변동성 비교)
  - volatility_detrended_features.csv  (최적 detrended CV 피처)
  - mnlogit_detrended_vol              (MNLogit 재추정)
  - fig_volatility_comparison.png      (방법별 비교 시각화)
  - fig_detrended_example.png          (추세 피팅 예시)
"""
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from scipy import stats
from src import config as cfg
from src.data_loader import load_labeled_features, load_weekly_raw, load_meta, run_mnlogit


# ── 추세 피팅 함수들 ─────────────────────────────────────

def _fit_linear(t, y):
    s, intercept, r, p, se = stats.linregress(t, y)
    fitted = s * t + intercept
    return fitted, r**2

def _fit_poly(t, y, degree=2):
    coeffs = np.polyfit(t, y, degree)
    fitted = np.polyval(coeffs, t)
    ss_res = np.sum((y - fitted) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2) + 1e-12
    r2 = max(0, 1 - ss_res / ss_tot)
    return fitted, r2

def _fit_log(t, y):
    t_log = np.log1p(t)
    s, intercept, r, p, se = stats.linregress(t_log, y)
    fitted = s * t_log + intercept
    return fitted, r**2

def _fit_lowess(t, y, frac=0.3):
    try:
        from statsmodels.nonparametric.smoothers_lowess import lowess
        result = lowess(y, t, frac=frac, return_sorted=True)
        fitted = result[:, 1]
        ss_res = np.sum((y - fitted) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2) + 1e-12
        r2 = max(0, 1 - ss_res / ss_tot)
        return fitted, r2
    except ImportError:
        return _fit_poly(t, y, degree=2)


def compute_detrended_volatility(y: np.ndarray) -> dict:
    """매출 시계열에 대해 다양한 추세 피팅 후 잔차 기반 변동성 계산."""
    n = len(y)
    if n < 10 or np.std(y) < 1e-12:
        return None

    t = np.arange(n, dtype=float)
    results = {}

    methods = {
        "linear":  lambda: _fit_linear(t, y),
        "poly2":   lambda: _fit_poly(t, y, 2),
        "poly3":   lambda: _fit_poly(t, y, 3),
        "log":     lambda: _fit_log(t, y),
        "lowess":  lambda: _fit_lowess(t, y),
    }

    for name, fn in methods.items():
        try:
            fitted, r2 = fn()
            residuals = y - fitted
            mean_trend = np.mean(np.abs(fitted)) + 1e-9
            detrended_cv = np.std(residuals) / mean_trend
            rmse = np.sqrt(np.mean(residuals ** 2))

            results[name] = {
                "r2_fit": float(r2),
                "detrended_cv": float(min(detrended_cv, 5.0)),
                "rmse": float(rmse),
                "resid_std": float(np.std(residuals)),
            }
        except Exception:
            continue

    if not results:
        return None

    # 원래 CV (기존 방식)
    original_cv = float(min(np.std(y) / (np.mean(y) + 1e-9), 2.0))
    results["original"] = {
        "r2_fit": 0.0,
        "detrended_cv": original_cv,
        "rmse": float(np.std(y)),
        "resid_std": float(np.std(y)),
    }

    return results


def best_detrended_cv(vol_dict: dict, prefer="poly2") -> float:
    """R² 기반으로 최적 피팅 방법의 detrended CV 반환.
    R²가 비슷하면 단순한 모델(poly2) 우선."""
    if vol_dict is None:
        return np.nan

    candidates = {k: v for k, v in vol_dict.items() if k != "original"}
    if not candidates:
        return vol_dict.get("original", {}).get("detrended_cv", np.nan)

    best_r2 = max(v["r2_fit"] for v in candidates.values())

    # R²가 0.1 미만이면 추세가 거의 없음 → 원래 CV 사용
    if best_r2 < 0.1:
        return vol_dict["original"]["detrended_cv"]

    # R² 차이가 0.05 이내면 단순 모델 선호
    for name in [prefer, "linear", "poly2", "poly3", "log", "lowess"]:
        if name in candidates:
            if candidates[name]["r2_fit"] >= best_r2 - 0.05:
                return candidates[name]["detrended_cv"]

    best_name = max(candidates, key=lambda k: candidates[k]["r2_fit"])
    return candidates[best_name]["detrended_cv"]


# ── 메인 분석 ─────────────────────────────────────────────

def compute_store_volatility(feat: pd.DataFrame, ts_raw: pd.DataFrame,
                              meta: pd.DataFrame) -> pd.DataFrame:
    """모든 매장에 대해 detrended volatility 계산."""
    keep_cols = [c for c in ("public_id", "open_month") if c in meta.columns]
    oinfo = meta[keep_cols].copy()
    oinfo["open_date"] = pd.to_datetime(
        oinfo["open_month"].astype(str), format="%Y-%m", errors="coerce"
    )
    ts = ts_raw.merge(oinfo, on="public_id", how="left")
    ts["weeks_since_open"] = (
        (ts["date_id"] - ts["open_date"]).dt.days // 7
    ).clip(lower=0)

    target_ids = set(feat["public_id"].unique())

    records = []
    groups = ts[ts["public_id"].isin(target_ids)].groupby("public_id")
    total = len(groups)

    for i, (pid, g) in enumerate(groups):
        if (i + 1) % 3000 == 0:
            print(f"  [{i+1:,}/{total:,}]")

        g = (g.sort_values("weeks_since_open")
              .drop_duplicates("weeks_since_open")
              .reset_index(drop=True))
        g = g[g["weeks_since_open"] < cfg.MAX_WEEKS]
        y = g["sales_card"].fillna(0).values.astype(float)
        y = pd.Series(y).interpolate("linear").ffill().bfill().values

        if len(y) < 20:
            continue

        vol = compute_detrended_volatility(y)
        if vol is None:
            continue

        rec = {"public_id": pid}
        for method, vals in vol.items():
            rec[f"cv_{method}"] = vals["detrended_cv"]
            rec[f"r2_{method}"] = vals["r2_fit"]
        rec["cv_best"] = best_detrended_cv(vol)
        rec["best_method"] = _select_best_method(vol)
        records.append(rec)

    vdf = pd.DataFrame(records)
    print(f"[Task01] {len(vdf):,} 매장 변동성 계산 완료")
    return vdf


def _select_best_method(vol_dict: dict) -> str:
    candidates = {k: v for k, v in vol_dict.items() if k != "original"}
    if not candidates:
        return "original"
    best_r2 = max(v["r2_fit"] for v in candidates.values())
    if best_r2 < 0.1:
        return "original"
    for name in ["poly2", "linear", "poly3", "log", "lowess"]:
        if name in candidates and candidates[name]["r2_fit"] >= best_r2 - 0.05:
            return name
    return max(candidates, key=lambda k: candidates[k]["r2_fit"])


def compare_volatility_measures(feat: pd.DataFrame, vol_df: pd.DataFrame):
    """기존 cv vs detrended cv 비교 분석."""
    merged = feat.merge(vol_df[["public_id", "cv_best", "cv_original",
                                 "best_method"]], on="public_id", how="inner")

    comparison = []
    for label in cfg.LIFECYCLE_LABELS:
        sub = merged[merged["label"] == label]
        if len(sub) < 10:
            continue
        comparison.append({
            "label": label,
            "n": len(sub),
            "cv_original_mean": round(sub["cv"].mean(), 4),
            "cv_detrended_mean": round(sub["cv_best"].mean(), 4),
            "cv_original_std": round(sub["cv"].std(), 4),
            "cv_detrended_std": round(sub["cv_best"].std(), 4),
        })

    comp_df = pd.DataFrame(comparison)
    comp_df.to_csv(cfg.TABLE_DIR / "volatility_methods_comparison.csv",
                   index=False, encoding="utf-8-sig")
    print(f"\n[Task01] 변동성 비교 (레이블별):")
    print(comp_df.to_string(index=False))
    return comp_df


def plot_volatility_comparison(feat, vol_df):
    """변동성 비교 시각화."""
    plt = cfg.setup_matplotlib()
    merged = feat.merge(vol_df[["public_id", "cv_best", "best_method"]],
                        on="public_id", how="inner")

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    # 1) 기존 cv vs detrended cv scatter
    ax = axes[0]
    ax.scatter(merged["cv"], merged["cv_best"], alpha=0.2, s=5, c="steelblue")
    ax.plot([0, 2], [0, 2], "r--", alpha=0.5, label="y=x")
    ax.set_xlabel("기존 CV (std/mean)")
    ax.set_ylabel("Detrended CV (잔차/추세)")
    ax.set_title("기존 CV vs Detrended CV")
    ax.legend()

    # 2) 레이블별 detrended cv 분포
    ax = axes[1]
    labels_in_data = [l for l in cfg.LIFECYCLE_LABELS if l in merged["label"].values]
    data_by_label = [merged.loc[merged["label"] == l, "cv_best"].dropna().values
                     for l in labels_in_data]
    ax.boxplot(data_by_label, labels=labels_in_data, vert=True)
    ax.set_ylabel("Detrended CV")
    ax.set_title("레이블별 Detrended CV 분포")
    ax.tick_params(axis="x", rotation=45)

    # 3) best method 분포
    ax = axes[2]
    method_counts = merged["best_method"].value_counts()
    ax.bar(method_counts.index, method_counts.values, color="steelblue")
    ax.set_ylabel("매장 수")
    ax.set_title("최적 추세 피팅 방법 분포")
    ax.tick_params(axis="x", rotation=45)

    plt.tight_layout()
    plt.savefig(cfg.FIGURE_DIR / "fig_volatility_comparison.png",
                dpi=150, bbox_inches="tight")
    plt.close("all")
    print("  → figures/fig_volatility_comparison.png")


def plot_detrend_example(ts_raw, meta, feat, n_examples=4):
    """추세 피팅 예시 시각화."""
    plt = cfg.setup_matplotlib()

    keep = [c for c in ("public_id", "open_month") if c in meta.columns]
    oinfo = meta[keep].copy()
    oinfo["open_date"] = pd.to_datetime(
        oinfo["open_month"].astype(str), format="%Y-%m", errors="coerce"
    )
    ts = ts_raw.merge(oinfo, on="public_id", how="left")
    ts["weeks_since_open"] = (
        (ts["date_id"] - ts["open_date"]).dt.days // 7
    ).clip(lower=0)

    sample_ids = feat.sample(n=min(n_examples, len(feat)),
                             random_state=cfg.SEED)["public_id"].values

    fig, axes = plt.subplots(n_examples, 1, figsize=(12, 3 * n_examples))
    if n_examples == 1:
        axes = [axes]

    for ax, pid in zip(axes, sample_ids):
        g = ts[ts["public_id"] == pid].sort_values("weeks_since_open")
        g = g.drop_duplicates("weeks_since_open").reset_index(drop=True)
        g = g[g["weeks_since_open"] < cfg.MAX_WEEKS]
        y = g["sales_card"].fillna(0).values.astype(float)
        y = pd.Series(y).interpolate("linear").ffill().bfill().values
        t = np.arange(len(y), dtype=float)

        ax.plot(t, y, "k-", alpha=0.4, linewidth=0.8, label="실제 매출")

        colors = {"linear": "blue", "poly2": "red", "poly3": "green",
                  "log": "orange", "lowess": "purple"}
        for name, fn in [("linear", lambda: _fit_linear(t, y)),
                         ("poly2", lambda: _fit_poly(t, y, 2)),
                         ("poly3", lambda: _fit_poly(t, y, 3)),
                         ("lowess", lambda: _fit_lowess(t, y))]:
            try:
                fitted, r2 = fn()
                ax.plot(t, fitted, color=colors[name], linewidth=1.5,
                        label=f"{name} (R²={r2:.2f})")
            except Exception:
                pass

        label = feat.loc[feat["public_id"] == pid, "label"].values
        lbl_str = label[0] if len(label) > 0 else "?"
        ax.set_title(f"Store {pid[:8]}... (Label: {lbl_str})")
        ax.legend(fontsize=8, loc="upper right")
        ax.set_xlabel("Week")
        ax.set_ylabel("매출")

    plt.tight_layout()
    plt.savefig(cfg.FIGURE_DIR / "fig_detrended_example.png",
                dpi=150, bbox_inches="tight")
    plt.close("all")
    print("  → figures/fig_detrended_example.png")


def run_mnlogit_with_detrended(feat, vol_df):
    """Detrended CV로 기존 cv 대체하여 MNLogit 재추정."""
    merged = feat.merge(vol_df[["public_id", "cv_best"]], on="public_id", how="inner")
    merged = merged.rename(columns={"cv": "cv_original"})
    merged = merged.rename(columns={"cv_best": "cv"})

    feature_cols = [
        "slope_early_mm", "cv", "mdd", "nc_rate", "del_ratio_log",
        "before_noon", "weekend", "trend_slope", "seasonal_strength",
        "noise_ratio", "n_weeks",
    ]

    if "category" in merged.columns:
        cat_dummies = pd.get_dummies(merged["category"], prefix="cat",
                                      drop_first=True, dtype=float)
        for c in cat_dummies.columns:
            merged[c] = cat_dummies[c].values
        feature_cols = feature_cols + list(cat_dummies.columns)

    avail = [c for c in feature_cols if c in merged.columns]
    print(f"\n[Task01] MNLogit with detrended CV (변수 {len(avail)}개)")

    result, _ = run_mnlogit(merged, avail, save_prefix="mnlogit_detrended_vol")
    return result


# ── 엔트리 ────────────────────────────────────────────────

def run_task01():
    """Task 01 전체 실행."""
    print("\n" + "=" * 62)
    print("  Task 01: 매출 변동성 재정의 (Trend-adjusted)")
    print("=" * 62)

    feat = load_labeled_features()
    meta = load_meta()
    ts_raw = load_weekly_raw()

    vol_df = compute_store_volatility(feat, ts_raw, meta)
    vol_df.to_csv(cfg.TABLE_DIR / "volatility_detrended_features.csv",
                  index=False, encoding="utf-8-sig")

    compare_volatility_measures(feat, vol_df)
    plot_volatility_comparison(feat, vol_df)
    plot_detrend_example(ts_raw, meta, feat, n_examples=4)
    run_mnlogit_with_detrended(feat, vol_df)

    print("\n[Task01] 완료")
