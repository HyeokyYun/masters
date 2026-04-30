"""Save/load artifacts (models, tables, figures) under outputs/."""
from pathlib import Path
import pickle

from .00_utils import get_output_dir


def save_table(df, name: str, ext: str = "csv") -> Path:
    """Save DataFrame to outputs/tables/<name>.<ext>."""
    out = get_output_dir("tables") / f"{name}.{ext}"
    if ext == "csv":
        df.to_csv(out, index=False)
    else:
        df.to_parquet(out, index=False)
    return out


def save_figure(fig, name: str, ext: str = "png") -> Path:
    """Save matplotlib figure to outputs/figures/<name>.<ext>."""
    out = get_output_dir("figures") / f"{name}.{ext}"
    fig.savefig(out, bbox_inches="tight")
    return out


def save_model(obj, name: str) -> Path:
    """Pickle object to outputs/models/<name>.pkl."""
    out = get_output_dir("models") / f"{name}.pkl"
    with open(out, "wb") as f:
        pickle.dump(obj, f)
    return out


def load_model(name: str):
    """Load pickled object from outputs/models/<name>.pkl."""
    out = get_output_dir("models") / f"{name}.pkl"
    with open(out, "rb") as f:
        return pickle.load(f)
