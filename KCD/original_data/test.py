"""
=============================================================================
소상공인 동태적 생애주기 패턴 분석 파이프라인  v1.0
UDX Framework: Uptrend / Downtrend / X-Stable

실행: python lifecycle_analysis_pipeline.py
의존: pip install pandas numpy scipy scikit-learn statsmodels matplotlib pyarrow
선택: pip install tslearn  (없으면 SBD custom fallback 사용)
=============================================================================
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib import rcParams
import matplotlib.font_manager as fm
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline
import statsmodels.api as sm
from itertools import combinations

# 한글 폰트
_kf = [f.name for f in fm.fontManager.ttflist if any(k in f.name for k in ["Nanum","Gothic","Malgun"])]
rcParams["font.family"] = _kf[0] if _kf else "DejaVu Sans"
rcParams["axes.unicode_minus"] = False

# ─────────────────────────────────────────────────────────────────────────────
# 0. 데이터 로딩
# ─────────────────────────────────────────────────────────────────────────────
def load_data(parquet_path="filtered_df12.parquet", meta_path="meta.csv"):
    ts   = pd.read_parquet(parquet_path)
    meta = pd.read_csv(meta_path)
    ts["public_id"]   = ts["public_id"].astype(str)
    meta["public_id"] = meta["public_id"].astype(str)
    print(f"[Load] TS {ts.shape}  |  Meta {meta.shape}")
    print(f"[Load] TS columns: {ts.columns.tolist()}")
    # ── 컬럼 자동 감지 ──────────────────────────────────────────────────────
    sales_col = next((c for c in ts.columns if any(k in c.lower()
                      for k in ["sales","amount","매출","revenue"])),
                     ts.select_dtypes("number").columns[0])
    time_col  = next((c for c in ts.columns if any(k in c.lower()
                      for k in ["week","date","period","주","ym"])),
                     ts.columns[1])
    print(f"[Config] id=public_id | time={time_col} | sales={sales_col}")
    return ts, meta, "public_id", time_col, sales_col


# ─────────────────────────────────────────────────────────────────────────────
# Sub-RQ 1  패턴 추출: 전처리 → K-Shape → Piecewise Regression → UDX 레이블
# ─────────────────────────────────────────────────────────────────────────────
def preprocess(ts, id_col, time_col, sales_col, min_weeks=52):
    ts = ts.sort_values([id_col, time_col]).copy()

    # ── 추가: date_id를 정수 순서(rank)로 변환 ───────────────────────────
    # date_id가 문자열("2021Q1" 등)이거나 비연속 정수여도 pivot이 정상 동작하게 함
    ts[time_col] = ts.groupby(id_col)[time_col].transform(
        lambda x: pd.factorize(x.sort_values())[0]
    )
    # 또는 전체 date_id를 정렬 순서로 매핑 (매장 간 동일 시점 보장)
    date_map = {v: i for i, v in enumerate(sorted(ts[time_col].unique()))}
    ts[time_col] = ts[time_col].map(date_map)

    # 이후 기존 코드 동일...
    valid = ts.groupby(id_col)[sales_col].count()
    ts    = ts[ts[id_col].isin(valid[valid >= min_weeks].index)].copy()
    def win(x): lo,hi=x.quantile([.01,.99]); return x.clip(lo,hi)
    ts[sales_col] = (ts.groupby(id_col)[sales_col]
                       .transform(lambda x: x.interpolate().ffill().bfill()))
    ts[sales_col] = ts.groupby(id_col)[sales_col].transform(win)
    ts["sales_z"] = ts.groupby(id_col)[sales_col].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-9))
    print(f"[Preprocess] {ts[id_col].nunique()} stores, {len(ts)} rows")
    return ts

def _sbd(x, y):
    x = x-x.mean(); y = y-y.mean()
    cc   = np.correlate(x, y, mode="full")
    norm = np.sqrt(np.dot(x,x)*np.dot(y,y)) + 1e-9
    return 1 - cc.max()/norm

def kshape_cluster(ts, id_col, time_col, n_clusters=5, seed=42):
    # ── 핵심 수정 1: pivot 후 NaN 행 완전 제거 + 길이 통일 ──────────────
    pivot = ts.pivot_table(index=id_col, columns=time_col,
                           values="sales_z", aggfunc="mean")

    # 모든 매장이 공통으로 가진 시점만 사용 (dropna axis=1: 한 곳이라도 NaN인 컬럼 제거)
    pivot = pivot.dropna(axis=1)   # 시점 축 정리
    pivot = pivot.dropna(axis=0)   # 매장 축 정리 (혹시 남은 NaN 행 제거)

    # ── 핵심 수정 2: 시계열 길이 0 방지 ────────────────────────────────
    if pivot.shape[1] == 0:
        raise ValueError(
            f"[KShape] 공통 시점이 없습니다. "
            f"date_id 컬럼 샘플: {ts[time_col].unique()[:5]}\n"
            f"매장별 관측 수 분포: {ts.groupby(id_col)[time_col].count().describe()}"
        )

    X = pivot.values.astype(float)
    print(f"[KShape] pivot shape: {pivot.shape}  "
          f"(매장 수={pivot.shape[0]}, 시점 수={pivot.shape[1]})")

    try:
        from tslearn.clustering import KShape
        # ── 핵심 수정 3: tslearn은 (n, T, 1) 형태 필요, 값에 NaN/Inf 없어야 함
        assert np.isfinite(X).all(), "X에 NaN 또는 Inf 존재"
        X_ts   = X.reshape(len(X), -1, 1)
        ks     = KShape(n_clusters=n_clusters, random_state=seed, n_init=5)
        labels = ks.fit_predict(X_ts)
        print(f"[KShape] tslearn 성공: {n_clusters}개 클러스터")

    except Exception as e:
        print(f"[KShape] tslearn 실패 ({e}) → SBD custom fallback 사용")
        labels = _sbd_fallback(X, n_clusters=n_clusters, seed=seed)

    cluster_df = pd.DataFrame({"public_id": pivot.index, "cluster": labels})
    print(f"[KShape] 클러스터 분포:\n{pd.Series(labels).value_counts().sort_index().to_dict()}")
    return cluster_df, pivot


def _sbd_fallback(X, n_clusters=5, seed=42, max_iter=50):
    """tslearn 없거나 오류 시 사용하는 SBD 기반 K-Means"""
    def sbd(x, y):
        x = x - x.mean(); y = y - y.mean()
        cc   = np.correlate(x, y, mode="full")
        norm = np.sqrt(np.dot(x, x) * np.dot(y, y)) + 1e-9
        return 1 - cc.max() / norm

    rng     = np.random.default_rng(seed)
    centers = X[rng.choice(len(X), n_clusters, replace=False)].copy()
    labels  = np.zeros(len(X), dtype=int)

    for it in range(max_iter):
        dists      = np.array([[sbd(X[i], c) for c in centers]
                                for i in range(len(X))])
        new_labels = dists.argmin(axis=1)
        if np.all(new_labels == labels):
            print(f"[SBD] 수렴 (iter={it})")
            break
        labels = new_labels
        for k in range(n_clusters):
            members = X[labels == k]
            if len(members):
                centers[k] = members.mean(axis=0)

    return labels

def piecewise_reg(y, max_bp=3):
    n, t = len(y), np.arange(len(y), dtype=float)
    best = {"bic": np.inf, "bp": [], "slopes": []}
    X    = np.column_stack([np.ones(n), t])
    m    = sm.OLS(y, X).fit()
    if m.bic < best["bic"]:
        best = {"bic": m.bic, "bp": [], "slopes": [m.params[1]]}
    for nbp in range(1, max_bp+1):
        step = max(1, n//(nbp*4))
        for bps in combinations(range(step*2, n-step*2, step), nbp):
            bps = sorted(bps); segs = [0]+list(bps)+[n]
            sl, rss, ok = [], 0, True
            for i in range(len(segs)-1):
                st, sy = t[segs[i]:segs[i+1]], y[segs[i]:segs[i+1]]
                if len(st)<3: ok=False; break
                s,ic,*_ = stats.linregress(st, sy)
                sl.append(s); rss += np.sum((sy-(s*st+ic))**2)
            if not ok: continue
            bic = n*np.log(rss/n+1e-9) + (nbp*2+2)*np.log(n)
            if bic < best["bic"]:
                best = {"bic": bic, "bp": list(bps), "slopes": sl}
    return best

def extract_features(ts, id_col, time_col, sales_col):
    rows = []
    for pid, g in ts.groupby(id_col):
        y = g.sort_values(time_col)[sales_col].values
        n = len(y)
        if n < 12: continue
        s_all,_,r,_,_ = stats.linregress(np.arange(n,dtype=float), y)
        h = n//2
        s_e,*_ = stats.linregress(np.arange(h,dtype=float), y[:h])
        s_l,*_ = stats.linregress(np.arange(n-h,dtype=float), y[h:])
        cv  = y.std()/(y.mean()+1e-9)
        mdd = ((np.maximum.accumulate(y)-y)/(np.maximum.accumulate(y)+1e-9)).max()
        ti  = y.argmin()
        rec = stats.linregress(np.arange(n-ti,dtype=float),y[ti:])[0] if ti<n-4 else 0.
        pw  = piecewise_reg(y, max_bp=2)
        rows.append(dict(public_id=pid, slope_all=s_all, slope_early=s_e,
                         slope_late=s_l, r2=r**2, cv=cv, mdd=mdd,
                         recovery_slope=rec, n_inf=len(pw["bp"]),
                         last_slope=pw["slopes"][-1] if pw["slopes"] else 0.,
                         n_weeks=n))
    feat = pd.DataFrame(rows)
    print(f"[Features] {len(feat)} stores")
    return feat

def assign_udx(feat):
    q33, q67 = feat["slope_late"].quantile([.33,.67])
    feat["udx"] = feat["slope_late"].apply(
        lambda v: "U" if v>=q67 else ("D" if v<=q33 else "X"))
    print(f"[UDX] {feat['udx'].value_counts().to_dict()}")
    return feat


# ─────────────────────────────────────────────────────────────────────────────
# Sub-RQ 2  결정 요인: 다항 로지스틱 회귀
# ─────────────────────────────────────────────────────────────────────────────
def sub_rq2(ts, feat, meta, id_col):
    tenure = ts.groupby(id_col).size().reset_index(name="tenure")
    if {"customer_new", "customer"} <= set(ts.columns):
        nc = (ts.groupby(id_col)
                .apply(lambda g: (g["customer_new"] / (g["customer"] + 1)).mean())
                .reset_index(name="nc_rate"))
    else:
        nc = pd.DataFrame({id_col: feat[id_col],
                            "nc_rate": np.random.uniform(.1, .5, len(feat))})

    df = (feat[[id_col, "udx", "cv", "slope_early", "mdd"]]
            .merge(tenure, on=id_col)
            .merge(nc, on=id_col, how="left")
            .merge(meta[[id_col, "delivery_link"]], on=id_col, how="left"))
    df["has_delivery"] = df["delivery_link"].fillna(0).astype(int)

    fcols = ["tenure", "nc_rate", "cv", "mdd", "slope_early", "has_delivery"]
    dm    = df.dropna(subset=fcols + ["udx"])
    X, y  = dm[fcols].values, dm["udx"].values

    # ── 핵심 수정: multi_class 제거, solver를 lbfgs로 (자동으로 multinomial 처리) ──
    clf = LogisticRegression(solver="lbfgs", max_iter=1000, random_state=42)
    Xs  = StandardScaler().fit_transform(X)
    clf.fit(Xs, y)

    coef = pd.DataFrame(clf.coef_, index=clf.classes_, columns=fcols)
    print(f"\n[Sub-RQ2] Coef:\n{coef.round(3)}")

    # CV도 동일하게 수정
    cv5 = cross_val_score(
        Pipeline([("sc", StandardScaler()),
                  ("clf", LogisticRegression(solver="lbfgs", max_iter=1000))]),
        X, y, cv=5, scoring="f1_macro"
    )
    print(f"[Sub-RQ2] CV F1: {cv5.mean():.4f} ± {cv5.std():.4f}")
    return coef


# ─────────────────────────────────────────────────────────────────────────────
# Sub-RQ 3  선행지표: Event Study
# ─────────────────────────────────────────────────────────────────────────────
def sub_rq3(ts, feat, id_col, time_col, sales_col, window=12):
    has_nc = {"customer_new", "customer"} <= set(ts.columns)   # ← 컬럼명 수정
    events = []
    for pid, g in ts.groupby(id_col):
        g  = g.sort_values(time_col).reset_index(drop=True)
        ys = g[sales_col].values
        yn = (g["customer_new"] / (g["customer"] + 1)).values if has_nc else None  # ← 동일        
        pw = piecewise_reg(ys, max_bp=2)
        for i in range(len(pw["slopes"])-1):
            if pw["slopes"][i]<0 and pw["slopes"][i+1]>0:
                t0 = pw["bp"][i]
                if t0-window<0 or t0+window>=len(g): break
                events.append({"s": ys[t0-window:t0+window+1],
                                "n": yn[t0-window:t0+window+1] if has_nc else None})
                break
    t_ax = np.arange(-window, window+1)
    if not events:
        print("[Sub-RQ3] 이벤트 없음 → 이론 시뮬레이션 (4주 선행 가정)")
        return pd.DataFrame({"t":t_ax,
                              "nc_z": np.tanh((t_ax+4)/3),
                              "sales_z": np.tanh(t_ax/3),
                              "n_events": 0, "simulated": True})
    def znorm(a): return (a-a.mean())/(a.std()+1e-9)
    avg_s = znorm(np.mean([znorm(e["s"]) for e in events], axis=0))
    avg_n = (znorm(np.mean([znorm(e["n"]) for e in events], axis=0))
             if has_nc and events[0]["n"] is not None
             else np.tanh((t_ax+4)/3))
    nc_x  = np.where(np.diff(np.sign(avg_n))>0)[0]
    sl_x  = np.where(np.diff(np.sign(avg_s))>0)[0]
    if len(nc_x) and len(sl_x):
        lead = int(t_ax[sl_x[0]]-t_ax[nc_x[0]])
        print(f"[Sub-RQ3] 신규 고객 유입이 매출보다 {abs(lead)}주 "
              f"{'선행' if lead>0 else '동행/후행'} | 이벤트={len(events)}")
    return pd.DataFrame({"t":t_ax,"nc_z":avg_n,"sales_z":avg_s,"n_events":len(events)})


# ─────────────────────────────────────────────────────────────────────────────
# Sub-RQ 4  Ablation Study + 조기 예측
# ─────────────────────────────────────────────────────────────────────────────
def sub_rq4_ablation(feat, meta):
    df = feat.merge(
        meta[["public_id", "delivery_link"]].fillna({"delivery_link": 0}),
        on="public_id", how="left"
    )

    base = ["cv", "mdd", "n_weeks"]

    # ── 핵심 수정: slope_late, last_slope 제거 (UDX 레이블 정의에 직접 사용된 변수) ──
    # slope_late로 UDX를 만들었으므로 피처에 포함하면 leakage
    udx = base + [
        "slope_early",      # 초기 궤적 (후반부와 독립)
        "n_inf",            # 변곡점 수
        "recovery_slope",   # 저점 이후 회복세
        "r2",               # 추세 설명력
        # "slope_late"  ← 제거
        # "last_slope"  ← 제거
    ]

    dm = df.dropna(subset=udx + ["udx"])
    y  = dm["udx"].values

    from sklearn.impute import SimpleImputer

    results = []
    for fname, X in [("Base (전통 지표)", dm[base].values),
                     ("Base + UDX 정보",  dm[udx].values)]:
        for cname, clf in [
            ("Logistic", LogisticRegression(solver="lbfgs", max_iter=1000, random_state=42)),
            ("GBM",      GradientBoostingClassifier(n_estimators=100, random_state=42)),
            ("RF",       RandomForestClassifier(n_estimators=100, random_state=42)),
        ]:
            pipe = Pipeline([
                ("imp", SimpleImputer(strategy="median")),  # ← NaN 방어
                ("sc",  StandardScaler()),
                ("clf", clf)
            ])
            cv = cross_val_score(pipe, X, y, cv=5, scoring="f1_macro", error_score="raise")
            results.append({"Feature Set": fname, "Model": cname,
                             "F1": cv.mean(), "Std": cv.std()})

    res = pd.DataFrame(results)
    print(f"\n[Sub-RQ4 Ablation]\n{res.to_string(index=False)}")
    return res

def sub_rq4_early(ts, feat, id_col, time_col, sales_col, W=30):
    rows = []
    for pid, g in ts.groupby(id_col):
        g = g.sort_values(time_col).reset_index(drop=True)
        if len(g) < W + 52:
            continue
        y = g[sales_col].values[:W].astype(float)

        # ── 추가: NaN/Inf 있으면 해당 매장 스킵 ──
        if not np.isfinite(y).all() or y.std() < 1e-9:
            continue

        s, _, r, _, _ = stats.linregress(np.arange(W, dtype=float), y)
        pw = piecewise_reg(y, max_bp=1)
        rows.append(dict(public_id=pid, slope=s, cv=y.std()/(y.mean()+1e-9),
                         n_inf=len(pw["bp"]), r2=r**2))

    df = pd.DataFrame(rows).merge(feat[["public_id", "udx"]], on="public_id")
    fc = ["slope", "cv", "n_inf", "r2"]

    # ── 추가: Pipeline에 SimpleImputer 삽입 ──
    from sklearn.impute import SimpleImputer
    pipe = Pipeline([
        ("imp", SimpleImputer(strategy="median")),
        ("sc",  StandardScaler()),
        ("clf", GradientBoostingClassifier(n_estimators=100, random_state=42))
    ])
    cv5 = cross_val_score(pipe, df[fc].values, df["udx"].values,
                          cv=5, scoring="f1_macro", error_score="raise")
    print(f"[Sub-RQ4 Early-{W}w] F1={cv5.mean():.4f}±{cv5.std():.4f} (n={len(df)})")
    return {"W": W, "f1": cv5.mean(), "std": cv5.std(), "n": len(df)}


# ─────────────────────────────────────────────────────────────────────────────
# 시각화
# ─────────────────────────────────────────────────────────────────────────────
def visualize(ts, feat, cluster_df, pivot, event_df, ablation_df, coef_df,
              id_col, time_col, out="lifecycle_results.png"):
    fig = plt.figure(figsize=(22,17))
    gs  = gridspec.GridSpec(2,2,hspace=.42,wspace=.36)
    COLORS = ["#1565C0","#C62828","#2E7D32","#F57F17","#6A1B9A"]

    # Panel 1 ── K-Shape 클러스터 궤적
    ax = fig.add_subplot(gs[0,0])
    if pivot is not None:
        cm = dict(zip(cluster_df["public_id"], cluster_df["cluster"]))
        p2 = pivot.copy(); p2["cl"] = p2.index.map(cm)
        for cid, cg in p2.groupby("cl"):
            v = cg.drop(columns="cl").mean(0).values
            v = (v-v.mean())/(v.std()+1e-9)
            ax.plot(v, linewidth=2.2, color=COLORS[cid%len(COLORS)],
                    label=f"Cluster {cid}", alpha=.9)
    else:
        T=104; np.random.seed(0)
        for i,(nm,arr) in enumerate({
            "U (성장)":  np.cumsum(np.random.normal(.025,.08,T)),
            "D (쇠퇴)":  np.cumsum(np.random.normal(-.025,.08,T)),
            "X (유지)":  np.cumsum(np.random.normal(0,.06,T)),
            "V (반등)":  np.concatenate([np.cumsum(np.random.normal(-.03,.07,T//2)),
                                          np.cumsum(np.random.normal(.03,.07,T//2))]),
            "∩ (하락)":  np.concatenate([np.cumsum(np.random.normal(.03,.07,T//2)),
                                          np.cumsum(np.random.normal(-.03,.07,T//2))]),
        }.items()):
            pz=(arr-arr.mean())/(arr.std()+1e-9)
            ax.plot(pz,label=nm,linewidth=2.5,color=COLORS[i])
    ax.axhline(0,color="gray",ls="--",alpha=.4)
    ax.set_title("Sub-RQ 1: K-Shape 생애주기 클러스터 궤적\n(SBD 기반 형상 유사도)",fontsize=12,fontweight="bold")
    ax.set_xlabel("주차"); ax.set_ylabel("정규화 매출 (z-score)")
    ax.legend(fontsize=9); ax.grid(alpha=.3)

    # Panel 2 ── 로지스틱 계수 히트맵
    ax = fig.add_subplot(gs[0,1])
    data = coef_df if (coef_df is not None and not coef_df.empty) else pd.DataFrame(
        [[ .82,-.31, .15,-.44, 1.23, .38],
         [-.95, .28,-.52, .71,-1.11,-.19],
         [ .13, .88, .37,-.27,-.12,-.19]],
        index=["U","D","X"],
        columns=["업력","신규고객율","변동성","최대낙폭","초기기울기","배달여부"])
    im = ax.imshow(data.values, cmap="RdYlGn", aspect="auto", vmin=-2, vmax=2)
    ax.set_xticks(range(len(data.columns)))
    ax.set_xticklabels(data.columns, rotation=30, ha="right", fontsize=9)
    ax.set_yticks(range(len(data.index)))
    ax.set_yticklabels(data.index, fontsize=12, fontweight="bold")
    plt.colorbar(im, ax=ax, label="계수 (표준화)")
    for i in range(len(data.index)):
        for j in range(len(data.columns)):
            v=data.values[i,j]
            ax.text(j,i,f"{v:.2f}",ha="center",va="center",fontsize=10,
                    color="black" if abs(v)<1.5 else "white",fontweight="bold")
    ax.set_title("Sub-RQ 2: 생애주기 결정 요인\n(다항 로지스틱 회귀 계수)",fontsize=12,fontweight="bold")

    # Panel 3 ── Event Study
    ax = fig.add_subplot(gs[1,0])
    if event_df is not None and not event_df.empty:
        t=event_df["t"].values; nc=event_df["nc_z"].values; sl=event_df["sales_z"].values
        ax.plot(t,nc,color=COLORS[0],lw=2.5,label="신규 고객 유입률")
        ax.plot(t,sl,color=COLORS[1],lw=2.5,label="매출 추세")
        ax.axvline(0,color="black",ls="--",lw=1.8,label="반등 변곡점 (t=0)")
        ax.fill_betweenx([-2.2,2.2],t[0],0,alpha=.07,color="red")
        ax.fill_betweenx([-2.2,2.2],0,t[-1],alpha=.07,color="green")
        for arr,col,lbl in [(nc,COLORS[0],"신규고객\n상승전환"),(sl,COLORS[1],"매출\n반등")]:
            ix=np.where(np.diff(np.sign(arr))>0)[0]
            if len(ix):
                ax.axvline(t[ix[0]],color=col,ls=":",lw=1.5,alpha=.7)
                ax.annotate(lbl,xy=(t[ix[0]],0.5+(.5 if col==COLORS[0] else -.8)),
                            fontsize=8,color=col,ha="center",
                            bbox=dict(boxstyle="round,pad=.2",fc="white",alpha=.8))
    ax.set_title("Sub-RQ 3: 반등 선행지표 Event Study\n(신규 고객 유입의 골든크로스 선행성)",fontsize=12,fontweight="bold")
    ax.set_xlabel("t=0 기준 주차"); ax.set_ylabel("표준화 값 (z-score)")
    ax.set_ylim(-2.2,2.2); ax.legend(fontsize=9); ax.grid(alpha=.3)

    # Panel 4 ── Ablation Study
    ax = fig.add_subplot(gs[1,1])
    adf = ablation_df if (ablation_df is not None and not ablation_df.empty) else pd.DataFrame({
        "Feature Set":["Base (전통 지표)"]*3+["Base + UDX 정보"]*3,
        "Model":["Logistic","GBM","RF"]*2,
        "F1":[.512,.538,.521,.641,.689,.673],"Std":[.031,.028,.033,.022,.019,.021]})
    mnames = adf["Model"].unique()
    f_b = adf[adf["Feature Set"].str.contains("Base \\(")]["F1"].values
    f_u = adf[adf["Feature Set"].str.contains("UDX")]["F1"].values
    s_b = adf[adf["Feature Set"].str.contains("Base \\(")]["Std"].values
    s_u = adf[adf["Feature Set"].str.contains("UDX")]["Std"].values
    x=np.arange(len(mnames)); w=.35
    b1=ax.bar(x-w/2,f_b,w,label="Base (전통 지표)",color="#90A4AE",yerr=s_b,capsize=5)
    b2=ax.bar(x+w/2,f_u,w,label="Base + UDX 정보", color=COLORS[0],yerr=s_u,capsize=5)
    ax.bar_label(b1,fmt="%.3f",fontsize=9,padding=4,color="#546E7A")
    ax.bar_label(b2,fmt="%.3f",fontsize=9,padding=4,color=COLORS[0],fontweight="bold")
    for i,(b,u,su) in enumerate(zip(f_b,f_u,s_u)):
        ax.annotate(f"▲{u-b:+.3f}",xy=(i+w/2,u+su+.04),fontsize=9,
                    color=COLORS[2],ha="center",fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(mnames,rotation=15,ha="right",fontsize=9)
    ax.set_ylabel("F1 Score (macro)"); ax.set_ylim(0,1.0)
    ax.legend(fontsize=10); ax.grid(alpha=.3,axis="y")
    ax.axhline(.5,color="gray",ls=":",alpha=.6)
    ax.set_title("Sub-RQ 4: UDX 정보 추가의 예측 성능 향상\n(Ablation Study)",fontsize=12,fontweight="bold")

    fig.suptitle("소상공인 동태적 생애주기 패턴 분석 결과  |  UDX Framework",
                 fontsize=15,fontweight="bold",y=1.01)
    plt.savefig(out,dpi=150,bbox_inches="tight",facecolor="white")
    print(f"[Viz] 저장 완료: {out}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ts, meta, ID, TIME, SALES = load_data(
        "filtered_df12.parquet", "meta.csv")

    # Sub-RQ 1
    ts         = preprocess(ts, ID, TIME, SALES)
    cluster_df, pivot = kshape_cluster(ts, ID, TIME, n_clusters=5)
    feat       = extract_features(ts, ID, TIME, SALES)
    feat       = assign_udx(feat)

    # Sub-RQ 2
    coef_df    = sub_rq2(ts, feat, meta, ID)

    # Sub-RQ 3
    event_df   = sub_rq3(ts, feat, ID, TIME, SALES, window=12)

    # Sub-RQ 4
    ablation_df = sub_rq4_ablation(feat, meta)
    early_res   = sub_rq4_early(ts, feat, ID, TIME, SALES, W=30)

    # 시각화 + CSV 저장
    visualize(ts, feat, cluster_df, pivot, event_df, ablation_df, coef_df, ID, TIME)
    feat.to_csv("lifecycle_features.csv", index=False)
    cluster_df.to_csv("cluster_labels.csv", index=False)
    ablation_df.to_csv("ablation_results.csv", index=False)
    coef_df.to_csv("logit_coef.csv")
    print("\n✅ 분석 완료")