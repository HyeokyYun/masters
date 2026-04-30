"""
260303 Step 2: Summary Statistics + Multinomial Logit

Y variable: life_cycle_category (rising, maintaining, declining).
Reference category: maintaining.
Run from 26-1: python 260303/02_regression/run_summary_and_multinomial.py
"""
from pathlib import Path
import pandas as pd
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = ROOT / "260303" / "outputs" / "tables"
LOG_DIR = ROOT / "260303" / "outputs" / "logs"

DF_INPUT = ROOT / "260303" / "outputs" / "tables" / "df_for_life_cycle_regression.csv"

try:
    import statsmodels.api as sm
    HAS_STATS = True
except ImportError:
    HAS_STATS = False


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "run_summary_and_multinomial.log"

    def log(msg: str):
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    log("=" * 60)
    log("260303 Step 2: Summary + Multinomial Logit (Y = life_cycle_category)")
    log("=" * 60)

    if not DF_INPUT.exists():
        log(f"ERROR: Run Step 1 first. Not found {DF_INPUT}")
        return

    df = pd.read_csv(DF_INPUT)
    log(f"Loaded: {len(df)} rows")
    log(f"life_cycle_category counts: {df['life_cycle_category'].value_counts().to_dict()}")

    # Summary statistics by life_cycle_category
    num_cols = ["business_age_months", "new_customer_ratio", "cv_sales_card", "growth_rate"]
    num_cols = [c for c in num_cols if c in df.columns]
    summary = df.groupby("life_cycle_category")[num_cols].agg(["mean", "std", "count"])
    summary.to_csv(OUT_DIR / "life_cycle_summary_key_vars.csv", encoding="utf-8-sig")
    log("Saved life_cycle_summary_key_vars.csv")

    # Multinomial Logit: baseline = maintaining
    if not HAS_STATS:
        log("SKIP Multinomial Logit: statsmodels not installed")
        return

    num_vars = ["business_age_months", "new_customer_ratio", "cv_sales_card"]
    num_vars = [c for c in num_vars if c in df.columns]
    df_clean = df.dropna(subset=num_vars + ["life_cycle_category"])

    X = df_clean[num_vars].copy()
    if "depth_2" in df_clean.columns:
        top5 = df_clean["depth_2"].value_counts().head(5).index.tolist()
        for d in top5[1:]:
            X[f"depth_{d}"] = (df_clean["depth_2"] == d).astype(int)
    X = sm.add_constant(X)

    # Categories: maintaining as reference (first in list for baseline)
    categories = ["maintaining", "rising", "declining"]
    y = pd.Categorical(
        df_clean["life_cycle_category"],
        categories=categories,
        ordered=False,
    )

    try:
        model = sm.MNLogit(y, X)
        res = model.fit(disp=0, maxiter=500)
        res.summary2().tables[1].to_csv(
            OUT_DIR / "multinomial_logit_life_cycle_coefficients.csv",
            encoding="utf-8-sig",
        )
        with open(OUT_DIR / "multinomial_logit_life_cycle_summary.txt", "w", encoding="utf-8") as f:
            f.write(res.summary().as_text())
        log("Multinomial Logit 완료 (baseline=maintaining).")
    except Exception as e:
        log(f"Multinomial Logit 실패: {e}")

    log("Step 2 완료.")


if __name__ == "__main__":
    main()
