"""
Step 1: 매출 변동성 재정의 — 추세(선형·2차) 대비 잔차 기준 CV

기존 cv_sales_card = std/mean 은 성장 추세가 있을 때 변동성이 과대 해석될 수 있음.
각 점포별 주간 sales_card에 선형·2차 추세를 적합한 뒤 잔차 표준편차 / 평균(|매출|)으로 정의.

Run from 26-1: python 260320_cur/run_01_trend_residual_cv.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime

from config import WEEKLY_PARQUET, DF_MULTINOM, DF_MULTINOM_FALLBACK, OUT_DIR, LOG_DIR, MIN_WEEKS_FOR_TREND


def _resid_cv(y: np.ndarray, yhat: np.ndarray) -> float:
    y = np.asarray(y, dtype=float)
    resid = y - yhat
    m = np.nanmean(np.abs(y))
    if m <= 0 or not np.isfinite(m):
        return np.nan
    return float(np.nanstd(resid) / m)


def per_store_trend_cv(g: pd.DataFrame) -> pd.Series:
    if "day_after1" in g.columns:
        g = g.sort_values("day_after1")
    elif "date_id" in g.columns:
        g = g.sort_values("date_id")
    if "sales_card" not in g.columns:
        return pd.Series({"cv_resid_linear": np.nan, "cv_resid_poly2": np.nan, "n_weeks_used": 0})

    y = g["sales_card"].astype(float).values
    mask = np.isfinite(y) & (y >= 0)
    y = y[mask]
    n = len(y)
    if n < MIN_WEEKS_FOR_TREND:
        return pd.Series({"cv_resid_linear": np.nan, "cv_resid_poly2": np.nan, "n_weeks_used": n})

    x = np.arange(n, dtype=float)
    try:
        coef1 = np.polyfit(x, y, 1)
        yhat1 = np.polyval(coef1, x)
        cv1 = _resid_cv(y, yhat1)
    except Exception:
        cv1 = np.nan
    try:
        coef2 = np.polyfit(x, y, 2)
        yhat2 = np.polyval(coef2, x)
        cv2 = _resid_cv(y, yhat2)
    except Exception:
        cv2 = np.nan

    return pd.Series({"cv_resid_linear": cv1, "cv_resid_poly2": cv2, "n_weeks_used": n})


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "run_01_trend_residual_cv.log"

    def log(msg: str):
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    df_path = DF_MULTINOM if DF_MULTINOM.exists() else DF_MULTINOM_FALLBACK
    if not df_path.exists():
        log(f"ERROR: No merged file at {df_path}")
        return
    if not WEEKLY_PARQUET.exists():
        log(f"ERROR: {WEEKLY_PARQUET} not found")
        return

    ids = pd.read_csv(df_path, usecols=["public_id"])["public_id"].unique()
    log(f"Stores to process: {len(ids)}")

    log("Loading weekly parquet ...")
    weekly = pd.read_parquet(WEEKLY_PARQUET)
    if "day_after1" not in weekly.columns and "date_id" in weekly.columns:
        weekly["date_id"] = pd.to_datetime(weekly["date_id"])
        mn = weekly["date_id"].min()
        weekly["day_after1"] = ((weekly["date_id"] - mn).dt.days // 7) + 1

    weekly = weekly[weekly["public_id"].isin(ids)]
    log(f"Weekly rows after filter: {len(weekly)}")

    log("Computing per-store trend residual CV ...")
    rows = []
    for pid, g in weekly.groupby("public_id"):
        s = per_store_trend_cv(g)
        s["public_id"] = pid
        rows.append(s)
    feat = pd.DataFrame(rows)

    out_path = OUT_DIR / "store_trend_residual_cv.csv"
    feat.to_csv(out_path, index=False, encoding="utf-8-sig")
    log(f"Saved {out_path} ({len(feat)} rows)")
    log("Done.")


if __name__ == "__main__":
    main()
