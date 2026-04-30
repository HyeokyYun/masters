"""
중앙 설정 ─ 경로, 하이퍼파라미터, 레이블 스키마
"""
from pathlib import Path
import numpy as np

# ── 경로 ─────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent   # 260319_cur/
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
CLUSTER_K_RANGE    = range(4, 10)   # K=4,5,6,7,8,9
CLUSTER_K_DEFAULT  = 6
DTW_N_INIT         = 5
CLUSTER_MAX_STORES = 15000          # DTW 샘플 상한 (서버급)


# ── 레이블 스키마 (12-class) ───────────────────────────────
#   1st letter: 전반기 추세  U=상승, D=하락
#   2nd letter: 후반기 추세  U=상승, D=하락
#   suffix:     전체 추세    X=상승, Y=유지, Z=하락
LIFECYCLE_LABELS = [
    "DD_Z", "DD_Y", "DD_X",
    "DU_Z", "DU_Y", "DU_X",
    "UU_Z", "UU_Y", "UU_X",
    "UD_Z", "UD_Y", "UD_X",
]

SLOPE_ALL_THRESHOLD_FACTOR = 0.5   # std × factor → 유지 대역 반폭

LABEL_DESC = {
    "DD_Z": "전반↓ 후반↓ 전체↓ (쇠퇴)",
    "DD_Y": "전반↓ 후반↓ 전체유지 (저성과 안정)",
    "DD_X": "전반↓ 후반↓ 전체↑ (V자 회복 미달)",
    "DU_Z": "전반↓ 후반↑ 전체↓ (불완전 반등)",
    "DU_Y": "전반↓ 후반↑ 전체유지 (부분 반등)",
    "DU_X": "전반↓ 후반↑ 전체↑ (강한 반등)",
    "UU_Z": "전반↑ 후반↑ 전체↓ (정체)",
    "UU_Y": "전반↑ 후반↑ 전체유지 (완만 성장)",
    "UU_X": "전반↑ 후반↑ 전체↑ (지속 성장)",
    "UD_Z": "전반↑ 후반↓ 전체↓ (급락)",
    "UD_Y": "전반↑ 후반↓ 전체유지 (소폭 조정)",
    "UD_X": "전반↑ 후반↓ 전체↑ (성장 후 경미 조정)",
}

LABEL_COLORS = {
    "DD_Z": "#B71C1C", "DD_Y": "#E53935", "DD_X": "#EF9A9A",
    "DU_Z": "#0D47A1", "DU_Y": "#1976D2", "DU_X": "#64B5F6",
    "UU_Z": "#1B5E20", "UU_Y": "#388E3C", "UU_X": "#66BB6A",
    "UD_Z": "#4A148C", "UD_Y": "#F57F17", "UD_X": "#FFB300",
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
