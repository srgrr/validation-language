from pathlib import Path

import polars as pl

from validation_language_mockup.rounds import load_round_csv, load_rounds


def test_load_round_csv(tmp_path: Path) -> None:
    path = tmp_path / "round_1.csv"
    path.write_text("id,value\n1,foo\n2,bar\n")

    df = load_round_csv(path)

    assert isinstance(df, pl.DataFrame)
    assert df.height == 2
    assert df.columns == ["id", "value"]
    assert df["value"].to_list() == ["foo", "bar"]


def test_load_rounds(tmp_path: Path) -> None:
    (tmp_path / "round_2.csv").write_text("x\n1\n")
    (tmp_path / "round_1.csv").write_text("y\n2\n")

    loaded = load_rounds(tmp_path)

    assert [r.number for r, _ in loaded] == [1, 2]
    assert loaded[0][1].columns == ["y"]
    assert loaded[1][1].height == 1
