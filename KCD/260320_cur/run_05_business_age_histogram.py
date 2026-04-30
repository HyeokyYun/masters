"""
업력(business_age_months) 분포 히스토그램 — 개별미팅에서 요청한 시각화

Run from 26-1: python 260320_cur/run_05_business_age_histogram.py
"""
from pathlib import Path
import pandas as pd

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_PLT = True
except ImportError:
    HAS_PLT = False

from config import DF_MULTINOM, DF_MULTINOM_FALLBACK, OUT_DIR

FIG_DIR = Path(__file__).resolve().parent / "outputs" / "figures"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    p = DF_MULTINOM if DF_MULTINOM.exists() else DF_MULTINOM_FALLBACK
    if not p.exists():
        print("No input csv")
        return
    df = pd.read_csv(p, usecols=["business_age_months"])
    s = df["business_age_months"].dropna()

    summary = s.describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9])
    summary.to_csv(OUT_DIR / "business_age_months_summary.csv", encoding="utf-8-sig")
    print(summary)

    if not HAS_PLT:
        print("matplotlib not installed; skip figure")
        return

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(s.clip(0, 300), bins=60, color="steelblue", edgecolor="white")
    ax.set_xlabel("business_age_months")
    ax.set_ylabel("count")
    ax.set_title("Distribution of business age (months)")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "business_age_histogram.png", dpi=150)
    print(f"Saved {FIG_DIR / 'business_age_histogram.png'}")


if __name__ == "__main__":
    main()
