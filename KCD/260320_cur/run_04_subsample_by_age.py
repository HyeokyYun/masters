"""
Step 4: 업력(business_age_months) 구간별 서브샘플 다항 로짓

개별미팅: 업력이 짧은 점포만 별도 표본으로 재추정해 '신규 창업' 관점 해석.

Run from 26-1: python 260320_cur/run_04_subsample_by_age.py
"""
from pathlib import Path
import pandas as pd
from datetime import datetime

from config import OUT_DIR, LOG_DIR, CATEGORIES

try:
    import statsmodels.api as sm
    HAS_STATS = True
except ImportError:
    HAS_STATS = False

EXTENDED_CSV = Path(__file__).resolve().parent / "outputs" / "tables" / "df_extended_for_regression.csv"

# 월 단위 업력 상한 (이하만 포함)
SUBSAMPLE_MAX_MONTHS = [None, 24, 12, 6]


def _relabel_summary(text: str, ref_name: str) -> str:
    ordered = [c for c in CATEGORIES if c != ref_name]
    for code, name in enumerate(ordered, start=1):
        text = text.replace(f"y={code}", f"y={name}")
    return text


def build_X(df, vol_col):
    num_vars = ["business_age_months", "new_customer_ratio", vol_col]
    num_vars = [c for c in num_vars if c in df.columns]
    df_work = df.dropna(subset=num_vars + ["outcome_3"]).copy()
    X = df_work[num_vars].copy()
    if "depth_2" in df_work.columns:
        top5 = df_work["depth_2"].value_counts().head(5).index.tolist()
        for d in top5[1:]:
            X[f"depth_{d}"] = (df_work["depth_2"] == d).astype(int)
            if f"dens_{d}" in df_work.columns:
                dens = df_work[f"dens_{d}"].fillna(0).astype(float)
                X[f"ix_{d}_x_dens"] = X[f"depth_{d}"] * dens
    X = sm.add_constant(X)
    return df_work, X


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "run_04_subsample_by_age.log"

    def log(msg: str):
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    if not EXTENDED_CSV.exists() or not HAS_STATS:
        log("ERROR: need df_extended + statsmodels")
        return

    df = pd.read_csv(EXTENDED_CSV)
    if "outcome_3" not in df.columns:
        log("ERROR: outcome_3 missing")
        return

    if "cv_resid_linear" in df.columns and df["cv_resid_linear"].notna().sum() > 500:
        vol_col = "cv_resid_linear"
    else:
        vol_col = "cv_sales_card"

    for max_m in SUBSAMPLE_MAX_MONTHS:
        tag = "all" if max_m is None else f"le{max_m}m"
        sub = df if max_m is None else df[df["business_age_months"] <= max_m]
        if len(sub) < 500:
            log(f"SKIP {tag}: n={len(sub)}")
            continue

        df_work, X = build_X(sub, vol_col)
        y_cat = df_work["outcome_3"]

        ref = "Stable"
        others = [c for c in CATEGORIES if c != ref]
        cat_order = [ref] + others
        y = pd.Categorical(y_cat, categories=cat_order).codes

        try:
            model = sm.MNLogit(y, X)
            res = model.fit(disp=0, maxiter=500)
            summary_text = _relabel_summary(res.summary().as_text(), ref)
            header = (
                f"서브샘플 업력: {tag} | n={len(df_work)} | vol={vol_col}\n"
                f"기준(Reference): {ref}\n{'=' * 78}\n"
            )
            fname = f"mnlogit_subsample_{tag}_ref_{ref}.txt"
            with open(OUT_DIR / fname, "w", encoding="utf-8") as f:
                f.write(header + summary_text)
            log(f"Saved {fname}")
        except Exception as e:
            log(f"FAIL {tag}: {e}")

    log("Done.")


if __name__ == "__main__":
    main()
