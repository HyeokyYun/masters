"""Load and expose store features CSV and variable description."""
import pandas as pd
from pathlib import Path

from .00_utils import get_features_csv, get_variable_desc_csv


def load_features() -> pd.DataFrame:
    """Load store features CSV from ../basic_data/store_features_for_analysis.csv."""
    path = get_features_csv()
    if not path.exists():
        raise FileNotFoundError(f"Features CSV not found: {path}")
    return pd.read_csv(path)


def load_variable_description() -> pd.DataFrame:
    """Load variable description CSV from ../basic_data/variable_description.csv."""
    path = get_variable_desc_csv()
    if not path.exists():
        raise FileNotFoundError(f"Variable description CSV not found: {path}")
    return pd.read_csv(path)
