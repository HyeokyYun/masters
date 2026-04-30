"""
논문 보강: Event Study — new_customer_ratio 기반
────────────────────────────────────────────────────────────────────
weekly.parquet의 customer, customer_new를 사용하여 신규고객비율 기반 Event Study 수행.
(기존 4주 매출성장률 대리지표의 동어반복 이슈 해소)

DUY vs DDZ 그룹: 변곡점(t=0) 전후 신규 고객 유입 추이 비교

실행: python thesis_supplement/run_event_study_new_customer.py
출력: thesis_supplement/outputs/
────────────────────────────────────────────────────────────────────
"""
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from pathlib import Path
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "thesis_supplement" / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

EVENT_GROUPS = ["DUY", "DDZ"]
WEEKS_BEFORE = 12
WEEKS_AFTER = 12


def load_final_code():
    """final_code + inflection_week 로드 (inflection_week = day_after1, 전역 주차)"""
    for p in [
        ROOT / "260204_gem" / "outputs" / "tables" / "final_code_by_store_260121_outlier_removal.csv",
        ROOT / "260224" / "03_inflection_udx" / "final_code_by_store_260121_outlier_removal.csv",
    ]:
        if p.exists():
            df = pd.read_csv(p)
            df["public_id"] = df["public_id"].astype(str)
            return df[["public_id", "inflection_week", "final_code"]].dropna()
    raise FileNotFoundError("final_code not found. Run 260204_gem first.")


def build_weekly_with_weeks(weekly_path, meta_path):
    """
    weekly.parquet + meta → weeks_since_open 계산
    customer_new / customer → new_customer_ratio
    Returns: (weekly_df, min_date)
    """
    weekly = pd.read_parquet(weekly_path)
    weekly["public_id"] = weekly["public_id"].astype(str)
    weekly["date_id"] = pd.to_datetime(weekly["date_id"])
    min_date = weekly["date_id"].min()

    meta = pd.read_csv(meta_path)
    meta["public_id"] = meta["public_id"].astype(str)
    meta["open_date"] = pd.to_datetime(meta["open_month"].astype(str), format="%Y-%m", errors="coerce")
    weekly = weekly.merge(meta[["public_id", "open_date"]], on="public_id", how="left")
    weekly["weeks_since_open"] = ((weekly["date_id"] - weekly["open_date"]).dt.days // 7).clip(lower=0)

    if "customer_new" in weekly.columns and "customer" in weekly.columns:
        denom = weekly["customer"].replace(0, np.nan)
        weekly["new_customer_ratio"] = weekly["customer_new"] / denom
        weekly = weekly.dropna(subset=["new_customer_ratio"])
    else:
        raise ValueError("weekly.parquet needs customer_new and customer columns.")

    return weekly[["public_id", "weeks_since_open", "new_customer_ratio"]], min_date


def main():
    print("=" * 60)
    print("논문 보강: Event Study (new_customer_ratio 기반)")
    print("=" * 60)

    # 1) final_code
    inf = load_final_code()
    inf = inf[inf["final_code"].isin(EVENT_GROUPS)]
    print(f"Stores (DUY+DDZ): {len(inf)} | DUY={(inf['final_code']=='DUY').sum()} | DDZ={(inf['final_code']=='DDZ').sum()}")

    # 2) weekly + new_customer_ratio
    weekly_path = ROOT / "original_data" / "weekly.parquet"
    if not weekly_path.exists():
        weekly_path = ROOT / "original_data" / "weekly_reduced.parquet"
    if not weekly_path.exists():
        print("ERROR: weekly.parquet or weekly_reduced.parquet not found.")
        return

    meta_path = ROOT / "original_data" / "meta.csv"
    if not meta_path.exists():
        print("ERROR: meta.csv not found.")
        return

    weekly, min_date = build_weekly_with_weeks(weekly_path, meta_path)
    print(f"Weekly with new_customer_ratio: {len(weekly):,} rows")

    # 3) merge: inflection_week는 day_after1(전역주차). weeks_since_open으로 변환.
    # date_at_inflection = min_date + (inflection_week-1)*7
    # inflection_weeks_since_open = (date_at_inflection - open_date).days // 7
    meta = pd.read_csv(meta_path)
    meta["public_id"] = meta["public_id"].astype(str)
    meta["open_date"] = pd.to_datetime(meta["open_month"].astype(str), format="%Y-%m", errors="coerce")
    inf = inf.merge(meta[["public_id", "open_date"]], on="public_id", how="inner")
    inf["inflection_date"] = min_date + pd.to_timedelta((inf["inflection_week"].astype(int) - 1) * 7, unit="D")
    inf["inflection_weeks_since_open"] = ((inf["inflection_date"] - inf["open_date"]).dt.days // 7).clip(lower=0)
    merge_df = weekly.merge(inf[["public_id", "inflection_weeks_since_open", "final_code"]], on="public_id", how="inner")
    merge_df["event_time"] = merge_df["weeks_since_open"] - merge_df["inflection_weeks_since_open"].astype(int)
    merge_df = merge_df[
        (merge_df["event_time"] >= -WEEKS_BEFORE) &
        (merge_df["event_time"] <= WEEKS_AFTER)
    ]
    print(f"Event window [-{WEEKS_BEFORE}, +{WEEKS_AFTER}]: {len(merge_df):,} rows")

    # 4) 집계
    agg = merge_df.groupby(["event_time", "final_code"])["new_customer_ratio"].agg(
        ["mean", "std", "count"]
    ).reset_index()
    agg["se"] = agg["std"] / np.sqrt(agg["count"].clip(1))

    # 5) 시각화 (matplotlib 있으면)
    if HAS_MATPLOTLIB:
        fig, ax = plt.subplots(1, 1, figsize=(10, 5))
        for code in EVENT_GROUPS:
            sub = agg[agg["final_code"] == code].sort_values("event_time")
            if len(sub) == 0:
                continue
            ax.plot(sub["event_time"], sub["mean"], "o-", markersize=4, label=code)
            ax.fill_between(
                sub["event_time"],
                sub["mean"] - 1.96 * sub["se"],
                sub["mean"] + 1.96 * sub["se"],
                alpha=0.2,
            )
        ax.axvline(0, color="gray", linestyle="--", label="변곡점 (t=0)")
        ax.set_xlabel("Event time (변곡점 기준 주차)")
        ax.set_ylabel("신규 고객 비율 (new_customer_ratio)")
        ax.set_title("Event Study: DUY vs DDZ — 신규 고객 유입 추이 (동어반복 없는 지표)")
        ax.legend()
        ax.grid(True, alpha=0.3)
        out_fig = OUT_DIR / "event_study_new_customer_ratio.png"
        fig.savefig(out_fig, bbox_inches="tight", dpi=150)
        plt.close()
        print(f"Saved: {out_fig}")
    else:
        print("(matplotlib 없음 — 시각화 생략. pip install matplotlib)")

    # 6) CSV 저장
    agg.to_csv(OUT_DIR / "event_study_new_customer_means.csv", index=False, encoding="utf-8-sig")
    print(f"Saved: {OUT_DIR / 'event_study_new_customer_means.csv'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
