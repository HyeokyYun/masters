"""
변곡점 추출 및 P1/P2 라벨링 (Piecewise Linear Regression)
- 업장(public_id)별 142주 주별 매출에 대해 분절 회귀로 변곡점 탐색
- 변곡점 이전 = P1, 이후 = P2
- P1/P2 기울기 각각 양수면 'U', 음수면 'D'
- 변곡점 미발견 시 전체 주수의 절반(142주 기준 71주)으로 분할

Run from 260204_gem: python scripts/run_01_inflection_p1p2.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.linear_model import LinearRegression

ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = ROOT / "outputs" / "logs" / "run_01_inflection_p1p2.log"
TABLES_DIR = ROOT / "outputs" / "tables"
FIGURES_DIR = ROOT / "outputs" / "figures"

DEFAULT_HALF_WEEKS = 71  # 142주의 절반


def load_config():
    try:
        import yaml
        with open(ROOT / "configs" / "base.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return {
            "data": {
                "weekly_parquet_primary": "../original_data/weekly_processed.parquet",
                "weekly_parquet_fallback": "../original_data/weekly.parquet",
                "id_col_store": "public_id",
                "time_col_week": "day_after1",
                "y_col_sales": "sales_card",
            },
            "inflection": {"min_segment_weeks": 2, "rss_improvement_threshold": 0.0},
        }


def get_weekly_path(cfg):
    data = cfg.get("data", {})
    primary = ROOT / data.get("weekly_parquet_primary", "../original_data/weekly_processed.parquet")
    if primary.exists():
        return primary
    fallback = ROOT / data.get("weekly_parquet_fallback", "../original_data/weekly.parquet")
    return fallback


def rss(y_true, y_pred):
    return np.sum((np.asarray(y_true) - np.asarray(y_pred)) ** 2)


def fit_slope_intercept(x, y):
    """OLS: y = a + b*x. Returns (intercept, slope)."""
    x = np.asarray(x).reshape(-1, 1)
    y = np.asarray(y).ravel()
    reg = LinearRegression(fit_intercept=True).fit(x, y)
    return float(reg.intercept_), float(reg.coef_[0])


def piecewise_fit_and_rss(x, y, break_week):
    """
    두 구간으로 나누어 각각 선형 회귀 후 총 RSS 반환.
    P1: x <= break_week, P2: x >= break_week (변곡점을 break_week 주 말로 둠)
    """
    x, y = np.asarray(x).ravel(), np.asarray(y).ravel()
    mask1 = x <= break_week
    mask2 = x > break_week
    if mask1.sum() < 2 or mask2.sum() < 2:
        return np.nan, np.nan, np.nan, np.nan, np.nan
    x1, y1 = x[mask1], y[mask1]
    x2, y2 = x[mask2], y[mask2]
    a1, b1 = fit_slope_intercept(x1, y1)
    a2, b2 = fit_slope_intercept(x2, y2)
    pred1 = a1 + b1 * x1
    pred2 = a2 + b2 * x2
    rss1 = rss(y1, pred1)
    rss2 = rss(y2, pred2)
    return rss1 + rss2, b1, b2, a1, a2


def find_inflection_and_labels(weeks, sales, min_segment_weeks, default_half_weeks, use_fallback_if_no_improvement=False, rss_threshold=0.0):
    """
    가능한 변곡점(break_week)을 모두 시도해 총 RSS가 최소인 변곡점을 찾고,
    P1/P2 기울기로 U/D 라벨 부여.
    변곡점 미발견(유효 구간 없음)이면 default_half_weeks를 변곡점으로 사용.

    Returns:
        inflection_week (int),
        P1_label ('U'|'D'),
        P2_label ('U'|'D'),
        slope_P1, slope_P2,
        used_fallback (bool)
    """
    weeks = np.asarray(weeks).ravel()
    sales = np.asarray(sales).ravel()
    n = len(weeks)
    if n < 2 * min_segment_weeks:
        # 데이터 부족: 전체 기울기만 계산 후 한 구간으로 처리하거나 절반으로 나눔
        half = max(1, n // 2)
        _, b1, b2, _, _ = piecewise_fit_and_rss(weeks, sales, weeks[half - 1])
        if np.isnan(b1):
            b1 = 0.0
            b2 = 0.0
        return half, ("U" if b1 > 0 else "D"), ("U" if b2 > 0 else "D"), b1, b2, True

    w_min, w_max = int(weeks.min()), int(weeks.max())
    # 변곡 후보: 실제 존재하는 주만 사용해 속도 개선 (각 구간 최소 min_segment_weeks 확보)
    unique_weeks = np.unique(weeks)
    break_candidates = [w for w in unique_weeks
                        if (w >= w_min + min_segment_weeks - 1 and w <= w_max - min_segment_weeks)]
    if not break_candidates:
        default_break = default_half_weeks if w_max >= DEFAULT_HALF_WEEKS else (w_min + w_max) // 2
        total_rss, b1, b2, _, _ = piecewise_fit_and_rss(weeks, sales, default_break)
        if np.isnan(total_rss):
            b1 = b2 = 0.0
        return default_break, ("U" if b1 > 0 else "D"), ("U" if b2 > 0 else "D"), b1, b2, True

    best_break = None
    best_rss = np.inf
    best_b1 = best_b2 = np.nan

    for b in break_candidates:
        total_rss, b1, b2, _, _ = piecewise_fit_and_rss(weeks, sales, b)
        if np.isnan(total_rss):
            continue
        if total_rss < best_rss:
            best_rss = total_rss
            best_break = b
            best_b1, best_b2 = b1, b2

    if best_break is None:
        default_break = default_half_weeks if w_max >= DEFAULT_HALF_WEEKS else (w_min + w_max) // 2
        total_rss, b1, b2, _, _ = piecewise_fit_and_rss(weeks, sales, default_break)
        if np.isnan(total_rss):
            b1 = b2 = 0.0
        return default_break, ("U" if b1 > 0 else "D"), ("U" if b2 > 0 else "D"), float(b1), float(b2), True

    # (선택) 단일 직선 대비 개선이 거의 없으면 절반 기준 사용
    _, b_single = fit_slope_intercept(weeks, sales)
    pred_single = np.polyval([b_single, np.mean(sales) - b_single * np.mean(weeks)], weeks)
    rss_single = rss(sales, pred_single)
    if use_fallback_if_no_improvement and rss_single > 0 and (rss_single - best_rss) / rss_single <= rss_threshold:
        default_break = default_half_weeks if w_max >= DEFAULT_HALF_WEEKS else (w_min + w_max) // 2
        total_rss, b1, b2, _, _ = piecewise_fit_and_rss(weeks, sales, default_break)
        if np.isnan(total_rss):
            b1, b2 = best_b1, best_b2
        return default_break, ("U" if b1 > 0 else "D"), ("U" if b2 > 0 else "D"), b1, b2, True

    return best_break, ("U" if best_b1 > 0 else "D"), ("U" if best_b2 > 0 else "D"), best_b1, best_b2, False


def main(limit_stores=None):
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    def log(msg: str):
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    cfg = load_config()
    data_cfg = cfg.get("data", {})
    inflection_cfg = cfg.get("inflection", {})
    min_segment_weeks = inflection_cfg.get("min_segment_weeks", 2)
    default_half_weeks = DEFAULT_HALF_WEEKS
    rss_threshold = inflection_cfg.get("rss_improvement_threshold", 0.0)
    use_fallback = rss_threshold > 0

    weekly_path = get_weekly_path(cfg)
    if not weekly_path.exists():
        log(f"ERROR: Weekly parquet not found. Tried: {weekly_path}")
        return

    log(f"Loading weekly data from {weekly_path}")
    df = pd.read_parquet(weekly_path)
    col_store = data_cfg.get("id_col_store", "public_id")
    col_week = data_cfg.get("time_col_week", "day_after1")
    col_sales = data_cfg.get("y_col_sales", "sales_card")
    for c in [col_store, col_week, col_sales]:
        if c not in df.columns:
            log(f"ERROR: Column not found: {c}. Columns: {list(df.columns)}")
            return

    log(f"Using columns: store={col_store}, week={col_week}, sales={col_sales}")
    store_ids = df[col_store].unique()
    if limit_stores is not None:
        store_ids = store_ids[: limit_stores]
        df = df[df[col_store].isin(store_ids)]
    n_stores = len(store_ids)
    log(f"Stores: {n_stores}, total rows: {len(df)}")

    results = []
    for i, (public_id, grp) in enumerate(df.groupby(col_store)):
        if (i + 1) % 5000 == 0 or i == 0:
            log(f"Processing store {i+1}/{n_stores} ...")
        grp = grp.sort_values(col_week)
        weeks = grp[col_week].values
        sales = grp[col_sales].values
        n_weeks = len(weeks)
        default_half = DEFAULT_HALF_WEEKS if n_weeks >= DEFAULT_HALF_WEEKS else max(1, n_weeks // 2)
        inf_week, p1_label, p2_label, slope_p1, slope_p2, used_fallback = find_inflection_and_labels(
            weeks, sales, min_segment_weeks, default_half, use_fallback_if_no_improvement=use_fallback, rss_threshold=rss_threshold
        )
        results.append({
            "public_id": public_id,
            "n_weeks": n_weeks,
            "inflection_week": inf_week,
            "P1_label": p1_label,
            "P2_label": p2_label,
            "slope_P1": slope_p1,
            "slope_P2": slope_p2,
            "used_fallback": used_fallback,
        })

    out_df = pd.DataFrame(results)
    out_path = TABLES_DIR / "inflection_p1p2_labels.csv"
    out_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    log(f"Saved: {out_path} (rows={len(out_df)})")

    # 요약
    log(f"P1/P2 label counts:\n{out_df.groupby(['P1_label','P2_label']).size().unstack(fill_value=0)}")
    log(f"Used fallback (no inflection): {out_df['used_fallback'].sum()} / {len(out_df)}")
    log("Done.")


if __name__ == "__main__":
    import sys
    limit = None
    for i, arg in enumerate(sys.argv):
        if arg == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
            break
    main(limit_stores=limit)
