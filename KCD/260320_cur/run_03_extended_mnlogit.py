"""
Step 3: 확장 다항 로짓 — 추세 잔차 CV, 동 밀도, 업종×밀도 상호작용, 대표 연령(선택)

기준 카테고리: Stable, Growth, Decline 각각 (260301과 동일)

Run from 26-1: python 260320_cur/run_03_extended_mnlogit.py
"""
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

from config import OUT_DIR, LOG_DIR, CATEGORIES

try:
    import statsmodels.api as sm
    HAS_STATS = True
except ImportError:
    HAS_STATS = False

EXTENDED_CSV = Path(__file__).resolve().parent / "outputs" / "tables" / "df_extended_for_regression.csv"

# 변동성 변수: 'auto' → cv_resid_linear 우선, 없으면 cv_sales_card
VOLATILITY_MODE = "auto"

# 상호작용: 업종 더미 × 해당 동 업종 밀도
USE_DENSITY_INTERACTIONS = True

# 대표 연령 포함 (결측 많으면 자동 스킵)
USE_OWNER_AGE = True
OWNER_AGE_MIN_NONNULL_PCT = 0.15


def _relabel_summary(text: str, ref_name: str) -> str:
    ordered = [c for c in CATEGORIES if c != ref_name]
    for code, name in enumerate(ordered, start=1):
        text = text.replace(f"y={code}", f"y={name}")
    return text


def _pick_volatility_col(df: pd.DataFrame) -> str:
    if VOLATILITY_MODE == "cv_sales_card":
        return "cv_sales_card"
    if VOLATILITY_MODE == "cv_resid_linear" and "cv_resid_linear" in df.columns:
        return "cv_resid_linear"
    if VOLATILITY_MODE == "cv_resid_poly2" and "cv_resid_poly2" in df.columns:
        return "cv_resid_poly2"
    if VOLATILITY_MODE == "auto":
        if "cv_resid_linear" in df.columns and df["cv_resid_linear"].notna().sum() > 1000:
            return "cv_resid_linear"
        if "cv_resid_poly2" in df.columns and df["cv_resid_poly2"].notna().sum() > 1000:
            return "cv_resid_poly2"
    return "cv_sales_card"


def build_design_matrix(df: pd.DataFrame, vol_col: str):
    num_vars = ["business_age_months", "new_customer_ratio", vol_col]
    num_vars = [c for c in num_vars if c in df.columns]

    if USE_OWNER_AGE and "owner_age_numeric" in df.columns:
        nn = df["owner_age_numeric"].notna().mean()
        if nn >= OWNER_AGE_MIN_NONNULL_PCT:
            num_vars.append("owner_age_numeric")

    df_work = df.dropna(subset=[c for c in num_vars if c in df.columns] + ["outcome_3"]).copy()

    X = df_work[num_vars].copy()

    if "depth_2" in df_work.columns:
        top5 = df_work["depth_2"].value_counts().head(5).index.tolist()
        for d in top5[1:]:
            X[f"depth_{d}"] = (df_work["depth_2"] == d).astype(int)
            if USE_DENSITY_INTERACTIONS and f"dens_{d}" in df_work.columns:
                dens = df_work[f"dens_{d}"].fillna(0).astype(float)
                X[f"ix_{d}_x_dens"] = X[f"depth_{d}"] * dens

    X = sm.add_constant(X)
    return df_work, X


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "run_03_extended_mnlogit.log"

    def log(msg: str):
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    if not EXTENDED_CSV.exists():
        log(f"ERROR: Run run_02 first. Missing {EXTENDED_CSV}")
        return
    if not HAS_STATS:
        log("ERROR: pip install statsmodels")
        return

    df = pd.read_csv(EXTENDED_CSV)
    if "outcome_3" not in df.columns:
        log("ERROR: outcome_3 column required")
        return

    vol_col = _pick_volatility_col(df)
    log(f"Volatility column used: {vol_col}")

    df_work, X = build_design_matrix(df, vol_col)
    log(f"Regression sample: {len(df_work)} rows, {X.shape[1]} regressors (incl. const)")

    y_cat = df_work["outcome_3"]

    for ref in CATEGORIES:
        others = [c for c in CATEGORIES if c != ref]
        cat_order = [ref] + others
        cat = pd.Categorical(y_cat, categories=cat_order)
        y = cat.codes

        try:
            model = sm.MNLogit(y, X)
            res = model.fit(disp=0, maxiter=500)
            summary_text = _relabel_summary(res.summary().as_text(), ref)
            header = (
                f"260320_cur 확장 모형 | 기준(Reference): {ref}\n"
                f"변동성 변수: {vol_col} | 상호작용: {USE_DENSITY_INTERACTIONS}\n"
                f"{'=' * 78}\n"
            )
            fname = f"multinomial_logit_ext_ref_{ref}.txt"
            with open(OUT_DIR / fname, "w", encoding="utf-8") as f:
                f.write(header + summary_text)
            res.summary2().tables[1].to_csv(
                OUT_DIR / f"multinomial_logit_ext_coefficients_ref_{ref}.csv",
                encoding="utf-8-sig",
            )
            log(f"OK → {fname}")
        except Exception as e:
            log(f"FAIL ref={ref}: {e}")

    log("Done.")


if __name__ == "__main__":
    main()
