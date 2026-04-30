"""
260301 Step 3-4: Summary Statistics + Multinomial Logit

Step 3: outcome_3(Growth/Stable/Decline)별 요약 통계
Step 4: Multinomial Logit — 기준을 Stable / Growth / Decline 각각으로 3회 추정
Run from 26-1: python 260301/04_summary_regression/run_summary_and_multinomial.py
"""
from pathlib import Path
import pandas as pd
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = ROOT / "260301" / "outputs" / "tables"
LOG_DIR = ROOT / "260301" / "outputs" / "logs"

DF_INPUT = ROOT / "260301" / "outputs" / "tables" / "df_for_multinomial_logit.csv"

try:
    import statsmodels.api as sm
    HAS_STATS = True
except ImportError:
    HAS_STATS = False

CATEGORIES = ["Stable", "Growth", "Decline"]
LABEL_MAP = {0: CATEGORIES[0], 1: CATEGORIES[1], 2: CATEGORIES[2]}


def _relabel_summary(text: str, ref_name: str) -> str:
    """y=0/1/2 숫자 라벨을 실제 카테고리 이름으로 치환."""
    ordered = [c for c in CATEGORIES if c != ref_name]
    for code, name in enumerate(ordered, start=1):
        text = text.replace(f"y={code}", f"y={name}")
    return text


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
    log("Step 3-4: Summary Statistics + Multinomial Logit")
    log("=" * 60)

    if not DF_INPUT.exists():
        log(f"ERROR: Run Step 2 first. Not found {DF_INPUT}")
        return

    df = pd.read_csv(DF_INPUT)
    log(f"Loaded: {len(df)} rows")

    # Step 3: Summary Statistics
    num_cols = ["business_age_months", "new_customer_ratio", "cv_sales_card", "growth_rate"]
    num_cols = [c for c in num_cols if c in df.columns]
    summary = df.groupby("outcome_3")[num_cols].agg(["mean", "std", "count"])
    summary.to_csv(OUT_DIR / "outcome3_summary_key_vars.csv", encoding="utf-8-sig")
    log(f"Saved outcome3_summary_key_vars.csv")
    log(f"Counts: {df['outcome_3'].value_counts().to_dict()}")

    # Step 4: Multinomial Logit
    if not HAS_STATS:
        log("SKIP Multinomial Logit: statsmodels not installed")
        return

    num_vars = ["business_age_months", "new_customer_ratio", "cv_sales_card"]
    num_vars = [c for c in num_vars if c in df.columns]
    df_clean = df.dropna(subset=num_vars + ["outcome_3"])

    X = df_clean[num_vars].copy()
    if "depth_2" in df_clean.columns:
        top5 = df_clean["depth_2"].value_counts().head(5).index.tolist()
        for d in top5[1:]:
            X[f"depth_{d}"] = (df_clean["depth_2"] == d).astype(int)
    X = sm.add_constant(X)

    for ref in CATEGORIES:
        others = [c for c in CATEGORIES if c != ref]
        cat_order = [ref] + others
        cat = pd.Categorical(df_clean["outcome_3"], categories=cat_order)
        y = cat.codes

        try:
            model = sm.MNLogit(y, X)
            res = model.fit(disp=0, maxiter=500)

            summary_text = _relabel_summary(res.summary().as_text(), ref)
            header = f"기준(Reference): {ref}\n{'=' * 78}\n"
            fname_txt = f"multinomial_logit_ref_{ref}.txt"
            with open(OUT_DIR / fname_txt, "w", encoding="utf-8") as f:
                f.write(header + summary_text)

            fname_csv = f"multinomial_logit_coefficients_ref_{ref}.csv"
            res.summary2().tables[1].to_csv(OUT_DIR / fname_csv, encoding="utf-8-sig")

            log(f"Multinomial Logit (ref={ref}) 완료 → {fname_txt}, {fname_csv}")
        except Exception as e:
            log(f"Multinomial Logit (ref={ref}) 실패: {e}")

    log("Step 3-4 완료.")


if __name__ == "__main__":
    main()
