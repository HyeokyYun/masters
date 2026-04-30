"""Load weekly processed parquet and meta CSV."""
import pandas as pd

from .00_utils import get_weekly_parquet, get_meta_csv


def load_weekly() -> pd.DataFrame:
    """Load weekly data from ../original_data/weekly_processed.parquet (fallback: weekly.parquet)."""
    path = get_weekly_parquet()
    if not path.exists():
        raise FileNotFoundError(f"Weekly parquet not found: {path}")
    return pd.read_parquet(path)


def load_meta() -> pd.DataFrame:
    """Load meta from ../original_data/meta_processed.csv (fallback: meta.csv)."""
    path = get_meta_csv()
    if not path.exists():
        raise FileNotFoundError(f"Meta CSV not found: {path}")
    return pd.read_csv(path)
