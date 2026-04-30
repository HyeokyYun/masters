"""
Step 02 ─ 업장별 피처 추출
  ● 추세 피처: 전반/후반/전체/tail 기울기, R²
  ● 변동성:   CV, MDD
  ● 고객:     신규고객비율(nc_rate)
  ● 영업특성:  배달비율(log1p), 오전비율, 주말비율
  ● STL 유래: trend_slope, seasonal_strength, noise_ratio
"""
import numpy as np
import pandas as pd
from scipy import stats
from src import config as cfg


def _safe_linregress(x, y):
    if len(x) < 3 or np.std(y) < 1e-12:
        return 0.0, 0.0, 0.0
    s, _, r, _, _ = stats.linregress(x.astype(float), y.astype(float))
    return float(s), float(r), float(r ** 2)


def extract_features(ts: pd.DataFrame) -> pd.DataFrame:
    """ts → 업장 1행 피처 DataFrame. columns ⊃ public_id."""
    records = []
    groups = ts.groupby("public_id")
    total = len(groups)

    for i, (pid, g) in enumerate(groups):
        if (i + 1) % 5000 == 0:
            print(f"  [{i+1:,}/{total:,}]")

        g = (g.sort_values("weeks_since_open")
              .drop_duplicates("weeks_since_open")
              .reset_index(drop=True))
        g = g[g["weeks_since_open"] < cfg.MAX_WEEKS]

        y_raw = g["sales_card"].fillna(0).values.astype(float)
        y_mm  = g["sales_card_mm"].fillna(0).values.astype(float)
        if len(y_raw) < 30 or not np.isfinite(y_mm).all():
            continue

        n = len(y_mm)
        h = n // 2
        t = np.arange(n, dtype=float)

        # ── 기울기 (MinMax 기반) ─────────────────────
        s_e, _, r2_e = _safe_linregress(t[:h], y_mm[:h])
        s_l, _, r2_l = _safe_linregress(t[h:] - h, y_mm[h:])
        s_a, r_all, r2_a = _safe_linregress(t, y_mm)

        tail_n = max(8, n // 5)
        s_tail, _, _ = _safe_linregress(np.arange(tail_n, dtype=float), y_mm[-tail_n:])

        # ── 변동성·손실 ──────────────────────────────
        cv  = min(y_raw.std() / (y_raw.mean() + 1e-9), 2.0)
        cum = np.maximum.accumulate(y_mm)
        mdd = ((cum - y_mm) / (cum + 1e-9)).max()

        # ── 고객 피처 ────────────────────────────────
        nc_rate = np.nan
        if "customer_new" in g.columns and "customer" in g.columns:
            denom = g["customer"].replace(0, np.nan) + 1
            nc = g["customer_new"] / denom
            nc_rate = float(nc.mean()) if nc.notna().any() else np.nan

        # ── 배달·시간대 ──────────────────────────────
        del_ratio_log = np.nan
        if "sales_delivery" in g.columns:
            total_sales = y_raw.sum()
            if total_sales > 0:
                del_ratio_log = float(np.log1p(
                    g["sales_delivery"].fillna(0).sum() / total_sales))

        before_noon = float(g["before_noon_sales"].mean()) if "before_noon_sales" in g.columns else np.nan
        weekend     = float(g["weekend_sales"].mean())     if "weekend_sales"     in g.columns else np.nan

        # ── STL 유래 피처 ─────────────────────────────
        trend_slope = 0.0
        seasonal_strength = 0.0
        noise_ratio = 0.0
        if "trend" in g.columns and "trend_mm" in g.columns:
            tr = g["trend_mm"].fillna(0).values
            trend_slope, _, _ = _safe_linregress(t, tr)
        if "seasonal" in g.columns:
            var_total  = np.var(y_raw) + 1e-9
            var_season = np.var(g["seasonal"].values)
            var_resid  = np.var(g["resid"].values) if "resid" in g.columns else 0
            seasonal_strength = float(max(0, 1 - var_resid / var_total))
            noise_ratio = float(var_resid / var_total)

        # ── 카테고리 ──────────────────────────────────
        category = g["category"].iloc[0] if "category" in g.columns else "기타"

        records.append({
            "public_id":        pid,
            "category":         category,
            "slope_early_mm":   s_e,
            "slope_late_mm":    s_l,
            "slope_all_mm":     s_a,
            "slope_tail_mm":    s_tail,
            "trend_slope":      trend_slope,
            "r2":               r2_a,
            "r2_early":         r2_e,
            "low_r2":           int(r2_a < 0.1),
            "cv":               cv,
            "mdd":              mdd,
            "nc_rate":          nc_rate,
            "del_ratio_log":    del_ratio_log,
            "before_noon":      before_noon,
            "weekend":          weekend,
            "seasonal_strength": seasonal_strength,
            "noise_ratio":      noise_ratio,
            "n_weeks":          n,
        })

    feat = pd.DataFrame(records)
    out_path = cfg.TABLE_DIR / "store_features.csv"
    feat.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[Step02] {len(feat):,} 매장 피처 추출 → {out_path.name}")
    return feat
