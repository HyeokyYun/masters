"""Phase 2.4 — Urban economics auxiliary analyses (C2/C3).

C2. Industry × Region G/S/D 비율 매트릭스
    - kostat_class × sigungu cell의 G/S/D 비율
    - cell이 작은 경우(< 30 store) 제외
    - 어떤 (업종, 지역) 조합이 상승률이 높은가

C3. 업력 cohort × 신규 유입 효과
    - tenure_months를 4 분위로 나누어 cohort 정의
    - 각 cohort 안에서 nc_slope (신규 유입 변화율)와 outcome_3 관계
    - logistic regression coefficient (nc_slope → P(Growth))를 cohort별로 fit

Outputs:
  outputs/tables/industry_region_growth_rate.csv
  outputs/tables/age_cohort_nc_effect.csv
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg  # noqa: E402
import utils_panel as up  # noqa: E402

PANELS = [
    ("sy2021_sm01_w3m_off1", "Jan-Mar 2021 → Jan-Mar 2022"),
    ("sy2021_sm05_w3m_off1", "May-Jul 2021 → May-Jul 2022"),
    ("sy2021_sm09_w3m_off1", "Sep-Nov 2021 → Sep-Nov 2022"),
    ("sy2022_sm01_w3m_off1", "Jan-Mar 2022 → Jan-Mar 2023"),
    ("sy2022_sm05_w3m_off1", "May-Jul 2022 → May-Jul 2023"),
    ("sy2021_sm01_w7m_off1", "Jan-Jul 2021 → Jan-Jul 2022 (7m)"),
    ("sy2022_sm01_w7m_off1", "Jan-Jul 2022 → Jan-Jul 2023 (7m)"),
]

CLASSES = cfg.OUTCOME_CLASSES
MIN_CELL = 30


def _build_combined() -> pd.DataFrame:
    meta = up.load_meta()[["public_id", "sigungu", "kostat_class"]]
    meta["public_id"] = meta["public_id"].astype(str)
    pieces = []
    for combo_id, desc in PANELS:
        l_path = up.label_path(combo_id)
        f_path = up.feature_path(combo_id)
        m_path = cfg.TABLE_DIR / "features_meta" / f"features_meta_{combo_id}.parquet"
        if not (l_path.exists() and f_path.exists() and m_path.exists()):
            continue
        labels = pd.read_parquet(l_path)[["public_id", "outcome_3"]]
        feats = pd.read_parquet(f_path)
        feats_keep = [c for c in ["public_id", "nc_slope", "nc_mean",
                                     "nc_first_q", "nc_last_q", "nc_delta"] if c in feats.columns]
        feats = feats[feats_keep]
        m = pd.read_parquet(m_path)[["public_id", "tenure_months"]]
        for d in (labels, feats, m):
            d["public_id"] = d["public_id"].astype(str)
        df = labels.merge(feats, on="public_id", how="inner") \
                    .merge(m, on="public_id", how="left") \
                    .merge(meta, on="public_id", how="left")
        df["combo_id"] = combo_id
        pieces.append(df)
    if not pieces:
        return pd.DataFrame()
    return pd.concat(pieces, ignore_index=True)


def _industry_region(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["outcome_3"].isin(CLASSES)].copy()
    grp = df.groupby(["combo_id", "kostat_class", "sigungu", "outcome_3"]).size().unstack(fill_value=0)
    for c in CLASSES:
        if c not in grp.columns:
            grp[c] = 0
    grp["n"] = grp[CLASSES].sum(axis=1)
    grp = grp[grp["n"] >= MIN_CELL]
    for c in CLASSES:
        grp[f"ratio_{c}"] = grp[c] / grp["n"]
    grp = grp.reset_index()
    return grp


def _age_cohort_nc(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["outcome_3"].isin(CLASSES)].copy()
    df = df.dropna(subset=["tenure_months", "nc_slope"])
    if df.empty:
        return pd.DataFrame()
    # Cohort by tenure quartiles per combo (so the cohort definition is panel-relative)
    rows = []
    for combo_id, sub in df.groupby("combo_id"):
        if len(sub) < 200:
            continue
        try:
            sub["cohort"] = pd.qcut(sub["tenure_months"], 4, labels=["Q1_short", "Q2", "Q3", "Q4_long"])
        except ValueError:
            continue
        for cohort, c_sub in sub.groupby("cohort"):
            if len(c_sub) < 100:
                continue
            X = c_sub[["nc_slope"]].fillna(0).to_numpy()
            y = (c_sub["outcome_3"] == "Growth").astype(int).to_numpy()
            if y.sum() < 10 or y.sum() > len(y) - 10:
                continue
            try:
                lr = LogisticRegression(max_iter=200)
                lr.fit(X, y)
                coef = float(lr.coef_[0, 0])
                intercept = float(lr.intercept_[0])
            except Exception:
                continue
            rows.append({
                "combo_id": combo_id, "cohort": str(cohort),
                "n": int(len(c_sub)),
                "tenure_months_p50": float(c_sub["tenure_months"].median()),
                "growth_rate": float(y.mean()),
                "nc_slope_mean": float(X.mean()),
                "logit_coef_nc_slope": coef,
                "logit_intercept": intercept,
            })
    return pd.DataFrame(rows)


def main() -> None:
    df = _build_combined()
    if df.empty:
        print("[ue] no data; abort")
        return
    print(f"[ue] combined rows={len(df):,} stores")

    ir = _industry_region(df)
    p1 = cfg.TABLE_DIR / "industry_region_growth_rate.csv"
    ir.to_csv(p1, index=False, encoding="utf-8-sig")
    print(f"[ue] saved {p1} (rows={len(ir)})")
    if not ir.empty:
        # top 10 (kostat × sigungu) by growth rate (averaged across panels)
        agg = (ir.groupby(["kostat_class", "sigungu"])
                  .agg(growth=("ratio_Growth", "mean"),
                       decline=("ratio_Decline", "mean"),
                       n_total=("n", "sum"),
                       n_panels=("combo_id", "nunique"))
                  .reset_index().sort_values("growth", ascending=False))
        top_path = cfg.TABLE_DIR / "industry_region_top.csv"
        agg.head(50).to_csv(top_path, index=False, encoding="utf-8-sig")
        print(f"[ue] top growth (industry × region):\n{agg.head(10).to_string(index=False)}")

    nc = _age_cohort_nc(df)
    p2 = cfg.TABLE_DIR / "age_cohort_nc_effect.csv"
    nc.to_csv(p2, index=False, encoding="utf-8-sig")
    print(f"[ue] saved {p2} (rows={len(nc)})")
    if not nc.empty:
        agg2 = (nc.groupby("cohort")
                  .agg(coef=("logit_coef_nc_slope", "mean"),
                       coef_std=("logit_coef_nc_slope", "std"),
                       growth_rate=("growth_rate", "mean"),
                       n_panels=("combo_id", "nunique"))
                  .reset_index())
        print(f"[ue] cohort-mean nc_slope coef:\n{agg2.to_string(index=False)}")


if __name__ == "__main__":
    main()
