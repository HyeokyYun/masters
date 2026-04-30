"""
소상공인 생애주기 진단 파이프라인 v4.0
────────────────────────────────────────────────────────────────────
입력 데이터 (원본 기준):
  - weekly.parquet    : 약 658만 행 × 12컬럼, 5.9만 매장, 255주
                        (public_id, date_id, sales_card, sales_delivery,
                         customer, customer_new,
                         before_noon_sales, after_noon_sales, weekend_sales, ...)
  - meta.csv          : 5.9만 매장 × 14컬럼
                        (public_id, open_month, delivery_link,
                         business_square_size,
                         classification__kcd_v3__depth_2_name, age, ...)

보고서(KAIST) 준수:
  1) 거시변수 통제: 개별 매출 / 해당 주 전체 합 → 코로나·계절 효과 제거
  2) Time alignment: 실제 날짜 X, 오픈 후 경과 주차(weeks_since_open) 기준
  3) 2019년 1월 이후 개업 업장만 분석 (보고서 조건)
  4) 업종 3분류: 일반음식점 / 술집 / 카페·베이커리
  5) 1단계: K-Means 업종별 K=9 클러스터링
  6) 2단계: 3자리 생애주기 레이블 (DDZ/DDY/DUY/UUX/UDY/UDZ)
  7) 3단계: XGB + Logistic 분류, Ablation Study
  8) 조기예측: 오픈 후 30주 데이터만으로 생애주기 예측

실행:
  python lifecycle_pipeline_v4.py
  (weekly.parquet, meta.csv 와 같은 디렉토리에서 실행)
────────────────────────────────────────────────────────────────────
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from scipy import stats
from itertools import combinations
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib import rcParams

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report, f1_score
from sklearn.utils.class_weight import compute_sample_weight
import statsmodels.api as sm

# ── 한글 폰트 설정
_kf = [f.name for f in fm.fontManager.ttflist
       if any(k in f.name for k in ["Nanum", "Gothic", "Malgun", "나눔"])]
rcParams["font.family"] = _kf[0] if _kf else "DejaVu Sans"
rcParams["axes.unicode_minus"] = False


# ═══════════════════════════════════════════════════════════
# 0. 데이터 로딩
#    원본: weekly.parquet (658만 행, 5.9만 매장)
#    개발/테스트: weekly_reduced.parquet 로 대체 가능
# ═══════════════════════════════════════════════════════════
def load_data(parquet_path="weekly.parquet", meta_path="meta.csv"):
    print(f"[Load] {parquet_path} 로딩 중...")
    ts   = pd.read_parquet(parquet_path)
    meta = pd.read_csv(meta_path)

    ts["public_id"]   = ts["public_id"].astype(str)
    meta["public_id"] = meta["public_id"].astype(str)

    # date_id: "2022-11-21" 형식 → datetime
    ts["date_id"] = pd.to_datetime(ts["date_id"])

    # 음수 매출 제거
    ts.loc[ts["sales_card"] < 0, "sales_card"] = np.nan

    print(f"[Load] TS {ts.shape}  |  매장 수: {ts['public_id'].nunique():,}")
    print(f"[Load] 기간: {ts['date_id'].min().date()} ~ {ts['date_id'].max().date()}")
    print(f"[Load] Meta {meta.shape}")
    return ts, meta


# ═══════════════════════════════════════════════════════════
# 1. 전처리
# ═══════════════════════════════════════════════════════════
def preprocess(ts, meta, min_weeks=52):
    """
    보고서 4.3.2 전처리:
    ① 거시변수 통제: 주별 전체 합 대비 개별 비율
    ② open_month → weeks_since_open 계산
    ③ 2019년 이후 개업 업장만
    ④ min_weeks 이상 관측 업장만
    ⑤ 결측 보간 + 업장별 MinMax scaling
    """
    ts = ts.copy().sort_values(["public_id", "date_id"])

    # ① 거시변수 통제
    ts["sales_ratio"] = ts.groupby("date_id")["sales_card"].transform(
        lambda x: x / (x.sum() + 1e-9)
    )

    # ② open_month 병합 + weeks_since_open
    open_info = meta[["public_id", "open_month",
                       "delivery_link", "business_square_size",
                       "classification__kcd_v3__depth_2_name",
                       "age"]].copy()
    open_info["open_date"] = pd.to_datetime(
        open_info["open_month"].astype(str), format="%Y-%m", errors="coerce"
    )
    ts = ts.merge(open_info, on="public_id", how="left")

    ts["weeks_since_open"] = (
        (ts["date_id"] - ts["open_date"]).dt.days // 7
    ).clip(lower=0)

    # ③ 2019년 이후 개업만 (보고서: 오픈 시기 기준 time alignment를 위해)
    ts = ts[ts["open_date"] >= "2019-01-01"].copy()

    # ④ min_weeks 이상 업장만
    n_obs  = ts.groupby("public_id")["weeks_since_open"].count()
    valid  = n_obs[n_obs >= min_weeks].index
    ts     = ts[ts["public_id"].isin(valid)].copy()

    # ⑤ 결측 보간 + MinMax (업장별)
    ts["sales_card"] = ts.groupby("public_id")["sales_card"].transform(
        lambda x: x.interpolate(method="linear").ffill().bfill()
    )
    ts["sales_minmax"] = ts.groupby("public_id")["sales_card"].transform(
        lambda x: (x - x.min()) / (x.max() - x.min() + 1e-9)
    )

    n_stores = ts["public_id"].nunique()
    print(f"[Preprocess] {n_stores:,} 매장, {len(ts):,} 행")
    print(f"[Preprocess] weeks_since_open 범위: "
          f"{ts['weeks_since_open'].min()} ~ {ts['weeks_since_open'].max()}")
    return ts


# ═══════════════════════════════════════════════════════════
# 2. 업종 분류 (보고서 4.3.2: 3종)
# ═══════════════════════════════════════════════════════════
def classify_category(ts):
    cat_col = "classification__kcd_v3__depth_2_name"
    if cat_col not in ts.columns:
        ts["category"] = "일반음식점"
        return ts

    cafe_kw = ["카페", "베이커리", "디저트", "커피"]
    bar_kw  = ["술집", "주점", "호프"]

    def _cat(v):
        v = str(v)
        if any(k in v for k in cafe_kw): return "카페/베이커리"
        if any(k in v for k in bar_kw):  return "술집"
        return "일반음식점"

    cat_map = ts.groupby("public_id")[cat_col].first().apply(_cat)
    ts["category"] = ts["public_id"].map(cat_map)

    dist = ts.groupby("category")["public_id"].nunique()
    print(f"[Category] {dist.to_dict()}")
    return ts


# ═══════════════════════════════════════════════════════════
# 3. 1단계: K-Means 클러스터링 (보고서 4.3.2)
#    업종별 × 샘플기간별(108주/162주), K=9
# ═══════════════════════════════════════════════════════════
def cluster_by_category(ts, n_clusters=9, sample_weeks=108, seed=42):
    """
    보고서: 업종별로 나눠서 K-Means
    인풋: sales_minmax (Min-Max scaled, 업장별)
    오픈 후 sample_weeks 이내 데이터만 사용
    """
    all_labels = []

    for cat, grp in ts.groupby("category"):
        sub = grp[grp["weeks_since_open"] < sample_weeks]
        pivot = (
            sub.drop_duplicates(["public_id", "weeks_since_open"])
               .pivot_table(index="public_id",
                            columns="weeks_since_open",
                            values="sales_minmax",
                            aggfunc="mean")
        )
        # 90% 이상 데이터 있는 주차만, 90% 이상 주차 있는 업장만
        pivot = pivot.dropna(axis=1, thresh=int(len(pivot) * 0.5))
        pivot = pivot.dropna(axis=0, thresh=int(pivot.shape[1] * 0.9))

        if len(pivot) < n_clusters * 3:
            print(f"[KMeans] {cat}: 샘플 부족 ({len(pivot)}) → 스킵")
            continue

        X  = pivot.fillna(pivot.median(axis=0)).values
        km = KMeans(n_clusters=n_clusters, random_state=seed,
                    n_init=10, max_iter=300)
        labels = km.fit_predict(X)

        # 클러스터별 센터 기울기 (추후 레이블링 참고용)
        center_slopes = []
        for c in range(n_clusters):
            ctr = km.cluster_centers_[c]
            s, *_ = stats.linregress(np.arange(len(ctr)), ctr)
            center_slopes.append(round(s, 6))

        df_c = pd.DataFrame({
            "public_id":     pivot.index,
            "cluster_raw":   labels,
            "category":      cat,
            "sample_weeks":  sample_weeks,
        })
        all_labels.append(df_c)

        dist = dict(pd.Series(labels).value_counts().sort_index())
        print(f"[KMeans] {cat} ({sample_weeks}w): "
              f"inertia={km.inertia_:.1f}  n={len(pivot):,}  분포={dist}")

    return (pd.concat(all_labels, ignore_index=True)
            if all_labels else pd.DataFrame())


# ═══════════════════════════════════════════════════════════
# 4. Piecewise Regression (변곡점 탐지)
# ═══════════════════════════════════════════════════════════
def piecewise_reg(y, max_bp=2):
    """BIC 최소화로 변곡점 위치 + 각 구간 기울기 탐색"""
    n    = len(y)
    t    = np.arange(n, dtype=float)
    best = {"bic": np.inf, "bp": [], "slopes": [0.0]}

    try:
        m = sm.OLS(y, np.column_stack([np.ones(n), t])).fit()
        best = {"bic": m.bic, "bp": [], "slopes": [float(m.params[1])]}
    except Exception:
        pass

    for nbp in range(1, max_bp + 1):
        step = max(1, n // (nbp * 5))
        for bps in combinations(range(step * 2, n - step * 2, step), nbp):
            bps_s = sorted(bps)
            segs  = [0] + bps_s + [n]
            sl, rss, ok = [], 0.0, True
            for i in range(len(segs) - 1):
                st = t[segs[i]:segs[i+1]]
                sy = y[segs[i]:segs[i+1]]
                if len(st) < 3:
                    ok = False; break
                s, ic, *_ = stats.linregress(st, sy)
                sl.append(float(s))
                rss += float(np.sum((sy - (s * st + ic)) ** 2))
            if not ok:
                continue
            bic = n * np.log(rss / n + 1e-9) + (nbp * 2 + 2) * np.log(n)
            if bic < best["bic"]:
                best = {"bic": bic, "bp": bps_s, "slopes": sl}

    return best


# ═══════════════════════════════════════════════════════════
# 5. 2단계: 3자리 생애주기 레이블 (보고서 4.4.1)
# ═══════════════════════════════════════════════════════════
def assign_label(y):
    """
    보고서 레이블 체계:
      기간1 (변곡점 이전): U(상승) / D(하락)
      기간2 (변곡점 이후): U(상승) / D(하락)
      현재 상태 (기간2 후반 1/3): X(성장) / Y(안정) / Z(퇴로)

    6개 클래스: DDZ, DDY, DUY, UUX, UDY, UDZ
    """
    n  = len(y)
    pw = piecewise_reg(y, max_bp=1)
    bp = pw["bp"]
    sl = pw["slopes"]

    if len(bp) == 0:
        bp_idx = n // 2
        s1 = s2 = sl[0] if sl else 0.0
    else:
        bp_idx = bp[0]
        s1 = sl[0] if len(sl) > 0 else 0.0
        s2 = sl[1] if len(sl) > 1 else s1

    c1 = "U" if s1 >= 0 else "D"
    c2 = "U" if s2 >= 0 else "D"

    # 현재 상태: 기간2 후반 1/3 구간
    tail_start = int(bp_idx + (n - bp_idx) * 2 / 3)
    tail_start = max(tail_start, n - 20)
    tail_y     = y[min(tail_start, n - 4):]

    if len(tail_y) >= 3:
        tail_slope, *_ = stats.linregress(
            np.arange(len(tail_y), dtype=float), tail_y)
    else:
        tail_slope = s2

    # 안정/성장/퇴로 임계: 표준편차 기반 동적 설정
    thr = y.std() * 0.004 + 1e-9
    if   tail_slope >  thr: state = "X"
    elif tail_slope < -thr: state = "Z"
    else:                    state = "Y"

    return f"{c1}{c2}{state}"


# ═══════════════════════════════════════════════════════════
# 6. 피처 추출 + 레이블 생성
# ═══════════════════════════════════════════════════════════
def extract_features(ts, max_weeks=108):
    """
    매장별:
    - 3자리 생애주기 레이블
    - 시계열 형상 피처 (slope, cv, mdd, n_inf, r2)
    - 고객·배달·시간대 피처
    """
    records = []

    for pid, g in ts.groupby("public_id"):
        g = (g.sort_values("weeks_since_open")
              .drop_duplicates("weeks_since_open")
              .reset_index(drop=True))
        g = g[g["weeks_since_open"] < max_weeks]
        y = g["sales_card"].fillna(0).values.astype(float)

        if len(y) < 30 or not np.isfinite(y).all():
            continue

        n = len(y)
        t = np.arange(n, dtype=float)

        s_all, _, r, _, _ = stats.linregress(t, y)
        h   = n // 2
        s_e, *_ = stats.linregress(t[:h], y[:h])
        s_l, *_ = stats.linregress(t[h:], y[h:])
        cv  = y.std() / (y.mean() + 1e-9)
        mdd = ((np.maximum.accumulate(y) - y) /
               (np.maximum.accumulate(y) + 1e-9)).max()
        pw  = piecewise_reg(y, max_bp=2)

        # 고객 피처
        nc_rate = np.nan
        if "customer_new" in g.columns and "customer" in g.columns:
            denom = g["customer"].replace(0, np.nan)
            nc    = g["customer_new"] / (denom + 1)
            nc_rate = float(nc.mean()) if nc.notna().any() else np.nan

        # 배달 비율
        del_ratio = np.nan
        if "sales_delivery" in g.columns:
            total = y.sum()
            if total > 0:
                del_ratio = float(
                    g["sales_delivery"].fillna(0).sum() / total)

        # 시간대 비율
        before_noon = (float(g["before_noon_sales"].mean())
                       if "before_noon_sales" in g.columns else np.nan)
        after_noon  = (float(g["after_noon_sales"].mean())
                       if "after_noon_sales"  in g.columns else np.nan)
        weekend     = (float(g["weekend_sales"].mean())
                       if "weekend_sales"  in g.columns else np.nan)

        records.append({
            "public_id":    pid,
            "label":        assign_label(y),
            "slope_all":    float(s_all),
            "slope_early":  float(s_e),
            "slope_late":   float(s_l),
            "r2":           float(r ** 2),
            "cv":           float(cv),
            "mdd":          float(mdd),
            "n_inf":        len(pw["bp"]),
            "nc_rate":      nc_rate,
            "del_ratio":    del_ratio,
            "before_noon":  before_noon,
            "after_noon":   after_noon,
            "weekend":      weekend,
            "n_weeks":      n,
        })

    feat = pd.DataFrame(records)
    print(f"\n[Features] {len(feat):,} 매장")
    print(f"[Labels]  분포:\n{feat['label'].value_counts().to_string()}")

    # 보고서 표 15와 비교
    print(f"\n[Labels] 각 레이블 평균 slope_early / slope_late:")
    for lbl, g in feat.groupby("label"):
        print(f"  {lbl}: early={g['slope_early'].mean():+.4f}  "
              f"late={g['slope_late'].mean():+.4f}  n={len(g):,}")

    return feat


# ═══════════════════════════════════════════════════════════
# 7. Sub-RQ2: 생애주기 결정 요인 (다항 로지스틱)
# ═══════════════════════════════════════════════════════════
def sub_rq2(feat, meta):
    df = feat.merge(
        meta[["public_id", "delivery_link",
              "business_square_size", "age"]].fillna(
              {"delivery_link": 0, "business_square_size": 0}),
        on="public_id", how="left"
    )
    df["tenure"] = df["n_weeks"]

    feature_cols = ["tenure", "nc_rate", "cv", "mdd",
                    "slope_early", "delivery_link"]

    vc = df["label"].value_counts()
    df = df[df["label"].isin(vc[vc >= 50].index)].copy()
    dm = df.dropna(subset=feature_cols).copy()

    X = dm[feature_cols].values
    y = dm["label"].values

    # 계수 출력용
    imp = SimpleImputer(strategy="median").fit(X)
    X_s = StandardScaler().fit_transform(imp.transform(X))
    lr  = LogisticRegression(solver="lbfgs", max_iter=2000,
                              class_weight="balanced",
                              random_state=42).fit(X_s, y)
    coef = pd.DataFrame(lr.coef_,
                         index=lr.classes_,
                         columns=feature_cols).round(3)
    print(f"\n[Sub-RQ2] Coef:\n{coef.to_string()}")

    pipe = Pipeline([
        ("imp", SimpleImputer(strategy="median")),
        ("sc",  StandardScaler()),
        ("clf", LogisticRegression(solver="lbfgs", max_iter=2000,
                                    class_weight="balanced",
                                    random_state=42))
    ])
    cv_f1 = cross_val_score(pipe, X, y, cv=5,
                             scoring="f1_weighted", error_score=0)
    print(f"[Sub-RQ2] CV F1(weighted): {cv_f1.mean():.4f} ± {cv_f1.std():.4f}")
    return coef, cv_f1.mean()


# ═══════════════════════════════════════════════════════════
# 8. Sub-RQ4: Ablation Study
#    leakage 방지: slope_late 제외
# ═══════════════════════════════════════════════════════════
def sub_rq4_ablation(feat, meta):
    """
    Base:       cv, mdd, n_weeks, delivery_link
    Base+UDX:   + slope_early, n_inf, nc_rate, del_ratio, before_noon, weekend
    
    slope_late 제외 이유:
      assign_label()이 내부적으로 tail_slope(≈ slope_late 후반부)를
      기준으로 X/Y/Z를 결정하므로 leakage 발생
    """
    df = feat.merge(
        meta[["public_id", "delivery_link",
              "business_square_size"]].fillna(0),
        on="public_id", how="left"
    )

    base = ["cv", "mdd", "n_weeks", "delivery_link"]
    udx  = base + ["slope_early", "n_inf", "nc_rate",
                   "del_ratio", "before_noon", "weekend"]

    vc = df["label"].value_counts()
    df = df[df["label"].isin(vc[vc >= 50].index)].copy()
    y  = df["label"].values

    rows = []
    print("[Sub-RQ4 Ablation]")
    for fname, fcols in [("Base (전통 지표)", base),
                         ("Base + UDX 정보",  udx)]:
        avail = [c for c in fcols if c in df.columns]
        X = df[avail].values
        for cname, clf in [
            ("Logistic", LogisticRegression(solver="lbfgs", max_iter=2000,
                                             class_weight="balanced")),
            ("GBM",      GradientBoostingClassifier(n_estimators=100,
                                                     random_state=42)),
            ("RF",       RandomForestClassifier(n_estimators=100,
                                                 class_weight="balanced",
                                                 random_state=42)),
        ]:
            pipe = Pipeline([
                ("imp", SimpleImputer(strategy="median")),
                ("sc",  StandardScaler()),
                ("clf", clf)
            ])
            cv = cross_val_score(pipe, X, y, cv=5,
                                  scoring="f1_weighted", error_score=0)
            rows.append({"Feature Set": fname, "Model": cname,
                          "F1": cv.mean(), "Std": cv.std()})
            print(f"  {fname[:20]:20s} | {cname:8s} | "
                  f"F1={cv.mean():.4f} ± {cv.std():.4f}")

    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════
# 9. Sub-RQ4: 조기 예측 (보고서 4.4.2: 오픈 후 30주)
# ═══════════════════════════════════════════════════════════
def sub_rq4_early(ts, feat, W=30):
    """
    보고서 발견:
    "오픈 후 약 30주 정도의 매출 추세만으로도
     대략적인 그래프 추이를 예측할 수 있음"

    → 처음 W주 데이터만 피처로 사용, 최종 레이블 예측
    """
    rows = []
    for pid, g in ts.groupby("public_id"):
        g = (g.sort_values("weeks_since_open")
              .drop_duplicates("weeks_since_open")
              .reset_index(drop=True))

        # 초기 W주 피처
        g_early = g[g["weeks_since_open"] < W]
        # 전체 기간 충분한지 확인 (레이블 신뢰도)
        g_full  = g[g["weeks_since_open"] < 108]

        if len(g_early) < 10 or len(g_full) < W + 30:
            continue

        y_e = g_early["sales_card"].fillna(0).values.astype(float)
        if not np.isfinite(y_e).all() or y_e.std() < 1e-9:
            continue

        t   = np.arange(len(y_e), dtype=float)
        s, _, r, _, _ = stats.linregress(t, y_e)
        pw  = piecewise_reg(y_e, max_bp=1)
        cv  = y_e.std() / (y_e.mean() + 1e-9)
        mdd = ((np.maximum.accumulate(y_e) - y_e) /
               (np.maximum.accumulate(y_e) + 1e-9)).max()

        rows.append({
            "public_id": pid,
            "slope_e":   float(s),
            "cv_e":      float(cv),
            "mdd_e":     float(mdd),
            "n_inf_e":   len(pw["bp"]),
            "r2_e":      float(r ** 2),
        })

    early_df = (pd.DataFrame(rows)
                  .merge(feat[["public_id", "label"]], on="public_id"))
    vc = early_df["label"].value_counts()
    early_df = early_df[early_df["label"].isin(vc[vc >= 30].index)]

    fc   = ["slope_e", "cv_e", "mdd_e", "n_inf_e", "r2_e"]
    pipe = Pipeline([
        ("imp", SimpleImputer(strategy="median")),
        ("sc",  StandardScaler()),
        ("clf", GradientBoostingClassifier(n_estimators=100, random_state=42))
    ])
    cv5 = cross_val_score(
        pipe, early_df[fc].values, early_df["label"].values,
        cv=5, scoring="f1_weighted", error_score=0
    )
    print(f"\n[Sub-RQ4 Early-{W}w]  "
          f"F1(weighted)={cv5.mean():.4f} ± {cv5.std():.4f}  "
          f"n={len(early_df):,}")
    return {"W": W, "f1": cv5.mean(), "std": cv5.std(), "n": len(early_df)}


# ═══════════════════════════════════════════════════════════
# 10. 시각화 (4-panel)
# ═══════════════════════════════════════════════════════════
def visualize(feat, ablation_df, ts, early_res,
              out="lifecycle_results_v4.png"):
    COLORS = {
        "DDZ": "#C62828", "DDY": "#EF9A9A",
        "DUY": "#1565C0", "UUX": "#2E7D32",
        "UDY": "#F57F17", "UDZ": "#6A1B9A"
    }

    fig, axes = plt.subplots(2, 2, figsize=(20, 16))

    # ── Panel 1: 레이블별 평균 매출 궤적
    ax = axes[0, 0]
    for lbl, grp in feat.groupby("label"):
        pids  = grp["public_id"].values
        trajs = []
        for pid in pids[:200]:
            g = (ts[ts["public_id"] == pid]
                   .sort_values("weeks_since_open")
                   .drop_duplicates("weeks_since_open"))
            y = g["sales_card"].fillna(0).values.astype(float)
            if len(y) >= 60 and np.isfinite(y).all():
                y_n = (y - y.mean()) / (y.std() + 1e-9)
                trajs.append(y_n[:108])
        if not trajs:
            continue
        L   = min(len(t) for t in trajs)
        avg = np.mean([t[:L] for t in trajs], axis=0)
        c   = COLORS.get(lbl, "gray")
        # 개별 궤적 (반투명)
        for traj in trajs[:30]:
            ax.plot(traj[:L], color=c, alpha=0.04, linewidth=0.8)
        # 평균선
        ax.plot(avg, label=f"{lbl} (n={len(grp):,})",
                color=c, linewidth=2.5)

    ax.axhline(0, color="gray", ls="--", alpha=0.4)
    ax.set_title("생애주기 레이블별 평균 매출 궤적\n(오픈 후 경과 주차, z-score)",
                 fontsize=12, fontweight="bold")
    ax.set_xlabel("오픈 후 경과 주차")
    ax.set_ylabel("정규화 매출 (z-score)")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)

    # ── Panel 2: 레이블 분포 (보고서 표 15 비교)
    ax = axes[0, 1]
    vc     = feat["label"].value_counts().sort_values(ascending=False)
    colors = [COLORS.get(l, "gray") for l in vc.index]
    bars   = ax.bar(vc.index, vc.values, color=colors,
                    edgecolor="white", linewidth=0.8)
    for bar, v in zip(bars, vc.values):
        pct = v / len(feat) * 100
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + len(feat) * 0.005,
                f"{v:,}\n({pct:.1f}%)",
                ha="center", fontsize=9, fontweight="bold")
    # 보고서 기준선 (DDZ 62%)
    ax.axhline(len(feat) * 0.62, color="red", ls="--",
               alpha=0.5, label="보고서 DDZ 기준 62%")
    ax.set_title("생애주기 패턴 분포\n(보고서 기준: DDZ ≈ 62%)",
                 fontsize=12, fontweight="bold")
    ax.set_ylabel("업장 수")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, axis="y")

    # ── Panel 3: slope_early vs slope_late (사분면)
    ax = axes[1, 0]
    for lbl, grp in feat.groupby("label"):
        sample = grp.sample(min(500, len(grp)), random_state=42)
        ax.scatter(sample["slope_early"], sample["slope_late"],
                   label=lbl, alpha=0.3, s=10,
                   color=COLORS.get(lbl, "gray"))
    ax.axhline(0, color="gray", ls="--", alpha=0.6)
    ax.axvline(0, color="gray", ls="--", alpha=0.6)
    # 사분면 주석
    ax.text(0.78, 0.93, "UU·성장", transform=ax.transAxes,
            fontsize=9, color="#2E7D32", fontweight="bold")
    ax.text(0.04, 0.93, "DU·반등", transform=ax.transAxes,
            fontsize=9, color="#1565C0", fontweight="bold")
    ax.text(0.78, 0.05, "UD·쇠퇴", transform=ax.transAxes,
            fontsize=9, color="#F57F17", fontweight="bold")
    ax.text(0.04, 0.05, "DD·지속하락", transform=ax.transAxes,
            fontsize=9, color="#C62828", fontweight="bold")
    ax.set_xlabel("초반부 기울기 (slope_early)")
    ax.set_ylabel("후반부 기울기 (slope_late)")
    ax.set_title("생애주기 패턴의 기울기 사분면 분포",
                 fontsize=12, fontweight="bold")
    ax.legend(fontsize=9, markerscale=2)
    ax.grid(alpha=0.3)

    # ── Panel 4: Ablation Study
    ax = axes[1, 1]
    if ablation_df is not None and not ablation_df.empty:
        mnames = ablation_df["Model"].unique()
        f_b = ablation_df[
            ablation_df["Feature Set"].str.contains("Base \\(")]["F1"].values
        f_u = ablation_df[
            ablation_df["Feature Set"].str.contains("UDX")]["F1"].values
        s_b = ablation_df[
            ablation_df["Feature Set"].str.contains("Base \\(")]["Std"].values
        s_u = ablation_df[
            ablation_df["Feature Set"].str.contains("UDX")]["Std"].values

        x, w = np.arange(len(mnames)), 0.35
        b1 = ax.bar(x - w/2, f_b, w, label="Base",
                    color="#90A4AE", yerr=s_b, capsize=5)
        b2 = ax.bar(x + w/2, f_u, w, label="Base+UDX",
                    color="#1565C0", yerr=s_u, capsize=5)
        ax.bar_label(b1, fmt="%.3f", fontsize=9, padding=3)
        ax.bar_label(b2, fmt="%.3f", fontsize=9, padding=3,
                     fontweight="bold")
        for i, (b, u, su) in enumerate(zip(f_b, f_u, s_u)):
            ax.annotate(f"▲{u-b:+.3f}",
                        xy=(i + w/2, u + su + 0.02),
                        fontsize=9, color="#2E7D32",
                        ha="center", fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(mnames, rotation=15, ha="right")
        ax.set_ylim(0, 1.0)
        ax.legend()
        ax.grid(alpha=0.3, axis="y")

        if early_res:
            ax.text(0.5, 0.06,
                    f"조기예측(30주): F1={early_res['f1']:.3f}±{early_res['std']:.3f}"
                    f"  (n={early_res['n']:,})",
                    transform=ax.transAxes, fontsize=10, ha="center",
                    color="#7B1FA2", fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.3",
                              facecolor="#F3E5F5", alpha=0.8))

    ax.set_title("Ablation Study: UDX 생애주기 정보의 예측 성능 기여\n(F1 weighted)",
                 fontsize=12, fontweight="bold")

    fig.suptitle(
        "소상공인 생애주기 진단 분석 결과  (원본 weekly.parquet 기반, v4.0)",
        fontsize=14, fontweight="bold"
    )
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    print(f"[Viz] 저장: {out}")
    plt.close()


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":

    # ── 경로 설정
    # 원본 데이터 사용 (테스트 시 weekly_reduced.parquet 로 변경 가능)
    PARQUET = "weekly.parquet"
    META    = "meta.csv"

    # ── 0. 로딩
    ts, meta = load_data(PARQUET, META)

    # ── 1. 전처리
    ts = preprocess(ts, meta, min_weeks=52)

    # ── 2. 업종 분류
    ts = classify_category(ts)

    # ── 3. 1단계: K-Means 클러스터링 (보고서: 업종별 K=9)
    print("\n[Step3] K-Means 클러스터링 (업종별, K=9, 108주 샘플)...")
    cluster_df = cluster_by_category(ts, n_clusters=9,
                                      sample_weeks=108, seed=42)
    if not cluster_df.empty:
        cluster_df.to_csv("cluster_labels_v4.csv", index=False)
        print(f"  → cluster_labels_v4.csv 저장")

    # (보고서: 162주 샘플도 추가 실행)
    print("\n[Step3b] K-Means 클러스터링 (162주 샘플)...")
    cluster_df_162 = cluster_by_category(ts, n_clusters=9,
                                          sample_weeks=162, seed=42)
    if not cluster_df_162.empty:
        cluster_df_162.to_csv("cluster_labels_162w_v4.csv", index=False)

    # ── 4. 2단계: 피처 추출 + 3자리 레이블
    print("\n[Step4] 피처 추출 + 생애주기 레이블링 (108주 기준)...")
    feat = extract_features(ts, max_weeks=108)
    feat.to_csv("lifecycle_features_v4.csv", index=False)
    print(f"  → lifecycle_features_v4.csv 저장")

    # ── 5. Sub-RQ2: 결정 요인 분석
    print("\n[Step5] Sub-RQ2: 생애주기 결정 요인 (다항 로지스틱)...")
    coef_df, rq2_f1 = sub_rq2(feat, meta)
    coef_df.to_csv("logit_coef_v4.csv")
    print(f"  → logit_coef_v4.csv 저장")

    # ── 6. Sub-RQ4: Ablation Study
    print("\n[Step6] Sub-RQ4: Ablation Study...")
    ablation_df = sub_rq4_ablation(feat, meta)
    ablation_df.to_csv("ablation_results_v4.csv", index=False)
    print(f"  → ablation_results_v4.csv 저장")

    # ── 7. Sub-RQ4: 조기 예측 (30주)
    print("\n[Step7] Sub-RQ4: 조기 예측 (오픈 후 30주)...")
    early_res = sub_rq4_early(ts, feat, W=30)

    # ── 8. 시각화
    print("\n[Step8] 시각화...")
    visualize(feat, ablation_df, ts, early_res,
              out="lifecycle_results_v4.png")

    # ── 최종 요약
    print("\n" + "═" * 60)
    print("✅  분석 완료 요약  (원본 weekly.parquet 기반)")
    print("═" * 60)
    print(f"  분석 매장 수:        {ts['public_id'].nunique():,}개")
    print(f"\n  생애주기 레이블 분포 (보고서 표 15 비교):")
    vc_report = {"DDZ": "62%", "DDY": "10%", "DUY": "7%",
                 "UUX": "11%", "UDY": "0.8%", "UDZ": "9%"}
    for lbl, cnt in feat["label"].value_counts().items():
        pct  = cnt / len(feat) * 100
        ref  = vc_report.get(lbl, "?")
        print(f"    {lbl}: {cnt:5,}개 ({pct:5.1f}%)  ← 보고서: {ref}")
    print(f"\n  Sub-RQ2 F1(weighted): {rq2_f1:.4f}")
    print(f"  조기예측(30주) F1:    {early_res['f1']:.4f} ± {early_res['std']:.4f}")
    print("═" * 60)

    outputs = [
        "lifecycle_features_v4.csv",
        "cluster_labels_v4.csv",
        "cluster_labels_162w_v4.csv",
        "logit_coef_v4.csv",
        "ablation_results_v4.csv",
        "lifecycle_results_v4.png",
    ]
    print("\n출력 파일:")
    for f in outputs:
        if os.path.exists(f):
            size = os.path.getsize(f) / 1024
            print(f"  ✓ {f:40s} ({size:7.1f} KB)")
