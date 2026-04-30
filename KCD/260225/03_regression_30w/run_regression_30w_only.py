"""
260225 Step 3: 회귀 2가지 설계 — (2) 첫 30주만 사용

목적: "초기 30주 변수가 유의하면, 초기 30주가 성공 예측" 주장 가능.
     주간 데이터가 있으면 첫 30주 매출 기반 피처(early_avg, early_slope, early_cv) 계산 후 Multinomial Logit.

Run from 26-1: python 260225/03_regression_30w/run_regression_30w_only.py
"""
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
from scipy.stats import linregress

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = ROOT / "260225" / "outputs" / "tables"
LOG_DIR = ROOT / "260225" / "outputs" / "logs"

DF_INPUT = ROOT / "260225" / "outputs" / "tables" / "df_for_multinomial_logit.csv"
WEEKLY_PARQUET = ROOT / "original_data" / "weekly_processed.parquet"
WEEKLY_FALLBACK = ROOT / "original_data" / "weekly.parquet"

try:
    import statsmodels.api as sm
    HAS_STATS = True
except ImportError:
    HAS_STATS = False


def calc_early_features(weekly_df, weeks=30, time_col="day_after1", sales_col="sales_card", id_col="public_id"):
    """첫 N주 매출로 피처 계산."""
    cols = set(weekly_df.columns)
    tw = time_col if time_col in cols else "day_after1"
    sid = id_col if id_col in cols else "public_id"
    sv = sales_col if sales_col in cols else "sales_card"
    early = weekly_df[weekly_df[tw].between(1, weeks)].copy()
    early = early.sort_values([sid, tw])
    rows = []
    for pid, g in early.groupby(sid):
        sales = g[sv].values.astype(float)
        if len(sales) < 2:
            continue
        avg = np.mean(sales)
        cv = np.std(sales) / (np.mean(sales) + 1e-8)
        slope, _, _, _, _ = linregress(np.arange(len(sales)), sales)
        rows.append({sid: pid, "early_avg": avg, "early_cv": cv, "early_slope": slope})
    return pd.DataFrame(rows)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "run_regression_30w.log"

    def log(msg: str):
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    log("=" * 60)
    log("Step 3: 회귀 — 첫 30주만 사용")
    log("=" * 60)

    if not DF_INPUT.exists():
        log(f"ERROR: Run Step 1 first. Not found {DF_INPUT}")
        return

    df = pd.read_csv(DF_INPUT)
    log(f"Loaded: {len(df)} rows")

    wp = WEEKLY_PARQUET if WEEKLY_PARQUET.exists() else WEEKLY_FALLBACK
    if wp.exists():
        try:
            df_weekly = pd.read_parquet(wp)
            log(f"Weekly: {len(df_weekly)} rows")
            df_early = calc_early_features(df_weekly, weeks=30)
            log(f"Early 30w features: {len(df_early)} stores")
            df_merge = df.merge(df_early, on="public_id", how="inner")
            df_merge = df_merge.dropna(subset=["early_avg", "early_cv", "early_slope", "outcome_4"])
            log(f"Merged: {len(df_merge)} rows")

            if HAS_STATS and len(df_merge) > 100:
                X = df_merge[["early_avg", "early_cv", "early_slope", "business_age_months"]].copy()
                X = sm.add_constant(X)
                y = pd.Categorical(df_merge["outcome_4"], categories=["Stable", "DUY", "DUX", "Decline"], ordered=False)
                model = sm.MNLogit(y, X)
                res = model.fit(disp=0, maxiter=500)
                res.summary2().tables[1].to_csv(OUT_DIR / "multinomial_logit_30w_coefficients.csv", encoding="utf-8-sig")
                log(f"Saved {OUT_DIR / 'multinomial_logit_30w_coefficients.csv'}")
            df_merge.to_csv(OUT_DIR / "df_30w_for_regression.csv", index=False, encoding="utf-8-sig")
        except Exception as e:
            log(f"Weekly regression failed: {e}")
    else:
        log("Weekly data 없음. df_base_features 전체 기간 변수 사용.")

    doc = """
# Step 3: 회귀 2가지 설계

## (1) 전체 데이터 회귀
- Step 2 Multinomial Logit과 동일
- X: 전체 기간 요약 변수 (new_customer_ratio, cv_sales_card, business_age_months 등)

## (2) 첫 30주만 사용 회귀
- X: early_avg, early_cv, early_slope, business_age_months
- 30주 변수가 유의하면 → "초기 30주가 성공 예측" 주장 가능
"""
    (OUT_DIR / "regression_30w_design.md").write_text(doc.strip(), encoding="utf-8")
    log(f"Saved {OUT_DIR / 'regression_30w_design.md'}")
    log("Step 3 완료.")


if __name__ == "__main__":
    main()
