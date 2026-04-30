"""
중앙 설정 ─ 경로, 하이퍼파라미터, 레이블 스키마
"""
from pathlib import Path
import numpy as np

# ── 경로 ─────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent   # 260316_cur/
REPO_ROOT    = PROJECT_ROOT.parent                      # 26-1/
DATA_DIR     = REPO_ROOT / "original_data"

WEEKLY_PARQUET  = DATA_DIR / "weekly.parquet"
WEEKLY_REDUCED  = DATA_DIR / "weekly_reduced.parquet"
META_CSV        = DATA_DIR / "meta.csv"

OUTPUT_DIR  = PROJECT_ROOT / "outputs"
FIGURE_DIR  = OUTPUT_DIR / "figures"
TABLE_DIR   = OUTPUT_DIR / "tables"

for _d in (OUTPUT_DIR, FIGURE_DIR, TABLE_DIR):
    _d.mkdir(parents=True, exist_ok=True)


# ── 전처리 파라미터 ───────────────────────────────────────
MIN_WEEKS       = 52
MAX_WEEKS       = 108
OPEN_DATE_MIN   = "2019-01-01"
STL_PERIOD      = 13          # 분기(13주) 주기 seasonal decomposition


# ── 클러스터링 ────────────────────────────────────────────
CLUSTER_K_RANGE    = range(3, 10)   # K=3,4,5,6,7,8,9
CLUSTER_K_DEFAULT  = 6
DTW_N_INIT         = 5
CLUSTER_MAX_STORES = 15000          # DTW 샘플 상한 (서버급)


# ── 레이블 스키마 (6-class) ────────────────────────────────
LIFECYCLE_LABELS = ["DD_Z", "DD_Y", "DU", "UU", "UD_Z", "UD_Y"]

LABEL_DESC = {
    "DD_Z": "전반↓ 후반↓ 고손실 (쇠퇴)",
    "DD_Y": "전반↓ 후반↓ 저손실 (저성과 안정)",
    "DU":   "전반↓ 후반↑ (반등)",
    "UU":   "전반↑ 후반↑ (지속 성장)",
    "UD_Z": "전반↑ 후반↓ 고손실 (급락)",
    "UD_Y": "전반↑ 후반↓ 저손실 (완만 하락)",
}

LABEL_COLORS = {
    "DD_Z": "#C62828", "DD_Y": "#EF9A9A",
    "DU":   "#1565C0", "UU":   "#2E7D32",
    "UD_Z": "#6A1B9A", "UD_Y": "#F57F17",
}


# ── 예측 ──────────────────────────────────────────────────
EARLY_WEEKS = 30
SEED        = 42
TEST_RATIO  = 0.2
CV_FOLDS    = 5


# ── 업종 매핑 ──────────────────────────────────────────────
def classify_industry(name: str) -> str:
    v = str(name)
    if any(k in v for k in ("카페", "커피")):        return "카페"
    if any(k in v for k in ("베이커리", "디저트")):  return "베이커리/디저트"
    if any(k in v for k in ("술집", "주점", "호프")): return "술집"
    for cat in ("한식", "일식", "양식", "중식", "분식", "패스트푸드"):
        if cat in v:
            return cat
    return "기타"


# ── Matplotlib 한글 폰트 ─────────────────────────────────
def setup_matplotlib():
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    from matplotlib import rcParams

    candidates = [f.name for f in fm.fontManager.ttflist
                  if any(k in f.name for k in ("Nanum", "Gothic", "Malgun", "나눔",
                                                 "Apple SD", "AppleGothic"))]
    rcParams["font.family"] = candidates[0] if candidates else "DejaVu Sans"
    rcParams["axes.unicode_minus"] = False
    return plt
