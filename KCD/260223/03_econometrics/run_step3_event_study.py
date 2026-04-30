"""
Step 3b: Event Study — 변곡점(t=0) 기준 '신규 고객 비율(new_customer_ratio)' 전후 12주 추이.
DUY vs DDZ 그룹별로 신규 고객 유입 추세가 어떻게 갈라지는지 시각화 (동어반복인 매출이 아님).
보강: 지역(sigungu)·업종(depth_2) 고정효과를 넣은 통제 추정(adjusted means) 추가.

Output:
  event_study_plots.png          — Raw 평균 추이 (DUY vs DDZ)
  event_study_plots_controlled.png — 지역·업종 통제 후 추정 추이
  event_study_means.csv          — Raw 집계
  event_study_means_controlled.csv — 통제 후 집계

Run from 260223: python 03_econometrics/run_step3_event_study.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "outputs" / "tables"
FIG_DIR = ROOT / "outputs" / "figures"
LOG_DIR = ROOT / "outputs" / "logs"

try:
    import yaml
    def load_config():
        with open(ROOT / "configs" / "pipeline.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
except ImportError:
    def load_config():
        return {"data": {"id_col": "public_id", "time_col_week": "day_after1", "sales_col": "sales_card", "weekly_parquet": "../original_data/weekly_processed.parquet", "weekly_parquet_fallback": "../original_data/weekly.parquet"}, "event_study": {"weeks_before": 12, "weeks_after": 12, "control_fixed_effects": True}}

# DUY(턴어라운드)·DDZ(쇠퇴) 그룹만 비교
EVENT_GROUPS = ["DUY", "DDZ"]


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "run_step3_event_study.log"

    def log(msg: str):
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    cfg = load_config()
    data_cfg = cfg.get("data", {})
    ev_cfg = cfg.get("event_study", {})
    weeks_before = ev_cfg.get("weeks_before", 12)
    weeks_after = ev_cfg.get("weeks_after", 12)
    id_col = data_cfg.get("id_col", "public_id")

    # 1) UDX 라벨 (inflection_week, final_code) 로드
    udx_path = ROOT / "outputs" / "tables" / "df_udx_labels.parquet"
    if not udx_path.exists():
        udx_path = ROOT / "outputs" / "tables" / "df_udx_labels.csv"
    if not udx_path.exists():
        log("ERROR: Run Step 2 first. df_udx_labels not found.")
        return
    udx = pd.read_parquet(udx_path) if str(udx_path).endswith(".parquet") else pd.read_csv(udx_path)
    if "inflection_week" not in udx.columns or "final_code" not in udx.columns:
        log("ERROR: df_udx_labels needs inflection_week and final_code.")
        return
    udx = udx[udx["final_code"].isin(EVENT_GROUPS)].copy()
    inf = udx[[id_col, "inflection_week", "final_code"]].dropna()
    log(f"Stores (DUY+DDZ) with inflection: {len(inf)}. DUY={len(inf[inf['final_code']=='DUY'])}, DDZ={len(inf[inf['final_code']=='DDZ'])}")

    # 2) 주별 데이터: 신규 고객 비율 또는 대리 지표
    # optional: customer 컬럼이 있는 별도 parquet 우선 시도 (event_study.weekly_customer_parquet)
    wp = None
    if ev_cfg.get("weekly_customer_parquet"):
        wp_candidate = (ROOT / ev_cfg["weekly_customer_parquet"]).resolve()
        if wp_candidate.exists():
            try:
                w = pd.read_parquet(wp_candidate)
                if "customer_new" in w.columns and "customer" in w.columns:
                    wp = wp_candidate
                    weekly = w
                    log(f"Using weekly with customer columns: {wp}")
            except Exception as e:
                log(f"weekly_customer_parquet load failed: {e}")
    if wp is None:
        wp = (ROOT / data_cfg.get("weekly_parquet", "../original_data/weekly_processed.parquet")).resolve()
        if not wp.exists():
            wp = (ROOT / data_cfg.get("weekly_parquet_fallback", "../original_data/weekly.parquet")).resolve()
        if not wp.exists():
            log("ERROR: Weekly parquet not found.")
            return
        weekly = pd.read_parquet(wp)
    cols = set(weekly.columns)
    sid = id_col if id_col in cols else "public_id"
    tw = data_cfg.get("time_col_week") or ("day_after1" if "day_after1" in cols else "week_id")
    sv = data_cfg.get("sales_col") or ("sales_card" if "sales_card" in cols else "sales")

    # 주별 new_customer_ratio 존재 여부
    if "new_customer_ratio" in cols:
        value_col = "new_customer_ratio"
        weekly = weekly[[sid, tw, "new_customer_ratio"]].rename(columns={sid: "public_id", tw: "week"})
        weekly = weekly.dropna(subset=["new_customer_ratio"])
        log("Using weekly column: new_customer_ratio")
    elif "customer_new" in cols and "customer" in cols:
        value_col = "new_customer_ratio"
        weekly = weekly[[sid, tw, "customer_new", "customer"]].rename(columns={sid: "public_id", tw: "week"})
        weekly["new_customer_ratio"] = weekly["customer_new"] / (weekly["customer"].replace(0, np.nan))
        weekly = weekly.dropna(subset=["new_customer_ratio"])[["public_id", "week", "new_customer_ratio"]]
        log("Computed weekly new_customer_ratio from customer_new / customer")
    else:
        # 대리: 4주 전 대비 매출 성장률 (신규 유입 추세 프록시)
        value_col = "sales_growth_4w"
        weekly = weekly[[sid, tw, sv]].rename(columns={sid: "public_id", tw: "week", sv: "sales"})
        weekly = weekly.sort_values(["public_id", "week"])
        weekly["sales_lag4"] = weekly.groupby("public_id")["sales"].shift(4)
        weekly["sales_growth_4w"] = (weekly["sales"] - weekly["sales_lag4"]) / (weekly["sales_lag4"].replace(0, np.nan))
        weekly = weekly.dropna(subset=["sales_growth_4w"])[["public_id", "week", "sales_growth_4w"]]
        weekly = weekly.rename(columns={"sales_growth_4w": value_col})
        log("Using proxy: sales_growth_4w (4-week sales growth). Add weekly new_customer_ratio in data for actual ratio.")

    # 3) event_time 정렬 및 그룹별 집계
    merge_df = weekly.merge(inf, on="public_id", how="inner")
    merge_df["event_time"] = merge_df["week"] - merge_df["inflection_week"]
    merge_df = merge_df[(merge_df["event_time"] >= -weeks_before) & (merge_df["event_time"] <= weeks_after)]
    merge_df = merge_df.rename(columns={value_col: "value"})
    log(f"Event window: event_time [{-weeks_before}, {weeks_after}], rows={len(merge_df)}")

    agg = merge_df.groupby(["event_time", "final_code"])["value"].agg(["mean", "std", "count"]).reset_index()
    agg["se"] = agg["std"] / np.sqrt(agg["count"].clip(1))

    # 4) 시각화: DUY vs DDZ
    fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    for code in EVENT_GROUPS:
        sub = agg[agg["final_code"] == code].sort_values("event_time")
        if len(sub) == 0:
            continue
        ax.plot(sub["event_time"], sub["mean"], "o-", markersize=4, label=code)
        ax.fill_between(sub["event_time"], sub["mean"] - 1.96 * sub["se"], sub["mean"] + 1.96 * sub["se"], alpha=0.2)
    ax.axvline(0, color="gray", linestyle="--", label="Inflection (t=0)")
    ax.set_xlabel("Event time (weeks from inflection)")
    ylabel = "New customer ratio" if value_col == "new_customer_ratio" else "Sales growth 4w (proxy)"
    ax.set_ylabel(ylabel)
    ax.set_title("Event Study: New Customer Inflow Trend by UDX Group (DUY vs DDZ)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    out_fig = FIG_DIR / "event_study_plots.png"
    fig.savefig(out_fig, bbox_inches="tight", dpi=150)
    plt.close()
    log(f"Saved {out_fig}")

    agg.to_csv(OUT_DIR / "event_study_means.csv", index=False, encoding="utf-8-sig")
    log(f"Saved {OUT_DIR / 'event_study_means.csv'}")

    # 5) 보강: 지역(sigungu)·업종(depth_2) 고정효과 통제 후 추정
    control_fe = ev_cfg.get("control_fixed_effects", True)
    base_path = OUT_DIR / "df_base_features.parquet"
    if not base_path.exists():
        base_path = OUT_DIR / "df_base_features.csv"
    if control_fe and base_path.exists():
        try:
            base = pd.read_parquet(base_path) if str(base_path).endswith(".parquet") else pd.read_csv(base_path)
            fe_cols = [c for c in ["sigungu", "depth_2"] if c in base.columns]
            if fe_cols:
                base_fe = base[[id_col] + fe_cols].drop_duplicates()
                for c in fe_cols:
                    base_fe[c] = base_fe[c].fillna("Unknown").astype(str)
                merge_fe = merge_df.merge(base_fe, on=id_col, how="inner")
                if len(merge_fe) < 100:
                    log("Event study controlled: too few rows after merging base FE; skip.")
                else:
                    dummies_fe = pd.get_dummies(merge_fe[fe_cols], drop_first=True, dtype=float)
                    et_dummies = pd.get_dummies(merge_fe["event_time"].astype(int), prefix="et", drop_first=False)
                    if -weeks_before in et_dummies.columns:
                        et_dummies = et_dummies.drop(columns=[-weeks_before])
                    fc_dummy = (merge_fe["final_code"] == "DUY").astype(float).values.reshape(-1, 1)
                    interaction = et_dummies.values * fc_dummy
                    X_design = np.hstack([
                        np.ones((len(merge_fe), 1)),
                        et_dummies.values,
                        fc_dummy,
                        interaction,
                        dummies_fe.values,
                    ])
                    y_val = merge_fe["value"].values.astype(float)
                    ok = np.isfinite(y_val) & np.all(np.isfinite(X_design), axis=1)
                    X_ok, y_ok = X_design[ok], y_val[ok]
                    if X_ok.shape[0] < 100:
                        log("Event study controlled: too few finite rows; skip.")
                    else:
                        try:
                            from sklearn.linear_model import LinearRegression
                            lr = LinearRegression(fit_intercept=False).fit(X_ok, y_ok)
                            pred = lr.predict(X_design)
                        except Exception as e2:
                            log(f"Event study controlled regression fit failed (e.g. singular matrix): {e2}")
                            pred = None
                        if pred is not None:
                            merge_fe = merge_fe.copy()
                            merge_fe["value_controlled"] = pred
                            agg_c = merge_fe.groupby(["event_time", "final_code"])["value_controlled"].agg(["mean", "std", "count"]).reset_index()
                            agg_c["se"] = agg_c["std"] / np.sqrt(agg_c["count"].clip(1))
                            agg_c.to_csv(OUT_DIR / "event_study_means_controlled.csv", index=False, encoding="utf-8-sig")
                            log(f"Saved {OUT_DIR / 'event_study_means_controlled.csv'} (sigungu, depth_2 controlled)")

                            fig2, ax2 = plt.subplots(1, 1, figsize=(10, 5))
                            for code in EVENT_GROUPS:
                                sub = agg_c[agg_c["final_code"] == code].sort_values("event_time")
                                if len(sub) == 0:
                                    continue
                                ax2.plot(sub["event_time"], sub["mean"], "o-", markersize=4, label=code)
                                ax2.fill_between(sub["event_time"], sub["mean"] - 1.96 * sub["se"], sub["mean"] + 1.96 * sub["se"], alpha=0.2)
                            ax2.axvline(0, color="gray", linestyle="--", label="Inflection (t=0)")
                            ax2.set_xlabel("Event time (weeks from inflection)")
                            ax2.set_ylabel(ylabel + " (sigungu, depth_2 controlled)")
                            ax2.set_title("Event Study: DUY vs DDZ (Adjusted for Region & Industry)")
                            ax2.legend()
                            ax2.grid(True, alpha=0.3)
                            fig2.savefig(FIG_DIR / "event_study_plots_controlled.png", bbox_inches="tight", dpi=150)
                            plt.close(fig2)
                            log(f"Saved {FIG_DIR / 'event_study_plots_controlled.png'}")
            else:
                log("Event study controlled: sigungu/depth_2 not in base; skip.")
        except Exception as e:
            log(f"Event study controlled step failed: {e}")
    else:
        if not control_fe:
            log("Event study controlled: disabled in config.")
        elif not base_path.exists():
            log("Event study controlled: df_base_features not found (run Step 1).")

if __name__ == "__main__":
    main()
