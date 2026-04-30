"""Project root and path resolution. All paths are relative to 260204 (project root)."""
from pathlib import Path
import yaml

# Project root = folder 260204 (parent of src/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_config(name: str = "base") -> dict:
    """Load config from configs/<name>.yaml."""
    path = PROJECT_ROOT / "configs" / f"{name}.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_features_csv() -> Path:
    return PROJECT_ROOT / ".." / "basic_data" / "store_features_for_analysis.csv"


def get_variable_desc_csv() -> Path:
    return PROJECT_ROOT / ".." / "basic_data" / "variable_description.csv"


def get_weekly_parquet() -> Path:
    p = PROJECT_ROOT / ".." / "original_data" / "weekly_processed.parquet"
    if not p.exists():
        p = PROJECT_ROOT / ".." / "original_data" / "weekly.parquet"
    return p


def get_meta_csv() -> Path:
    p = PROJECT_ROOT / ".." / "original_data" / "meta_processed.csv"
    if not p.exists():
        p = PROJECT_ROOT / ".." / "original_data" / "meta.csv"
    return p


def get_output_dir(key: str) -> Path:
    """key one of: tables, figures, logs, models."""
    cfg = load_config()
    out = PROJECT_ROOT / cfg["outputs"][key]
    out.mkdir(parents=True, exist_ok=True)
    return out
