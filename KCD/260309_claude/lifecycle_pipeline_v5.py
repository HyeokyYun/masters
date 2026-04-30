"""
소상공인 생애주기 진단 파이프라인 v5.0  ─ 데이터 드리븐
═══════════════════════════════════════════════════════════════════
보고서 분포를 맞추려는 제약 없이, 데이터 탐색에서 발견한 특성 기반으로 설계.

핵심 설계 결정 (EDA 근거):
  1. 레이블: slope 방향(전반/후반) × mdd 수준 → 6개 자연 클래스
       EDA: Silhouette < 0 → KMeans 피처 클러스터링 부적합
            slope×mdd 8분류 → 6개 병합이 해석 가능하고 균형적

  2. 기울기: sales_minmax(업장별 0~1 정규화) 기반
       EDA: raw slope 스케일이 수백만원 → 단위 불일치로 시각화·ML 왜곡

  3. 레이블 임계:
       기간1(전반부): slope_early_mm 부호 (중앙값~0)
       기간2(후반부): slope_late_mm  부호 (중앙값~0)
       현재 상태:    mdd 중앙값(0.87) 기준 고/저
                     → 고mdd+후반하락=Z, 저mdd=Y, 후반상승=별도 클래스

  4. 6개 클래스 (EDA 분포 기반):
       DD_Z : 전반↓ 후반↓ 고손실  — 전형적 쇠퇴
       DD_Y : 전반↓ 후반↓ 저손실  — 저성과 안정
       DU   : 전반↓ 후반↑         — 반등
       UU   : 전반↑ 후반↑         — 지속 성장
       UD_Z : 전반↑ 후반↓ 고손실  — 성장 후 급락
       UD_Y : 전반↑ 후반↓ 저손실  — 성장 후 완만 하락

  5. 피처 전처리:
       del_ratio: log1p 변환 (EDA: >1 케이스 14%)
       cv > 2:    클리핑 (이상치 0.2%)
       low_r2:    r2 < 0.1 플래그 (EDA: 42.5%가 선형 추세 약함)

실행: python lifecycle_pipeline_v5.py
      출력 파일: /Volumes/SAMSUMG_128/master_graduate/KCD_source_code_from_Yang/26-1/260309_claude/
═══════════════════════════════════════════════════════════════════
"""

import warnings, os
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from scipy import stats

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib import rcParams

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

_kf = [f.name for f in fm.fontManager.ttflist
       if any(k in f.name for k in ["Nanum","Gothic","Malgun","나눔"])]
rcParams["font.family"] = _kf[0] if _kf else "DejaVu Sans"
rcParams["axes.unicode_minus"] = False

LABELS = ["DD_Z", "DD_Y", "DU", "UU", "UD_Z", "UD_Y"]
COLORS = {
    "DD_Z": "#C62828", "DD_Y": "#EF9A9A",
    "DU":   "#1565C0", "UU":   "#2E7D32",
    "UD_Z": "#6A1B9A", "UD_Y": "#F57F17",
}
LABEL_DESC = {
    "DD_Z": "전반↓ 후반↓  고손실  (쇠퇴)",
    "DD_Y": "전반↓ 후반↓  저손실  (저성과 안정)",
    "DU":   "전반↓ 후반↑           (반등)",
    "UU":   "전반↑ 후반↑           (지속 성장)",
    "UD_Z": "전반↑ 후반↓  고손실  (성장 후 급락)",
    "UD_Y": "전반↑ 후반↓  저손실  (성장 후 완만 하락)",
}


# ═══════════════════════════════════════════════════════════
# 0. 로딩
# ═══════════════════════════════════════════════════════════
def load_data(parquet_path="weekly.parquet", meta_path="meta.csv"):
    print(f"[Load] {parquet_path} 로딩 중...")
    ts   = pd.read_parquet(parquet_path)
    meta = pd.read_csv(meta_path)
    ts["public_id"]   = ts["public_id"].astype(str)
    meta["public_id"] = meta["public_id"].astype(str)
    ts["date_id"]     = pd.to_datetime(ts["date_id"])
    ts.loc[ts["sales_card"] < 0, "sales_card"] = np.nan
    print(f"[Load] TS {ts.shape}  매장={ts['public_id'].nunique():,}")
    print(f"[Load] 기간: {ts['date_id'].min().date()} ~ {ts['date_id'].max().date()}")
    return ts, meta


# ═══════════════════════════════════════════════════════════
# 1. 전처리
# ═══════════════════════════════════════════════════════════
def preprocess(ts, meta, min_weeks=52):
    ts = ts.copy().sort_values(["public_id", "date_id"])

    # 거시변수 통제
    ts["sales_ratio"] = ts.groupby("date_id")["sales_card"].transform(
        lambda x: x / (x.sum() + 1e-9)
    )

    # open_month 병합
    keep = [c for c in ["public_id","open_month","delivery_link",
                         "business_square_size",
                         "classification__kcd_v3__depth_2_name","age"]
            if c in meta.columns]
    oinfo = meta[keep].copy()
    oinfo["open_date"] = pd.to_datetime(
        oinfo["open_month"].astype(str), format="%Y-%m", errors="coerce")
    ts = ts.merge(oinfo, on="public_id", how="left")

    ts["weeks_since_open"] = (
        (ts["date_id"] - ts["open_date"]).dt.days // 7
    ).clip(lower=0)

    # 2019년 이후만
    ts = ts[ts["open_date"] >= "2019-01-01"].copy()

    # min_weeks 이상 업장만
    cnt = ts.groupby("public_id")["weeks_since_open"].count()
    ts  = ts[ts["public_id"].isin(cnt[cnt >= min_weeks].index)].copy()

    # 결측 보간
    ts["sales_card"] = ts.groupby("public_id")["sales_card"].transform(
        lambda x: x.interpolate("linear").ffill().bfill()
    )

    # 업장별 MinMax (0~1)
    ts["sales_minmax"] = ts.groupby("public_id")["sales_card"].transform(
        lambda x: (x - x.min()) / (x.max() - x.min() + 1e-9)
    )

    print(f"[Preprocess] {ts['public_id'].nunique():,} 매장, {len(ts):,} 행")
    return ts


# ═══════════════════════════════════════════════════════════
# 2. 업종 분류
# ═══════════════════════════════════════════════════════════
def classify_category(ts):
    col = "classification__kcd_v3__depth_2_name"
    if col not in ts.columns:
        ts["category"] = "기타"
        return ts

    def _cat(v):
        v = str(v)
        if any(k in v for k in ["카페","커피"]):        return "카페"
        if any(k in v for k in ["베이커리","디저트"]): return "베이커리/디저트"
        if any(k in v for k in ["술집","주점","호프"]): return "술집"
        if "한식"    in v: return "한식"
        if "일식"    in v: return "일식"
        if "양식"    in v: return "양식"
        if "중식"    in v: return "중식"
        if "분식"    in v: return "분식"
        if "패스트푸드" in v: return "패스트푸드"
        return "기타"

    cat_map = ts.groupby("public_id")[col].first().apply(_cat)
    ts["category"] = ts["public_id"].map(cat_map)
    dist = ts.groupby("category")["public_id"].nunique().sort_values(ascending=False)
    print(f"[Category]\n{dist.to_string()}")
    return ts


# ═══════════════════════════════════════════════════════════
# 3. 피처 추출 (MinMax 기반 slope)
# ═══════════════════════════════════════════════════════════
def extract_features(ts, max_weeks=108):
    records = []
    for pid, g in ts.groupby("public_id"):
        g = (g.sort_values("weeks_since_open")
              .drop_duplicates("weeks_since_open")
              .reset_index(drop=True))
        g = g[g["weeks_since_open"] < max_weeks]

        y_raw = g["sales_card"].fillna(0).values.astype(float)
        y_mm  = g["sales_minmax"].fillna(0).values.astype(float)
        if len(y_raw) < 30 or not np.isfinite(y_mm).all():
            continue

        n = len(y_mm)
        h = n // 2
        t = np.arange(n, dtype=float)

        # MinMax 기반 기울기
        s_e, *_     = stats.linregress(np.arange(h, dtype=float), y_mm[:h])
        s_l, *_     = stats.linregress(np.arange(n-h, dtype=float), y_mm[h:])
        s_a, _, r, *_ = stats.linregress(t, y_mm)

        # 마지막 20% 기울기 (현재 상태 보조)
        tail_n     = max(8, n // 5)
        tail_s, *_ = stats.linregress(np.arange(tail_n, dtype=float), y_mm[-tail_n:])

        # 변동성 / 손실
        cv  = min(y_raw.std() / (y_raw.mean() + 1e-9), 2.0)
        mdd = ((np.maximum.accumulate(y_mm) - y_mm) /
               (np.maximum.accumulate(y_mm) + 1e-9)).max()

        low_r2 = int(r**2 < 0.1)

        # 고객 피처
        nc_rate = np.nan
        if "customer_new" in g.columns and "customer" in g.columns:
            denom = g["customer"].replace(0, np.nan)
            nc    = g["customer_new"] / (denom + 1)
            nc_rate = float(nc.mean()) if nc.notna().any() else np.nan

        # 배달 비율 (log1p)
        del_ratio_log = np.nan
        if "sales_delivery" in g.columns:
            total = y_raw.sum()
            if total > 0:
                dr = g["sales_delivery"].fillna(0).sum() / total
                del_ratio_log = float(np.log1p(dr))

        before_noon = (float(g["before_noon_sales"].mean())
                       if "before_noon_sales" in g.columns else np.nan)
        weekend     = (float(g["weekend_sales"].mean())
                       if "weekend_sales" in g.columns else np.nan)

        records.append({
            "public_id":       pid,
            "slope_early_mm":  float(s_e),
            "slope_late_mm":   float(s_l),
            "slope_all_mm":    float(s_a),
            "tail_slope_mm":   float(tail_s),
            "r2":              float(r**2),
            "low_r2":          low_r2,
            "cv":              float(cv),
            "mdd":             float(mdd),
            "nc_rate":         nc_rate,
            "del_ratio_log":   del_ratio_log,
            "before_noon":     before_noon,
            "weekend":         weekend,
            "n_weeks":         n,
        })

    feat = pd.DataFrame(records)
    print(f"[Features] {len(feat):,} 매장")
    return feat


# ═══════════════════════════════════════════════════════════
# 4. 레이블링 (데이터 드리븐, 6클래스)
# ═══════════════════════════════════════════════════════════
def assign_labels(feat):
    """
    EDA 근거:
      slope_early_mm 중앙값 ≈ 0 → 부호로 U/D 구분
      mdd 중앙값 = 0.87         → 고손실(Z) / 저손실(Y) 구분
      DU(반등), UU(성장): n이 충분하므로 mdd 분화 없이 단일 클래스
    """
    mdd_med = feat["mdd"].median()
    print(f"[Label] mdd 임계(중앙값): {mdd_med:.4f}")

    def _label(row):
        up_e = row["slope_early_mm"] > 0
        up_l = row["slope_late_mm"]  > 0
        hi   = row["mdd"] >= mdd_med

        if   not up_e and not up_l: return "DD_Z" if hi else "DD_Y"
        elif not up_e and     up_l: return "DU"
        elif     up_e and     up_l: return "UU"
        else:                       return "UD_Z" if hi else "UD_Y"

    feat["label"] = feat.apply(_label, axis=1)

    print(f"\n[Labels] 분포:")
    vc = feat["label"].value_counts().reindex(LABELS, fill_value=0)
    for lbl in LABELS:
        cnt = vc[lbl]; pct = cnt / len(feat) * 100
        print(f"  {lbl:6s}: {cnt:6,}개 ({pct:5.1f}%)  {LABEL_DESC[lbl]}")

    print(f"\n[Labels] 클래스별 피처 평균:")
    cols = ["slope_early_mm","slope_late_mm","mdd","cv","nc_rate","n_weeks"]
    print(feat.groupby("label")[cols].mean().reindex(LABELS).round(4).to_string())

    return feat


# ═══════════════════════════════════════════════════════════
# 5. K-Means 궤적 클러스터링 (K=6)
# ═══════════════════════════════════════════════════════════
def cluster_trajectories(ts, n_clusters=6, max_weeks=108, seed=42):
    sub   = ts[ts["weeks_since_open"] < max_weeks]
    pivot = (
        sub.drop_duplicates(["public_id","weeks_since_open"])
           .pivot_table(index="public_id", columns="weeks_since_open",
                        values="sales_minmax", aggfunc="mean")
    )
    pivot = pivot.dropna(axis=1, thresh=int(len(pivot)*0.6))
    pivot = pivot.dropna(axis=0, thresh=int(pivot.shape[1]*0.85))
    X     = pivot.fillna(pivot.median(axis=0)).values

    km     = KMeans(n_clusters=n_clusters, random_state=seed,
                    n_init=15, max_iter=500)
    labels = km.fit_predict(X)

    cluster_df = pd.DataFrame({"public_id": pivot.index,
                                "traj_cluster": labels})

    print(f"\n[Cluster] K={n_clusters} 궤적 클러스터:")
    for c in range(n_clusters):
        ctr    = km.cluster_centers_[c]
        s, *_  = stats.linregress(np.arange(len(ctr), dtype=float), ctr)
        n      = (labels == c).sum()
        print(f"  C{c}: n={n:,} ({n/len(labels)*100:.1f}%)  "
              f"기울기={s:+.5f}  시작={ctr[:8].mean():.3f}  끝={ctr[-8:].mean():.3f}")

    return cluster_df, km


# ═══════════════════════════════════════════════════════════
# 6. Ablation Study
# ═══════════════════════════════════════════════════════════
def run_ablation(feat, meta):
    """
    피처셋 3단계:
      Base:      전통 운영 지표
      +Shape:    + 매출 궤적 형태 피처
      +Customer: + 고객·시간대 피처 (Full)

    slope_late_mm 제외: 레이블 정의에 직접 사용 (leakage)
    """
    df = feat.merge(
        meta[["public_id","delivery_link"]].astype({"public_id": str}).fillna(0),
        on="public_id", how="left"
    )
    vc = df["label"].value_counts()
    df = df[df["label"].isin(vc[vc >= 30].index)].copy()

    sets = {
        "Base":      ["cv","mdd","n_weeks","del_ratio_log","delivery_link"],
        "+Shape":    ["cv","mdd","n_weeks","del_ratio_log","delivery_link",
                      "slope_early_mm","tail_slope_mm","low_r2","r2"],
        "+Customer": ["cv","mdd","n_weeks","del_ratio_log","delivery_link",
                      "slope_early_mm","tail_slope_mm","low_r2","r2",
                      "nc_rate","before_noon","weekend"],
    }

    rows = []
    print("\n[Ablation Study]")
    for fname, fcols in sets.items():
        avail = [c for c in fcols if c in df.columns]
        X = df[avail].values
        y = df["label"].values
        for cname, clf in [
            ("Logistic", LogisticRegression(solver="lbfgs", max_iter=2000,
                                             class_weight="balanced")),
            ("GBM",      GradientBoostingClassifier(n_estimators=150,
                                                     max_depth=4,
                                                     random_state=42)),
            ("RF",       RandomForestClassifier(n_estimators=150,
                                                 class_weight="balanced",
                                                 random_state=42)),
        ]:
            pipe = Pipeline([
                ("imp", SimpleImputer(strategy="median")),
                ("sc",  StandardScaler()),
                ("clf", clf),
            ])
            cv = cross_val_score(pipe, X, y, cv=5,
                                  scoring="f1_weighted", error_score=0)
            rows.append({"Feature Set": fname, "Model": cname,
                          "F1": cv.mean(), "Std": cv.std()})
            print(f"  {fname:12s} | {cname:8s} | "
                  f"F1={cv.mean():.4f} ± {cv.std():.4f}")

    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════
# 7. 조기 예측 (오픈 후 30주)
# ═══════════════════════════════════════════════════════════
def early_prediction(ts, feat, W=30):
    rows = []
    for pid, g in ts.groupby("public_id"):
        g   = (g.sort_values("weeks_since_open")
                .drop_duplicates("weeks_since_open")
                .reset_index(drop=True))
        g_e = g[g["weeks_since_open"] < W]
        g_f = g[g["weeks_since_open"] < 108]
        if len(g_e) < 10 or len(g_f) < W + 30:
            continue
        y = g_e["sales_minmax"].fillna(0).values.astype(float)
        if not np.isfinite(y).all() or y.std() < 1e-9:
            continue
        t      = np.arange(len(y), dtype=float)
        h      = len(y) // 2
        s, _, r, *_ = stats.linregress(t, y)
        se, *_ = stats.linregress(t[:h], y[:h]) if h > 2 else (0.0,)
        cv     = min(y.std() / (y.mean() + 1e-9), 2.0)
        mdd    = ((np.maximum.accumulate(y) - y) /
                  (np.maximum.accumulate(y) + 1e-9)).max()
        rows.append({"public_id": pid, "s_all": s, "s_early": se,
                     "cv_e": cv, "mdd_e": mdd, "r2_e": r**2})

    edf  = pd.DataFrame(rows).merge(feat[["public_id","label"]], on="public_id")
    vc   = edf["label"].value_counts()
    edf  = edf[edf["label"].isin(vc[vc >= 30].index)]
    fc   = ["s_all","s_early","cv_e","mdd_e","r2_e"]
    pipe = Pipeline([
        ("imp", SimpleImputer(strategy="median")),
        ("sc",  StandardScaler()),
        ("clf", GradientBoostingClassifier(n_estimators=150,
                                            max_depth=4, random_state=42)),
    ])
    cv5 = cross_val_score(pipe, edf[fc].values, edf["label"].values,
                           cv=5, scoring="f1_weighted", error_score=0)
    print(f"\n[Early-{W}w] F1={cv5.mean():.4f} ± {cv5.std():.4f}  (n={len(edf):,})")
    return {"W": W, "f1": cv5.mean(), "std": cv5.std(), "n": len(edf)}


# ═══════════════════════════════════════════════════════════
# 8. 시각화 (5-panel)
# ═══════════════════════════════════════════════════════════
def visualize(feat, ablation_df, ts, early_res, km_model,
              out="lifecycle_results_v5.png"):
    fig = plt.figure(figsize=(22, 18))
    gs  = fig.add_gridspec(3, 2, hspace=0.42, wspace=0.30)
    ax1 = fig.add_subplot(gs[0, :])
    ax2 = fig.add_subplot(gs[1, 0])
    ax3 = fig.add_subplot(gs[1, 1])
    ax4 = fig.add_subplot(gs[2, 0])
    ax5 = fig.add_subplot(gs[2, 1])

    # ── 1: 레이블별 평균 궤적
    for lbl in LABELS:
        grp   = feat[feat["label"] == lbl]
        pids  = grp["public_id"].values
        trajs = []
        for pid in pids[:200]:
            g = (ts[ts["public_id"] == pid]
                   .sort_values("weeks_since_open")
                   .drop_duplicates("weeks_since_open"))
            y = g["sales_minmax"].fillna(0).values.astype(float)
            if len(y) >= 50 and np.isfinite(y).all():
                trajs.append(y[:108])
        if not trajs:
            continue
        L   = min(len(t) for t in trajs)
        avg = np.mean([t[:L] for t in trajs], axis=0)
        c   = COLORS[lbl]
        for traj in trajs[:25]:
            ax1.plot(traj[:L], color=c, alpha=0.04, linewidth=0.8)
        ax1.plot(avg, color=c, linewidth=2.5,
                 label=f"{lbl}  {LABEL_DESC[lbl]}  (n={len(grp):,})")

    ax1.axhline(0.5, color="gray", ls="--", alpha=0.3)
    ax1.set_title("생애주기 레이블별 평균 매출 궤적  "
                  "(MinMax 정규화 [0,1], 오픈 후 경과 주차)",
                  fontsize=13, fontweight="bold")
    ax1.set_xlabel("오픈 후 경과 주차")
    ax1.set_ylabel("정규화 매출 (MinMax)")
    ax1.set_ylim(-0.05, 1.1)
    ax1.legend(fontsize=9, loc="upper right")
    ax1.grid(alpha=0.3)

    # ── 2: 분포 bar
    vc     = feat["label"].value_counts().reindex(LABELS, fill_value=0)
    bars   = ax2.bar(LABELS, vc.values,
                     color=[COLORS[l] for l in LABELS], edgecolor="white")
    for bar, lbl, v in zip(bars, LABELS, vc.values):
        pct = v / len(feat) * 100
        ax2.text(bar.get_x() + bar.get_width()/2,
                 bar.get_height() + len(feat)*0.003,
                 f"{v:,}\n({pct:.1f}%)", ha="center",
                 fontsize=9, fontweight="bold")
    ax2.set_title("생애주기 패턴 분포  (6클래스)", fontsize=12, fontweight="bold")
    ax2.set_ylabel("업장 수")
    ax2.grid(alpha=0.3, axis="y")

    # ── 3: slope scatter (단위 통일)
    for lbl in LABELS:
        grp    = feat[feat["label"] == lbl]
        sample = grp.sample(min(600, len(grp)), random_state=42)
        ax3.scatter(sample["slope_early_mm"], sample["slope_late_mm"],
                    label=lbl, alpha=0.35, s=10, color=COLORS[lbl])
    ax3.axhline(0, color="gray", ls="--", alpha=0.6)
    ax3.axvline(0, color="gray", ls="--", alpha=0.6)
    ax3.set_xlabel("전반부 기울기 (MinMax 기반)")
    ax3.set_ylabel("후반부 기울기 (MinMax 기반)")
    ax3.set_title("전반/후반 기울기 사분면  (단위 통일)", fontsize=12, fontweight="bold")
    ax3.legend(fontsize=8, markerscale=2)
    ax3.grid(alpha=0.3)

    # ── 4: Ablation
    if ablation_df is not None and not ablation_df.empty:
        fsets   = ablation_df["Feature Set"].unique()
        models  = ablation_df["Model"].unique()
        x       = np.arange(len(models))
        w       = 0.25
        bcolors = ["#90A4AE","#42A5F5","#1565C0"]
        for i, fs in enumerate(fsets):
            sub  = ablation_df[ablation_df["Feature Set"] == fs]
            bars = ax4.bar(x + i*w, sub["F1"].values, w,
                           label=fs, color=bcolors[i],
                           yerr=sub["Std"].values, capsize=4)
            ax4.bar_label(bars, fmt="%.3f", fontsize=8, padding=3,
                          fontweight="bold" if i == len(fsets)-1 else "normal")
        base_f1 = ablation_df[ablation_df["Feature Set"]=="Base"]["F1"].values
        full_f1 = ablation_df[ablation_df["Feature Set"]==fsets[-1]]["F1"].values
        for j, (b, u) in enumerate(zip(base_f1, full_f1)):
            ax4.annotate(f"▲{u-b:+.3f}",
                         xy=(j + (len(fsets)-1)*w, u + 0.03),
                         fontsize=8, color="#2E7D32", ha="center",
                         fontweight="bold")
        ax4.set_xticks(x + w)
        ax4.set_xticklabels(models, rotation=10, ha="right")
        ax4.set_ylim(0, 1.0)
        ax4.legend(fontsize=9)
        ax4.grid(alpha=0.3, axis="y")
        if early_res:
            ax4.text(0.5, 0.06,
                     f"조기예측({early_res['W']}주): "
                     f"F1={early_res['f1']:.3f}±{early_res['std']:.3f}"
                     f"  (n={early_res['n']:,})",
                     transform=ax4.transAxes, fontsize=10, ha="center",
                     color="#7B1FA2", fontweight="bold",
                     bbox=dict(boxstyle="round,pad=0.3",
                               facecolor="#F3E5F5", alpha=0.8))
    ax4.set_title("Ablation Study: 피처셋별 예측 성능 (F1 weighted)",
                  fontsize=12, fontweight="bold")

    # ── 5: K-Means 클러스터 중심선
    if km_model is not None:
        nc   = km_model.n_clusters
        cmap = plt.cm.get_cmap("tab10", nc)
        for c in range(nc):
            ctr   = km_model.cluster_centers_[c]
            s, *_ = stats.linregress(np.arange(len(ctr), dtype=float), ctr)
            ax5.plot(ctr, color=cmap(c), linewidth=2.2,
                     label=f"C{c}  (기울기 {s:+.4f})")
        ax5.axhline(0.5, color="gray", ls="--", alpha=0.3)
        ax5.set_title(f"K-Means 궤적 클러스터 중심  (K={nc})",
                      fontsize=12, fontweight="bold")
        ax5.set_xlabel("오픈 후 경과 주차")
        ax5.set_ylabel("정규화 매출 (MinMax)")
        ax5.legend(fontsize=9)
        ax5.grid(alpha=0.3)

    fig.suptitle(
        "소상공인 생애주기 진단  v5.0  ─  데이터 드리븐  (6클래스)",
        fontsize=15, fontweight="bold", y=0.998
    )
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    print(f"[Viz] 저장: {out}")
    plt.close()


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    BASE    = "../original_data"
    PARQUET = f"{BASE}/weekly.parquet"   # 원본 (테스트: weekly_reduced.parquet)
    META    = f"{BASE}/meta.csv"

    ts, meta = load_data(PARQUET, META)
    ts       = preprocess(ts, meta, min_weeks=52)
    ts       = classify_category(ts)

    print("\n[Step3] 피처 추출...")
    feat = extract_features(ts, max_weeks=108)

    print("\n[Step4] 레이블 할당 (데이터 드리븐)...")
    feat = assign_labels(feat)

    print("\n[Step5] 궤적 클러스터링 (K=6)...")
    cluster_df, km_model = cluster_trajectories(ts, n_clusters=6, seed=42)
    feat = feat.merge(cluster_df, on="public_id", how="left")
    feat.to_csv("lifecycle_features_v5.csv", index=False)
    print(f"  → lifecycle_features_v5.csv")

    print("\n[Step6] Ablation Study...")
    ablation_df = run_ablation(feat, meta)
    ablation_df.to_csv("ablation_results_v5.csv", index=False)
    print(f"  → ablation_results_v5.csv")

    print("\n[Step7] 조기 예측 (30주)...")
    early_res = early_prediction(ts, feat, W=30)

    print("\n[Step8] 시각화...")
    visualize(feat, ablation_df, ts, early_res, km_model,
              out="lifecycle_results_v5.png")

    # ── 최종 요약
    print("\n" + "═"*62)
    print("✅  분석 완료  (v5.0 — 데이터 드리븐, 6클래스)")
    print("═"*62)
    vc = feat["label"].value_counts().reindex(LABELS, fill_value=0)
    print(f"\n  {'레이블':<6} {'업장수':>7} {'비율':>7}  설명")
    print("  " + "-"*55)
    for lbl in LABELS:
        cnt = vc[lbl]; pct = cnt / len(feat) * 100
        print(f"  {lbl:<6} {cnt:>7,} {pct:>6.1f}%  {LABEL_DESC[lbl]}")
    print(f"\n  조기예측(30주) F1: {early_res['f1']:.4f} ± {early_res['std']:.4f}")
    print("═"*62)

    for f in ["lifecycle_features_v5.csv","ablation_results_v5.csv",
              "lifecycle_results_v5.png"]:
        if os.path.exists(f):
            print(f"  ✓ {f}  ({os.path.getsize(f)/1024:.0f} KB)")
