"""
Step 04b ─ 레이블별 기술통계 + 데이터 기반 변수 선택
  ● 레이블(생애주기)별 Summary Statistics (평균, 표준편차, 중앙값 등)
  ● Kruskal-Wallis H-test (비모수 다군 차이 검정)
  ● Effect Size (η²) 기반 변수 중요도 순위
  ● 유의 변수 자동 선별 → Step 05 회귀분석 / Step 06 예측에 전달
"""
import numpy as np
import pandas as pd
from scipy import stats as sp_stats
from src import config as cfg


CANDIDATE_FEATURES = [
    "slope_early_mm", "slope_late_mm", "slope_all_mm", "slope_tail_mm",
    "trend_slope", "r2", "r2_early", "cv", "mdd", "nc_rate",
    "del_ratio_log", "before_noon", "weekend",
    "seasonal_strength", "noise_ratio", "n_weeks",
]

EARLY_FEATURE_MAP = {
    "slope_early_mm": "e_slope_early",
    "slope_all_mm":   "e_slope_all",
    "cv":             "e_cv",
    "mdd":            "e_mdd",
    "r2":             "e_r2",
    "nc_rate":        "e_nc_rate",
}


# ─────────────────────────────────────────────────────────
def compute_summary_stats(feat: pd.DataFrame) -> pd.DataFrame:
    """레이블별 기술통계 (평균, 표준편차, 중앙값, 사분위수)."""
    avail = [c for c in CANDIDATE_FEATURES if c in feat.columns]
    rows = []
    for var in avail:
        for label in cfg.LIFECYCLE_LABELS:
            sub = feat.loc[feat["label"] == label, var].dropna()
            if len(sub) == 0:
                continue
            rows.append({
                "variable": var,
                "label": label,
                "n": len(sub),
                "mean": round(sub.mean(), 6),
                "std": round(sub.std(), 6),
                "median": round(sub.median(), 6),
                "q25": round(sub.quantile(0.25), 6),
                "q75": round(sub.quantile(0.75), 6),
                "min": round(sub.min(), 6),
                "max": round(sub.max(), 6),
            })
    summary = pd.DataFrame(rows)
    out_path = cfg.TABLE_DIR / "label_summary_stats.csv"
    summary.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[Step04b] 레이블별 기술통계 ({len(avail)}개 변수 x {len(cfg.LIFECYCLE_LABELS)} 레이블)")
    print(f"  저장 → {out_path.name}")
    return summary


# ─────────────────────────────────────────────────────────
def variable_importance_test(feat: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """Kruskal-Wallis H-test + η² 효과크기로 변수 중요도 평가."""
    avail = [c for c in CANDIDATE_FEATURES if c in feat.columns]
    unique_labels = sorted(feat["label"].unique())

    results = []
    for var in avail:
        valid = feat.dropna(subset=[var])
        groups = [valid.loc[valid["label"] == lbl, var].values for lbl in unique_labels]
        groups = [g for g in groups if len(g) >= 5]
        if len(groups) < 2:
            continue

        h_stat, p_value = sp_stats.kruskal(*groups)

        n_total = sum(len(g) for g in groups)
        k = len(groups)
        eta_sq = max(0, (h_stat - k + 1) / (n_total - k)) if n_total > k else 0.0

        results.append({
            "variable": var,
            "H_statistic": round(h_stat, 2),
            "p_value": p_value,
            "eta_squared": round(eta_sq, 4),
            "significant": p_value < alpha,
            "n_valid": n_total,
        })

    result_df = (pd.DataFrame(results)
                 .sort_values("eta_squared", ascending=False)
                 .reset_index(drop=True))
    result_df["rank"] = range(1, len(result_df) + 1)

    out_path = cfg.TABLE_DIR / "variable_importance_test.csv"
    result_df.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"\n[Step04b] 변수 중요도 검정 (Kruskal-Wallis H-test):")
    print(f"  {'순위':>4}  {'변수':<20}  {'H통계량':>10}  {'p-value':>12}  {'eta_sq':>8}  유의")
    print(f"  {'─' * 70}")
    for _, row in result_df.iterrows():
        sig = ("***" if row["p_value"] < 0.001
               else "**" if row["p_value"] < 0.01
               else "*" if row["p_value"] < 0.05
               else "")
        print(f"  {int(row['rank']):>4}  {row['variable']:<20}"
              f"  {row['H_statistic']:>10.1f}  {row['p_value']:>12.2e}"
              f"  {row['eta_squared']:>8.4f}  {sig}")

    return result_df


# ─────────────────────────────────────────────────────────
def select_variables(test_df: pd.DataFrame,
                     alpha: float = 0.05,
                     min_eta_sq: float = 0.01) -> list:
    """유의(p < alpha)하고 효과크기(η² ≥ min_eta_sq)가 충분한 변수 선별."""
    selected = test_df[
        (test_df["significant"]) & (test_df["eta_squared"] >= min_eta_sq)
    ]["variable"].tolist()

    out_path = cfg.TABLE_DIR / "selected_variables.csv"
    pd.DataFrame({"rank": range(1, len(selected) + 1), "variable": selected}).to_csv(
        out_path, index=False, encoding="utf-8-sig")

    print(f"\n[Step04b] 선별된 X변수 ({len(selected)}개, p<{alpha}, eta_sq>={min_eta_sq}):")
    for i, v in enumerate(selected, 1):
        eta = test_df.loc[test_df["variable"] == v, "eta_squared"].values[0]
        print(f"    {i}. {v}  (eta_sq={eta:.4f})")

    return selected


# ─────────────────────────────────────────────────────────
def map_to_early_features(selected_vars: list) -> list:
    """선별된 전체기간 변수를 조기(30주) 변수명으로 매핑."""
    early_vars = []
    for v in selected_vars:
        if v in EARLY_FEATURE_MAP:
            early_vars.append(EARLY_FEATURE_MAP[v])
    return early_vars


# ─────────────────────────────────────────────────────────
def run_variable_selection(feat: pd.DataFrame) -> dict:
    """변수 선택 전체 파이프라인."""
    print("\n" + "=" * 60)
    print("[Step04b] 레이블별 기술통계 + 데이터 기반 변수 선택")
    print("=" * 60)

    summary = compute_summary_stats(feat)
    test_df = variable_importance_test(feat)
    selected = select_variables(test_df)
    early_selected = map_to_early_features(selected)

    # 조기예측용 변수도 파일로 저장
    pd.DataFrame({"variable": early_selected}).to_csv(
        cfg.TABLE_DIR / "selected_early_variables.csv",
        index=False, encoding="utf-8-sig")

    print(f"\n[Step04b] 조기예측용 변수 매핑 ({len(early_selected)}개):")
    for orig, mapped in zip(selected, [EARLY_FEATURE_MAP.get(v) for v in selected]):
        if mapped:
            print(f"    {orig} → {mapped}")

    unmapped = [v for v in selected if v not in EARLY_FEATURE_MAP]
    if unmapped:
        print(f"  (조기 피처 매핑 불가: {unmapped})")

    return {
        "summary": summary,
        "test": test_df,
        "selected_vars": selected,
        "early_selected_vars": early_selected,
    }
