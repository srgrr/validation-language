from pathlib import Path

import polars as pl
import pytest

from validation_language_mockup.data import load_csv


def test_load_csv(tmp_path: Path) -> None:
    path = tmp_path / "data.csv"
    path.write_text("id,value\n1,foo\n2,bar\n")

    df = load_csv(path)

    assert isinstance(df, pl.DataFrame)
    assert df.height == 2
    assert df.columns == ["id", "value"]
    assert df["value"].to_list() == ["foo", "bar"]


def test_load_csv_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_csv(tmp_path / "missing.csv")
