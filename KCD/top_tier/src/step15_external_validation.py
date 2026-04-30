"""Step 15 - External validation using Seoul public data.

External sources in thesis/data_external:
  1) LOCAL_PEOPLE_GU_2021/2022/2023.zip
  2) seoul_food_permits.csv
  3) Seoul commercial-district store/sales ZIP files

Outputs:
  outputs/tables/external_living_population_gu_monthly.csv
  outputs/tables/external_permits_gu_monthly.csv
  outputs/tables/external_validation_gu.csv
  outputs/tables/external_validation_correlations.csv
  outputs/tables/external_commercial_quarterly.csv
  outputs/tables/external_kcd_quarterly.csv
  outputs/tables/external_temporal_correlations.csv
  outputs/docs/step15_external_validation.log
  outputs/figures/fig17_external_gu_validation.png
  outputs/figures/fig18_external_temporal_validation.png
"""
from __future__ import annotations

import re
import sys
import unicodedata
import zipfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg  # noqa: E402

plt.rcParams.update(cfg.FIG_STYLE)


GU_CODE = {
    11110: "종로구", 11140: "중구", 11170: "용산구", 11200: "성동구",
    11215: "광진구", 11230: "동대문구", 11260: "중랑구", 11290: "성북구",
    11305: "강북구", 11320: "도봉구", 11350: "노원구", 11380: "은평구",
    11410: "서대문구", 11440: "마포구", 11470: "양천구", 11500: "강서구",
    11530: "구로구", 11545: "금천구", 11560: "영등포구", 11590: "동작구",
    11620: "관악구", 11650: "서초구", 11680: "강남구", 11710: "송파구",
    11740: "강동구",
}


def _open_csv_from_zip(path: Path, **kwargs) -> pd.DataFrame:
    with zipfile.ZipFile(path) as zf:
        name = [n for n in zf.namelist() if n.lower().endswith(".csv")][0]
        try:
            return pd.read_csv(zf.open(name), encoding="cp949", **kwargs)
        except UnicodeDecodeError:
            return pd.read_csv(zf.open(name), encoding="utf-8", **kwargs)


def load_living_population() -> pd.DataFrame:
    rows = []
    for year in [2021, 2022, 2023]:
        p = cfg.DATA_EXTERNAL_DIR / f"LOCAL_PEOPLE_GU_{year}.zip"
        df = _open_csv_from_zip(
            p,
            usecols=["기준일ID", "시간대구분", "자치구코드", "총생활인구수"],
            dtype={"기준일ID": str, "시간대구분": int, "자치구코드": int, "총생활인구수": float},
        )
        daily = df.groupby(["기준일ID", "자치구코드"], as_index=False)["총생활인구수"].mean()
        daily["date"] = pd.to_datetime(daily["기준일ID"], format="%Y%m%d")
        daily["year_month"] = daily["date"].dt.to_period("M").astype(str)
        daily["quarter"] = daily["date"].dt.to_period("Q").astype(str)
        daily["sigungu"] = daily["자치구코드"].map(GU_CODE)
        rows.append(daily.dropna(subset=["sigungu"]))
    lp = pd.concat(rows, ignore_index=True)
    monthly = (
        lp.groupby(["sigungu", "year_month"], as_index=False)["총생활인구수"]
        .mean()
        .rename(columns={"총생활인구수": "lp_mean"})
    )
    monthly.to_csv(cfg.TABLE_DIR / "external_living_population_gu_monthly.csv", index=False, encoding="utf-8-sig")
    return monthly


def load_permits() -> pd.DataFrame:
    permits = pd.read_csv(
        cfg.DATA_EXTERNAL_DIR / "seoul_food_permits.csv",
        encoding="cp949",
        encoding_errors="replace",
        usecols=["인허가일자", "영업상태명", "상세영업상태명", "폐업일자", "지번주소", "도로명주소"],
        dtype=str,
        low_memory=False,
    )

    def pick_addr(row):
        road = row.get("도로명주소")
        if isinstance(road, str) and road.strip():
            return road
        jibun = row.get("지번주소")
        return jibun if isinstance(jibun, str) else ""

    permits["addr"] = permits.apply(pick_addr, axis=1)
    permits["sigungu"] = permits["addr"].str.extract(r"서울특별시\s+(\S+?구)\b")[0]
    permits["permit_date"] = pd.to_datetime(permits["인허가일자"], errors="coerce")
    permits["close_date"] = pd.to_datetime(permits["폐업일자"], errors="coerce")

    months = pd.period_range("2021-01", "2023-08", freq="M")
    valid = permits.dropna(subset=["sigungu", "permit_date"]).copy()
    rows = []
    for sig in sorted(GU_CODE.values()):
        sub = valid[valid["sigungu"] == sig]
        for m in months:
            start, end = m.start_time, m.end_time
            active = (
                (sub["permit_date"] <= start)
                & ((sub["close_date"].isna()) | (sub["close_date"] > end))
            ).sum()
            closed = ((sub["close_date"] >= start) & (sub["close_date"] <= end)).sum()
            rows.append(
                {
                    "sigungu": sig,
                    "year_month": str(m),
                    "n_active": int(active),
                    "n_closures": int(closed),
                    "permit_closure_rate": float(closed / active) if active else np.nan,
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(cfg.TABLE_DIR / "external_permits_gu_monthly.csv", index=False, encoding="utf-8-sig")
    return out


def build_kcd_gu_index() -> pd.DataFrame:
    df = pd.read_parquet(cfg.TABLE_DIR / "unified_store_table.parquet")
    panel = df[df["in_panel"] == 1].dropna(subset=["sigungu", "outcome_3"]).copy()
    counts = panel.pivot_table(index="sigungu", columns="outcome_3", values="public_id", aggfunc="count", fill_value=0)
    for c in cfg.OUTCOME_CLASSES:
        if c not in counts.columns:
            counts[c] = 0
    counts = counts[cfg.OUTCOME_CLASSES].reset_index()
    counts["kcd_n_stores"] = counts[cfg.OUTCOME_CLASSES].sum(axis=1)
    counts["kcd_growth_share"] = counts["Growth"] / counts["kcd_n_stores"]
    counts["kcd_decline_share"] = counts["Decline"] / counts["kcd_n_stores"]
    counts["kcd_stable_share"] = counts["Stable"] / counts["kcd_n_stores"]
    counts["kcd_levi"] = counts["kcd_growth_share"] - counts["kcd_decline_share"]

    closure = (
        df.dropna(subset=["sigungu"])
        .groupby("sigungu")
        .agg(kcd_total_stores=("public_id", "count"), kcd_closed=("is_closed", "sum"))
        .reset_index()
    )
    closure["kcd_closure_rate"] = closure["kcd_closed"] / closure["kcd_total_stores"]
    return counts.merge(closure, on="sigungu", how="left")


def build_gu_external_validation(lp_monthly: pd.DataFrame, permits_monthly: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    kcd = build_kcd_gu_index()
    lp = lp_monthly.copy()
    lp["date"] = pd.to_datetime(lp["year_month"] + "-01")
    lp = lp[(lp["date"] >= "2021-01-01") & (lp["date"] <= "2023-08-31")]
    lp_agg = (
        lp.groupby("sigungu")
        .agg(lp_mean=("lp_mean", "mean"), lp_first=("lp_mean", "first"), lp_last=("lp_mean", "last"))
        .reset_index()
    )
    lp_agg["lp_pct_change"] = (lp_agg["lp_last"] - lp_agg["lp_first"]) / lp_agg["lp_first"]

    pm = permits_monthly.copy()
    pm["date"] = pd.to_datetime(pm["year_month"] + "-01")
    pm = pm[(pm["date"] >= "2021-01-01") & (pm["date"] <= "2023-08-31")]
    permit_agg = (
        pm.groupby("sigungu")
        .agg(
            permit_closure_rate_mean=("permit_closure_rate", "mean"),
            permit_closure_rate_median=("permit_closure_rate", "median"),
            permit_closures_total=("n_closures", "sum"),
            permit_active_mean=("n_active", "mean"),
        )
        .reset_index()
    )

    gu = kcd.merge(lp_agg, on="sigungu", how="inner").merge(permit_agg, on="sigungu", how="inner")
    gu.to_csv(cfg.TABLE_DIR / "external_validation_gu.csv", index=False, encoding="utf-8-sig")

    kcd_cols = ["kcd_levi", "kcd_growth_share", "kcd_decline_share", "kcd_closure_rate"]
    ext_cols = ["lp_mean", "lp_pct_change", "permit_closure_rate_mean", "permit_closure_rate_median"]
    rows = []
    for kc in kcd_cols:
        for ec in ext_cols:
            rows.append(
                {
                    "kcd_metric": kc,
                    "external_metric": ec,
                    "pearson": gu[[kc, ec]].corr(method="pearson").iloc[0, 1],
                    "spearman": gu[[kc, ec]].corr(method="spearman").iloc[0, 1],
                    "n": int(gu[[kc, ec]].dropna().shape[0]),
                }
            )
    corr = pd.DataFrame(rows)
    corr.to_csv(cfg.TABLE_DIR / "external_validation_correlations.csv", index=False, encoding="utf-8-sig")
    return gu, corr


def _external_zips(kind: str) -> list[Path]:
    out = []
    for p in cfg.DATA_EXTERNAL_DIR.glob("*.zip"):
        name = unicodedata.normalize("NFC", p.name)
        if kind in name and "상권분석서비스" in name:
            out.append(p)
    return sorted(out)


def load_commercial_quarterly() -> pd.DataFrame:
    sales_rows = []
    for p in _external_zips("추정매출-상권배후지"):
        df = _open_csv_from_zip(
            p,
            usecols=["기준_년분기_코드", "서비스_업종_코드", "당월_매출_금액", "당월_매출_건수"],
        )
        df = df[df["서비스_업종_코드"].astype(str).str.startswith("CS100")]
        sales_rows.append(df)
    sales = pd.concat(sales_rows, ignore_index=True)
    sales_q = (
        sales.groupby("기준_년분기_코드")
        .agg(external_sales=("당월_매출_금액", "sum"), external_transactions=("당월_매출_건수", "sum"))
        .reset_index()
    )

    store_rows = []
    for kind in ["점포-상권", "점포-상권배후지"]:
        for p in _external_zips(kind):
            if kind == "점포-상권" and "상권배후지" in unicodedata.normalize("NFC", p.name):
                continue
            df = _open_csv_from_zip(
                p,
                usecols=["기준_년분기_코드", "서비스_업종_코드", "점포_수", "개업_점포_수", "폐업_점포_수"],
            )
            df = df[df["서비스_업종_코드"].astype(str).str.startswith("CS100")]
            df["source"] = kind
            store_rows.append(df)
    stores = pd.concat(store_rows, ignore_index=True)
    store_q = (
        stores.groupby(["source", "기준_년분기_코드"])
        .agg(external_store_count=("점포_수", "sum"), external_openings=("개업_점포_수", "sum"), external_closures=("폐업_점포_수", "sum"))
        .reset_index()
    )
    store_q["external_closure_rate"] = store_q["external_closures"] / store_q["external_store_count"].replace(0, np.nan)
    store_q = store_q.pivot(index="기준_년분기_코드", columns="source")
    store_q.columns = ["_".join([b, a]).strip("_") for a, b in store_q.columns]
    store_q = store_q.reset_index()

    out = sales_q.merge(store_q, on="기준_년분기_코드", how="outer")
    out["quarter_code"] = out["기준_년분기_코드"].astype(int)
    out["quarter"] = out["quarter_code"].astype(str).str[:4] + "Q" + out["quarter_code"].astype(str).str[-1]
    out = out.sort_values("quarter_code")
    out.to_csv(cfg.TABLE_DIR / "external_commercial_quarterly.csv", index=False, encoding="utf-8-sig")
    return out


def build_kcd_quarterly() -> pd.DataFrame:
    weekly = pd.read_parquet(cfg.WEEKLY_PATH)
    weekly["date_id"] = pd.to_datetime(weekly["date_id"])
    weekly = weekly[(weekly["date_id"] >= "2021-01-01") & (weekly["date_id"] <= "2023-08-31")].copy()
    weekly["quarter"] = weekly["date_id"].dt.to_period("Q").astype(str)
    out = (
        weekly.groupby("quarter")
        .agg(
            kcd_sales=("sales_card", "sum"),
            kcd_transactions=("customer", "sum"),
            kcd_active_stores=("public_id", "nunique"),
        )
        .reset_index()
    )
    out["quarter_code"] = out["quarter"].str[:4].astype(int) * 10 + out["quarter"].str[-1].astype(int)
    out.to_csv(cfg.TABLE_DIR / "external_kcd_quarterly.csv", index=False, encoding="utf-8-sig")
    return out


def build_temporal_validation(ext_q: pd.DataFrame, kcd_q: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    q = kcd_q.merge(ext_q, on=["quarter", "quarter_code"], how="inner")
    q = q[q["quarter_code"] <= 20233].sort_values("quarter_code").copy()
    for c in ["kcd_sales", "kcd_transactions", "external_sales", "external_transactions"]:
        if c in q:
            q[f"{c}_qoq"] = q[c].pct_change()
    rows = []
    pairs = [
        ("kcd_sales", "external_sales"),
        ("kcd_transactions", "external_transactions"),
        ("kcd_sales_qoq", "external_sales_qoq"),
        ("kcd_transactions_qoq", "external_transactions_qoq"),
    ]
    for a, b in pairs:
        sub = q[[a, b]].replace([np.inf, -np.inf], np.nan).dropna()
        rows.append(
            {
                "kcd_metric": a,
                "external_metric": b,
                "pearson": sub.corr(method="pearson").iloc[0, 1] if len(sub) >= 3 else np.nan,
                "spearman": sub.corr(method="spearman").iloc[0, 1] if len(sub) >= 3 else np.nan,
                "n": int(len(sub)),
            }
        )
    corr = pd.DataFrame(rows)
    q.to_csv(cfg.TABLE_DIR / "external_temporal_validation.csv", index=False, encoding="utf-8-sig")
    corr.to_csv(cfg.TABLE_DIR / "external_temporal_correlations.csv", index=False, encoding="utf-8-sig")
    return q, corr


def make_figures(gu: pd.DataFrame, temporal: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].scatter(gu["kcd_levi"], gu["lp_pct_change"] * 100, s=55, alpha=0.8)
    axes[0].set_xlabel("KCD LEVI (Growth share - Decline share)")
    axes[0].set_ylabel("Living population change (%)")
    axes[0].set_title("External validity: LEVI vs living-population change")
    axes[0].grid(True, alpha=0.3)

    axes[1].scatter(gu["kcd_closure_rate"] * 100, gu["permit_closure_rate_mean"] * 100, s=55, alpha=0.8, color="#b04a4a")
    axes[1].set_xlabel("KCD inferred closure rate (%)")
    axes[1].set_ylabel("Permit-register monthly closure rate (%)")
    axes[1].set_title("Closure construct check")
    axes[1].grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(cfg.FIGURE_DIR / "fig17_external_gu_validation.png")
    plt.close(fig)

    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(temporal["quarter"], temporal["kcd_sales"] / temporal["kcd_sales"].iloc[0], "o-", label="KCD card sales index")
    ax1.plot(temporal["quarter"], temporal["external_sales"] / temporal["external_sales"].iloc[0], "o-", label="Seoul commercial sales index")
    ax1.set_ylabel("Index (first quarter = 1.0)")
    ax1.set_xlabel("Quarter")
    ax1.set_title("Temporal external validation: KCD vs Seoul commercial sales")
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    fig.autofmt_xdate(rotation=35)
    fig.tight_layout()
    fig.savefig(cfg.FIGURE_DIR / "fig18_external_temporal_validation.png")
    plt.close(fig)


def write_log(gu_corr: pd.DataFrame, time_corr: pd.DataFrame, gu: pd.DataFrame) -> None:
    def val(k, e, df):
        r = df[(df["kcd_metric"] == k) & (df["external_metric"] == e)].iloc[0]
        return f"Pearson {r['pearson']:.3f}, Spearman {r['spearman']:.3f}, n={int(r['n'])}"

    lines = [
        "# Step 15 External Validation",
        "",
        "## Headline correlations",
        f"- KCD LEVI vs living-population change: {val('kcd_levi', 'lp_pct_change', gu_corr)}",
        f"- KCD LEVI vs permit closure rate: {val('kcd_levi', 'permit_closure_rate_mean', gu_corr)}",
        f"- KCD inferred closure vs permit closure rate: {val('kcd_closure_rate', 'permit_closure_rate_mean', gu_corr)}",
        f"- KCD quarterly sales vs Seoul commercial sales: {val('kcd_sales', 'external_sales', time_corr)}",
        f"- QoQ sales growth correlation: {val('kcd_sales_qoq', 'external_sales_qoq', time_corr)}",
        "",
        "## Top LEVI districts",
        gu.sort_values("kcd_levi", ascending=False)[["sigungu", "kcd_n_stores", "kcd_levi", "lp_pct_change", "permit_closure_rate_mean"]]
        .head(8)
        .to_string(index=False),
    ]
    out = "\n".join(lines)
    (cfg.DOC_DIR / "step15_external_validation.log").write_text(out, encoding="utf-8")
    print(out)


def main() -> None:
    print("[15] loading living population ...")
    lp = load_living_population()
    print("[15] loading permit register ...")
    permits = load_permits()
    print("[15] building gu-level validation ...")
    gu, gu_corr = build_gu_external_validation(lp, permits)
    print("[15] loading commercial district quarterly data ...")
    ext_q = load_commercial_quarterly()
    kcd_q = build_kcd_quarterly()
    temporal, time_corr = build_temporal_validation(ext_q, kcd_q)
    make_figures(gu, temporal)
    write_log(gu_corr, time_corr, gu)
    print("[15] external validation complete")


if __name__ == "__main__":
    main()
