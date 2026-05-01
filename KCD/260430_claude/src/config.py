"""260430_claude 공통 설정."""
from __future__ import annotations

from pathlib import Path

ROOT = Path("/home/hyeoky98/kcd")
BASE = ROOT / "260430_claude"
SRC_DIR = BASE / "src"
OUT_DIR = BASE / "outputs"
TABLE_DIR = OUT_DIR / "tables"
FIGURE_DIR = OUT_DIR / "figures"
DOC_DIR = BASE / "docs"
PANEL_DIR = TABLE_DIR / "panels"
LABEL_DIR = TABLE_DIR / "labels"
FEATURE_DIR = TABLE_DIR / "features"

for _p in [TABLE_DIR, FIGURE_DIR, DOC_DIR, PANEL_DIR, LABEL_DIR, FEATURE_DIR]:
    _p.mkdir(parents=True, exist_ok=True)

WEEKLY_PATH = ROOT / "original_data" / "weekly.parquet"
META_PATH = ROOT / "original_data" / "meta.csv"

DATA_START = "2021-01-01"
DATA_END = "2023-08-28"

START_YEARS = [2021, 2022]
START_MONTHS = list(range(1, 13))
WINDOW_MONTHS = [1, 2, 3]
TARGET_YEAR_OFFSETS = [1, 2]

WEEKS_PER_MONTH = 4

MIN_FEATURE_WEEKS_RATIO = 0.6
MIN_TARGET_WEEKS_RATIO = 0.6

MIN_PANEL_WEEKS = 26

OUTCOME_CLASSES = ["Decline", "Stable", "Growth"]
SLOPE_THRESHOLD_SIGMA = 0.5

CV_FOLDS = 5
SEED = 42

FIG_DPI = 200
FIG_STYLE = {
    "font.family": "DejaVu Sans",
    "axes.unicode_minus": False,
    "font.size": 10,
    "figure.dpi": 110,
    "savefig.dpi": FIG_DPI,
    "savefig.bbox": "tight",
}


def combo_id(start_year: int, start_month: int, window_months: int, target_offset: int) -> str:
    return f"sy{start_year}_sm{start_month:02d}_w{window_months}m_off{target_offset}"
