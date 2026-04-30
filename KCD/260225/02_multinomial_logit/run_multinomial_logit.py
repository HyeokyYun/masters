"""
260225 Step 2: Multinomial Logit (다항 로지스틱 회귀)

목적: outcome_4(DUX/DUY/Stable/Decline)를 Y로, 요약 통계 변수를 X로 회귀.
     기준(Baseline): Stable (평범) — "어떤 변수가 DUX/DUY로 가는지, 망하는지" 규명.

Y: outcome_4 (DUX, DUY, Stable, Decline)
X: business_age_months, new_customer_ratio, cv_sales_card, depth_2 더미 등

Run from 26-1: python 260225/02_multinomial_logit/run_multinomial_logit.py
"""
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = ROOT / "260225" / "outputs" / "tables"
LOG_DIR = ROOT / "260225" / "outputs" / "logs"

DF_INPUT = ROOT / "260225" / "outputs" / "tables" / "df_for_multinomial_logit.csv"

try:
    import statsmodels.api as sm
    from statsmodels.miscmodels.ordinal_model import OrderedModel
    HAS_STATS = True
except ImportError:
    HAS_STATS = False


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "run_multinomial_logit.log"

    def log(msg: str):
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    log("=" * 60)
    log("Step 2: Multinomial Logit (outcome_4)")
    log("=" * 60)

    if not DF_INPUT.exists():
        log(f"ERROR: Run Step 1 first. Not found {DF_INPUT}")
        return

    df = pd.read_csv(DF_INPUT)
    log(f"Loaded: {len(df)} rows")

    # outcome_4 분포
    log(f"outcome_4: {df['outcome_4'].value_counts().to_dict()}")

    # DUX, DUY 샘플 수 확인 (교수님 피드백: 충분한지 확인)
    n_dux = (df["outcome_4"] == "DUX").sum()
    n_duy = (df["outcome_4"] == "DUY").sum()
    log(f"DUX={n_dux}, DUY={n_duy} — Multinomial Logit 가능 여부 확인")

    if not HAS_STATS:
        log("ERROR: statsmodels required. pip install statsmodels")
        return

    # X 변수: 수치형 + 업종 더미
    num_vars = ["business_age_months", "new_customer_ratio", "cv_sales_card"]
    num_vars = [c for c in num_vars if c in df.columns]
    df_clean = df.dropna(subset=num_vars + ["outcome_4"])
    log(f"After dropna: {len(df_clean)} rows")

    X_num = df_clean[num_vars].copy()
    # depth_2 더미 (상위 5개 업종만, 나머지 Other)
    if "depth_2" in df_clean.columns:
        top5 = df_clean["depth_2"].value_counts().head(5).index.tolist()
        for d in top5[1:]:  # 첫 번째 기준
            X_num[f"depth_{d}"] = (df_clean["depth_2"] == d).astype(int)
    X_num = sm.add_constant(X_num)
    # 기준(Baseline): Stable — MNLogit은 첫 번째 카테고리를 기준으로 함
    y = df_clean["outcome_4"].astype(str)
    # Stable을 첫 번째로 (기준)
    order = ["Stable", "DUY", "DUX", "Decline"]
    y_ordered = pd.Categorical(y, categories=order, ordered=False)

    try:
        model = sm.MNLogit(y_ordered, X_num)
        result = model.fit(disp=0, maxiter=500)
        log("Multinomial Logit 추정 완료.")

        # 계수표 저장
        coef_df = result.summary2().tables[1]
        coef_df.to_csv(OUT_DIR / "multinomial_logit_coefficients.csv", encoding="utf-8-sig")
        log(f"Saved {OUT_DIR / 'multinomial_logit_coefficients.csv'}")

        # Odds ratio (exp(coef))
        odds = np.exp(result.params)
        odds_df = pd.DataFrame(odds, columns=["Odds_Ratio"])
        odds_df.to_csv(OUT_DIR / "multinomial_logit_odds_ratios.csv", encoding="utf-8-sig")
        log(f"Saved {OUT_DIR / 'multinomial_logit_odds_ratios.csv'}")

        # 전체 요약 텍스트
        with open(OUT_DIR / "multinomial_logit_summary.txt", "w", encoding="utf-8") as f:
            f.write(result.summary().as_text())
        log(f"Saved {OUT_DIR / 'multinomial_logit_summary.txt'}")

    except Exception as e:
        log(f"Multinomial Logit 추정 실패: {e}")
        # 대안: Binary Logit (성공 vs 쇠퇴)
        log("대안: Binary Logit (성공=DUX+DUY vs 쇠퇴=Decline) 시도")
        df_bin = df_clean.copy()
        df_bin["success"] = df_bin["outcome_4"].isin(["DUX", "DUY"]).astype(int)
        y_bin = df_bin["success"]
        try:
            model_bin = sm.Logit(y_bin, X_num)
            res_bin = model_bin.fit(disp=0)
            res_bin.summary2().tables[1].to_csv(
                OUT_DIR / "binary_logit_coefficients.csv", encoding="utf-8-sig"
            )
            log("Binary Logit 저장 완료.")
        except Exception as e2:
            log(f"Binary Logit도 실패: {e2}")

    log("Step 2 완료.")


if __name__ == "__main__":
    main()
