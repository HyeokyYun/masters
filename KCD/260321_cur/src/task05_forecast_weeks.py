"""
Task 05 ─ 예측 주차별 Ablation + Forecasting 벤치마크 비교
═══════════════════════════════════════════════════════════
미팅 피드백:
  - 30주→0.37, 50주→0.43 (3-class 기준)
  - 다양한 W(20/30/40/50주)로 조기 예측 실행
  - 12-class + 3-class(Growth/Stable/Decline) 모두 리포트
  - sales forecasting / demand forecasting 벤치마크 조사

출력:
  - forecast_weeks_comparison.csv      (W별 예측 성능 비교)
  - forecast_weeks_3class.csv          (3-class 버전)
  - forecast_benchmark_literature.csv  (벤치마크 비교표)
  - fig_forecast_weeks.png             (W별 성능 그래프)
"""
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import (
    RandomForestClassifier, GradientBoostingClassifier,
)
from sklearn.metrics import f1_score, accuracy_score
from src import config as cfg
from src.data_loader import (
    load_labeled_features, load_weekly_raw, load_meta,
    prepare_ts_for_prediction, add_outcome3,
)

try:
    import lightgbm as lgb
    HAS_LGB = True
except ImportError:
    HAS_LGB = False


# ── 조기 피처 추출 ────────────────────────────────────────

def build_early_features(ts: pd.DataFrame, W: int) -> pd.DataFrame:
    """오픈 후 W주 데이터만으로 피처 추출."""
    records = []

    for pid, g in ts.groupby("public_id"):
        g = (g.sort_values("weeks_since_open")
              .drop_duplicates("weeks_since_open")
              .reset_index(drop=True))
        ge = g[g["weeks_since_open"] < W]

        if len(ge) < max(10, W // 3):
            continue

        y = ge["sales_card_mm"].fillna(0).values.astype(float)
        if not np.isfinite(y).all() or y.std() < 1e-9:
            continue

        t = np.arange(len(y), dtype=float)
        h = len(y) // 2

        s_all, _, r, _, _ = stats.linregress(t, y)
        s_e = stats.linregress(t[:h], y[:h])[0] if h > 2 else 0.0
        cv = min(y.std() / (y.mean() + 1e-9), 2.0)
        mdd = ((np.maximum.accumulate(y) - y) / (np.maximum.accumulate(y) + 1e-9)).max()

        nc_rate_e = np.nan
        if "customer_new" in ge.columns and "customer" in ge.columns:
            denom = ge["customer"].replace(0, np.nan) + 1
            nc = ge["customer_new"] / denom
            nc_rate_e = float(nc.mean()) if nc.notna().any() else np.nan

        records.append({
            "public_id": pid,
            "e_slope_all":   float(s_all),
            "e_slope_early": float(s_e),
            "e_cv":          float(cv),
            "e_mdd":         float(mdd),
            "e_r2":          float(r ** 2),
            "e_mean":        float(y.mean()),
            "e_nc_rate":     nc_rate_e,
        })

    edf = pd.DataFrame(records)
    print(f"  W={W}: {len(edf):,} 매장 피처 추출")
    return edf


# ── 예측 모델 ─────────────────────────────────────────────

def _get_models():
    models = {
        "RF":  RandomForestClassifier(
            n_estimators=200, class_weight="balanced",
            max_depth=8, random_state=cfg.SEED),
        "GBM": GradientBoostingClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.1,
            subsample=0.8, random_state=cfg.SEED),
    }
    if HAS_LGB:
        models["LightGBM"] = lgb.LGBMClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            class_weight="balanced", random_state=cfg.SEED, verbose=-1)
    return models


def evaluate_prediction(edf: pd.DataFrame, feat: pd.DataFrame,
                         W: int, label_col: str = "label") -> list:
    """특정 W에서 예측 성능 평가 (CV)."""
    merged = edf.merge(feat[["public_id", label_col]].drop_duplicates("public_id"),
                       on="public_id", how="inner")
    vc = merged[label_col].value_counts()
    min_count = max(20, cfg.CV_FOLDS + 1)
    merged = merged[merged[label_col].isin(vc[vc >= min_count].index)].copy()

    if len(merged) < 50 or merged[label_col].nunique() < 2:
        print(f"  W={W}, {label_col}: 데이터 부족 (n={len(merged)})")
        return []

    feature_cols = [c for c in edf.columns if c.startswith("e_")]
    X = merged[feature_cols].values
    y = merged[label_col].values

    skf = StratifiedKFold(n_splits=cfg.CV_FOLDS, shuffle=True, random_state=cfg.SEED)
    rows = []

    for model_name, clf in _get_models().items():
        pipe = Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("sc",  StandardScaler()),
            ("clf", clf),
        ])

        le = LabelEncoder().fit(y)
        y_enc = le.transform(y)
        all_preds = np.zeros_like(y_enc)

        try:
            for train_idx, test_idx in skf.split(X, y_enc):
                pipe.fit(X[train_idx], y[train_idx])
                all_preds[test_idx] = le.transform(pipe.predict(X[test_idx]))

            f1 = f1_score(y_enc, all_preds, average="weighted")
            acc = accuracy_score(y_enc, all_preds)

            rows.append({
                "W": W,
                "label_type": label_col,
                "n_classes": merged[label_col].nunique(),
                "n_samples": len(merged),
                "model": model_name,
                "F1_weighted": round(f1, 4),
                "Accuracy": round(acc, 4),
            })
            print(f"  W={W} | {label_col:10s} | {model_name:8s} | "
                  f"F1={f1:.4f}  Acc={acc:.4f}")
        except Exception as e:
            print(f"  W={W} | {model_name}: 오류 → {e}")

    return rows


def run_weeks_comparison(ts: pd.DataFrame, feat: pd.DataFrame,
                          weeks_list: list = None) -> pd.DataFrame:
    """다양한 W에서 12-class + 3-class 예측 비교."""
    if weeks_list is None:
        weeks_list = [20, 30, 40, 50]

    feat_3 = add_outcome3(feat)

    all_rows = []
    for W in weeks_list:
        print(f"\n{'─' * 40}")
        print(f"  조기 예측 W={W}주")
        print(f"{'─' * 40}")

        edf = build_early_features(ts, W)
        if len(edf) < 50:
            print(f"  W={W}: 피처 추출 매장 부족 → 건너뜀")
            continue

        # 12-class
        rows_12 = evaluate_prediction(edf, feat, W, label_col="label")
        all_rows.extend(rows_12)

        # 3-class
        rows_3 = evaluate_prediction(edf, feat_3, W, label_col="outcome3")
        all_rows.extend(rows_3)

    result_df = pd.DataFrame(all_rows)
    if not result_df.empty:
        result_df.to_csv(cfg.TABLE_DIR / "forecast_weeks_comparison.csv",
                         index=False, encoding="utf-8-sig")

        # 3-class 별도 저장
        df3 = result_df[result_df["label_type"] == "outcome3"]
        if not df3.empty:
            df3.to_csv(cfg.TABLE_DIR / "forecast_weeks_3class.csv",
                       index=False, encoding="utf-8-sig")

    return result_df


# ── 벤치마크 비교표 ───────────────────────────────────────

def create_benchmark_table():
    """Sales / demand forecasting 문헌 벤치마크 비교표."""
    benchmarks = [
        {
            "domain": "Small Business Sales (this study)",
            "task": "Lifecycle classification (3-class)",
            "horizon": "30 weeks ahead",
            "metric": "F1-weighted",
            "baseline_range": "0.33–0.40",
            "note": "Using first 30 weeks of data to predict lifecycle outcome",
        },
        {
            "domain": "Retail Demand Forecasting",
            "task": "SKU-level demand prediction",
            "horizon": "1–4 weeks",
            "metric": "MAPE / WMAPE",
            "baseline_range": "15–30% error",
            "note": "Fildes et al. (2019), IJF; M5 competition",
        },
        {
            "domain": "Stock Market Prediction",
            "task": "Direction (up/down/flat)",
            "horizon": "1 day – 1 month",
            "metric": "Accuracy",
            "baseline_range": "0.50–0.60",
            "note": "Sezer et al. (2020), Expert Systems; binary/ternary",
        },
        {
            "domain": "Restaurant Survival",
            "task": "Closure prediction (binary)",
            "horizon": "1–3 years",
            "metric": "AUC / Accuracy",
            "baseline_range": "0.65–0.80",
            "note": "Parsa et al. (2005), Cornell HQ; Luo & Stark (2015)",
        },
        {
            "domain": "Company Sales Forecasting",
            "task": "Revenue growth classification",
            "horizon": "1 quarter – 1 year",
            "metric": "Accuracy / F1",
            "baseline_range": "0.40–0.65",
            "note": "Agrawal et al. (2022), ML for Finance; analyst consensus",
        },
        {
            "domain": "M5 Forecasting Competition",
            "task": "Walmart sales forecasting",
            "horizon": "28 days ahead",
            "metric": "WRMSSE",
            "baseline_range": "0.52–0.75",
            "note": "Makridakis et al. (2022), IJF; top solutions",
        },
        {
            "domain": "New Product Demand",
            "task": "First-year demand prediction",
            "horizon": "6–12 months",
            "metric": "MAPE",
            "baseline_range": "30–50% error",
            "note": "Goodwin et al. (2017); cold-start problem",
        },
    ]

    bench_df = pd.DataFrame(benchmarks)
    bench_df.to_csv(cfg.TABLE_DIR / "forecast_benchmark_literature.csv",
                    index=False, encoding="utf-8-sig")
    print(f"\n[Task05] 벤치마크 비교표:")
    print(bench_df.to_string(index=False))
    return bench_df


# ── 시각화 ────────────────────────────────────────────────

def plot_forecast_weeks(result_df: pd.DataFrame):
    """W별 예측 성능 그래프."""
    if result_df.empty:
        return

    plt = cfg.setup_matplotlib()
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for ax_idx, (label_type, title) in enumerate([
        ("label", "12-class 예측 성능"),
        ("outcome3", "3-class (Growth/Stable/Decline) 예측 성능"),
    ]):
        ax = axes[ax_idx]
        sub = result_df[result_df["label_type"] == label_type]
        if sub.empty:
            ax.text(0.5, 0.5, "데이터 없음", ha="center", transform=ax.transAxes)
            ax.set_title(title)
            continue

        for model in sub["model"].unique():
            ms = sub[sub["model"] == model]
            ax.plot(ms["W"], ms["F1_weighted"], "o-", label=f"{model} (F1)", linewidth=2)

        ax.set_xlabel("조기 예측 주수 (W)")
        ax.set_ylabel("F1-weighted")
        ax.set_title(title)
        ax.set_xticks(sub["W"].unique())
        ax.legend()
        ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(cfg.FIGURE_DIR / "fig_forecast_weeks.png",
                dpi=150, bbox_inches="tight")
    plt.close("all")
    print("  → figures/fig_forecast_weeks.png")


# ── 엔트리 ────────────────────────────────────────────────

def run_task05():
    """Task 05 전체 실행."""
    print("\n" + "=" * 62)
    print("  Task 05: 예측 주차별 Ablation + 벤치마크")
    print("=" * 62)

    feat = load_labeled_features()
    meta = load_meta()

    print("\n[Task05] 시계열 전처리 중...")
    ts_raw = load_weekly_raw()
    ts = prepare_ts_for_prediction(ts_raw, meta)

    result_df = run_weeks_comparison(ts, feat, weeks_list=[20, 30, 40, 50])
    create_benchmark_table()

    if not result_df.empty:
        plot_forecast_weeks(result_df)

        # 요약 출력
        print(f"\n{'=' * 50}")
        print("  예측 성능 요약 (Best model per W)")
        print(f"{'=' * 50}")
        for label_type in ["label", "outcome3"]:
            sub = result_df[result_df["label_type"] == label_type]
            if sub.empty:
                continue
            best = sub.loc[sub.groupby("W")["F1_weighted"].idxmax()]
            print(f"\n  [{label_type}]")
            for _, row in best.iterrows():
                print(f"    W={int(row['W']):2d}주: F1={row['F1_weighted']:.4f} "
                      f"({row['model']}, n={int(row['n_samples']):,})")

    print("\n[Task05] 완료")
