"""
Prepare external macro indicators for gu-level LEVI correlation.

Inputs:
  - thesis/data_external/LOCAL_PEOPLE_GU_2021/2022/2023.zip
      : Seoul living population, daily x hour x gu (CP949)
  - thesis/data_external/seoul_food_permits.csv
      : Seoul food-service permit register (CP949)

Outputs (thesis/analysis/outputs/):
  - living_population_gu_monthly.csv
  - closures_gu_monthly.csv
  - macro_gu_panel.csv : merged gu x month panel
"""

import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/hyeoky98/kcd")
EXT = ROOT / "thesis" / "data_external"
OUT = ROOT / "thesis" / "analysis" / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

# Seoul gu code -> name (행정구역 코드 v. 2022)
GU_CODE = {
    11110: "종로구", 11140: "중구", 11170: "용산구", 11200: "성동구",
    11215: "광진구", 11230: "동대문구", 11260: "중랑구", 11290: "성북구",
    11305: "강북구", 11320: "도봉구", 11350: "노원구", 11380: "은평구",
    11410: "서대문구", 11440: "마포구", 11470: "양천구", 11500: "강서구",
    11530: "구로구", 11545: "금천구", 11560: "영등포구", 11590: "동작구",
    11620: "관악구", 11650: "서초구", 11680: "강남구", 11710: "송파구",
    11740: "강동구",
}


# ---------------- 1. Living population ----------------
def load_lp(zip_path: Path) -> pd.DataFrame:
    """Load one year's LP zip, aggregate to daily total per gu."""
    with zipfile.ZipFile(zip_path) as zf:
        name = [n for n in zf.namelist() if n.endswith(".csv")][0]
        with zf.open(name) as f:
            df = pd.read_csv(
                f, encoding="cp949",
                usecols=["기준일ID", "시간대구분", "자치구코드", "총생활인구수"],
                dtype={"기준일ID": str, "시간대구분": int,
                       "자치구코드": int, "총생활인구수": float},
            )
    # Daily mean of hourly total (avg 24h level, more stable than sum)
    daily = (
        df.groupby(["기준일ID", "자치구코드"], as_index=False)["총생활인구수"].mean()
    )
    daily["date"] = pd.to_datetime(daily["기준일ID"], format="%Y%m%d")
    daily["year_month"] = daily["date"].dt.to_period("M").astype(str)
    daily["sigungu"] = daily["자치구코드"].map(GU_CODE)
    return daily.dropna(subset=["sigungu"])


print("[1/3] Loading living population ...")
lp_all = pd.concat([
    load_lp(EXT / "LOCAL_PEOPLE_GU_2021.zip"),
    load_lp(EXT / "LOCAL_PEOPLE_GU_2022.zip"),
    load_lp(EXT / "LOCAL_PEOPLE_GU_2023.zip"),
], ignore_index=True)

lp_monthly = (
    lp_all.groupby(["sigungu", "year_month"], as_index=False)["총생활인구수"]
          .mean()
          .rename(columns={"총생활인구수": "lp_mean"})
)
lp_monthly.to_csv(OUT / "living_population_gu_monthly.csv", index=False)
print(f"  living pop monthly: {lp_monthly.shape[0]} rows, "
      f"{lp_monthly['sigungu'].nunique()} gus, "
      f"{lp_monthly['year_month'].nunique()} months")


# ---------------- 2. Permits / closures ----------------
print("[2/3] Loading permits file ...")
permits = pd.read_csv(
    EXT / "seoul_food_permits.csv",
    encoding="cp949",
    encoding_errors="replace",
    usecols=["인허가일자", "영업상태명", "상세영업상태명",
             "폐업일자", "지번주소", "도로명주소"],
    dtype=str,
    low_memory=False,
)
print(f"  permits loaded: {permits.shape[0]:,} rows")

# Extract sigungu from address (road-name preferred, else 지번)
def pick_addr(row):
    a = row["도로명주소"]
    if isinstance(a, str) and a.strip():
        return a
    return row["지번주소"] if isinstance(row["지번주소"], str) else ""

permits["addr"] = permits.apply(pick_addr, axis=1)
# Match '서울특별시 XXX구'
pat = re.compile(r"서울특별시\s+(\S+?구)\b")
permits["sigungu"] = permits["addr"].str.extract(pat)[0]

# Parse dates
permits["permit_date"] = pd.to_datetime(permits["인허가일자"], errors="coerce")
permits["close_date"] = pd.to_datetime(permits["폐업일자"], errors="coerce")

# Analysis window: 2021-01 ~ 2023-08 (KCD data window)
win_start = pd.Timestamp("2021-01-01")
win_end = pd.Timestamp("2023-08-31")

closures = permits.dropna(subset=["close_date", "sigungu"])
closures = closures[
    (closures["close_date"] >= win_start) & (closures["close_date"] <= win_end)
].copy()
closures["year_month"] = closures["close_date"].dt.to_period("M").astype(str)

closures_monthly = (
    closures.groupby(["sigungu", "year_month"])
            .size()
            .reset_index(name="n_closures")
)

# Active-store denominator: stores with permit_date <= month_start
# and (close_date is null OR close_date > month_end)
def month_active_count(df_permit: pd.DataFrame, month: pd.Period, sigungu: str):
    m_start = month.start_time
    m_end = month.end_time
    mask = (
        (df_permit["sigungu"] == sigungu)
        & (df_permit["permit_date"] <= m_start)
        & ((df_permit["close_date"].isna()) | (df_permit["close_date"] > m_end))
    )
    return int(mask.sum())

# Compute denominator efficiently via merge-sort logic
print("  computing monthly active-store denominators ...")
month_idx = pd.period_range("2021-01", "2023-08", freq="M")
permits_valid = permits.dropna(subset=["sigungu", "permit_date"]).copy()
denom_rows = []
for sig in sorted(GU_CODE.values()):
    sub = permits_valid[permits_valid["sigungu"] == sig]
    for m in month_idx:
        m_start = m.start_time
        m_end = m.end_time
        active = (
            (sub["permit_date"] <= m_start)
            & ((sub["close_date"].isna()) | (sub["close_date"] > m_end))
        ).sum()
        denom_rows.append({
            "sigungu": sig,
            "year_month": str(m),
            "n_active": int(active),
        })
denom = pd.DataFrame(denom_rows)

closures_full = denom.merge(closures_monthly, on=["sigungu", "year_month"],
                            how="left").fillna({"n_closures": 0})
closures_full["closure_rate"] = closures_full["n_closures"] / closures_full["n_active"].replace(0, np.nan)
closures_full.to_csv(OUT / "closures_gu_monthly.csv", index=False)
print(f"  closures monthly: {closures_full.shape[0]} rows")


# ---------------- 3. Merge to gu x month panel ----------------
print("[3/3] Merging gu x month panel ...")
panel = (
    lp_monthly.merge(closures_full, on=["sigungu", "year_month"], how="inner")
)
panel["date"] = pd.to_datetime(panel["year_month"] + "-01")
panel = panel.sort_values(["sigungu", "date"]).reset_index(drop=True)
panel.to_csv(OUT / "macro_gu_panel.csv", index=False)
print(f"  panel: {panel.shape[0]} rows, cols={list(panel.columns)}")
print(panel.head(3).to_string())
print("\nclosure_rate summary:")
print(panel["closure_rate"].describe().round(4).to_string())
print("\nlp_mean summary:")
print(panel["lp_mean"].describe().round(1).to_string())
