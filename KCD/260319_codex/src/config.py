from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parent
DATA_DIR = REPO_ROOT / "original_data"

WEEKLY_PARQUET = DATA_DIR / "weekly.parquet"
WEEKLY_REDUCED = DATA_DIR / "weekly_reduced.parquet"
META_CSV = DATA_DIR / "meta.csv"

OUTPUT_DIR = PROJECT_ROOT / "outputs"
TABLE_DIR = OUTPUT_DIR / "tables"
FIGURE_DIR = OUTPUT_DIR / "figures"
LOG_DIR = OUTPUT_DIR / "logs"

for path in (OUTPUT_DIR, TABLE_DIR, FIGURE_DIR, LOG_DIR):
    path.mkdir(parents=True, exist_ok=True)


MIN_WEEKS = 52
MAX_WEEKS = 108
OPEN_DATE_MIN = "2019-01-01"
STL_PERIOD = 13

SEED = 42
CV_FOLDS = 5
EARLY_WEEKS = 30

CLUSTER_K_RANGE = range(3, 10)
CLUSTER_K_DEFAULT = 3
CLUSTER_MAX_STORES = 15000
DTW_N_INIT = 5

SLOPE_EPSILON = 0.0
PATTERN_GROWTH_THRESHOLD = 0.05
PATTERN_EDGE_WEEKS = 12

LIFE_CYCLE_MAP = {
    "X": "rising",
    "Y": "maintaining",
    "Z": "declining",
}


def setup_matplotlib():
    import matplotlib.font_manager as fm
    from matplotlib import rcParams
    import matplotlib.pyplot as plt

    candidates = [
        font.name
        for font in fm.fontManager.ttflist
        if any(
            key in font.name
            for key in ("Nanum", "Gothic", "Malgun", "나눔", "Apple SD", "AppleGothic")
        )
    ]
    rcParams["font.family"] = candidates[0] if candidates else "DejaVu Sans"
    rcParams["axes.unicode_minus"] = False
    return plt
