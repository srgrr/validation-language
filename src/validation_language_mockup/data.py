from pathlib import Path

import polars as pl


def load_csv(path: Path) -> pl.DataFrame:
    """Load a CSV file as a Polars DataFrame."""
    if not path.is_file():
        raise FileNotFoundError(f"CSV file not found: {path}")
    return pl.read_csv(path)
